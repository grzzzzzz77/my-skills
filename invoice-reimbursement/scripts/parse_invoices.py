#!/usr/bin/env python3
"""
高德打车电子发票解析器  —  v0.1

仅支持高德平台开具的"旅客运输服务"类电子普通发票。
不支持: 滴滴 / 首汽 / 出租车 / 神州专车等其他平台、增值税专用发票、纸质发票、非客运类发票。

Usage:
    python3 parse_invoices.py <invoice_pdf_path> [--pretty]

Output (JSON to stdout):
    {
      "parser_version": "0.1",
      "platform": "gaode",
      "source_pdf": "...",
      "invoice_number": "...",           # 去重 key
      "invoice_date": "YYYY-MM-DD",
      "buyer":  {"name": "...", "tax_id": "..."},
      "seller": {"name": "...", "tax_id": "..."},
      "item_name": "*运输服务*客运服务费",
      "unit_price": ...,
      "quantity": ...,
      "amount_excl_tax": ...,
      "tax_rate": "3%",
      "tax_amount": ...,
      "total_amount": ...,               # 价税合计（小写）, 报销金额
      "total_amount_chinese": "...",
      "issuer": "..."
    }

字段提取规范见 skill/references/sample-analysis.md §1。
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


def parse_invoice(pdf_path: Path) -> dict:
    if not pdf_path.exists():
        raise ParseError(f"PDF not found: {pdf_path}")

    with pdfplumber.open(pdf_path) as pdf:
        text = "\n".join((page.extract_text() or "") for page in pdf.pages)

    # 归一化 Unicode：把康熙部首等兼容字符映射回常规 CJK
    # （某些 PDF 字体把 "子"/"卩" 等渲染为 U+2Fxx 区段的部首字符）
    text = unicodedata.normalize("NFKC", text)

    # 平台 / 类型校验
    if "电子发票" not in text:
        raise ParseError("Not an 电子发票. v0.1 only supports 高德 electronic invoices.")
    if "旅客运输服务" not in text and "客运服务费" not in text:
        raise ParseError(
            "Not a 旅客运输服务 invoice (lacking '旅客运输服务' / '客运服务费'). "
            "v0.1 only supports 高德 taxi invoices."
        )

    result = {
        "parser_version": PARSER_VERSION,
        "platform": "gaode",
        "source_pdf": str(pdf_path),
    }

    # 发票号码：优先标签匹配，回退到任意 20 位连续数字
    # （不同 PDF 字体的列布局可能导致标签和数值不在同一行）
    m = re.search(r"发票号码\s*[：:]\s*(\d{15,})", text)
    if m:
        result["invoice_number"] = m.group(1)
    else:
        nums20 = re.findall(r"\b\d{20}\b", text)
        if not nums20:
            raise ParseError("Cannot extract 发票号码")
        result["invoice_number"] = nums20[0]

    # 开票日期：优先标签匹配，回退到第一个 YYYY年MM月DD日
    m = re.search(r"开票日期\s*[：:]\s*(\d{4})年(\d{1,2})月(\d{1,2})日", text)
    if not m:
        m = re.search(r"(\d{4})年(\d{1,2})月(\d{1,2})日", text)
    if not m:
        raise ParseError("Cannot extract 开票日期")
    result["invoice_date"] = f"{m.group(1)}-{int(m.group(2)):02d}-{int(m.group(3)):02d}"

    # 购买方 / 销售方 名称：直接抓正文中前两个以 "公司" 结尾的字符串
    # （标签紧贴汉字会导致严格正则匹配到单字 "售"/"买"，所以不再使用标签匹配）
    names = re.findall(r"[一-鿿()（）A-Za-z0-9·]+公司", text)
    if len(names) < 2:
        raise ParseError(f"Cannot extract buyer & seller names. Found: {names}")
    result["buyer"] = {"name": names[0]}
    result["seller"] = {"name": names[1]}

    # 税号：优先标签匹配，回退到前两个中国统一社会信用代码（18 位字母数字）
    tax_ids = re.findall(
        r"统一社会(?:信用|信息)代码\s*/\s*纳税人识别号\s*[：:]\s*([A-Z0-9]+)",
        text,
    )
    if len(tax_ids) < 2:
        tax_ids = re.findall(r"\b[A-Z0-9]{18}\b", text)
    if len(tax_ids) < 2:
        raise ParseError(f"Cannot extract buyer & seller tax IDs. Found: {tax_ids}")
    result["buyer"]["tax_id"] = tax_ids[0]
    result["seller"]["tax_id"] = tax_ids[1]

    # 项目明细行: *运输服务*客运服务费 22.68 1 22.68 3% 0.68
    m = re.search(
        r"(\*[^\*\n]+\*[^\s]+)\s+([\d.]+)\s+(\d+)\s+([\d.]+)\s+(\d+%)\s+([\d.]+)",
        text,
    )
    if m:
        result["item_name"] = m.group(1)
        result["unit_price"] = float(m.group(2))
        result["quantity"] = int(m.group(3))
        result["amount_excl_tax"] = float(m.group(4))
        result["tax_rate"] = m.group(5)
        result["tax_amount"] = float(m.group(6))

    # 价税合计（大写）
    m = re.search(r"价税合计\s*[（(]\s*大写\s*[）)]\s*([一-鿿]+)", text)
    if m:
        result["total_amount_chinese"] = m.group(1)

    # 价税合计（小写） — 这是报销金额
    m = re.search(r"[（(]\s*小写\s*[）)]\s*¥?\s*([\d.]+)", text)
    if not m:
        raise ParseError("Cannot extract 价税合计 (小写)")
    result["total_amount"] = float(m.group(1))

    # 开票人
    m = re.search(r"开票人\s*[：:]\s*([一-鿿·]+)", text)
    if m:
        result["issuer"] = m.group(1)

    return result


def main():
    parser = argparse.ArgumentParser(
        description="Parse a 高德 taxi electronic invoice PDF (v0.1, 高德 only).",
    )
    parser.add_argument("pdf_path", type=Path, help="Path to invoice PDF")
    parser.add_argument("--pretty", action="store_true", help="Pretty-print JSON output")
    args = parser.parse_args()

    try:
        result = parse_invoice(args.pdf_path)
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
