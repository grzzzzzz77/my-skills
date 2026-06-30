---
name: resume-optimize
description: "One-time standalone resume optimization from an existing resume, producing an evidence-safe Markdown draft plus fact boundary, rewrite notes, confirmation items, and ATS/layout guidance. Use for 无 JD 简历润色, 一次性完整优化简历, 通用投递底稿, 技能区/项目经历基于原文改写, or safe optimized draft. Do not use for JD matching, ongoing job-search workflows, scoring/comparison reports, career planning, interview prep, company research, or codebase-to-resume extraction."
---

# Resume Optimize

Use this skill to optimize an existing resume into an evidence-safe draft. It is standalone and one-time: no JD matching, no job-search case management, no application tracker, no interview workflow, and no project-code extraction.

## Routing

Use this skill when the user wants resume-body optimization based on an existing resume:

- 无 JD 简历润色 or 一次性完整优化简历.
- 通用投递底稿 or safe optimized draft.
- 技能区、项目经历、实习经历, or summary rewritten from the existing text.
- A weak target direction such as "大概投前端" without JD matching.

Use another skill when the request is not standalone resume optimization:

- `job-ok`: JD matching, "按这个 JD 命中/适配/逐条优化", job opportunity ranking, application tracking, interview workflow, or a long-running job-search case.
- `resume-scorecard`: scores, benchmarking, resume comparison, JD fit score, or HTML score report.
- `resume-deep-report`: career planning or market/career strategy report.
- `project-to-resume`: inspect local project code and extract evidence.
- `smart-interview-prep`: interview simulation, question bank, or mock interview.
- `research-company`: company research or interview/company dossier.

JD gray zone:

- If the user says "按这个 JD 匹配/命中/逐条优化/适配分/投这个岗位", route away from this skill.
- If the user says "我大概投前端, 这个 JD 只是参考, 不用逐条匹配", stay in this skill and treat the JD only as weak direction.

## Inputs

Ask only for missing essentials:

- `resume`: pasted text, Markdown, PDF, DOCX, or a local file path.
- `target_direction`: optional. If omitted, infer the broad direction from the resume and state it as an assumption.
- `candidate_stage`: optional, such as 校招、实习、应届、1-3 年、3-5 年、转岗.
- `optimization_level`: optional: `conservative`, `balanced`, or `strong`. Default `balanced`.
- `mode`: optional: `quick`, `full`, or `file`. Infer it from the request when possible.

If PDF/DOCX parsing fails or text order is unreliable, ask for pasted text or a text/Markdown export.

## Mode Selection

Use the lightest mode that satisfies the request:

- `quick`: Use when the user asks to rewrite one section, one project, a skills block, a summary, or a few bullets. Output only the revised text, concise notes, and risk/confirmation flags.
- `full`: Use when the user asks for complete resume optimization, a general submission base, content plus layout, or does not limit the scope. Output the full contract below.
- `file`: Use when the user asks for a saved deliverable. Save Markdown or DOCX-ready Markdown. This skill has no bundled DOCX/HTML renderer; create DOCX/HTML only when the user explicitly asks and suitable document tooling is available.

`quick` may omit the full fact boundary table, but it must still flag risky claims, unsupported metrics, and unconfirmed ownership. `full` must show the fact boundary before the draft.

## Workflow

1. Parse the resume and preserve section meaning.
2. Redact private phone numbers, emails, detailed addresses, ID numbers, and private links in analysis unless the user asks to keep them.
3. Build a fact boundary: `confirmed_facts`, `reasonable_inferences`, `needs_confirmation`, `risky_claims`, `content_confidence`, and `layout_confidence`.
4. Ask at most 1-3 questions only when missing facts would materially affect truthfulness. Otherwise proceed conservatively.
5. Read `references/optimization-rules.md` before rewriting section text, bullets, skills, or final resume content.
6. Produce the selected mode output.

Confidence rules:

- `content_confidence`: high/medium/low based on source completeness and parse quality.
- `layout_confidence`: high only when the original layout is visible or reliably extracted; low when only pasted text is available.
- When `layout_confidence` is low, phrase ATS/layout guidance as recommendations, not visual diagnosis.

File naming rules:

- Save to the user-provided output path when given; otherwise save beside the source file, or the current working directory for pasted text.
- Default Markdown filename: `resume-optimize-YYYYMMDD-{full|quick|file}.md`.
- If a safe target direction is obvious, append it before the mode, such as `resume-optimize-YYYYMMDD-frontend-full.md`.
- Avoid names that expose phone, email, ID number, or private employer/client information.

## Full Output Contract

For `full` mode, output these sections in order:

1. **事实边界表**: confirmed facts, reasonable inferences, needs confirmation, risky claims, content_confidence, layout_confidence.
2. **优化后完整简历草稿**: a clean Markdown resume draft based only on confirmed facts and safe inferences.
3. **主要改动说明**: section-level changes and why they help.
4. **原句 -> 优化后示例**: 3-8 representative before/after pairs.
5. **待确认增强项**: stronger metrics, scope, ownership, or outcomes the user can confirm later.
6. **排版与 ATS 建议**: concise guidance aligned with layout confidence.
7. **风险提醒**: interview-defense and truthfulness risks.

Apply `Final Draft Safety` from the rewrite rules before returning the resume draft.

## Quick Output Contract

For `quick` mode, output:

1. **优化后文本**: rewritten section/bullets only.
2. **改写说明**: 1-4 concise notes.
3. **待确认 / 风险**: unsupported metrics, ownership, tools, or wording to avoid.

Do not expand into a full resume unless the user asks.

## Style

Default to Chinese unless the resume is English or the user asks otherwise. Follow final draft safety and rewrite rules in `references/optimization-rules.md`.

## References

- Rewrite rules: `references/optimization-rules.md`
