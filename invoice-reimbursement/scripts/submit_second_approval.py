#!/usr/bin/env python3
"""
M4: 验证第一审批状态并提交飞书第二个审批 (费用报销)  —  v0.1

从 state.json 读取 first_approval_pending 的记录 →
  - APPROVED  → 上传 PDF → 创建费用报销审批 → 写 history.json → 清理 tmp/
  - REJECTED  → 标记 rejected
  - PENDING   → 告知用户仍在审批中，不处理

Usage:
    python3 submit_second_approval.py [--reimbursement-reason TEXT] [--dry-run] [--pretty]
    python3 submit_second_approval.py --direct [--reimbursement-reason TEXT] [--dry-run] [--pretty]

Exit codes:
  0  处理成功 (或没有待处理项)
  1  API 返回错误
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


# 费用报销表单 widget ID（从实例 9021AD80-ACE3-49AD-B9EB-EFC09C7C3BED 提取）
W2_REASON       = "widget16510509704570001"   # 报销事由 textarea
W2_RELATE       = "widget17655881349660001"   # 关联审批 connect
W2_COMPANY      = "widget17786605192630001"   # 公司主体 radioV2
W2_FIELDLIST    = "widget17786605494580001"   # 费用明细 fieldList
W2_EXPENSE_TYPE = "widget17641551707250001"   # ↳ 费用类型 radioV2
W2_DATE         = "widget17641645253820001"   # ↳ 费用发生时间 date
W2_AMOUNT       = "widget17641648377750001"   # ↳ 费用金额 amount
W2_INVOICE      = "widget16510510447300001"   # ↳ 发票/账单/支付记录 attachmentV2

COMPANY_KEY     = "mp3sjs68-qm8docs1rm-0"    # 找北智职
EXPENSE_TYPE_KEY = "mifwftlx-gqbji2uoe7-0"  # 差旅费-打车费


# ---------- 查询第一审批状态 ----------

def get_first_approval_status(instance_code: str,
                               app_id: str, app_secret: str) -> str:
    """返回 APPROVED / REJECTED / PENDING (tenant token, 无需用户授权)."""
    result = call_open_api(
        "GET", "/open-apis/approval/v4/instances/" + instance_code,
        app_id=app_id, app_secret=app_secret,
    )
    status = (result.get("data") or {}).get("status", "PENDING")
    return status


# ---------- 文件上传 ----------

def upload_attachment(filepath: Path, app_id: str, app_secret: str,
                      name: str = None) -> str:
    """走 v2 endpoint (www.feishu.cn) 上传, 返回 file code."""
    return upload_file_v2(filepath, app_id=app_id, app_secret=app_secret, name=name)


# ---------- 表单组装 ----------

def _build_form(pending: list, item_file_codes: dict,
                first_instance_code: Optional[str], submit_date: str,
                reimbursement_reason: str,
                company_key: str = COMPANY_KEY,
                company_text: str = "找北智职",
                expense_type_key: str = EXPENSE_TYPE_KEY,
                expense_type_text: str = "差旅费-打车费") -> str:
    """组装费用报销表单 JSON 字符串.

    item_file_codes: {invoice_number: [code1, code2]} — 每张发票对应的 PDF codes
    每张发票在 fieldList 中占一行。
    """
    fieldlist_rows = []
    for item in pending:
        codes = item_file_codes.get(item["invoice_number"], [])
        fieldlist_rows.append([
            {"id": W2_EXPENSE_TYPE, "type": "radioV2",
             "value": expense_type_key,
             "option": {"key": expense_type_key, "text": expense_type_text}},
            {"id": W2_DATE, "type": "date",
             "value": f"{submit_date}T00:00:00+08:00"},
            {"id": W2_AMOUNT, "type": "amount", "value": item["amount"]},
            {"id": W2_INVOICE, "type": "attachmentV2", "value": codes},
        ])

    form = [
        {"id": W2_REASON,   "type": "textarea", "value": reimbursement_reason},
        {"id": W2_COMPANY,  "type": "radioV2",
         "value": company_key,
         "option": {"key": company_key, "text": company_text}},
        {"id": W2_FIELDLIST,"type": "fieldList", "value": fieldlist_rows},
    ]
    if first_instance_code:
        form.insert(1, {"id": W2_RELATE, "type": "connect", "value": [first_instance_code]})
    return json.dumps(form, ensure_ascii=False)


def _normalize_text(value: Optional[str]) -> str:
    return (value or "").strip()


def _resolve_reimbursement_reason(pending: list,
                                  reimbursement_reason: Optional[str]) -> str:
    """优先使用显式传入的报销事由，其次使用 M3 写入 state.json 的值."""
    explicit = _normalize_text(reimbursement_reason)
    if explicit:
        return explicit

    saved_reasons = {
        _normalize_text(item.get("reimbursement_reason"))
        for item in pending
        if _normalize_text(item.get("reimbursement_reason"))
    }
    if len(saved_reasons) == 1:
        return next(iter(saved_reasons))
    if len(saved_reasons) > 1:
        raise RuntimeError(
            "state.json 中存在多个不同的 reimbursement_reason, "
            "请通过 --reimbursement-reason 明确本次费用报销的报销事由。"
        )
    raise RuntimeError(
        "缺少报销事由. 提交费用报销前请先询问用户'报销事由是什么', "
        "并通过 --reimbursement-reason 传入; 如果走自动 watcher, "
        "需在 submit-1 时通过 --reimbursement-reason 写入 state.json。"
    )


# ---------- 创建审批实例 ----------

def _create_instance(body: dict, app_id: str, app_secret: str,
                     dry_run: bool = False) -> dict:
    """创建费用报销审批实例 (tenant token, 无需用户授权)."""
    if dry_run:
        return {"data": {"instance_code": "DRYRUN-INSTANCE"}}
    return call_open_api(
        "POST", "/open-apis/approval/v4/instances",
        body=body, app_id=app_id, app_secret=app_secret,
    )


# ---------- 主流程 ----------

def submit_second_approval(
    *,
    storage: Storage,
    reimbursement_reason: str = None,
    dry_run: bool = False,
) -> dict:
    """查询第一审批状态，APPROVED 则提交费用报销。返回摘要 dict."""

    state = storage.load_state()
    pending = [p for p in state.get("pending", [])
               if p.get("status") == "first_approval_pending"]

    if not pending:
        return {"ok": True, "message": "无待处理项 (no items with status=first_approval_pending).",
                "instance_code": None}

    config = storage.load_config()
    feishu = config.get("feishu") or {}
    definition_code = feishu.get("expense_definition_code",
                                 "FAB04EBA-8365-46CA-B273-2F9CF1355460")
    user_id = feishu.get("user_id")
    dept_id = feishu.get("department_id")
    app_id = feishu.get("app_id")
    app_secret = feishu.get("app_secret")
    if not user_id:
        raise RuntimeError(
            "config.json 缺少 feishu.user_id. 请在 config.json 中添加飞书配置。"
        )
    if not dry_run and (not app_id or not app_secret):
        raise RuntimeError(
            "config.json 缺少 feishu.app_id / app_secret (v2 上传需要)."
        )

    explicit_reimbursement_reason = _normalize_text(reimbursement_reason)
    if explicit_reimbursement_reason and not dry_run:
        for item in pending:
            item["reimbursement_reason"] = explicit_reimbursement_reason
        storage.save_state(state)

    # 所有 pending 项共用同一个第一审批实例 code
    first_instance_code = pending[0].get("first_approval_id")
    if not first_instance_code:
        return {"ok": False, "message": "state.json 中 first_approval_id 为空，无法验证状态。"}

    # 1. 查询第一审批状态
    if dry_run:
        first_status = "APPROVED"  # dry-run 假设通过
    else:
        first_status = get_first_approval_status(first_instance_code,
                                                  app_id=app_id, app_secret=app_secret)

    result_summary = {"first_approval_status": first_status, "first_instance_code": first_instance_code}

    if first_status == "REJECTED":
        for item in pending:
            item["status"] = "rejected"
            item["reject_reason"] = "first_approval_rejected"
        storage.save_state(state)
        result_summary.update({"ok": True, "action": "marked_rejected", "items": len(pending)})
        return result_summary

    if first_status == "PENDING":
        result_summary.update({
            "ok": True,
            "action": "still_pending",
            "message": "第一审批仍在审批中，请等待飞书通知后再次触发。",
        })
        return result_summary

    # APPROVED → 上传 PDF 并创建费用报销
    reimbursement_reason_text = _resolve_reimbursement_reason(
        pending, explicit_reimbursement_reason
    )
    today = date.today().isoformat()
    item_file_codes: dict = {}
    upload_errors = []

    for item in pending:
        codes = []
        for pdf_key in ("invoice_pdf", "trip_pdf"):
            path_str = item.get(pdf_key)
            if not path_str:
                continue
            fp = Path(path_str)
            if not fp.exists():
                upload_errors.append(f"PDF 缺失: {fp}")
                continue
            if dry_run:
                codes.append(f"DRYRUN-{fp.name}")
            else:
                try:
                    code = upload_attachment(fp, app_id, app_secret, fp.name)
                    codes.append(code)
                except (RuntimeError, UploadError) as e:
                    upload_errors.append(f"上传失败 {fp.name}: {e}")
        item_file_codes[item["invoice_number"]] = codes

    if upload_errors:
        return {"ok": False, "message": "文件上传失败", "errors": upload_errors}

    form_json = _build_form(
        pending, item_file_codes, first_instance_code, today,
        reimbursement_reason_text
    )

    body = {
        "approval_code": definition_code,
        "open_id": user_id,
        "form": form_json,
    }
    if dept_id:
        body["department_id"] = dept_id

    api_result = _create_instance(body, app_id=app_id, app_secret=app_secret, dry_run=dry_run)

    if dry_run:
        result_summary.update({"ok": True, "dry_run": True, "form_body": body})
        return result_summary

    instance_code = (api_result.get("data") or {}).get("instance_code")
    if not instance_code:
        return {"ok": False, "message": "费用报销审批创建未返回 instance_code",
                "api_response": api_result}

    # 写 history.json + 清理 tmp/ + 从 pending 移除
    completed_invoice_numbers = set()
    for item in pending:
        storage.history_append({"invoice_number": item["invoice_number"],
                                "completed_at": today,
                                "first_approval_id": first_instance_code,
                                "second_approval_id": instance_code,
                                "reimbursement_reason": reimbursement_reason_text,
                                "amount": item["amount"]})
        completed_invoice_numbers.add(item["invoice_number"])
        for pdf_key in ("invoice_pdf", "trip_pdf"):
            path_str = item.get(pdf_key)
            if path_str:
                fp = Path(path_str)
                if fp.exists():
                    try:
                        fp.unlink()
                    except OSError:
                        pass

    # 从 pending 中移除已完成项 (而不是设 status=completed 留在 pending 里)
    state["pending"] = [p for p in state.get("pending", [])
                        if p.get("invoice_number") not in completed_invoice_numbers]
    storage.save_state(state)

    result_summary.update({
        "ok": True,
        "submitter_version": SUBMITTER_VERSION,
        "second_instance_code": instance_code,
        "items_completed": len(pending),
        "total_amount": round(sum(p["amount"] for p in pending), 2),
        "reimbursement_reason": reimbursement_reason_text,
    })
    return result_summary


def _expense_form_config(feishu: dict) -> tuple[str, str, str, str]:
    entity = feishu.get("reimburse_entity") or feishu.get("purchase_entity") or {}
    expense_type = feishu.get("expense_type") or {}
    return (
        entity.get("key") or COMPANY_KEY,
        entity.get("text") or "找北智职",
        expense_type.get("key") or EXPENSE_TYPE_KEY,
        expense_type.get("text") or "差旅费-打车费",
    )


def submit_expense_approval_direct(
    *,
    storage: Storage,
    reimbursement_reason: str = None,
    dry_run: bool = False,
) -> dict:
    """无第一审批时，直接把 parsed 项提交到费用报销审批."""
    state = storage.load_state()
    pending = [p for p in state.get("pending", []) if p.get("status") == "parsed"]

    if not pending:
        return {"ok": True, "message": "无待提交项 (no pending items with status=parsed).",
                "instance_code": None}

    reimbursement_reason_text = _resolve_reimbursement_reason(pending, reimbursement_reason)

    config = storage.load_config()
    feishu = config.get("feishu") or {}
    definition_code = feishu.get("expense_definition_code",
                                 "FAB04EBA-8365-46CA-B273-2F9CF1355460")
    user_id = feishu.get("user_id")
    dept_id = feishu.get("department_id")
    app_id = feishu.get("app_id")
    app_secret = feishu.get("app_secret")
    if not user_id:
        raise RuntimeError("config.json 缺少 feishu.user_id. 请在 config.json 中添加飞书配置。")
    if not dry_run and (not app_id or not app_secret):
        raise RuntimeError("config.json 缺少 feishu.app_id / app_secret (v2 上传需要).")

    company_key, company_text, expense_type_key, expense_type_text = _expense_form_config(feishu)

    today = date.today().isoformat()
    item_file_codes: dict = {}
    upload_errors = []

    for item in pending:
        codes = []
        for pdf_key in ("invoice_pdf", "trip_pdf"):
            path_str = item.get(pdf_key)
            if not path_str:
                continue
            fp = Path(path_str)
            if not fp.exists():
                upload_errors.append(f"PDF 缺失: {fp}")
                continue
            if dry_run:
                codes.append(f"DRYRUN-{fp.name}")
            else:
                try:
                    code = upload_attachment(fp, app_id, app_secret, fp.name)
                    codes.append(code)
                except (RuntimeError, UploadError) as e:
                    upload_errors.append(f"上传失败 {fp.name}: {e}")
        item_file_codes[item["invoice_number"]] = codes

    if upload_errors:
        return {"ok": False, "message": "文件上传失败", "errors": upload_errors}

    form_json = _build_form(
        pending, item_file_codes, None, today, reimbursement_reason_text,
        company_key, company_text, expense_type_key, expense_type_text
    )

    body = {
        "approval_code": definition_code,
        "open_id": user_id,
        "form": form_json,
    }
    if dept_id:
        body["department_id"] = dept_id

    api_result = _create_instance(body, app_id=app_id, app_secret=app_secret, dry_run=dry_run)

    if dry_run:
        return {"ok": True, "dry_run": True, "direct": True, "form_body": body}

    instance_code = (api_result.get("data") or {}).get("instance_code")
    if not instance_code:
        return {"ok": False, "message": "费用报销审批创建未返回 instance_code",
                "api_response": api_result}

    completed_invoice_numbers = set()
    for item in pending:
        storage.history_append({"invoice_number": item["invoice_number"],
                                "completed_at": today,
                                "second_approval_id": instance_code,
                                "reimbursement_reason": reimbursement_reason_text,
                                "amount": item["amount"]})
        completed_invoice_numbers.add(item["invoice_number"])
        for pdf_key in ("invoice_pdf", "trip_pdf"):
            path_str = item.get(pdf_key)
            if path_str:
                fp = Path(path_str)
                if fp.exists():
                    try:
                        fp.unlink()
                    except OSError:
                        pass

    state["pending"] = [p for p in state.get("pending", [])
                        if p.get("invoice_number") not in completed_invoice_numbers]
    storage.save_state(state)

    return {
        "ok": True,
        "direct": True,
        "submitter_version": SUBMITTER_VERSION,
        "second_instance_code": instance_code,
        "items_completed": len(pending),
        "total_amount": round(sum(p["amount"] for p in pending), 2),
        "reimbursement_reason": reimbursement_reason_text,
    }


# ---------- CLI ----------

def main():
    ap = argparse.ArgumentParser(
        description="M4: 验证第一审批并提交飞书费用报销 (v0.1).",
    )
    ap.add_argument("--dry-run", action="store_true",
                    help="跳过真实 API 调用，用 APPROVED 假设预览表单。")
    ap.add_argument("--reimbursement-reason", "--expense-reason",
                    dest="reimbursement_reason", default=None,
                    help="报销事由文本 (用于飞书费用报销审批的'报销事由'字段)")
    ap.add_argument("--direct", action="store_true",
                    help="无第一审批时，直接提交费用报销。")
    ap.add_argument("--pretty", action="store_true")
    args = ap.parse_args()

    storage = Storage()

    try:
        if args.direct:
            summary = submit_expense_approval_direct(
                storage=storage,
                reimbursement_reason=args.reimbursement_reason,
                dry_run=args.dry_run,
            )
        else:
            summary = submit_second_approval(
                storage=storage,
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
