#!/usr/bin/env python3
"""Validate resume-scorecard v2 analysis JSON."""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
from typing import Any


SCHEMA_VERSION = "2.0"
SCORE_MODES = {"standalone", "jd_fit", "comparison", "cross_industry_comparison"}
CONFIDENCE_VALUES = {"high", "medium", "low"}
SEVERITY_VALUES = {"high", "medium", "low"}
ROLE_FAMILIES = {
    "engineering_data",
    "product_design",
    "sales_growth_ops",
    "corporate_functions",
    "research_professional",
    "leadership_management",
    "general",
}
CANDIDATE_STAGES = {
    "intern_entry",
    "early_career",
    "experienced_ic",
    "senior_ic",
    "manager_lead",
    "career_changer",
}
AXIS_DIMENSIONS = {
    "career_capital": {
        "relevance_trajectory": 15,
        "complexity_scope": 20,
        "ownership": 20,
        "impact_value": 20,
        "expertise_scarcity": 15,
        "growth_validation": 10,
    },
    "communication_quality": {
        "positioning": 20,
        "selection_prioritization": 20,
        "evidence_expression": 25,
        "semantic_clarity": 20,
        "consistency_defensibility": 15,
    },
    "presentation_quality": {
        "visual_hierarchy": 25,
        "density_whitespace": 20,
        "typography_alignment": 15,
        "visual_organization": 15,
        "ats_layout": 15,
        "professional_fit": 10,
    },
    "jd_fit": {
        "must_haves": 35,
        "responsibility_match": 25,
        "seniority_scope": 15,
        "domain_tools": 15,
        "targeted_evidence": 10,
    },
}
LAYOUT_EVIDENCE_CAPS = {
    "rendered_file": (100, "high"),
    "file_structure": (90, "high"),
    "extracted_text": (82, "medium"),
    "pasted_text": (75, "medium"),
    "ocr_only": (65, "low"),
}
STAGE_LINES = {
    "intern_entry": (60, 75, 88),
    "early_career": (68, 80, 90),
    "experienced_ic": (74, 84, 92),
    "senior_ic": (80, 88, 94),
    "manager_lead": (82, 90, 95),
}
ISSUE_KINDS = {"gap", "risk", "contradiction", "layout"}
ISSUE_AXES = set(AXIS_DIMENSIONS) | {"none"}
COMPARISON_CONTEXTS = {"same_target", "same_industry", "cross_role", "cross_industry", "universal_baseline"}

EMAIL_RE = re.compile(r"[\w.+-]+@[\w.-]+\.[A-Za-z]{2,}")
PHONE_RE = re.compile(r"(?<!\d)(?:\+?\d[\d\s().-]{7,}\d)(?!\d)")
DATE_PREFIX_RE = re.compile(r"\b(?:19|20)\d{2}[-/.]\d{1,2}[-/.]\d{1,2}")
CN_ID_RE = re.compile(r"(?<!\d)[1-9]\d{5}(?:18|19|20)\d{2}(?:0[1-9]|1[0-2])(?:0[1-9]|[12]\d|3[01])\d{3}[\dXx](?!\d)")
URL_RE = re.compile(r"https?://[^\s<>)\"']+")
SENSITIVE_URL_RE = re.compile(r"(?i)(?:access[_-]?token|auth[_-]?key|api[_-]?key|signature|sig|token|secret|code)=")
PRIVATE_HOST_RE = re.compile(r"(?i)(?:localhost|127\.0\.0\.1|0\.0\.0\.0|docs\.qq\.com|feishu\.cn|larksuite\.com|notion\.site|sharepoint\.com)")
TOKEN_RE = re.compile(r"(?i)\b(?:api[_-]?key|access[_-]?token|secret|bearer|authorization)\b\s*[:=]\s*['\"]?[A-Za-z0-9._~+/=-]{12,}")
ADDRESS_RE = re.compile(r"[\u4e00-\u9fff]{2,}(?:省|市|区|县)[\u4e00-\u9fff0-9A-Za-z]{0,30}(?:路|街|巷|弄|号|小区|大厦|单元|室)")
GAIN_RE = re.compile(r"^\+(\d+(?:\.\d+)?)-(\d+(?:\.\d+)?)$")


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
    return value if isinstance(value, list) else [value]


def is_text(value: Any) -> bool:
    return isinstance(value, str) and bool(value.strip())


def number(value: Any) -> float | None:
    if isinstance(value, bool):
        return None
    if isinstance(value, (int, float)):
        return float(value)
    try:
        return float(str(value))
    except Exception:
        return None


def add(findings: list[dict], level: str, path: str, message: str) -> None:
    findings.append({"level": level, "path": path, "message": message})


def infer_band(score: float) -> str:
    if score >= 90:
        return "A+"
    if score >= 80:
        return "A"
    if score >= 70:
        return "B"
    if score >= 60:
        return "C"
    return "D"


def coverage_status(score: float) -> str:
    if score >= 85:
        return "high"
    if score >= 60:
        return "medium"
    return "low"


def looks_like_phone(candidate: str) -> bool:
    if DATE_PREFIX_RE.search(candidate):
        return False
    digits = re.sub(r"\D", "", candidate)
    return bool(
        re.fullmatch(r"1[3-9]\d{9}", digits)
        or (candidate.strip().startswith("+") and len(digits) >= 10)
        or (re.search(r"\(\d{2,4}\)", candidate) and len(digits) >= 10)
    )


def looks_like_sensitive_url(candidate: str) -> bool:
    return bool(SENSITIVE_URL_RE.search(candidate) or PRIVATE_HOST_RE.search(candidate))


def redact_text(value: str) -> str:
    value = TOKEN_RE.sub("[已脱敏密钥]", value)
    value = CN_ID_RE.sub("[已脱敏身份证]", value)
    value = ADDRESS_RE.sub("[已脱敏地址]", value)
    value = EMAIL_RE.sub("[已脱敏邮箱]", value)
    value = PHONE_RE.sub(lambda match: "[已脱敏电话]" if looks_like_phone(match.group(0)) else match.group(0), value)
    value = URL_RE.sub(lambda match: "[已脱敏私有链接]" if looks_like_sensitive_url(match.group(0)) else match.group(0), value)
    return value


def redact_payload(value: Any) -> Any:
    if isinstance(value, dict):
        return {key: redact_payload(child) for key, child in value.items()}
    if isinstance(value, list):
        return [redact_payload(child) for child in value]
    return redact_text(value) if isinstance(value, str) else value


def scan_pii(value: Any, findings: list[dict], path: str = "$") -> None:
    if isinstance(value, dict):
        for key, child in value.items():
            scan_pii(child, findings, f"{path}.{key}")
    elif isinstance(value, list):
        for index, child in enumerate(value):
            scan_pii(child, findings, f"{path}[{index}]")
    elif isinstance(value, str):
        if EMAIL_RE.search(value):
            add(findings, "warning", path, "text appears to contain an email address")
        if any(looks_like_phone(match.group(0)) for match in PHONE_RE.finditer(value)):
            add(findings, "warning", path, "text appears to contain a phone number")
        if CN_ID_RE.search(value):
            add(findings, "warning", path, "text appears to contain a Chinese ID number")
        if ADDRESS_RE.search(value):
            add(findings, "warning", path, "text may contain an exact address")
        if TOKEN_RE.search(value):
            add(findings, "warning", path, "text appears to contain a secret/token")
        if any(looks_like_sensitive_url(match.group(0)) for match in URL_RE.finditer(value)):
            add(findings, "warning", path, "text appears to contain a private or tokenized URL")


def validate_dimension(item: Any, axis: str, path: str, findings: list[dict]) -> tuple[float, float, str]:
    if not isinstance(item, dict):
        add(findings, "error", path, "dimension must be an object")
        return 0.0, 0.0, ""
    dim_id = str(item.get("id") or "")
    expected = AXIS_DIMENSIONS[axis]
    if dim_id not in expected:
        add(findings, "error", f"{path}.id", f"unexpected dimension id for {axis}: {dim_id or '<missing>'}")
    for key in ("name", "rationale"):
        if not is_text(item.get(key)):
            add(findings, "error", f"{path}.{key}", f"{key} is required")
    score = number(item.get("score"))
    max_score = number(item.get("max_score"))
    if score is None:
        add(findings, "error", f"{path}.score", "score must be numeric")
        score = 0.0
    if max_score is None:
        add(findings, "error", f"{path}.max_score", "max_score must be numeric")
        max_score = 0.0
    if dim_id in expected and abs(max_score - expected[dim_id]) > 0.01:
        add(findings, "error", f"{path}.max_score", f"{dim_id} max_score must be {expected[dim_id]}")
    if score < 0 or score > max_score:
        add(findings, "error", f"{path}.score", "score must be between 0 and max_score")
    confidence = item.get("confidence")
    if confidence not in CONFIDENCE_VALUES:
        add(findings, "error", f"{path}.confidence", f"confidence must be one of {sorted(CONFIDENCE_VALUES)}")
    if score > 0 and not as_list(item.get("evidence")):
        add(findings, "warning", f"{path}.evidence", "positive scores require positive evidence")
    for optional_list in ("gaps", "lift_actions"):
        if optional_list in item and not isinstance(item.get(optional_list), list):
            add(findings, "error", f"{path}.{optional_list}", f"{optional_list} must be a list")
    return score, max_score, dim_id


def validate_axis(item: Any, axis: str, path: str, findings: list[dict]) -> float | None:
    if not isinstance(item, dict):
        add(findings, "error", path, f"{axis} must be an object")
        return None
    score = number(item.get("score"))
    if score is None or score < 0 or score > 100:
        add(findings, "error", f"{path}.score", "axis score must be 0-100")
    band = item.get("band")
    if score is not None and band != infer_band(score):
        add(findings, "error", f"{path}.band", f"band must be {infer_band(score)} for score {score:g}")
    if item.get("confidence") not in CONFIDENCE_VALUES:
        add(findings, "error", f"{path}.confidence", f"confidence must be one of {sorted(CONFIDENCE_VALUES)}")
    if not is_text(item.get("summary")):
        add(findings, "warning", f"{path}.summary", "axis summary should be included")
    dimensions = item.get("dimensions")
    if not isinstance(dimensions, list) or not dimensions:
        add(findings, "error", f"{path}.dimensions", "dimensions must be a non-empty list")
        return score
    sum_score = 0.0
    sum_max = 0.0
    seen: set[str] = set()
    for index, dimension in enumerate(dimensions):
        dim_score, dim_max, dim_id = validate_dimension(dimension, axis, f"{path}.dimensions[{index}]", findings)
        sum_score += dim_score
        sum_max += dim_max
        if dim_id in seen:
            add(findings, "error", f"{path}.dimensions[{index}].id", f"duplicate dimension id: {dim_id}")
        seen.add(dim_id)
    missing = set(AXIS_DIMENSIONS[axis]) - seen
    if missing:
        add(findings, "error", f"{path}.dimensions", f"missing dimensions: {sorted(missing)}")
    if abs(sum_max - 100) > 0.01:
        add(findings, "error", f"{path}.dimensions", f"dimension max_score total must be 100, got {sum_max:g}")
    if score is not None and abs(sum_score - score) > 0.1:
        add(findings, "error", f"{path}.score", f"axis score must equal dimension sum {sum_score:g}")
    if axis == "presentation_quality":
        evidence = item.get("layout_evidence")
        if evidence not in LAYOUT_EVIDENCE_CAPS:
            add(findings, "error", f"{path}.layout_evidence", f"layout_evidence must be one of {sorted(LAYOUT_EVIDENCE_CAPS)}")
        elif score is not None:
            cap, max_confidence = LAYOUT_EVIDENCE_CAPS[evidence]
            if score > cap:
                add(findings, "error", f"{path}.score", f"presentation score exceeds cap {cap} for {evidence}")
            if item.get("confidence") == "high" and max_confidence != "high":
                add(findings, "error", f"{path}.confidence", f"high confidence is not allowed for {evidence}")
            if evidence == "ocr_only" and item.get("confidence") != "low":
                add(findings, "warning", f"{path}.confidence", "ocr_only should use low presentation confidence")
    return score


def validate_evidence_coverage(item: Any, path: str, findings: list[dict]) -> None:
    if not isinstance(item, dict):
        add(findings, "error", path, "evidence_coverage must be an object")
        return
    score = number(item.get("score"))
    if score is None or score < 0 or score > 100:
        add(findings, "error", f"{path}.score", "evidence coverage score must be 0-100")
    elif item.get("status") != coverage_status(score):
        add(findings, "error", f"{path}.status", f"status must be {coverage_status(score)} for score {score:g}")
    if not is_text(item.get("summary")):
        add(findings, "warning", f"{path}.summary", "evidence coverage summary should be included")
    if "missing_evidence" in item and not isinstance(item.get("missing_evidence"), list):
        add(findings, "error", f"{path}.missing_evidence", "missing_evidence must be a list")


def validate_issue_ledger(items: Any, axes: dict, path: str, findings: list[dict]) -> None:
    if not isinstance(items, list):
        add(findings, "error", path, "issue_ledger must be a list")
        return
    seen: set[str] = set()
    for index, item in enumerate(items):
        item_path = f"{path}[{index}]"
        if not isinstance(item, dict):
            add(findings, "error", item_path, "issue must be an object")
            continue
        issue_id = str(item.get("issue_id") or "")
        if not issue_id:
            add(findings, "error", f"{item_path}.issue_id", "issue_id is required")
        elif issue_id in seen:
            add(findings, "error", f"{item_path}.issue_id", f"duplicate issue_id: {issue_id}")
        seen.add(issue_id)
        for key in ("title", "detail"):
            if not is_text(item.get(key)):
                add(findings, "error", f"{item_path}.{key}", f"{key} is required")
        if not as_list(item.get("evidence")):
            add(findings, "warning", f"{item_path}.evidence", "issue should include evidence")
        kind = item.get("kind")
        if kind not in ISSUE_KINDS:
            add(findings, "error", f"{item_path}.kind", f"kind must be one of {sorted(ISSUE_KINDS)}")
        if item.get("severity") not in SEVERITY_VALUES:
            add(findings, "error", f"{item_path}.severity", f"severity must be one of {sorted(SEVERITY_VALUES)}")
        primary_axis = item.get("primary_axis")
        primary_dimension = str(item.get("primary_dimension") or "")
        points = number(item.get("points"))
        if primary_axis not in ISSUE_AXES:
            add(findings, "error", f"{item_path}.primary_axis", f"primary_axis must be one of {sorted(ISSUE_AXES)}")
        if points is None or points > 0:
            add(findings, "error", f"{item_path}.points", "points must be numeric, zero, or negative")
        if primary_axis == "none":
            if primary_dimension:
                add(findings, "error", f"{item_path}.primary_dimension", "primary_dimension must be empty when primary_axis is none")
            if points not in (None, 0.0):
                add(findings, "error", f"{item_path}.points", "points must be 0 when primary_axis is none")
        elif primary_axis in AXIS_DIMENSIONS:
            if primary_axis not in axes:
                add(findings, "error", f"{item_path}.primary_axis", f"axis {primary_axis} is not present in score_axes")
            if primary_dimension not in AXIS_DIMENSIONS[primary_axis]:
                add(findings, "error", f"{item_path}.primary_dimension", f"dimension does not belong to {primary_axis}")
        if kind == "layout" and primary_axis != "presentation_quality":
            add(findings, "error", f"{item_path}.primary_axis", "layout issues may only target presentation_quality")
        if primary_axis == "presentation_quality" and kind != "layout":
            add(findings, "warning", f"{item_path}.kind", "presentation issues should normally use kind=layout")


def validate_stage_benchmark(item: Any, career_score: float | None, path: str, findings: list[dict]) -> None:
    if item in (None, ""):
        return
    if not isinstance(item, dict):
        add(findings, "error", path, "stage_benchmark must be an object")
        return
    if item.get("benchmark_type") != "internal_expectation":
        add(findings, "error", f"{path}.benchmark_type", "benchmark_type must be internal_expectation")
    if item.get("basis_axis") != "career_capital":
        add(findings, "error", f"{path}.basis_axis", "stage benchmark must use career_capital")
    note = str(item.get("note") or "")
    if ("市场平均" in note or "百分位" in note) and "不是" not in note:
        add(findings, "warning", f"{path}.note", "do not present internal anchors as market averages or percentiles")
    stages = item.get("stages")
    if not isinstance(stages, list) or not stages:
        add(findings, "error", f"{path}.stages", "stage benchmark requires stage rows")
        return
    for index, row in enumerate(stages):
        row_path = f"{path}.stages[{index}]"
        if not isinstance(row, dict):
            add(findings, "error", row_path, "stage row must be an object")
            continue
        stage = row.get("stage")
        if stage not in STAGE_LINES:
            add(findings, "error", f"{row_path}.stage", f"stage must be one of {sorted(STAGE_LINES)}")
            continue
        for key, expected in zip(("reference_score", "strong_score", "exceptional_score"), STAGE_LINES[stage]):
            value = number(row.get(key))
            if value is None or abs(value - expected) > 0.01:
                add(findings, "error", f"{row_path}.{key}", f"{key} must be {expected} for {stage}")
        delta = number(row.get("candidate_delta"))
        reference = number(row.get("reference_score"))
        if career_score is not None and reference is not None and delta is not None and abs(delta - (career_score - reference)) > 0.1:
            add(findings, "error", f"{row_path}.candidate_delta", f"candidate_delta must equal career_capital - reference_score ({career_score - reference:g})")


def validate_score_lifts(items: Any, axes: dict, path: str, findings: list[dict]) -> None:
    if not isinstance(items, list):
        add(findings, "error", path, "score_lifts must be a list")
        return
    for index, item in enumerate(items):
        item_path = f"{path}[{index}]"
        if not isinstance(item, dict):
            add(findings, "error", item_path, "score lift must be an object")
            continue
        axis = item.get("axis")
        if axis not in axes:
            add(findings, "error", f"{item_path}.axis", "score-lift axis must exist in score_axes")
        for key in ("action", "why"):
            if not is_text(item.get(key)):
                add(findings, "error", f"{item_path}.{key}", f"{key} is required")
        match = GAIN_RE.match(str(item.get("estimated_gain") or ""))
        if not match:
            add(findings, "error", f"{item_path}.estimated_gain", "estimated_gain must be a range like +2-4")
        elif axis in axes:
            upper = float(match.group(2))
            axis_score = number(axes[axis].get("score")) if isinstance(axes.get(axis), dict) else None
            if axis_score is not None and axis_score + upper > 100.01:
                add(findings, "warning", f"{item_path}.estimated_gain", "estimated gain exceeds the axis ceiling")


def validate_resume(item: Any, index: int, jd_provided: bool, findings: list[dict]) -> None:
    path = f"resumes[{index}]"
    if not isinstance(item, dict):
        add(findings, "error", path, "resume must be an object")
        return
    for key in ("id", "name", "scoring_context", "score_summary"):
        if not is_text(item.get(key)):
            add(findings, "error", f"{path}.{key}", f"{key} is required")
    if item.get("role_family") not in ROLE_FAMILIES:
        add(findings, "error", f"{path}.role_family", f"role_family must be one of {sorted(ROLE_FAMILIES)}")
    if item.get("candidate_stage") not in CANDIDATE_STAGES:
        add(findings, "error", f"{path}.candidate_stage", f"candidate_stage must be one of {sorted(CANDIDATE_STAGES)}")
    axes = item.get("score_axes")
    if not isinstance(axes, dict):
        add(findings, "error", f"{path}.score_axes", "score_axes must be an object")
        axes = {}
    axis_scores: dict[str, float | None] = {}
    for required_axis in ("career_capital", "communication_quality"):
        if required_axis not in axes:
            add(findings, "error", f"{path}.score_axes.{required_axis}", f"{required_axis} is required")
        else:
            axis_scores[required_axis] = validate_axis(axes[required_axis], required_axis, f"{path}.score_axes.{required_axis}", findings)
    if "presentation_quality" in axes:
        axis_scores["presentation_quality"] = validate_axis(axes["presentation_quality"], "presentation_quality", f"{path}.score_axes.presentation_quality", findings)
    if jd_provided:
        if "jd_fit" not in axes:
            add(findings, "error", f"{path}.score_axes.jd_fit", "jd_fit is required when jd_provided is true")
        else:
            axis_scores["jd_fit"] = validate_axis(axes["jd_fit"], "jd_fit", f"{path}.score_axes.jd_fit", findings)
    elif "jd_fit" in axes:
        add(findings, "error", f"{path}.score_axes.jd_fit", "jd_fit must be omitted when jd_provided is false")
    unexpected_axes = set(axes) - set(AXIS_DIMENSIONS)
    if unexpected_axes:
        add(findings, "error", f"{path}.score_axes", f"unexpected axes: {sorted(unexpected_axes)}")
    career = axis_scores.get("career_capital")
    communication = axis_scores.get("communication_quality")
    core = number(item.get("core_score"))
    if core is None or core < 0 or core > 100:
        add(findings, "error", f"{path}.core_score", "core_score must be 0-100")
    if career is not None and communication is not None and core is not None:
        expected_core = round(career * 0.7 + communication * 0.3, 1)
        if abs(core - expected_core) > 0.1:
            add(findings, "error", f"{path}.core_score", f"core_score must equal 70% career + 30% communication ({expected_core:g})")
    if core is not None and item.get("band") != infer_band(core):
        add(findings, "error", f"{path}.band", f"band must be {infer_band(core)} for core_score {core:g}")
    validate_evidence_coverage(item.get("evidence_coverage"), f"{path}.evidence_coverage", findings)
    validate_issue_ledger(item.get("issue_ledger"), axes, f"{path}.issue_ledger", findings)
    validate_stage_benchmark(item.get("stage_benchmark"), career, f"{path}.stage_benchmark", findings)
    validate_score_lifts(item.get("score_lifts", []), axes, f"{path}.score_lifts", findings)


def validate_comparison(item: Any, mode: str, resume_count: int, findings: list[dict]) -> None:
    required = mode in {"comparison", "cross_industry_comparison"} or resume_count > 1
    if not required and item in (None, ""):
        return
    if not isinstance(item, dict):
        add(findings, "error", "comparison", "comparison object is required")
        return
    if item.get("context_type") not in COMPARISON_CONTEXTS:
        add(findings, "error", "comparison.context_type", f"context_type must be one of {sorted(COMPARISON_CONTEXTS)}")
    if not is_text(item.get("reason")):
        add(findings, "warning", "comparison.reason", "comparison should include a reason")
    axes = item.get("normalized_axes")
    if mode == "cross_industry_comparison" and (not isinstance(axes, list) or not axes):
        add(findings, "error", "comparison.normalized_axes", "cross-industry comparison requires normalized axes")
    for index, axis in enumerate(as_list(axes)):
        axis_path = f"comparison.normalized_axes[{index}]"
        if not isinstance(axis, dict):
            add(findings, "error", axis_path, "normalized axis must be an object")
            continue
        if not is_text(axis.get("axis")) or not is_text(axis.get("reason")):
            add(findings, "error", axis_path, "axis and reason are required")
        scores = axis.get("scores")
        if not isinstance(scores, dict) or not scores:
            add(findings, "error", f"{axis_path}.scores", "normalized axes require numeric scores")
        else:
            for key, value in scores.items():
                score = number(value)
                if score is None or score < 0 or score > 100:
                    add(findings, "error", f"{axis_path}.scores.{key}", "normalized score must be 0-100")
    if mode == "cross_industry_comparison" and not as_list(item.get("best_for")):
        add(findings, "error", "comparison.best_for", "cross-industry comparison requires scenario-specific best_for entries")


def validate_analysis_payload(analysis: dict) -> list[dict]:
    findings: list[dict] = []
    if str(analysis.get("schema_version") or "") != SCHEMA_VERSION:
        add(findings, "error", "schema_version", f"schema_version must be {SCHEMA_VERSION}")
    for key in ("report_title", "overall_summary"):
        if not is_text(analysis.get(key)):
            add(findings, "error", key, f"{key} is required")
    mode = analysis.get("score_mode")
    if mode not in SCORE_MODES:
        add(findings, "error", "score_mode", f"score_mode must be one of {sorted(SCORE_MODES)}")
    confidence = analysis.get("confidence")
    if confidence not in CONFIDENCE_VALUES:
        add(findings, "error", "confidence", f"confidence must be one of {sorted(CONFIDENCE_VALUES)}")
    jd_provided = analysis.get("jd_provided")
    if not isinstance(jd_provided, bool):
        add(findings, "error", "jd_provided", "jd_provided must be boolean")
        jd_provided = False
    if mode == "jd_fit" and not jd_provided:
        add(findings, "error", "jd_provided", "jd_fit mode requires jd_provided=true")
    if mode == "standalone" and jd_provided:
        add(findings, "error", "score_mode", "standalone mode cannot use jd_provided=true")
    if mode == "cross_industry_comparison" and jd_provided:
        add(findings, "warning", "jd_provided", "cross-industry comparison normally uses own-target scoring, not one shared JD")
    resumes = analysis.get("resumes")
    if not isinstance(resumes, list) or not resumes:
        add(findings, "error", "resumes", "at least one resume is required")
        resumes = []
    for index, resume in enumerate(resumes):
        validate_resume(resume, index, jd_provided, findings)
    if mode in {"comparison", "cross_industry_comparison"} and len(resumes) < 2:
        add(findings, "error", "resumes", f"{mode} requires at least two resumes")
    if mode in {"standalone", "jd_fit"} and len(resumes) > 1:
        add(findings, "error", "score_mode", f"{mode} requires one resume; use comparison mode for multiple resumes")
    validate_comparison(analysis.get("comparison"), str(mode or ""), len(resumes), findings)
    scan_pii(analysis, findings)
    return findings


def format_findings(findings: list[dict]) -> str:
    if not findings:
        return "scorecard v2 validation passed"
    return "\n".join(f"[{item['level'].upper()}] {item['path']}: {item['message']}" for item in findings)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--analysis", required=True, help="resume_scorecard_analysis.json")
    parser.add_argument("--strict", action="store_true", help="Exit non-zero on warnings as well as errors")
    parser.add_argument("--redacted-output", help="Write and validate a redacted copy")
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
