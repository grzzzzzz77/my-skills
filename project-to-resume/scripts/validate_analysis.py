#!/usr/bin/env python3
"""Validate project_resume_analysis.json for project-to-resume."""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
from typing import Any


RISK_VALUES = {"safe", "needs_confirmation", "risky"}
READINESS_VALUES = {"direct", "rewrite", "confirm", "idea"}
STAR_KEYS = ("situation", "task", "action", "result", "tradeoff")

SENSITIVE_RE = re.compile(
    r"(?i)(password|passwd|secret|token|api[_-]?key|access[_-]?key|private[_-]?key|"
    r"credential|cookie|authorization|bearer|客户名称|客户名|内部客户|真实客户|"
    r"手机号|身份证|银行卡|邮箱[:：]|内网|生产库)"
)

HIGH_OWNERSHIP_RE = re.compile(r"主导|全盘|独立负责|Owner|从\s*0\s*到\s*1|核心负责人", re.I)
UNCONFIRMED_METRIC_RE = re.compile(r"提升\s*\d|降低\s*\d|减少\s*\d|缩短\s*\d|增长\s*\d|\d+\s*%")


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


def is_nonempty_text(value: Any) -> bool:
    return isinstance(value, str) and bool(value.strip())


def add(findings: list[dict], level: str, path: str, message: str) -> None:
    findings.append({"level": level, "path": path, "message": message})


def validate_highlight(item: Any, index: int, findings: list[dict]) -> None:
    path = f"highlights[{index}]"
    if not isinstance(item, dict):
        add(findings, "error", path, "highlight must be an object")
        return

    for key in ("title", "category", "safe_bullet", "why"):
        if not is_nonempty_text(item.get(key)):
            add(findings, "error", f"{path}.{key}", f"{key} is required")

    risk = item.get("risk")
    if risk not in RISK_VALUES:
        add(findings, "error", f"{path}.risk", f"risk must be one of {sorted(RISK_VALUES)}")

    readiness = item.get("readiness")
    if readiness not in READINESS_VALUES:
        add(findings, "error", f"{path}.readiness", f"readiness must be one of {sorted(READINESS_VALUES)}")

    evidence = [x for x in as_list(item.get("evidence")) if str(x).strip()]
    if not evidence:
        add(findings, "error", f"{path}.evidence", "at least one evidence path/count/signal is required")

    bullet = str(item.get("safe_bullet") or "")
    if SENSITIVE_RE.search(bullet):
        add(findings, "error", f"{path}.safe_bullet", "safe_bullet appears to contain sensitive data or secrets")

    if risk == "safe" and UNCONFIRMED_METRIC_RE.search(bullet):
        add(findings, "warning", f"{path}.safe_bullet", "safe bullet contains a numeric improvement; ensure it is verified or move it to enhanced_bullet")

    if risk == "safe" and HIGH_OWNERSHIP_RE.search(bullet):
        add(findings, "warning", f"{path}.safe_bullet", "high-ownership wording requires confirmed role evidence")

    if risk == "needs_confirmation" and not is_nonempty_text(item.get("enhanced_bullet")):
        add(findings, "warning", f"{path}.enhanced_bullet", "needs_confirmation highlights should include an enhanced_bullet")

    if risk in {"needs_confirmation", "risky"} and not [x for x in as_list(item.get("data_to_confirm")) if str(x).strip()]:
        add(findings, "warning", f"{path}.data_to_confirm", "confirmation-dependent highlights should list data_to_confirm")

    interview = item.get("interview") or item.get("star")
    if not isinstance(interview, dict):
        add(findings, "error", f"{path}.interview", "interview must be a STAR object")
    else:
        missing = [key for key in STAR_KEYS if not is_nonempty_text(interview.get(key))]
        if missing:
            add(findings, "error", f"{path}.interview", "missing STAR fields: " + ", ".join(missing))


def scan_sensitive_values(value: Any, findings: list[dict], path: str = "$") -> None:
    if isinstance(value, dict):
        for key, child in value.items():
            if key in {"role_assumption", "disclosure_assumption", "data_to_confirm"}:
                continue
            scan_sensitive_values(child, findings, f"{path}.{key}")
    elif isinstance(value, list):
        for index, child in enumerate(value):
            scan_sensitive_values(child, findings, f"{path}[{index}]")
    elif isinstance(value, str) and SENSITIVE_RE.search(value):
        add(findings, "warning", path, "text may contain secrets, credentials, or disclosure-sensitive details")


def validate_analysis_payload(analysis: dict) -> list[dict]:
    findings: list[dict] = []

    for key in ("project_name", "summary", "target_role", "readiness", "role_assumption", "disclosure_assumption"):
        if not is_nonempty_text(analysis.get(key)):
            add(findings, "error", key, f"{key} is required")

    keywords = [x for x in as_list(analysis.get("keywords")) if str(x).strip()]
    if not keywords:
        add(findings, "warning", "keywords", "keywords should include role-relevant technologies or domain terms")

    facts = analysis.get("facts")
    if not isinstance(facts, (list, dict)) or not facts:
        add(findings, "error", "facts", "facts must include business/module/API/data-flow evidence")

    highlights = analysis.get("highlights")
    if not isinstance(highlights, list) or not highlights:
        add(findings, "error", "highlights", "at least one highlight is required")
    else:
        for index, item in enumerate(highlights):
            validate_highlight(item, index, findings)

    safe_highlights = [
        item for item in highlights or []
        if isinstance(item, dict) and item.get("risk") == "safe" and is_nonempty_text(item.get("safe_bullet"))
    ]
    if highlights and not safe_highlights:
        add(findings, "warning", "highlights", "no safe highlight found; final report may have no directly usable resume bullet")

    scan_sensitive_values(analysis, findings)

    return findings


def format_findings(findings: list[dict]) -> str:
    if not findings:
        return "analysis validation passed"
    lines = []
    for item in findings:
        lines.append(f"[{item['level'].upper()}] {item['path']}: {item['message']}")
    return "\n".join(lines)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--analysis", required=True, help="project_resume_analysis.json")
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
