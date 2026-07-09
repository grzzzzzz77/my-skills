# Highlight Logic Chain Details

Use this reference when the user wants each resume highlight to be easier to understand, explain, or jump into from an HTML report. The goal is not a longer bullet. The goal is a closed-loop explanation that lets a beginner understand why the highlight exists and how the code evidence supports it.

## Purpose

Every strong highlight should answer this chain:

```text
业务/用户问题 -> 触发入口 -> 核心技术处理 -> 输出/反馈 -> 可验证结果 -> 简历表达边界
```

This prevents generic bullets such as "负责模块开发" by forcing each highlight to explain:

- What problem or user action starts the flow.
- Which code files carry the flow.
- What state, data, API, model, job, or UI transition happens in order.
- What the user/system receives at the end.
- What can be safely claimed and what still needs confirmation.

## Required Highlight Fields

For standard and strict_report analyses, add these fields to every final highlight:

```json
{
  "detail_anchor": "permission-access-control",
  "logic_chain": {
    "plain_summary": "用一句小白能懂的话说明这个亮点是什么。",
    "beginner_context": "解释项目里的相关角色、页面、服务或业务对象。",
    "problem": "原问题、风险或低效点。",
    "trigger": "谁在什么场景下触发这条链路。",
    "flow_steps": [
      {
        "step": "入口",
        "explanation": "页面、接口、任务或命令如何进入流程。",
        "evidence": ["src/router/guard.ts"]
      },
      {
        "step": "处理",
        "explanation": "核心模块如何校验、转换、编排或兜底。",
        "evidence": ["src/stores/user.ts", "src/services/auth.ts"]
      },
      {
        "step": "输出",
        "explanation": "用户、页面、服务或下游系统得到什么结果。",
        "evidence": ["src/router/guard.ts"]
      }
    ],
    "closure": "这条链路如何闭环：结果、反馈、异常处理或后续确认点。",
    "difficulty": "复杂点：多状态、多角色、跨系统、性能、可靠性、AI 评估等。",
    "resume_connection": "为什么安全版 bullet 可以这么写，增强版还差什么证据。",
    "limits": "不能直接声称的指标、所有权或生产影响。"
  }
}
```

## Writing Rules

- Keep `detail_anchor` stable, lowercase, URL-safe, and unique within the report.
- Write the logic chain for a smart beginner, not for the original developer.
- Prefer 3-6 `flow_steps`. Fewer than 3 usually means the highlight is not a chain yet.
- Each step should include evidence when possible. Use file paths, route names, tests, configs, docs, or code-derived counts.
- Put runtime implementation evidence first. Tests are excellent for proving the chain closes, but they should usually appear in the final verification/closure step rather than replacing the actual route, store, service, adapter, controller, or prompt builder.
- The chain must close. Do not stop at "调用接口"; explain the returned state, UI feedback, persisted result, generated file, model response, test assertion, or manual confirmation point.
- Separate code-verified closure from user-confirmed business result. Example: "代码层面完成异常拦截；减少人工返工比例需确认。"
- Do not expose sensitive customer names, private endpoints, tokens, production data, or internal business numbers.

## Good Shape

```text
一句话：这个亮点是在说“用户登录后，系统能根据角色判断能进哪些后台页面”。
背景：后台不是所有人都能看到全部菜单，运营、客服、管理员入口不同。
闭环：登录态进入路由守卫 -> 读取用户权限 -> 生成菜单和访问判断 -> 未授权时跳转/提示 -> 页面访问被控制。
证据：router guard、user store、auth service。
简历边界：可以安全写“封装访问控制链路”；角色数量、页面数量、配置效率需要确认后再增强。
```

Avoid:

```text
实现了权限模块，提升系统安全性。
```

That does not explain the trigger, process, output, or evidence.
