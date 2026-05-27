#!/usr/bin/env python3
"""
高德打车电子行程单解析器  —  v0.1

仅支持高德地图打车 (AMAP ITINERARY) 的电子行程单。
不支持: 其他平台（滴滴、首汽、出租车、神州专车）的行程单。

Usage:
    python3 parse_trips.py <trip_pdf_path> [--pretty]

Output (JSON to stdout):
    {
      "parser_version": "0.1",
      "platform": "gaode",
      "source_pdf": "...",
      "request_date": "YYYY-MM-DD",
      "trip_window_start": "YYYY-MM-DD HH:MM",
      "trip_window_end":   "YYYY-MM-DD HH:MM",
      "passenger_phone": "...",
      "trip_count": N,
      "total_amount": ...,                # 行程合计金额, 必须等于发票价税合计
      "trips": [
        {
          "index": 1,
          "service_provider": "...",
          "car_type": "...",
          "pickup_time": "YYYY-MM-DD HH:MM",
          "city": "...",
          "origin": "...",
          "destination": "...",
          "amount": ...
        }
      ]
    }

字段提取规范见 skill/references/sample-analysis.md §2。
"""

PARSER_VERSION = "0.1"

import sys
import json
import re
import argparse
import unicodedata
from pathlib import Path

try:
    import pdfplumber
except ImportError:
    print("[ERROR] pdfplumber not installed. Run: pip3 install pdfplumber", file=sys.stderr)
    sys.exit(2)


class ParseError(Exception):
    pass


_DATA_ROW_RE = re.compile(
    r"^(\d+)\s+(.+?)\s+(\d{4}-\d{2}-\d{2}\s+\d{2}:\d{2})\s+(\S+?)\s+(.+?)\s+([\d.]+)元\s*$"
)


def parse_trip(pdf_path: Path) -> dict:
    if not pdf_path.exists():
        raise ParseError(f"PDF not found: {pdf_path}")

    with pdfplumber.open(pdf_path) as pdf:
        text = "\n".join((p.extract_text() or "") for p in pdf.pages)

    # NFKC 归一化 Unicode（同 parse_invoices.py）
    text = unicodedata.normalize("NFKC", text)

    # 平台校验
    if "高德地图" not in text and "AMAP ITINERARY" not in text:
        raise ParseError(
            "Not a 高德 trip itinerary (lacking '高德地图' / 'AMAP ITINERARY'). "
            "v0.1 only supports 高德 (AMAP)."
        )

    result = {
        "parser_version": PARSER_VERSION,
        "platform": "gaode",
        "source_pdf": str(pdf_path),
    }

    # 申请时间
    m = re.search(r"申请时间\s*[：:]\s*(\d{4}-\d{2}-\d{2})", text)
    if not m:
        raise ParseError("Cannot extract 申请时间")
    result["request_date"] = m.group(1)

    # 行程时间起 / 止
    m = re.search(
        r"行程时间\s*[：:]\s*(\d{4}-\d{2}-\d{2}\s+\d{2}:\d{2})\s*至\s*(\d{4}-\d{2}-\d{2}\s+\d{2}:\d{2})",
        text,
    )
    if not m:
        raise ParseError("Cannot extract 行程时间")
    result["trip_window_start"] = m.group(1)
    result["trip_window_end"] = m.group(2)

    # 行程人手机号
    m = re.search(r"行程人手机号\s*[：:]\s*(\d+)", text)
    if not m:
        raise ParseError("Cannot extract 行程人手机号")
    result["passenger_phone"] = m.group(1)

    # 共计 N 单
    m = re.search(r"共计\s*(\d+)\s*单", text)
    if not m:
        raise ParseError("Cannot extract 共计行程数")
    result["trip_count"] = int(m.group(1))

    # 合计金额
    m = re.search(r"合计\s*([\d.]+)\s*元", text)
    if not m:
        raise ParseError("Cannot extract 合计金额")
    result["total_amount"] = float(m.group(1))

    # 行程明细
    result["trips"] = _extract_trips(text, result["trip_count"])
    return result


def _extract_trips(text: str, expected_count: int) -> list:
    """
    解析行程表格。pdfplumber 把表格输出为类似:

        序号 服务商 车型 上车时间 城市 起点 终点 金额
        中国杭州人力 浙江大学(紫金
        1 T3出行 经济型 2026-05-11 22:49 杭州市 23.36元
        资源服务产业园 港校区)校医院
        页码： 1 / 1

    新版高德 PDF 常把"起点"拆到数据行的上一行和下一行；少数服务商
    名也会随表格列一起拆行。数据行本身通常保留"终点"和"金额"。
    """
    lines = text.split("\n")

    # 找表头
    header_idx = None
    for i, line in enumerate(lines):
        if "序号" in line and "服务商" in line and "起点" in line and "终点" in line:
            header_idx = i
            break
    if header_idx is None:
        raise ParseError("Cannot find table header line")

    # 表头之后到 "页码" / 文件结束
    end_idx = len(lines)
    for i in range(header_idx + 1, len(lines)):
        if lines[i].lstrip().startswith("页码"):
            end_idx = i
            break

    data_lines = lines[header_idx + 1:end_idx]
    trips = []

    for i, line in enumerate(data_lines):
        m = _DATA_ROW_RE.match(line.strip())
        if not m:
            continue

        upper = data_lines[i - 1] if i - 1 >= 0 else ""
        lower = data_lines[i + 1] if i + 1 < len(data_lines) else ""

        # 上一行如果是表头本身或别的数据行，则该行不属于本单的"起终点上半"
        if "序号" in upper or _DATA_ROW_RE.match(upper.strip()):
            upper = ""
        if "序号" in lower or lower.lstrip().startswith("页码") or _DATA_ROW_RE.match(lower.strip()):
            lower = ""

        service_provider, car_type = _parse_provider_and_car_type(m.group(2), upper, lower)
        origin = _extract_wrapped_origin(upper, lower)

        trips.append({
            "index": int(m.group(1)),
            "service_provider": service_provider,
            "car_type": car_type,
            "pickup_time": m.group(3),
            "city": m.group(4),
            "origin": origin,
            "destination": m.group(5).strip(),
            "amount": float(m.group(6)),
        })

    if len(trips) != expected_count:
        raise ParseError(
            f"Trip count mismatch: header says {expected_count}, parsed {len(trips)}"
        )

    return trips


def _split_wrapped_columns(line: str):
    parts = re.split(r"\s+", line.strip(), maxsplit=1)
    if len(parts) == 2:
        return parts[0], parts[1]
    return "", parts[0] if parts else ""


def _parse_provider_and_car_type(row_prefix: str, upper_line: str, lower_line: str):
    """
    row_prefix 是序号后、上车时间前的列内容。常见为"服务商 车型"；
    若服务商被拆到上下行，row_prefix 只剩车型，此时从上下行第一列拼回。
    """
    tokens = row_prefix.strip().split()
    if len(tokens) >= 2:
        return "".join(tokens[:-1]), tokens[-1]

    upper_provider, _ = _split_wrapped_columns(upper_line)
    lower_provider, _ = _split_wrapped_columns(lower_line)
    provider = (upper_provider + lower_provider).strip()
    car_type = tokens[0] if tokens else ""
    return provider, car_type


def _extract_wrapped_origin(upper_line: str, lower_line: str):
    """从数据行上下两行拼出新版高德表格里的起点。"""
    _, upper_origin = _split_wrapped_columns(upper_line)
    _, lower_origin = _split_wrapped_columns(lower_line)
    return (upper_origin + lower_origin).strip()


def main():
    parser = argparse.ArgumentParser(
        description="Parse a 高德 taxi trip itinerary PDF (v0.1, 高德 only).",
    )
    parser.add_argument("pdf_path", type=Path, help="Path to trip itinerary PDF")
    parser.add_argument("--pretty", action="store_true", help="Pretty-print JSON output")
    args = parser.parse_args()

    try:
        result = parse_trip(args.pdf_path)
    except ParseError as e:
        print(f"[PARSE ERROR] {e}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"[UNEXPECTED ERROR] {type(e).__name__}: {e}", file=sys.stderr)
        sys.exit(2)

    json.dump(result, sys.stdout, ensure_ascii=False, indent=2 if args.pretty else None)
    sys.stdout.write("\n")


if __name__ == "__main__":
    main()
