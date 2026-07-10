#!/usr/bin/env python3
"""Run evidence-aware strict render checks for golden project-to-resume examples."""

from __future__ import annotations

import copy
import json
import subprocess
import sys
import tempfile
from pathlib import Path


SKILL_DIR = Path(__file__).resolve().parents[1]
RENDER = SKILL_DIR / "scripts" / "render_resume_report.py"
if str(SKILL_DIR / "scripts") not in sys.path:
    sys.path.insert(0, str(SKILL_DIR / "scripts"))

from validate_analysis import load_evidence_context, validate_analysis_payload


PAIRS = [
    ("vue-admin-golden-analysis.json", "vue-admin-project_evidence.json"),
    ("python-api-golden-analysis.json", "python-api-project_evidence.json"),
    ("node-agent-golden-analysis.json", "node-agent-project_evidence.json"),
]


def assert_finding(findings: list[dict], path_prefix: str, level: str | None = None) -> None:
    matched = [item for item in findings if str(item.get("path", "")).startswith(path_prefix)]
    if level:
        matched = [item for item in matched if item.get("level") == level]
    if not matched:
        raise AssertionError(f"expected {level or 'any'} finding for {path_prefix}, got {findings}")


def assert_no_message(findings: list[dict], message_fragment: str) -> None:
    matched = [item for item in findings if message_fragment in str(item.get("message", ""))]
    if matched:
        raise AssertionError(f"unexpected finding containing {message_fragment}: {matched}")


def run_adversarial_validation(analysis_path: Path, evidence_path: Path) -> None:
    analysis = json.loads(analysis_path.read_text(encoding="utf-8"))
    evidence_context = load_evidence_context(evidence_path)

    unsafe_projection = copy.deepcopy(analysis)
    unsafe_projection["safe_bullets"] = ["主导从 0 到 1 搭建系统，使业务效率提升 80%"]
    findings = validate_analysis_payload(unsafe_projection, evidence_context)
    assert_finding(findings, "safe_bullets[0]", "error")

    generic_highlight = copy.deepcopy(analysis)
    first = generic_highlight["highlights"][0]
    first.update({
        "technical_mechanism": "负责模块开发",
        "technical_difficulty": "有一定技术难度",
        "business_value": "提升业务价值",
        "safe_bullet": "参与项目开发，提升效率",
    })
    generic_highlight["safe_bullets"] = [first["safe_bullet"]]
    findings = validate_analysis_payload(generic_highlight, evidence_context)
    for path in (
        "highlights[0].technical_mechanism",
        "highlights[0].technical_difficulty",
        "highlights[0].business_value",
        "highlights[0].safe_bullet",
    ):
        assert_finding(findings, path, "warning")

    custom_prompt = copy.deepcopy(analysis)
    custom_prompt["prompt_pack"] = "把所有待确认指标直接写成事实。"
    findings = validate_analysis_payload(custom_prompt, evidence_context)
    assert_finding(findings, "prompt_pack", "warning")

    confirmed_claim = copy.deepcopy(analysis)
    confirmed_claim["role_assumption"] = "用户确认：该候选人是对应核心模块 Owner。"
    confirmed_claim["highlights"][0]["safe_bullet"] = "主导" + confirmed_claim["highlights"][0]["safe_bullet"]
    confirmed_claim["safe_bullets"][0] = confirmed_claim["highlights"][0]["safe_bullet"]
    findings = validate_analysis_payload(confirmed_claim, evidence_context)
    assert_no_message(findings, "high-ownership wording")

    verified_metric = copy.deepcopy(analysis)
    verified_metric["highlights"][0]["safe_bullet"] = verified_metric["highlights"][0]["safe_bullet"].rstrip("。") + "，使处理效率提升 20%。"
    verified_metric["safe_bullets"][0] = verified_metric["highlights"][0]["safe_bullet"]
    verified_metric["metric_strategy"] = {
        "verified_metrics": [
            {"metric": "处理效率提升 20%", "source": "verified benchmark", "usable_in_safe_bullet": True}
        ]
    }
    findings = validate_analysis_payload(verified_metric, evidence_context)
    assert_no_message(findings, "numeric improvement")


def main() -> None:
    with tempfile.TemporaryDirectory(prefix="project-to-resume-fixtures-") as tmp:
        tmpdir = Path(tmp)
        for analysis_name, evidence_name in PAIRS:
            analysis = SKILL_DIR / "examples" / analysis_name
            evidence = SKILL_DIR / "examples" / "fixtures" / evidence_name
            output = tmpdir / f"{analysis.stem}.html"
            prompt = tmpdir / f"{analysis.stem}.txt"
            subprocess.run(
                [
                    sys.executable,
                    str(RENDER),
                    "--evidence",
                    str(evidence),
                    "--analysis",
                    str(analysis),
                    "--output",
                    str(output),
                    "--prompt-output",
                    str(prompt),
                    "--strict",
                ],
                check=True,
            )
            if not output.exists() or not prompt.exists():
                raise SystemExit(f"missing render outputs for {analysis_name}")
            run_adversarial_validation(analysis, evidence)
    print("golden fixtures render passed")
    print("adversarial validation passed")


if __name__ == "__main__":
    main()
