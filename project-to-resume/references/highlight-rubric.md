# Highlight Rubric

Use this rubric to decide whether a codebase finding is worth turning into a resume highlight.

## Score Dimensions

Rate each candidate from 0-3.

| Dimension | 0 | 1 | 2 | 3 |
|---|---|---|---|---|
| Business relevance | Purely internal or trivial | Supports a small feature | Supports a clear user/business flow | Connects to core product value |
| Technical difficulty | CRUD or static page | Standard integration | Multiple modules/states/edge cases | Architecture, performance, reliability, or cross-system challenge |
| Evidence strength | Guess only | One file or weak clue | Multiple files/configs/commits | Code + tests/docs/git/user facts agree |
| Resume readability | Too generic | Needs heavy explanation | Clear bullet possible | Strong bullet + STAR story possible |
| Differentiation | Common task | Some specificity | Role-relevant signal | Distinctive project selling point |
| Handoff readiness | Cannot be reused downstream | Needs many assumptions | Clear project fact for another agent | Ready for resume merge prompt with facts, keywords, and caveats |

Prioritize candidates scoring 12+ total. Keep 9-11 as backup. Discard or label risky below 9 unless the user asks for exhaustive notes.

For strict reports, a high-scoring highlight should also pass the closed-loop test:

```text
problem/trigger -> technical mechanism -> output/feedback -> evidence-backed closure -> resume boundary
```

If the chain cannot be explained to a beginner with concrete evidence paths, reduce `resume_readability` or `handoff_readiness` instead of compensating with stronger wording.

In strict reports, add a short `score_breakdown` or `score_rationale` when useful so the reader understands why a highlight is ranked high. Keep it concise:

```json
"score_breakdown": {
  "business_relevance": 3,
  "technical_difficulty": 3,
  "evidence_strength": 3,
  "resume_readability": 3,
  "differentiation": 3,
  "handoff_readiness": 2,
  "ai_application_bonus": 2
},
"score_rationale": "Agent 记忆与上下文注入属于 AI 应用核心能力，证据包含实现、测试和生命周期接入。"
```

## Project Resume Value Score (100 Points)

Use this score when the user asks for project comparison, "含金量", "打分", or "为什么没上 90". Score the whole project, not a single highlight.

| Dimension | Points | What To Look For |
|---|---:|---|
| Technical depth | 25 | Architecture, state complexity, performance/reliability, cross-system integration, hard edge cases, tests or quality mechanisms. |
| AI/rarity signal | 20 | Agent/RAG/tool calling/model orchestration/evaluation, or otherwise uncommon role-relevant technical depth. Non-AI projects can score here through rare domain complexity. |
| Business completeness | 15 | Real user flow, monetization/operation loop, permission/payment/order/content/data lifecycle, production-like scope. |
| Evidence and quality | 15 | Strong repo evidence, docs, tests, Git contribution, CI/config, repeatable validation, clear ownership or module boundaries. |
| Resume readability | 15 | Can become 3-5 strong bullets with mechanism, scope, impact, and interview stories. |
| Interview expansion | 10 | Can support STAR follow-up, tradeoff discussion, failure modes, debugging, and alternative designs. |

Output two scores when metrics or ownership are uncertain:

- `evidence_safe_score`: facts only. Count verified and code-derived metrics; ignore unconfirmed business results.
- `potential_score`: includes clearly labeled assumptions, estimated metric directions, and improvements the user could confirm later.

### 90+ Gate

An evidence-safe score above 90 requires at least one of:

- Verified production/business impact, such as user scale, revenue/GMV, conversion, latency, automation time saved, support cost reduced, or adoption.
- Confirmed personal ownership over a hard module, supported by Git/user facts.
- Exceptionally strong code evidence: multiple high-difficulty highlights, clear architecture depth, tests/quality controls, and code-derived scope metrics that are hard to fake in interviews.

If none of these are present, cap `evidence_safe_score` at 89 even when the project is impressive. The report should explain the cap as a data/ownership/evidence gap, not as a dismissal of project quality.

Common reasons a project stops at 85-89:

- Business impact exists but has no verified number.
- Role boundary is unknown, so wording must stay conservative.
- Code shows features, but less evidence for production operation, tests, monitoring, or failure handling.
- AI/architecture claims are plausible but not fully supported by code.
- The project has many pages/modules but lacks a single standout hard problem.

Use `potential_score` to show what the project could reach after confirmation. Example:

```json
"project_score": {
  "evidence_safe_score": 89,
  "potential_score": 93,
  "score_ceiling_reason": "缺少已确认业务指标和个人 Owner 边界，安全分不宜超过 89；若确认上线规模、效率提升和负责范围，可按 90+ 项目包装。",
  "score_breakdown_100": {
    "technical_depth": 23,
    "ai_or_rarity_signal": 19,
    "business_completeness": 13,
    "evidence_and_quality": 13,
    "resume_readability": 14,
    "interview_expansion": 7
  }
}
```

## AI Application Weighting

When the project is an AI application, AI Agent platform, model-powered workflow, coding assistant, RAG/search assistant, local AI desktop client, or tool-calling system, adjust scoring and ordering:

- Add `+2` to highlights that cover **Agent orchestration, memory, prompt/context injection, tool calling, MCP, RAG/retrieval, evaluation/guardrails, workflow automation, model routing, or long-session AI state**.
- Add `+1` to highlights that support AI experience indirectly, such as streaming rendering, long conversation UI, Markdown rendering, message protocol adaptation, or AI result state management.
- Keep ordinary page delivery, generic forms, CRUD, or marketing/business modules below the AI core unless their technical difficulty is clearly higher.
- In the report order, place AI core highlights before general frontend/backend delivery when their evidence is strong. For example: `记忆/上下文注入`、`Agent 协同/工具调用`、`RAG/检索`、`模型路由/Provider 编排` should usually appear before `普通页面状态`、`支付`、`上传`、`埋点`.
- Do not inflate unsupported AI claims. The bonus only applies when the repository contains code evidence such as prompt/context builders, memory stores, tool registration, MCP config, agent protocol handlers, model routing, stream processors, or tests.
- In desktop AI clients or skill-market repositories, distinguish core product code from bundled skills, vendored templates, generated resources, screenshots, and copied sidecar assets. Do not award AI/Agent bonus for resource packs alone; prefer source directories that participate in runtime flows, tests, stores, IPC, API routes, or product UI.
- When tests are strong, use them to raise `evidence_strength` and close the chain. Do not let test paths outrank runtime source files unless the highlight itself is about testing infrastructure.

Recommended AI-app priority tiers:

1. **Tier A**: Agent orchestration, memory/context, tool/MCP/RAG, model routing, safety/evaluation guardrails.
2. **Tier B**: AI streaming protocol, long-session state machine, incremental Markdown rendering, conversation UI reliability.
3. **Tier C**: AI product workflows such as result pages, form flows, upload, payment, analytics, and general business modules.

## Highlight Categories

### Business/Product Delivery

Look for pages, flows, modules, roles, domain entities, form workflows, order/payment/approval flows, dashboards, growth features, content publishing, search/filter, notification, or admin operations.

Evidence examples:

- `pages/`, `views/`, `routes/`, `controllers/`, `modules/`
- domain words in filenames and routes
- mock data and API schemas
- README feature list

### Architecture and System Design

Look for layered architecture, monorepo boundaries, shared packages, service abstractions, state machines, plugin systems, queues, caches, adapters, SDK wrappers, or module federation.

Evidence examples:

- `packages/`, `apps/`, `libs/`, `services/`
- dependency injection, adapters, repositories
- centralized route/store/API modules
- architecture docs or diagrams

### Core Features

Look for substantial, user-visible modules with state, validation, permissions, data fetching, persistence, or complex UI behavior.

Evidence examples:

- component trees
- API/service calls
- tests around the feature
- related route and state files

### Performance and Reliability

Look for caching, pagination, lazy loading, virtual lists, debouncing, retry, error boundaries, fallback states, loading states, offline support, idempotency, rate limits, background jobs, or monitoring.

Do not claim latency/throughput improvements without measurement. Instead write code-derived wording such as "引入分页和缓存策略，减少大列表一次性渲染压力".

### Engineering Quality

Look for TypeScript types, tests, linting, CI, design system, reusable hooks/components, API normalization, error handling, documentation, scripts, or refactoring.

Evidence examples:

- test files
- `tsconfig`, `eslint`, `vitest`, `jest`, `playwright`
- shared `utils`, `hooks`, `components`, `composables`
- CI files

### Data, AI, Automation

Look for ETL, analytics, charts, recommendation, model calls, prompt templates, vector search, scheduled tasks, scraping, report generation, or workflow automation.

### Security/Auth/Compliance

Look for login, permission, RBAC, token refresh, route guards, encryption, sanitization, audit logs, privacy handling, or payment security.

Only claim security ownership when code evidence is strong.

### Collaboration and Ownership

Use only with Git or user-provided evidence. Signals include commits across modules, feature branches, PR docs, issue references, cross-module changes, tests/docs accompanying code, or reviewer notes.

Avoid "主导" unless commit history/user facts clearly support ownership.

### Resume Merge Handoff

Look for facts that a downstream resume-writing agent can safely reuse:

- Project one-line summary.
- User role or conservative role assumption.
- Role-relevant keywords.
- 3-5 strongest bullets, not an exhaustive feature list.
- Data that needs user confirmation before becoming a resume claim.

## Anti-Generic Highlight Test

A highlight is too generic if it only says:

- Used a framework or common tool.
- Built a module without naming the hard state, edge case, protocol, or abstraction.
- "Supported" a business scenario without explaining what the code changed or prevented.
- Lists many capabilities in one sentence but has no interview story.

Before accepting a highlight, rewrite it through this lens:

```text
业务矛盾 / 技术风险 -> 具体机制 -> 覆盖范围 -> 可验证结果或需确认结果
```

Prefer:

- Request race control, stale response prevention, pagination state boundaries.
- AI streaming protocol parsing, markdown chunk rendering, long-session list virtualization.
- Payment unlock states, order polling, fallback and entitlement gating.
- Structured field mapping, multi-step form orchestration, skip/edit/confirm state transitions.
- Upload permission, OSS signing, media type routing, retry/error exposure.
- Cross-page renderer/composable/request-layer reuse with concrete consumers.

Avoid safe bullets shaped like:

```text
参与某模块开发，封装 A/B/C，支撑 X/Y/Z 场景。
```

That pattern can appear in a project overview, but it is usually too flat for a final resume bullet unless the mechanism and edge case are also named.

When the user explicitly asks for a stronger packaged story, the enhanced bullet may include a plausible product-result direction, but it must stay under confirmation unless the metric or ownership is verified.

## Chinese-First Technical Mechanism Priority

In strict reports, phrase each accepted highlight as a technical capability first, not a business module first. Prefer Chinese technical mechanisms. Keep English only for established terms, protocols, frameworks, abbreviations, or code identifiers that are normally written in English.

Good title patterns:

- `异步请求竞态治理与 stale response 防护`
- `WebSocket 消息协议适配与长会话渲染`
- `流式 Markdown 渲染与打字队列`
- `字段映射驱动的表单流转`
- `请求网关与 API 可观测性`
- `Tauri IPC 子进程管线`
- `MCP 会话级配置隔离`

Weak title patterns:

- `职位检索和筛选`
- `AI 小北聊天`
- `简历上传流程`
- `会员付费功能`
- `Streaming State Controller / rAF Buffer / Orphan Queue`
- `Provider Model Pass-through / Spawn Config Hash`

The body can mention the product scenario, but the title and first clause should expose the professional technical essence. Avoid making every title bilingual; a report should read like a Chinese technical resume, not a glossary. English is valuable when it names the actual technology (`WebSocket`, `CLI`, `SSE`, `MCP`, `SQLite FTS`, `Tauri`, `Rust`, `stream-json`), not when it is only a decorative translation.
