---
name: invoice-reimbursement
description: Automate Feishu taxi-invoice reimbursement (v0.1, Amap / 高德打车 only). Use when the user wants to process today's 高德 taxi invoices, submit reimbursement, or continue a reimbursement after the first Feishu approval has passed. Flow runs in two conversations — first to read email, parse PDFs and submit the first approval; second (after user receives Feishu "approved" notification) to verify and submit the second approval.
---

# Invoice Reimbursement Skill

> v0.1 — 高德打车发票 → 飞书双审批报销自动化

## Version & Supported Platforms

**Current version: v0.1**

✅ **Supported**
- 高德打车（AMAP）开具的"旅客运输服务"类电子普通发票（包含 T3 出行 / 喜行约车 / 招招出行 / 鞍马出行 / 高德平台下挂的其他承运方）
- 高德地图打车的电子行程单（AMAP ITINERARY）

❌ **Not supported in v0.1**
- 滴滴出行、首汽约车、神州专车、出租车票等**其他打车平台**的发票或行程单
- 增值税专用发票、纸质发票
- 餐饮、住宿、办公等非客运类发票
- 飞书邮箱（暂仅支持通用 IMAP）

如果传入的 PDF 不是高德格式，`scripts/parse_invoices.py` / `scripts/parse_trips.py` 会立即抛出 `ParseError` 并退出（非零退出码），不会静默产出错误数据。

## When to use

用户表达类似意图时调用：
- "处理一下今天的打车发票"、"提交报销"
- "第一个审批通过了，继续走第二步"
- 首次使用 / 配置缺失时也通过本 skill 进入引导

## Prerequisites

- `~/.invoice-reimbursement/config.json` 存在且通过 `scripts/validate_config.py` 全量校验
- `~/.invoice-reimbursement/rules.json` 存在且合法
- `python3` / `pdfplumber` 已安装
- 飞书应用凭证: `feishu.app_id` + `feishu.app_secret` 能换到 `tenant_access_token` (校验器会实测)
- `lark-cli` **可选**: 现在 onboard 内置 `lookup-open-id` 已可用手机号自助反查 `user_open_id`, 工作流主路径全程不依赖 lark-cli

> **鉴权说明**: 工作流全程使用 tenant token (App 身份), 2 小时自动续期, 永远不需要浏览器重新授权。
> 只要 `app_secret` 不变, 整个流程不需要任何人工干预。

**每次执行工作流脚本前，Agent 必须先调用 `python3 validate_config.py --json` 做预检。**
预检不通过则拒绝继续，向用户汇报缺失项及修复建议，并引导运行 `onboard` 或手动编辑 config.json。

> CLI 子命令（除 init/status/validate/onboard 外）已内置自动预检，不通过会拒绝执行。Agent 显式再跑一次 validate 是为了**提前给出清晰的修复指引**，而不是让用户看到干巴巴的 exit 2。

## Config validation (每次工作流必做)

```bash
python3 scripts/validate_config.py --json
```

校验范围：
- `config.json`：imap 节 (host/port/account/password/senders)、feishu 节 (definition_code/user_id/purchase_entity.key/app_id/app_secret)
- `rules.json`：存在 + 合法 JSON + 必要字段 (buyer.company_name/tax_id)
- `feishu.app_id` + `app_secret`：**实测能换到 tenant_access_token** (工作流硬性依赖)
- `lark-cli`：可选 warning — 没有也行, onboard 现在自带 `lookup-open-id` 用手机号反查
- Python 依赖：pdfplumber 可 import

如果 `ok: false`，向用户展示所有 errors 的 `message` + `fix_hint`，**退出码 2 阻断流程**。

## High-level flow

### 第一次对话：读邮件 → 解析 → 提交第一个审批

1. **运行配置预检**：`python3 scripts/validate_config.py --json`，不通过则阻断并引导修复
2. **抓取邮件附件**：`python3 scripts/cli.py fetch [--days N] [--since YYYY-MM-DD]`
   - 从 IMAP 下载今日（默认）高德发票 + 行程单 PDF 到 `~/.invoice-reimbursement/tmp/`
3. **解析配对筛选**：`python3 scripts/cli.py parse`
   - 解析 PDF → 按金额配对 → 规则筛选 → history 去重 → 写入 `state.json`
   - 如果全被跳过，告知原因并结束
4. **生成采购事由草稿**：`python3 scripts/cli.py submit-1 --generate-reason-draft`
   - 根据行程单数据自动生成事由文本，展示给用户确认
   - 用户可补充修改（如添加项目名称、工作内容等）
5. **确认报销事由（必问）**：在正式提交前，Agent 必须问用户："这次报销事由写什么？"
   - 这是飞书第二个审批「费用报销」里的 `报销事由` 字段，不能再默认写 `"打车"`
   - 用户确认后，后续命令必须通过 `--reimbursement-reason "用户确认的报销事由"` 传入
   - M3 会把该值写入 `state.json`，供后台 watcher 在第一审批通过后自动提交 M4 时使用
6. **提交第一个审批**：`python3 scripts/cli.py submit-1 --reason "用户确认的采购事由" --reimbursement-reason "用户确认的报销事由"`
   - 上传发票+行程单 PDF（v2 endpoint，保证附件正常显示）
   - 组装采购申请表单（每张发票一行 fieldList，数量固定 1）
   - 创建飞书审批实例，回填 `first_approval_id` 和 `reimbursement_reason` 到 state.json
   - 建议先 `--dry-run` 预览表单再正式提交
7. **汇报结果**：提交了 N 条、合计金额、instance_code
   - 提示用户等待飞书"审批通过"通知后再次触发

### 第二次对话：验证 → 提交第二个审批

> **自动接力**: M3 提交完成时已自动启动后台 watcher (1 小时轮询)，**通常无需手动跑 submit-2**。
> 第一审批通过后 watcher 会自动触发 M4，结果写入 state.json + watcher.log。
> 重启电脑会导致 watcher 失效, 此时手动跑 submit-2 兜底。

1. **(可选) 查询 watcher 状态**: `python3 scripts/cli.py watcher-status`
2. **手动触发 (兜底)**: `python3 scripts/cli.py submit-2 [--reimbursement-reason "用户确认的报销事由"] [--dry-run]`
   - 自动查询第一个审批状态：
     - `APPROVED` → 上传 PDF → 创建费用报销审批 → 写 history.json → 清理 tmp/
     - `REJECTED` → 标记 rejected，告知用户
     - `PENDING` → 跳过，告知用户仍在审批中
   - 如果 `state.json` 里没有 M3 保存的 `reimbursement_reason`，或者用户想覆盖原事由，必须先询问用户并传入 `--reimbursement-reason`
3. **汇报结果**：second_instance_code、完成条数、合计金额

### 首次使用引导

`python3 scripts/cli.py onboard` — 交互式逐项收集缺失配置，写入 `~/.invoice-reimbursement/config.json`。
其中 `feishu.user_id` (open_id) 支持**直接输入手机号自动反查**，背后调用 `lookup-open-id`。

也可以独立查 open_id（无需进入 onboard）：
```bash
python3 scripts/cli.py lookup-open-id --mobile 13800138000
python3 scripts/cli.py lookup-open-id --email someone@example.com --json
```

配置模板参考 `assets/config.example.json`，飞书审批字段映射参考 `references/lark-cli-cheatsheet.md`。

## Files

| 文件 | 作用 |
|------|------|
| `scripts/validate_config.py` | **入口守卫** — 全量校验 config/rules/lark-cli/deps |
| `scripts/init_storage.py` | 初始化 `~/.invoice-reimbursement/` 目录 |
| `scripts/storage.py` | JSON 文件读写工具（原子写、Storage API） |
| `scripts/fetch_emails.py` | M1 — IMAP 邮件抓取 + PDF 附件下载 |
| `scripts/parse_invoices.py` | 解析高德发票 PDF（含 NFKC Unicode 归一化） |
| `scripts/parse_trips.py` | 解析高德行程单 PDF（多行程兼容） |
| `scripts/pair_pdfs.py` | 发票 ↔ 行程单按金额配对 |
| `scripts/rules.py` | 规则引擎（company/tax/location/time/amount） |
| `scripts/parse_and_filter.py` | M2 编排器（pair → rules → history → state） |
| `scripts/feishu_upload.py` | 飞书 v2 endpoint 文件上传（解决 v4 上传显示 "unknown-file"） |
| `scripts/submit_first_approval.py` | M3 — 上传附件 + 创建采购申请审批 + 保存报销事由 + spawn watcher |
| `scripts/submit_second_approval.py` | M4 — 查询第一审批状态 + 创建费用报销审批，并填入用户确认的报销事由 |
| `scripts/approval_watcher.py` | 后台守护 — M3 后 1h 轮询审批状态, APPROVED 自动触发 M4 |
| `scripts/lookup_open_id.py` | 通过手机号/邮箱反查 user_open_id (onboard 内置 + 独立子命令) |
| `scripts/cli.py` | CLI 统一入口（init/status/validate/onboard/fetch/parse/submit-1/submit-2/watcher-status/watcher-stop/lookup-open-id） |
| `references/lark-cli-cheatsheet.md` | lark-cli 命令速查、双审批表单字段映射 |
| `assets/config.example.json` | 配置模板（IMAP + 飞书 + 规则） |
| `assets/rules.example.json` | 报销规则模板（公司/税号/起终点/时间窗口/金额上限） |

## Error handling 要点

- **IMAP 认证失败** → 提示重新配置邮箱密码（QQ 邮箱需授权码）
- **无匹配邮件** → 告知"今天没有需要报销的发票"
- **PDF 解析失败** → 跳过该条并告知文件名，不因单条阻断整批
- **规则筛选不通过** → 写入 skipped[] 并列出 skip_reason
- **tenant token 获取失败** → 检查 `feishu.app_id` / `app_secret` 是否正确, 应用是否启用
- **lark-cli 401** (仅 onboard 时遇到) → 提示重新 `lark-cli auth login --domain approval,drive`; 工作流主路径不受影响
- **审批被拒绝** → 标记 rejected，**不**写 history，允许后续重新提交
- **radioV2 字段** → value 必须用 option key 而非显示文本，否则飞书返回 1390001

---

需求定义见工作区 `docs/spec.md`，阶段计划见 `docs/plan.md`，待办见 `docs/todo.md`。
