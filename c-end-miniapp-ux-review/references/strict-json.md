# 严格 JSON 模式

当用户要求机器可读评审、自动门禁或可回归对比时，输出一个 JSON 文件并运行 `scripts/validate_review.py`。JSON 使用 UTF-8。

## 顶层字段

```json
{
  "meta": {
    "review_id": "review-demo-v1",
    "mode": "spec_only",
    "round": 1
  },
  "scope": {
    "surface": "预约小程序",
    "target_user": "首次预约用户",
    "context": "移动端碎片时间",
    "user_goal": "完成预约并获得确认",
    "success_outcome": "出现可保存的预约凭证",
    "start": "首页入口",
    "end": "预约成功",
    "non_goals": ["后台排班"]
  },
  "evidence": [
    {
      "evidence_id": "E1",
      "source": "PRD 2.1",
      "kind": "prd",
      "grade": "specified",
      "limitations": "未提供交互原型"
    }
  ],
  "flow_steps": [
    {
      "step_id": "S1",
      "order": 1,
      "name": "选择服务",
      "user_intent": "找到合适服务",
      "user_action": "点击服务卡片",
      "system_response": "进入详情并展示可预约时间",
      "next_or_recovery": "返回保留筛选条件",
      "evidence_refs": ["E1"],
      "health": "risk"
    }
  ],
  "state_matrix": [
    {
      "state": "loading",
      "applicability": "applicable",
      "trigger": "读取可预约时间",
      "visible_feedback": "显示骨架与加载说明",
      "allowed_actions": ["返回"],
      "recovery": "失败后重试并保留已选服务",
      "evidence_refs": ["E1"]
    }
  ],
  "findings": [
    {
      "finding_id": "F1",
      "step_ids": ["S1"],
      "layer": "flow",
      "severity": "P1",
      "confidence": "high",
      "evidence_grade": "specified",
      "evidence_refs": ["E1"],
      "problem": "加载失败后丢失已选服务",
      "user_impact": "用户必须重新选择并可能放弃",
      "recommendation": "保留选择并提供原地重试",
      "validation": "断网后恢复网络，重试仍保留已选服务"
    }
  ],
  "prd_updates": [
    {
      "update_id": "R1",
      "type": "acceptance_criteria",
      "text": "Given 已选服务且请求失败，When 用户重试，Then 系统保留服务并重新加载时段",
      "finding_refs": ["F1"]
    }
  ],
  "validation_plan": [
    {
      "validation_id": "V1",
      "method": "interactive_prototype",
      "target": "F1",
      "pass_condition": "失败重试不丢失选择"
    }
  ],
  "limitations": ["未验证真实网络耗时和读屏行为"]
}
```

## 约束

- `mode`：`spec_only`、`static_artifact`、`interactive_flow`。
- `grade/evidence_grade`：`observed`、`specified`、`inferred`、`unknown`。
- `severity`：`P0`、`P1`、`P2`、`Opportunity`。
- `confidence`：`high`、`medium`、`low`。
- `health`：`healthy`、`risk`、`blocked`、`unknown`。
- `applicability`：`applicable` 或 `not_applicable`。后者必须给出非空 `reason`。
- `evidence_refs`、`step_ids`、`finding_refs` 必须引用已存在的 ID。
- 所有 P0/P1 必须有非空 evidence_refs、recommendation 和 validation。
- 状态矩阵必须逐项包含核心状态；不适用的状态用 `not_applicable + reason`，不要删除。
- 严格验证器按结构、证据引用、链路、状态、问题闭环、PRD 回写和验证计划计算报告质量分。
