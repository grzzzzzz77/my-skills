# lark-cli 命令速查

> 本文档记录发票报销自动化中用到的飞书 CLI 命令。Agent 在需要与飞书交互时按需读取。

---

## 环境准备

```bash
# 安装并配置应用
lark-cli config init --new

# 用户授权（首次使用）
lark-cli auth login --domain approval,drive
```

**必需的应用身份权限（bot 权限，在飞书开放平台后台配置）：**
- `approval:approval` — 审批应用管理
- `approval:instance` — 创建、查看审批实例
- `approval:task` — 审批任务操作（预留）
- `approval:instance.comment` — 审批评论（可选）

---

## 文件上传

### 上传审批附件

```bash
lark-cli api POST '/open-apis/approval/v4/files/upload' \
  --as bot \
  --file './xxx.pdf' \
  --params '{"name": "文件名.pdf", "type": "attachment"}'
```

- `type` 取值: `image` 或 `attachment`。PDF 用 `attachment`。
- 返回的 `data.urls_detail[0].code` 即为文件 code，用于审批表单的 `attachmentV2` widget。

### 文件 code 格式

返回示例：
```json
{
  "code": 0,
  "data": {
    "urls_detail": [
      {
        "code": "A8C94490-51A0-4E04-9B8E-D8DD9D20CF91",
        "url": "https://..."
      }
    ]
  }
}
```

---

## 审批实例

### 创建审批实例

```bash
lark-cli api POST '/open-apis/approval/v4/instances/create' \
  --as bot \
  --data '{
    "definition_code": "<模板code>",
    "user_id": "<user_open_id>",
    "department_id": "<dept_open_id>",
    "form": "<form JSON 字符串>"
  }'
```

- `form` 是 JSON 字符串（不是对象），需要 `json.dumps()` 序列化。
- `attachmentV2` widget 的值是文件 code 字符串数组，如 `["code1", "code2"]`。

### 查询审批实例详情

```bash
lark-cli api GET '/open-apis/approval/v4/instances/<instance_code>' --as user
```

- 只能使用 user token（`--as user`），bot 不支持此 API。
- 返回的 `data.status` 可能值: `APPROVED`, `REJECTED`, `PENDING`。

---

## 当前审批模板信息

| 字段 | 值 |
|------|-----|
| 模板名称 | 采购申请 |
| `definition_code` | `868B710A-A742-45EE-9E6D-C61D0BF5963F` |
| 用户 Open ID | `ou_5ccb7186857489d79262b168fbd0876a` |
| 部门 ID | `od-01b9d982e94ee8a22bc737bd20ab493f` |
| 采购主体 option key | `mp3dpnnw-07gunm764bby-0` (找北智职) |

### 表单 Widget 映射

| Widget ID | 名称 | 类型 | 说明 |
|-----------|------|------|------|
| `widget16510608596030001` | 采购事由 | textarea | 报销原因文本 |
| `widget17786355991160001` | 采购主体 | radioV2 | 固定选"找北智职" |
| `widget16510608918180001` | 期望采购时间 | date | 当天日期 |
| `widget16510609006710001` | 费用明细 | fieldList | 子表单数组 |
| ↳ `widget16510609105290001` | 物品/服务名称 | input | "打车费" |
| ↳ `widget16510609161480001` | 规格型号 | input | "无" |
| ↳ `widget16510609215120001` | 数量 | number | 发票数量 |
| ↳ `widget16510609358260001` | 金额 | amount | 合计金额 |
| ↳ `widget17638204676490001` | 说明 1 | text | 行程摘要 |
| `widget16510609389860001` | 附件 | attachmentV2 | 文件 code 数组 |

---

---

## 费用报销审批模板信息（流程2）

| 字段 | 值 |
|------|-----|
| 模板名称 | 费用报销 |
| `definition_code` | `FAB04EBA-8365-46CA-B273-2F9CF1355460` |
| 用户 Open ID | 同流程1：`ou_5ccb7186857489d79262b168fbd0876a` |
| 部门 ID | 同流程1：`od-01b9d982e94ee8a22bc737bd20ab493f` |

### 表单 Widget 映射（已从真实实例提取）

| Widget ID | 名称 | 类型 | 填写值 |
|-----------|------|------|--------|
| `widget16510509704570001` | 报销事由 | textarea | `"打车"` |
| `widget17655881349660001` | 关联审批 | connect | 流程1 `instance_code` 字符串数组 |
| `widget17786605192630001` | 公司主体 | radioV2 | option key `mp3sjs68-qm8docs1rm-0`（找北智职） |
| `widget17786605494580001` | 费用明细 | fieldList | 每张发票一行，见下表 |
| ↳ `widget17641551707250001` | 费用类型 | radioV2 | option key `mifwftlx-gqbji2uoe7-0`（差旅费-打车费） |
| ↳ `widget17641645253820001` | 费用发生时间 | date | 提交当天 `YYYY-MM-DDT00:00:00+08:00` |
| ↳ `widget17641648377750001` | 费用金额 | amount | 该发票金额 |
| ↳ `widget16510510447300001` | 发票/账单/支付记录 | attachmentV2 | 该发票 + 行程单 PDF file codes |

> 注意：`widget17786607354690001`（说明1）是只读提示文本，提交时不需要包含。

### 多发票提交规则

- **一个费用报销实例** 包含所有待报销发票（费用明细 fieldList 多行）
- 每行明细独立对应一张发票：当张金额、当张两个 PDF（发票+行程单）
- `关联审批（connect）` 字段值是数组，填流程1的 `instance_code`

---

## 常见问题

- **99991672 Permission denied**: 检查飞书开放平台后台 → 应用身份权限是否已添加所需 scope 并发布新版本
- **99991668 user access token not support**: 该 API 不支持 user token，改用 `--as bot`
- **1390001 Parameter type is empty/invalid**: 审批文件上传需要 `--params` 里指定 `type` (image/attachment)
