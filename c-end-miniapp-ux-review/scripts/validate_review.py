#!/usr/bin/env python3
"""Validate a strict C-end miniapp UX review and calculate report quality."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any


MODES = {"spec_only", "static_artifact", "interactive_flow"}
GRADES = {"observed", "specified", "inferred", "unknown"}
SEVERITIES = {"P0", "P1", "P2", "Opportunity"}
CONFIDENCE = {"high", "medium", "low"}
HEALTH = {"healthy", "risk", "blocked", "unknown"}
APPLICABILITY = {"applicable", "not_applicable"}
CORE_STATES = {
    "initial",
    "loading",
    "empty",
    "partial_success",
    "success",
    "failure",
    "no_permission",
    "offline",
    "timeout",
    "session_expired",
    "duplicate_submit",
    "unsupported_version",
}


def nonempty(value: Any) -> bool:
    if isinstance(value, str):
        return bool(value.strip())
    if isinstance(value, (list, dict)):
        return bool(value)
    return value is not None


def require_fields(item: dict[str, Any], fields: list[str], prefix: str, errors: list[str]) -> None:
    for field in fields:
        if field not in item or not nonempty(item[field]):
            errors.append(f"{prefix}.{field} is required")


def unique_ids(items: list[dict[str, Any]], field: str, prefix: str, errors: list[str]) -> set[str]:
    ids: set[str] = set()
    for index, item in enumerate(items):
        value = item.get(field)
        if not nonempty(value):
            errors.append(f"{prefix}[{index}].{field} is required")
        elif value in ids:
            errors.append(f"duplicate {field}: {value}")
        else:
            ids.add(value)
    return ids


def check_refs(refs: Any, valid: set[str], prefix: str, errors: list[str], allow_empty: bool = False) -> None:
    if not isinstance(refs, list):
        errors.append(f"{prefix} must be an array")
        return
    if not refs and not allow_empty:
        errors.append(f"{prefix} must not be empty")
    for ref in refs:
        if ref not in valid:
            errors.append(f"{prefix} references missing id: {ref}")


def validate(data: dict[str, Any]) -> tuple[int, list[str], list[str], dict[str, int]]:
    errors: list[str] = []
    warnings: list[str] = []
    sections = {
        "scope": 0,
        "evidence": 0,
        "flow": 0,
        "states": 0,
        "findings": 0,
        "recommendations": 0,
        "priority": 0,
        "prd": 0,
        "clarity": 0,
    }

    required_top = [
        "meta",
        "scope",
        "evidence",
        "flow_steps",
        "state_matrix",
        "findings",
        "prd_updates",
        "validation_plan",
        "limitations",
    ]
    for key in required_top:
        if key not in data:
            errors.append(f"top-level field missing: {key}")

    meta = data.get("meta", {})
    scope = data.get("scope", {})
    evidence = data.get("evidence", [])
    flow = data.get("flow_steps", [])
    states = data.get("state_matrix", [])
    findings = data.get("findings", [])
    prd_updates = data.get("prd_updates", [])
    validation_plan = data.get("validation_plan", [])
    limitations = data.get("limitations", [])

    if not isinstance(meta, dict) or not isinstance(scope, dict):
        errors.append("meta and scope must be objects")
        return 0, errors, warnings, sections
    for name, value in [
        ("evidence", evidence),
        ("flow_steps", flow),
        ("state_matrix", states),
        ("findings", findings),
        ("prd_updates", prd_updates),
        ("validation_plan", validation_plan),
        ("limitations", limitations),
    ]:
        if not isinstance(value, list):
            errors.append(f"{name} must be an array")
            return 0, errors, warnings, sections

    require_fields(meta, ["review_id", "mode", "round"], "meta", errors)
    if meta.get("mode") not in MODES:
        errors.append(f"meta.mode must be one of {sorted(MODES)}")
    require_fields(
        scope,
        ["surface", "target_user", "context", "user_goal", "success_outcome", "start", "end", "non_goals"],
        "scope",
        errors,
    )
    if all(nonempty(scope.get(key)) for key in ["target_user", "user_goal", "success_outcome", "start", "end", "non_goals"]):
        sections["scope"] = 10

    evidence_ids = unique_ids(evidence, "evidence_id", "evidence", errors)
    evidence_by_id: dict[str, dict[str, Any]] = {}
    evidence_ok = bool(evidence)
    for index, item in enumerate(evidence):
        require_fields(item, ["source", "kind", "grade", "limitations"], f"evidence[{index}]", errors)
        if item.get("grade") not in GRADES:
            errors.append(f"evidence[{index}].grade must be one of {sorted(GRADES)}")
            evidence_ok = False
        if nonempty(item.get("evidence_id")):
            evidence_by_id[item["evidence_id"]] = item
    mode = meta.get("mode")
    if mode == "spec_only" and any(item.get("grade") == "observed" for item in evidence):
        errors.append("spec_only mode cannot contain observed evidence")
        evidence_ok = False
    if mode == "interactive_flow" and not any(item.get("grade") == "observed" for item in evidence):
        errors.append("interactive_flow mode requires at least one observed evidence item")
        evidence_ok = False
    if evidence_ok and limitations:
        sections["evidence"] = 15

    step_ids = unique_ids(flow, "step_id", "flow_steps", errors)
    flow_ok = bool(flow)
    orders: list[int] = []
    for index, item in enumerate(flow):
        require_fields(
            item,
            ["order", "name", "user_intent", "user_action", "system_response", "next_or_recovery", "evidence_refs", "health"],
            f"flow_steps[{index}]",
            errors,
        )
        if isinstance(item.get("order"), int):
            orders.append(item["order"])
        else:
            errors.append(f"flow_steps[{index}].order must be an integer")
            flow_ok = False
        if item.get("health") not in HEALTH:
            errors.append(f"flow_steps[{index}].health must be one of {sorted(HEALTH)}")
            flow_ok = False
        check_refs(item.get("evidence_refs"), evidence_ids, f"flow_steps[{index}].evidence_refs", errors)
    if orders and sorted(orders) != list(range(1, len(orders) + 1)):
        errors.append("flow_steps.order must be contiguous starting at 1")
        flow_ok = False
    if flow_ok:
        sections["flow"] = 15

    states_seen: set[str] = set()
    states_ok = bool(states)
    for index, item in enumerate(states):
        require_fields(item, ["state", "applicability"], f"state_matrix[{index}]", errors)
        state = item.get("state")
        if state in states_seen:
            errors.append(f"duplicate state: {state}")
            states_ok = False
        states_seen.add(state)
        applicability = item.get("applicability")
        if applicability not in APPLICABILITY:
            errors.append(f"state_matrix[{index}].applicability must be one of {sorted(APPLICABILITY)}")
            states_ok = False
        elif applicability == "not_applicable":
            require_fields(item, ["reason"], f"state_matrix[{index}]", errors)
        else:
            require_fields(
                item,
                ["trigger", "visible_feedback", "allowed_actions", "recovery", "evidence_refs"],
                f"state_matrix[{index}]",
                errors,
            )
            check_refs(item.get("evidence_refs"), evidence_ids, f"state_matrix[{index}].evidence_refs", errors, allow_empty=True)
    missing_states = sorted(CORE_STATES - states_seen)
    if missing_states:
        errors.append(f"state_matrix missing core states: {', '.join(missing_states)}")
        states_ok = False
    if states_ok:
        sections["states"] = 15

    finding_ids = unique_ids(findings, "finding_id", "findings", errors)
    findings_ok = bool(findings)
    rec_ok = bool(findings)
    priority_ok = bool(findings)
    normalized_problems: set[str] = set()
    for index, item in enumerate(findings):
        require_fields(
            item,
            [
                "step_ids",
                "layer",
                "severity",
                "confidence",
                "evidence_grade",
                "evidence_refs",
                "problem",
                "user_impact",
                "recommendation",
                "validation",
            ],
            f"findings[{index}]",
            errors,
        )
        check_refs(item.get("step_ids"), step_ids, f"findings[{index}].step_ids", errors)
        check_refs(item.get("evidence_refs"), evidence_ids, f"findings[{index}].evidence_refs", errors)
        if item.get("severity") not in SEVERITIES:
            errors.append(f"findings[{index}].severity must be one of {sorted(SEVERITIES)}")
            priority_ok = False
        if item.get("confidence") not in CONFIDENCE:
            errors.append(f"findings[{index}].confidence must be one of {sorted(CONFIDENCE)}")
            findings_ok = False
        if item.get("evidence_grade") not in GRADES:
            errors.append(f"findings[{index}].evidence_grade must be one of {sorted(GRADES)}")
            findings_ok = False
        finding_grade = item.get("evidence_grade")
        referenced_grades = {
            evidence_by_id[ref].get("grade")
            for ref in item.get("evidence_refs", [])
            if ref in evidence_by_id
        }
        if finding_grade in {"observed", "specified"} and finding_grade not in referenced_grades:
            errors.append(
                f"findings[{index}].evidence_grade={finding_grade} has no matching referenced evidence grade"
            )
            findings_ok = False
        problem = " ".join(str(item.get("problem", "")).lower().split())
        if problem in normalized_problems:
            errors.append(f"duplicate normalized problem at findings[{index}]")
            priority_ok = False
        normalized_problems.add(problem)
        if item.get("severity") in {"P0", "P1"} and item.get("evidence_grade") == "unknown":
            errors.append(f"findings[{index}] P0/P1 cannot use unknown evidence")
            findings_ok = False
        if not nonempty(item.get("recommendation")) or not nonempty(item.get("validation")):
            rec_ok = False
    if findings_ok:
        sections["findings"] = 15
    if rec_ok:
        sections["recommendations"] = 15
    if priority_ok:
        sections["priority"] = 5

    prd_ok = bool(prd_updates)
    for index, item in enumerate(prd_updates):
        require_fields(item, ["update_id", "type", "text", "finding_refs"], f"prd_updates[{index}]", errors)
        check_refs(item.get("finding_refs"), finding_ids, f"prd_updates[{index}].finding_refs", errors)
    if prd_ok:
        sections["prd"] = 5

    validation_ok = bool(validation_plan)
    for index, item in enumerate(validation_plan):
        require_fields(item, ["validation_id", "method", "target", "pass_condition"], f"validation_plan[{index}]", errors)
        target = item.get("target")
        if target not in finding_ids and target not in step_ids:
            errors.append(f"validation_plan[{index}].target references missing finding or step: {target}")
            validation_ok = False

    if limitations and validation_ok:
        sections["clarity"] = 5
    elif not limitations:
        errors.append("limitations must not be empty")

    score = sum(sections.values())
    if errors:
        warnings.append("Hard gate failed; report cannot pass regardless of numeric score.")
    return score, errors, warnings, sections


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("review", type=Path, help="Path to strict review JSON")
    parser.add_argument("--min-score", type=int, default=95, help="Minimum passing report-quality score")
    args = parser.parse_args()

    try:
        data = json.loads(args.review.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        print(json.dumps({"status": "invalid", "score": 0, "errors": [str(exc)]}, ensure_ascii=False, indent=2))
        return 2
    if not isinstance(data, dict):
        print(json.dumps({"status": "invalid", "score": 0, "errors": ["top-level JSON must be an object"]}, ensure_ascii=False, indent=2))
        return 2

    score, errors, warnings, sections = validate(data)
    passed = score >= args.min_score and not errors
    result = {
        "status": "pass" if passed else "fail",
        "score": score,
        "min_score": args.min_score,
        "hard_gates_passed": not errors,
        "sections": sections,
        "errors": errors,
        "warnings": warnings,
    }
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if passed else 1


if __name__ == "__main__":
    sys.exit(main())
