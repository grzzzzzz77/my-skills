#!/usr/bin/env python3
"""
本地存储层 (S1)  —  v0.1

封装 ~/.invoice-reimbursement/ 下三个 JSON 文件的读写:
  - config.json   IMAP 凭证 + approval_code 等用户配置 (由 M0 引导填充)
  - state.json    当前批次的工作态: pending[] / skipped[]
  - history.json  永久去重记录: processed[]
  - rules.json    报销规则 (由 init_storage 从 skill/assets/rules.example.json 复制)

所有写入走 atomic rename, 避免崩溃留下半截文件.
不实现锁; v0.1 假设同一时刻只有一个 skill 实例在跑.

环境变量 INVOICE_REIMBURSEMENT_DIR 可覆盖存储目录, 便于测试.
"""

STORAGE_VERSION = "0.1"

import os
import json
import tempfile
from pathlib import Path
from typing import Optional


CONFIG_FILE = "config.json"
STATE_FILE = "state.json"
HISTORY_FILE = "history.json"
RULES_FILE = "rules.json"
TMP_DIR = "tmp"


def get_storage_dir() -> Path:
    """默认 ~/.invoice-reimbursement/, 可由 INVOICE_REIMBURSEMENT_DIR 覆盖."""
    override = os.environ.get("INVOICE_REIMBURSEMENT_DIR")
    if override:
        return Path(override).expanduser()
    return Path.home() / ".invoice-reimbursement"


# ---------- 原始读写 ----------

def read_json(path: Path) -> dict:
    """读 JSON; 直接抛 FileNotFoundError / json.JSONDecodeError."""
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def write_json_atomic(path: Path, data, *, indent: int = 2) -> None:
    """
    原子写入: 先写同目录下的临时文件 -> fsync -> rename 覆盖.
    崩溃时要么是旧文件完好, 要么是新文件完好, 不会留半截.
    """
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp_path = tempfile.mkstemp(
        prefix=path.name + ".",
        suffix=".tmp",
        dir=str(path.parent),
    )
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=indent)
            f.flush()
            os.fsync(f.fileno())
        os.replace(tmp_path, path)
    except Exception:
        try:
            os.unlink(tmp_path)
        except OSError:
            pass
        raise


# ---------- 高层封装 ----------

class Storage:
    """统一访问 ~/.invoice-reimbursement/ 下的所有持久化数据."""

    def __init__(self, base_dir: Optional[Path] = None):
        self.base_dir = Path(base_dir).expanduser() if base_dir else get_storage_dir()

    # ----- paths -----
    @property
    def config_path(self) -> Path: return self.base_dir / CONFIG_FILE
    @property
    def state_path(self) -> Path: return self.base_dir / STATE_FILE
    @property
    def history_path(self) -> Path: return self.base_dir / HISTORY_FILE
    @property
    def rules_path(self) -> Path: return self.base_dir / RULES_FILE
    @property
    def tmp_dir(self) -> Path: return self.base_dir / TMP_DIR

    def ensure_dirs(self) -> None:
        self.base_dir.mkdir(parents=True, exist_ok=True)
        self.tmp_dir.mkdir(parents=True, exist_ok=True)

    # ----- config -----
    def load_config(self) -> dict:
        return read_json(self.config_path) if self.config_path.exists() else {}

    def save_config(self, data: dict) -> None:
        write_json_atomic(self.config_path, data)

    # ----- rules -----
    def load_rules(self) -> dict:
        if not self.rules_path.exists():
            raise FileNotFoundError(
                f"Rules file not found: {self.rules_path}. Run init first."
            )
        return read_json(self.rules_path)

    def save_rules(self, data: dict) -> None:
        write_json_atomic(self.rules_path, data)

    # ----- state -----
    def load_state(self) -> dict:
        if not self.state_path.exists():
            return {"pending": [], "skipped": []}
        data = read_json(self.state_path)
        data.setdefault("pending", [])
        data.setdefault("skipped", [])
        return data

    def save_state(self, data: dict) -> None:
        write_json_atomic(self.state_path, data)

    def add_pending(self, record: dict) -> None:
        data = self.load_state()
        data["pending"].append(record)
        self.save_state(data)

    def add_skipped(self, record: dict) -> None:
        data = self.load_state()
        data["skipped"].append(record)
        self.save_state(data)

    def update_pending_status(self, invoice_number: str, **updates) -> bool:
        """按发票号码找记录并更新若干字段. 找到返回 True, 否则 False."""
        data = self.load_state()
        for r in data["pending"]:
            if r.get("invoice_number") == invoice_number:
                r.update(updates)
                self.save_state(data)
                return True
        return False

    # ----- history -----
    def load_history(self) -> dict:
        if not self.history_path.exists():
            return {"processed": []}
        data = read_json(self.history_path)
        data.setdefault("processed", [])
        return data

    def save_history(self, data: dict) -> None:
        write_json_atomic(self.history_path, data)

    def history_has(self, invoice_number: str) -> bool:
        if not invoice_number:
            return False
        return any(
            r.get("invoice_number") == invoice_number
            for r in self.load_history()["processed"]
        )

    def history_append(self, record: dict) -> bool:
        """
        追加到去重记录. 幂等: 同 invoice_number 已存在则跳过, 返回 False;
        实际写入返回 True.
        """
        inv_no = record.get("invoice_number")
        if not inv_no:
            raise ValueError("history_append: record must include 'invoice_number'")
        if self.history_has(inv_no):
            return False
        data = self.load_history()
        data["processed"].append(record)
        self.save_history(data)
        return True


__all__ = [
    "STORAGE_VERSION",
    "Storage",
    "get_storage_dir",
    "read_json",
    "write_json_atomic",
]
