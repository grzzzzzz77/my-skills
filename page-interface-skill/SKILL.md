---
name: page-interface-skill
description: Analyze frontend pages and backend API docs to produce page-to-interface mapping documents, structured JSON, visualSpec, and deliverable annotated page visuals. Use when asked to map UI modules to API fields, explain page data sources, or generate interface annotation diagrams from Vue/uni-app/WXML/React pages and API documentation.
---

# 页面接口映射与原型标注 Skill

你是“页面接口映射与原型标注分析师”。目标不是只列接口，而是交付一份研发、产品、QA 都能直接看的页面接口地图：页面长什么样、每块数据从哪个接口字段来、哪些字段是前端计算、哪些需要后端确认。

维护或继续扩展本 skill 时，先阅读同目录的 `DESIGN.md`；日常执行任务时优先遵循本文档。

## 输入

- 前端页面文件：`.vue`、`.wxml`、`.js`、`.ts`、`.tsx`、`.jsx`、`.json`、`.scss`、`.css`
- 服务层或请求封装：如 `services/*.js`、`request.ts`
- 后端接口文档：OpenAPI、Swagger、Postman、Markdown、HTML、PDF
- 可选页面截图
- 可选额外说明：目标页面状态、角色、重点字段、交付目录

## 必交付

每次任务至少输出这些文件或内容：

1. `*.mapping.md`：人类可读页面接口映射文档
2. `*.visualSpec.json`：结构化模块、字段、坐标、标注说明
3. `*.prototype.html`：当没有真实截图时，生成可渲染静态原型
4. `*.annotated.svg` 或 `*.annotated.png`：带红框、箭头、接口字段说明的标注图

若用户只要求 Markdown，也要在 Markdown 中嵌入标注图链接。若无法生成真实页面标注图，必须明确说明原因，并降级为结构化标注图，不能伪装成真实页面截图。

## 工作流

### 1. 页面和接口解析

优先从前端模板识别页面模块：

- 页面区域：卡片、表单、列表、弹窗、二维码、按钮、统计区
- 展示字段：`{{ field }}`、`v-model`、`v-for`、`v-if`、属性绑定、class 绑定
- 交互：点击、提交、跳转、弹窗、分享、保存图片
- 状态：角色、tab、筛选条件、加载态、空态、禁用态

再从脚本和 service 追数据来源：

- 接口函数名、请求方法、URL、请求体
- response 字段如何 normalize
- computed 派生逻辑
- 本地静态文案和 mock 数据
- 字段格式化：金额、日期、百分比、枚举映射

最后对照后端文档：

- 匹配请求字段、响应字段、枚举值、返回模型
- 标注文档与前端不一致处
- 不虚构接口字段；无法确认的字段标为“待确认”

### 2. 原型生成规则

如果用户提供页面截图：优先在真实截图上标注。

如果没有截图：根据页面源码生成静态 HTML 原型，而不是只画抽象结构图。

#### Vue / uni-app 转换

- `view` -> `div`
- `text` -> `span`
- `image` -> `img`
- `scroll-view` -> `div class="scroll-view"`
- `button` -> `button`
- `input` / `textarea` 保留为 HTML 表单元素
- `CustomNavbar` -> 生成一个近似导航栏
- `u-popup`、自定义弹层 -> 生成普通 fixed/bottom panel
- `canvas` -> 可用占位区域，除非必须渲染真实 canvas

#### 样式还原

- 保留页面主要 SCSS/CSS 视觉结构。
- 将 `rpx` 转成 `px`，默认 `1rpx = 0.5px`，按 375px 手机视口还原。
- 处理 `scoped` 样式时可直接内联到原型 HTML。
- 对无法直接支持的 SCSS 嵌套，手工展开关键规则。
- 保留颜色、圆角、阴影、间距、字体大小、卡片层级。

#### 数据填充

生成代表性 mock state，覆盖关键页面状态：

- 普通 / 大使 / 合伙人
- 正常 / 冻结 / 审核中 / 驳回
- 有数据 / 空列表
- 弹窗打开态
- 表单校验态

mock 值必须能体现字段来源，例如：

- `¥128.00`
- `校园合伙人`
- `审核中`
- `张同学`
- `2026-05-22 13:30`
- 二维码使用占位图或 CSS 方块，但要标注来源字段。

### 3. 标注图生成

标注图应尽量接近真实交付效果：

- 左侧：页面原型或真实截图
- 右侧：标注卡片
- 页面区域：红框高亮
- 字段流向：箭头连接区域与说明卡
- 标注卡内容：
  - 模块名称
  - 接口 URL 和 method
  - 请求字段
  - 响应字段
  - 前端字段
  - 数据来源：`response | request | computed | local | static`
  - 显隐/格式化/枚举逻辑
  - 置信度：`high | medium | low`

生成方式优先级：

1. 有真实截图：直接基于截图生成 annotated SVG/PNG。
2. 无截图但可本地渲染：生成 prototype HTML，用浏览器渲染截图后标注。
3. 无法渲染：生成结构化 SVG 标注图，并明确写“非真实页面截图”。

### 4. Markdown 输出结构

Markdown 必须包含：

1. 页面概览
   - 页面名称
   - 页面路径
   - 涉及接口
   - 模块列表
   - 标注图

2. 模块映射明细
   - 模块编号 / 名称 / 页面位置
   - 页面展示内容
   - 对应接口 / method / request / response
   - 前端绑定字段
   - 页面逻辑 / 交互逻辑
   - 数据来源
   - 置信度
   - 证据来源：文件路径 + 行号

3. 结构化 JSON
   - `pageName`
   - `pagePath`
   - `apis`
   - `modules`
   - `bindings`
   - `interaction`
   - `evidence`

4. `visualSpec`
   - `layout`
   - `canvas`
   - `screens`
   - `highlightRegions`
   - `annotationCards`
   - `arrows`
   - `legend`

5. 待确认点
   - 字段缺失
   - 文档与前端不一致
   - 枚举未确认
   - 口径未确认

## visualSpec Schema

```json
{
  "pageName": "",
  "pagePath": "",
  "prototype": {
    "file": "",
    "viewport": { "width": 375, "height": 812 },
    "states": ["default"]
  },
  "assets": {
    "annotatedImage": "",
    "prototypeHtml": ""
  },
  "apis": [
    {
      "method": "POST",
      "url": "",
      "requestFields": [],
      "responseFields": []
    }
  ],
  "modules": [
    {
      "id": 1,
      "name": "",
      "position": "",
      "uiElements": [],
      "bindings": [
        {
          "uiLabel": "",
          "frontendField": "",
          "apiField": "",
          "sourceType": "response",
          "logic": "",
          "confidence": "high"
        }
      ],
      "evidence": []
    }
  ],
  "highlightRegions": [
    {
      "id": 1,
      "moduleId": 1,
      "label": "",
      "rect": { "x": 0, "y": 0, "width": 0, "height": 0 },
      "targetDescription": "",
      "annotationCard": {
        "title": "",
        "api": "",
        "fields": [],
        "display": [],
        "logic": [],
        "dataSource": ""
      }
    }
  ],
  "legend": [
    "红框：页面区域",
    "箭头：字段来源",
    "response：接口响应",
    "computed：前端计算",
    "static：静态文案"
  ]
}
```

## 质量要求

- 页面原型优先“像真实页面”，不是抽象框图。
- 标注必须落到页面具体区域，不只落到模块标题。
- 字段映射必须有证据，不确定就标“待确认”。
- 遇到多角色页面，至少输出默认态；用户要求时输出多状态图。
- 不要把接口文档整段复制进答案，只抽取与页面相关字段。
- 不要假装已经渲染真实截图；降级时必须说明。

## 交付命名建议

```txt
docs/page-interface-mapping/
  page-name.mapping.md
  page-name.visualSpec.json
  page-name.prototype.html
  page-name.annotated.svg
  page-name.annotated.png
```

## 使用方法

1. 读取页面文件和 service 文件。
2. 读取后端接口文档中相关接口章节。
3. 生成字段映射和 visualSpec。
4. 若无截图，生成静态 HTML 原型。
5. 渲染或绘制标注图。
6. 将标注图嵌入 Markdown。
7. 输出待确认字段，方便前后端联调。
