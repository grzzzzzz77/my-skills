---
name: project-to-resume
description: Turn local code evidence into evidence-backed resume bullets, project highlights, anchor-linked highlight logic-chain details, STAR interview stories, optional HTML reports, and downstream resume-rewrite prompt packs. Requires a local repository, project path, or explicit code files/snippets as evidence; not for resume polishing without code evidence. Use for codebase-to-resume, 代码项目转简历, 项目亮点, 简历项目描述, project bullets, contribution packaging, 项目链路闭环, 亮点详情跳转, project value scoring, and portfolio/interview story extraction across frontend/uni-app, Node/backend, AI/Agent, data automation, and full-stack projects.
---

# Project To Resume

Use this skill to turn real project code into credible resume material. Do not merely polish wording; first anchor claims in repository or code evidence.

## Routing

Use this skill when the user provides or points to code evidence:

- local repository/project path
- 1-2 source files, diffs, or code snippets for local evidence
- request for project bullets, project highlights, STAR stories, project value score, HTML report, or downstream resume prompt pack

Do not use this skill for plain resume rewriting without code evidence. Use `resume-optimize` for resume-only polishing, `resume-scorecard` for scoring existing resumes, and `job-ok` for JD matching or ongoing job-search workflows.

## Inputs

Ask only for missing truth-critical details:

- `repo` or code evidence: local repository path, project folder, specific files, diff, or pasted source snippets.
- `target_role`: target role, such as 前端开发、后端开发、全栈、测试、AI 工程师.
- `mode`: optional: `micro`, `quick`, `standard`, or `strict_report`.
- `output_dir`: optional. Use it for generated evidence, JSON, reports, and prompt packs.
- `author`: optional Git author name/email for personal contribution analysis.
- `role_claim`: optional ownership boundary, such as independent owner, module owner, team member, or unknown.
- `publicity`: optional disclosure boundary for internal metrics, customer names, private APIs, revenue, traffic, or company details.
- Existing resume/JD: optional context for wording only; never use it to fabricate project facts.

If role boundary or disclosure boundary would materially change truthfulness, ask at most 1-2 questions. If the user wants to proceed, use conservative assumptions and show them.

## Output Directory

Use a controlled output directory for any generated files:

1. Use the user-provided `output_dir` when present.
2. Otherwise use `<current-working-directory>/outputs/project-to-resume/<project-name>/`.
3. Do not default to Desktop or the project parent directory unless the user explicitly asks.
4. Keep generated files together: `project_evidence.json`, `project_evidence.md`, `project_resume_analysis.json`, `{project-name}-project-to-resume-report.html`, and `{project-name}-resume-project-pitch.txt`.

## Mode Selection

Use the lightest mode that satisfies the request:

- `micro`: Use when the user provides only 1-2 files, a diff, a snippet, or asks for one small section. Do not run full repository collection. Inspect only supplied evidence and output localized bullets/caveats in chat.
- `quick`: Use for "写几条/5 条/bullet/项目描述" against a local repo. Run the collector, inspect only strongest evidence files, and answer in chat. Do not create JSON, HTML, or prompt pack unless asked.
- `standard`: Use for reusable project analysis, categorized highlights, STAR stories, highlight logic-chain details, project score, or handoff prompt. Run collector, inspect targeted files, write `project_resume_analysis.json`, and validate it.
- `strict_report`: Use for HTML reports, deliverables, uploadable/package-quality output, or stable repeatable results. Run collector, structured JSON with anchor-linked highlight logic chains, evidence-aware strict validation, renderer, and prompt pack.

If wording is ambiguous:

- "只看这段/这个文件/这个 diff" -> `micro`
- "写几条/5 条/bullet/项目描述" -> `quick`
- "分析项目/整理亮点/面试讲法/含金量" -> `standard`
- "HTML 报告/漂亮报告/可交付/上传/完整报告" -> `strict_report`

## Evidence Workflow

For `quick`, `standard`, and `strict_report`, run the collector first:

```bash
python3 <skill_dir>/scripts/collect_project_evidence.py \
  --repo /path/to/project \
  --output /path/to/output_dir \
  --author "Author Name"
```

Read `project_evidence.json` and `project_evidence.md`, then inspect targeted source files. Use the evidence output to choose relevant docs, entrypoints, routes, services, stores, tests, configs, and framework-specific files. Do not read every file blindly.

For monorepos or multi-app workspaces, inspect `manifests.workspace_projects`, top-level `signal_files_total`, `signal_lines_estimate`, and `signal_policy` before choosing highlights. Prefer the actual product/service source directories over bundled examples, vendored packages, generated resources, screenshots, or built-in skill packs. If the root evidence is noisy, run the collector again on the strongest subprojects and compare root vs subproject evidence before writing final highlights.

When evidence includes tests, treat implementation files as the main runtime chain and tests as closure/quality proof. Do not let test files, reproduction scripts, generated resources, or a misleading parent directory name become the primary reason for a highlight.

For `micro`, do not run the collector unless the user also provides a repo and asks for repo-level confidence. Treat claims as local-evidence-only and label missing repo context.

Author handling:

- If `author` is unknown and Git history has multiple authors, show top authors and ask which one to analyze.
- If the user says to analyze the whole project, continue without author-specific ownership claims.

## Reference Loading

Load references only when needed:

- Before selecting/scoring highlights: `references/highlight-rubric.md`.
- Before writing anchor-linked highlight details or explaining a highlight's full path to a beginner: `references/highlight-logic-chain.md`.
- Before writing bullets, metric strategy, STAR notes, ownership wording, or disclosure-sensitive content: `references/resume-bullet-rules.md`.
- Before creating `project_resume_analysis.json`: `references/analysis-schema.md`.
- Before generating a prompt pack: `references/pitch-prompt-pack.md`.
- Before rendering or QA-ing HTML reports: `references/html-report-spec.md`.

## Deliverables

### Micro / Quick Chat Output

Return:

1. evidence scope used
2. 3-8 safe bullets, or fewer if evidence is limited
3. optional anchor-linked detail notes when the user needs to understand the highlight chain
4. optional enhanced bullets requiring confirmation
5. risk/unknowns, including role, metrics, and disclosure gaps
6. interview talking points when useful

### Standard Output

Create and validate `project_resume_analysis.json` using `references/analysis-schema.md`. For every final highlight, include a stable `detail_anchor` and `logic_chain` so the summary bullet can jump to a beginner-readable detail section explaining the full closed loop.

Run:

```bash
python3 <skill_dir>/scripts/validate_analysis.py \
  --analysis /path/to/project_resume_analysis.json \
  --evidence /path/to/project_evidence.json \
  --strict
```

### Strict Report Output

Render with the bundled script; do not manually edit the HTML template for final delivery:

```bash
python3 <skill_dir>/scripts/render_resume_report.py \
  --evidence /path/to/project_evidence.json \
  --analysis /path/to/project_resume_analysis.json \
  --output /path/to/output_dir/{project-name}-project-to-resume-report.html \
  --prompt-output /path/to/output_dir/{project-name}-resume-project-pitch.txt \
  --strict
```

Use `references/html-report-spec.md` for report QA. The final chat response should link generated files, list the best 3-5 safe bullets, and name data still needing confirmation.

## Validation

Before final delivery:

- Confirm every final bullet has evidence or a visible risk label.
- Confirm every final highlight has `detail_anchor` and `logic_chain` in standard/strict_report outputs.
- Confirm safe bullets do not contain unverified business metrics, ownership, users, revenue, GMV, latency, or production impact.
- Confirm role/disclosure assumptions are visible when not user-confirmed.
- Confirm generated JSON passes `scripts/validate_analysis.py --strict`; in report mode include `--evidence project_evidence.json`.
- Confirm strict reports are rendered by `scripts/render_resume_report.py --strict`.
- For skill maintenance, run `scripts/check_golden_fixtures.py`.
- For substantial skill revisions, forward-test collector behavior on 2-3 real local repositories when available, not only golden fixtures; record repo type, command, pass/fail, and notable gaps in the final response.
- Run no project build/test command unless required for understanding or explicitly requested. Static scanning, collector scripts, renderer validation, and Git commands are enough by default.

## References

- Highlight scoring: `references/highlight-rubric.md`
- Structured analysis schema: `references/analysis-schema.md`
- Bullet, metric, ownership, and disclosure rules: `references/resume-bullet-rules.md`
- Highlight logic-chain detail rules: `references/highlight-logic-chain.md`
- Downstream prompt pack: `references/pitch-prompt-pack.md`
- HTML report requirements: `references/html-report-spec.md`
- Evidence collector: `scripts/collect_project_evidence.py`
- Analysis validator: `scripts/validate_analysis.py`
- Report renderer: `scripts/render_resume_report.py`
- Golden fixture check: `scripts/check_golden_fixtures.py`
- Report template: `assets/report-template.html`
- Golden examples: `examples/*-golden-analysis.json`
- Golden evidence fixtures: `examples/fixtures/*-project_evidence.json`
