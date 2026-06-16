#!/usr/bin/env python3
"""
配置校验器 — v0.1

每次技能启动时, 必须先通过本模块的校验才能继续.
校验范围:
  - config.json (imap / feishu 节)
  - rules.json (存在 + 合法 JSON)
  - lark-cli (可选: 已安装 + 已授权)
  - Python 依赖 (pdfplumber)

Usage:
    python3 validate_config.py [--json] [--quiet]

Exit codes:
  0  全部通过
  1  有 warning (不阻塞, 但建议修复)
  2  有 error (阻塞, 必须修复)
"""

import sys
import json
import shutil
import subprocess
from pathlib import Path
from typing import Optional

sys.path.insert(0, str(Path(__file__).resolve().parent))
from storage import Storage  # noqa: E402


# ---------- 校验结果结构 ----------

class Issue:
    def __init__(self, field: str, message: str, severity: str = "error",
                 fix_hint: str = ""):
        self.field = field
        self.message = message
        self.severity = severity  # error | warning
        self.fix_hint = fix_hint

    def to_dict(self):
        d = {"field": self.field, "message": self.message, "severity": self.severity}
        if self.fix_hint:
            d["fix_hint"] = self.fix_hint
        return d


class ValidationResult:
    def __init__(self):
        self.issues: list[Issue] = []

    @property
    def errors(self) -> list[Issue]:
        return [i for i in self.issues if i.severity == "error"]

    @property
    def warnings(self) -> list[Issue]:
        return [i for i in self.issues if i.severity == "warning"]

    @property
    def ok(self) -> bool:
        return len(self.errors) == 0

    def add(self, field: str, message: str, severity: str = "error",
            fix_hint: str = ""):
        self.issues.append(Issue(field, message, severity, fix_hint))
        return self

    def to_dict(self):
        return {
            "ok": self.ok,
            "errors": [i.to_dict() for i in self.errors],
            "warnings": [i.to_dict() for i in self.warnings],
        }


# ---------- 各节校验 ----------

def _check_emailish(s: str) -> bool:
    """粗略检查是否像邮箱地址."""
    return "@" in s and len(s) <= 254 and "\x00" not in s


def _validate_imap(imap_cfg: dict, result: ValidationResult):
    """校验 config.json imap 节."""
    if not imap_cfg or not isinstance(imap_cfg, dict):
        result.add("imap", "config.json 缺少 'imap' 节.",
                   fix_hint="在 config.json 中添加 imap 配置 (参考 skill/assets/rules.example.json 中的说明)")
        return

    for key in ("host", "account", "password"):
        if not imap_cfg.get(key):
            result.add(f"imap.{key}",
                       f"IMAP {key} 缺失或为空.",
                       fix_hint=f"填入你的邮箱 {key}")

    # port
    port = imap_cfg.get("port")
    if port is not None:
        try:
            p = int(port)
            if not (1 <= p <= 65535):
                result.add("imap.port", f"IMAP port 不在合法范围: {p}",
                           fix_hint="通常 IMAP SSL 用 993, 非 SSL 用 143")
        except (TypeError, ValueError):
            result.add("imap.port", f"IMAP port 不是合法整数: {port!r}",
                       fix_hint="通常 IMAP SSL 用 993, 非 SSL 用 143")

    # account
    account = imap_cfg.get("account", "")
    if account and not _check_emailish(account):
        result.add("imap.account", f"IMAP 账号不像邮箱地址: {account!r}",
                   severity="warning", fix_hint="确认邮箱地址是否完整")

    # senders
    senders = imap_cfg.get("senders")
    if not senders:
        result.add("imap.senders", "IMAP 发件人列表为空. 至少需要 1 个发件人地址.",
                   fix_hint="在 config.json imap.senders 中添加高德发票发件人, "
                            "如 itinerary@ridesharing.amap.com")
    elif isinstance(senders, list):
        for s in senders:
            if not _check_emailish(str(s)):
                result.add("imap.senders", f"发件人地址不像邮箱: {s!r}",
                           severity="warning")
    elif isinstance(senders, str):
        if not _check_emailish(senders):
            result.add("imap.senders", f"发件人地址不像邮箱: {senders!r}",
                       severity="warning")
    else:
        result.add("imap.senders",
                   f"senders 类型不合法: {type(senders).__name__} (应为 list 或 string)")


def _validate_feishu(feishu_cfg: dict, result: ValidationResult):
    """校验 config.json feishu 节.

    当前主流程为直接提交费用报销，不再强制要求旧的采购申请
    definition_code / purchase_entity 配置。
    """
    if not feishu_cfg or not isinstance(feishu_cfg, dict):
        result.add("feishu", "config.json 缺少 'feishu' 节.",
                   fix_hint="在 config.json 中添加 feishu 配置. "
                            "需要: expense_definition_code, user_id, "
                            "reimburse_entity.key/text, expense_type.key/text")
        return

    if not feishu_cfg.get("user_id"):
        result.add("feishu.user_id",
                   "飞书 user_id 缺失.",
                   fix_hint="从已通过的审批实例获取 user_id, 或用 lookup-open-id 反查")

    if not feishu_cfg.get("expense_definition_code"):
        result.add("feishu.expense_definition_code",
                   "费用报销 expense_definition_code 缺失.",
                   fix_hint="从飞书审批后台获取费用报销流程的 definition_code")

    entity = feishu_cfg.get("reimburse_entity") or feishu_cfg.get("purchase_entity")
    if not entity or not isinstance(entity, dict):
        result.add("feishu.reimburse_entity",
                   "飞书报销主体配置缺失.",
                   fix_hint="添加 reimburse_entity: {key: '...', text: '...'} 到 feishu 节")
    else:
        for ek in ("key", "text"):
            if not entity.get(ek):
                result.add(f"feishu.reimburse_entity.{ek}",
                           f"报销主体 {ek} 缺失.",
                           fix_hint="从已通过的费用报销表单中获取 option key 和显示文本")

    expense_type = feishu_cfg.get("expense_type")
    if not expense_type or not isinstance(expense_type, dict):
        result.add("feishu.expense_type",
                   "飞书费用类型配置缺失.",
                   fix_hint="添加 expense_type: {key: '...', text: '差旅费-打车费'} 到 feishu 节")
    else:
        for ek in ("key", "text"):
            if not expense_type.get(ek):
                result.add(f"feishu.expense_type.{ek}",
                           f"费用类型 {ek} 缺失.",
                           fix_hint="从已通过的费用报销表单中获取 option key 和显示文本")

    dept = feishu_cfg.get("department_id")
    if dept is not None and not isinstance(dept, str):
        result.add("feishu.department_id",
                   "department_id 应为 string 或留空.",
                   severity="warning")

    # 验证 app_id + app_secret 能获取 tenant token
    app_id = feishu_cfg.get("app_id")
    app_secret = feishu_cfg.get("app_secret")
    if not app_id or not app_secret:
        result.add("feishu.app_credentials",
                   "feishu.app_id / app_secret 缺失 (工作流所需, 用于自动获取 tenant token).",
                   fix_hint="去飞书开放平台后台拷贝 App ID 和 App Secret 填入 config.json feishu 节")
    else:
        try:
            sys.path.insert(0, str(Path(__file__).resolve().parent))
            from feishu_upload import get_tenant_access_token, UploadError
            get_tenant_access_token(app_id, app_secret)
        except Exception as e:
            result.add("feishu.app_credentials",
                       f"app_id/app_secret 无法获取 tenant_access_token: {e}",
                       fix_hint="确认 App ID 和 App Secret 填写正确, 且应用已启用")


def _validate_rules(storage: Storage, result: ValidationResult):
    """校验 rules.json."""
    path = storage.rules_path
    if not path.exists():
        result.add("rules.json",
                   f"rules.json 不存在 ({path}).",
                   fix_hint="运行: python3 cli.py init 会自动复制模板")
        return

    try:
        cfg = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as e:
        result.add("rules.json", f"rules.json 不是合法 JSON: {e}",
                   fix_hint="检查 JSON 语法, 或重新运行 init --force")
        return

    # 基础字段检查
    if not cfg.get("buyer", {}).get("company_name"):
        result.add("rules.buyer.company_name", "报销公司名缺失.",
                   severity="warning",
                   fix_hint="在 rules.json buyer.company_name 中填入公司全称")
    if not cfg.get("buyer", {}).get("tax_id"):
        result.add("rules.buyer.tax_id", "报销公司税号缺失.",
                   severity="warning",
                   fix_hint="在 rules.json buyer.tax_id 中填入公司税号")

    location = cfg.get("location", {})
    ep_match = location.get("endpoint_match", {})
    keywords = ep_match.get("keywords") or []
    if ep_match.get("mode") == "origin_in":
        if not keywords:
            result.add("rules.location.endpoint_match.keywords",
                       "起点校验已启用 但关键词列表为空.",
                       severity="warning",
                       fix_hint="在 rules.json location.endpoint_match.keywords 中添加至少一个允许的出发点")
        elif any(str(k).startswith("<") for k in keywords):
            result.add("rules.location.endpoint_match.keywords",
                       f"起点关键词含占位符未替换: {keywords}",
                       severity="warning",
                       fix_hint="运行 onboard 或手动编辑 rules.json 替换 <your-departure-location>")


def _validate_lark_cli(result: ValidationResult):
    """校验可选的 lark-cli 是否安装并已授权."""
    if not shutil.which("lark-cli"):
        result.add("lark-cli", "lark-cli 未安装.",
                   severity="warning",
                   fix_hint="安装: npm install -g @anthropic/lark-cli (或你的安装方式)")
        return

    try:
        proc = subprocess.run(
            ["lark-cli", "auth", "status"],
            capture_output=True, text=True, timeout=10,
        )
    except FileNotFoundError:
        result.add("lark-cli", "lark-cli 命令不可用 (FileNotFound).",
                   severity="warning")
        return
    except subprocess.TimeoutExpired:
        result.add("lark-cli", "lark-cli auth status 超时.",
                   severity="warning")
        return

    if proc.returncode != 0:
        result.add("lark-cli",
                   "lark-cli 未授权或未初始化.",
                   severity="warning",
                   fix_hint="运行: lark-cli config init --new && lark-cli auth login --domain approval")
        return

    try:
        status = json.loads(proc.stdout)
    except json.JSONDecodeError:
        result.add("lark-cli", "lark-cli auth status 返回非 JSON.",
                   severity="warning")
        return

    if status.get("tokenStatus") != "valid":
        result.add("lark-cli",
                   "lark-cli token 已过期 (onboard 时需要, 工作流使用 app_id/secret 自动续期).",
                   severity="warning",
                   fix_hint="如需重新引导配置, 运行: lark-cli auth login --domain approval")


def _validate_python_deps(result: ValidationResult):
    """校验 Python 依赖."""
    try:
        import pdfplumber  # noqa: F401
    except ImportError:
        result.add("pdfplumber", "pdfplumber 未安装.",
                   fix_hint="运行: pip3 install pdfplumber")


# ---------- 主入口 ----------

def validate(storage: Storage = None) -> ValidationResult:
    """全量校验, 返回 ValidationResult."""
    if storage is None:
        storage = Storage()
    result = ValidationResult()

    # 0. config.json 是否存在且合法
    if not storage.config_path.exists():
        result.add("config.json",
                   f"config.json 不存在 ({storage.config_path}).",
                   fix_hint="运行: python3 cli.py init 然后编辑配置文件")
    else:
        try:
            config = storage.load_config()
        except (json.JSONDecodeError, RuntimeError) as e:
            result.add("config.json", f"config.json 解析失败: {e}",
                       fix_hint="检查 JSON 语法")
            config = {}

        _validate_imap(config.get("imap"), result)
        _validate_feishu(config.get("feishu"), result)

    # 1. rules.json
    _validate_rules(storage, result)

    # 2. lark-cli
    _validate_lark_cli(result)

    # 3. python deps
    _validate_python_deps(result)

    return result


# ---------- CLI ----------

def main():
    import argparse
    ap = argparse.ArgumentParser(
        description="校验发票报销 Skill 的配置是否就绪."
    )
    ap.add_argument("--json", action="store_true", help="JSON 输出")
    ap.add_argument("--quiet", action="store_true", help="通过时不输出")
    args = ap.parse_args()

    result = validate()

    if args.json:
        json.dump(result.to_dict(), sys.stdout, ensure_ascii=False, indent=2)
        sys.stdout.write("\n")
    elif not args.quiet or not result.ok:
        for i in result.errors:
            print(f"  [ERROR] {i.field}: {i.message}")
            if i.fix_hint:
                print(f"          -> {i.fix_hint}")
        for i in result.warnings:
            print(f"  [WARN]  {i.field}: {i.message}")
            if i.fix_hint:
                print(f"          -> {i.fix_hint}")
        if result.ok:
            print("  配置校验通过.")

    sys.exit(0 if result.ok else 2)


if __name__ == "__main__":
    main()
