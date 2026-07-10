---
name: resume-scorecard
description: Evaluate and compare resumes with a calibrated multi-axis scorecard that separates demonstrated career capital, content communication quality, presentation/layout quality, and optional JD fit. Use for 简历打分, 无 JD 评分, 履历含金量, 内容表达分, 排版评分, ATS/可读性, JD 匹配, A/B 或跨行业简历对比, 年限/阶段对标, 90+ 差距分析, 敏感信息脱敏, or a defensible Chinese HTML diagnostic report without rewriting the resume by default.
---

# Resume Scorecard

Evaluate resumes; do not rewrite them unless the user explicitly asks after the diagnosis.

## Measurement Contract

Keep four scores separate:

1. `career_capital`: demonstrated value of the candidate's experience, scope, ownership, impact, expertise, and trajectory.
2. `communication_quality`: how well the resume selects, positions, explains, and defends that experience in text.
3. `presentation_quality`: visual hierarchy, density, typography, page organization, and layout-related ATS safety. Never add this score to the core score.
4. `jd_fit`: must-have and responsibility fit for a provided JD. Omit it when no JD is provided.

Derive the no-JD or general core score only as:

```text
core_score = career_capital × 0.70 + communication_quality × 0.30
```

Round to one decimal when needed. Do not mix layout or JD fit into `core_score`. Call all scores diagnostic evidence scores, never hiring probability or a score of the whole person.

## Non-Negotiable Fairness Rules

- Score from positive evidence and anchored levels; do not start at 100 and hunt for deductions.
- Treat absent evidence as an evidence-coverage or confidence gap, not proof of weakness, dishonesty, or low career value.
- Accept multiple proof types: metrics, scope, artifacts, decisions, adoption, reliability, risk reduction, external validation, and credible qualitative outcomes. Never require numbers for every role.
- Put each issue in `issue_ledger` once. Only its `primary_axis` and `primary_dimension` may reflect a score effect; cross-references cannot deduct again.
- Keep content ATS signals (standard headings, keyword wording) in communication quality and visual parsing hazards (columns, text boxes, reading order) in presentation quality.
- Apply role-family and career-stage anchors. Do not judge interns with senior ownership standards or reward employer prestige without demonstrated scope.
- Use confidence and evidence coverage to express uncertainty. Reserve credibility penalties for contradictions, implausible ownership, unsupported inflation, or clear timeline conflicts.
- Do not use fixed experience averages as live market statistics. If the user asks for stage comparison, label it an internal expectation anchor based on `career_capital` only.

Read `references/scoring-rubric.md` before scoring. Also read `references/role-calibration.md` when a target role, role family, or candidate stage is known.

## Inputs

Use available inputs and ask only for missing essentials:

- `resume`: text or local PDF/DOCX/Markdown path; accept two or more versions for comparison.
- `target_role` and optional `target_industry`.
- `jd`: optional; set `jd_provided` accordingly.
- `candidate_stage` and optional `candidate_experience_years`; infer conservatively when possible.
- `per_resume_target`: use when cross-industry resumes target different lanes.
- `output_dir`: optional destination for report artifacts.

If parsing or layout evidence is incomplete, follow `references/input-parsing.md`. Do not infer hidden achievements, private data, or unsupported metrics.

## Modes

- **Quick score**: Return the score vector, evidence coverage, strongest evidence, largest score gaps, and 3-5 lift levers in chat. Do not create files unless asked.
- **Standalone**: No JD. Score career capital, communication quality, and presentation when supported.
- **JD fit**: Score the three resume axes plus an independent JD-fit axis.
- **Comparison**: Score every version independently under the same context, then compare deltas and best-use scenarios.
- **Cross-industry comparison**: Score each resume against its own target and stage; compare normalized axes and scenarios, not raw JD keywords.
- **Report**: Create v2 analysis JSON, validate strictly, then render a Chinese HTML report.

## Workflow

### 1. Parse And Normalize

Preserve contact/header, education, skills, work/internships, projects, awards/certifications, publications, and portfolios. Infer stage from dates and role labels without treating internships as full-time seniority.

Redact phone numbers, email addresses, exact street addresses, ID numbers, credentials, and private/tokenized links from report artifacts.

### 2. Select Context

Choose one `role_family` from `references/role-calibration.md`, or use `general` when evidence is insufficient. Choose the closest career-stage overlay. State the scoring context for every resume.

Use `score_mode` values:

- `standalone`
- `jd_fit`
- `comparison`
- `cross_industry_comparison`

Set top-level `jd_provided` to `true` only when an actual JD is present.

### 3. Score Positive Evidence

Score every dimension against the anchors in `references/scoring-rubric.md` and the selected role profile. Each dimension must include:

- `id`, name, score, and max score
- confidence
- positive evidence
- rationale
- optional gaps and lift actions

Do not force a gap when there is no material gap. Calculate `career_capital`, `communication_quality`, and `core_score` before considering layout or JD fit.

### 4. Build Evidence Coverage And Issue Ledger

Report `evidence_coverage` separately. Add one ledger entry per material issue with a stable unique `issue_id`, issue kind, evidence, primary axis/dimension, optional non-positive score effect, and cross-references.

An issue with `primary_axis: none` must have `points: 0`. Do not repeat the same issue under multiple IDs merely to lower several axes.

### 5. Add Optional Diagnostics

- Add `presentation_quality` only when structural or visual signals exist; obey layout-evidence caps.
- Add `jd_fit` only when `jd_provided` is true.
- Add `stage_benchmark` only when requested and stage evidence is adequate. Label it an internal expectation anchor, not an average or percentile.
- Add comparison, ATS notes, interview risks, and lift levers without rewriting the resume.

### 6. Validate And Render

Read `references/analysis-schema.md`, write `resume_scorecard_analysis.json`, then run:

```bash
python3 <skill_dir>/scripts/validate_scorecard.py \
  --analysis /path/to/resume_scorecard_analysis.json \
  --strict
```

If private data is reported, produce a redacted copy:

```bash
python3 <skill_dir>/scripts/validate_scorecard.py \
  --analysis /path/to/resume_scorecard_analysis.json \
  --redacted-output /path/to/resume_scorecard_analysis.redacted.json \
  --strict
```

Render only strict-valid data:

```bash
python3 <skill_dir>/scripts/render_scorecard_report.py \
  --analysis /path/to/resume_scorecard_analysis.json \
  --output /path/to/resume-scorecard-report.html \
  --auto-redact \
  --strict
```

## Output Order

Lead with:

1. `core_score` and band
2. career-capital score
3. communication-quality score
4. independent presentation score and evidence level, when available
5. independent JD-fit score, when available
6. evidence coverage and confidence
7. strongest evidence, primary issues, and lift levers

For comparisons, name the scoring context and best-use scenario. Do not declare one resume universally superior across unrelated targets.

## References

- Scoring anchors and no-double-count policy: `references/scoring-rubric.md`
- Role-family and stage calibration: `references/role-calibration.md`
- Analysis JSON contract: `references/analysis-schema.md`
- Parsing and layout confidence: `references/input-parsing.md`
- Comparison rules: `references/comparison-rules.md`
- HTML report requirements: `references/html-report-spec.md`
- Strict-valid sample: `examples/complete-analysis-sample.json`
- Calibration cases: `examples/calibration-cases.json`
- Validator: `scripts/validate_scorecard.py`
- Renderer: `scripts/render_scorecard_report.py`
- Regression tests: `tests/test_scorecard.py`
