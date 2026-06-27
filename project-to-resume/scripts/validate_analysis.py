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
    r"(?i)(password|passwd|secret|api[_-]?key|access[_-]?key|private[_-]?key|"
    r"credential|cookie|authorization|bearer|客户名称|客户名|内部客户|真实客户|"
    r"手机号|身份证|银行卡|邮箱[:：]|内网|生产库)"
)
TOKEN_SECRET_RE = re.compile(
    r"(?i)("
    r"(?:api|auth|access|refresh|id|private|secret)[_-]?token\s*[:=]\s*['\"][A-Za-z0-9._/+=-]{12,}['\"]|"
    r"token\s*[:=]\s*['\"][A-Za-z0-9._/+=-]{16,}['\"]|"
    r"bearer\s+[A-Za-z0-9._/+=-]{12,}|"
    r"(?:hardcode|hard-coded|leak|泄露|明文|硬编码|凭证|密钥)[^。；;\\n]{0,30}token"
    r")"
)

HIGH_OWNERSHIP_RE = re.compile(r"主导|全盘|独立负责|Owner|从\s*0\s*到\s*1|核心负责人", re.I)
UNCONFIRMED_METRIC_RE = re.compile(r"提升\s*\d|降低\s*\d|减少\s*\d|缩短\s*\d|增长\s*\d|\d+\s*%")
PATH_EXT_RE = re.compile(
    r"\.(vue|svelte|jsx?|tsx?|mjs|cjs|py|go|rs|java|kt|swift|php|rb|cs|json|ya?ml|toml|md|mdx|html|css|scss|sql|sh)$",
    re.I,
)
PATH_PREFIX_RE = re.compile(
    r"^(src|app|apps|pages|views|components|widgets|routes|api|server|services|store|stores|lib|libs|"
    r"models|schemas|tests?|__tests__|docs?|references|scripts|config|configs|uni_modules|packages|tools|agents)/",
    re.I,
)


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


def contains_sensitive_text(text: str) -> bool:
    return bool(SENSITIVE_RE.search(text) or TOKEN_SECRET_RE.search(text))


def load_evidence_context(path: Path | None) -> dict:
    if path is None:
        return {}
    evidence = load_json(path)
    path_source = evidence.get("evidence_paths_index") or evidence.get("file_index")
    file_index = {str(item).replace("\\", "/").lstrip("./") for item in as_list(path_source)}
    for item in as_list(evidence.get("key_files")):
        if str(item).strip():
            file_index.add(str(item).replace("\\", "/").lstrip("./"))
    for doc in as_list(evidence.get("docs")):
        if isinstance(doc, dict) and str(doc.get("path", "")).strip():
            file_index.add(str(doc["path"]).replace("\\", "/").lstrip("./"))
    return {"repo": evidence.get("repo") or "", "file_index": file_index}


def normalize_evidence_path(value: Any, repo: str = "") -> str:
    text = str(value or "").strip().strip("`").strip()
    if not text:
        return ""
    text = text.replace("\\", "/")
    text = re.sub(r"^file://", "", text)
    text = re.sub(r"^['\"]|['\"]$", "", text)
    text = re.sub(r":\d+(?::\d+)?$", "", text)
    text = re.split(r"\s+(?:->|=>|\(|\[)", text, 1)[0].strip()
    text = text.lstrip("./")
    if repo:
        repo_norm = repo.replace("\\", "/").rstrip("/") + "/"
        if text.startswith(repo_norm):
            text = text[len(repo_norm):]
    return text.strip("/")


def is_path_like_evidence(value: Any) -> bool:
    text = normalize_evidence_path(value)
    if not text or text.startswith(("http://", "https://")):
        return False
    if " " in text and "/" not in text:
        return False
    return "/" in text or bool(PATH_EXT_RE.search(text)) or bool(PATH_PREFIX_RE.search(text))


def evidence_path_exists(value: Any, context: dict) -> bool:
    file_index = context.get("file_index") or set()
    repo = str(context.get("repo") or "")
    candidate = normalize_evidence_path(value, repo)
    if not candidate:
        return False
    if candidate in file_index:
        return True
    directory = candidate.rstrip("/") + "/"
    if any(path.startswith(directory) for path in file_index):
        return True
    return False


def validate_evidence_paths(evidence: list[Any], path: str, context: dict, findings: list[dict]) -> None:
    if not context:
        return
    for item_index, item in enumerate(evidence):
        if not is_path_like_evidence(item):
            continue
        if not evidence_path_exists(item, context):
            add(
                findings,
                "error",
                f"{path}.evidence[{item_index}]",
                "evidence path is not present in project_evidence.json file_index/key_files/docs",
            )


def validate_highlight(item: Any, index: int, findings: list[dict], evidence_context: dict | None = None) -> None:
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
    else:
        validate_evidence_paths(evidence, path, evidence_context or {}, findings)

    bullet = str(item.get("safe_bullet") or "")
    if contains_sensitive_text(bullet):
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
    elif isinstance(value, str) and contains_sensitive_text(value):
        add(findings, "warning", path, "text may contain secrets, credentials, or disclosure-sensitive details")


def validate_analysis_payload(analysis: dict, evidence_context: dict | None = None) -> list[dict]:
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
            validate_highlight(item, index, findings, evidence_context)

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
    parser.add_argument("--evidence", help="Optional project_evidence.json for strict evidence path checks")
    parser.add_argument("--strict", action="store_true", help="Exit non-zero on warnings as well as errors")
    args = parser.parse_args()

    analysis = load_json(Path(args.analysis).expanduser().resolve())
    evidence_context = load_evidence_context(Path(args.evidence).expanduser().resolve()) if args.evidence else {}
    findings = validate_analysis_payload(analysis, evidence_context)
    print(format_findings(findings))
    has_error = any(item["level"] == "error" for item in findings)
    has_warning = any(item["level"] == "warning" for item in findings)
    if has_error or (args.strict and has_warning):
        raise SystemExit(1)


if __name__ == "__main__":
    main()
