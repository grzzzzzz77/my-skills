# Resume Scorecard V2 Analysis Schema

## Contents

1. Required top-level shape
2. Resume score vector
3. Axis and dimension objects
4. Evidence coverage
5. Issue ledger
6. Optional diagnostics
7. Comparison
8. Validation and rendering

Use `examples/complete-analysis-sample.json` as the complete strict-valid example.

## 1. Required Top-Level Shape

```json
{
  "schema_version": "2.0",
  "report_title": "简历多轴评分卡报告",
  "score_mode": "standalone",
  "jd_provided": false,
  "candidate_label": "候选人",
  "target_role": "前端开发",
  "overall_summary": "履历含金量强，内容表达仍有提升空间。",
  "confidence": "medium",
  "generated_at": "2026-07-10 12:00",
  "resumes": [],
  "missing_information": []
}
```

Rules:

- `schema_version` must be `2.0`.
- `score_mode`: `standalone`, `jd_fit`, `comparison`, or `cross_industry_comparison`.
- `jd_provided` must be boolean. Use `true` only with an actual JD.
- `confidence`: `high`, `medium`, or `low`.
- `resumes` must contain at least one item.
- Comparison modes require at least two resumes and a `comparison` object.

## 2. Resume Score Vector

```json
{
  "id": "A",
  "name": "当前简历",
  "source": "resume.pdf",
  "target_role": "前端开发",
  "target_industry": "互联网 / 软件",
  "role_family": "engineering_data",
  "candidate_stage": "early_career",
  "scoring_context": "无 JD，按前端岗位与 early_career 锚点评分",
  "core_score": 84.1,
  "band": "A",
  "score_summary": "履历价值较强，主要改进空间在证据表达。",
  "score_axes": {
    "career_capital": {},
    "communication_quality": {},
    "presentation_quality": {}
  },
  "evidence_coverage": {},
  "issue_ledger": [],
  "strengths": [],
  "ats_notes": [],
  "interview_risks": [],
  "score_lifts": []
}
```

Rules:

- `role_family`: `engineering_data`, `product_design`, `sales_growth_ops`, `corporate_functions`, `research_professional`, `leadership_management`, or `general`.
- `candidate_stage`: `intern_entry`, `early_career`, `experienced_ic`, `senior_ic`, `manager_lead`, or `career_changer`.
- `core_score = career_capital × 0.70 + communication_quality × 0.30`, rounded to one decimal.
- `band` must exactly match `core_score`.
- `presentation_quality` is optional but recommended when structural/layout evidence exists.
- `jd_fit` is required when `jd_provided` is true and forbidden when false.

## 3. Axis And Dimension Objects

```json
{
  "score": 86,
  "band": "A",
  "confidence": "medium",
  "summary": "复杂度和 ownership 较强，业务口径仍需补充。",
  "dimensions": [
    {
      "id": "complexity_scope",
      "name": "任务复杂度与影响范围",
      "score": 18,
      "max_score": 20,
      "confidence": "high",
      "rationale": "经历体现多端交付和生产约束。",
      "evidence": ["负责 Web、小程序和跨端一致性方案"],
      "gaps": ["缺少用户规模或运行范围"],
      "lift_actions": ["补充系统覆盖范围或关键约束"]
    }
  ]
}
```

Axis rules:

- Include every required dimension exactly once with the exact ID and max score from `scoring-rubric.md`.
- Axis score must equal the sum of dimension scores.
- Axis band must match its score.
- Evidence is positive support; `gaps` is optional. Do not invent a gap merely to fill the field.
- Every dimension with a positive score requires evidence.

Additional presentation fields:

```json
{
  "layout_evidence": "rendered_file",
  "strengths": [],
  "issues": [],
  "lift_actions": [],
  "ats_layout_notes": []
}
```

`layout_evidence`: `rendered_file`, `file_structure`, `extracted_text`, `pasted_text`, or `ocr_only`.

Additional JD fields:

```json
{
  "must_have_coverage": "4/5",
  "matched_keywords": [],
  "missing_keywords": [],
  "notes": []
}
```

## 4. Evidence Coverage

```json
{
  "score": 78,
  "status": "medium",
  "summary": "主要经历完整，但关键指标口径和个人边界仍有缺口。",
  "missing_evidence": ["核心项目规模", "性能指标测量方法"]
}
```

Rules:

- Score from 0 to 100.
- `status`: `high` for 85+, `medium` for 60-84, `low` below 60.
- Evidence coverage does not reduce another score automatically.

## 5. Issue Ledger

```json
{
  "issue_id": "metric-context-01",
  "title": "性能指标缺少测量口径",
  "kind": "gap",
  "severity": "medium",
  "primary_axis": "communication_quality",
  "primary_dimension": "evidence_expression",
  "points": -2,
  "detail": "40% 提升没有基线、环境或测量方法。",
  "evidence": ["项目 bullet：性能提升 40%"],
  "cross_references": ["interview_risk"]
}
```

Rules:

- `issue_id` must be unique within a resume.
- `kind`: `gap`, `risk`, `contradiction`, or `layout`.
- `points` must be zero or negative.
- `primary_axis`: `career_capital`, `communication_quality`, `presentation_quality`, `jd_fit`, or `none`.
- `primary_dimension` must belong to the primary axis.
- `primary_axis: none` requires empty `primary_dimension` and `points: 0`.
- Layout issues may only target `presentation_quality`; JD gaps may only target `jd_fit`.
- Mention the same issue elsewhere by its ID; do not create a second ledger entry.

## 6. Optional Diagnostics

### Stage Benchmark

Use only when requested:

```json
{
  "benchmark_type": "internal_expectation",
  "basis_axis": "career_capital",
  "estimated_years": 2,
  "current_stage": "early_career",
  "next_stage": "experienced_ic",
  "note": "内部阶段期望锚点，不是市场平均值或百分位。",
  "stages": [
    {
      "stage": "early_career",
      "reference_score": 68,
      "strong_score": 80,
      "exceptional_score": 90,
      "candidate_delta": 18,
      "expectations": ["独立模块交付", "清晰个人边界"]
    }
  ],
  "interpretation": "已达到 early_career 强水平。"
}
```

`candidate_delta` is career-capital score minus `reference_score`.

### Score Lifts

```json
{
  "axis": "communication_quality",
  "action": "补充两个核心成果的范围和测量口径",
  "estimated_gain": "+3-5",
  "effort": "medium",
  "why": "提高证据表达和面试可防守性"
}
```

Estimated gain must be a range and cannot imply guaranteed improvement.

## 7. Comparison

```json
{
  "context_type": "same_target",
  "winner": "A",
  "reason": "A 的内容表达更清晰；两版履历含金量基本相同。",
  "delta_summary": [],
  "normalized_axes": [
    {
      "axis": "communication_quality",
      "winner": "A",
      "scores": {"A": 86, "B": 78},
      "confidence": "high",
      "reason": "A 的证据更集中。"
    }
  ],
  "best_for": []
}
```

For cross-industry comparison, include normalized axes and scenario-specific `best_for` entries.

## 8. Validate And Render

```bash
python3 <skill_dir>/scripts/validate_scorecard.py \
  --analysis /path/to/resume_scorecard_analysis.json \
  --strict

python3 <skill_dir>/scripts/render_scorecard_report.py \
  --analysis /path/to/resume_scorecard_analysis.json \
  --output /path/to/resume-scorecard-report.html \
  --auto-redact \
  --strict
```

Strict mode treats warnings as publication blockers. Use `--redacted-output` or `--auto-redact` before publication when sensitive information is detected.
