#!/usr/bin/env python3
"""Regression tests for resume-scorecard v2 invariants."""

from __future__ import annotations

import copy
import json
import sys
import unittest
from pathlib import Path


SKILL_DIR = Path(__file__).resolve().parents[1]
SCRIPTS_DIR = SKILL_DIR / "scripts"
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

from render_scorecard_report import render_report
from validate_scorecard import AXIS_DIMENSIONS, redact_payload, validate_analysis_payload


def load_sample() -> dict:
    return json.loads((SKILL_DIR / "examples" / "complete-analysis-sample.json").read_text(encoding="utf-8"))


def messages(payload: dict) -> list[str]:
    return [f"{item['path']}: {item['message']}" for item in validate_analysis_payload(payload)]


def perfect_axis(axis_name: str) -> dict:
    dimensions = []
    for dim_id, max_score in AXIS_DIMENSIONS[axis_name].items():
        dimensions.append(
            {
                "id": dim_id,
                "name": dim_id,
                "score": max_score,
                "max_score": max_score,
                "confidence": "high",
                "rationale": "Evidence matches the exceptional anchor.",
                "evidence": ["Verified role-relevant evidence"],
                "gaps": [],
                "lift_actions": [],
            }
        )
    axis = {
        "score": 100,
        "band": "A+",
        "confidence": "high",
        "summary": "Exceptional evidence.",
        "dimensions": dimensions,
    }
    if axis_name == "jd_fit":
        axis.update({"must_have_coverage": "5/5", "matched_keywords": ["required"], "missing_keywords": [], "notes": []})
    return axis


class ScorecardV2Tests(unittest.TestCase):
    def test_complete_sample_is_strict_valid(self) -> None:
        self.assertEqual(messages(load_sample()), [])

    def test_core_score_formula_is_enforced(self) -> None:
        payload = load_sample()
        payload["resumes"][0]["core_score"] = 90
        self.assertTrue(any("70% career + 30% communication" in message for message in messages(payload)))

    def test_exact_axis_dimensions_and_weights_are_enforced(self) -> None:
        payload = load_sample()
        dimension = payload["resumes"][0]["score_axes"]["career_capital"]["dimensions"][0]
        dimension["max_score"] = 16
        self.assertTrue(any("max_score must be 15" in message for message in messages(payload)))

    def test_duplicate_issue_ids_are_rejected(self) -> None:
        payload = load_sample()
        duplicate = copy.deepcopy(payload["resumes"][0]["issue_ledger"][0])
        payload["resumes"][0]["issue_ledger"].append(duplicate)
        self.assertTrue(any("duplicate issue_id" in message for message in messages(payload)))

    def test_layout_issue_cannot_reduce_career_capital(self) -> None:
        payload = load_sample()
        issue = payload["resumes"][0]["issue_ledger"][2]
        issue["primary_axis"] = "career_capital"
        issue["primary_dimension"] = "impact_value"
        self.assertTrue(any("layout issues may only target presentation_quality" in message for message in messages(payload)))

    def test_presentation_evidence_cap_is_enforced(self) -> None:
        payload = load_sample()
        axis = payload["resumes"][0]["score_axes"]["presentation_quality"]
        axis["score"] = 90
        axis["band"] = "A+"
        self.assertTrue(any("presentation score exceeds cap 82" in message for message in messages(payload)))

    def test_jd_axis_is_isolated_from_standalone_mode(self) -> None:
        payload = load_sample()
        payload["resumes"][0]["score_axes"]["jd_fit"] = perfect_axis("jd_fit")
        self.assertTrue(any("jd_fit must be omitted" in message for message in messages(payload)))

    def test_valid_jd_mode_requires_and_accepts_independent_jd_axis(self) -> None:
        payload = load_sample()
        payload["score_mode"] = "jd_fit"
        payload["jd_provided"] = True
        payload["resumes"][0]["score_axes"]["jd_fit"] = perfect_axis("jd_fit")
        self.assertEqual(messages(payload), [])

    def test_redaction_does_not_change_scores(self) -> None:
        payload = load_sample()
        original_scores = copy.deepcopy(payload["resumes"][0]["score_axes"])
        payload["overall_summary"] += " Contact: user@example.com"
        redacted = redact_payload(payload)
        self.assertEqual(redacted["resumes"][0]["score_axes"], original_scores)
        self.assertEqual(messages(redacted), [])

    def test_calibration_suite_has_24_cross_family_cases(self) -> None:
        data = json.loads((SKILL_DIR / "examples" / "calibration-cases.json").read_text(encoding="utf-8"))
        cases = data["cases"]
        self.assertEqual(len(cases), 24)
        expected_families = {
            "engineering_data",
            "product_design",
            "sales_growth_ops",
            "corporate_functions",
            "research_professional",
            "leadership_management",
        }
        self.assertEqual({item["role_family"] for item in cases}, expected_families)
        for item in cases:
            self.assertTrue(item["invariant"])
            for score_range in item["expected"].values():
                self.assertEqual(len(score_range), 2)
                self.assertLessEqual(score_range[0], score_range[1])
                self.assertGreaterEqual(score_range[0], 0)
                self.assertLessEqual(score_range[1], 100)

    def test_renderer_exposes_score_separation_and_issue_ledger(self) -> None:
        template = (SKILL_DIR / "assets" / "report-template.html").read_text(encoding="utf-8")
        output = render_report(load_sample(), template)
        for expected in ("履历含金量", "内容表达质量", "排版布局质量", "唯一问题台账", "不参与核心分"):
            self.assertIn(expected, output)
        self.assertNotRegex(output, r"\{\{[A-Z0-9_]+\}\}")


if __name__ == "__main__":
    unittest.main()
