# Downstream Resume Prompt Pack

Use this reference when generating `{project-name}-resume-project-pitch.txt` or the matching section inside the HTML report.

## Purpose

The prompt pack is not a final resume. It is a structured handoff to another agent that will receive the user's original resume and merge this project into it.

## Rules

- Use only facts from repository evidence, user input, or clearly labeled code-derived counts.
- Do not invent users, revenue, GMV, traffic, performance gains, team size, or ownership.
- Estimated metric directions are allowed only as placeholders under a separate section. They are prompts for the user to confirm, not facts.
- Mark role assumptions and disclosure assumptions.
- Keep safe bullets separate from enhanced bullets that need confirmation.
- Keep verified/code-derived metrics separate from estimated metric suggestions.
- Include highlight logic-chain details when available so the downstream agent can preserve the user's ability to explain the project in interviews.
- Preserve enough project facts for the downstream agent to match the user's original resume style.

## Template

```text
我想把一个项目写进简历。请你结合我下面附上的原始简历，把这个项目用合适的措辞和详略融入进去，并输出一版完整的新简历。

写作要求：
1. 风格、语言、人称、bullet 详略与我的原始简历保持一致；如果原简历是英文，请翻译成地道英文。
2. 用“动作 + 技术/方法 + 业务对象 + 规模/指标 + 结果”组织，不要写成功能清单。
3. 只能使用下方提供的事实和数字，不要编造用户量、收益、性能提升、团队规模等信息。
4. 项目经历建议控制在 3-5 条 bullet，可保留一句项目概述。
5. 与原简历已有经历、技能或项目重复时，帮我合并去重，并指出改动点。
6. 对“需要确认”的指标或角色表述，不要直接写成事实；可用占位符或在修改建议中提醒我补充。
7. 对“估算指标方向”只能保留为待确认建议，不要把它改写成已发生的业务结果。

项目信息：
【项目名称】
...

【一句话概述】
...

【目标岗位】
...

【我的角色/边界】
...

【是否可公开的边界】
...

【技术栈与关键词】
- ...

【项目事实与证据】
- ...

【可直接写入简历的 bullet】
- ...

【亮点链路详情，用于理解和面试复述】
- 亮点：
- 一句话解释：
- 闭环链路：
- 证据：
- 简历边界：

【增强版 bullet，需要我确认数据后再用】
- ...

【估算指标方向，不可直接当事实】
- 指标方向：
- 推测依据：
- 可替换占位句：
- 需要我确认：

【不要直接写的高风险表述】
- ...

【面试可展开的 STAR 故事】
- 背景：
- 任务：
- 行动：
- 结果：
- 取舍：

【待我确认的问题】
- ...

请基于以上项目信息与我的原始简历，输出新版完整简历。
```

## Good Handoff Shape

Prefer this:

```text
【可直接写入简历的 bullet】
- 负责后台权限配置模块开发，基于路由守卫、菜单配置和接口权限封装访问控制链路，覆盖 4 类角色和 20+ 页面入口。

【增强版 bullet，需要我确认数据后再用】
- 负责后台权限配置模块开发，沉淀角色、菜单和接口权限复用能力，将新角色配置时间从 X 小时缩短至 Y 分钟。

【估算指标方向，不可直接当事实】
- 指标方向：配置效率提升
- 推测依据：代码中存在角色、菜单、接口权限配置复用链路。
- 可替换占位句：将新角色配置时间从 X 小时缩短至 Y 分钟。
- 需要我确认：实际配置前后耗时、角色数量、是否由本人负责。
```

Avoid this:

```text
- 主导公司核心后台从 0 到 1 建设，提升运营效率 80%。
```

Unless the repository or user explicitly proves ownership, production scope, and the metric.
