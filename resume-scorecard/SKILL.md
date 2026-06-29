---
name: resume-scorecard
description: Score and compare resumes with a structured 100-point scorecard, standalone no-JD resume scoring, cross-industry resume comparison, JD-fit analysis, ATS/readability checks, credibility risks, and a Chinese HTML report. Use when the user asks for 简历打分, 单独评分, 无 JD 评分, 简历评分, 简历对比, 跨行业简历对比, A/B 简历比较, ATS 分数, JD 匹配分, 简历质量评估, 为什么这版简历更强, or wants an objective score report instead of resume rewriting or optimization.
---

# Resume Scorecard

Use this skill to evaluate resumes, not to rewrite them by default. The output is a scorecard: scores, evidence, deductions, comparison, risks, and lift levers. Only rewrite resume bullets when the user explicitly asks after the score report.

## Core Promise

Produce a defensible score that separates:

- **Resume quality**: whether the resume itself is clear, credible, scannable, and evidence-rich.
- **Standalone competitiveness**: how strong the resume is when no JD is provided, using general role-market expectations or universal resume quality.
- **JD fit**: whether this resume matches a specific job description or role.
- **Version or cross-industry advantage**: which resume is stronger for a target, or which is stronger within its own target market when targets differ.
- **Interview risk**: which claims may collapse under follow-up.

Never treat the score as hiring probability. Say it is a diagnostic score for resume competitiveness and evidence quality.

## Inputs

Ask only for missing essentials:

- `resume`: text or a local file path. For comparison, accept two or more versions.
- `target_role`: optional target role, such as 前端开发、后端开发、产品经理、测试、数据分析. If omitted, run standalone no-JD scoring.
- `per_resume_target`: optional target role/industry for each resume when comparing cross-industry resumes.
- `jd`: optional job description. When present, run JD-fit mode.
- `candidate_stage`: 校招、实习、社招、转岗、专科/高职、本科、硕士/博士, if relevant.
- `output_dir`: where to save the HTML report. If omitted, save next to the resume file or in the current working directory.

If a PDF/DOCX cannot be reliably parsed, ask for pasted text or a text/Markdown export. Do not score screenshots unless text is available.

## Execution Modes

- **Quick score**: Use when the user asks for a simple score in chat. Output total score, dimension table, top deductions, and 3-5 lift levers. Do not create files unless requested.
- **Standalone no-JD mode**: Use when the user provides one resume without JD or target role. Score universal resume quality: clarity, evidence, depth, structure, credibility, and market-readiness. Do not ask for a JD unless the user specifically wants JD fit.
- **Report mode**: Use when the user asks for HTML, deliverable, detailed report, or comparison. Create `resume_scorecard_analysis.json`, validate it, then render HTML.
- **Comparison mode**: Use when the user gives multiple resumes or asks A/B, old/new, or "哪版更好". Score each version with the same rubric and include deltas.
- **Cross-industry comparison mode**: Use when resumes target different roles or industries. Score each resume against its own intended target or a universal baseline, then compare normalized quality, evidence density, credibility, and market-readiness. Do not declare a single absolute winner without naming the scenario.
- **JD-fit mode**: Use when a target JD is provided. Score both resume quality and JD fit; emphasize must-have coverage and keyword placement.

## Workflow

### 1. Parse and Normalize

Extract the resume into plain text. Preserve section boundaries:

- Contact and headline
- Education
- Skills
- Work/internship experience
- Projects
- Awards/certifications
- Publications/portfolio links, if present

Remove or redact private contact details from the report. Do not include phone numbers, email addresses, exact street addresses, ID numbers, or private links in final artifacts.

### 2. Choose Scoring Context

Use `references/scoring-rubric.md`.

- No JD: score `baseline_resume_score`.
- No JD and no target role: use `standalone` mode and score universal resume competitiveness. The target clarity dimension should judge whether the resume itself declares a coherent direction; do not punish for missing JD keywords.
- Target role but no JD: score role-market fit based on target role expectations.
- JD provided: score `jd_fit_score` and include must-have coverage.
- Multiple resumes with the same target: score each independently, then use normal comparison rules.
- Multiple resumes across different roles/industries: set `score_mode` to `cross_industry_comparison`, include each resume's own `target_role` when known, and compare normalized quality rather than one JD-fit score.

### 3. Score With Evidence

For each resume version, produce a 100-point score with these default dimensions:

- Target clarity and role alignment: 15
- Evidence strength and quantified impact: 20
- Experience and project depth: 20
- Role competency and skill signal: 15
- Structure, ATS, and scanability: 15
- Credibility and interview defensibility: 15

Every dimension must include:

- Score and max score.
- Evidence from the resume.
- Deductions.
- Rationale.
- Lift actions with estimated score gain.

Use score bands:

- `90-100`: A+ / strong submit-ready.
- `80-89`: A / competitive, but not fully maximized.
- `70-79`: B / usable, but obvious gaps remain.
- `60-69`: C / needs significant rebuild before serious submission.
- `<60`: D / not ready for target use.

### 4. Risk Rules

Do not reward unsupported claims. Penalize:

- Metrics without context or source.
- Skills listed but not evidenced in experience/projects.
- High-ownership words such as 主导、独立负责、Owner、从 0 到 1 when the role is unclear.
- Timeline conflicts, vague company/project names, or inconsistent dates.
- ATS-hostile formatting signals if file/layout evidence is available.
- Resume content that cannot survive interview follow-up.

If data is missing, mark `confidence` as `low` or `medium` rather than inventing details.

### 5. Structured Analysis JSON

Read `references/analysis-schema.md`, then create:

```text
resume_scorecard_analysis.json
```

Validate it:

```bash
python3 <skill_dir>/scripts/validate_scorecard.py \
  --analysis /path/to/resume_scorecard_analysis.json \
  --strict
```

### 6. Render HTML Report

Use the bundled renderer:

```bash
python3 <skill_dir>/scripts/render_scorecard_report.py \
  --analysis /path/to/resume_scorecard_analysis.json \
  --output /path/to/resume-scorecard-report.html \
  --strict
```

The HTML report must include:

- Overall score cards for each resume version.
- Dimension breakdown with bars and deductions.
- Version comparison and winner when multiple versions exist.
- Cross-industry comparison notes when resumes target different industries, including "best for" scenarios instead of a simplistic winner.
- JD-fit coverage when a JD is provided.
- ATS/readability notes.
- Credibility and interview-risk warnings.
- Score lift levers, not full resume rewriting.
- Clear confidence level and missing information.

## Output Guidance

For chat summaries, keep the answer concise:

- Total score and band.
- Biggest 3 deductions.
- Strongest 3 advantages.
- Best version if comparing.
- Whether HTML was generated and where.

Do not end by rewriting the resume unless the user asks. The default close is: what changed the score and what data would make the score more reliable.

## References

- Scoring rubric: `references/scoring-rubric.md`
- Analysis schema: `references/analysis-schema.md`
- Comparison rules: `references/comparison-rules.md`
- HTML report spec: `references/html-report-spec.md`
- Validator: `scripts/validate_scorecard.py`
- Renderer: `scripts/render_scorecard_report.py`
- Template: `assets/report-template.html`
