#!/usr/bin/env python3
"""
初始化用户家目录下的 ~/.invoice-reimbursement/  —  v0.1

创建:
  ~/.invoice-reimbursement/
    config.json     {} (M0 引导后填充)
    state.json      {"pending": [], "skipped": []}
    history.json    {"processed": []}
    rules.json      <- 从 skill/assets/rules.example.json 复制
    tmp/

默认幂等: 已存在的文件不会被覆盖. --force 强制重置.

Usage:
    python3 init_storage.py [--force] [--dir <override-dir>]
"""

import os
import sys
import argparse
import tempfile
from pathlib import Path
from typing import Optional

sys.path.insert(0, str(Path(__file__).resolve().parent))
from storage import Storage  # noqa: E402

SKILL_ROOT = Path(__file__).resolve().parent.parent
RULES_TEMPLATE = SKILL_ROOT / "assets" / "rules.example.json"


def _atomic_copy(src: Path, dst: Path) -> None:
    """原子复制: 先写到目标目录下的临时文件 -> fsync -> rename. 与 storage.write_json_atomic 同套语义."""
    dst.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp_path = tempfile.mkstemp(
        prefix=dst.name + ".",
        suffix=".tmp",
        dir=str(dst.parent),
    )
    try:
        with os.fdopen(fd, "wb") as out, open(src, "rb") as inp:
            out.write(inp.read())
            out.flush()
            os.fsync(out.fileno())
        os.replace(tmp_path, dst)
    except Exception:
        try:
            os.unlink(tmp_path)
        except OSError:
            pass
        raise


def run_init(*, force: bool = False, base_dir: Optional[Path] = None) -> int:
    # 模板缺失 = 初始化失败, 提前明确报错而不是静默继续
    if not RULES_TEMPLATE.exists():
        print(
            f"[ERROR] Rules template not found at {RULES_TEMPLATE}.\n"
            f"  Init aborted to avoid leaving the storage dir without a rules.json.\n"
            f"  Make sure the skill package is intact (skill/assets/rules.example.json must exist).",
            file=sys.stderr,
        )
        return 3

    s = Storage(base_dir=base_dir)
    s.ensure_dirs()

    created, skipped = [], []

    def maybe_create(path: Path, default_factory):
        if force or not path.exists():
            default_factory()
            created.append(path)
        else:
            skipped.append(path)

    maybe_create(s.config_path,  lambda: s.save_config({}))
    maybe_create(s.state_path,   lambda: s.save_state({"pending": [], "skipped": []}))
    maybe_create(s.history_path, lambda: s.save_history({"processed": []}))
    maybe_create(s.rules_path,   lambda: _atomic_copy(RULES_TEMPLATE, s.rules_path))

    print(f"Storage directory: {s.base_dir}")
    print(f"  tmp/ subdir:     {s.tmp_dir}")
    if created:
        print("Created:")
        for p in created:
            print(f"  + {p}")
    if skipped:
        print("Already exists (use --force to overwrite):")
        for p in skipped:
            print(f"  - {p}")
    print("Done.")
    return 0


def main():
    ap = argparse.ArgumentParser(
        description="Initialize ~/.invoice-reimbursement/ storage directory (v0.1)."
    )
    ap.add_argument("--force", action="store_true",
                    help="Overwrite existing files (DANGER: erases config/state/history/rules)")
    ap.add_argument("--dir", default=None,
                    help="Override storage dir (default: $INVOICE_REIMBURSEMENT_DIR or ~/.invoice-reimbursement)")
    args = ap.parse_args()
    sys.exit(run_init(force=args.force, base_dir=Path(args.dir) if args.dir else None))


if __name__ == "__main__":
    main()
