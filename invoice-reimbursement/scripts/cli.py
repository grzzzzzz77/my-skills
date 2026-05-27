#!/usr/bin/env python3
"""
Invoice Reimbursement Skill — CLI 入口  v0.1

子命令:
  init        初始化 ~/.invoice-reimbursement/ (复制规则模板, 建立空 state / history)
  status      打印当前 state.json + history.json 摘要
  validate    校验 config.json / rules.json / lark-cli 是否就绪
  onboard     交互式引导, 逐项填入缺失的配置
  fetch       M1: 从 IMAP 拉取发票邮件并下载 PDF 附件到 <storage>/tmp/
  parse       M2: 解析 PDF + 配对 + 应用规则 + 写入 state.json (调 parse_and_filter)
  submit-1    M3: 上传附件 + 提交飞书第一审批 (采购申请)
                  提交成功后自动 spawn 后台 watcher, 1h 轮询审批状态, 通过即自动 M4
  submit-2    M4: 验证第一审批状态 + 提交飞书第二审批 (费用报销)
  watcher-status  查询后台审批守护进程状态 + 最近日志
  watcher-stop    手动停止后台审批守护进程
  lookup-open-id  通过手机号或邮箱反查 user_open_id (在本项目 app 视角下)
  uninstall   卸载 skill: 删除 ~/.claude/skills/invoice-reimbursement/ 与
              ~/.invoice-reimbursement/ (含 IMAP 密码 / app_secret / 审批历史)

实现的子命令: init, status, validate, onboard, fetch, parse, submit-1, submit-2,
              watcher-status, watcher-stop, lookup-open-id, uninstall.

预检机制:
  除了 init / status / validate / onboard 之外, 所有子命令执行前都会调用
  validate_config.validate() 做全量配置校验. 校验不通过则拒绝执行, 打印所有
  错误及修复建议, 以退出码 2 退出.
"""

import sys
import argparse
from datetime import date, timedelta
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from storage import Storage  # noqa: E402
from init_storage import run_init  # noqa: E402
from parse_and_filter import parse_and_filter  # noqa: E402
from fetch_emails import fetch_emails  # noqa: E402
from submit_first_approval import submit_first_approval  # noqa: E402
from submit_second_approval import submit_second_approval  # noqa: E402
from validate_config import validate  # noqa: E402
from lookup_open_id import lookup_open_id, LookupError  # noqa: E402
from uninstall import run as run_uninstall  # noqa: E402

# 不需要预检的命令 (用于初始化 / 诊断 / 引导)
_SKIP_PREFLIGHT = {"init", "status", "validate", "onboard",
                   "watcher-status", "watcher-stop", "lookup-open-id",
                   "uninstall"}


def _preflight_check(cmd_name: str) -> int:
    """执行配置预检. 通过返回 -1 (继续); 不通过打印错误并返回退出码."""
    if cmd_name in _SKIP_PREFLIGHT:
        return -1

    result = validate()
    if result.ok:
        return -1

    print("[PREFLIGHT] 配置校验不通过, 请先修复以下问题:\n", file=sys.stderr)
    for i in result.errors:
        print(f"  [ERROR] {i.field}: {i.message}", file=sys.stderr)
        if i.fix_hint:
            print(f"          -> {i.fix_hint}", file=sys.stderr)
    if result.warnings:
        print("", file=sys.stderr)
        for i in result.warnings:
            print(f"  [WARN]  {i.field}: {i.message}", file=sys.stderr)
            if i.fix_hint:
                print(f"          -> {i.fix_hint}", file=sys.stderr)
    print(f"\n  修复后运行 'python3 cli.py validate' 重新检查.", file=sys.stderr)
    return 2


def cmd_init(args) -> int:
    return run_init(force=args.force, base_dir=Path(args.dir) if args.dir else None)


def cmd_status(args) -> int:
    s = Storage(base_dir=Path(args.dir) if args.dir else None)
    state = s.load_state()
    history = s.load_history()

    print(f"Storage:   {s.base_dir}")
    print(f"  rules.json:   {'present' if s.rules_path.exists() else 'MISSING'}")
    print(f"  config.json:  {'present' if s.config_path.exists() else 'MISSING (run init)'}")

    # 顺便跑一次校验, 让用户看到当前状态
    from validate_config import validate as v
    vr = v(storage=s)
    if vr.ok:
        print(f"  validation:   PASS")
    else:
        print(f"  validation:   {len(vr.errors)} error(s), {len(vr.warnings)} warning(s)")

    pending = state.get("pending", [])
    skipped = state.get("skipped", [])
    print(f"\nstate.json pending ({len(pending)}):")
    for r in pending:
        print(f"  - {r.get('invoice_number','?')}  status={r.get('status','?')}  amount={r.get('amount','?')}")
    print(f"\nstate.json skipped ({len(skipped)}):")
    for r in skipped:
        print(f"  - {r.get('invoice_pdf','?').split('/')[-1]}  skip_reason={r.get('skip_reason','?')}")
    print(f"\nhistory.json processed ({len(history.get('processed', []))}):")
    for r in history.get("processed", [])[-5:]:
        print(f"  - {r.get('invoice_number','?')}  date={r.get('processed_date','?')}  amount={r.get('amount','?')}")
    return 0


def cmd_validate(args) -> int:
    import json
    storage = Storage(base_dir=Path(args.dir) if args.dir else None)
    result = validate(storage=storage)
    if args.json:
        json.dump(result.to_dict(), sys.stdout, ensure_ascii=False, indent=2)
        sys.stdout.write("\n")
    else:
        for i in result.errors:
            print(f"  [ERROR] {i.field}: {i.message}")
            if i.fix_hint:
                print(f"          -> {i.fix_hint}")
        for i in result.warnings:
            print(f"  [WARN]  {i.field}: {i.message}")
            if i.fix_hint:
                print(f"          -> {i.fix_hint}")
        if result.ok:
            print("  配置校验通过. 可以开始使用.")
        else:
            print(f"\n  共 {len(result.errors)} 个错误, {len(result.warnings)} 个警告.")
            print(f"  修复后重新运行此命令检查.")
    return 0 if result.ok else 2


def _prompt(prompt_text: str, default: str = "", secret: bool = False) -> str:
    """交互式提示, 支持默认值和隐私输入."""
    import getpass
    suffix = f" [{default}]: " if default else ": "
    if secret:
        return getpass.getpass(prompt_text + suffix) or default
    return input(prompt_text + suffix) or default


def _resolve_open_id(raw: str, *, app_id: str, app_secret: str) -> str:
    """onboard 辅助: 输入是 ou_xxx 直接返回; 否则按手机号反查."""
    raw = (raw or "").strip()
    if not raw:
        return ""
    if raw.startswith("ou_"):
        return raw
    if not (app_id and app_secret):
        print("  [WARN] 未填 app_id / app_secret, 无法自动反查, 直接保留原始输入.")
        return raw
    try:
        data = lookup_open_id(
            mobiles=[raw],
            app_id=app_id,
            app_secret=app_secret,
        )
    except LookupError as e:
        print(f"  [WARN] 反查失败: {e}")
        print(f"  保留原始输入, 你可以稍后手动改 config.json 的 feishu.user_id.")
        return raw
    user_list = data.get("user_list", [])
    if not user_list or not user_list[0].get("user_id"):
        miss = data.get("mobiles_not_exist") or []
        print(f"  [WARN] 手机号 {raw} 未匹配到飞书用户 (not_exist={miss}).")
        return raw
    open_id = user_list[0]["user_id"]
    print(f"  → 反查成功: {raw} → {open_id}")
    return open_id


def cmd_onboard(args) -> int:
    """交互式引导: 逐项填入缺失的配置, 写入 config.json / rules.json."""
    import json

    storage = Storage()
    result = validate(storage)

    if result.ok:
        print("所有配置已就绪, 无需引导.")
        return 0

    # 确保 config.json 存在
    if not storage.config_path.exists():
        print("正在初始化存储目录...")
        run_init(force=False, base_dir=storage.base_dir)
        storage.config_path.write_text(json.dumps({}, ensure_ascii=False, indent=2))

    config = storage.load_config()
    rules = storage.load_rules() if storage.rules_path.exists() else {}

    changed = False

    # ---- 1. IMAP 邮箱配置 ----
    imap_issues = [i for i in result.errors if i.field.startswith("imap")]
    config_issues = [i for i in result.errors if i.field == "config.json"]
    if imap_issues or config_issues:
        print(f"\n{'='*60}")
        print("  [1/4] IMAP 邮箱")
        print(f"{'='*60}")
        print("  需要你的邮箱凭证来读取高德发票邮件.")
        print("  QQ邮箱请使用授权码而非密码 (设置→账户→POP3/IMAP→生成授权码)")

        imap = config.get("imap", {})
        if not imap.get("host"):
            imap["host"] = _prompt("  IMAP 服务器地址", "imap.qq.com")
        if not imap.get("port"):
            port_str = _prompt("  IMAP 端口", "993")
            imap["port"] = int(port_str)
        if not imap.get("account"):
            imap["account"] = _prompt("  邮箱账号 (如 xxx@qq.com)")
        if not imap.get("password"):
            imap["password"] = _prompt("  邮箱密码/授权码", secret=True)
        if not imap.get("senders"):
            senders_str = _prompt(
                "  高德发票发件人 (逗号分隔多个)",
                "itinerary@ridesharing.amap.com"
            )
            imap["senders"] = [s.strip() for s in senders_str.split(",") if s.strip()]
        config["imap"] = imap
        changed = True

    # ---- 2. 飞书审批配置 ----
    feishu_issues = [i for i in result.errors if i.field.startswith("feishu")]
    if feishu_issues:
        print(f"\n{'='*60}")
        print("  [2/4] 飞书审批配置")
        print(f"{'='*60}")
        print("  需要飞书应用凭证 + 审批 definition_code + 你的 open_id.")
        print("  - app_id / app_secret: 飞书开放平台 → 你的应用 → 凭证与基础信息")
        print("  - definition_code: 飞书审批后台 → 审批流程 → URL 中的 UUID")
        print("  - user_open_id (ou_xxx): 推荐用 `python3 cli.py lookup-open-id --mobile <手机号>`")
        print("    自助反查 (前提: app_id / app_secret 已填好). 也可在 API explorer 手动查.")

        feishu = config.get("feishu", {})
        # 先收 app_id / app_secret, 以便后面 user_id 能用 lookup-open-id 自助查.
        if not feishu.get("app_id"):
            feishu["app_id"] = _prompt(
                "  飞书应用 App ID (如 cli_xxx)",
                "cli_aa8000f2827a9cbc",
            )
        if not feishu.get("app_secret"):
            feishu["app_secret"] = _prompt("  飞书应用 App Secret", secret=True)

        if not feishu.get("definition_code"):
            feishu["definition_code"] = _prompt(
                "  采购申请 definition_code (UUID)",
                "868B710A-A742-45EE-9E6D-C61D0BF5963F"
            )
        if not feishu.get("user_id"):
            print("  飞书 user_open_id (ou_xxx) — 输入你的手机号自动反查, 或直接粘贴已知的 ou_xxx.")
            raw = _prompt("  手机号 或 ou_xxx")
            feishu["user_id"] = _resolve_open_id(
                raw,
                app_id=feishu.get("app_id"),
                app_secret=feishu.get("app_secret"),
            )
        if not feishu.get("expense_definition_code"):
            feishu["expense_definition_code"] = _prompt(
                "  费用报销 definition_code (UUID)",
                "FAB04EBA-8365-46CA-B273-2F9CF1355460"
            )

        entity = feishu.get("purchase_entity") or {}
        if not entity.get("key"):
            entity["key"] = _prompt("  采购主体 option key", "mp3dpnnw-07gunm764bby-0")
        if not entity.get("text"):
            entity["text"] = _prompt("  采购主体显示文本", "找北智职")
        feishu["purchase_entity"] = entity

        if not feishu.get("default_reason"):
            feishu["default_reason"] = _prompt(
                "  默认采购事由", "高德打车费报销"
            )
        # app_id / app_secret 已经在本节开头采集
        config["feishu"] = feishu
        changed = True

    # ---- 3. 报销规则 ----
    # 公司层面字段 (公司名/税号/时间窗口/金额上限) 已在 rules.example.json 预填,
    # 这里只问个人化的起点关键词.
    location = (rules.get("location") or {}).get("endpoint_match") or {}
    current_keywords = location.get("keywords", [])
    needs_keyword = (
        not current_keywords
        or any(str(k).startswith("<") for k in current_keywords)
    )

    if needs_keyword and location.get("mode") in ("origin_in", "both", "either", "destination_in"):
        print(f"\n{'='*60}")
        print("  [3/4] 报销规则 — 起点关键词")
        print(f"{'='*60}")
        print("  报销要求行程起点(或终点)包含特定关键词. 填你常用的出发地址,")
        print("  按子串匹配, 不区分大小写. 多个用逗号分隔.")
        print("  示例: 中国杭州人力资源服务产业园")

        kw_input = _prompt("  起点关键词 (多个用逗号)")
        if kw_input:
            keywords = [k.strip() for k in kw_input.split(",") if k.strip()]
            rules.setdefault("location", {}).setdefault("endpoint_match", {})["keywords"] = keywords
            changed = True

    # 补全 buyer (兼容老 rules.json)
    buyer = rules.get("buyer", {})
    if not buyer.get("company_name"):
        buyer["company_name"] = _prompt("  公司全称")
        changed = True
    if not buyer.get("tax_id"):
        buyer["tax_id"] = _prompt("  公司税号 (18位)")
        changed = True
    rules["buyer"] = buyer

    # ---- 4. Python 依赖 ----
    dep_issues = [i for i in result.errors if i.field == "pdfplumber"]
    if dep_issues:
        print(f"\n{'='*60}")
        print("  [4/4] Python 依赖")
        print(f"{'='*60}")
        print("  缺少 pdfplumber 库.")
        ans = _prompt("是否现在安装? (y/n)", "y")
        if ans.lower() == "y":
            import subprocess
            subprocess.run([sys.executable, "-m", "pip", "install", "pdfplumber"])

    # ---- 写入 ----
    if changed:
        storage.config_path.write_text(
            json.dumps(config, ensure_ascii=False, indent=2)
        )
        print(f"\n配置已写入: {storage.config_path}")

        if rules:
            storage.rules_path.write_text(
                json.dumps(rules, ensure_ascii=False, indent=2)
            )
            print(f"规则已写入: {storage.rules_path}")

    # ---- 终验 ----
    print("\n正在重新校验...")
    result_final = validate(storage)
    if result_final.ok:
        print("全部配置通过! 可以开始使用了.")
        return 0
    else:
        print("仍有以下问题需手动修复:")
        for i in result_final.errors:
            print(f"  [ERROR] {i.field}: {i.message}")
            if i.fix_hint:
                print(f"          -> {i.fix_hint}")
        print("\n可重新运行 onboard 继续配置.")
        return 2


def cmd_fetch(args) -> int:
    import json
    today = date.today()
    if args.since:
        try:
            since = date.fromisoformat(args.since)
        except ValueError as e:
            print(f"[ERROR] --since 不是合法 YYYY-MM-DD: {e}", file=sys.stderr)
            return 2
    elif args.days is not None:
        if args.days < 0:
            print("[ERROR] --days 必须 >= 0", file=sys.stderr)
            return 2
        since = today - timedelta(days=args.days)
    else:
        since = today

    storage = Storage(base_dir=Path(args.dir) if args.dir else None)
    try:
        summary = fetch_emails(
            storage=storage,
            since_date=since,
            dry_run=args.dry_run,
            limit=args.limit,
        )
    except RuntimeError as e:
        print(f"[ERROR] {e}", file=sys.stderr)
        return 2
    print(json.dumps(summary, ensure_ascii=False, indent=2))
    return 0


def cmd_parse(args) -> int:
    import json
    storage = Storage(base_dir=Path(args.dir) if args.dir else None)
    pdf_dir = Path(args.pdf_dir) if args.pdf_dir else storage.tmp_dir
    try:
        summary = parse_and_filter(storage=storage, pdf_dir=pdf_dir)
    except RuntimeError as e:
        print(f"[ERROR] {e}", file=sys.stderr)
        return 2
    print(json.dumps(summary, ensure_ascii=False, indent=2))
    if summary["skipped_by_parse_error"]:
        return 1
    if summary["paired"] == 0 and (
        summary["details"]["unpaired_invoice_pdfs"]
        or summary["details"]["unpaired_trip_pdfs"]
    ):
        return 1
    return 0


def cmd_submit_1(args) -> int:
    import json
    storage = Storage(base_dir=Path(args.dir) if args.dir else None)
    try:
        summary = submit_first_approval(
            storage=storage,
            reason=args.reason,
            dry_run=args.dry_run,
        )
    except RuntimeError as e:
        print(f"[ERROR] {e}", file=sys.stderr)
        return 2
    print(json.dumps(summary, ensure_ascii=False, indent=2))
    if not summary.get("ok"):
        return 1
    return 0


def cmd_submit_2(args) -> int:
    import json
    storage = Storage(base_dir=Path(args.dir) if args.dir else None)
    try:
        summary = submit_second_approval(
            storage=storage,
            dry_run=args.dry_run,
        )
    except RuntimeError as e:
        print(f"[ERROR] {e}", file=sys.stderr)
        return 2
    print(json.dumps(summary, ensure_ascii=False, indent=2))
    if not summary.get("ok"):
        return 1
    return 0


def cmd_watcher_status(args) -> int:
    """显示 watcher 进程状态 + 最近日志."""
    import os
    storage = Storage(base_dir=Path(args.dir) if args.dir else None)
    pid_path = storage.base_dir / "watcher.pid"
    log_path = storage.base_dir / "watcher.log"

    print(f"watcher.pid:  {pid_path}")
    print(f"watcher.log:  {log_path}")
    print()

    if not pid_path.exists():
        print("  状态: 未运行 (无 PID 文件)")
    else:
        try:
            pid = int(pid_path.read_text().strip())
            try:
                os.kill(pid, 0)
                print(f"  状态: 运行中 (pid={pid})")
            except OSError:
                print(f"  状态: 已停止 (pid={pid} 不存在, 残留 PID 文件)")
        except (ValueError, OSError) as e:
            print(f"  状态: 无法读取 PID 文件: {e}")

    if log_path.exists():
        print(f"\n  最近 {args.log_lines} 行日志:")
        try:
            lines = log_path.read_text(encoding="utf-8").splitlines()
            for line in lines[-args.log_lines:]:
                print(f"    {line}")
        except OSError as e:
            print(f"    (读取失败: {e})")
    return 0


def cmd_watcher_stop(args) -> int:
    """手动停止 watcher 进程."""
    import os
    import signal
    storage = Storage(base_dir=Path(args.dir) if args.dir else None)
    pid_path = storage.base_dir / "watcher.pid"

    if not pid_path.exists():
        print("watcher 未运行 (无 PID 文件)", file=sys.stderr)
        return 0
    try:
        pid = int(pid_path.read_text().strip())
    except (ValueError, OSError) as e:
        print(f"[ERROR] 无法读取 PID 文件: {e}", file=sys.stderr)
        return 2
    try:
        os.kill(pid, signal.SIGTERM)
        print(f"已发送 SIGTERM 到 watcher pid={pid}")
    except ProcessLookupError:
        print(f"watcher 进程 pid={pid} 已不存在, 清理残留 PID 文件")
    except OSError as e:
        print(f"[ERROR] 发送信号失败: {e}", file=sys.stderr)
        return 2
    try:
        pid_path.unlink()
    except OSError:
        pass
    return 0


def cmd_lookup_open_id(args) -> int:
    """通过手机号或邮箱反查 user_open_id."""
    import json
    storage = Storage(base_dir=Path(args.dir) if args.dir else None)
    try:
        data = lookup_open_id(
            mobiles=args.mobile or None,
            emails=args.email or None,
            storage=storage,
        )
    except LookupError as e:
        print(f"[ERROR] {e}", file=sys.stderr)
        return 2

    if args.json:
        print(json.dumps(data, ensure_ascii=False, indent=2))
        return 0

    user_list = data.get("user_list", [])
    mobiles_miss = data.get("mobiles_not_exist", []) or []
    emails_miss = data.get("emails_not_exist", []) or []

    if not user_list:
        print("[ERROR] 没有匹配到用户.", file=sys.stderr)
        if mobiles_miss:
            print(f"  未匹配手机号: {', '.join(mobiles_miss)}", file=sys.stderr)
        if emails_miss:
            print(f"  未匹配邮箱: {', '.join(emails_miss)}", file=sys.stderr)
        print(
            "\n  提示: 确认该手机号/邮箱已在飞书注册, 且与本项目 app 在同一企业租户.",
            file=sys.stderr,
        )
        return 1

    print("查询结果 (左侧 ou_xxx 即填入 config 的 feishu.user_id):")
    for u in user_list:
        uid = u.get("user_id") or "(无 open_id)"
        key = u.get("mobile") or u.get("email") or "?"
        print(f"  {uid}    ←  {key}")

    if mobiles_miss or emails_miss:
        print("\n  以下未匹配到:")
        for m in mobiles_miss:
            print(f"    手机号 {m}")
        for e in emails_miss:
            print(f"    邮箱   {e}")
    return 0


def cmd_uninstall(args) -> int:
    """卸载 skill + 删除存储目录."""
    storage = Storage(base_dir=Path(args.dir) if args.dir else None)
    return run_uninstall(
        keep_data=args.keep_data,
        assume_yes=args.yes,
        storage=storage,
        skill_dir=Path(args.skill_dir) if args.skill_dir else None,
    )


def cmd_not_implemented(args) -> int:
    print(f"[NOT IMPLEMENTED] '{args.cmd}' is not yet available.", file=sys.stderr)
    print("Currently implemented: init, status, validate, onboard, fetch, parse, "
          "submit-1, submit-2, watcher-status, watcher-stop.", file=sys.stderr)
    return 2


def main():
    p = argparse.ArgumentParser(
        prog="invoice-reimbursement",
        description="Invoice Reimbursement Skill CLI (v0.1, 高德 only).",
    )
    p.add_argument("--dir", default=None,
                   help="Override storage dir (default: $INVOICE_REIMBURSEMENT_DIR or ~/.invoice-reimbursement)")
    sub = p.add_subparsers(dest="cmd", required=True)

    p_init = sub.add_parser("init", help="Initialize storage")
    p_init.add_argument("--force", action="store_true", help="Overwrite existing files")
    p_init.set_defaults(func=cmd_init)

    p_status = sub.add_parser("status", help="Show current state + config validation summary")
    p_status.set_defaults(func=cmd_status)

    p_validate = sub.add_parser("validate", help="Validate config.json / rules.json / lark-cli readiness")
    p_validate.add_argument("--json", action="store_true", help="Output as JSON")
    p_validate.set_defaults(func=cmd_validate)

    p_onboard = sub.add_parser("onboard", help="Interactive setup guide for missing config")
    p_onboard.set_defaults(func=cmd_onboard)

    p_fetch = sub.add_parser("fetch", help="M1: fetch invoice PDFs from IMAP into <storage>/tmp/")
    grp = p_fetch.add_mutually_exclusive_group()
    grp.add_argument("--since", help="搜索起始日期 YYYY-MM-DD (默认: 今天)")
    grp.add_argument("--days", type=int, help="搜索过去 N 天 (含今天)")
    p_fetch.add_argument("--dry-run", action="store_true", help="不写文件, 只列出会下载哪些附件")
    p_fetch.add_argument("--limit", type=int, default=None, help="最多下载多少个 PDF 附件后停止")
    p_fetch.set_defaults(func=cmd_fetch)

    p_parse = sub.add_parser("parse", help="M2: parse PDFs + apply rules + write state.json")
    p_parse.add_argument("--pdf-dir", default=None,
                         help="PDF directory to scan (default: <storage>/tmp/)")
    p_parse.set_defaults(func=cmd_parse)

    p_submit1 = sub.add_parser("submit-1", help="M3: upload PDFs + create first approval instance")
    p_submit1.add_argument("--reason", default=None, help="采购事由文本 (不指定则用 config 默认值)")
    p_submit1.add_argument("--dry-run", action="store_true", help="预览表单 JSON, 不上传也不真提交")
    p_submit1.set_defaults(func=cmd_submit_1)

    p_submit2 = sub.add_parser("submit-2", help="M4: check first approval status + create expense report")
    p_submit2.add_argument("--dry-run", action="store_true",
                           help="假设第一审批 APPROVED，预览表单 JSON，不真提交")
    p_submit2.set_defaults(func=cmd_submit_2)

    p_ws = sub.add_parser("watcher-status", help="查询后台审批守护进程状态 + 最近一次轮询结果")
    p_ws.add_argument("--log-lines", type=int, default=10,
                      help="显示最近 N 行 watcher 日志 (默认 10)")
    p_ws.set_defaults(func=cmd_watcher_status)

    p_wstop = sub.add_parser("watcher-stop", help="手动停止后台审批守护进程")
    p_wstop.set_defaults(func=cmd_watcher_stop)

    p_lookup = sub.add_parser(
        "lookup-open-id",
        help="通过手机号或邮箱反查 user_open_id (在本项目 app 视角下, 用于 onboard)",
    )
    p_lookup.add_argument("--mobile", action="append", default=[],
                          help="手机号 (可重复)")
    p_lookup.add_argument("--email", action="append", default=[],
                          help="邮箱 (可重复)")
    p_lookup.add_argument("--json", action="store_true", help="输出原始 JSON")
    p_lookup.set_defaults(func=cmd_lookup_open_id)

    p_uninstall = sub.add_parser(
        "uninstall",
        help="卸载 skill: 删除 ~/.claude/skills/invoice-reimbursement/ + ~/.invoice-reimbursement/",
    )
    p_uninstall.add_argument("--keep-data", action="store_true",
                             help="只删 skill 文件, 保留 ~/.invoice-reimbursement/ (config + history)")
    p_uninstall.add_argument("--yes", "-y", action="store_true",
                             help="不再二次确认, 直接执行")
    p_uninstall.add_argument("--skill-dir", default=None,
                             help="覆盖 skill 安装路径 (默认 ~/.claude/skills/invoice-reimbursement/); "
                                  "主要给开发 smoke test 用")
    p_uninstall.set_defaults(func=cmd_uninstall)

    args = p.parse_args()

    # 预检
    preflight_rc = _preflight_check(args.cmd)
    if preflight_rc >= 0:
        sys.exit(preflight_rc)

    sys.exit(args.func(args))


if __name__ == "__main__":
    main()
