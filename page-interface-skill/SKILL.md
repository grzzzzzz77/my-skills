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
- `traceabilityContract`：说明字段必须包含 displayLabel、sourceType、sourceRoot、apiField、frontendLogic、traceChain、evidence。
- `apiFieldMappingContract`：说明本报告是否建立“页面显示字段 -> 后端接口字段”的一一映射矩阵；当用户要求接口字段、后端字段、字段来源、PRD 给 AI 读时必须启用。
- `displayDataIndexContract`：说明本报告是否按“前端显示数据”建立索引；复杂页面或用户关心“数据从哪来”时必须启用。
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
- 服务层：`services/*`、`api/*`、request/http 封装、字段整理/格式化 工具
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

主报告瘦身规则：

- `*.flow.html` 是核心阅读入口，默认只做紧凑顶部摘要 + 三列工作台，不要把大面积手机原型、截图标注、长接口表、长状态表直接铺在三列之前。
- 静态原型、手机结构图、红框标注图应输出到单独的 `*.prototype.html`、`*.annotated.svg/png`，主 `flow.html` 只保留必要的模块结构卡、接口 chip 和字段溯源。
- 如果用户说“像之前那个三列逻辑”“不要原型图标注”“东西太多”，必须优先压缩主报告：顶部只留结论/接口/风险数量，下面直接进入左流程、中模块、右字段；详细矩阵和标注放到折叠区或配套文件。

复杂度匹配规则：

- 单页面、1-2 个接口、1 个核心分支的简单功能，默认使用“轻量报告”：3-5 个模块、10-15 个关键字段以内。不要把分享 hook、纯装饰图、每句静态文案都展开成主报告字段；可合并为“静态页面文案/静态资源”一条，并在 evidence 中给出行号。
- 多页面、多角色、多接口、多表单/列表的复杂功能，才使用完整矩阵、全量字段索引和更细的原子字段拆分。
- 字段完整性优先覆盖动态数据、接口字段、computed 门禁、请求参数、用户可操作按钮和风险字段；静态文案只在它影响业务判断、提交口径或用户流程时拆成单独字段。
- 右侧详情默认只显示当前模块字段，不要默认把全页面所有字段索引都堆在右侧。点击模块或流程时，右侧字段索引应切换到当前模块范围。
- 简单功能的中间模块区默认单列，不要为了显得信息多而做双列模块网格；双列模块只适合模块数量多、视口宽度足够且不会挤压右侧详情的复杂报告。

## 工作流

### 1. 建立分析模型

先从源码和文档建立一份内部模型，禁止直接开始写 HTML。

必须识别：

- 页面：路径、入口参数、生命周期、页面级接口
- 模块：导航、卡片、表单、列表、tab、筛选、弹窗、二维码、海报、按钮、空态、错误态
- 状态：角色、审核、冻结、空列表、有列表、弹窗打开、表单禁用、tab/scope 选中
- 交互：点击、提交、跳转、分享、保存、预览、刷新、下钻、返回
- API：方法名、method、URL、请求体、响应模型、字段整理/格式化、错误/禁用逻辑
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
-> 字段整理/格式化 函数
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
中文展示/页面文案 | 前端字段 | sourceType | 源头URL/本地来源 | API 字段 | 前端计算逻辑 | 证据 | 置信度
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
- **frontendLogic**：computed/ref/reactive/字段整理/格式化/分组/过滤/静态配置的具体规则
- **traceChain**：字段溯源链路，至少列出 UI 绑定、页面状态/computed、接口 URL 或本地来源、API 字段、证据行号。尤其是 computed 字段，必须写出它依赖哪个 ref/computed，以及这个依赖最终来自哪个接口字段。完整链路里也不得用 `APIxxx -> processingFn` 代替接口 URL。
- **evidence**：源码行号或文档位置

如果字段经过 service 字段整理 或页面 computed 二次加工，要同时写后端原字段和前端加工逻辑，例如：

```txt
累计收益 | distributionData.balance | totalIncomeAmount | workspace字段整理 -> formatDistributionAmount(totalIncomeAmount) | distribution.js:176-181
团队直属大使分组 | teamAmbassadors | records[].promoterUid | teamUsers 按 promoterUid/promoterAgentNo 分组 | register-detail.vue:137-153
```

computed 字段必须呈现为链路，而不是一句概述：

```txt
身份标题
1. UI：模板展示 roleView.title
2. computed：roleView = roleViewMap[distributionData.role]
3. 页面状态：distributionData 来自 POST /api/campus-distribution/workspace
4. 字段整理：workspace字段整理 将 identityStatus.identityType 归一化为 role
5. API：POST /api/campus-distribution/workspace -> identityStatus.identityType
6. 证据：index.vue:205-229；distribution.js:163-201；接口文档:498-534
```

前端判断型状态必须把“判断过程”作为独立字段卡，而不是只写最终 UI 状态。尤其是这些场景：

- 接口只返回日志、历史消息、原始 JSON、文本、数组，前端通过扫描、解析、关键词匹配、正则、分组、去重、计数、阈值判断后得到状态。
- 页面状态由接口字段和本地交互共同决定，例如“历史已反馈 1 次 + 当前再点 1 次 = 达到 2 次阈值”。
- 前端兼容多个可选字段，例如 `data.count || data.total || snapshot.count || localCount`。
- 接口文档没有明确列出最终状态字段，前端靠历史消息或本地状态恢复。

这种字段卡必须额外写清楚：

```txt
历史不满意次数恢复
1. UI：老师卡片只在 message.kind === teacher 时展示
2. 原始接口字段：GET /api/job-recommendations/session -> historyConversation.recentMessages[].content
3. 前端解析：遍历 USER_MESSAGE，调用 isHistoryFeedbackText / applyHistoryFeedbackToLastJobsMessage
4. 命中规则：文本包含“不满意/换一批/反馈”，或命中结构化反馈字段、反馈原因、下一批意向
5. 计数：每命中一次 restoredFeedbackCount += 1，回填 dislikeCount
6. 阈值：用户再点一次后 dislikeCount >= 2，appendTeacherMessage()
7. 风险：不是后端显式返回 count=1，文案格式变化会影响恢复结果
8. 证据：页面解析函数行号、service 方法、接口文档 recentMessages 字段
```

禁止把这种逻辑简写成：

```txt
老师卡片展示 | mentorTrigger.triggered / dislikeCount | 达到两次展示
```

正确写法要拆成至少两条：

```txt
历史不满意次数恢复 | historyResult.feedbackCount | recentMessages[].content | 前端解析历史 USER_MESSAGE 文本并计数
老师卡片展示门禁 | message.kind === teacher | historyResult.feedbackCount + local dislikeCount + mentorTrigger.triggered | 三条触发路径分别说明
```

#### 4.0.1 触发型模块门禁必须归属到当前模块

如果一个模块本身是“达到条件才出现”的状态模块，例如人工介入卡、联系客服卡、审核驳回说明、冻结提示、升级入口、二次确认弹窗、风控拦截、老师/客服/运营介入卡，右侧详情不能只写模块出现后的展示字段（例如二维码、电话、老师名称）。必须把“为什么这个模块会出现”的触发门禁作为该模块的第一组字段卡。

强制拆分：

```txt
触发门禁总览 | message.kind === teacher / showServiceCard | mentorTrigger.triggered + local count + history parse | 后端触发、本地点击、历史恢复三条路径
当前会话点击计数 | dislikeCount / message.feedbackCounted | - | 第一次点击打开反馈，第二次点击达到阈值追加卡片
历史会话恢复计数 | historyResult.feedbackCount | recentMessages[].content + data.dislikeCount | 原始字段、解析函数、命中规则、计数合并、阈值
模块展示字段 | supportContact.qrcodeUrl / phone | data.qrcodeUrl / phone | 模块出现后才读取或展示的接口字段
```

质量要求：

- 触发型模块的 `fieldTraces[0]` 应回答“这个模块为什么出现”，而不是从联系方式、金额、图片等展示字段开始。
- 如果触发来源跨越当前会话、本地点击次数、历史会话恢复、后端显式 trigger，必须分别拆成字段卡，且在“总门禁”字段卡里汇总所有路径。
- 对“点击两次/达到阈值/连续失败/累计次数”这类门禁，必须写出防重复计数条件，例如 `message.feedbackOpen`、`message.feedbackCounted`、`locked`、`submitted` 等如何避免同一模块重复计数。
- 如果历史恢复依赖文本、日志、JSON 字符串或消息数组解析，必须写出原始接口字段、解析函数、命中关键词/结构化字段、初始 count 与解析 count 的合并公式、阈值判断和兜底追加逻辑。
- 模块的流程轴文案也必须同步体现触发来源，不能只写“点击人工圈岗浮窗”这种出现后的入口。

#### 4.0.2 显示数据优先的源头索引

当用户问“每一个显示在前端的数据来源是什么”“溯源到源头”“接口哪个字段”时，报告必须从 API 清单模式切换为“显示数据索引模式”。这时 `fieldTraces` 的主语必须是页面上用户看见的单个数据、文案、状态、按钮、输入提示、图片或空/加载态，而不是接口、模块或数组容器。

每条显示数据字段卡至少包含：

```txt
displayLabel | displayScene | sourceType | sourceRoot | field | apiField | frontendLogic | traceChain | evidence
```

字段含义：

- `displayLabel`：屏幕上看到的中文文案、业务含义或可见状态，例如“岗位名称”“老师二维码”“继续推荐按钮禁用态”。
- `displayScene`：出现位置和条件，例如“推荐岗位卡片”“人工卡片出现后”“历史详情老师卡”。
- `sourceType`：`response`、`request`、`computed`、`local`、`static`、`derived-risk`。
- `sourceRoot`：最短源头答案，必须放在字段卡顶部。例如 `POST /api/job-recommendations -> data.jobs[].title`、`template static`、`computed: canSubmitFeedback`、`local ref: selectedReasons`。
- `field`：前端绑定字段、computed、ref、配置键、方法返回值或模板表达式。
- `apiField`：后端字段或请求字段；没有后端直连时写 `-`，不能写成模糊的 `data`。
- `frontendLogic`：所有前端判断、兜底、格式化、过滤、计数、阈值、展示条件。
- `traceChain`：从 UI 绑定到接口/静态配置/本地状态的完整链路。
- `evidence`：源码行号、接口文档位置或明确文件路径。

展示字段命名必须以前端为准，而不是以后端接口文档为准：

- `displayLabel` 必须优先取模板真实文案、`v-for` 行里的 `row.label`、`metric.label`、`path.title`、按钮文案、截图可见文案，或前端 normalize/config 中写死的中文 label。
- 接口文档只用于确认字段来源、类型和接口路径，不能反向把页面字段名改成接口字段名或对象名。
- 如果页面通过 computed/normalize 把一个对象拆成多行展示，例如 `normalizeRows([{ label:'报录比', value:data.xxx }])`，必须按每一个前端 label 拆字段卡，并映射到对应 value 读取的后端字段。
- 如果接口文档只写到对象级，例如 `vip.interviewProbability`，但前端源码实际读取 `interviewProbability.interviewApplicationRatio`，字段卡仍应写页面展示名 `报录比（投递:录取）`，`apiField` 写实际代码读取路径；文档对象级说明放在 evidence 或 notes，不得把字段合并成“基础竞争指标 / data.vip.interviewProbability”。
- 如果 service/adapter 先把后端原始 response key 映射成前端中间字段，例如 `raw['内推加成'] -> interviewReferralBoost`，字段卡必须区分两层：`apiField` / `sourceRoot` 写真实后端原始字段路径 `data.vip.interviewProbability['内推加成']`；`field` / `frontendLogic` / `traceChain` 再写前端归一化字段 `interviewReferralBoost`。除非接口文档或真实响应明确包含该英文 key，否则不得把前端中间字段写成后端 API 字段。
- 如果 mapper 对同一展示字段兼容多个原始 key，例如 `raw['报录比投递录取'] ?? raw['报录比']`，`apiField` 写当前证据最强的主字段，兼容字段写进 `frontendLogic` 或风险说明；不要用“或者或者”的口吻替代主链路。
- 如果文档和代码都没有对应字段，才标记为 `derived-risk` 或 `pendingQuestions`；不要用接口文档里的近似对象名代替页面字段。

后端响应字段必须写成：

```txt
源头：METHOD /api/path -> response.data.xxx.yyy
接口字段：data.xxx.yyy
前端逻辑：字段整理 / computed / v-if / fallback
```

首层源头禁止写成 service 函数名或 前端处理函数名，例如不要写：

```txt
serviceFn -> data.qrcodeUrl
processingFn -> data.infoPoolSummary
selectionParserFn -> recentMessages[].content
```

应写成：

```txt
GET /api/support/contact -> response.data.qrcodeUrl
GET /api/job-recommendations/session?sessionId={sessionId} -> response.data.infoPoolSummary / response.snapshot.infoPoolSummary
GET /api/job-recommendations/session?sessionId={sessionId} -> response.historyConversation.recentMessages[].content；前端 getHistoryBaseConditionSelections/getHistoryDynamicConditionSelections 解析
```

service 函数名、前端处理函数名和解析函数名只能放在 `frontendLogic`、`traceChain` 或证据链中，用来说明前端如何处理接口数据；不能代替接口地址。

前端生成字段必须写成：

```txt
源头：template static / local ref / computed / route query / storage / config
接口字段：-
前端逻辑：具体表达式、依赖变量、命中条件和兜底值
```

条件展示字段必须同时写“数据源”和“出现条件”。例如二维码字段不能只写 `data.qrcodeUrl`，还要写 `message.kind === 'teacher'`、`qrcodeUrl` 为空时显示什么、何时调用 `GET /support/contact`。

质量门禁：

- 必须扫描模板内的 `{{ }}`、`v-if`、`v-show`、`v-for`、`:disabled`、`:class`、`:src`、`placeholder`、按钮文案、空态、加载态、错误态；每个业务相关可见数据都要有字段卡，或在 `qualityNotes` 说明为什么合并/排除。
- 右侧详情字段卡第一屏必须直接出现 `sourceRoot`，用户不展开完整链路也能知道“来自哪个接口哪个字段/哪个前端逻辑”。
- 对 `response` / `request` / `parse` / `derived-risk` 类型字段，`sourceRoot` 必须以 `METHOD /api/...` 或明确的非网络来源开头，质量门禁要检查是否仍残留 service 函数名、前端处理函数名、selection 解析函数名作为首层源头。
- `fieldTraces` 不得只覆盖接口响应字段；静态文案、本地状态、computed 状态、提交请求字段和 fallback 文案也要标明源头。
- 如果某个 UI 展示由多个来源合并，例如“后端 count + 历史消息解析 + 本地点击次数”，必须拆出总门禁字段和各来源字段，不能只写最终变量。

#### 4.0.3 后端接口字段一一映射矩阵（强制）

当用户明确要求“接口字段”“后端字段”“字段来源一一对应”“给 AI 足够上下文不用再读代码”时，报告必须额外建立 `apiFieldMappings`，并且右侧字段卡、字段索引表、Markdown 明细都以它为主数据源。源码行号只能作为 `evidence`，不能作为字段来源的主答案。

`apiFieldMappings` 每一条必须回答：

```txt
页面显示字段 -> 后端接口 URL -> response/request 字段路径 -> 前端字段 -> 加工逻辑 -> 展示条件 -> 证据
```

结构建议：

```json
{
  "id": "practice.question-title",
  "moduleId": "practice.question-objective",
  "displayLabel": "题干内容",
  "displayScene": "答题页题目区域",
  "direction": "response",
  "apiName": "APIGetPracticeRecordDetail / APIGeneratePracticeBySearch / APIRetryPractice",
  "method": "POST",
  "url": "/question/bank/practice-detail",
  "sourceRoot": "POST /question/bank/practice-detail -> response.data.questions[].content",
  "apiField": "data.questions[].content",
  "apiFieldMeaning": "题目题干",
  "frontendField": "currentQuestion.content",
  "frontendLogic": "currentQuestion = questions[currentIndex]；record/search/retry 三种加载模式都会写入 questions",
  "displayCondition": "questions.length > 0",
  "fallback": "-",
  "evidence": ["practice.vue:30", "practice.vue:173-176", "practice.vue:630-744"],
  "confidence": "high"
}
```

拆分规则：

- 一个页面显示项对应一个 mapping，不要把多个后端字段合并成“题目对象”“记录对象”“结果统计对象”。
- 列表字段必须写数组路径，例如 `response.data[].fileName`、`response.data.questions[].options[].value`；同时写前端 item 字段，例如 `item.fileName`、`option.value`。
- 提交字段也要进入矩阵，`direction` 写 `request`，例如 `POST /question/bank/update-answer -> request.userAnswer`。
- 同一 UI 字段可能来自多个入口接口时，必须列出多个 `sourceRoot` 或拆成多条 mapping，并说明入口条件。例如答题页题目来自 record/search/retry 三个接口。
- 如果是本地状态、静态文案、computed、storage 或 route query，`apiField` 写 `-`，`sourceRoot` 写 `route query -> practiceId`、`storage questionBankSearchHistory`、`template static` 等明确非后端来源。
- 如果目前只能从前端代码推断后端响应字段，没有 OpenAPI/Swagger 证据，`confidence` 不能写满；在 `pendingQuestions` 标注“后端 schema 待确认”。
- 字段卡顶部必须优先展示 `sourceRoot` 与 `apiField`。如果顶部只出现 `index.vue:xx`、`computed`、`APIGetXxx` 等而没有 URL 和字段路径，对 response/request 字段视为不合格。

HTML 交付要求：

- 主报告必须有一个宽区块叫“后端字段映射矩阵”或等价名称，列出 `页面显示字段 / 接口 / 后端字段 / 前端字段 / 加工逻辑 / 证据`。
- 右侧详情点击某个模块时，必须只显示该模块相关 mappings，并在第一屏直接看到后端接口字段。
- `flowSpec.modules[*]` 应使用 `fieldTraces` 或 `mappingIds` 关联 `apiFieldMappings`；不要只放旧式 `fields: [{ name, source, usage }]`。
- 质量门禁必须检查：`apiFieldMappings.length > 0`；每条 response/request mapping 的 `sourceRoot` 以 `METHOD /path` 开头；每条 response/request mapping 的 `apiField` 不为空且不等于笼统 `data`。

#### 4.1 原子字段拆分规则（强制）

字段溯源必须按“页面上用户能看到的单个文案/数值/状态/输入项”拆成原子字段卡，禁止把多个 UI 数据合并成一条模糊字段。

必须拆分的场景：

- `v-for` 数组展示多个业务指标时，每个 label/value 都是一条字段溯源。例如 `teamStats[]` 必须拆成“发展大使”“达标大使”“团队注册”“团队订单”，分别写出各自 API 字段。
- `v-for` 展示由前端 normalize/config 生成的分析行时，也必须按前端 label 拆开。例如“报录比（投递:录取）”“网申通过率”“平均晋升周期”“管理序列”分别对应各自读取的字段，不能合并成“竞争比对象”“发展前景对象”。
- 一个卡片同时展示标题、金额、状态、时间、账号、原因时，每个展示项都要拆开。例如提现记录必须拆成“提现金额”“申请时间”“提现状态”“收款方式”“收款账号”“审核时间/打款时间”“驳回原因”。
- 一个 computed 数组或配置数组由多个后端字段 push/拼装而成时，不得只写数组名。例如 `pageData.structure` 必须拆成“个人推广佣金”“团队任务奖励”“团队订单分佣”“待结算”。
- 列表项字段必须拆到列表项内部字段。例如用户卡片必须拆成“用户昵称”“注册时间”“来源渠道”“有效状态”；团队大使卡必须拆成“大使名称”“注册人数”“达标状态”。
- 表单提交字段必须按输入项拆分。例如提现申请必须拆成“提现金额”“收款方式”“收款账号”“收款姓名”，每条说明 v-model、校验、请求字段和接口文档。
- 动态中文 label 和 value 要分开或明确成对说明，不能只写一个组合字段。若 label 与 value 的 API 口径不一致，必须列为风险。

禁止写法：

```txt
发展大使/团队注册/团队订单/达标大使 | teamStats[] | directAmbassadorCount / rewardReachedCount / ...
提现记录卡片 | withdrawalRecords[] | amount / status / receiveType / ...
统计四宫格 | currentStats | records.length + totalRegisterCount + ...
```

正确写法：

```txt
发展大使 | teamStats[0].value | directAmbassadorCount | teamStats computed 读取 distributionData.directAmbassadorCount
达标大使 | teamStats[1].value | rewardReachedCount | workspace字段整理 优先 workspace.rewardReachedCount，缺失回退 growthRewardProgress
团队注册 | teamStats[2].value | teamRegisterCount | teamStats computed 读取 distributionData.teamRegisterCount
团队订单 | teamStats[3].value | teamVipOrderCount | teamStats computed 读取 distributionData.teamVipOrderCount
```

质量门禁必须额外检查：

- `fieldTraces[*].field` 不应只有数组容器名，例如 `teamStats[]`、`currentStats`、`withdrawalRecords[]`、`pageData.structure`，除非该字段卡只描述“数组生成规则”且同模块已经有每个展示字段的原子卡。
- 每个模块的 `fieldTraces` 数量要覆盖该模块模板内所有用户可见的动态数据点；若无法覆盖，必须在 `pendingQuestions` 或 `qualityNotes` 写明遗漏原因。
- 右侧详情默认先显示“字段索引/一眼总览”，每张字段卡顶部必须直接展示 `displayLabel -> frontend field -> API field -> METHOD /api/...`，避免用户打开完整链路才能知道来源。
- 对“前端判断型状态”，质量门禁必须检查是否写明原始接口字段、解析函数、命中规则、计数/阈值、本地状态合并、文档缺口和证据行号；不能只写最终状态字段或最终 UI 文案。
- 对“触发型模块”，质量门禁必须检查当前模块详情里是否包含触发门禁字段卡。若用户点击该模块时右侧只出现二维码、电话、金额、图片等展示字段，而没有出现条件、计数、阈值和历史恢复逻辑，则视为未通过。

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
- 字段卡片内的 `sourceRoot`、`API 字段`、`前端逻辑` 等标签不得使用过窄左列，不能把中文挤成逐字换行或竖排。优先使用“标签在上、内容在下”的上下式字段块；若使用左右两列，标签列必须能完整容纳常见标签，并设置 `white-space: nowrap` 或等价防断行策略。
- 右侧详情面板宽度不足时，字段信息宁可纵向堆叠，也不要压缩标签列。大屏可以切换为两列字段块，但每个字段块内部仍保持标签完整可读。
- 三栏/多卡片布局默认采用“大屏工作台 + 面板内滚动”：桌面端内容区建议设置 `min-width: 1440px`（复杂报告可到 1560px+），三栏宽度要给足，左侧流程、中间模块、右侧详情都保留独立滚动条，形成稳定的工具界面。
- 面板不能矮：不要把主内容锁在很短的 `height: calc(100vh - ...)` 里。桌面端三栏可视高度建议不低于 `820px`，或使用 `height: calc(100vh - compactHeaderHeight)` + `min-height: 820px`；顶部摘要要紧凑，给三栏留下足够高度。
- 外层页面滚动作为兜底：`body`/页面总滚动条用于顶部摘要过高、小屏、或整体画布超出时兜底，不应取代三栏内部滚动。用户应能在每个主面板内部顺畅浏览长流程、长模块和长字段详情。
- 禁止默认让整个页面横向滚动。桌面端三栏应在视口内自适应，设置 `overflow-x:hidden` 或等价策略；长 API、长模块列表、长字段链路允许在具体卡片内部横向滚动，例如 `module-card` / `field-trace-card` / chip strip 内部 `overflow-x:auto`。
- 普通模块卡片不要因为接口路径长就加横向滚动条。模块卡片里的接口 chip 应优先去掉公共前缀（例如 `/api`）、使用短标签、自然换行或 `overflow-wrap:anywhere`。只有密集标签区、字段链路或证据列表确实无法压缩时，才在该内部区域启用横向滚动。
- 可视化区域不得只显示技术 ID。模块、字段、接口、角色状态 chip 应优先显示项目里的中文名、页面文案或业务叫法；技术 ID、字段名、模块 ID 作为小号辅助信息保留，方便研发回查源码。
- 容器使用 `overflow:auto`，中间区域可横向滚动，不裁掉模块或字段。
- 视觉上是工具型界面：信息密集但清晰，少装饰，多对齐。

### 7.5 默认布局模板

除非用户明确指定其他形式，`*.flow.html` 默认使用以下模板，不能退化成三栏重复卡片：

```txt
顶部摘要：页面/状态、核心接口、待确认点（保持紧凑，避免占掉大面积首屏）
左侧：紧凑流程轴 / stepper / nav rail，只显示步骤、页面、触发、定位模块
中间：页面模块结构图，使用模块卡片展示模块摘要和接口 chip
右侧：模块详情，使用字段卡片展示接口、字段、computed/字段整理、证据和风险
```

职责边界：

- 流程轴回答“用户怎么走”。
- 模块结构图回答“页面有什么”。
- 详情面板回答“数据从哪里来”。
- 同一段业务说明不得同时完整出现在流程轴和模块卡片里。
- 桌面端优先做稳定三栏工作台：三栏各自滚动，顶部摘要紧凑，模块卡片保持舒适密度。不要为了减少滚动条把所有内容摊成很长的页面，也不要让整个页面出现横向滚动；横向溢出应发生在卡片内部。
- 角色/状态矩阵不要默认用宽表格塞进中间面板。优先渲染为“角色状态速览卡片”：每个角色/状态一张卡，默认接口、可见模块、禁用模块用 chip/标签展示，chip 行内部可横向滚动。模块 chip 必须显示中文模块名，模块 ID 只作为辅助小字；只有用户明确要求表格或导出数据时，才额外提供完整表格。
- 主 `flow.html` 不要默认内嵌手机原型大图、红框截图或长篇标注说明。可视化原型只在中间模块结构需要少量辅助时出现，且必须轻量；完整原型和标注图放到单独附件。主视图的第一屏应能看到三列主体，而不是先滚过多段说明区。

### 7.6 右侧详情卡片信息架构

右侧详情面板的目标是“快速判断字段从哪里来”，不是把所有字段、链路、证据一次性铺满。默认采用渐进披露：

```txt
模块概览卡：
  标题 / 模块 ID
  一句话结论
  页面、状态、可见条件
  相关接口 chip

字段溯源卡：
  第一行：中文字段名 + sourceType badge + confidence badge
  核心区：源头 sourceRoot、前端字段、API 字段（两列信息块，窄屏自动单列）
  摘要区：前端逻辑（短段落，默认展开）
  折叠区：完整 traceChain、证据 evidence、字段风险（默认可折叠）
```

右侧字段卡片必须遵守：

- 默认只展开能帮助读者判断口径的核心信息：字段名、来源类型、sourceRoot、前端字段、API 字段、前端逻辑。
- `sourceRoot` 是第一优先级信息。后端/请求字段必须直接显示接口 URL 和字段路径，例如 `GET /api/support/contact -> response.data.qrcodeUrl`；不得显示 service 函数名、前端处理函数名或 selection 解析函数名作为首层来源。
- `traceChain` 和 `evidence` 默认放进 `<details>`、折叠面板、展开行或等价结构中；不要让 6 步链路和 8 个证据 chip 一上来撑满卡片。
- 字段卡片不要使用大段编号列表作为主视觉。编号链路只出现在“完整链路”折叠区。
- 每张字段卡最多优先展示 2 个主字段块：`frontend field` 与 `API field`。接口来源必须使用 `sourceRoot` 的 URL 写法，前端处理逻辑用独立摘要块展示。
- `sourceType` 与 `confidence` 使用 badge，不要混在正文里。
- 证据 chip 保留，但默认折叠；展开后允许换行，不要在右侧面板制造横向滚动。
- 长 URL、长字段名、长函数名、英文 token 必须设置 `overflow-wrap:anywhere`、`word-break:break-word` 或等价规则；字段卡、kv 块、sourceRoot、logic、traceChain、证据 chip 都不能把右侧面板撑宽。窄屏时两列字段块必须自动变成单列。
- 风险只在存在时展示，且放在字段卡底部独立黄色提示块，不要混入逻辑摘要。
- 如果字段很多，右侧字段区可加“字段数量/筛选/分组”，但不能退化成一张宽表。

### 8. HTML 质量硬约束

生成 `*.flow.html` 时必须满足这些可检查约束，不能只凭主观感觉：

- **结构数据驱动**：HTML 只能从 `flowSpec` 渲染，不要把重要业务解释只写在 HTML 字符串里；`flowSpec.json` 必须单独输出。
- **后端字段矩阵驱动**：用户要求接口字段/后端字段/字段来源时，必须生成 `apiFieldMappings`，并由它驱动右侧字段卡和字段索引。源码行号只是证据，不能替代 `METHOD /api/path -> response/request.field`。
- **字段卡片而非窄表格**：右侧详情面板里的字段溯源默认使用分层卡片。卡片必须包含中文名、前端字段、sourceType、API 字段、来源接口、置信度、前端计算逻辑、traceChain；其中 traceChain/evidence 默认可折叠，不作为卡片主视觉。
- **接口 URL 优先**：`response` / `request` / `parse` / `derived-risk` 字段的首层 sourceRoot 必须是 `METHOD /api/... -> response/request 字段`；字段卡主视觉、完整链路、Markdown 表格里都不能用 service 函数名或 前端处理函数名代替接口地址。
- **traceChain 全覆盖**：每个字段都必须有 `traceChain`，且链路至少 4 步；computed 字段必须追到最终 API 字段或明确说明无 API 字段。
- **中文展示全覆盖**：每个字段都必须有 `displayLabel`，不能只显示变量名。
- **以前端页面为准**：字段中文名必须优先来自模板实际文案、动态 label、按钮文案或页面截图。不要用后端字段语义反推页面展示。遇到 `roleView.leftAmountLabel + distributionData.pendingAmount` 这类“动态中文名 + 复用数值字段”时，必须把 label 和 value 分成两条溯源，并把文案与后端字段源头不一致列为风险。
- **模块中文名全覆盖**：`roleStateMatrix.visibleModules`、`roleStateMatrix.disabledModules`、`flows[*].module`、`hotspots[*].label` 必须能展示中文模块名。优先使用 `modules[*].title`，对 `workspace.*`、`register.team-*` 这类通配符在 `flowSpec.moduleDisplayNames` 里补中文兜底。
- **滚动体验**：桌面端默认三栏内部滚动条必须存在且可用，左侧列表、中间模块结构、右侧详情面板分别滚动；外层页面滚动只做兜底。主要面板高度要足够大，避免出现短小、难用的内滚区域。
- **横向溢出控制**：整页不应出现横向滚动条；长 token、接口路径、模块 ID、字段链路应在所属卡片内换行，必要时才在 chip strip 内部横向滚动。字段卡主内容默认使用换行，不允许长函数名或长字段路径穿出卡片。
- **接口路径展示**：模块卡片、摘要 chip 中的接口 URL 默认省略公共前缀 `/api`；若仍然过长，优先换行或缩短标签，不要在普通模块卡片底部出现横向滚动条。
- **矩阵展示**：角色/状态矩阵默认使用卡片和标签，不使用会把中文压成竖排的宽表格作为主展示。
- **无低可信视觉**：没有真实截图/DOM 测量时，不使用漂浮红框和手写坐标。
- **首屏有结论**：首屏顶部必须展示页面/状态、核心接口、待确认风险。
- **流程/模块联动一致**：任意时刻左侧选中的流程与中间高亮模块必须对应；不得出现流程选中 A、模块高亮 B 的错位状态。
- **流程轴优先**：左侧流程区使用 compact timeline / stepper / nav rail，不使用与中间相同的模块卡片样式。
- **信息去重**：左侧流程列表不重复渲染模块摘要、字段表、风险详情或完整接口清单；模块卡负责说明模块内容，右侧负责字段和接口溯源。

推荐在生成后执行最少校验：

```txt
1. 解析 HTML 内嵌脚本，确认不报语法错。
2. 检查 flowSpec.layoutContract / traceabilityContract / qualityGates 存在。
2. 检查用户要求后端字段时，flowSpec.apiFieldMappingContract 存在，且 flowSpec.apiFieldMappings.length > 0。
3. 检查 flowSpec.flows[*].module 都能命中 modules[*].id。
4. 检查 flowSpec.modules[*].fieldTraces[*].displayLabel 非空。
5. 检查每个 fieldTrace.traceChain 至少 4 步，computed/local/static 字段不得只有来源类型。
6. 检查 response/request/parse 字段的 sourceRoot、traceChain、Markdown 明细和 HTML 主视觉都不以 service 函数名或 前端处理函数名代替 URL。
6. 检查 response/request 类型的 apiFieldMappings[*].sourceRoot 以 `METHOD /path -> response/request.` 开头，apiField 不为空、不等于 `data`，且 detail 面板第一屏能看到这些值。
7. 检查 HTML 包含 flow-rail 或等价流程轴、module-card、field-trace-card。
8. 检查字段卡长 token 换行规则存在：sourceRoot、API 字段、前端字段、traceChain、证据 chip 都不会撑出右侧面板。
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
  "apiFieldMappingContract": "",
  "apiFieldMappings": [],
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
  "sourceType": "response+字段整理",
  "sourceRoot": "POST /api/.../workspace -> response.incomeSummary.totalIncomeAmount",
  "apiField": "incomeSummary.totalIncomeAmount",
  "frontendLogic": "身份卡展示格式化后的累计收益",
  "traceChain": [
    "UI：身份卡累计收益展示 distributionData.balance",
    "页面状态：distributionData 来自 POST /api/.../workspace",
    "接口：POST /api/.../workspace -> response.incomeSummary.totalIncomeAmount",
    "前端处理：读取 incomeSummary.totalIncomeAmount 并格式化为金额文案",
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
