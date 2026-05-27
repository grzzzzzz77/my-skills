#!/usr/bin/env python3
"""
高德发票 ↔ 行程单配对工具  —  v0.1

输入: 一个或多个 PDF 路径，或包含 PDF 的目录
输出: stdout 上的 JSON

  {
    "pairs": [
      {
        "invoice": {...完整发票 JSON...},
        "trip":    {...完整行程单 JSON...},
        "match_key": "amount=23.36",
        "warnings": []
      }
    ],
    "unpaired_invoices": [...],
    "unpaired_trips": [...],
    "parse_errors": [
      {"pdf": "...", "kind": "invoice|trip|unknown", "error": "..."}
    ]
  }

配对依据: 发票"价税合计"== 行程单"合计金额"（精确到两位小数）。
不依赖文件名，避免邮件附件命名变更带来风险。

Usage:
    python3 pair_pdfs.py <pdf_or_dir> [<more_pdfs>...] [--pretty]
"""

PAIRER_VERSION = "0.1"

import sys
import json
import argparse
import unicodedata
from pathlib import Path

# 同目录下的 parser 模块
sys.path.insert(0, str(Path(__file__).resolve().parent))

try:
    import pdfplumber
except ImportError:
    print("[ERROR] pdfplumber not installed. Run: pip3 install pdfplumber", file=sys.stderr)
    sys.exit(2)

from parse_invoices import parse_invoice, ParseError as InvoiceParseError
from parse_trips import parse_trip, ParseError as TripParseError


def _detect_kind(pdf_path: Path) -> str:
    """Returns 'invoice' / 'trip' / 'unknown' by inspecting first page text."""
    try:
        with pdfplumber.open(pdf_path) as pdf:
            text = (pdf.pages[0].extract_text() or "") if pdf.pages else ""
    except Exception:
        return "unknown"
    # NFKC 把康熙部首等兼容字符映射回常规 CJK（部分 PDF 把"子"渲染为 U+2F26）
    text = unicodedata.normalize("NFKC", text)
    if "电子发票" in text and ("旅客运输服务" in text or "客运服务费" in text):
        return "invoice"
    if "高德地图" in text or "AMAP ITINERARY" in text:
        return "trip"
    return "unknown"


def _amount_key(amount) -> str:
    """规范化金额: 两位小数字符串, 避免 21.8 vs 21.80 之类的比较问题."""
    try:
        return f"{float(amount):.2f}"
    except (TypeError, ValueError):
        return ""


def collect_pdfs(paths: list) -> list:
    """展开目录, 返回所有 .pdf 文件路径 (扩展名比较 case-insensitive)."""
    out = []
    for p in paths:
        p = Path(p)
        if p.is_dir():
            out.extend(sorted(
                f for f in p.iterdir()
                if f.is_file() and f.suffix.lower() == ".pdf"
            ))
        elif p.is_file() and p.suffix.lower() == ".pdf":
            out.append(p)
        else:
            print(f"[WARN] Ignoring non-PDF / missing path: {p}", file=sys.stderr)
    return out


def pair_pdfs(paths: list) -> dict:
    invoices = []
    trips = []
    errors = []

    for pdf in collect_pdfs(paths):
        kind = _detect_kind(pdf)
        if kind == "invoice":
            try:
                invoices.append(parse_invoice(pdf))
            except InvoiceParseError as e:
                errors.append({"pdf": str(pdf), "kind": "invoice", "error": str(e)})
        elif kind == "trip":
            try:
                trips.append(parse_trip(pdf))
            except TripParseError as e:
                errors.append({"pdf": str(pdf), "kind": "trip", "error": str(e)})
        else:
            errors.append({
                "pdf": str(pdf),
                "kind": "unknown",
                "error": "Cannot detect type (not a 高德 invoice nor trip itinerary).",
            })

    # 按金额配对
    unpaired_invoices = list(invoices)
    unpaired_trips = list(trips)
    pairs = []

    # 用金额做 key, 处理同金额多张的情况
    trips_by_amount = {}
    for t in trips:
        k = _amount_key(t.get("total_amount"))
        trips_by_amount.setdefault(k, []).append(t)

    for inv in invoices:
        k = _amount_key(inv.get("total_amount"))
        candidates = trips_by_amount.get(k, [])
        if not candidates:
            continue  # 留在 unpaired_invoices
        warnings = []
        if len(candidates) > 1:
            warnings.append(
                f"Multiple trips with amount {k}: ambiguous match, used first by申请时间."
            )
            # 候选按 request_date 排序, 取最早的
            candidates.sort(key=lambda t: t.get("request_date", ""))
        trip = candidates.pop(0)
        if not candidates:
            del trips_by_amount[k]
        pairs.append({
            "invoice": inv,
            "trip": trip,
            "match_key": f"amount={k}",
            "warnings": warnings,
        })
        unpaired_invoices.remove(inv)
        unpaired_trips.remove(trip)

    return {
        "pairer_version": PAIRER_VERSION,
        "pairs": pairs,
        "unpaired_invoices": unpaired_invoices,
        "unpaired_trips": unpaired_trips,
        "parse_errors": errors,
    }


def main():
    ap = argparse.ArgumentParser(
        description="Pair 高德 invoice PDFs with trip itinerary PDFs by total_amount (v0.1).",
    )
    ap.add_argument("paths", nargs="+", type=Path, help="PDF files or directories")
    ap.add_argument("--pretty", action="store_true")
    args = ap.parse_args()

    result = pair_pdfs(args.paths)
    json.dump(result, sys.stdout, ensure_ascii=False, indent=2 if args.pretty else None)
    sys.stdout.write("\n")

    # 退出码反映结果: 0=有配对成功, 1=没有任何配对, 2=有解析错误
    if result["parse_errors"] and not result["pairs"]:
        sys.exit(2)
    if not result["pairs"]:
        sys.exit(1)


if __name__ == "__main__":
    main()
