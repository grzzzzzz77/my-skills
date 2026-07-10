# Resume Scorecard V2 Rubric

## Contents

1. Measurement model
2. Shared score bands
3. Career-capital rubric
4. Communication-quality rubric
5. Presentation-quality rubric
6. JD-fit rubric
7. Evidence and confidence rules
8. Issue-ledger and no-double-count policy
9. Stage benchmarks
10. 90+ rules

## 1. Measurement Model

Score four independent axes. Only the first two form `core_score`.

| Axis | Meaning | Core weight |
|---|---|---:|
| `career_capital` | Resume-demonstrated value of experience, scope, ownership, impact, expertise, and trajectory | 70% |
| `communication_quality` | Quality of positioning, selection, evidence articulation, semantic clarity, and defensibility | 30% |
| `presentation_quality` | Visual hierarchy, density, typography, organization, and layout ATS safety | 0% |
| `jd_fit` | Match to a provided JD | 0% |

Calculate:

```text
core_score = round(career_capital × 0.70 + communication_quality × 0.30, 1)
```

Never infer the candidate's hidden ability. Name the first axis “简历已展示的履历含金量”, not a definitive score of the person.

## 2. Shared Score Bands

| Score | Band | Interpretation |
|---:|---|---|
| 90-100 | A+ | Exceptional evidence for the selected context; only minor gaps remain. |
| 80-89 | A | Strong and competitive; meaningful strengths outweigh limited gaps. |
| 70-79 | B | Credibly usable and competitive in some contexts; improvement is identifiable. |
| 60-69 | C | Partial evidence or uneven packaging; focused work is needed. |
| <60 | D | Insufficient demonstrated evidence for the selected context. Do not equate this with low personal ability. |

Use one-decimal scores when the weighted formula produces them. Report confidence separately.

## 3. Career-Capital Rubric

Use these exact dimensions and weights.

| ID | Dimension | Points | Measures |
|---|---|---:|---|
| `relevance_trajectory` | 方向相关性与成长轨迹 | 15 | Coherence, increasing responsibility, and relevance to the selected role family or own-target lane. |
| `complexity_scope` | 任务复杂度与影响范围 | 20 | Problem difficulty, constraints, system/business scope, stakeholders, scale, and ambiguity handled. |
| `ownership` | 责任边界与主导程度 | 20 | What the candidate personally decided, built, operated, influenced, or owned end to end. |
| `impact_value` | 结果价值与实际影响 | 20 | Business, user, technical, operational, research, risk, or organizational value. |
| `expertise_scarcity` | 专业深度与能力稀缺性 | 15 | Role-relevant depth, tradeoffs, specialist knowledge, and hard-to-replace capability. |
| `growth_validation` | 成长性与外部验证 | 10 | Promotions, expanding scope, adoption, awards, publications, certifications, trusted selection, or repeat responsibility. |

### Career-Capital Anchors

Apply each anchor proportionally to its max score:

- **90-100% of dimension max**: multiple strong, specific signals; clear personal boundary; complexity and value survive follow-up.
- **80-89%**: strong evidence with one limited gap in scope, result, or verification.
- **70-79%**: credible and relevant evidence, but depth, range, or personal boundary is uneven.
- **60-69%**: some relevant evidence, with material ambiguity or shallow scope.
- **Below 60%**: little demonstrated evidence for this dimension.

Do not lower career capital solely because the resume lacks precise metrics. Use scope, artifacts, decisions, adoption, quality, reliability, or risk reduction when appropriate.

## 4. Communication-Quality Rubric

Use these exact dimensions and weights.

| ID | Dimension | Points | Measures |
|---|---|---:|---|
| `positioning` | 目标定位与职业叙事 | 20 | Whether the target, stage, and strongest value are understandable without guessing. |
| `selection_prioritization` | 内容取舍与优先级 | 20 | Whether the strongest relevant evidence is selected and ordered ahead of noise. |
| `evidence_expression` | 证据表达完整度 | 25 | Whether claims include action, method, scope, result/artifact, and personal contribution where available. |
| `semantic_clarity` | 语义结构与扫读效率 | 20 | Headings, bullet logic, wording, information hierarchy in text, and textual ATS semantics. |
| `consistency_defensibility` | 一致性与面试可防守性 | 15 | Timeline, terminology, ownership wording, metric framing, and claim consistency. |

### Communication Boundaries

- Standard section names, keyword wording, and bullet clarity belong here.
- Fonts, spacing, columns, text boxes, margins, and visual reading order do not belong here.
- A strong career history written vaguely may receive high career capital with medium confidence and a lower communication score.
- Missing context is a communication gap unless it creates a genuine contradiction or implausible claim.

## 5. Presentation-Quality Rubric

Use these exact dimensions and weights when layout evidence exists.

| ID | Dimension | Points | Measures |
|---|---|---:|---|
| `visual_hierarchy` | 信息层级与首屏抓取 | 25 | Visual emphasis and first-screen comprehension. |
| `density_whitespace` | 版面密度与留白 | 20 | Margins, spacing, bullet density, line length, and page balance. |
| `typography_alignment` | 字体、字号、对齐与一致性 | 15 | Typography, dates, punctuation, alignment, and repeated patterns. |
| `visual_organization` | 模块组织与视觉引导 | 15 | Grouping, ordering, and visual flow. |
| `ats_layout` | 版式 ATS/机器解析友好度 | 15 | Columns, tables, text boxes, image-only text, copyability, and reading order. |
| `professional_fit` | 专业感与岗位气质 | 10 | Appropriate visual tone without harmful decoration. |

Presentation score caps by `layout_evidence`:

| Evidence | Cap | Max confidence |
|---|---:|---|
| `rendered_file` | 100 | high |
| `file_structure` | 90 | high |
| `extracted_text` | 82 | medium |
| `pasted_text` | 75 | medium |
| `ocr_only` | 65 | low |

If only pasted or extracted text is available, do not claim exact typography, margins, or visual polish.

## 6. JD-Fit Rubric

Create this axis only when an actual JD is provided.

| ID | Dimension | Points | Measures |
|---|---|---:|---|
| `must_haves` | 硬性条件覆盖 | 35 | Explicit must-have qualifications and disqualifying gaps. |
| `responsibility_match` | 核心职责匹配 | 25 | Evidence aligned with the JD's actual work. |
| `seniority_scope` | 年限、级别与责任范围 | 15 | Seniority, ownership, and scale expected by the role. |
| `domain_tools` | 领域、方法与工具匹配 | 15 | Domain knowledge, methods, platforms, or tools. |
| `targeted_evidence` | 关键证据呈现 | 10 | Whether relevant proof is visible and credible in the resume. |

An unrelated or missing JD must never reduce career capital, communication quality, or presentation quality.

## 7. Evidence And Confidence Rules

### Accepted Evidence Types

Treat these as legitimate proof when role-appropriate:

- quantified result or before/after comparison
- scale, users, transactions, budget, team, geography, stakeholders, or operational reach
- shipped artifact, system, product, publication, policy, campaign, design, process, or certification
- decision, tradeoff, diagnosis, experiment, architecture, or strategy
- adoption, reuse, customer acceptance, stakeholder approval, citation, award, or promotion
- quality, reliability, compliance, safety, cost, time, or risk improvement
- credible qualitative result when disclosure restrictions prevent exact numbers

No single evidence type is mandatory across all roles.

### Confidence

- `high`: complete text, adequate context, and strong evidence for the scored axis.
- `medium`: complete resume but some target, scope, ownership, or verification context is missing.
- `low`: partial text, OCR uncertainty, unclear target/stage, or many assumptions.

### Evidence Coverage

Report a separate 0-100 `evidence_coverage.score`:

- 85-100: most major claims have enough context to score confidently.
- 70-84: several strong signals, but material claims need context.
- 50-69: scoring is possible but sensitive to missing information.
- Below 50: avoid strong conclusions; emphasize what cannot be determined.

Do not subtract evidence coverage from any score. It qualifies the reliability of the diagnosis.

## 8. Issue-Ledger And No-Double-Count Policy

Represent each material issue once in `issue_ledger`.

Required fields:

- unique `issue_id`
- `kind`: `gap`, `risk`, `contradiction`, or `layout`
- `severity`: `high`, `medium`, or `low`
- `primary_axis`: one score axis or `none`
- `primary_dimension`: a valid dimension ID for the primary axis, or empty when `none`
- `points`: zero or negative; use `0` for informational gaps
- evidence and explanation
- optional `cross_references`

Rules:

1. One issue may affect only one primary dimension.
2. Cross-references are narrative only and cannot deduct again.
3. Missing evidence should usually have `points: 0` and reduce coverage/confidence.
4. Use negative points only when the dimension score explicitly reflects a real weakness or risk.
5. Layout issues may affect only `presentation_quality`.
6. JD gaps may affect only `jd_fit`.
7. A metric without context is normally a communication issue; treat it as credibility risk only when implausible, contradictory, or inflated.

## 9. Stage Benchmarks

Generate `stage_benchmark` only when requested and stage evidence is adequate. Base it on `career_capital`, never `core_score` or presentation.

Use the label `internal_expectation`, not market average or percentile. The reference lines are calibration anchors, not observed hiring-market statistics.

| Stage | Reference line | Strong line | Exceptional line |
|---|---:|---:|---:|
| `intern_entry` | 60 | 75 | 88 |
| `early_career` | 68 | 80 | 90 |
| `experienced_ic` | 74 | 84 | 92 |
| `senior_ic` | 80 | 88 | 94 |
| `manager_lead` | 82 | 90 | 95 |

Interpret these through the selected role-family profile. Do not claim that a score is above a real population average without external cohort data.

## 10. 90+ Rules

Do not use a universal 89 cap. Award 90+ on an axis when evidence matches the exceptional anchors for that axis.

Career capital may exceed 90 without numeric metrics when there is strong alternative proof of complexity, ownership, and value. Communication may exceed 90 with minor missing context if the narrative is otherwise precise and defensible. Presentation may exceed 90 only with rendered evidence.

Use a hard cap only on the directly affected axis:

- unresolved timeline contradiction
- clearly implausible or inflated ownership
- critical content missing so the axis cannot be evaluated
- a JD hard requirement demonstrably not met, applied only to `jd_fit`

When confidence is low, report the score with low confidence instead of inventing certainty or automatically forcing a low score.
