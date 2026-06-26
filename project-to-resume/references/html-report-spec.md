# HTML Report Spec

The final report is a standalone Chinese HTML file.

Generate it with `scripts/render_resume_report.py` from:

- `project_evidence.json`
- `project_resume_analysis.json`
- `assets/report-template.html`

Do not manually replace template placeholders for final delivery.

For final delivery, render with `--strict` so invalid `project_resume_analysis.json` fails before producing a polished-looking but low-quality report.

## Required Sections

1. Hero
   - Project name
   - Target role
   - Analysis time
   - Repo path
   - Overall readiness

2. Evidence Summary
   - Tech stack
   - File/module counts
   - Git author stats when available
   - Key directories
   - Tests/config/docs signals

3. Highlight Explorer
   - Filter by category
   - Filter by risk label
   - Filter by resume readiness
   - Search keyword

4. Project Fact Pack
   - One-line project summary.
   - Role/disclosure assumptions.
   - Tech stack and keywords.
   - Verified and code-derived metrics with sources.

5. Resume-Ready Bullets
   - A copy-friendly list of safe bullets.

6. Enhanced Bullets Requiring Confirmation
   - Include suggested metrics and what the user must verify.

7. Downstream Resume Prompt
   - Copy-friendly prompt for another agent to merge the project into the user's original resume.
   - Keep safe bullets, enhanced bullets, risky claims, and unknowns clearly separated.

8. Interview Story Bank
   - STAR notes for the best highlights.

9. Evidence Appendix
   - File paths and counts.
   - Mention that secrets and sensitive content were not included.

## Card Fields

Each highlight card must include:

- Title
- Category
- Readiness score
- Risk label
- Evidence paths or counts
- Safe resume bullet
- Enhanced bullet
- Why it is valuable
- Interview notes
- Data to confirm
- Downstream usage suggestion: direct paste, rewrite candidate, or confirmation needed

## Visual Requirements

- Chinese content.
- Clean professional style, not a marketing landing page.
- Responsive layout.
- No external JavaScript dependency.
- Cards with 8px border radius or less unless consistent with the design.
- Custom filter controls for category/risk/readiness, not browser-default select styling when practical.
- Copy controls for safe bullets and the downstream prompt when practical.
- Text must not overflow on mobile.
