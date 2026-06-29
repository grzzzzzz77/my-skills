#!/usr/bin/env python3
"""Validate resume_scorecard_analysis.json for resume-scorecard."""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
from typing import Any


SCORE_MODES = {"standalone", "single", "jd_fit", "comparison", "cross_industry_comparison"}
CONFIDENCE_VALUES = {"high", "medium", "low"}
SEVERITY_VALUES = {"high", "medium", "low"}
EMAIL_RE = re.compile(r"[\w.+-]+@[\w.-]+\.[A-Za-z]{2,}")
PHONE_RE = re.compile(r"(?<!\d)(?:\+?\d[\d\s().-]{7,}\d)(?!\d)")


def load_json(path: Path) -> dict:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except Exception as exc:
        raise SystemExit(f"Cannot read JSON {path}: {exc}") from exc
    if not isinstance(data, dict):
        raise SystemExit("analysis JSON root must be an object")
    return data


def as_list(value: Any) -> list:
    if value is None:
        return []
    if isinstance(value, list):
        return value
    return [value]


def is_text(value: Any) -> bool:
    return isinstance(value, str) and bool(value.strip())


def add(findings: list[dict], level: str, path: str, message: str) -> None:
    findings.append({"level": level, "path": path, "message": message})


def numeric_score(value: Any) -> float | None:
    if isinstance(value, bool):
        return None
    if isinstance(value, (int, float)):
        return float(value)
    try:
        return float(str(value))
    except Exception:
        return None


def scan_pii(value: Any, findings: list[dict], path: str = "$") -> None:
    if isinstance(value, dict):
        for key, child in value.items():
            scan_pii(child, findings, f"{path}.{key}")
    elif isinstance(value, list):
        for index, child in enumerate(value):
            scan_pii(child, findings, f"{path}[{index}]")
    elif isinstance(value, str):
        if EMAIL_RE.search(value):
            add(findings, "warning", path, "text appears to contain an email address; redact private contact details")
        if PHONE_RE.search(value):
            add(findings, "warning", path, "text appears to contain a phone number; redact private contact details")


def validate_dimension(item: Any, path: str, findings: list[dict]) -> tuple[float, float]:
    if not isinstance(item, dict):
        add(findings, "error", path, "dimension must be an object")
        return 0.0, 0.0
    for key in ("name", "rationale"):
        if not is_text(item.get(key)):
            add(findings, "error", f"{path}.{key}", f"{key} is required")
    score = numeric_score(item.get("score"))
    max_score = numeric_score(item.get("max_score"))
    if score is None:
        add(findings, "error", f"{path}.score", "score must be numeric")
        score = 0.0
    if max_score is None:
        add(findings, "error", f"{path}.max_score", "max_score must be numeric")
        max_score = 0.0
    if score < 0 or score > max_score:
        add(findings, "error", f"{path}.score", "score must be between 0 and max_score")
    if not as_list(item.get("evidence")):
        add(findings, "warning", f"{path}.evidence", "dimension should include resume evidence")
    if not as_list(item.get("deductions")):
        add(findings, "warning", f"{path}.deductions", "dimension should include deductions, even if '无明显扣分'")
    return score, max_score


def validate_resume(item: Any, index: int, findings: list[dict], score_mode: str = "") -> None:
    path = f"resumes[{index}]"
    if not isinstance(item, dict):
        add(findings, "error", path, "resume must be an object")
        return
    for key in ("id", "name", "score_summary"):
        if not is_text(item.get(key)):
            add(findings, "error", f"{path}.{key}", f"{key} is required")
    if score_mode == "cross_industry_comparison" and not is_text(item.get("target_role")):
        add(findings, "warning", f"{path}.target_role", "cross-industry comparisons should include each resume's own target_role")
    if score_mode == "cross_industry_comparison" and not is_text(item.get("scoring_context")):
        add(findings, "warning", f"{path}.scoring_context", "explain whether this resume is scored against its own target or a universal baseline")
    total = numeric_score(item.get("total_score"))
    if total is None or total < 0 or total > 100:
        add(findings, "error", f"{path}.total_score", "total_score must be 0-100")
    dimensions = item.get("dimensions")
    if not isinstance(dimensions, list) or not dimensions:
        add(findings, "error", f"{path}.dimensions", "dimensions must be a non-empty list")
    else:
        sum_score = 0.0
        sum_max = 0.0
        for dim_index, dim in enumerate(dimensions):
            score, max_score = validate_dimension(dim, f"{path}.dimensions[{dim_index}]", findings)
            sum_score += score
            sum_max += max_score
        if abs(sum_max - 100.0) > 0.01:
            add(findings, "warning", f"{path}.dimensions", f"dimension max_score total should be 100, got {sum_max:g}")
        if total is not None and abs(sum_score - total) > 1.0:
            add(findings, "warning", f"{path}.total_score", f"total_score differs from dimension sum ({sum_score:g})")
    for flag_index, flag in enumerate(as_list(item.get("red_flags"))):
        if isinstance(flag, dict):
            severity = flag.get("severity")
            if severity not in SEVERITY_VALUES:
                add(findings, "error", f"{path}.red_flags[{flag_index}].severity", "severity must be high, medium, or low")


def validate_analysis_payload(analysis: dict) -> list[dict]:
    findings: list[dict] = []
    if not is_text(analysis.get("report_title")):
        add(findings, "error", "report_title", "report_title is required")
    mode = analysis.get("score_mode")
    if mode not in SCORE_MODES:
        add(findings, "error", "score_mode", f"score_mode must be one of {sorted(SCORE_MODES)}")
    confidence = analysis.get("confidence")
    if confidence not in CONFIDENCE_VALUES:
        add(findings, "error", "confidence", f"confidence must be one of {sorted(CONFIDENCE_VALUES)}")
    if not is_text(analysis.get("overall_summary")):
        add(findings, "error", "overall_summary", "overall_summary is required")
    resumes = analysis.get("resumes")
    if not isinstance(resumes, list) or not resumes:
        add(findings, "error", "resumes", "at least one resume is required")
    else:
        for index, item in enumerate(resumes):
            validate_resume(item, index, findings, str(mode or ""))
        if mode == "comparison" and len(resumes) < 2:
            add(findings, "error", "resumes", "comparison mode requires at least two resumes")
        if mode == "cross_industry_comparison" and len(resumes) < 2:
            add(findings, "error", "resumes", "cross_industry_comparison mode requires at least two resumes")
        if len(resumes) > 1 and not isinstance(analysis.get("comparison"), dict):
            add(findings, "warning", "comparison", "multiple resumes should include comparison")
        if mode == "standalone" and len(resumes) > 1:
            add(findings, "warning", "score_mode", "standalone mode usually has one resume; use comparison or cross_industry_comparison for multiple resumes")
    scan_pii(analysis, findings)
    return findings


def format_findings(findings: list[dict]) -> str:
    if not findings:
        return "scorecard validation passed"
    return "\n".join(f"[{item['level'].upper()}] {item['path']}: {item['message']}" for item in findings)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--analysis", required=True, help="resume_scorecard_analysis.json")
    parser.add_argument("--strict", action="store_true", help="Exit non-zero on warnings as well as errors")
    args = parser.parse_args()

    analysis = load_json(Path(args.analysis).expanduser().resolve())
    findings = validate_analysis_payload(analysis)
    print(format_findings(findings))
    has_error = any(item["level"] == "error" for item in findings)
    has_warning = any(item["level"] == "warning" for item in findings)
    if has_error or (args.strict and has_warning):
        raise SystemExit(1)


if __name__ == "__main__":
    main()
