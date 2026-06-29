# Structured Analysis Schema

Create `project_resume_analysis.json` after reading the evidence and targeted source files. The render script consumes this file and produces the HTML report plus prompt pack.

## Minimal Command

Validate before rendering:

```bash
python3 <skill_dir>/scripts/validate_analysis.py \
  --analysis /path/to/project_resume_analysis.json \
  --evidence /path/to/project_evidence.json \
  --strict
```

Render with strict validation:

```bash
python3 <skill_dir>/scripts/render_resume_report.py \
  --evidence /path/to/project_evidence.json \
  --analysis /path/to/project_resume_analysis.json \
  --output /path/to/project-to-resume-report.html \
  --prompt-output /path/to/resume-project-pitch.txt \
  --strict
```

If `--analysis` is omitted, the renderer creates an evidence-only draft report. Use that only for debugging, not as the final user deliverable.

## Required Shape

```json
{
  "project_name": "项目名称",
  "summary": "一句话说明项目解决什么问题、服务什么用户或业务场景。",
  "target_role": "前端开发 / 后端开发 / 全栈 / AI 工程师 / 测试等",
  "readiness": "整体判断，例如：可直接整理为简历素材，仍需确认业务指标",
  "role_assumption": "用户角色边界。未知时写：未确认，默认使用保守表述。",
  "disclosure_assumption": "公开边界。未知时写：未确认，不暴露内部指标、客户名和敏感细节。",
  "keywords": ["TypeScript", "Vue", "权限体系"],
  "project_score": {
    "evidence_safe_score": 89,
    "potential_score": 93,
    "score_mode": "evidence_safe_and_potential",
    "score_breakdown_100": {
      "technical_depth": 23,
      "ai_or_rarity_signal": 19,
      "business_completeness": 13,
      "evidence_and_quality": 13,
      "resume_readability": 14,
      "interview_expansion": 7
    },
    "score_rationale": "代码证据显示技术深度和简历可读性强，但业务指标与个人 Owner 边界仍需确认。",
    "score_ceiling_reason": "缺少已确认业务指标或上线规模，evidence-safe score 不宜超过 89。"
  },
  "metric_strategy": {
    "verified_metrics": [
      {"metric": "12 个页面", "source": "pages.json", "usable_in_safe_bullet": true}
    ],
    "code_derived_metrics": [
      {"metric": "20+ 组件", "source": "src/components", "usable_in_safe_bullet": true}
    ],
    "estimated_metric_suggestions": [
      {
        "claim_direction": "效率提升",
        "basis": "多页面复用字段映射表单和统一请求层。",
        "placeholder": "将同类页面开发周期从 X 天缩短至 Y 天",
        "confidence": "medium",
        "confirmation_needed": "确认历史开发周期和复用前后差异"
      }
    ],
    "metrics_not_to_claim": ["用户量", "营收", "转化率", "线上延迟降低百分比"]
  },
  "facts": [
    {"label": "业务流程", "value": ["用户登录", "订单管理", "审批流"]},
    {"label": "核心模块", "value": ["src/pages/order", "src/services/order.ts"]}
  ],
  "highlights": [
    {
      "title": "后台权限体系建设",
      "category": "权限与安全",
      "score": 13,
      "score_breakdown": {
        "business_relevance": 3,
        "technical_difficulty": 2,
        "evidence_strength": 3,
        "resume_readability": 2,
        "differentiation": 1,
        "handoff_readiness": 2,
        "ai_application_bonus": 0
      },
      "score_rationale": "权限链路有明确代码证据和简历表达价值，但不属于 AI 应用核心能力。",
      "risk": "safe",
      "readiness": "direct",
      "evidence": ["src/router/guard.ts", "src/stores/user.ts"],
      "safe_bullet": "负责后台权限与菜单配置模块开发，基于路由守卫、菜单配置和登录态校验封装访问控制链路，支撑多角色后台页面访问控制。",
      "enhanced_bullet": "负责后台权限与菜单配置模块开发，覆盖 X 类角色和 Y+ 页面入口，将新增角色配置时间缩短约 Z%。",
      "why": "能体现业务权限抽象、前端架构和安全意识。",
      "interview": {
        "situation": "后台页面入口多、不同角色权限不同。",
        "task": "负责权限校验和菜单渲染链路。",
        "action": "抽象路由守卫、登录态刷新、菜单配置和异常兜底。",
        "result": "代码层面支持多角色页面访问控制；业务指标需用户确认。",
        "tradeoff": "前端控制提升体验，但关键权限仍需后端校验。"
      },
      "data_to_confirm": ["角色数量", "页面数量", "配置效率变化"],
      "usage": "direct_paste"
    }
  ],
  "safe_bullets": [],
  "confirmation_items": [],
  "interview_stories": [],
  "prompt_pack": ""
}
```

## Golden Examples

Use these as quality bars before writing a new analysis:

- `examples/vue-admin-golden-analysis.json`: frontend/admin system example with permissions, route guards, table filtering, and reusable components.
- `examples/python-api-golden-analysis.json`: backend/Python automation example with parsing, validation, reliability, and workflow automation.
- `examples/node-agent-golden-analysis.json`: Node backend + AI Agent example with tool calling, RAG, model orchestration, and evaluation metrics.

All examples should pass:

```bash
python3 <skill_dir>/scripts/validate_analysis.py \
  --analysis <example-json> \
  --strict
```

Each golden example also has a paired evidence fixture under `examples/fixtures/`. Use this end-to-end check before publishing changes:

```bash
python3 <skill_dir>/scripts/check_golden_fixtures.py
```

The fixture check runs `render_resume_report.py --strict`, so it exercises evidence-aware path validation and HTML/prompt rendering together.

## Field Rules

- `risk`: use `safe`, `needs_confirmation`, or `risky`.
- `readiness`: use `direct`, `rewrite`, `confirm`, or `idea`.
- `score`: required for serious report highlights; use the rubric score after any AI application bonus.
- `score_breakdown`: optional but recommended for strict reports; include the six base dimensions and `ai_application_bonus` when relevant.
- `score_rationale`: optional but recommended; one concise Chinese sentence explaining why this highlight ranks high or low.
- `project_score`: optional, but required when the user asks for comparison, "含金量", "打分", or "为什么没上 90".
- `project_score.evidence_safe_score`: 0-100 score using only verified and code-derived evidence.
- `project_score.potential_score`: 0-100 score after clearly labeled assumptions or estimated metric directions are confirmed.
- `project_score.score_breakdown_100`: use `technical_depth`, `ai_or_rarity_signal`, `business_completeness`, `evidence_and_quality`, `resume_readability`, and `interview_expansion`.
- `project_score.score_ceiling_reason`: required when evidence-safe score is below 90 but potential score is 90+.
- `metric_strategy`: optional, but recommended for strict reports and any quantified bullet request.
- `metric_strategy.verified_metrics` and `metric_strategy.code_derived_metrics`: may be used in safe bullets when sources are listed.
- `metric_strategy.estimated_metric_suggestions`: must stay under enhanced/confirmation sections and use placeholders or ranges, not factual claims.
- `metric_strategy.metrics_not_to_claim`: list metrics that would overstate the project unless the user provides proof.
- `evidence`: required for every highlight.
- `safe_bullet`: must be conservative and evidence-backed.
- `interview`: must include `situation`, `task`, `action`, `result`, and `tradeoff`.
- `enhanced_bullet`: may include `X/Y/Z` placeholders or suggested metrics, but must remain under confirmation sections.
- `facts`: include business flows, module map, API/page map, data flow, integration points, quality signals, and contribution boundary when known.
- Evidence fixtures and generated evidence should include `evidence_paths_index` for complete strict path validation. `file_index` may be truncated for readability.

## Highlight Ordering

The renderer sorts highlights by risk, score, AI-priority, readiness, and original order. For AI application projects, Agent orchestration, memory/context, tool/MCP/RAG, model routing, evaluation/guardrail, and long-session AI state highlights should receive higher `score` and appear before ordinary page/business modules when evidence is strong.

## Business Flow Notes

Before writing highlights, capture at least one of these maps when evidence allows:

- Frontend: page -> component -> service/API -> state/store -> user scenario.
- Backend: route/controller -> service -> model/repository -> external dependency -> business scenario.
- Full-stack: frontend flow -> API endpoint -> backend service -> data persistence.
- AI/data project: input -> processing/prompt/model -> output -> evaluation/guardrail.

Use these maps to avoid generic bullets like "负责项目开发".
