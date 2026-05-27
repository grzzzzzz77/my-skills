#!/usr/bin/env python3
"""
审批状态守护进程  —  v0.1

M3 提交成功后被 submit_first_approval.py 通过 subprocess.Popen 拉起,
后台轮询第一审批状态, APPROVED 即自动触发 M4, 然后退出.

退出条件 (任一):
  - 第一审批 APPROVED  → 跑 M4 → 退出
  - 第一审批 REJECTED  → 标记 state.rejected → 退出
  - 已无 first_approval_pending 项 → 退出
  - 超过 MAX_HOURS 小时未变化 → 退出 (兜底)
  - 已有同一 PID 锁 → 立刻退出 (防重启)

设计:
  - 仅用 stdlib + feishu_upload (tenant token 自动续期)
  - 网络错误 5 分钟后重试, 不消耗轮询配额
  - PID 锁: ~/.invoice-reimbursement/watcher.pid
  - 日志:   ~/.invoice-reimbursement/watcher.log

Usage:
    python3 approval_watcher.py [--once] [--poll-interval SEC]

  --once          只查一次, 不进入循环 (用于 cli watcher-status 检查)
  --poll-interval 自定义轮询间隔秒数 (默认 3600)

Exit codes:
  0  正常退出
  1  无 pending 项 / 已有 watcher 在跑
  2  config 缺失 / API 错误超限
"""

WATCHER_VERSION = "0.1"

import sys
import os
import time
import json
import argparse
from pathlib import Path
from datetime import datetime

sys.path.insert(0, str(Path(__file__).resolve().parent))
from storage import Storage  # noqa: E402
from feishu_upload import call_open_api, UploadError  # noqa: E402


DEFAULT_POLL_SEC = 3600        # 1 小时
ERROR_RETRY_SEC = 300          # 5 分钟
MAX_DURATION_SEC = 72 * 3600   # 72 小时兜底
PID_FILE = "watcher.pid"
LOG_FILE = "watcher.log"


# ---------- 日志 / 锁 ----------

def _log(msg: str, log_path: Path) -> None:
    """append-only 写日志."""
    line = f"[{datetime.now().isoformat(timespec='seconds')}] {msg}\n"
    try:
        with open(log_path, "a", encoding="utf-8") as f:
            f.write(line)
    except OSError:
        pass


def _pid_alive(pid: int) -> bool:
    try:
        os.kill(pid, 0)
        return True
    except OSError:
        return False


def _acquire_lock(pid_path: Path) -> bool:
    """同一时间只允许 1 个 watcher. True = 拿到锁."""
    if pid_path.exists():
        try:
            existing = int(pid_path.read_text().strip())
            if _pid_alive(existing):
                return False
        except (ValueError, OSError):
            pass
    pid_path.write_text(str(os.getpid()))
    return True


def _release_lock(pid_path: Path) -> None:
    try:
        if pid_path.exists():
            current = int(pid_path.read_text().strip())
            if current == os.getpid():
                pid_path.unlink()
    except (OSError, ValueError):
        pass


# ---------- 状态查询 ----------

def query_first_approval_status(instance_code: str,
                                 app_id: str, app_secret: str) -> str:
    """返回 APPROVED / REJECTED / PENDING / ERROR:<msg>."""
    try:
        result = call_open_api(
            "GET", "/open-apis/approval/v4/instances/" + instance_code,
            app_id=app_id, app_secret=app_secret,
        )
    except UploadError as e:
        return f"ERROR:{e}"
    except Exception as e:
        return f"ERROR:{type(e).__name__}: {e}"

    if result.get("code") not in (0, None):
        return f"ERROR:API code={result.get('code')} msg={result.get('msg')}"
    return (result.get("data") or {}).get("status", "PENDING")


# ---------- 主流程 ----------

def watch(storage: Storage, *, poll_interval: int = DEFAULT_POLL_SEC,
          once: bool = False) -> int:
    """轮询第一审批, APPROVED 即触发 M4. 返回 exit code."""
    log_path = storage.base_dir / LOG_FILE
    pid_path = storage.base_dir / PID_FILE

    config = storage.load_config()
    feishu = config.get("feishu") or {}
    app_id = feishu.get("app_id")
    app_secret = feishu.get("app_secret")
    if not app_id or not app_secret:
        _log("config.feishu.app_id/app_secret 缺失, 退出.", log_path)
        return 2

    state = storage.load_state()
    pending = [p for p in state.get("pending", [])
               if p.get("status") == "first_approval_pending"]
    if not pending:
        _log("无 first_approval_pending 项, 退出.", log_path)
        return 1

    instance_code = pending[0].get("first_approval_id")
    if not instance_code:
        _log("first_approval_id 为空, 退出.", log_path)
        return 1

    _log(f"watcher v{WATCHER_VERSION} 启动 (pid={os.getpid()}) "
         f"instance={instance_code} interval={poll_interval}s once={once}",
         log_path)

    start_time = time.time()

    while True:
        status = query_first_approval_status(instance_code, app_id, app_secret)
        _log(f"status = {status}", log_path)

        if status == "APPROVED":
            _log("第一审批通过, 触发 M4 ...", log_path)
            try:
                from submit_second_approval import submit_second_approval
                summary = submit_second_approval(storage=storage)
                _log(f"M4 结果: {json.dumps(summary, ensure_ascii=False)}",
                     log_path)
            except Exception as e:
                _log(f"M4 异常: {type(e).__name__}: {e}", log_path)
                return 2
            return 0

        if status == "REJECTED":
            _log("第一审批被拒绝, 标记 state + 清理 tmp PDF 并退出.", log_path)
            fresh = storage.load_state()
            for item in fresh.get("pending", []):
                if item.get("status") == "first_approval_pending":
                    item["status"] = "rejected"
                    item["reject_reason"] = "first_approval_rejected"
                    # 清 tmp 避免下次 fetch 时残留垃圾
                    for pdf_key in ("invoice_pdf", "trip_pdf"):
                        path_str = item.get(pdf_key)
                        if path_str:
                            fp = Path(path_str)
                            if fp.exists():
                                try:
                                    fp.unlink()
                                except OSError:
                                    pass
            storage.save_state(fresh)
            return 0

        if once:
            return 0

        if status.startswith("ERROR"):
            _log(f"查询失败, {ERROR_RETRY_SEC}s 后重试.", log_path)
            sleep_sec = ERROR_RETRY_SEC
        else:
            sleep_sec = poll_interval

        if time.time() - start_time + sleep_sec > MAX_DURATION_SEC:
            _log(f"已运行 {MAX_DURATION_SEC // 3600} 小时, 退出兜底.",
                 log_path)
            return 0

        time.sleep(sleep_sec)


def main():
    ap = argparse.ArgumentParser(
        description="后台审批守护: M3 提交后轮询第一审批, APPROVED 自动触发 M4."
    )
    ap.add_argument("--once", action="store_true",
                    help="只查一次, 不进入循环 (用于诊断).")
    ap.add_argument("--poll-interval", type=int, default=DEFAULT_POLL_SEC,
                    help=f"轮询间隔秒数 (默认 {DEFAULT_POLL_SEC} = 1h).")
    args = ap.parse_args()

    storage = Storage()
    storage.ensure_dirs()
    pid_path = storage.base_dir / PID_FILE
    log_path = storage.base_dir / LOG_FILE

    if not args.once:
        if not _acquire_lock(pid_path):
            _log("已有 watcher 在运行, 跳过.", log_path)
            sys.exit(1)

    try:
        code = watch(storage, poll_interval=args.poll_interval, once=args.once)
    finally:
        if not args.once:
            _release_lock(pid_path)
        _log("watcher 退出.", log_path)

    sys.exit(code)


if __name__ == "__main__":
    main()
