# Target-Role-First STAR Scoring

Use this reference on every project-to-resume invocation. It prevents the skill from treating one previously selected role—including Agent development—as a permanent default.

## Mandatory Role Gate

Before repository analysis, always ask the current application direction:

> 这次准备投递什么岗位方向？请给出岗位名称或 3-5 个能力关键词。

- If the same user message already says the direction, use a confirmation-form question such as `本次按 Agent 应用开发方向筛选和评分，可以吗？` and continue provisionally with that stated direction; revise it if the user corrects you.
- Do not inherit the role from an earlier run, a folder name, repository keywords, or an existing report.
- If the user refuses to choose, label the output `通用工程方向` and explain that role-fit ranking is provisional.

## Build a Role Signal Map

Convert the chosen direction into 3-6 observable signals before ranking. Examples are illustrative, not defaults:

| Direction | Observable signals |
|---|---|
| Agent application/platform | runtime loop, tool calling, context/memory, artifact/protocol design, HITL, evaluation/guardrails, deterministic replay |
| Backend/platform | API/domain boundaries, queues/cache, consistency/idempotency, reliability, observability, performance |
| Frontend/engineering | state architecture, component abstraction, interaction complexity, performance, accessibility, build/tooling |
| Data/automation | ingestion, schema/data quality, orchestration, lineage, reproducibility, monitoring |
| Test/quality | risk modeling, automation layers, fixtures, determinism, coverage strategy, failure localization |

Each signal needs a repository evidence pattern. Generic technology presence is not enough.

## Three Mandatory Scoring Rounds

Score each candidate from 0-100 in all three rounds. Keep the rationale concise and evidence-linked.

### Round 1: Evidence Safety

Question: can the statement be defended from code, docs, tests, Git, or user-confirmed facts?

- 90-100: implementation plus closure/verification evidence agree.
- 75-89: strong implementation evidence, but ownership, production use, or metrics are unconfirmed.
- 60-74: one-sided or indirect evidence; keep as backup or `needs_confirmation`.
- Below 60: reject from direct-paste bullets.

Hard fail: invented metrics, ownership, scale, business impact, or production claims.

### Round 2: Target-Role Relevance

Question: does this highlight demonstrate one or more signals from the current role map better than generic delivery work?

- 90-100: core differentiating competency for the target role.
- 75-89: clearly relevant supporting competency.
- 60-74: adjacent/general engineering value.
- Below 60: omit unless needed for project completeness.

This score is dynamic. A Redis task loop may rank highly for backend/platform, while an Agent runtime/tool contract may rank highly for Agent development. Neither ranking should leak into the next invocation.

### Round 3: STAR and Interview Defensibility

Question: can the candidate explain a concrete Situation, Task, Action, Result, and tradeoff under follow-up?

- 90-100: all STAR fields are concrete; Action names the mechanism; Result is evidence-safe; failure boundary and verification are available.
- 75-89: strong Action and Result, but production effect or ownership still needs confirmation.
- 60-74: technology list or responsibility language dominates; rewrite before use.
- Below 60: reject from direct-paste bullets.

Hard fail: Result merely repeats the Action, or the story depends on unverifiable business impact.

## Final Ranking

Use the geometric idea of a weakest-link gate rather than averaging away a failure:

```text
eligible = evidence_safety >= 75 and role_relevance >= 75 and star_defensibility >= 75
final_score = round(0.40 * evidence_safety + 0.35 * role_relevance + 0.25 * star_defensibility)
```

For direct-paste bullets, all hard fails must be false. A candidate with 98 role relevance but 55 evidence safety is not safe.

## STAR Compression for Resume Bullets

The expanded interview story keeps all fields. The resume bullet compresses them:

```text
Situation/Task cue + Action with mechanism + evidence-safe Result
```

Good pattern:

> 针对多站点登录流程难以稳定复用的问题，设计带身份匹配、语义校验和状态化回放的 Artifact 协议，将探索结果沉淀为执行器可消费、可诊断的机器契约。

Weak pattern:

> 负责 Agent、Redis、Playwright 和 Schema 相关开发。

The good pattern exposes the problem, specific Action, and code-implied Result without claiming unsupported metrics.

## Output Contract

For standard/strict outputs, include:

- `target_role`: confirmed current direction.
- `role_signal_map`: selected signals and supporting evidence.
- `scoring_rounds`: round name, score, decision, and short rationale.
- `highlights[].interview`: explicit `situation`, `task`, `action`, `result`, and `tradeoff`.
- `highlights[].safe_bullet`: exact direct-paste compressed STAR wording.

If the current renderer does not have dedicated fields, expose the role map and scoring rounds through `facts` so they remain visible in the HTML report.

## Feedback Loop for Skill Maintenance

After a real-project run, record which candidates failed and why:

1. Evidence failure: add or tighten evidence/validation rules.
2. Role-fit failure: adjust only the role signal example, never the global default.
3. STAR failure: refine bullet compression or interview prompts.
4. Repeated false positive across at least two repositories: add a golden/adversarial fixture before changing scoring behavior.

Do not silently turn one project's role calibration into a universal skill rule.
