#!/usr/bin/env python3
"""
M2 编排器: PDF 解析 + 配对 + 规则筛选 + 写入 state.json + history 去重  —  v0.1

流水线 (顺序很重要):

  1. 读 ~/.invoice-reimbursement/rules.json (规则配置, _doc 字段已剥离)
  2. 扫描 PDF 目录, 调 pair_pdfs 配对 + 解析
  3. **先**用 history.json + 现有 state.pending[] 过滤已存在的发票号
     - 命中 history       → 直接进 skipped[]（不参与规则判定，避免 F2 单日累计误伤）
     - 命中 pending 非终态 → 直接进 skipped[]（防重复运行 parse 重复入库）
  4. 剩余 pair 才跑 rules.check_pair + check_batch (F2)
  5. 通过的 → state.pending[], 含 status="parsed" 等元数据
     被跳过的 → state.skipped[], 含 skip_reason 和 skipped_at
  6. **额外**: unpaired_invoices / unpaired_trips / parse_errors 也都追加进 skipped[]
              （spec §6.3 要求 M2 配对失败入 skipped[]）
  7. 一次性 save_state, 不做中间小写

state.json 的写入只在 M2 这里发生; M3 / M4 通过 update_pending_status 更新 status.

Usage:
    python3 parse_and_filter.py [--dir <storage-dir>] [--pdf-dir <pdf-dir>] [--pretty]

Exit codes:
  0  正常完成且数据健康 (所有 PDF 都被配对+判定)
  1  正常完成但有数据问题: 解析错误 / 未配对 / 全部被 skip
  2  前置配置/环境错误: rules.json 缺失或损坏 / PDF 目录不存在
"""

ORCHESTRATOR_VERSION = "0.1"

import sys
import json
import argparse
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from storage import Storage  # noqa: E402
from pair_pdfs import pair_pdfs  # noqa: E402
from rules import check_pair, check_batch, _strip_doc  # noqa: E402


TERMINAL_STATUSES = {"completed", "rejected"}


def _now_iso() -> str:
    return datetime.now().strftime("%Y-%m-%dT%H:%M:%S")


def _split_pickup_time(pickup_time):
    """'YYYY-MM-DD HH:MM' → (date, time). 任一缺失返回 None."""
    if not pickup_time or " " not in pickup_time:
        return (None, None)
    parts = pickup_time.split(" ", 1)
    return (parts[0], parts[1])


def parse_and_filter(*, storage: Storage, pdf_dir: Path) -> dict:
    """
    Orchestrate the full M2 pipeline. Returns summary dict.
    Writes to state.json once at the end (single atomic write).
    """
    # 1. Load rules - 配置层错误 → RuntimeError (调用者映射 exit 2)
    try:
        raw_rules = storage.load_rules()
    except FileNotFoundError as e:
        raise RuntimeError(
            f"Rules file missing: {storage.rules_path}. 先跑 `cli init`."
        ) from e
    except json.JSONDecodeError as e:
        raise RuntimeError(
            f"Rules file {storage.rules_path} 不是合法 JSON: {e}"
        ) from e
    rules = _strip_doc(raw_rules)

    # 2. PDF 目录校验 - 同样视为前置错误
    if not pdf_dir.exists():
        raise RuntimeError(f"PDF directory not found: {pdf_dir}")

    # 3. 配对
    pair_result = pair_pdfs([pdf_dir])

    # 4. 预加载 history + state, 一次 IO 各一次
    history = storage.load_history()
    history_numbers = {r.get("invoice_number") for r in history.get("processed", []) if r.get("invoice_number")}
    state = storage.load_state()
    pending_non_terminal = {
        r.get("invoice_number")
        for r in state.get("pending", [])
        if r.get("invoice_number") and r.get("status") not in TERMINAL_STATUSES
    }

    now = _now_iso()
    pre_filtered = []  # [(pair, skip_reason)]
    surviving = []

    # 5. 先按 history / pending 去重 (在规则判定之前!)
    for pair in pair_result["pairs"]:
        inv_no = pair["invoice"].get("invoice_number", "")
        if inv_no and inv_no in history_numbers:
            pre_filtered.append((pair, f"history_dedup: 发票号 {inv_no} 已在 history.json 中（曾完整走完流程）"))
        elif inv_no and inv_no in pending_non_terminal:
            pre_filtered.append((pair, f"already_pending: 发票号 {inv_no} 已在 state.pending[] 中且 status 未到 completed/rejected"))
        else:
            surviving.append(pair)

    # 6. 仅对 surviving 跑规则
    for p in surviving:
        p["verdict"] = check_pair(p["invoice"], p["trip"], rules)
    batch_verdict = check_batch(surviving, rules)

    # 7. summary 框架
    summary = {
        "orchestrator_version": ORCHESTRATOR_VERSION,
        "pdf_dir": str(pdf_dir),
        "rules_file": str(storage.rules_path),
        "paired": len(pair_result["pairs"]),
        "passed": 0,
        "skipped_by_history": len(pre_filtered),
        "skipped_by_rules": 0,
        "skipped_by_pairing": 0,
        "skipped_by_parse_error": 0,
        "batch_verdict": batch_verdict,
        "details": {
            "passed_invoices": [],
            "skipped_invoices": [],
            "unpaired_invoice_pdfs": [],
            "unpaired_trip_pdfs": [],
            "parse_error_details": [],
        },
    }

    # 7a. history / pending 重复 → skipped[]
    for pair, reason in pre_filtered:
        inv = pair["invoice"]; trp = pair["trip"]
        state["skipped"].append({
            "invoice_number": inv.get("invoice_number"),
            "invoice_pdf": inv.get("source_pdf"),
            "trip_pdf": trp.get("source_pdf"),
            "skip_reason": reason,
            "skipped_at": now,
        })
        summary["details"]["skipped_invoices"].append({
            "invoice_number": inv.get("invoice_number"),
            "reason": reason,
        })

    # 7b. 规则判定后的 surviving 分流
    for pair in surviving:
        invoice = pair["invoice"]
        trip = pair["trip"]
        verdict = pair["verdict"]
        invoice_number = invoice.get("invoice_number", "")

        if not verdict["passed"]:
            reason = "; ".join(verdict["skip_reasons"])
            state["skipped"].append({
                "invoice_number": invoice_number,
                "invoice_pdf": invoice.get("source_pdf"),
                "trip_pdf": trip.get("source_pdf"),
                "skip_reason": reason,
                "skipped_at": now,
            })
            summary["skipped_by_rules"] += 1
            summary["details"]["skipped_invoices"].append({
                "invoice_number": invoice_number,
                "reason": reason,
            })
            continue

        # 通过 → 写 pending. 按 spec §6.2 字段命名 (trip_date / trip_start_time)
        trips_list = trip.get("trips", [])
        spec_trips = []
        for t in trips_list:
            date_part, time_part = _split_pickup_time(t.get("pickup_time"))
            spec_trips.append({
                "trip_date": date_part,
                "trip_start_time": time_part,
                "origin": t.get("origin"),
                "destination": t.get("destination"),
                "city": t.get("city"),
                "amount": t.get("amount"),
            })
        record = {
            "invoice_number": invoice_number,
            "invoice_date": invoice.get("invoice_date"),
            "amount": invoice.get("total_amount"),
            "trip_count": trip.get("trip_count", len(trips_list)),
            "trips": spec_trips,
            "invoice_pdf": invoice.get("source_pdf"),
            "trip_pdf": trip.get("source_pdf"),
            "first_approval_id": None,
            "second_approval_id": None,
            "status": "parsed",
            "parsed_at": now,
        }
        state["pending"].append(record)
        summary["passed"] += 1
        summary["details"]["passed_invoices"].append({
            "invoice_number": invoice_number,
            "amount": invoice.get("total_amount"),
        })

    # 7c. unpaired 和 parse_errors 也入 skipped[] (spec §6.3)
    for inv in pair_result["unpaired_invoices"]:
        reason = f"pairing_failed: 找不到金额匹配的行程单 (amount={inv.get('total_amount')})"
        state["skipped"].append({
            "invoice_number": inv.get("invoice_number"),
            "invoice_pdf": inv.get("source_pdf"),
            "trip_pdf": None,
            "skip_reason": reason,
            "skipped_at": now,
        })
        summary["skipped_by_pairing"] += 1
        summary["details"]["unpaired_invoice_pdfs"].append(inv.get("source_pdf"))
        summary["details"]["skipped_invoices"].append({
            "invoice_number": inv.get("invoice_number"),
            "reason": reason,
        })

    for tr in pair_result["unpaired_trips"]:
        reason = f"pairing_failed: 找不到金额匹配的发票 (amount={tr.get('total_amount')})"
        state["skipped"].append({
            "invoice_number": None,
            "invoice_pdf": None,
            "trip_pdf": tr.get("source_pdf"),
            "skip_reason": reason,
            "skipped_at": now,
        })
        summary["skipped_by_pairing"] += 1
        summary["details"]["unpaired_trip_pdfs"].append(tr.get("source_pdf"))
        summary["details"]["skipped_invoices"].append({
            "invoice_number": None,
            "reason": reason,
        })

    for err in pair_result["parse_errors"]:
        kind = err.get("kind", "?")
        state["skipped"].append({
            "invoice_number": None,
            "invoice_pdf": err.get("pdf") if kind == "invoice" else None,
            "trip_pdf": err.get("pdf") if kind == "trip" else None,
            "skip_reason": f"parse_error[{kind}]: {err.get('error')}",
            "skipped_at": now,
        })
        summary["skipped_by_parse_error"] += 1
        summary["details"]["parse_error_details"].append(err)

    # 8. 一次原子写
    storage.save_state(state)
    return summary


def _has_data_issues(summary: dict) -> bool:
    return bool(
        summary["skipped_by_parse_error"]
        or summary["skipped_by_pairing"]
        or summary["skipped_by_rules"]
        or summary["skipped_by_history"]
    ) and summary["passed"] == 0  # 全部失败时报 1; 有部分通过算正常


def main():
    ap = argparse.ArgumentParser(
        description="M2 orchestrator: parse + filter + write state.json (v0.1, 高德 only).",
    )
    ap.add_argument("--dir", default=None,
                    help="Storage dir override (default: $INVOICE_REIMBURSEMENT_DIR or ~/.invoice-reimbursement)")
    ap.add_argument("--pdf-dir", default=None,
                    help="PDF dir to scan (default: <storage>/tmp/)")
    ap.add_argument("--pretty", action="store_true")
    args = ap.parse_args()

    storage = Storage(base_dir=Path(args.dir) if args.dir else None)
    pdf_dir = Path(args.pdf_dir) if args.pdf_dir else storage.tmp_dir

    try:
        summary = parse_and_filter(storage=storage, pdf_dir=pdf_dir)
    except RuntimeError as e:
        print(f"[ERROR] {e}", file=sys.stderr)
        sys.exit(2)

    json.dump(summary, sys.stdout, ensure_ascii=False, indent=2 if args.pretty else None)
    sys.stdout.write("\n")

    # exit 1 仅当: 一条都没过 但有数据 OR 有解析错误
    if summary["skipped_by_parse_error"]:
        sys.exit(1)
    if summary["paired"] == 0 and (summary["details"]["unpaired_invoice_pdfs"] or summary["details"]["unpaired_trip_pdfs"]):
        sys.exit(1)


if __name__ == "__main__":
    main()
