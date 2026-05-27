#!/usr/bin/env python3
"""
反查飞书 user_open_id — v0.1

用本项目的飞书应用凭证 (tenant_access_token), 通过手机号或邮箱反查 open_id.
open_id 是应用维度的 ID, 必须用本项目同一个 app_id 才能拿到正确值.

公开函数:
  lookup_open_id(*, mobiles=None, emails=None, storage=None,
                 app_id=None, app_secret=None) -> dict

CLI 用法:
  python3 lookup_open_id.py --mobile 13800138000
  python3 lookup_open_id.py --email someone@example.com --json
"""

import sys
import json
import argparse
from pathlib import Path
from typing import Optional, List

sys.path.insert(0, str(Path(__file__).resolve().parent))
from feishu_upload import call_open_api, UploadError  # noqa: E402
from storage import Storage  # noqa: E402


class LookupError(RuntimeError):
    pass


def lookup_open_id(
    *,
    mobiles: Optional[List[str]] = None,
    emails: Optional[List[str]] = None,
    storage: Optional[Storage] = None,
    app_id: Optional[str] = None,
    app_secret: Optional[str] = None,
) -> dict:
    """通过手机号或邮箱反查 open_id.

    Args:
        mobiles: 手机号列表 (任意之一, 与 emails 共存时同时查).
        emails: 邮箱列表.
        storage: Storage 实例; 若为 None 从默认目录读取.
        app_id / app_secret: 显式覆盖, 否则从 config.json 读.

    Returns:
        飞书 API data 字段, 形如:
        {
          "user_list": [{"user_id": "ou_xxx", "mobile": "138..."}],
          "mobiles_not_exist": [...],
          "emails_not_exist": [...]
        }

    Raises:
        LookupError: 参数不全 / 凭证缺失 / API 报错.
    """
    if not mobiles and not emails:
        raise LookupError("必须至少提供一个手机号 (--mobile) 或邮箱 (--email)")

    if not (app_id and app_secret):
        if storage is None:
            storage = Storage()
        feishu = (storage.load_config() or {}).get("feishu", {})
        app_id = app_id or feishu.get("app_id")
        app_secret = app_secret or feishu.get("app_secret")

    if not app_id or not app_secret:
        raise LookupError(
            "缺少 feishu.app_id 或 feishu.app_secret. "
            "请先在 ~/.invoice-reimbursement/config.json 填好, "
            "或通过 --app-id / --app-secret 显式传入."
        )

    body: dict = {}
    if mobiles:
        body["mobiles"] = mobiles
    if emails:
        body["emails"] = emails

    try:
        resp = call_open_api(
            "POST",
            "/open-apis/contact/v3/users/batch_get_id",
            body=body,
            params={"user_id_type": "open_id"},
            app_id=app_id,
            app_secret=app_secret,
        )
    except UploadError as e:
        raise LookupError(f"调用飞书 API 失败: {e}") from None

    code = resp.get("code", 0)
    if code != 0:
        raise LookupError(
            f"飞书 API 返回错误 code={code} msg={resp.get('msg')}. "
            f"常见原因: app 未开通 contact.user.id.search 权限, "
            f"或目标用户与本 app 不在同一租户."
        )

    return resp.get("data", {})


def main(argv: Optional[List[str]] = None) -> int:
    p = argparse.ArgumentParser(
        prog="lookup_open_id",
        description="通过手机号或邮箱反查飞书 user_open_id (在本项目 app 视角下).",
    )
    p.add_argument("--mobile", action="append", default=[],
                   help="手机号 (可重复); 国内号码可不加区号")
    p.add_argument("--email", action="append", default=[],
                   help="邮箱 (可重复)")
    p.add_argument("--app-id", default=None, help="覆盖 config 中的 app_id")
    p.add_argument("--app-secret", default=None, help="覆盖 config 中的 app_secret")
    p.add_argument("--dir", default=None, help="覆盖存储目录 (默认 ~/.invoice-reimbursement)")
    p.add_argument("--json", action="store_true", help="输出原始 JSON")
    args = p.parse_args(argv)

    storage = Storage(base_dir=Path(args.dir) if args.dir else None)

    try:
        data = lookup_open_id(
            mobiles=args.mobile or None,
            emails=args.email or None,
            storage=storage,
            app_id=args.app_id,
            app_secret=args.app_secret,
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

    print("查询结果:")
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


if __name__ == "__main__":
    sys.exit(main())
