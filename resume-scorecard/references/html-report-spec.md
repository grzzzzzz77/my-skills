# HTML Report Spec

The report is a standalone Chinese HTML file rendered from `resume_scorecard_analysis.json`.

## Required Sections

1. Hero
   - Report title
   - Target role
   - Score mode
   - Confidence level
   - Generated time

2. Executive Summary
   - Overall conclusion
   - Missing information and confidence caveats

3. Score Overview
   - One card per resume version
   - Total score, band, short summary
   - JD-fit score when available

4. Experience-Year Benchmark
   - Show when a resume includes `experience_benchmark`
   - Estimate or display the candidate's years of experience
   - Compare the candidate score against the current experience band average
   - Also compare against the next higher band average
   - Clearly state in a visible callout and in methodology that built-in averages are rubric-calibrated reference baselines, not live market statistics

5. Presentation / Layout Score
   - Show when a resume includes `presentation_review`
   - Display a separate 0-100 presentation score, band, confidence, and short summary
   - Display `layout_evidence` when available so readers understand whether the score came from rendered layout, extracted text, pasted text, or OCR
   - Include criteria breakdown for information hierarchy, density/white space, typography/alignment consistency, module organization, ATS parsing friendliness, and professional tone
   - List visual strengths, visible layout issues, concrete layout lift actions, and ATS layout notes
   - Make clear that this is separate from the main resume competitiveness score

6. Version Comparison
   - Show only when there are multiple resume versions or `comparison` exists
   - Winner, reason, score deltas, best-use scenario
   - For cross-industry comparisons, show `comparison.normalized_axes` as a table when available

7. Dimension Breakdown
   - For each resume version:
     - Dimension score and max score
     - Progress bar
     - Rationale
     - Evidence
     - Deductions
     - Lift actions

8. Risk And ATS Notes
   - Red flags grouped by severity
   - ATS/readability notes
   - Interview risks

9. Score Lift Levers
   - Action
   - Estimated score gain
   - Effort
   - Why it matters

10. Methodology
   - Explain that the score is diagnostic, not hiring probability
   - Mention the six default score dimensions
   - Mention that experience-year averages are internal benchmark references unless an external dataset is provided
   - Mention that presentation/layout score, when present, is an independent 100-point visual/readability diagnostic and is not added to the main total score

## UX Requirements

- Clean professional style.
- Responsive layout.
- No external dependencies.
- Text must not overflow on mobile.
- Use tables for dense comparisons and cards for score summaries.
- Wrap dense tables in a horizontal scroll container on mobile; table overflow must not widen the whole page.
- Use color sparingly:
  - Green for strong scores.
  - Amber for medium.
  - Red for high-risk deductions.
  - Neutral gray for methodology.
- Do not include private phone numbers, email addresses, or sensitive contact details. Use renderer `--auto-redact` or validator `--redacted-output` before final HTML publication when warnings appear.

## Copy Rules

- The report may include "提分杠杆" but should not rewrite the full resume by default.
- If recommending a score lift, phrase it as diagnostic advice, not guaranteed improvement.
- Estimated score gains must be ranges and labeled as estimates.
