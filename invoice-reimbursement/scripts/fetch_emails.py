#!/usr/bin/env python3
"""
M1: IMAP 邮箱发票邮件抓取  —  v0.1

从 ~/.invoice-reimbursement/config.json["imap"] 读取凭证, 按 FROM + SINCE 搜索邮件,
把所有 PDF 附件下载到 <storage>/tmp/ 目录, 输出本次下载摘要 (JSON, stdout).

设计原则:
  - 只下载, 不配对. 发票 / 行程单的配对延后给 M2 的 pair_pdfs.py 按金额比对
    (比文件名 / 主题更可靠).
  - 不做去重. 同名附件以 `-1`, `-2` 等后缀保存; 真正的发票号去重在 M2 完成.
  - 凭证只在内存中流转, 错误信息不打印 password.

config.json["imap"] schema:
  {
    "host":     "imap.example.com",      # 必填
    "port":     993,                     # 默认 993
    "ssl":      true,                    # 默认 true
    "account":  "user@example.com",      # 必填
    "password": "<app-specific password>", # 必填
    "senders":  ["no-reply@gaode.com"]   # 至少 1 个; 也可写成 string
  }

Usage:
    python3 fetch_emails.py [--dir <storage-dir>]
                            [--since YYYY-MM-DD | --days N]
                            [--dry-run] [--limit N] [--pretty]

Exit codes:
  0  正常完成 (即使 0 封邮件 / 0 个 PDF 附件)
  2  前置错误: 配置缺失 / 字段非法 / IMAP 连接 / 认证 / SEARCH 失败
"""

FETCHER_VERSION = "0.1"

import sys
import json
import email
import imaplib
import argparse
from email.header import decode_header, make_header
from datetime import date, timedelta
from pathlib import Path
from typing import Optional

sys.path.insert(0, str(Path(__file__).resolve().parent))
from storage import Storage  # noqa: E402


REQUIRED_IMAP_KEYS = ("host", "account", "password")


# ---------- helpers ----------

def _decode_str(raw) -> str:
    """安全解码 RFC 2047 邮件头 (Subject / From / filename). None 返回空字符串."""
    if raw is None:
        return ""
    if isinstance(raw, bytes):
        try:
            return raw.decode("utf-8", errors="replace")
        except Exception:
            return raw.decode("latin-1", errors="replace")
    try:
        return str(make_header(decode_header(raw)))
    except Exception:
        return str(raw)


def _imap_since_token(d: date) -> str:
    """IMAP RFC 3501: SINCE 使用 DD-Mon-YYYY 英文短月名 (区分大小写不敏感)."""
    months = ["Jan", "Feb", "Mar", "Apr", "May", "Jun",
              "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
    return f"{d.day:02d}-{months[d.month - 1]}-{d.year}"


def _sanitize_filename(name: str) -> str:
    """文件名去路径穿越 / 控制字符 / 操作系统不友好字符; 按 UTF-8 字节截断."""
    if not name:
        return "attachment.pdf"
    # 路径穿越 + CR/LF/NUL
    path_bad = {"/", "\\", "\x00", "\r", "\n"}
    # macOS 不友好 (Finder 不支持 ":")
    # Windows 不友好: < > : " | ? *
    os_bad = {"<", ">", ":", '"', "|", "?", "*"}
    bad = path_bad | os_bad
    cleaned = "".join(
        "_" if (c in bad or ord(c) < 0x20 or ord(c) == 0x7F) else c
        for c in name
    ).strip()
    cleaned = cleaned.lstrip(".") or "attachment.pdf"
    # 按 UTF-8 字节长度截断, 保留扩展名
    suffix = ""
    stem = cleaned
    dot_idx = cleaned.rfind(".")
    if dot_idx > 0 and dot_idx < len(cleaned) - 1:
        suffix = cleaned[dot_idx:]
        stem = cleaned[:dot_idx]
    max_bytes = 200 - len(suffix.encode("utf-8"))
    if max_bytes > 0:
        encoded = stem.encode("utf-8")
        if len(encoded) > max_bytes:
            truncated = encoded[:max_bytes]
            for cut in range(len(truncated), max(0, len(truncated) - 4), -1):
                try:
                    stem = truncated[:cut].decode("utf-8")
                    break
                except UnicodeDecodeError:
                    continue
    cleaned = stem + suffix
    return cleaned


def _ensure_pdf_suffix(name: str) -> str:
    """保证 M2 的 `*.pdf` 扫描契约: 没有 .pdf (大小写不敏感) 后缀就补一个."""
    if name.lower().endswith(".pdf"):
        return name
    return name + ".pdf"


def _atomic_write(dest: Path, data: bytes) -> None:
    """原子写: 先写同名临时文件, fsync 后 rename. 失败不留半截文件."""
    tmp_dest = dest.with_suffix(dest.suffix + ".tmp")
    try:
        with open(tmp_dest, "wb") as f:
            f.write(data)
            f.flush()
            import os
            os.fsync(f.fileno())
        tmp_dest.rename(dest)
    except Exception:
        if tmp_dest.exists():
            tmp_dest.unlink(missing_ok=True)
        raise


def _unique_dest(tmp_dir: Path, filename: str) -> Path:
    """同名追加 -1 / -2 后缀避免覆盖."""
    dest = tmp_dir / filename
    if not dest.exists():
        return dest
    stem, suffix = dest.stem, dest.suffix
    i = 1
    while True:
        candidate = tmp_dir / f"{stem}-{i}{suffix}"
        if not candidate.exists():
            return candidate
        i += 1


def _iter_pdf_parts(msg):
    """遍历 multipart, 产出 (filename, payload_bytes) 的 PDF 附件.

    PDF 识别采用并集策略:
      - Content-Type 是 application/pdf, 或
      - 文件名扩展是 .pdf (大小写不敏感), 或
      - payload magic 头 == b"%PDF" (兜底无 filename 也无明确 Content-Type 的情况)
    无文件名时返回占位名 attachment.pdf, 由调用方再走 _unique_dest 防覆盖.
    """
    idx = 0
    for part in msg.walk():
        if part.is_multipart():
            continue
        content_type = (part.get_content_type() or "").lower()
        filename_raw = part.get_filename()
        filename = _decode_str(filename_raw) if filename_raw else ""

        payload = part.get_payload(decode=True)
        if not payload:
            continue

        is_pdf_ct = content_type == "application/pdf"
        is_pdf_name = filename.lower().endswith(".pdf")
        is_pdf_magic = isinstance(payload, (bytes, bytearray)) and payload[:4] == b"%PDF"
        if not (is_pdf_ct or is_pdf_name or is_pdf_magic):
            continue

        idx += 1
        yield filename or f"attachment-{idx}.pdf", payload


# IMAP quoted-string metachars + 换行 / NUL. 拼进 SEARCH 会破坏语法甚至改写查询.
_SENDER_FORBIDDEN_CHARS = frozenset('"\\\r\n\x00')


def _validate_sender(sender: str) -> str:
    """对将拼进 IMAP SEARCH 的 sender 做严格校验.

    拒绝: IMAP 引用元字符 (`"`, `\\`) / CRLF / NUL / 其它 ASCII 控制字符.
    要求: 至少包含一个 `@`, 长度 1..254.
    """
    if not sender:
        raise RuntimeError("imap.senders 含空字符串")
    if any(c in _SENDER_FORBIDDEN_CHARS for c in sender):
        raise RuntimeError(
            f"imap.senders 含非法字符 (双引号 / 反斜杠 / 换行 / NUL): {sender!r}"
        )
    if any((ord(c) < 0x20 or ord(c) == 0x7F) for c in sender):
        raise RuntimeError(f"imap.senders 含 ASCII 控制字符: {sender!r}")
    if "@" not in sender:
        raise RuntimeError(f"imap.senders 缺少 '@', 不像邮箱地址: {sender!r}")
    if len(sender) > 254:
        raise RuntimeError(f"imap.senders 超长 (>254): len={len(sender)}")
    return sender


def _normalize_senders(raw) -> list:
    if raw is None:
        return []
    if isinstance(raw, str):
        items = [raw.strip()] if raw.strip() else []
    elif isinstance(raw, list):
        items = [str(s).strip() for s in raw if str(s).strip()]
    else:
        raise RuntimeError(f"config.json imap.senders 字段类型不合法: {type(raw).__name__}")
    return [_validate_sender(s) for s in items]


# ---------- IMAP 抽象 ----------

def _connect(imap_cfg: dict):
    """建立并登录 IMAP 连接. 失败抛 RuntimeError (不泄漏 password)."""
    host = imap_cfg["host"]
    try:
        port = int(imap_cfg.get("port", 993))
    except (TypeError, ValueError) as e:
        raise RuntimeError(f"config.json imap.port 不是合法整数: {imap_cfg.get('port')!r}") from e
    ssl = bool(imap_cfg.get("ssl", True))
    account = imap_cfg["account"]
    password = imap_cfg["password"]
    try:
        M = imaplib.IMAP4_SSL(host, port) if ssl else imaplib.IMAP4(host, port)
    except OSError as e:
        raise RuntimeError(f"IMAP 连接失败 ({host}:{port}): {e}") from e
    try:
        M.login(account, password)
    except (imaplib.IMAP4.error, OSError):
        # 不拼接原始异常 (有泄漏 account/password 的风险), 只给可操作指引
        raise RuntimeError(
            f"IMAP 认证失败 (account={account}). "
            f"检查邮箱是否开启 IMAP 服务、是否使用应用专用密码 (而非登录密码)."
        ) from None
    return M


def _search_ids(M, sender: str, since_token: str) -> list:
    typ, data = M.search(None, "FROM", f'"{sender}"', "SINCE", since_token)
    if typ != "OK":
        raise RuntimeError(f"IMAP SEARCH 失败 (sender={sender}, since={since_token}): {typ} {data}")
    if not data or not data[0]:
        return []
    return data[0].split()


# ---------- 主流程 ----------

def fetch_emails(
    *,
    storage: Storage,
    since_date: date,
    dry_run: bool = False,
    limit: Optional[int] = None,
) -> dict:
    """
    抓取符合条件的邮件并下载 PDF 附件. 返回 summary dict.
    """
    if limit is not None and limit < 0:
        raise RuntimeError(f"--limit 必须 >= 0, 当前值: {limit}")

    try:
        config = storage.load_config()
    except json.JSONDecodeError as e:
        raise RuntimeError(
            f"config.json 不是合法 JSON ({storage.config_path}): {e}"
        ) from None
    imap_cfg = config.get("imap")
    if not imap_cfg or not isinstance(imap_cfg, dict):
        raise RuntimeError(
            f"config.json 缺少 'imap' 节: {storage.config_path}. "
            f"先跑 onboarding (M0) 或手工填入凭证."
        )
    for key in REQUIRED_IMAP_KEYS:
        if not imap_cfg.get(key):
            raise RuntimeError(f"config.json imap.{key} 缺失或为空.")

    senders = _normalize_senders(imap_cfg.get("senders"))
    if not senders:
        raise RuntimeError("config.json imap.senders 必须至少配置 1 个发件人地址.")

    storage.ensure_dirs()
    tmp_dir = storage.tmp_dir

    since_token = _imap_since_token(since_date)
    downloads = []
    messages_matched = 0
    errors = []

    M = _connect(imap_cfg)
    try:
        try:
            typ, _ = M.select("INBOX", readonly=True)
        except (imaplib.IMAP4.error, OSError) as e:
            raise RuntimeError(f"IMAP SELECT INBOX 异常: {e}") from None
        if typ != "OK":
            raise RuntimeError("IMAP SELECT INBOX 失败 (typ != OK)")

        for sender in senders:
            ids = _search_ids(M, sender, since_token)
            messages_matched += len(ids)
            for msg_id in ids:
                if limit is not None and len(downloads) >= limit:
                    break
                try:
                    typ, msg_data = M.fetch(msg_id, "(RFC822)")
                except (imaplib.IMAP4.error, OSError) as e:
                    errors.append({
                        "message_seq": msg_id.decode("ascii", errors="replace"),
                        "error": f"FETCH 异常: {e}",
                    })
                    continue
                if typ != "OK" or not msg_data or not msg_data[0]:
                    errors.append({
                        "message_seq": msg_id.decode("ascii", errors="replace"),
                        "error": f"FETCH 失败: {typ}",
                    })
                    continue
                raw_bytes = msg_data[0][1]
                try:
                    msg = email.message_from_bytes(raw_bytes)
                except Exception as e:
                    errors.append({
                        "message_seq": msg_id.decode("ascii", errors="replace"),
                        "error": f"邮件解析失败: {e}",
                    })
                    continue
                subject = _decode_str(msg.get("Subject"))
                from_addr = _decode_str(msg.get("From"))
                date_hdr = msg.get("Date") or ""

                for filename, payload in _iter_pdf_parts(msg):
                    safe_name = _ensure_pdf_suffix(_sanitize_filename(filename))
                    dest = _unique_dest(tmp_dir, safe_name)
                    if not dry_run:
                        try:
                            _atomic_write(dest, payload)
                        except OSError as e:
                            errors.append({
                                "message_seq": msg_id.decode("ascii", errors="replace"),
                                "filename": filename,
                                "error": f"写文件失败: {e}",
                            })
                            continue
                    downloads.append({
                        "message_seq": msg_id.decode("ascii", errors="replace"),
                        "from": from_addr,
                        "subject": subject,
                        "date": date_hdr,
                        "filename": filename,
                        "saved_to": str(dest),
                        "size_bytes": len(payload),
                        "matched_sender": sender,
                    })
            if limit is not None and len(downloads) >= limit:
                break
    finally:
        try:
            M.close()
        except Exception:
            pass
        try:
            M.logout()
        except Exception:
            pass

    return {
        "fetcher_version": FETCHER_VERSION,
        "since": since_date.isoformat(),
        "senders": senders,
        "messages_matched": messages_matched,
        "attachments_downloaded": len(downloads),
        "dry_run": dry_run,
        "tmp_dir": str(tmp_dir),
        "downloads": downloads,
        "errors": errors,
    }


# ---------- CLI ----------

def _resolve_since(args) -> date:
    today = date.today()
    if args.since:
        try:
            return date.fromisoformat(args.since)
        except ValueError as e:
            raise SystemExit(f"[ERROR] --since 不是合法 YYYY-MM-DD: {e}")
    if args.days is not None:
        if args.days < 0:
            raise SystemExit("[ERROR] --days 必须 >= 0")
        return today - timedelta(days=args.days)
    # 默认近 1 天: 覆盖跨午夜场景 (凌晨时也能搜到昨天的发票邮件)
    return today - timedelta(days=1)


def main():
    ap = argparse.ArgumentParser(
        description="M1: fetch invoice PDFs from IMAP into ~/.invoice-reimbursement/tmp/ (v0.1).",
    )
    ap.add_argument("--dir", default=None,
                    help="Storage dir override (default: $INVOICE_REIMBURSEMENT_DIR or ~/.invoice-reimbursement)")
    grp = ap.add_mutually_exclusive_group()
    grp.add_argument("--since", help="搜索起始日期 YYYY-MM-DD (默认: 今天)")
    grp.add_argument("--days", type=int,
                     help="搜索过去 N 天 (含今天). 与 --since 互斥.")
    ap.add_argument("--dry-run", action="store_true",
                    help="不写文件, 只列出会下载哪些附件.")
    ap.add_argument("--limit", type=int, default=None,
                    help="最多下载多少个 PDF 附件后停止.")
    ap.add_argument("--pretty", action="store_true")
    args = ap.parse_args()

    since = _resolve_since(args)
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
        sys.exit(2)

    json.dump(summary, sys.stdout, ensure_ascii=False, indent=2 if args.pretty else None)
    sys.stdout.write("\n")


if __name__ == "__main__":
    main()
