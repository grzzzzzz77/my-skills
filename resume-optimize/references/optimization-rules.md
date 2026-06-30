# Resume Optimization Rules

Use this reference when rewriting resume sections, bullets, skills, or layout guidance.

## Contents

- [Priority Order](#priority-order)
- [Final Draft Safety](#final-draft-safety)
- [Optimization Intensity](#optimization-intensity)
- [Bullet Formula](#bullet-formula)
- [Ownership Verbs](#ownership-verbs)
- [Metrics](#metrics)
- [Skills And Tools](#skills-and-tools)
- [Section Guidance](#section-guidance)
- [Layout And ATS](#layout-and-ats)
- [Final Check](#final-check)

## Priority Order

1. Truthfulness and evidence.
2. Interview defensibility.
3. Recruiter scanability.
4. ATS readability.
5. Wording polish.

Style never overrides facts.

## Final Draft Safety

The optimized resume draft is the safe version, not a scratchpad.

Do not put these in the final resume draft unless the user explicitly asks for a placeholder version:

- `X`, `Y`, `Z`
- `待确认`
- `[补充真实数据]`
- unconfirmed user scale, revenue, performance change, team size, ownership, or awards

Use placeholders only in:

- `待确认增强项`
- before/after examples
- optional alternate wording clearly marked as requiring confirmation

Do not add new tools, frameworks, certificates, awards, employers, projects, responsibilities, or business outcomes unless they appear in the source resume or the user confirms them.

## Optimization Intensity

Use the requested intensity without changing truth boundaries:

- `conservative`: improve grammar, structure, section order, and repetition. Keep the original positioning mostly intact.
- `balanced`: default. Reframe bullets into clearer action/method/scope/result language, infer a broad target direction when the resume makes it obvious, and reorganize for scanability.
- `strong`: sharper packaging within evidence boundaries. Move strongest proof earlier, make role positioning more explicit, compress weak sections, and propose stronger metric/ownership upgrades only in `待确认增强项`.

Never treat `strong` as permission to invent impact, seniority, ownership, business scale, or domain depth.

## Bullet Formula

Prefer:

```text
动作 + 方法/工具/机制 + 场景/对象 + 范围/产出/结果 + 能力信号
```

Weak:

```text
负责项目开发，完成页面和接口联调。
```

Better:

```text
围绕用户资料补全流程，完成表单页面开发、接口联调与异常提示优化，支撑资料采集链路闭环，体现前端页面实现与联调能力。
```

Enhanced only if confirmed:

```text
围绕用户资料补全流程，完成 X 个表单页面开发、接口联调与异常提示优化，将资料提交失败率从 X% 降至 Y%。
```

## Ownership Verbs

Use strong verbs only when supported:

- Confirmed strong ownership: 主导、独立负责、设计、搭建、推动、落地.
- Unclear or team work: 参与、负责其中、配合、围绕某模块完成、协助推进.
- Avoid when unsupported: 从 0 到 1、Owner、全权负责、架构、负责人、核心贡献者.

If the source says only "参与" or gives no contribution boundary, do not upgrade it to "主导" or "独立负责".

## Metrics

Use numbers only when verified by the resume, user, docs, screenshots, logs, or reliable evidence.

If a number is missing:

- Do not invent it.
- Keep the final resume non-numeric.
- Put possible metrics under `待确认增强项`.
- Use `X/Y/Z` only outside the final draft.

Acceptable non-numeric outcomes:

- 支撑流程闭环
- 提升页面复用与维护效率
- 降低重复配置成本
- 优化异常提示与用户反馈
- 提升信息层级和扫读效率
- 强化岗位关键词与经历证据的一致性

## Skills And Tools

Group skills by category and evidence:

- Put tools with project/work evidence first.
- Keep coursework-only or self-study tools lower or mark them as weaker.
- Remove unsupported tool lists unless the user confirms them.
- Do not add fashionable keywords only because they fit the target direction.

Common groups:

- 前端基础
- 框架与生态
- 工程化与构建
- 后端/数据库
- 测试与协作工具
- 数据分析/AI 工具

## Section Guidance

### Header

Keep name, target role, city if useful, and safe contact placeholders. Do not expose private contact details in shared analysis.

### Summary

Use only when it clarifies target and strongest evidence. Keep it to 2-3 lines. Avoid labels like `资深`, `专家`, or `架构师` unless clearly proven.

### Projects

For each major project, prefer:

- project name and role
- tech stack already evidenced by the resume
- 3-5 bullets
- strongest role-relevant bullet first
- one complexity/tradeoff bullet when evidence exists
- one outcome or deliverable bullet using safe evidence

### Internships / Work

Lead with business context and responsibilities. Separate real work from school-like projects. Clarify personal contribution boundary.

### Education / Awards

Keep factual and compact. Keep GPA/ranking/awards only when helpful or requested.

## Layout And ATS

Tie layout comments to layout confidence:

- `layout_confidence: high`: original layout is visible or reliably extracted; you may diagnose spacing, density, hierarchy, and alignment.
- `layout_confidence: medium`: file structure is partially visible; qualify visual claims.
- `layout_confidence: low`: only pasted text or unreliable extraction; give recommendations, not visual diagnosis.

Recommend:

- standard section names
- consistent dates like `2024.06 - 2024.09`
- aligned project/company/date lines
- bullets mostly within 1-2 lines
- no image-only text
- no contact info only in header/footer/text boxes
- export to text-copyable PDF

## Final Check

Before returning:

- final resume draft contains no unconfirmed metrics
- no `X/Y/Z` placeholders in final draft unless explicitly requested
- no unsupported strong ownership verbs
- no new tools/skills added unless present in source resume or confirmed by the user
- skills are supported by experiences or moved to weaker/confirmation wording
- metrics are verified or moved out of the final resume
- the optimized version remains believable in an interview
- full mode shows fact boundary before draft
- quick mode may omit full fact table but must still flag risky claims
- ATS/layout advice matches `layout_confidence`
