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
   - Show all highlight cards by default.
   - Show technical-first highlight titles, category, risk label, resume readiness, visible count, safe bullet, enhanced bullet, evidence paths, and STAR notes.
   - Use expandable details for dense evidence/interview content.

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

## Information Architecture Requirements

- The left sidebar has one job: **reading navigation**.
- Sidebar links must jump to major report sections and update active-section highlighting while scrolling.
- Do not add a separate highlight filter block unless the user explicitly asks for filtering.
- Major sections must have stable anchors: overview, safe bullets, confirmation items, highlight explorer, downstream prompt, interview stories, and evidence appendix.
- Keep the report scannable: show the safest resume material early, keep dense evidence and STAR notes behind expandable detail areas when practical.
- The highlight explorer must show the total highlight count.
- Highlight titles should expose professional technical essence first, preferably in Chinese, such as `异步请求竞态治理`, `流式 Markdown 渲染`, `请求网关`, or `前端可观测性链路`.
- Keep English in titles only for established technical names, protocols, frameworks, abbreviations, or code identifiers such as `WebSocket`, `SSE`, `SDK`, `CLI`, `MCP`, `API`, `Markdown`, `SQLite FTS`, `Tauri`, `Rust`, `rAF`, or `stream-json`; avoid bilingual title stacking for style.

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
- Copy controls for safe bullets and the downstream prompt when practical.
- Left sidebar reading nav and right-side content must be interactive and aligned through anchors/active states.
- Dense card details should be progressively disclosed with expandable evidence/interview sections instead of forcing everything into one visual block.
- Text must not overflow on mobile.
