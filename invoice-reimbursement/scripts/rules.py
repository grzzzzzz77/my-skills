#!/usr/bin/env python3
"""
报销规则引擎  —  v0.1

输入: pair_pdfs.py 的输出 JSON（从 stdin 或 --pairs 文件）+ rules.json
输出: 同样结构的 JSON，每个 pair 增加 verdict 字段:

    "verdict": {
      "passed": bool,
      "skip_reasons": ["规则编号: 中文原因", ...],
      "checks": [
        {"rule": "B2.buyer_name", "passed": bool, "detail": "..."},
        ...
      ]
    }

也增加一个 batch 级 verdict 字段记录跨 pair 的 F2 (单日累计) 等检查结果。

规则编号对应见对话中"当前筛选规则"列表 + spec.md 中 rules.json schema。

Usage:
    python3 pair_pdfs.py <dir> | python3 rules.py --rules skill/assets/rules.example.json
    python3 rules.py --pairs <pairs.json> --rules <rules.json> [--pretty]

退出码:
    0  全部 pair 通过
    1  至少一个 pair 被规则跳过
    2  规则文件读取 / 解析失败
"""

ENGINE_VERSION = "0.1"

import sys
import json
import argparse
from datetime import datetime
from pathlib import Path


# -------- 工具 --------

def _strip_doc(obj):
    """递归去掉所有 _doc 开头的注释字段."""
    if isinstance(obj, dict):
        return {k: _strip_doc(v) for k, v in obj.items() if not (isinstance(k, str) and k.startswith("_doc"))}
    if isinstance(obj, list):
        return [_strip_doc(item) for item in obj]
    return obj


def _parse_hour(time_str: str):
    """从 'YYYY-MM-DD HH:MM' 提取小时整数."""
    try:
        return int(time_str.split(" ")[1].split(":")[0])
    except (IndexError, ValueError, AttributeError):
        return None


def _parse_dt(time_str: str):
    """'YYYY-MM-DD HH:MM' → datetime."""
    try:
        return datetime.strptime(time_str, "%Y-%m-%d %H:%M")
    except (ValueError, TypeError):
        return None


# -------- 单 pair 规则 --------

def check_pair(invoice: dict, trip_doc: dict, rules: dict) -> dict:
    """
    对一个 (invoice, trip_doc) 配对运行规则引擎.
    trip_doc 是 parse_trips.py 输出, 含 trips[] 列表.
    """
    checks = []
    reasons = []

    def add(rule_id: str, passed: bool, detail: str = ""):
        checks.append({"rule": rule_id, "passed": passed, "detail": detail})
        if not passed:
            reasons.append(f"{rule_id}: {detail}")

    inv_validity = rules.get("invoice_validity", {})
    buyer_rule = rules.get("buyer", {})
    location = rules.get("location", {})
    time_rule = rules.get("time_window", {})
    amount_rule = rules.get("amount", {})

    # ---- B 类: 发票合规 + 购买方 ----
    if inv_validity.get("must_have_invoice_number"):
        ok = bool(invoice.get("invoice_number"))
        add("B1.invoice_number", ok, "" if ok else "发票号码缺失")

    if inv_validity.get("buyer_name_must_match"):
        expected = buyer_rule.get("company_name")
        actual = invoice.get("buyer", {}).get("name", "")
        if expected:
            ok = expected in actual
            add("B2.buyer_name", ok, "" if ok else f"购买方名称'{actual}'不含'{expected}'")

    expected_tax = buyer_rule.get("tax_id")
    if expected_tax:
        actual_tax = invoice.get("buyer", {}).get("tax_id", "")
        ok = expected_tax == actual_tax
        add("B3.tax_id", ok, "" if ok else f"购买方税号'{actual_tax}' ≠ '{expected_tax}'")

    type_keywords = inv_validity.get("invoice_type_keywords", [])
    if type_keywords:
        item_name = invoice.get("item_name", "")
        missing = [k for k in type_keywords if k not in item_name]
        ok = not missing
        add("B4.invoice_type", ok, "" if ok else f"项目名称'{item_name}'缺少关键词 {missing}")

    # ---- C 类: 平台 ----
    platform_kw = rules.get("platform", {}).get("title_keyword_whitelist", [])
    if platform_kw:
        # 解析器已经强制了平台校验; 这里只做软校验
        platform = trip_doc.get("platform", "")
        ok = platform == "gaode"  # v0.1 仅高德
        add("C1.platform", ok, "" if ok else f"行程单平台'{platform}'不在白名单 {platform_kw}")

    # ---- D / E 类: 按行程逐单校验 ----
    trips = trip_doc.get("trips", [])
    city_wl = location.get("city_whitelist", {}).get("values", [])
    em = location.get("endpoint_match", {})
    em_mode = em.get("mode", "none")
    em_keywords = em.get("keywords", [])
    tw_mode = time_rule.get("mode", "none")

    for trip in trips:
        idx = trip.get("index", "?")

        # D1 城市
        if city_wl:
            city = trip.get("city", "")
            ok = city in city_wl
            add(f"D1.city[第{idx}单]", ok, "" if ok else f"城市'{city}'不在白名单 {city_wl}")

        # D2 起终点
        if em_mode != "none":
            origin = trip.get("origin", "")
            dest = trip.get("destination", "")
            if not em_keywords:
                # mode 非 none 但 keywords=[]：视为配置错误, fail-closed
                add(
                    f"D2.endpoint[第{idx}单]",
                    False,
                    f"endpoint_match.mode='{em_mode}' 但 keywords=[]；视为配置错误，fail-closed 拒绝",
                )
            else:
                o_hit = any(k in origin for k in em_keywords)
                d_hit = any(k in dest for k in em_keywords)
                if em_mode == "either":
                    ok = o_hit or d_hit
                    detail = f"起点'{origin}'和终点'{dest}'都不含 {em_keywords}"
                elif em_mode == "both":
                    ok = o_hit and d_hit
                    detail = f"起点或终点未同时命中 {em_keywords} (origin='{origin}', destination='{dest}')"
                elif em_mode == "origin_in":
                    ok = o_hit
                    detail = f"起点'{origin}'不含 {em_keywords} 中任一关键词"
                elif em_mode == "destination_in":
                    ok = d_hit
                    detail = f"终点'{dest}'不含 {em_keywords} 中任一关键词"
                else:
                    ok = False
                    detail = f"未知的 endpoint_match.mode='{em_mode}'"
                add(f"D2.endpoint[第{idx}单]", ok, "" if ok else detail)

        # E1 时间窗口
        if tw_mode != "none":
            pickup = trip.get("pickup_time", "")
            if tw_mode == "hour_range":
                start = time_rule.get("start_hour", 0)
                end = time_rule.get("end_hour", 24)
                hour = _parse_hour(pickup)
                if hour is None:
                    add(f"E1.time[第{idx}单]", False, f"无法解析上车时间'{pickup}'")
                else:
                    if start <= end:
                        ok = start <= hour < end
                    else:
                        # 跨午夜: [start, 24) ∪ [0, end)
                        ok = hour >= start or hour < end
                    detail = (
                        f"上车时间 {pickup} 的小时 {hour:02d} 不在 [{start:02d}, {end:02d}) "
                        f"{'(跨午夜)' if start > end else ''}"
                    )
                    add(f"E1.time[第{idx}单]", ok, "" if ok else detail)
            elif tw_mode in ("weekdays_only", "weekends_only"):
                dt = _parse_dt(pickup)
                if dt is None:
                    add(f"E1.time[第{idx}单]", False, f"无法解析上车时间'{pickup}'")
                else:
                    weekday = dt.weekday()  # Mon=0
                    if tw_mode == "weekdays_only":
                        ok = weekday < 5
                        detail = f"上车日 {pickup} 是周末（仅允许工作日）"
                    else:
                        ok = weekday >= 5
                        detail = f"上车日 {pickup} 是工作日（仅允许周末）"
                    add(f"E1.time[第{idx}单]", ok, "" if ok else detail)
            else:
                add(f"E1.time[第{idx}单]", False, f"未知的 time_window.mode='{tw_mode}'")

    # ---- F 类: 金额（仅单笔，单日累计在批次层） ----
    max_pt = amount_rule.get("max_per_trip")
    if max_pt is not None:
        total = invoice.get("total_amount", 0)
        ok = total <= max_pt
        add("F1.max_per_trip", ok, "" if ok else f"单笔 {total} 超过上限 {max_pt}")

    passed = all(c["passed"] for c in checks)
    return {
        "passed": passed,
        "skip_reasons": reasons,
        "checks": checks,
    }


# -------- 批次级规则 --------

def check_batch(pairs_with_verdict: list, rules: dict) -> dict:
    """
    跨 pair 的规则 (目前只有 F2 单日累计金额).
    pairs_with_verdict 已经过 check_pair, 含 verdict 字段.
    返回 batch 级别的 verdict 信息.
    """
    batch_checks = []
    batch_reasons = []

    amount_rule = rules.get("amount", {})
    max_day = amount_rule.get("max_per_day_total")

    if max_day is not None:
        # 按 trip_window_start 的日期聚合, 只统计 verdict.passed 的 pair
        from collections import defaultdict
        day_total = defaultdict(float)
        day_pairs = defaultdict(list)
        for p in pairs_with_verdict:
            if not p.get("verdict", {}).get("passed"):
                continue
            trip_doc = p.get("trip", {})
            day = (trip_doc.get("trip_window_start") or "").split(" ")[0]
            day_total[day] += float(p["invoice"].get("total_amount", 0))
            day_pairs[day].append(p)

        for day, total in day_total.items():
            ok = total <= max_day
            detail = f"{day} 单日累计 {total:.2f} 超过上限 {max_day}"
            batch_checks.append({"rule": f"F2.max_per_day[{day}]", "passed": ok, "detail": "" if ok else detail})
            if not ok:
                batch_reasons.append(f"F2.max_per_day[{day}]: {detail}")
                # 把该天所有 pair 标记为 batch-rejected
                for p in day_pairs[day]:
                    p["verdict"]["passed"] = False
                    p["verdict"]["skip_reasons"].append(f"F2.max_per_day[{day}]: {detail}")

    return {
        "passed": all(c["passed"] for c in batch_checks),
        "skip_reasons": batch_reasons,
        "checks": batch_checks,
    }


# -------- CLI --------

def main():
    ap = argparse.ArgumentParser(description="Apply reimbursement rules to paired invoice/trip data (v0.1).")
    ap.add_argument("--rules", required=True, type=Path, help="Path to rules.json")
    ap.add_argument("--pairs", type=Path, help="Path to pair_pdfs.py output JSON; defaults to stdin")
    ap.add_argument("--pretty", action="store_true")
    args = ap.parse_args()

    # 读规则
    try:
        with open(args.rules, encoding="utf-8") as f:
            raw_rules = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError) as e:
        print(f"[ERROR] Cannot read rules file {args.rules}: {e}", file=sys.stderr)
        sys.exit(2)
    rules = _strip_doc(raw_rules)

    # 读 pair 数据
    if args.pairs:
        try:
            with open(args.pairs, encoding="utf-8") as f:
                pair_data = json.load(f)
        except (FileNotFoundError, json.JSONDecodeError) as e:
            print(f"[ERROR] Cannot read pairs file {args.pairs}: {e}", file=sys.stderr)
            sys.exit(2)
    else:
        try:
            pair_data = json.load(sys.stdin)
        except json.JSONDecodeError as e:
            print(f"[ERROR] Cannot parse stdin JSON: {e}", file=sys.stderr)
            sys.exit(2)

    # 跑单 pair 检查
    pairs = pair_data.get("pairs", [])
    for p in pairs:
        p["verdict"] = check_pair(p["invoice"], p["trip"], rules)

    # 跑批次检查
    batch_verdict = check_batch(pairs, rules)

    # 输出
    out = {
        "engine_version": ENGINE_VERSION,
        "rules_file": str(args.rules),
        **pair_data,
        "batch_verdict": batch_verdict,
    }
    json.dump(out, sys.stdout, ensure_ascii=False, indent=2 if args.pretty else None)
    sys.stdout.write("\n")

    if any(not p["verdict"]["passed"] for p in pairs):
        sys.exit(1)


if __name__ == "__main__":
    main()
