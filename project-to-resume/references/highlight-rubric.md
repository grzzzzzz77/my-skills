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

## Technical Term Priority

In strict reports, phrase each accepted highlight as a technical capability first, not a business module first.

Good title patterns:

- `Stale Response 防护与列表状态一致性`
- `WebSocket 消息协议适配与长会话渲染`
- `Incremental Markdown Renderer`
- `Schema-driven Form Flow`
- `Request Gateway 与 API Telemetry`

Weak title patterns:

- `职位检索和筛选`
- `AI 小北聊天`
- `简历上传流程`
- `会员付费功能`

The body can mention the product scenario, but the title and first clause should expose the professional technical essence.
