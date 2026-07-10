#!/usr/bin/env python3
"""Exercise the evidence collector against small representative repositories."""

from __future__ import annotations

import json
import subprocess
import sys
import tempfile
from pathlib import Path


SKILL_DIR = Path(__file__).resolve().parents[1]
COLLECTOR = SKILL_DIR / "scripts" / "collect_project_evidence.py"


def write(root: Path, relative: str, content: str) -> None:
    path = root / relative
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content.strip() + "\n", encoding="utf-8")


def collect(root: Path, output: Path) -> dict:
    subprocess.run(
        [sys.executable, str(COLLECTOR), "--repo", str(root), "--output", str(output)],
        check=True,
        capture_output=True,
        text=True,
    )
    evidence = json.loads((output / "project_evidence.json").read_text(encoding="utf-8"))
    for seed in evidence.get("highlight_seeds", []):
        paths = seed.get("example_paths") or []
        assert len(paths) == len(set(paths)), seed
    return evidence


def check_uniapp(base: Path) -> None:
    repo = base / "uniapp-project"
    write(repo, "package.json", json.dumps({
        "dependencies": {"vue": "3.5.0", "@dcloudio/uni-app": "3.0.0"},
    }))
    write(repo, "pages.json", json.dumps({
        "pages": [
            {"path": "pages/home/index"},
            {"path": "pages/order/list"},
        ],
        "subPackages": [{"root": "packageA", "pages": [{"path": "detail/index"}]}],
        "tabBar": {"list": [{"pagePath": "pages/home/index"}]},
    }))
    write(repo, "pages/order/list.vue", """
<script setup lang="ts">
const loadOrders = () => uni.request({ url: '/api/orders' })
const uploadInvoice = () => uni.uploadFile({ url: '/api/upload', filePath: 'invoice.pdf', name: 'file' })
</script>
""")
    write(repo, "src/uni_modules/vendor/drag-tool.js", "const RAG = { memory: true, MCP: true, tools: [] }")
    evidence = collect(repo, base / "uniapp-output")
    signal = (evidence.get("specialized_signals") or {}).get("uniapp") or {}
    assert signal.get("page_count") == 2, signal
    assert signal.get("subpackages") == 1, signal
    assert "pages/order/list.vue" in evidence.get("evidence_paths_index", []), evidence.get("evidence_paths_index")
    assert any(item[0] == "Vue" for item in evidence.get("languages_by_lines", [])), evidence.get("languages_by_lines")
    assert not (evidence.get("specialized_signals") or {}).get("ai_agent"), evidence.get("specialized_signals")


def check_node_agent(base: Path) -> None:
    repo = base / "node-agent-project"
    write(repo, "package.json", json.dumps({
        "dependencies": {
            "express": "5.0.0",
            "openai": "5.0.0",
            "@modelcontextprotocol/sdk": "1.0.0",
        },
    }))
    write(repo, "src/routes/chat.ts", """
import express from 'express'
import { runAgent } from '../agents/customerAgent'
const router = express.Router()
router.post('/chat', async (req, res) => res.json(await runAgent(req.body)))
export default router
""")
    write(repo, "src/agents/customerAgent.ts", """
import { createTicket } from '../tools/ticketTool'
export async function runAgent(input: unknown) {
  const memory = { chat_history: [input] }
  const tools = [{ name: 'create_ticket', execute: createTicket }]
  return { workflow: 'support-agent', memory, tools }
}
""")
    write(repo, "src/tools/ticketTool.ts", """
export function createTicket(input: { title?: string }) {
  if (!input.title) throw new Error('title required')
  return { status: 'draft', title: input.title }
}
""")
    write(repo, "tests/customerAgent.test.ts", "describe('agent', () => { it('validates tools', () => {}) })")
    evidence = collect(repo, base / "node-agent-output")
    specialized = evidence.get("specialized_signals") or {}
    assert specialized.get("node_backend"), specialized
    assert specialized.get("ai_agent"), specialized
    routes = (evidence.get("code_graph") or {}).get("routes") or []
    assert any(item.get("path") == "/chat" for item in routes), routes


def check_python_api(base: Path) -> None:
    repo = base / "python-api-project"
    write(repo, "requirements.txt", "fastapi\npydantic\npytest")
    write(repo, "app/main.py", """
from fastapi import FastAPI
from app.services.invoice import parse_invoice

app = FastAPI()

@app.post('/invoices/parse')
def parse_invoice_route(payload: dict):
    return parse_invoice(payload)
""")
    write(repo, "app/services/invoice.py", """
from pydantic import BaseModel

class Invoice(BaseModel):
    amount: float

def parse_invoice(payload: dict) -> dict:
    invoice = Invoice.model_validate(payload)
    return invoice.model_dump()
""")
    write(repo, "tests/test_invoice.py", "def test_parse_invoice():\n    assert True")
    evidence = collect(repo, base / "python-api-output")
    specialized = evidence.get("specialized_signals") or {}
    assert specialized.get("python_backend"), specialized
    graph = evidence.get("code_graph") or {}
    assert any(item.get("path") == "/invoices/parse" for item in graph.get("routes", [])), graph.get("routes")
    assert any(item.get("source") == "app/main.py" for item in graph.get("ast_summaries", [])), graph.get("ast_summaries")


def main() -> None:
    with tempfile.TemporaryDirectory(prefix="project-to-resume-collector-") as tmp:
        base = Path(tmp)
        check_uniapp(base)
        check_node_agent(base)
        check_python_api(base)
    print("collector fixtures passed: uni-app, Node Agent, Python API")


if __name__ == "__main__":
    main()
