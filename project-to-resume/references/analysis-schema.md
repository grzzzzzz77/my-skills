# Structured Analysis Schema

Create `project_resume_analysis.json` after reading the evidence and targeted source files. The render script consumes this file and produces the HTML report plus prompt pack.

## Minimal Command

Validate before rendering:

```bash
python3 <skill_dir>/scripts/validate_analysis.py \
  --analysis /path/to/project_resume_analysis.json \
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
  "facts": [
    {"label": "业务流程", "value": ["用户登录", "订单管理", "审批流"]},
    {"label": "核心模块", "value": ["src/pages/order", "src/services/order.ts"]}
  ],
  "highlights": [
    {
      "title": "后台权限体系建设",
      "category": "权限与安全",
      "score": 13,
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

Both examples should pass:

```bash
python3 <skill_dir>/scripts/validate_analysis.py \
  --analysis <example-json> \
  --strict
```

## Field Rules

- `risk`: use `safe`, `needs_confirmation`, or `risky`.
- `readiness`: use `direct`, `rewrite`, `confirm`, or `idea`.
- `evidence`: required for every highlight.
- `safe_bullet`: must be conservative and evidence-backed.
- `interview`: must include `situation`, `task`, `action`, `result`, and `tradeoff`.
- `enhanced_bullet`: may include `X/Y/Z` placeholders or suggested metrics, but must remain under confirmation sections.
- `facts`: include business flows, module map, API/page map, data flow, integration points, quality signals, and contribution boundary when known.

## Business Flow Notes

Before writing highlights, capture at least one of these maps when evidence allows:

- Frontend: page -> component -> service/API -> state/store -> user scenario.
- Backend: route/controller -> service -> model/repository -> external dependency -> business scenario.
- Full-stack: frontend flow -> API endpoint -> backend service -> data persistence.
- AI/data project: input -> processing/prompt/model -> output -> evaluation/guardrail.

Use these maps to avoid generic bullets like "负责项目开发".
