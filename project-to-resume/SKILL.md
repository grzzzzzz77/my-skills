---
name: project-to-resume
description: Analyze a local project/repository deeply and turn real code, docs, architecture, Git history, framework/AST/code-graph signals, modules, business flows, and technical decisions into validated structured resume analysis JSON, resume-ready project highlights, quantified resume bullets, STAR interview stories, claim-risk labels, a downstream resume-rewrite prompt pack, and a strict script-rendered filterable Chinese HTML report. Use when the user asks to read a local code project thoroughly, mine project亮点, package code experience for a resume, write project bullets, extract resume-ready achievements, generate a prompt for another resume-writing agent, or generate a codebase-to-resume report.
---

# Project To Resume

Use this skill to turn a real local code project into credible resume material. The primary output is a Chinese HTML report containing categorized, selectable resume highlights and bullet points. Also generate a copy-friendly downstream prompt pack when the user may want another agent to merge the project into an existing resume.

## Core Promise

Do not merely beautify wording. First build an evidence trail from the repository, then write resume bullets that can survive interview follow-up and background checks.

Optimize for two use cases:

1. **Direct resume material**: safe bullets, enhanced bullets, and interview stories in the HTML report.
2. **Resume merge handoff**: a prompt pack containing project facts, writing constraints, role assumptions, keywords, and uncertainty notes for a downstream resume-writing agent.

Each final highlight must include:

- Category, such as business value, architecture, core feature, performance, engineering quality, collaboration, security, data, AI, or DevOps.
- Evidence, such as file paths, modules, route/API counts, component counts, Git commits, tests, configs, docs, or concrete code patterns.
- Resume-ready bullet in Chinese.
- Optional stronger bullet with metrics that require user confirmation.
- Risk label: `safe`, `needs_confirmation`, or `risky`.
- Interview talking points: problem, action, result, tradeoff.
- Whether the bullet is suitable for direct paste, downstream rewrite, or only as an idea that needs confirmation.

## Inputs

Ask only for missing essentials that cannot be inferred:

- `repo`: local project path.
- `target_role`: target role, such as 前端开发、后端开发、全栈、测试、AI 工程师.
- `author`: Git author name/email if the user wants personal contribution analysis. If omitted, analyze the whole project and use conservative wording.
- `resume_style`: 校招/实习/社招/转岗; infer when possible.
- `role_claim`: independent owner, module owner, team member, or unknown. Ask when this affects truthfulness.
- `publicity`: whether internal metrics, customer names, or company details can be written publicly. Ask when the repo looks commercial/private.
- Existing resume or JD, optional. Use them to tailor language, not to fabricate project facts.

## Workflow

### 1. Evidence Collection

Run the bundled script first unless the repository is inaccessible:

```bash
python3 <skill_dir>/scripts/collect_project_evidence.py \
  --repo /path/to/project \
  --output /path/to/output-dir \
  --author "Author Name"
```

If `author` is unknown and Git history has multiple authors, show the top authors and ask which one to analyze. If the user says to analyze the whole project, continue without author-specific ownership claims.

Read the script outputs:

- `project_evidence.json`
- `project_evidence.md`

Use these evidence sections before choosing files to inspect:

- `project_evidence.json.framework_profiles`: framework-specific signals and confidence.
- `project_evidence.json.code_graph`: route candidates, API call candidates, local import edges, entrypoints, AST summaries, and business-flow candidates.

Then inspect targeted files directly. At minimum read:

- `CLAUDE.md`, `AGENTS.md`, README, docs, package manifests, and lockfile metadata when present.
- Entrypoints and route files.
- Core business modules.
- API/service layer.
- State management or data layer.
- Tests and CI/config files.
- Git diffs or key commits if author analysis is requested.

Do not read every file blindly. Use the evidence output to choose the most relevant docs, modules, routes, services, stores, tests, and configs.

### 2. Confirm Truth-Critical Unknowns

Ask at most 1-2 questions before writing only when the answer cannot be inferred and would change resume truthfulness:

- Personal role/boundary: 独立完成、负责人、负责某模块、团队成员, or only analysis of the whole project.
- Disclosure boundary: whether internal metrics, customer names, revenue, traffic, or company-specific details can be used.

If the user wants you to proceed without answering, continue with conservative assumptions and mark them in the report and prompt pack.

### 3. Understand the Project

Create a concise project model:

- What problem the project solves.
- Primary users and business flows.
- Tech stack and architecture.
- Core modules and data flow.
- Integration points: API, database, auth, payment, third-party services, AI/model calls, file upload, message, map, charts, etc.
- Engineering quality signals: tests, types, lint, CI, modularization, error handling, caching, performance, observability.
- Personal contribution signals if an author is specified.

For frontend projects, also map pages/components to business flows. For backend projects, map endpoints/services/models/jobs. For full-stack projects, connect frontend flows to backend APIs.

Capture at least one explicit flow map before writing final bullets:

- Frontend: page -> component -> service/API -> state/store -> user scenario.
- Backend: route/controller -> service -> model/repository -> external dependency -> business scenario.
- Full-stack: frontend flow -> API endpoint -> backend service -> data persistence.
- AI/data project: input -> processing/prompt/model -> output -> evaluation/guardrail.

### 4. Mine Resume Highlights

Use `references/highlight-rubric.md` to score candidate highlights. Prefer highlights that combine:

- Business scenario: what user/business problem this module serves.
- Technical difficulty: why it was non-trivial.
- Personal action: what the candidate actually did.
- Impact: code-derived metric, verified metric, or clearly marked metric needing confirmation.

Generate at least 8 candidate highlights when evidence allows, grouped into categories:

- Business/product delivery
- Architecture and system design
- Core features
- Performance and reliability
- Engineering quality and maintainability
- Data/AI/automation
- Security/auth/compliance
- Collaboration and ownership

### 5. Write Structured Analysis JSON

Read `references/analysis-schema.md`, then create:

```text
project_resume_analysis.json
```

This JSON is the handoff between deep project understanding and deterministic report rendering. It must include:

- Project summary, target role, role assumption, disclosure assumption.
- Business flow map, module map, API/page/data-flow notes in `facts`.
- Keywords suitable for the skills section.
- Categorized highlights with `risk`, `readiness`, evidence paths, safe bullet, enhanced bullet, STAR notes, and data to confirm.
- Optional custom `prompt_pack` only when the generated default prompt would not be enough.

Do not manually replace placeholders in `assets/report-template.html` for final delivery. Use the render script in step 9.

Validate the JSON before rendering:

```bash
python3 <skill_dir>/scripts/validate_analysis.py \
  --analysis /path/to/project_resume_analysis.json \
  --strict
```

Fix any validation errors or warnings. Final delivery should pass strict validation unless the user explicitly asks for a draft.

### 6. Quantification Rules

Use three metric tiers:

1. `verified`: Directly observed in repo, logs, tests, docs, issue text, or user-provided facts.
2. `code_derived`: Counted or inferred from code, such as `12 pages`, `28 components`, `16 API endpoints`, `4 roles`, `3 platforms`, `70+ commits`, `20+ tests`.
3. `needs_confirmation`: Reasonable business metric suggestions, such as conversion, latency, retention, adoption, cost, efficiency, or manual time saved. These must be labeled as needing user confirmation.

Never present `needs_confirmation` metrics as facts. In the HTML report, separate:

- **可直接写入简历**: safe wording.
- **增强版，需要你确认数据**: stronger wording with suggested metrics.
- **不要直接写**: risky wording to avoid.

When the user explicitly wants more quantified bullets, add metric placeholders or conservative ranges, but keep the risk label visible.

### 7. Write Resume Bullets

Use this structure:

```text
动词 + 技术/方法 + 业务对象 + 规模/指标 + 结果
```

Good examples:

- 负责订单模块重构，基于状态机拆分 6 类订单流转场景，沉淀可复用状态组件与异常兜底逻辑，降低后续需求改动成本。
- 搭建后台权限与菜单配置体系，覆盖 4 类角色和 20+ 页面访问控制，支持运营后台按角色分配功能入口。
- 封装统一请求、错误处理和登录态刷新链路，减少页面重复鉴权逻辑，提升接口联调与问题定位效率。

Avoid unproven wording:

- 不要写“主导/负责全盘/从 0 到 1/提升 80%” unless evidence supports it.
- Do not invent real user counts, revenue, GMV, order volume, or latency.
- Do not claim production impact when the project appears to be a demo, toy, school assignment, or unfinished prototype.

### 8. Generate Downstream Resume Prompt Pack

Generate a second copy-friendly text artifact through the renderer unless the user only wants HTML:

```text
{project-name}-resume-project-pitch.txt
```

Use `references/pitch-prompt-pack.md` for the exact structure. The prompt pack must include:

- Writing instructions for a downstream agent that will see the user's original resume.
- Project name, one-sentence overview, target role, and role/disclosure assumptions.
- Technical highlights grouped by category.
- Safe bullets and enhanced bullets that require confirmation.
- Verified/code-derived metrics with sources.
- Keywords suitable for the skills section.
- Unknowns the user should confirm before sending the resume.

On macOS, optionally copy the prompt pack to the clipboard with `pbcopy` after writing the file. If clipboard tools are unavailable, just save the file and link it in the final response.

### 9. Generate HTML Report

Default final artifact: create a polished standalone Chinese `.html` report. If the user did not specify a path, save it to the project parent or Desktop as:

```text
{project-name}-project-to-resume-report.html
```

Run the bundled renderer:

```bash
python3 <skill_dir>/scripts/render_resume_report.py \
  --evidence /path/to/project_evidence.json \
  --analysis /path/to/project_resume_analysis.json \
  --output /path/to/{project-name}-project-to-resume-report.html \
  --prompt-output /path/to/{project-name}-resume-project-pitch.txt \
  --strict
```

Use the renderer output as the final report. The report must include:

- Project overview and target role.
- Evidence summary.
- Filterable highlight cards by category, risk, and resume readiness.
- Project fact pack for downstream resume rewrite.
- Each highlight card with:
  - title
  - category
  - evidence
  - safe resume bullet
  - enhanced bullet requiring confirmation
  - STAR interview notes
  - risk label
- A “直接可粘贴到简历” section.
- A “需要补充真实数据后再写” section.
- A “下游 Agent 简历改写 Prompt” section.
- A “面试追问准备” section.

Final chat response should be short: link the HTML file, link the prompt pack when generated, list the best 3-5 bullets, and mention any data that still needs confirmation.

## Validation

Before final delivery:

- Confirm the report contains multiple categories, not only generic technical wording.
- Confirm every bullet has evidence or a risk label.
- Confirm no sensitive secrets from the repo are copied into the report.
- Confirm role assumptions and disclosure assumptions are visible when not user-confirmed.
- Confirm `project_resume_analysis.json` exists and passes `scripts/validate_analysis.py --strict`.
- Confirm the final report was rendered by `scripts/render_resume_report.py --strict`.
- Confirm the HTML opens as a static file and the filters work.
- Run no build/test command unless required for understanding or explicitly requested. Static scanning and Git commands are enough by default.

## References

- Highlight scoring: `references/highlight-rubric.md`
- Structured analysis schema: `references/analysis-schema.md`
- Bullet and metric rules: `references/resume-bullet-rules.md`
- Downstream prompt pack: `references/pitch-prompt-pack.md`
- HTML report requirements: `references/html-report-spec.md`
- Evidence collector: `scripts/collect_project_evidence.py`
- Analysis validator: `scripts/validate_analysis.py`
- Report renderer: `scripts/render_resume_report.py`
- Report template: `assets/report-template.html`
- Golden examples: `examples/vue-admin-golden-analysis.json`, `examples/python-api-golden-analysis.json`
