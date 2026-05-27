#!/usr/bin/env python3
"""
发票报销 Skill 卸载脚本 — v0.1

默认全删:
  - ~/.claude/skills/invoice-reimbursement/   (skill 文件)
  - ~/.invoice-reimbursement/                 (config / rules / state / history / watcher)

可选保留存储 (--keep-data): 只删 skill, 留下配置和历史, 便于重装后不用重新配.

⚠️ 开发须知:
  skill 安装路径默认硬编码为 ~/.claude/skills/invoice-reimbursement/.
  storage 路径可被 INVOICE_REIMBURSEMENT_DIR 环境变量覆盖.
  做 smoke test 时只覆盖 storage **不会**保护 skill 目录, 必须显式传
  --skill-dir 到一个临时目录, 否则会真删生产安装的 skill.

公开函数:
  run(*, keep_data=False, assume_yes=False, storage=None,
      skill_dir=None) -> int

CLI:
  python3 uninstall.py [--keep-data] [--yes] [--skill-dir PATH]
"""

import os
import sys
import signal
import shutil
import argparse
import time
from pathlib import Path
from typing import Optional

sys.path.insert(0, str(Path(__file__).resolve().parent))
from storage import Storage, get_storage_dir  # noqa: E402


DEFAULT_SKILL_INSTALL_DIR = Path.home() / ".claude" / "skills" / "invoice-reimbursement"


def _stop_watcher(storage: Storage) -> Optional[str]:
    """如果 watcher 正在跑就 SIGTERM 它, 返回简短描述; 失败也不阻塞卸载."""
    pid_path = storage.base_dir / "watcher.pid"
    if not pid_path.exists():
        return None
    try:
        pid = int(pid_path.read_text().strip())
    except (ValueError, OSError):
        return f"watcher.pid 不可读, 跳过"

    try:
        os.kill(pid, 0)
    except OSError:
        return f"watcher pid={pid} 已停止, 仅清理残留 PID"

    try:
        os.kill(pid, signal.SIGTERM)
    except OSError as e:
        return f"watcher pid={pid} 发送 SIGTERM 失败: {e}"

    # 给进程 2 秒优雅退出
    for _ in range(20):
        time.sleep(0.1)
        try:
            os.kill(pid, 0)
        except OSError:
            return f"watcher pid={pid} 已停止"
    return f"watcher pid={pid} 收到 SIGTERM 但未在 2s 内退出 (将继续删除文件)"


def _confirm(prompt: str) -> bool:
    """读 stdin; 非 TTY 时返回 False (要求显式 --yes)."""
    if not sys.stdin.isatty():
        return False
    ans = input(prompt).strip().lower()
    return ans in ("y", "yes")


def run(
    *,
    keep_data: bool = False,
    assume_yes: bool = False,
    storage: Optional[Storage] = None,
    skill_dir: Optional[Path] = None,
) -> int:
    """卸载主流程. 返回退出码."""
    if storage is None:
        storage = Storage()
    storage_dir = storage.base_dir
    skill_install_dir = Path(skill_dir).expanduser() if skill_dir else DEFAULT_SKILL_INSTALL_DIR

    skill_present = skill_install_dir.exists()
    data_present = storage_dir.exists()

    print("==> 发票报销 Skill 卸载")
    print()
    print(f"  Skill 目录:   {skill_install_dir}  ({'存在' if skill_present else '不存在'})")
    print(f"  存储目录:     {storage_dir}  ({'存在' if data_present else '不存在'})")
    print(f"  保留存储:     {'是' if keep_data else '否 (含 IMAP 密码 / app_secret / 审批历史会一起删)'}")
    print()

    if not skill_present and not data_present:
        print("  没有可卸载的内容. 直接退出.")
        return 0

    if not assume_yes:
        if keep_data:
            tip = "将删除 skill 目录, 保留存储. 继续? [y/N]: "
        else:
            tip = "将永久删除以上目录及其中**全部**文件 (无法恢复). 继续? [y/N]: "
        if not _confirm(tip):
            print("  已取消.")
            return 1

    # 1. 停 watcher (即使 keep_data, watcher.pid 也得停, 否则后续 skill 不在了 watcher 会找不到脚本)
    if data_present:
        note = _stop_watcher(storage)
        if note:
            print(f"  [watcher] {note}")

    # 2. 删 storage (除非 --keep-data)
    if data_present and not keep_data:
        try:
            shutil.rmtree(storage_dir)
            print(f"  [删除] {storage_dir}")
        except OSError as e:
            print(f"  [ERROR] 删除 {storage_dir} 失败: {e}", file=sys.stderr)
            return 2
    elif data_present and keep_data:
        # 即使保留, 也清掉 watcher.pid 残留
        pid_path = storage_dir / "watcher.pid"
        if pid_path.exists():
            try:
                pid_path.unlink()
                print(f"  [清理] {pid_path}")
            except OSError:
                pass
        print(f"  [保留] {storage_dir}")

    # 3. 删 skill 目录 (放在最后, 因为本脚本住在里面)
    if skill_present:
        try:
            shutil.rmtree(skill_install_dir)
            print(f"  [删除] {skill_install_dir}")
        except OSError as e:
            print(f"  [ERROR] 删除 {skill_install_dir} 失败: {e}", file=sys.stderr)
            return 2

    print()
    print("==> 卸载完成")
    if keep_data:
        print(f"  存储目录已保留: {storage_dir}")
        print(f"  重装后可直接 validate, 不需要重新 onboard.")
    else:
        print(f"  所有数据已清除. 重装请重新跑 install.sh + onboard.")
    return 0


def main(argv=None) -> int:
    p = argparse.ArgumentParser(
        prog="uninstall",
        description="卸载发票报销 Skill (删除 skill 文件 + 存储目录).",
    )
    p.add_argument("--keep-data", action="store_true",
                   help="只删 skill 文件, 保留 ~/.invoice-reimbursement/ (config + history)")
    p.add_argument("--yes", "-y", action="store_true",
                   help="不再二次确认, 直接执行")
    p.add_argument("--skill-dir", default=None,
                   help="覆盖 skill 安装路径 (默认 ~/.claude/skills/invoice-reimbursement/); "
                        "主要给开发 smoke test 用, 普通用户不要传")
    args = p.parse_args(argv)
    return run(
        keep_data=args.keep_data,
        assume_yes=args.yes,
        skill_dir=Path(args.skill_dir) if args.skill_dir else None,
    )


if __name__ == "__main__":
    sys.exit(main())
