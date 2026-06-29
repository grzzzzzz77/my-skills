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
   - Clearly state that built-in averages are rubric-calibrated reference baselines, not live market statistics

5. Version Comparison
   - Show only when there are multiple resume versions or `comparison` exists
   - Winner, reason, score deltas, best-use scenario

6. Dimension Breakdown
   - For each resume version:
     - Dimension score and max score
     - Progress bar
     - Rationale
     - Evidence
     - Deductions
     - Lift actions

7. Risk And ATS Notes
   - Red flags grouped by severity
   - ATS/readability notes
   - Interview risks

8. Score Lift Levers
   - Action
   - Estimated score gain
   - Effort
   - Why it matters

9. Methodology
   - Explain that the score is diagnostic, not hiring probability
   - Mention the six default score dimensions
   - Mention that experience-year averages are internal benchmark references unless an external dataset is provided

## UX Requirements

- Clean professional style.
- Responsive layout.
- No external dependencies.
- Text must not overflow on mobile.
- Use tables for dense comparisons and cards for score summaries.
- Use color sparingly:
  - Green for strong scores.
  - Amber for medium.
  - Red for high-risk deductions.
  - Neutral gray for methodology.
- Do not include private phone numbers, email addresses, or sensitive contact details.

## Copy Rules

- The report may include "提分杠杆" but should not rewrite the full resume by default.
- If recommending a score lift, phrase it as diagnostic advice, not guaranteed improvement.
- Estimated score gains must be ranges and labeled as estimates.
