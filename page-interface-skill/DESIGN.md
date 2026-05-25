# page-interface-skill v4 设计文档

## 目标

把 `page-interface-skill` 从“能生成页面接口映射”升级为“稳定、通用、可审查的联调地图生成器”。

v4 的重点不是更像某一个业务页面，而是让任何页面分析任务都先经过统一建模，再生成可视化交付物：

1. 页面模块模型
2. 角色/状态矩阵
3. API 清单
4. 业务流程节点
5. 字段溯源 details
6. 风险与待确认点
7. 可点击 HTML 与标注图

## v3 暴露的问题

以复杂移动端页面为例，v3 容易产生这些问题：

- 红框坐标靠手工估算，和实际模块不稳定对齐。
- 页面原型太像“示意图”，却没有明确说明哪些来自真实布局、哪些是抽象结构。
- 流程节点缺少角色/状态维度，复杂功能会变成一串模糊步骤。
- 字段表堆在右侧，缺少“模块结论”和“接口总览”。
- 风险点隐藏在明细里，不利于产品、QA、后端快速发现联调问题。
- schema 没有记录热点定位策略，后续无法判断红框可信度。

## 会话无关设计目标

v4 报告必须能在一个全新会话里稳定复现同等质量。判断标准不是“当前对话解释后能看懂”，而是只打开 `flowSpec.json` 和 `flow.html`，也能看懂页面、接口、字段和风险。

因此生成逻辑要把布局、字段溯源、流程/模块联动、质量校验写成默认契约：

- 左侧默认是紧凑流程轴，不是模块卡片副本。
- 中间默认是模块结构卡片，不承载完整流程说明。
- 右侧默认是字段溯源卡片，不使用窄表格。
- 所有非直接响应字段都必须在 `traceChain` 里追到依赖来源或明确写“无接口来源”。
- 所有人工判断必须进入 `pendingQuestions` 或 `qualityNotes`，不能只留在聊天上下文。

## v4 设计原则

### 1. 先建模再生成

每次生成前必须先得到：

- `roleStateMatrix`
- `apiInventory`
- `modules`
- `flows`
- `details`
- `pendingQuestions`

HTML 只是模型的呈现层，不应在生成 HTML 时临时拼逻辑。

模型必须自包含。不要依赖用户和助手当前对话里的解释来补足报告含义；下一次单独拿 `flowSpec.json` 和 HTML 打开，也应该能看懂字段来源、计算逻辑和风险点。

### 2. 热点不再默认使用手写坐标

热点定位策略分级：

1. `screenshot-measured`：真实截图或 DOM 测量，可信度最高。
2. `generated-dom`：静态原型中模块容器自动生成，可信。
3. `module-card`：结构化模块卡片，不伪装真实页面。
4. `structure-row`：表格/列表结构行。
5. `manual-low-confidence`：低可信手工坐标，只能作为最后兜底，并必须写入质量说明。

默认禁止凭感觉给手机原型写绝对红框坐标。

### 3. 无真实截图时改用结构图

无截图、无法运行页面、无法测量 DOM 时，优先生成：

- 页面模块结构图
- 手机宽度的模块卡片图
- 流程 + 模块 + 字段联动图

而不是假装 1:1 还原真实 UI。

### 4. 首页必须回答三个问题

`flow.html` 首屏必须清楚回答：

1. 这个功能有哪些页面/状态？
2. 这个功能调用哪些接口？
3. 当前最重要的待确认点是什么？

字段表是第二层信息，不应该挤占首屏结论。

### 5. 面向三类读者

- 产品：看流程、状态、风险。
- QA：看触发方式、页面状态、空态/失败分支、验收点。
- 研发：看接口、字段、normalize、证据行号。

交互 HTML 需要用 Tab 或面板把三类信息分层。

### 6. computed/local/static 不能当成结论

字段表里如果某个 UI 字段不是后端直接返回，不能只显示 `computed/local/static`。这几个词只是来源类型，不是溯源结果。

必须补齐：

- `displayLabel`：中文展示名、页面文案或业务含义，优先来自 template 文案；没有直接文案时写产品能看懂的中文名。
- `sourceType`：字段来源类型。
- `apiField`：直连 API 字段，没有则写 `-`。
- `frontendLogic`：前端如何生成该值，包括 computed、normalize、Map 映射、列表分组、日期计算、静态配置。
- `traceChain`：字段溯源链路，按 UI -> 页面状态/computed -> service/normalize -> API 字段 -> 证据的顺序展示。
- `evidence`：源码行号。

合格示例：

```txt
身份标题 | roleView.title | computed | - | roleViewMap[activeRole] 选择身份标题 | index.vue:168-229
累计收益 | distributionData.balance | response+normalize | totalIncomeAmount | normalizeWorkspace 后 formatDistributionAmount | distribution.js:176-181
团队直属大使分组 | register.teamAmbassadors | computed | records[].promoterUid | teamUsers 按 promoterUid/promoterAgentNo 分组 | register-detail.vue:137-153
```

不合格示例：

```txt
roleView.title | computed/local/static
distributionData.balance | incomeSummary.totalIncomeAmount
```

computed 字段的最低合格展示应包含链路，例如：

```txt
身份标题
UI roleView.title
-> computed roleView = roleViewMap[distributionData.role]
-> distributionData 来自 APIgetDistributionWorkspace()
-> normalizeWorkspace 将 identityStatus.identityType 归一化为 role
-> API workspace.identityStatus.identityType
```

## 推荐 flowSpec

```json
{
  "featureName": "",
  "sourceFiles": [],
  "apiDocs": [],
  "roles": [],
  "roleStateMatrix": [
    {
      "role": "",
      "state": "",
      "entry": "",
      "screens": [],
      "defaultApis": [],
      "visibleModules": [],
      "disabledModules": [],
      "next": []
    }
  ],
  "apiInventory": [
    {
      "id": "",
      "method": "POST",
      "url": "",
      "purpose": "",
      "triggers": [],
      "requestFields": [],
      "responseFields": [],
      "usedByModules": [],
      "evidence": []
    }
  ],
  "flows": [],
  "screens": [],
  "modules": [],
  "details": [],
  "pendingQuestions": [],
  "qualityNotes": []
}
```

## HTML 信息架构

建议布局：

```txt
┌────────────────────────────────────────────────────────────┐
│ 顶部摘要：页面/状态、接口清单、待确认点                    │
├───────────────┬───────────────────────────┬────────────────┤
│ 紧凑流程轴/矩阵 │ 页面模块结构图/原型         │ 模块数据来源     │
│ API 清单       │ 可点击模块卡片/热点         │ 字段/证据/风险   │
└───────────────┴───────────────────────────┴────────────────┘
```

必要能力：

- 点击流程节点，并让中间结构图滚动到对应模块。
- 点击模块卡片或热点，并让左侧流程同步到对应流程；没有对应流程时取消流程高亮。
- 左侧流程区使用紧凑流程轴、stepper 或导航轨，不使用与中间模块相同的大卡片视觉。
- 左侧流程节点只表达步骤名、页面/状态、触发方式和对应模块，不重复模块摘要、字段详情、风险详情或完整接口清单。
- 切换角色、状态、tab、弹窗状态。
- 右侧先展示模块结论，再展示字段表。
- 右侧窄面板展示字段溯源时使用字段卡片，而不是 6 列以上表格；表格只能放在宽区域或单独 Tab 中。
- 左侧导航、中间结构图、右侧详情面板应各自独立滚动；外层页面允许保留总滚动条作为小屏兜底。独立滚动是主路径，整页滚动是兜底。
- 风险面板独立可见。

## 可视化选择规则

```txt
有真实截图 -> 截图标注
可运行页面 -> 浏览器/小程序截图或 DOM 测量后标注
只有源码 -> 模块结构图 + 静态原型
源码结构复杂且样式难还原 -> 模块结构图，不强行手机仿真
```

## 默认报告骨架

任何新任务默认生成以下信息架构，除非用户明确要求换一种展示：

```txt
Top summary：页面/状态、核心接口、待确认风险
Left rail：紧凑流程轴，只展示步骤级信息
Center map：页面模块结构图，只展示模块级信息
Right detail：接口、字段、computed/normalize、证据、风险
```

这四块必须从同一个 `flowSpec` 渲染，不能在 HTML 字符串里临时写一套解释。

## 质量检查清单

每次交付前必须确认：

- `flowSpec` 包含 layoutContract、traceabilityContract、qualityGates，保证新会话也能按同一标准生成。
- `flow.html` 点击流程和模块不会报错。
- 流程选中态和模块高亮态一致，不出现左侧流程 A、中间模块 B 的错位。
- 左侧流程区是紧凑时间线/导航轨，中间才是模块卡片；两栏视觉形态不同。
- 左侧流程列表与中间模块卡信息分工清楚，无大段重复信息。
- 内嵌 JS 通过 `node --check`。
- 每个热点都有 detail。
- 每个 detail 有证据行号。
- 每个接口至少说明用途和触发点。
- 每个字段有中文 `displayLabel`。
- 每个字段有 `traceChain`，computed/local/static 字段的链路能追到依赖来源或明确说明无接口来源。
- 右侧窄面板字段区使用字段卡片，不使用 6 列以上宽表格。
- 左侧列表、中间结构图、右侧详情面板分别可独立滚动；外层滚动只作为兜底。
- 待确认点在首页摘要可见。
- 没有真实截图时明确标注“非真机截图”。
- 没有使用无依据的漂浮红框。
- `rg` 能搜索到关键接口、关键字段、关键风险。

建议自动校验：

```txt
node --check 生成脚本
解析 flow.html 内嵌 JS
读取 flowSpec.json，断言 fieldTraces 全部存在 displayLabel 和 traceChain
rg "field-trace-card|traceChain|基于源码生成，非真机截图|核心接口|待确认"
```

## 不做什么

- 不生成只靠视觉但没有字段证据的页面。
- 不复制整段后端文档。
- 不把所有字段塞进一个超长表格。
- 不为了“像手机截图”牺牲清晰度。
- 不把业务特定规则写死进 skill；具体业务只进入本次生成的 flowSpec。
