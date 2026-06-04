#!/usr/bin/env python3
"""
M3: 提交飞书第一个审批 (采购申请)  —  v0.1

从 state.json 读取已解析的待报销项 → 上传 PDF 附件 → 组装表单 JSON → 创建审批实例 → 更新状态.

设计原则:
  - 所有 PDF (发票 + 行程单) 一起上传, 合并为一个审批实例
  - 通过 subprocess 调 lark-cli, 不自己管理 token
  - 支持 --dry-run 预览表单不真提交

Usage:
    python3 submit_first_approval.py [--reason TEXT] [--reimbursement-reason TEXT] [--dry-run] [--pretty]

Exit codes:
  0  提交成功 (或没有待提交项)
  1  上传 / 创建实例 API 返回错误
  2  配置缺失 / 状态文件不存在 / lark-cli 未安装
"""

SUBMITTER_VERSION = "0.1"

import sys
import json
import argparse
from datetime import date
from pathlib import Path
from typing import Optional

sys.path.insert(0, str(Path(__file__).resolve().parent))
from storage import Storage  # noqa: E402
from feishu_upload import upload_file_v2, call_open_api, UploadError  # noqa: E402


# 采购申请表单 widget ID 常量 (提取自已通过的实例 D8DC43CC-6331-45CB-A4A4-838B446ED625)
W_REASON = "widget16510608596030001"
W_ENTITY = "widget17786355991160001"
W_DATE = "widget16510608918180001"
W_FIELDLIST = "widget16510609006710001"
W_ITEM_NAME = "widget16510609105290001"
W_SPEC = "widget16510609161480001"
W_QTY = "widget16510609215120001"
W_AMOUNT = "widget16510609358260001"
W_NOTE = "widget17638204676490001"
W_ATTACHMENT = "widget16510609389860001"


# ---------- 文件上传 ----------

def upload_attachment(filepath: Path, app_id: str, app_secret: str,
                      name: str = None) -> str:
    """上传 PDF 到飞书审批 v2 endpoint, 返回 file code (UUID).

    不走 lark-cli 因为 1.0.32 只有 v4 endpoint, 返回的 code 让 attachmentV2
    显示成 "unknown-file"; v2 endpoint 走 www.feishu.cn 域, 显示正常.
    """
    return upload_file_v2(filepath, app_id=app_id, app_secret=app_secret, name=name)


# ---------- 表单组装 ----------

def generate_reason_draft(pending: list) -> str:
    """根据行程单数据生成采购事由草稿，供用户在提交前确认补充."""
    parts = []
    for item in pending:
        for t in item.get("trips", []):
            date_str = t.get("trip_date", "")
            origin = t.get("origin", "?")
            dest = t.get("destination", "?")
            parts.append(f"{date_str} {origin}→{dest}")
    if parts:
        return "打车报销：" + "；".join(parts)
    return "高德打车费报销"


def _build_form(pending: list, file_codes: list, reason: str,
                entity_key: str, submit_date: str) -> str:
    """组装采购申请表单 JSON 字符串.

    每张发票对应 fieldList 中的一行（数量固定为 1），附件统一放在顶层 attachmentV2。
    """
    # 每张发票一行明细，数量固定 1
    # 注：W_NOTE ("说明 1") 是只读 text 提示 widget，提交后会被模板默认值覆盖，故不提交。
    fieldlist_rows = []
    for item in pending:
        fieldlist_rows.append([
            {"id": W_ITEM_NAME, "type": "input", "value": "打车费"},
            {"id": W_SPEC, "type": "input", "value": "无"},
            {"id": W_QTY, "type": "number", "value": 1},
            {"id": W_AMOUNT, "type": "amount", "value": item["amount"]},
        ])

    form = [
        {"id": W_REASON, "type": "textarea", "value": reason},
        {"id": W_ENTITY, "type": "radioV2", "value": entity_key},
        {"id": W_DATE, "type": "date",
         "value": f"{submit_date}T00:00:00+08:00"},
        {"id": W_FIELDLIST, "type": "fieldList", "value": fieldlist_rows},
        {"id": W_ATTACHMENT, "type": "attachmentV2", "value": file_codes},
    ]
    return json.dumps(form, ensure_ascii=False)


# ---------- 创建审批实例 ----------

def _create_instance(body: dict, app_id: str, app_secret: str,
                     dry_run: bool = False) -> dict:
    """调用审批实例创建接口, 返回 API 响应 (tenant token, 无需用户授权)."""
    if dry_run:
        return {"data": {"instance_code": "DRYRUN-INSTANCE"}}
    return call_open_api(
        "POST", "/open-apis/approval/v4/instances",
        body=body, app_id=app_id, app_secret=app_secret,
    )


# ---------- 主流程 ----------

def submit_first_approval(
    *,
    storage: Storage,
    reason: str = None,
    reimbursement_reason: str = None,
    dry_run: bool = False,
) -> dict:
    """上传附件并提交采购申请审批. 返回摘要 dict."""

    # 1. 读待提交项
    state = storage.load_state()
    pending = [p for p in state.get("pending", []) if p.get("status") == "parsed"]
    if not pending:
        return {"ok": True, "message": "无待提交项 (no pending items with status=parsed).",
                "instance_code": None}

    # 2. 读飞书配置
    config = storage.load_config()
    feishu = config.get("feishu") or {}
    definition_code = feishu.get("definition_code")
    user_id = feishu.get("user_id")
    entity_key = (feishu.get("purchase_entity") or {}).get("key")
    app_id = feishu.get("app_id")
    app_secret = feishu.get("app_secret")
    if not definition_code or not user_id or not entity_key:
        raise RuntimeError(
            "config.json 缺少 feishu 节 (definition_code / user_id / purchase_entity.key). "
            "请在 config.json 中添加飞书审批配置。参见 skill/assets/rules.example.json 中 feishu 段。"
        )
    if not dry_run and (not app_id or not app_secret):
        raise RuntimeError(
            "config.json 缺少 feishu.app_id / app_secret (v2 上传需要). "
            "去飞书开发者后台拷贝 App Secret 写入 config.json feishu 节."
        )
    dept_id = feishu.get("department_id")

    reason_text = reason or feishu.get("default_reason", "高德打车费报销")
    reimbursement_reason_text = (reimbursement_reason or "").strip()
    if not reimbursement_reason_text and not dry_run:
        raise RuntimeError(
            "缺少报销事由. 提交 M3 前请先询问用户'报销事由是什么', "
            "并通过 --reimbursement-reason 传入; 该文本会写入 state.json, "
            "供 watcher 自动提交 M4 费用报销时填入飞书'报销事由'字段。"
        )

    # 3. 上传所有 PDF (v2 endpoint)
    file_codes = []
    upload_errors = []
    for item in pending:
        for pdf_key in ("invoice_pdf", "trip_pdf"):
            path_str = item.get(pdf_key)
            if not path_str:
                continue
            fp = Path(path_str)
            if not fp.exists():
                upload_errors.append(f"PDF 缺失: {fp}")
                continue
            if dry_run:
                file_codes.append(f"DRYRUN-{fp.name}")
            else:
                try:
                    code = upload_attachment(fp, app_id, app_secret, fp.name)
                    file_codes.append(code)
                except (RuntimeError, UploadError) as e:
                    upload_errors.append(f"上传失败 {fp.name}: {e}")

    if upload_errors:
        return {"ok": False, "message": "文件上传失败", "errors": upload_errors}

    # 4. 组装表单
    today = date.today().isoformat()
    form_json = _build_form(pending, file_codes, reason_text, entity_key, today)

    # 5. 创建审批实例
    body = {
        "approval_code": definition_code,
        "open_id": user_id,
        "form": form_json,
    }
    if dept_id:
        body["department_id"] = dept_id

    result = _create_instance(body, app_id=app_id, app_secret=app_secret, dry_run=dry_run)

    if dry_run:
        return {"ok": True, "dry_run": True, "form_body": body}

    instance_code = (result.get("data") or {}).get("instance_code")
    if not instance_code:
        return {"ok": False, "message": "审批创建未返回 instance_code",
                "api_response": result}

    # 6. 更新状态
    for item in pending:
        item["first_approval_id"] = instance_code
        item["status"] = "first_approval_pending"
        item["submitted_at"] = today
        item["reimbursement_reason"] = reimbursement_reason_text
    storage.save_state(state)

    # 7. spawn 后台 watcher: 1 小时轮询审批状态, 通过即自动触发 M4
    watcher_pid = _spawn_watcher(storage)

    return {
        "ok": True,
        "submitter_version": SUBMITTER_VERSION,
        "instance_code": instance_code,
        "items_submitted": len(pending),
        "total_amount": round(sum(p["amount"] for p in pending), 2),
        "reimbursement_reason": reimbursement_reason_text,
        "file_codes": file_codes,
        "watcher_pid": watcher_pid,
    }


# ---------- 后台 watcher ----------

def _spawn_watcher(storage) -> Optional[int]:
    """提交完成后立即启动后台守护. 返回 watcher 的 PID; 失败返回 None.

    通过 subprocess.Popen + start_new_session=True detach 父进程,
    Claude Code 会话结束后 watcher 仍在跑.
    """
    import subprocess
    watcher_script = Path(__file__).resolve().parent / "approval_watcher.py"
    if not watcher_script.exists():
        return None
    log_path = storage.base_dir / "watcher.log"
    try:
        proc = subprocess.Popen(
            [sys.executable, str(watcher_script)],
            stdout=open(log_path, "ab"),
            stderr=subprocess.STDOUT,
            start_new_session=True,
            close_fds=True,
        )
        return proc.pid
    except OSError:
        return None


# ---------- CLI ----------

def main():
    ap = argparse.ArgumentParser(
        description="M3: 上传 PDF 附件并提交飞书采购申请审批 (v0.1).",
    )
    ap.add_argument("--reason", default=None,
                    help="采购事由文本 (可选, 不指定则用 config 默认值)")
    ap.add_argument("--reimbursement-reason", "--expense-reason",
                    dest="reimbursement_reason", default=None,
                    help="报销事由文本 (必填, 会写入 state.json 并用于 M4 费用报销审批)")
    ap.add_argument("--generate-reason-draft", action="store_true",
                    help="根据 state.json 行程数据生成采购事由草稿并打印, 不提交.")
    ap.add_argument("--dry-run", action="store_true",
                    help="预览表单 JSON, 不上传也不真提交.")
    ap.add_argument("--pretty", action="store_true")
    args = ap.parse_args()

    storage = Storage()

    if args.generate_reason_draft:
        state = storage.load_state()
        pending = [p for p in state.get("pending", []) if p.get("status") == "parsed"]
        draft = generate_reason_draft(pending)
        print(draft)
        return

    try:
        summary = submit_first_approval(
            storage=storage,
            reason=args.reason,
            reimbursement_reason=args.reimbursement_reason,
            dry_run=args.dry_run,
        )
    except RuntimeError as e:
        print(f"[ERROR] {e}", file=sys.stderr)
        sys.exit(2)

    json.dump(summary, sys.stdout, ensure_ascii=False,
              indent=2 if args.pretty else None)
    sys.stdout.write("\n")

    if not summary.get("ok"):
        sys.exit(1)


if __name__ == "__main__":
    main()
