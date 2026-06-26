# Resume Bullet and Metric Rules

## Bullet Formula

Use:

```text
动作动词 + 技术/方法 + 业务对象 + 规模/指标 + 结果/价值
```

Good verbs for Chinese technical resumes:

- 搭建、设计、封装、重构、实现、优化、接入、沉淀、抽象、拆分、治理、排查、联调、交付、维护

Prefer concrete nouns:

- 权限体系、订单流转、审批链路、数据看板、组件库、接口层、缓存策略、错误兜底、发布流程、监控告警

## Metric Tiers

### 1. Verified

Use as fact when backed by code, docs, logs, tests, Git, or user input.

Examples:

- `30+ commits`
- `12 个页面`
- `18 个接口`
- `4 类角色`
- `20+ 组件`
- `6 个核心模块`

### 2. Code-Derived

Use as fact if counted from files, routes, tests, or configuration. Mention it as code-derived when appropriate.

Examples:

- "覆盖 20+ 后台页面的访问控制"
- "封装 15+ 接口的统一请求层"
- "沉淀 10+ 可复用表单/列表组件"

### 3. Needs Confirmation

Use only in enhanced bullets or a separate "待确认数据" section.

Examples:

- "将人工处理时间从 X 分钟降至 Y 分钟"
- "支撑日均 X 单/请求/用户"
- "使运营配置效率提升 X%"
- "页面加载耗时降低 X%"

Never put unconfirmed numbers in the safe bullet.

## Risk Labels

### safe

The bullet is grounded in code evidence and uses conservative wording.

### needs_confirmation

The idea is plausible, but needs user confirmation for ownership, business metric, production use, or exact result.

### risky

The claim is unsupported or overstates scope. Keep it in the report only as "不要直接写".

## Before/After Pattern

Weak:

```text
负责后台管理系统开发。
```

Safe:

```text
参与后台管理系统核心模块开发，封装列表、筛选、表单和接口请求通用能力，支撑多页面复用和后续需求迭代。
```

Enhanced, needs confirmation:

```text
参与后台管理系统核心模块开发，沉淀列表/筛选/表单等 10+ 通用组件，将同类页面开发周期缩短约 X%。
```

## Interview STAR Notes

For each strong bullet, prepare:

- Situation: 业务背景和原问题。
- Task: 你负责什么边界。
- Action: 技术方案、拆分、关键实现。
- Result: 代码可验证结果 + 待确认业务结果。
- Tradeoff: 为什么这么设计，有什么边界。

## Role and Disclosure Safety

Before using high-ownership words, check whether the role is confirmed.

Use only when confirmed by Git/user facts:

- 主导、Owner、独立负责、从 0 到 1、全盘设计

Use conservative wording when role is unknown:

- 参与、负责其中、配合完成、围绕某模块实现、在项目中落地

For commercial or internal projects, do not expose customer names, revenue, traffic, order volume, private endpoints, or internal architecture details unless the user confirms they are allowed to appear in a resume.

## Downstream Prompt Packaging

When generating a prompt pack for another resume-writing agent:

- Include safe bullets exactly as they can be pasted.
- Include enhanced bullets only under "需要我确认数据后再用".
- Include keywords separately so the downstream agent can decide whether to place them in the skills section.
- Include unknowns and assumptions so the downstream agent does not accidentally turn them into facts.
