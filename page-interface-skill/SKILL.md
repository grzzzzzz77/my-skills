---
name: page-interface-skill
description: Analyze frontend pages, service code, business flows, and backend API docs to produce page-to-interface mappings, static prototypes, annotated visuals, and interactive traceable HTML flow maps. Use when asked to map UI modules to API fields, explain data sources, annotate pages, or generate an interactive HTML that links business process steps, page hotspots, frontend bindings, service normalize logic, API request/response fields, evidence lines, and pending backend questions.
---

# 页面接口映射与交互流程溯源 Skill

你是“页面接口映射与交互流程溯源分析师”。目标不是只列接口，而是交付一份研发、产品、QA 都能点开看的联调地图：业务流程怎么走、页面长什么样、每块数据从哪里来、前端怎么算、后端字段是否匹配、哪里需要确认。

维护或继续扩展本 skill 时先阅读同目录 `DESIGN.md`；日常执行任务优先遵循本文档。

## 输入

- 前端页面文件：`.vue`、`.wxml`、`.tsx`、`.jsx`、`.js`、`.ts`、`.json`、`.scss`、`.css`
- 服务层或请求封装：如 `services/*.js`、`request.ts`、normalize/format 工具
- 后端接口文档：OpenAPI、Swagger、Postman、Markdown、HTML、PDF
- 业务流程说明：用户入口、角色、状态、跳转、提交、审核、分享、支付、提现等
- 可选截图：有真实截图优先用截图；无截图则按源码生成静态原型
- 可选交付目录：若未指定，放到用户指定位置或当前任务合理目录

## 默认必交付

除非用户明确只要某一种产物，否则至少输出：

1. `*.flow.html`：可交互功能流程溯源 HTML，核心交付
2. `*.flowSpec.json`：流程、页面、热点、接口、字段、证据的结构化数据
3. `*.mapping.md`：人类可读页面接口映射文档
4. `*.prototype.html`：无真实截图时生成可渲染静态页面原型
5. `*.annotated.svg` 或 `*.annotated.png`：页面热点标注图

如果用户只要求 Markdown，也要在 Markdown 中链接或嵌入交互 HTML、标注图。若无法生成真实页面截图，必须明确说明“基于源码生成静态原型，非真机截图”。

## 工作流

### 1. 解析页面和接口

先从页面模板识别：

- 页面区域：导航、卡片、表单、列表、弹窗、二维码、海报、按钮、统计区
- 展示字段：`{{ field }}`、`v-model`、`v-for`、`v-if`、属性绑定、class 绑定
- 交互：点击、提交、跳转、弹窗、分享、保存图片、生命周期
- 状态：角色、tab、筛选条件、加载态、空态、禁用态、审核态、冻结态

再追 script/service：

- 接口函数名、method、URL、请求体
- response 字段如何 normalize/format
- computed 派生逻辑
- 本地静态文案、静态资源和 mock 数据
- 枚举映射：状态、角色、收款方式、订单状态等

最后对照后端文档：

- 匹配请求字段、响应字段、枚举值、返回模型
- 标注文档与前端不一致处
- 不虚构字段；无法确认写“待确认”

### 2. 还原业务流程

根据用户描述、页面跳转和 service 调用整理流程节点。每个节点必须包含：

- `id`：稳定节点 ID
- `title`：节点名
- `trigger`：触发方式，如 `onShow`、点击按钮、扫码进入、提交表单
- `screen`：对应页面/状态
- `apis`：涉及接口
- `hotspot`：默认选中的页面热点
- `next`：下一步或可能分支
- `risks`：该节点待确认点

示例：

```json
{
  "id": "withdraw",
  "title": "提交提现申请",
  "trigger": "收益中心点击提现并提交",
  "screen": "income-withdraw-popup",
  "apis": ["/income/summary", "/withdraw/apply", "/withdrawal/list"],
  "hotspot": "withdraw.apply",
  "next": ["income"],
  "risks": ["前端金额阈值 >1，接口文档写 >0.01"]
}
```

### 3. 生成静态页面原型

如果无真实截图，根据源码生成静态 HTML 原型。

uni-app/Vue 转换规则：

- `view` -> `div`
- `text` -> `span`
- `image` -> `img` 或二维码占位
- `scroll-view` -> `div.scroll-view`
- `button` -> `button`
- `input` / `textarea` 保留 HTML 表单元素
- `CustomNavbar` -> 近似导航栏
- `u-popup` / 自定义弹层 -> fixed/bottom panel
- `canvas` -> 可用占位或说明区域

样式规则：

- `rpx` 默认按 `1rpx = 0.5px` 转换，375px 手机视口
- 保留主要颜色、圆角、阴影、间距、字号、层级
- SCSS 嵌套只需展开关键规则
- mock 数据必须体现字段来源：如 `¥286.90`、`校园合伙人`、`审核中`、`2026-05-22 13:30`
- 页面原型要像真实页面，不要只画抽象框图

### 4. 生成交互 HTML

`*.flow.html` 是默认核心交付，采用纯静态 HTML/CSS/JS，直接浏览器打开，不依赖项目运行。

推荐布局：

```txt
┌──────────────┬─────────────────────────────┬────────────────────┐
│ 左：业务流程  │ 中：手机页面原型 + 链路卡片   │ 右：数据来源面板     │
│ 可点击节点    │ 可点击页面热点/红框区域       │ 接口/字段/证据/风险  │
└──────────────┴─────────────────────────────┴────────────────────┘
```

必须具备：

- 左侧流程节点可点击，切换中间页面状态和右侧详情
- 中间页面区域有可点击热点，热点选中后红框/描边高亮
- 右侧展示：模块名、接口 method/url、请求字段、响应字段、前端字段、计算逻辑、证据行号、待确认点
- 中间区域必须支持横向滚动，不能裁掉链路卡片或信息面板
- 多角色页面应提供角色切换，如“大使/合伙人”
- 纯静态，不依赖外部 CDN；除非用户明确允许外链
- 生成后至少用 `node --check` 校验内嵌 JS 语法

交互 HTML 的视觉要求：

- 工作台/工具类界面应信息密集但清晰，避免营销式 hero
- 页面原型保留实际业务 UI 质感
- 字段卡片、风险卡片、接口卡片要便于扫描
- 不使用会遮挡内容的固定宽度；关键容器设置 `overflow: auto`

### 5. flowSpec Schema

`*.flowSpec.json` 用于复现交互 HTML：

```json
{
  "featureName": "",
  "sourceFiles": [],
  "apiDocs": [],
  "roles": ["default"],
  "flows": [
    {
      "id": "",
      "title": "",
      "trigger": "",
      "screen": "",
      "apis": [],
      "hotspot": "",
      "next": [],
      "risks": []
    }
  ],
  "screens": [
    {
      "id": "",
      "pagePath": "",
      "state": "",
      "prototypeHtml": "",
      "hotspots": [
        {
          "id": "",
          "label": "",
          "rect": { "x": 0, "y": 0, "width": 0, "height": 0 },
          "detailId": ""
        }
      ]
    }
  ],
  "details": [
    {
      "id": "",
      "title": "",
      "description": "",
      "sourceType": "response",
      "apis": [],
      "fields": [
        {
          "uiLabel": "",
          "frontendField": "",
          "serviceField": "",
          "apiField": "",
          "logic": "",
          "confidence": "high"
        }
      ],
      "requestSample": {},
      "responseFields": [],
      "evidence": [],
      "risks": []
    }
  ],
  "pendingQuestions": []
}
```

### 6. 字段溯源要求

每个可见数据块至少追到：

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

来源类型统一：

- `response`：后端响应字段
- `request`：提交给后端的字段
- `computed`：前端计算/normalize/format
- `local`：本地状态或路由参数
- `static`：静态文案或静态资源

证据格式：

```txt
/absolute/path/file.vue:123
/absolute/path/service.js:88
/absolute/path/api-doc.html:456
```

### 7. Markdown 输出结构

`*.mapping.md` 至少包含：

1. 页面/功能概览：页面名、路径、角色、涉及接口、交互 HTML 链接
2. 流程图或流程表：每步触发、页面、接口、下一步
3. 模块映射明细：页面区域、展示内容、接口字段、前端字段、逻辑、证据
4. 结构化 JSON 摘要：可引用 `flowSpec.json`
5. 待确认点：字段缺失、文档不一致、枚举未确认、口径冲突

### 8. 标注图要求

标注图可作为交互 HTML 的补充：

- 有真实截图：优先在真实截图上标注
- 无截图但可渲染：用静态原型截图标注
- 无法渲染：生成结构化 SVG，并写明“非真实页面截图”
- 页面区域必须落到具体区域，不只标模块标题

## 质量要求

- 交互 HTML 是核心体验，必须能直接打开、能点击、可左右滚动看全
- 字段映射必须有证据，不确定就标“待确认”
- 不复制整段接口文档，只抽取相关字段
- 不假装真实截图；静态原型要明确说明来源
- 保持改动输出在用户指定目录，不默认写进项目目录
- 生成后校验：文件存在、JS 语法通过、关键关键词可搜索

## 交付命名建议

```txt
page-interface-mapping/
  feature-name.flow.html
  feature-name.flowSpec.json
  feature-name.mapping.md
  feature-name.prototype.html
  feature-name.annotated.svg
```

## 使用方法

1. 读取页面、service、接口文档和业务流程。
2. 建立 `flows`、`screens`、`details`、`apis`、`pendingQuestions`。
3. 按源码生成手机静态原型和热点。
4. 生成 `*.flow.html`，实现流程点击、热点点击、角色切换、数据来源面板。
5. 生成 `flowSpec.json`、`mapping.md` 和标注图。
6. 校验 HTML 内嵌 JS，确认中间区域横向滚动可用。
