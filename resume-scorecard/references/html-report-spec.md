# HTML Report Spec V2

Render a standalone Chinese HTML file from strict-valid v2 analysis JSON.

## Required Sections

1. Hero: report title, target, mode, confidence, time, and diagnostic disclaimer.
2. Score vector: core score plus separate career-capital, communication, presentation, and optional JD-fit scores.
3. Executive summary: strongest evidence, main gaps, evidence coverage, and missing information.
4. Axis breakdown: exact dimension scores, positive evidence, rationale, optional gaps, and lift actions.
5. Issue ledger: unique issue ID, primary axis/dimension, points, evidence, and cross-references.
6. Presentation diagnosis: evidence level, confidence, layout strengths/issues, and ATS-layout notes when available.
7. JD-fit diagnosis: must-have coverage and matched/missing terms only when a JD exists.
8. Stage benchmark: show only when present and label it an internal expectation anchor, not a market average.
9. Comparison: show axis deltas, numeric normalized axes, and scenario winners when multiple resumes exist.
10. Risks, ATS notes, and score-lift levers.
11. Methodology: formula, score separation, evidence coverage, no-double-count rule, and limitations.

## UX Requirements

- Make the score vector more prominent than any one isolated number.
- Label presentation and JD fit as independent scores that do not enter core score.
- Show confidence and evidence coverage beside scores rather than burying them at the end.
- Use cards for score summaries and horizontally scrollable tables for dense comparisons.
- Keep responsive layout and avoid external dependencies.
- Use restrained colors and never communicate low evidence as personal worth.
- Escape all report content and auto-redact sensitive contact details before publication.

## Copy Rules

- Say “简历已展示的履历含金量”, not “候选人能力分”.
- Say “内部阶段期望锚点”, not “市场平均分”, unless an external dataset is provided.
- Explain that missing evidence affects confidence/coverage before treating it as a weakness.
- Estimated gains must be ranges and must not promise outcomes.
- Do not rewrite the resume by default.
