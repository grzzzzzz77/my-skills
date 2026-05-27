#!/usr/bin/env python3
"""
飞书 API 客户端  —  v0.2

用 app_id + app_secret 获取 tenant_access_token (2 小时, 自动续期), 替代
lark-cli 用户 OAuth token (7 天 refresh, 到期需浏览器重新授权).

公开函数:
  get_tenant_access_token(app_id, app_secret) -> str
  call_open_api(method, path, *, body, params, app_id, app_secret) -> dict
  upload_file_v2(pdf_path, *, app_id, app_secret, name) -> str

依赖: 仅 stdlib (urllib + uuid).
"""

import json
import urllib.request
import urllib.error
import uuid
import time
from pathlib import Path


# 简单的 tenant token 缓存 (进程内有效)
_TOKEN_CACHE = {"token": None, "expires_at": 0.0}


class UploadError(Exception):
    pass


def get_tenant_access_token(app_id: str, app_secret: str) -> str:
    """获取 tenant_access_token, 缓存 2 小时 (官方有效期 2h)."""
    now = time.time()
    cache = _TOKEN_CACHE
    if cache["token"] and cache["expires_at"] - 60 > now:
        return cache["token"]

    body = json.dumps({"app_id": app_id, "app_secret": app_secret}).encode()
    req = urllib.request.Request(
        "https://open.feishu.cn/open-apis/auth/v3/tenant_access_token/internal",
        data=body,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    try:
        resp = urllib.request.urlopen(req, timeout=30).read()
    except urllib.error.URLError as e:
        raise UploadError(f"获取 tenant_access_token 网络错误: {e}") from None

    r = json.loads(resp)
    if r.get("code") != 0:
        raise UploadError(f"获取 tenant_access_token 失败: {r}")
    token = r.get("tenant_access_token")
    expires_in = int(r.get("expire", 7200))
    cache["token"] = token
    cache["expires_at"] = now + expires_in
    return token


def upload_file_v2(
    pdf_path: Path,
    *,
    app_id: str,
    app_secret: str,
    name: str = None,
) -> str:
    """上传单个 PDF 到飞书审批 v2 endpoint, 返回 file code (UUID).

    Args:
        pdf_path: 本地 PDF 路径.
        app_id / app_secret: 飞书应用凭证 (来自 config.json feishu.app_id / app_secret).
        name: 提交给飞书侧的显示文件名 (默认 = pdf_path.name).

    Returns:
        飞书侧 file code (UUID, 用于 attachmentV2 widget value).

    Raises:
        UploadError: 网络 / 鉴权 / API 错误.
    """
    if not pdf_path.exists():
        raise UploadError(f"PDF 不存在: {pdf_path}")

    token = get_tenant_access_token(app_id, app_secret)
    display_name = name or pdf_path.name
    data = pdf_path.read_bytes()

    boundary = uuid.uuid4().hex
    parts = [
        f"--{boundary}\r\nContent-Disposition: form-data; "
        f'name="name"\r\n\r\n{display_name}\r\n'.encode(),
        f"--{boundary}\r\nContent-Disposition: form-data; "
        f'name="type"\r\n\r\nattachment\r\n'.encode(),
        f"--{boundary}\r\nContent-Disposition: form-data; "
        f'name="content"; filename="{display_name}"\r\n'
        f"Content-Type: application/pdf\r\n\r\n".encode()
        + data + b"\r\n",
        f"--{boundary}--\r\n".encode(),
    ]
    body = b"".join(parts)

    req = urllib.request.Request(
        "https://www.feishu.cn/approval/openapi/v2/file/upload",
        data=body,
        headers={
            "Authorization": f"Bearer {token}",
            "Content-Type": f"multipart/form-data; boundary={boundary}",
        },
        method="POST",
    )
    try:
        resp = urllib.request.urlopen(req, timeout=60).read()
    except urllib.error.HTTPError as e:
        body_text = e.read()[:500].decode(errors="replace")
        raise UploadError(f"HTTP {e.code} 上传 {pdf_path.name}: {body_text}") from None
    except urllib.error.URLError as e:
        raise UploadError(f"网络错误 上传 {pdf_path.name}: {e}") from None

    r = json.loads(resp)
    if r.get("code") != 0:
        raise UploadError(f"v2 上传失败 {pdf_path.name}: {r}")
    code = r.get("data", {}).get("code")
    if not code:
        raise UploadError(f"v2 上传响应缺少 data.code: {r}")
    return code


# ---------- 通用 open-apis HTTP 调用 ----------

def call_open_api(
    method: str,
    path: str,
    *,
    body: dict = None,
    params: dict = None,
    app_id: str,
    app_secret: str,
) -> dict:
    """用 tenant_access_token 调用 open.feishu.cn OpenAPI.

    Args:
        method: "GET" / "POST" 等.
        path: 以 / 开头的 API 路径, 如 "/open-apis/approval/v4/instances".
        body: POST body (dict, 会 JSON 序列化).
        params: GET query params (dict).
        app_id / app_secret: 飞书应用凭证.

    Returns:
        飞书 API 响应 dict (已解析 JSON).

    Raises:
        UploadError: 网络 / 鉴权 / HTTP 非 2xx 错误.
    """
    token = get_tenant_access_token(app_id, app_secret)
    url = "https://open.feishu.cn" + path
    if params:
        from urllib.parse import urlencode
        url += "?" + urlencode(params)

    data = json.dumps(body, ensure_ascii=False).encode() if body else None
    req = urllib.request.Request(
        url,
        data=data,
        headers={
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json; charset=utf-8",
        },
        method=method,
    )
    try:
        resp = urllib.request.urlopen(req, timeout=30).read()
    except urllib.error.HTTPError as e:
        body_text = e.read()[:500].decode(errors="replace")
        raise UploadError(f"HTTP {e.code} {method} {path}: {body_text}") from None
    except urllib.error.URLError as e:
        raise UploadError(f"网络错误 {method} {path}: {e}") from None

    return json.loads(resp)
