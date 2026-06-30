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
COMPARISON_CONTEXT_VALUES = {"same_target", "same_industry", "cross_role", "cross_industry", "universal_baseline"}
LAYOUT_EVIDENCE_CAPS = {
    "rendered_file": 100,
    "file_structure": 90,
    "extracted_text": 82,
    "pasted_text": 75,
    "ocr_only": 65,
}
EMAIL_RE = re.compile(r"[\w.+-]+@[\w.-]+\.[A-Za-z]{2,}")
PHONE_RE = re.compile(r"(?<!\d)(?:\+?\d[\d\s().-]{7,}\d)(?!\d)")
DATE_PREFIX_RE = re.compile(r"\b(?:19|20)\d{2}[-/.]\d{1,2}[-/.]\d{1,2}")
CN_ID_RE = re.compile(r"(?<!\d)[1-9]\d{5}(?:18|19|20)\d{2}(?:0[1-9]|1[0-2])(?:0[1-9]|[12]\d|3[01])\d{3}[\dXx](?!\d)")
URL_RE = re.compile(r"https?://[^\s<>)\"']+")
SENSITIVE_URL_RE = re.compile(r"(?i)(?:access[_-]?token|auth[_-]?key|api[_-]?key|signature|sig|token|secret|code)=")
PRIVATE_HOST_RE = re.compile(r"(?i)(?:localhost|127\.0\.0\.1|0\.0\.0\.0|docs\.qq\.com|feishu\.cn|larksuite\.com|notion\.site|sharepoint\.com)")
TOKEN_RE = re.compile(r"(?i)\b(?:api[_-]?key|access[_-]?token|secret|bearer|authorization)\b\s*[:=]\s*['\"]?[A-Za-z0-9._~+/=-]{12,}")
ADDRESS_RE = re.compile(r"[\u4e00-\u9fff]{2,}(?:省|市|区|县)[\u4e00-\u9fff0-9A-Za-z]{0,30}(?:路|街|巷|弄|号|小区|大厦|单元|室)")


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


def looks_like_phone(candidate: str) -> bool:
    if DATE_PREFIX_RE.search(candidate):
        return False
    digits = re.sub(r"\D", "", candidate)
    if re.fullmatch(r"1[3-9]\d{9}", digits):
        return True
    stripped = candidate.strip()
    if stripped.startswith("+") and len(digits) >= 10:
        return True
    if re.search(r"\(\d{2,4}\)", candidate) and len(digits) >= 10:
        return True
    return False


def looks_like_sensitive_url(candidate: str) -> bool:
    return bool(SENSITIVE_URL_RE.search(candidate) or PRIVATE_HOST_RE.search(candidate))


def redact_text(value: str) -> str:
    redacted = TOKEN_RE.sub("[已脱敏密钥]", value)
    redacted = CN_ID_RE.sub("[已脱敏身份证]", redacted)
    redacted = ADDRESS_RE.sub("[已脱敏地址]", redacted)
    redacted = EMAIL_RE.sub("[已脱敏邮箱]", redacted)

    def redact_phone(match: re.Match[str]) -> str:
        candidate = match.group(0)
        return "[已脱敏电话]" if looks_like_phone(candidate) else candidate

    def redact_url(match: re.Match[str]) -> str:
        candidate = match.group(0)
        return "[已脱敏私有链接]" if looks_like_sensitive_url(candidate) else candidate

    redacted = PHONE_RE.sub(redact_phone, redacted)
    redacted = URL_RE.sub(redact_url, redacted)
    return redacted


def redact_payload(value: Any) -> Any:
    if isinstance(value, dict):
        return {key: redact_payload(child) for key, child in value.items()}
    if isinstance(value, list):
        return [redact_payload(child) for child in value]
    if isinstance(value, str):
        return redact_text(value)
    return value


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
        if any(looks_like_phone(match.group(0)) for match in PHONE_RE.finditer(value)):
            add(findings, "warning", path, "text appears to contain a phone number; redact private contact details")
        if CN_ID_RE.search(value):
            add(findings, "warning", path, "text appears to contain a Chinese ID number; redact private identity details")
        if ADDRESS_RE.search(value):
            add(findings, "warning", path, "text may contain an exact address; redact street-level private addresses")
        if TOKEN_RE.search(value):
            add(findings, "warning", path, "text appears to contain a secret/token; remove credentials from report artifacts")
        if any(looks_like_sensitive_url(match.group(0)) for match in URL_RE.finditer(value)):
            add(findings, "warning", path, "text appears to contain a private or tokenized URL; redact private links")


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


def validate_experience_benchmark(item: Any, path: str, findings: list[dict], total_score: float | None) -> None:
    if item in (None, ""):
        return
    if not isinstance(item, dict):
        add(findings, "error", path, "experience_benchmark must be an object")
        return
    if not is_text(item.get("current_band")):
        add(findings, "warning", f"{path}.current_band", "current experience band should be included")
    if not is_text(item.get("next_band")):
        add(findings, "warning", f"{path}.next_band", "next higher experience band should be included")
    bands = item.get("bands")
    if not isinstance(bands, list) or not bands:
        add(findings, "warning", f"{path}.bands", "experience benchmark should include current and next-band rows")
        return
    if len(bands) < 2:
        add(findings, "warning", f"{path}.bands", "include at least current band and next higher band")
    for band_index, band in enumerate(bands):
        band_path = f"{path}.bands[{band_index}]"
        if not isinstance(band, dict):
            add(findings, "error", band_path, "benchmark band must be an object")
            continue
        if not is_text(band.get("band")):
            add(findings, "error", f"{band_path}.band", "band label is required")
        average = numeric_score(band.get("average_score"))
        if average is None:
            add(findings, "error", f"{band_path}.average_score", "average_score must be numeric")
        elif average < 0 or average > 100:
            add(findings, "error", f"{band_path}.average_score", "average_score must be 0-100")
        for optional_key in ("competitive_score", "excellent_score", "candidate_delta"):
            value = band.get(optional_key)
            if value not in (None, "") and numeric_score(value) is None:
                add(findings, "error", f"{band_path}.{optional_key}", f"{optional_key} must be numeric when present")
        delta = numeric_score(band.get("candidate_delta"))
        if total_score is not None and average is not None and delta is not None:
            expected_delta = total_score - average
            if abs(delta - expected_delta) > 1.0:
                add(findings, "warning", f"{band_path}.candidate_delta", f"candidate_delta differs from total_score - average_score ({expected_delta:g})")


def validate_presentation_review(item: Any, path: str, findings: list[dict]) -> None:
    if item in (None, ""):
        return
    if not isinstance(item, dict):
        add(findings, "error", path, "presentation_review must be an object")
        return
    score = numeric_score(item.get("score"))
    if score is None or score < 0 or score > 100:
        add(findings, "error", f"{path}.score", "presentation score must be 0-100")
    confidence = item.get("confidence")
    if confidence not in (None, "") and confidence not in CONFIDENCE_VALUES:
        add(findings, "error", f"{path}.confidence", f"confidence must be one of {sorted(CONFIDENCE_VALUES)}")
    layout_evidence = item.get("layout_evidence")
    if layout_evidence not in (None, "") and layout_evidence not in LAYOUT_EVIDENCE_CAPS:
        add(findings, "error", f"{path}.layout_evidence", f"layout_evidence must be one of {sorted(LAYOUT_EVIDENCE_CAPS)}")
    if score is not None and layout_evidence in LAYOUT_EVIDENCE_CAPS:
        cap = LAYOUT_EVIDENCE_CAPS[layout_evidence]
        if score > cap:
            add(findings, "warning", f"{path}.score", f"presentation score exceeds cap {cap} for layout_evidence={layout_evidence}")
    if confidence == "high" and layout_evidence in {"pasted_text", "ocr_only"}:
        add(findings, "warning", f"{path}.confidence", f"high confidence is not appropriate for layout_evidence={layout_evidence}")
    if not is_text(item.get("summary")):
        add(findings, "warning", f"{path}.summary", "presentation_review should include a short summary")
    criteria = item.get("criteria")
    if not isinstance(criteria, list) or not criteria:
        add(findings, "warning", f"{path}.criteria", "presentation_review should include criteria breakdown")
        return
    sum_score = 0.0
    sum_max = 0.0
    for criterion_index, criterion in enumerate(criteria):
        criterion_path = f"{path}.criteria[{criterion_index}]"
        if not isinstance(criterion, dict):
            add(findings, "error", criterion_path, "presentation criterion must be an object")
            continue
        for key in ("name", "rationale"):
            if not is_text(criterion.get(key)):
                add(findings, "error", f"{criterion_path}.{key}", f"{key} is required")
        criterion_score = numeric_score(criterion.get("score"))
        max_score = numeric_score(criterion.get("max_score"))
        if criterion_score is None:
            add(findings, "error", f"{criterion_path}.score", "score must be numeric")
            criterion_score = 0.0
        if max_score is None:
            add(findings, "error", f"{criterion_path}.max_score", "max_score must be numeric")
            max_score = 0.0
        if criterion_score < 0 or criterion_score > max_score:
            add(findings, "error", f"{criterion_path}.score", "score must be between 0 and max_score")
        sum_score += criterion_score
        sum_max += max_score
        if not as_list(criterion.get("evidence")):
            add(findings, "warning", f"{criterion_path}.evidence", "criterion should include layout evidence")
        if not as_list(criterion.get("deductions")):
            add(findings, "warning", f"{criterion_path}.deductions", "criterion should include deductions, even if '无明显扣分'")
    if abs(sum_max - 100.0) > 0.01:
        add(findings, "warning", f"{path}.criteria", f"presentation criteria max_score total should be 100, got {sum_max:g}")
    if score is not None and abs(sum_score - score) > 1.0:
        add(findings, "warning", f"{path}.score", f"presentation score differs from criteria sum ({sum_score:g})")


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
    validate_experience_benchmark(item.get("experience_benchmark"), f"{path}.experience_benchmark", findings, total)
    validate_presentation_review(item.get("presentation_review"), f"{path}.presentation_review", findings)


def validate_comparison(item: Any, path: str, findings: list[dict], score_mode: str, resume_count: int) -> None:
    if item in (None, ""):
        return
    if not isinstance(item, dict):
        add(findings, "error", path, "comparison must be an object")
        return
    context_type = item.get("context_type")
    if context_type not in (None, "") and context_type not in COMPARISON_CONTEXT_VALUES:
        add(findings, "error", f"{path}.context_type", f"context_type must be one of {sorted(COMPARISON_CONTEXT_VALUES)}")
    if resume_count > 1 and not is_text(item.get("reason")):
        add(findings, "warning", f"{path}.reason", "comparison should include a reason")
    if score_mode == "cross_industry_comparison":
        if not as_list(item.get("best_for")):
            add(findings, "warning", f"{path}.best_for", "cross-industry comparison should include scenario-specific best_for entries")
        axes = item.get("normalized_axes")
        if not isinstance(axes, list) or not axes:
            add(findings, "warning", f"{path}.normalized_axes", "cross-industry comparison should include normalized_axes")
        else:
            for axis_index, axis in enumerate(axes):
                axis_path = f"{path}.normalized_axes[{axis_index}]"
                if not isinstance(axis, dict):
                    add(findings, "error", axis_path, "normalized axis must be an object")
                    continue
                if not is_text(axis.get("axis")):
                    add(findings, "error", f"{axis_path}.axis", "axis is required")
                if not is_text(axis.get("winner")):
                    add(findings, "warning", f"{axis_path}.winner", "winner should be included")
                if not is_text(axis.get("reason")):
                    add(findings, "warning", f"{axis_path}.reason", "reason should be included")


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
    validate_comparison(analysis.get("comparison"), "comparison", findings, str(mode or ""), len(resumes) if isinstance(resumes, list) else 0)
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
    parser.add_argument("--redacted-output", help="Write a redacted copy of the analysis JSON, then validate that redacted payload")
    args = parser.parse_args()

    analysis = load_json(Path(args.analysis).expanduser().resolve())
    if args.redacted_output:
        output = Path(args.redacted_output).expanduser().resolve()
        analysis = redact_payload(analysis)
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(json.dumps(analysis, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        print(f"Wrote redacted analysis to {output}")
    findings = validate_analysis_payload(analysis)
    print(format_findings(findings))
    has_error = any(item["level"] == "error" for item in findings)
    has_warning = any(item["level"] == "warning" for item in findings)
    if has_error or (args.strict and has_warning):
        raise SystemExit(1)


if __name__ == "__main__":
    main()
