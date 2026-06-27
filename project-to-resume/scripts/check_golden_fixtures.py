#!/usr/bin/env python3
"""Run evidence-aware strict render checks for golden project-to-resume examples."""

from __future__ import annotations

import subprocess
import sys
import tempfile
from pathlib import Path


SKILL_DIR = Path(__file__).resolve().parents[1]
RENDER = SKILL_DIR / "scripts" / "render_resume_report.py"
PAIRS = [
    ("vue-admin-golden-analysis.json", "vue-admin-project_evidence.json"),
    ("python-api-golden-analysis.json", "python-api-project_evidence.json"),
    ("node-agent-golden-analysis.json", "node-agent-project_evidence.json"),
]


def main() -> None:
    with tempfile.TemporaryDirectory(prefix="project-to-resume-fixtures-") as tmp:
        tmpdir = Path(tmp)
        for analysis_name, evidence_name in PAIRS:
            analysis = SKILL_DIR / "examples" / analysis_name
            evidence = SKILL_DIR / "examples" / "fixtures" / evidence_name
            output = tmpdir / f"{analysis.stem}.html"
            prompt = tmpdir / f"{analysis.stem}.txt"
            subprocess.run(
                [
                    sys.executable,
                    str(RENDER),
                    "--evidence",
                    str(evidence),
                    "--analysis",
                    str(analysis),
                    "--output",
                    str(output),
                    "--prompt-output",
                    str(prompt),
                    "--strict",
                ],
                check=True,
            )
            if not output.exists() or not prompt.exists():
                raise SystemExit(f"missing render outputs for {analysis_name}")
    print("golden fixtures render passed")


if __name__ == "__main__":
    main()
