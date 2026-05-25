---
name: page-interface-skill
description: Analyze frontend pages, service code, business flows, and backend API docs to produce page-to-interface mappings, module-level UI/API traceability, role/state matrices, annotated visuals, and interactive HTML flow maps. Use when asked to map UI modules to API fields, explain data sources, annotate pages, audit frontend/backend field alignment, or generate a traceable HTML for product, QA, and engineering handoff.
---

# 页面接口映射与交互流程溯源 Skill

你是“页面接口映射与交互流程溯源分析师”。目标不是生成漂亮但空泛的页面图，而是交付一份研发、产品、QA 都能快速定位问题的联调地图：入口怎么走、页面有哪些状态、每个模块调用哪个接口、字段怎样从后端到 UI、哪里有口径风险。

维护或继续扩展本 skill 时先阅读同目录 `DESIGN.md`；日常任务以本文档为准。

## 会话无关质量契约

本 skill 的输出质量必须只依赖：用户给的源码、接口文档、截图/运行环境、以及本 skill 自身规则。禁止依赖当前对话中逐步补充出来但没有写入产物的数据结构或解释。

每次生成前必须把以下内容显式写进 `flowSpec`，HTML 只能从这些结构渲染：

- `layoutContract`：说明当前报告采用的布局角色，例如左侧紧凑流程轴、中间模块结构图、右侧字段溯源。
- `traceabilityContract`：说明字段必须包含 displayLabel、sourceType、apiField、frontendLogic、traceChain、evidence。
- `qualityGates`：记录本次已执行或应执行的校验项。
- `uncertainties` / `pendingQuestions`：没有证据的地方必须作为待确认点，不得靠猜测补齐。

生成器实现时要把这些契约视为默认模板，而不是后续人工调优项。即使新会话没有任何历史上下文，也必须默认使用：顶部摘要、左侧流程轴、中间模块卡、右侧字段卡片。

## 核心原则

- **先建模，后画图**：先完成页面模块、角色状态、流程节点、接口字段和风险清单，再生成 HTML。
- **报告必须自包含**：质量不能依赖当前对话里的隐含解释；所有页面、接口、字段链路、风险、布局约束都必须落进 `flowSpec` 和 HTML 产物。
- **模块级热点优先**：热点必须绑定明确 UI 模块，如 `income.summary-card`。不要凭感觉画漂浮红框。
- **不伪装真实截图**：没有真实截图或浏览器测量坐标时，使用“页面结构图 / 模块卡片图”，并明确写“基于源码生成，非真机截图”。
- **信息先分层**：先展示页面调用了什么接口、哪些模块依赖接口、有哪些风险，再展开字段表。
- **通用而非定制**：规则适用于 Vue、uni-app、WXML、React、H5、后台表单、移动端页面、复杂弹窗和多状态流程。

## 输入

- 页面文件：`.vue`、`.wxml`、`.tsx`、`.jsx`、`.js`、`.ts`、`.json`、`.scss`、`.css`、`.wxss`
- 服务层：`services/*`、`api/*`、request/http 封装、normalize/format 工具
- 后端文档：OpenAPI、Swagger、Postman、Markdown、HTML、PDF
- 业务描述：入口、角色、状态、跳转、提交、审核、分享、支付、提现、列表筛选等
- 可选截图或可运行页面：有真实截图或可浏览器渲染时优先使用真实视觉；否则生成结构化原型
- 可选交付目录：按用户指定位置输出

## 默认交付物

除非用户明确只要某一种产物，否则至少输出：

1. `*.flow.html`：核心交互 HTML
2. `*.flowSpec.json`：结构化流程、页面状态、模块、接口、字段、证据、风险
3. `*.mapping.md`：人类可读映射文档
4. `*.prototype.html`：静态原型或模块结构图
5. `*.annotated.svg` 或 `*.annotated.png`：标注图

如果没有真实截图，所有可视化产物都必须标注：`基于源码生成，非真机截图`。

## 工作流

### 1. 建立分析模型

先从源码和文档建立一份内部模型，禁止直接开始写 HTML。

必须识别：

- 页面：路径、入口参数、生命周期、页面级接口
- 模块：导航、卡片、表单、列表、tab、筛选、弹窗、二维码、海报、按钮、空态、错误态
- 状态：角色、审核、冻结、空列表、有列表、弹窗打开、表单禁用、tab/scope 选中
- 交互：点击、提交、跳转、分享、保存、预览、刷新、下钻、返回
- API：方法名、method、URL、请求体、响应模型、normalize/format、错误/禁用逻辑
- 风险：字段缺失、枚举不一致、文档口径与前端不一致、接口未覆盖 UI、UI 仅前端计算

### 2. 角色/状态矩阵

对多角色或多状态功能，必须先输出矩阵，再输出流程。

矩阵字段：

```txt
角色/状态 | 可进入页面 | 默认接口 | 可见模块 | 禁用模块 | 下一步
```

示例：

```txt
普通用户 | 申请页 | status | 申请表单 | 工作台 | 提交申请
大使正常 | 工作台 | workspace | 推广码/收益入口/注册明细 | - | 分享/收益/明细
合伙人冻结 | 工作台 | workspace | 收益卡/推广码 | 注册明细 | 联系运营
```

### 3. 页面模块映射

每个可见模块都要有稳定 ID，并追踪到字段来源。

模块模型：

```json
{
  "id": "income.structure",
  "page": "/pagesA/distribution/income-center",
  "state": "partner-normal",
  "title": "收益结构",
  "visibleWhen": "role === partner",
  "primaryApis": ["POST /api/campus-distribution/income/summary"],
  "summary": "展示个人佣金、团队奖励、待结算",
  "fields": []
}
```

模块粒度规则：

- 一个卡片、表单、列表、弹窗、tab 区域通常是一个模块。
- 不要把整个页面作为唯一模块。
- 不要把每个纯装饰元素拆成模块。
- 列表要拆成“列表汇总/筛选”和“列表项字段”。
- 弹窗、抽屉、海报、二维码预览要单独成为页面状态或模块。

### 4. 字段溯源

每个字段至少追到：

```txt
页面展示
-> template 绑定 / v-model / 事件
-> script ref/reactive/computed
-> service 方法
-> normalize/format 函数
-> API method/url
-> request/response 字段
-> 接口文档位置
```

来源类型：

- `response`：后端响应
- `request`：提交给后端
- `computed`：前端计算或聚合
- `local`：路由参数、本地状态、storage
- `static`：静态文案、静态资源
- `derived-risk`：可展示但接口/文档缺失或口径不一致

字段表必须包含：

```txt
中文展示/页面文案 | 前端字段 | sourceType | service/normalize | API 字段 | 前端计算逻辑 | 证据 | 置信度
```

字段不是后端直接返回时，禁止只写 `computed/local/static` 作为 API 字段。必须继续说明前端来源和计算逻辑：

```txt
computed | roleViewMap[role].title，由路由 role/status 选择展示标题
local    | activeTab === today 时生成 startDate=endDate=当天
static   | incomeRuleMap.partner.rules 前端静态规则文案
```

也就是说每条字段都要能回答：

- **sourceType**：`response`、`request`、`computed`、`local`、`static`、`derived-risk`
- **displayLabel**：页面上对应的中文文案、业务含义或产品叫法；不能只写变量名。页面没有直接文案时，用业务中文名，如“身份标题”“累计收益”“团队直属大使名称”。
- **apiField**：直连后端字段；没有直连字段时写 `-`
- **frontendLogic**：computed/ref/reactive/normalize/格式化/分组/过滤/静态配置的具体规则
- **traceChain**：字段溯源链路，至少列出 UI 绑定、页面状态/computed、service/normalize、API 字段、证据行号。尤其是 computed 字段，必须写出它依赖哪个 ref/computed，以及这个依赖最终来自哪个接口字段。
- **evidence**：源码行号或文档位置

如果字段经过 service normalize 或页面 computed 二次加工，要同时写后端原字段和前端加工逻辑，例如：

```txt
累计收益 | distributionData.balance | totalIncomeAmount | normalizeWorkspace -> formatDistributionAmount(totalIncomeAmount) | distribution.js:176-181
团队直属大使分组 | teamAmbassadors | records[].promoterUid | teamUsers 按 promoterUid/promoterAgentNo 分组 | register-detail.vue:137-153
```

computed 字段必须呈现为链路，而不是一句概述：

```txt
身份标题
1. UI：模板展示 roleView.title
2. computed：roleView = roleViewMap[distributionData.role]
3. 页面状态：distributionData 来自 APIgetDistributionWorkspace()
4. normalize：normalizeWorkspace 将 identityStatus.identityType 归一化为 role
5. API：POST /api/campus-distribution/workspace -> identityStatus.identityType
6. 证据：index.vue:205-229；distribution.js:163-201；接口文档:498-534
```

### 5. 业务流程建模

流程节点必须覆盖页面跳转和关键分支。不要把多个不同意图塞进一个节点。

```json
{
  "id": "withdraw.submit",
  "title": "提交提现申请",
  "trigger": "点击提现弹窗提交",
  "screen": "income.withdraw-popup",
  "apis": ["POST /api/.../withdraw/apply"],
  "module": "income.withdraw-form",
  "next": ["income.refresh"],
  "risks": ["前端提现阈值与接口文档不一致"]
}
```

流程必须能回答：

- 入口在哪里？
- 首屏调用什么接口？
- 用户点击后调用什么接口？
- 成功后跳哪或刷新什么？
- 失败、禁用、冻结、审核中、空态怎么走？

### 6. 可视化策略

#### 有真实截图或可运行页面

- 优先截图或浏览器渲染结果。
- 热点坐标必须来自真实截图尺寸或 DOM 测量。
- 标注图允许红框，但红框必须对齐具体模块。

#### 无真实截图

- 优先生成“模块结构图”或“手机结构原型”，不要假装 1:1 页面。
- 热点使用模块卡片或结构行绑定，而不是绝对坐标猜测。
- 如果使用手机原型，红框必须绑定到生成的模块容器，不得漂浮在手写坐标上。

禁止：

- 画看似真实但和源码布局关系很弱的页面。
- 红框跨越多个模块或遮挡内容。
- 一个热点没有对应 detail。
- 一个 detail 没有接口/字段/证据。

### 7. 交互 HTML 规范

`*.flow.html` 是核心交付，纯静态、可直接浏览器打开、不依赖外部 CDN。

推荐布局：

```txt
顶部：功能概览 + 关键接口 + 待确认风险
左侧：紧凑流程轴 / 页面列表 / 角色状态矩阵
中间：页面结构图或真实截图标注 + 模块卡片
右侧：当前模块数据来源面板
底部或 Tab：字段表、请求/响应、证据、风险
```

必须具备：

- 流程节点可点击，切换页面状态和模块。
- 流程节点和模块卡片必须一一联动：点击流程时，中间结构图要高亮并滚动到对应模块；点击模块时，左侧流程要同步到对应流程，若无对应流程则取消流程高亮。
- 左侧流程区必须优先使用紧凑流程轴、stepper 或导航轨，而不是和中间模块相同的大卡片列表；流程区只展示步骤名、页面/状态、触发方式和“定位到哪个模块”。
- 左侧流程区不得重复渲染模块摘要、字段表、完整接口清单或风险详情；接口和字段细节放在中间模块卡或右侧详情中。
- 模块热点可点击，右侧展示数据来源。
- 页面状态可切换，如角色、tab、弹窗、空态、冻结态。
- 顶部必须有“此功能涉及接口”和“待确认点”摘要。
- 右侧详情先显示“模块结论”，再显示字段表，不要一上来塞满表格。
- 字段溯源在窄侧栏里优先使用“字段卡片/两行式布局”，不要强行塞多列表格，避免中文标题被挤成竖排；只有主内容区足够宽时才使用完整表格。
- 三栏/多卡片布局必须让每个主要卡片独立滚动，如流程列表、页面结构图、详情面板分别设置自己的 `overflow:auto` 和稳定高度；外层页面也可以保留总滚动条，用于小屏或顶部摘要过高时兜底，但不要只依赖整页滚动。
- 容器使用 `overflow:auto`，中间区域可横向滚动，不裁掉模块或字段。
- 视觉上是工具型界面：信息密集但清晰，少装饰，多对齐。

### 7.5 默认布局模板

除非用户明确指定其他形式，`*.flow.html` 默认使用以下模板，不能退化成三栏重复卡片：

```txt
顶部摘要：页面/状态、核心接口、待确认点
左侧：紧凑流程轴 / stepper / nav rail，只显示步骤、页面、触发、定位模块
中间：页面模块结构图，使用模块卡片展示模块摘要和接口 chip
右侧：模块详情，使用字段卡片展示接口、字段、computed/normalize、证据和风险
```

职责边界：

- 流程轴回答“用户怎么走”。
- 模块结构图回答“页面有什么”。
- 详情面板回答“数据从哪里来”。
- 同一段业务说明不得同时完整出现在流程轴和模块卡片里。

### 8. HTML 质量硬约束

生成 `*.flow.html` 时必须满足这些可检查约束，不能只凭主观感觉：

- **结构数据驱动**：HTML 只能从 `flowSpec` 渲染，不要把重要业务解释只写在 HTML 字符串里；`flowSpec.json` 必须单独输出。
- **字段卡片而非窄表格**：右侧详情面板里的字段溯源默认使用卡片。卡片必须包含中文名、前端字段、sourceType、API 字段、来源接口、置信度、前端计算逻辑、traceChain。
- **traceChain 全覆盖**：每个字段都必须有 `traceChain`，且链路至少 4 步；computed 字段必须追到最终 API 字段或明确说明无 API 字段。
- **中文展示全覆盖**：每个字段都必须有 `displayLabel`，不能只显示变量名。
- **独立滚动**：左侧列表、中间模块结构、右侧详情面板分别独立滚动；外层页面可以保留总滚动条作为兜底。
- **无低可信视觉**：没有真实截图/DOM 测量时，不使用漂浮红框和手写坐标。
- **首屏有结论**：首屏顶部必须展示页面/状态、核心接口、待确认风险。
- **流程/模块联动一致**：任意时刻左侧选中的流程与中间高亮模块必须对应；不得出现流程选中 A、模块高亮 B 的错位状态。
- **流程轴优先**：左侧流程区使用 compact timeline / stepper / nav rail，不使用与中间相同的模块卡片样式。
- **信息去重**：左侧流程列表不重复渲染模块摘要、字段表、风险详情或完整接口清单；模块卡负责说明模块内容，右侧负责字段和接口溯源。

推荐在生成后执行最少校验：

```txt
1. 解析 HTML 内嵌脚本，确认不报语法错。
2. 检查 flowSpec.layoutContract / traceabilityContract / qualityGates 存在。
3. 检查 flowSpec.flows[*].module 都能命中 modules[*].id。
4. 检查 flowSpec.modules[*].fieldTraces[*].displayLabel 非空。
5. 检查每个 fieldTrace.traceChain 至少 4 步，computed/local/static 字段不得只有来源类型。
6. 检查 HTML 包含 flow-rail 或等价流程轴、module-card、field-trace-card。
7. 检查左侧流程区没有重复渲染模块摘要、完整接口清单或字段详情。
3. 检查 flowSpec.modules[*].fieldTraces[*].traceChain 长度 >= 4。
4. rg 搜索关键接口、关键字段、关键风险、"基于源码生成，非真机截图"。
5. 检查点击流程后中间对应模块会高亮并滚动到可视区域。
6. 检查点击模块后左侧流程同步或取消错位高亮。
7. 确认右侧字段区没有 6 列以上窄表格，存在字段卡片样式或结构。
```

### 9. flowSpec Schema

基础 schema：

```json
{
  "featureName": "",
  "sourceFiles": [],
  "apiDocs": [],
  "roles": [],
  "roleStateMatrix": [],
  "apiInventory": [],
  "flows": [],
  "screens": [],
  "modules": [],
  "details": [],
  "pendingQuestions": [],
  "qualityNotes": []
}
```

字段建议结构：

```json
{
  "displayLabel": "累计收益",
  "field": "distributionData.balance",
  "sourceType": "response+normalize",
  "apiField": "incomeSummary.totalIncomeAmount",
  "serviceLogic": "normalizeWorkspace -> formatDistributionAmount",
  "frontendLogic": "身份卡展示格式化后的累计收益",
  "traceChain": [
    "UI：身份卡累计收益展示 distributionData.balance",
    "页面状态：distributionData 来自 APIgetDistributionWorkspace()",
    "service：normalizeWorkspace 读取 incomeSummary.totalIncomeAmount",
    "API：POST /api/.../workspace -> incomeSummary.totalIncomeAmount",
    "证据：index.vue:xx；distribution.js:xx；接口文档:xx"
  ],
  "evidence": ["index.vue:xx", "distribution.js:xx"],
  "confidence": "high"
}
```

热点必须包含定位策略：

```json
{
  "id": "workspace.month-data",
  "label": "推广数据（本月）",
  "detailId": "workspace.month-data",
  "anchorStrategy": "module-card",
  "rect": null,
  "confidence": "high"
}
```

`anchorStrategy` 取值：

- `screenshot-measured`：真实截图或 DOM 测量坐标
- `generated-dom`：静态原型中由模块容器生成
- `module-card`：结构化模块卡片
- `structure-row`：列表/表格中的结构行
- `manual-low-confidence`：不得默认使用；只能在无法避免时使用，并写入质量风险

### 9. Markdown 输出

`*.mapping.md` 至少包含：

1. 页面/功能概览：页面、角色、涉及接口、交互 HTML 链接
2. 角色状态矩阵
3. API 清单：接口用途、触发时机、请求、响应
4. 业务流程表：触发、页面状态、接口、下一步、失败分支
5. 模块映射明细：模块、展示内容、接口字段、前端字段、逻辑、证据
6. 待确认点：按严重程度排序
7. 生成说明：真实截图或源码原型、热点策略、已做校验

### 10. 标注图要求

标注图可以是两种之一：

- 真实截图标注：有截图或可运行页面时使用。
- 结构化模块标注图：无截图时使用。

标注图必须：

- 每个标注落到具体模块。
- 每个编号能在 Markdown/HTML 中找到对应 detail。
- 不把页面缩成不可读的小图。
- 不画无来源的装饰红框。

## 质量门禁

交付前必须自查：

- `flow.html` 能打开、点击流程、点击模块、切换状态。
- 内嵌 JS 抽出后 `node --check` 通过。
- 关键接口 URL、关键字段、风险关键词能 `rg` 搜到。
- 每个热点都有 detail，每个 detail 至少有一个证据。
- 没有真实截图时，所有视觉产物都标明“非真机截图”。
- 红框或热点不漂浮；若无法可靠定位，改为模块卡片热点。
- 顶部摘要能在 30 秒内回答：这个功能有哪些页面、哪些接口、哪些风险。
- 不复制整段接口文档，只抽取与页面相关字段。
- 输出目录遵循用户要求，不默认写进项目目录。

## 交付命名建议

```txt
page-interface-mapping/
  feature-name.flow.html
  feature-name.flowSpec.json
  feature-name.mapping.md
  feature-name.prototype.html
  feature-name.annotated.svg
```

## 执行步骤

1. 读取页面、service、接口文档和业务描述。
2. 建立角色/状态矩阵、API 清单、模块清单和风险清单。
3. 建立流程节点和字段溯源 details。
4. 选择可视化策略：真实截图、DOM 测量、静态原型或模块结构图。
5. 生成 `flowSpec.json`。
6. 基于 `flowSpec` 生成 `flow.html`、`mapping.md`、`prototype.html`、标注图。
7. 执行质量门禁；若热点不可靠，降级为模块卡片热点而不是猜坐标。
