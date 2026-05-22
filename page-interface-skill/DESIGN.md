# page-interface-skill v2 设计文档

## 目标

把 `page-interface-skill` 从“接口字段映射文档生成器”升级为“页面原型 + 接口标注交付器”。

升级后的效果应该是：

1. 读取 Vue / uni-app / WXML / React 页面源码。
2. 读取 service 请求代码和后端接口文档。
3. 分析页面模块、展示字段、接口字段、前端计算逻辑。
4. 在没有真实截图时，根据页面代码生成接近真实页面的静态 HTML 原型。
5. 把原型渲染成图片或 SVG。
6. 在页面区域上画红框、箭头和接口字段说明卡片。
7. 输出可交付 Markdown，里面嵌入标注图、字段表、JSON 和待确认点。

## 为什么要升级

原来的 skill 可以说明“字段来自哪里”，但可视化只停留在 `visualSpec` 或结构图。

真正用于联调时，研发、产品、QA 更需要看到：

- 页面上这块区域是什么；
- 它展示了哪些字段；
- 字段来自哪个接口；
- 哪些是接口原始字段，哪些是前端 computed；
- 哪些展示受状态控制；
- 哪些字段后端文档缺失或口径不一致。

因此 v2 的核心价值是：**把页面视觉和接口字段绑定在同一个可交付图里。**

## 新的交付物

建议每次输出到类似目录：

```txt
docs/page-interface-mapping/
  page-name.mapping.md
  page-name.visualSpec.json
  page-name.prototype.html
  page-name.annotated.svg
  page-name.annotated.png
```

其中：

- `mapping.md`：主交付文档。
- `visualSpec.json`：结构化标注数据，可复用生成图片。
- `prototype.html`：根据页面源码还原的静态原型。
- `annotated.svg/png`：带接口字段标注的页面图。

如果用户只要一个 Markdown 文件，也应该把标注图嵌入 Markdown。

## 处理流程

### 1. 输入解析

读取：

- 页面文件：`.vue`、`.wxml`、`.tsx`、`.jsx`
- 样式文件：`.scss`、`.css`、`.wxss`
- service 文件：接口 URL、method、请求体、normalize 逻辑
- 后端文档：接口路径、入参、响应字段、枚举、模型

分析页面模板里的：

- `{{ field }}`
- `v-if`
- `v-for`
- `v-model`
- `:class`
- `:src`
- `@tap`
- 表单字段
- 弹窗
- 列表
- 二维码
- 分享海报

### 2. 字段追踪

追踪路径：

```txt
页面展示字段
-> script 变量 / computed
-> service 方法
-> normalize 函数
-> 后端接口字段
-> 接口文档字段
```

字段来源类型：

- `response`：接口响应字段
- `request`：提交给后端的字段
- `computed`：前端计算字段
- `local`：本地状态
- `static`：静态文案或本地资源

### 3. 静态原型生成

如果没有真实截图，则从页面源码生成原型，而不是只画抽象框图。

uni-app 转 HTML 规则：

| uni-app / Vue | HTML 原型 |
| --- | --- |
| `view` | `div` |
| `text` | `span` |
| `image` | `img` |
| `scroll-view` | `div.scroll-view` |
| `CustomNavbar` | 自定义导航栏 div |
| `u-popup` | fixed 弹层 |
| `button` | button |
| `input` | input |
| `textarea` | textarea |

样式处理：

- `rpx` 默认按 `1rpx = 0.5px` 转换。
- 以 375px 手机宽度作为默认视口。
- 尽量保留颜色、字号、卡片、圆角、阴影和间距。
- SCSS 嵌套可以只展开关键选择器。
- 不能解析的复杂样式，以视觉近似为准。

### 4. Mock 数据生成

为了让页面看起来真实，需要生成 mock state。

例如分销页面：

```js
{
  roleName: '校园合伙人',
  statusText: '正常',
  name: '张同学 | 浙江大学',
  balance: '1280.00',
  pendingAmount: '120.00',
  withdrawableAmount: '860.00',
  monthRegisterCount: 36,
  monthOrderCount: 8,
  monthReward: '320.00'
}
```

mock 数据要覆盖关键状态：

- 正常
- 冻结
- 审核中
- 驳回
- 空列表
- 有列表
- 弹窗打开

### 5. 标注图生成

标注图布局建议：

```txt
┌──────────────────────┬───────────────────────────┐
│ 页面原型 / 截图       │ 标注卡片                   │
│ 红框圈出页面区域      │ 接口 URL / 字段 / 逻辑      │
│ 箭头指向右侧说明      │ response/computed/static    │
└──────────────────────┴───────────────────────────┘
```

每个标注卡包含：

- 模块名
- 页面位置
- 接口 URL
- method
- 请求字段
- 响应字段
- 前端绑定字段
- 显隐逻辑
- 格式化逻辑
- 置信度
- 证据来源

### 6. Markdown 输出

Markdown 结构：

```md
# 页面接口映射分析

## 可视化标注图

![](./page.annotated.png)

## 一、页面概览

## 二、模块映射明细

## 三、结构化 JSON

## 四、visualSpec

## 五、待后端确认点
```

## visualSpec 建议结构

```json
{
  "pageName": "分销中心",
  "pagePath": "src/pagesA/distribution/index.vue",
  "prototype": {
    "file": "distribution-index.prototype.html",
    "viewport": { "width": 375, "height": 812 },
    "states": ["partner-default"]
  },
  "assets": {
    "annotatedImage": "distribution-index.annotated.png",
    "prototypeHtml": "distribution-index.prototype.html"
  },
  "apis": [
    {
      "method": "POST",
      "url": "/api/campus-distribution/workspace",
      "requestFields": [],
      "responseFields": [
        "identityStatus.identityType",
        "incomeSummary.availableAmount"
      ]
    }
  ],
  "modules": [
    {
      "id": 1,
      "name": "身份收益卡",
      "position": "顶部蓝色卡片",
      "bindings": [
        {
          "uiLabel": "可提现",
          "frontendField": "distributionData.withdrawableAmount",
          "apiField": "incomeSummary.availableAmount",
          "sourceType": "computed",
          "logic": "formatDistributionAmount",
          "confidence": "high"
        }
      ]
    }
  ],
  "highlightRegions": [
    {
      "id": 1,
      "moduleId": 1,
      "rect": { "x": 20, "y": 72, "width": 335, "height": 150 },
      "annotationCard": {
        "title": "模块：身份收益卡",
        "api": "POST /api/campus-distribution/workspace",
        "fields": ["identityStatus", "incomeSummary"],
        "dataSource": "response+computed"
      }
    }
  ]
}
```

## 降级策略

1. 有真实截图：直接标真实截图。
2. 无截图但能生成原型：生成 HTML 原型并标注。
3. 无法渲染原型：生成结构化 SVG 标注图。

降级时必须写清楚：

```md
> 未提供页面截图，本图为根据源码生成的静态原型标注图。
```

或者：

```md
> 当前环境无法渲染页面原型，本图为结构化模块标注图，不代表真实页面截图。
```

## v2 验收标准

一份合格输出应满足：

- 能看到接近真实页面的布局。
- 每个主要模块都有红框。
- 每个红框都有接口字段说明。
- 字段来源明确区分 response / request / computed / static。
- 文档与前端不一致的地方单独列出。
- Markdown 中能直接看到图片。
- 生成物可以发给后端联调。

## 已更新的 skill 文件

```txt
/Users/Zhuanz/.codex/skills/page-interface-skill/SKILL.md
```

该路径是软链，实际文件位于：

```txt
/Users/Zhuanz/.skills-manager/skills/page-interface-skill/SKILL.md
```
