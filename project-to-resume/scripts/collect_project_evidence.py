#!/usr/bin/env python3
"""Collect codebase evidence for project-to-resume.

The script is intentionally dependency-free. It scans a local repository and writes
machine-readable JSON plus a compact Markdown summary for later human/agent review.
"""

from __future__ import annotations

import argparse
import ast
import json
import os
import re
import subprocess
from collections import Counter, defaultdict
from datetime import datetime
from pathlib import Path


IGNORE_DIRS = {
    ".git", "node_modules", "dist", "build", ".next", ".nuxt", ".output",
    "coverage", ".venv", "venv", "__pycache__", ".turbo", ".cache",
    "Pods", "DerivedData", "target", ".gradle", ".idea", ".vscode",
    ".pnpm-store", "vendor", "vendors",
}

IGNORE_FILES = {".DS_Store", "Thumbs.db"}

SIGNAL_EXCLUDE_PREFIXES = ("examples/", "references/", "assets/", "docs/", "doc/")
SIGNAL_EXCLUDE_DIR_PARTS = {
    ".test",
    "doc",
    "docs",
    "fixtures",
    "preskill",
    "screenshots",
    "uni_modules",
    "vendor",
    "vendors",
}
SIGNAL_EXCLUDE_PATH_MARKERS = (
    "src-tauri/resources/skills/",
    "src-tauri/sidecar/.beima/",
)
SIGNAL_EXCLUDE_FILES = {"agents/openai.yaml"}

TEXT_EXTS = {
    ".js", ".jsx", ".ts", ".tsx", ".vue", ".svelte", ".py", ".go", ".rs",
    ".java", ".kt", ".swift", ".php", ".rb", ".cs", ".c", ".cc", ".cpp",
    ".h", ".hpp", ".css", ".scss", ".less", ".html", ".md", ".json",
    ".yaml", ".yml", ".toml", ".xml", ".sql", ".sh", ".mjs", ".cjs",
}

LANG_BY_EXT = {
    ".js": "JavaScript", ".jsx": "React", ".ts": "TypeScript", ".tsx": "React/TypeScript",
    ".vue": "Vue", ".svelte": "Svelte", ".py": "Python", ".go": "Go", ".rs": "Rust",
    ".java": "Java", ".kt": "Kotlin", ".swift": "Swift", ".php": "PHP", ".rb": "Ruby",
    ".cs": "C#", ".css": "CSS", ".scss": "SCSS", ".html": "HTML", ".sql": "SQL",
    ".md": "Markdown", ".mdx": "Markdown", ".json": "JSON", ".yaml": "YAML", ".yml": "YAML",
}

KEY_FILES = [
    "SKILL.md", "CLAUDE.md", "AGENTS.md", "README.md", "README.zh-CN.md", "README.en.md",
    "package.json", "pnpm-lock.yaml", "yarn.lock", "package-lock.json",
    "pyproject.toml", "requirements.txt", "go.mod", "Cargo.toml", "pom.xml",
    "Dockerfile", "docker-compose.yml", "turbo.json", "vite.config.ts",
    "next.config.js", "nuxt.config.ts", "tsconfig.json", ".github/workflows",
]

DOC_NAMES = {"SKILL", "README", "CLAUDE", "AGENTS", "CHANGELOG", "ROADMAP", "DESIGN", "ARCHITECTURE"}

METRIC_RE = re.compile(
    r"(?i)(?:[^。\n\r]{0,28})"
    r"(?:\d+(?:\.\d+)?\s?(?:%|ms|秒|分钟|小时|天|w|万|k|K|M|QPS|RPS|qps|rps|个|条|页|接口|组件|用户|订单|角色|模块|用例|commits?|次))"
    r"(?:[^。\n\r]{0,28})"
)

METRIC_CONTEXT_RE = re.compile(
    r"性能|提升|降低|减少|缩短|增加|达到|支持|覆盖|并发|延迟|耗时|吞吐|"
    r"页面|接口|组件|用户|订单|角色|模块|用例|测试|覆盖率|QPS|RPS|commit|提交|效率|成本",
    re.I,
)

NEGATIVE_METRIC_CONTEXT_RE = re.compile(
    r"不要写|不要直接写|反面|风险|夸大|编造|不严谨|unsupported|unproven|avoid|"
    r"do not|don't|never|unless evidence|risky|bad example|weak example",
    re.I,
)

TECH_KEYWORDS = {
    "vue": "Vue",
    "nuxt": "Nuxt",
    "react": "React",
    "next": "Next.js",
    "svelte": "Svelte",
    "vite": "Vite",
    "typescript": "TypeScript",
    "tailwindcss": "Tailwind CSS",
    "unocss": "UnoCSS",
    "pinia": "Pinia",
    "redux": "Redux",
    "zustand": "Zustand",
    "uni-app": "UniApp",
    "@dcloudio": "UniApp",
    "uview": "uView",
    "uni-ui": "uni-ui",
    "mp-weixin": "微信小程序",
    "express": "Express",
    "koa": "Koa",
    "nestjs": "NestJS",
    "fastify": "Fastify",
    "hono": "Hono",
    "flask": "Flask",
    "django": "Django",
    "fastapi": "FastAPI",
    "sqlalchemy": "SQLAlchemy",
    "prisma": "Prisma",
    "typeorm": "TypeORM",
    "sequelize": "Sequelize",
    "mongoose": "Mongoose",
    "mysql": "MySQL",
    "postgres": "PostgreSQL",
    "mongodb": "MongoDB",
    "redis": "Redis",
    "bullmq": "BullMQ",
    "jwt": "JWT",
    "docker": "Docker",
    "kubernetes": "Kubernetes",
    "playwright": "Playwright",
    "vitest": "Vitest",
    "jest": "Jest",
    "eslint": "ESLint",
    "prettier": "Prettier",
    "openai": "OpenAI",
    "anthropic": "Anthropic",
    "langchain": "LangChain",
    "llamaindex": "LlamaIndex",
    "mcp": "MCP",
    "agent": "Agent",
    "tool_call": "Tool Calling",
    "rag": "RAG",
    "embedding": "Embedding",
}

FRAMEWORK_DEFINITIONS = {
    "Vue": {
        "manifest": ["vue", "nuxt", "pinia", "vue-router", "@vitejs/plugin-vue"],
        "files": ["vue.config.js", "nuxt.config.ts", "nuxt.config.js", "vite.config.ts"],
        "patterns": [r"<script\s+setup", r"defineProps\s*\(", r"createApp\s*\("],
        "role": "frontend",
    },
    "React": {
        "manifest": ["react", "next", "react-router", "zustand", "redux", "@vitejs/plugin-react"],
        "files": ["next.config.js", "next.config.ts", "vite.config.ts"],
        "patterns": [r"from\s+[\"']react[\"']", r"useState\s*\(", r"createRoot\s*\("],
        "role": "frontend",
    },
    "UniApp": {
        "manifest": ["@dcloudio", "uni-app", "uview-ui", "uni-ui"],
        "files": ["manifest.json", "pages.json", "uni.scss", "uni_modules"],
        "patterns": [
            r"uni\.(login|getUserProfile|requestPayment|chooseLocation|uploadFile|chooseImage|request)",
            r"#ifdef\s+(MP-WEIXIN|APP-PLUS|H5)",
            r"subPackages|subpackages|tabBar",
        ],
        "role": "frontend",
    },
    "Node API": {
        "manifest": [
            "express", "koa", "nestjs", "@nestjs", "fastify", "hono", "prisma",
            "typeorm", "sequelize", "mongoose", "bullmq", "redis", "jsonwebtoken",
        ],
        "files": ["server.js", "app.js", "main.ts", "nest-cli.json", "prisma/schema.prisma"],
        "patterns": [r"app\.(get|post|put|delete)", r"router\.(get|post|put|delete)", r"@Controller\s*\(", r"createServer\s*\("],
        "role": "backend",
    },
    "Python API": {
        "manifest": ["fastapi", "flask", "django", "sqlalchemy", "pydantic"],
        "files": ["manage.py", "app.py", "main.py"],
        "patterns": [r"FastAPI\s*\(", r"Flask\s*\(", r"@app\.(get|post|route)"],
        "role": "backend",
    },
    "Testing": {
        "manifest": ["vitest", "jest", "playwright", "pytest", "unittest"],
        "files": ["vitest.config.ts", "jest.config.js", "playwright.config.ts", "pytest.ini"],
        "patterns": [r"\bdescribe\s*\(", r"\bit\s*\(", r"\bdef\s+test_"],
        "role": "quality",
    },
    "AI/Data": {
        "manifest": ["openai", "anthropic", "langchain", "llamaindex", "pandas", "numpy", "sklearn"],
        "files": [],
        "patterns": [r"OpenAI\s*\(", r"Anthropic\s*\(", r"embedding", r"prompt", r"pandas", r"numpy"],
        "role": "ai_data",
    },
    "AI Agent": {
        "manifest": ["openai", "anthropic", "langchain", "llamaindex", "crewai", "autogen", "@modelcontextprotocol", "ai"],
        "files": ["agents", "tools", "prompts", "workflows", "mcp.json"],
        "patterns": [
            r"tool_call|function_call|tools\s*[:=]",
            r"createAgent|AgentExecutor|StateGraph|workflow",
            r"retriever|vectorStore|embedding|\bRAG\b|memory",
            r"system_prompt|PromptTemplate|messages\s*[:=]",
        ],
        "role": "ai_agent",
    },
}

PATTERNS = {
    "frontend_pages": ["pages", "views", "routes"],
    "components": ["components", "widgets"],
    "api_routes": ["api", "routes", "controllers", "server/api"],
    "services": ["services", "service", "api", "client"],
    "state": ["store", "stores", "pinia", "redux", "zustand"],
    "tests": ["test", "tests", "__tests__"],
    "docs": ["docs", "README"],
    "ci_devops": [".github/workflows", "Dockerfile", "docker", "k8s", "helm"],
    "auth_security": ["auth", "permission", "rbac", "guard", "token", "login"],
    "data_ai": ["model", "prompt", "vector", "embedding", "analytics", "chart", "etl"],
    "agent_ai": ["agent", "agents", "tool", "tools", "workflow", "workflows", "mcp", "rag", "retrieval"],
}

TEST_FILE_RE = re.compile(
    r"(^|/)(__tests__|tests?|specs?)(/|$)|"
    r"(^|/)test_[^/]*\.py$|"
    r"(\.|-|_)(test|spec)\.(js|jsx|ts|tsx|mjs|cjs|py|go|java|rb)$|"
    r"(_test\.(py|go)$)|"
    r"(test\.(py|js|jsx|ts|tsx)$)",
    re.I,
)

LOW_SIGNAL_EVIDENCE_FILENAMES = {"build.mjs"}
LOW_SIGNAL_EVIDENCE_PREFIXES = ("repro-",)

CODE_GRAPH_EXTS = {
    ".js", ".jsx", ".ts", ".tsx", ".vue", ".svelte", ".py", ".go", ".java",
    ".kt", ".swift", ".php", ".rb", ".mjs", ".cjs",
}

ENTRYPOINT_RE = re.compile(r"(^|/)(main|index|app|server|router|routes|client)\.(js|jsx|ts|tsx|mjs|cjs|py|go|java)$", re.I)

JS_IMPORT_RE = re.compile(r"(?:import\s+.*?\s+from\s+|import\s*\(|require\s*\()\s*[\"']([^\"']+)[\"']", re.S)
PY_IMPORT_RE = re.compile(r"^\s*(?:from\s+([.\w]+)\s+import|import\s+([.\w]+))", re.M)
HTTP_ROUTE_RE = re.compile(
    r"(?:app|router|server|fastify|api)\.(get|post|put|patch|delete|options)\s*\(\s*[\"'`]([^\"'`]+)[\"'`]|"
    r"@(Get|Post|Put|Patch|Delete|Options)\s*\(\s*[\"'`]([^\"'`]*)[\"'`]|"
    r"@(app|router)\.(route|get|post|put|patch|delete)\s*\(\s*[\"']([^\"']+)[\"']",
    re.I,
)
ROUTE_PATH_RE = re.compile(r"\bpath\s*:\s*[\"'`]([^\"'`]+)[\"'`]")
PY_ROUTE_RE = re.compile(r"@(?:app|router|blueprint)\.(route|get|post|put|patch|delete)\s*\(\s*[\"']([^\"']+)[\"']", re.I)
API_CALL_RE = re.compile(
    r"(fetch)\s*\(\s*[\"'`]([^\"'`]+)[\"'`]|"
    r"(axios|request)\.(get|post|put|patch|delete)\s*\(\s*[\"'`]([^\"'`]+)[\"'`]|"
    r"(axios|request)\s*\(\s*\{[^}]*\burl\s*:\s*[\"'`]([^\"'`]+)[\"'`]",
    re.I | re.S,
)
UNI_API_RE = re.compile(
    r"\buni\.(login|getUserProfile|getUserInfo|requestPayment|chooseLocation|openLocation|"
    r"uploadFile|downloadFile|chooseImage|request|navigateTo|switchTab|showToast)\b"
)
UNI_CONDITION_RE = re.compile(r"#(?:ifdef|ifndef)\s+([A-Z0-9_-]+)")
NODE_BACKEND_DEPS = {
    "express", "koa", "fastify", "hono", "nestjs", "@nestjs/core", "@nestjs/common",
    "prisma", "@prisma/client", "typeorm", "sequelize", "mongoose", "mysql2", "pg",
    "redis", "ioredis", "bull", "bullmq", "jsonwebtoken", "passport", "zod", "joi",
}
AI_AGENT_DEPS = {
    "openai", "@ai-sdk/openai", "ai", "anthropic", "@anthropic-ai/sdk", "langchain",
    "@langchain/core", "@langchain/openai", "llamaindex", "crewai", "autogen",
    "@modelcontextprotocol/sdk", "chromadb", "pinecone-client", "@pinecone-database/pinecone",
}
AI_AGENT_PATTERNS = {
    "tool_calling": re.compile(r"tool_call|function_call|tools\s*[:=]|Tool\s*\(", re.I),
    "prompt_engineering": re.compile(r"system_prompt|PromptTemplate|messages\s*[:=]|role\s*:\s*[\"']system", re.I),
    "rag_retrieval": re.compile(r"retriever|vectorStore|similaritySearch|\bRAG\b|context\s+window", re.I),
    "memory_state": re.compile(r"memory|checkpoint|conversation_state|chat_history", re.I),
    "workflow_orchestration": re.compile(r"StateGraph|createAgent|AgentExecutor|workflow|planner|executor", re.I),
    "mcp_integration": re.compile(r"modelcontextprotocol|mcp\.|\bMCP\b", re.I),
}

COMMON_DOMAIN_WORDS = {
    "src", "app", "apps", "pages", "page", "views", "view", "components", "component",
    "widgets", "routes", "router", "api", "apis", "service", "services", "client",
    "server", "store", "stores", "utils", "lib", "libs", "common", "shared", "index",
    "main", "assets", "styles", "hooks", "composables", "models", "model", "types",
    "constants", "config", "configs", "tests", "test", "spec", "docs", "references",
    "script", "scripts",
}


def run(cmd: list[str], cwd: Path) -> str:
    try:
        return subprocess.check_output(cmd, cwd=str(cwd), text=True, stderr=subprocess.DEVNULL).strip()
    except Exception:
        return ""


def is_ignored(path: Path) -> bool:
    return any(part in IGNORE_DIRS for part in path.parts)


def is_signal_excluded(rel: str) -> bool:
    normalized = rel.replace("\\", "/").lstrip("./")
    parts = normalized.split("/")
    return (
        normalized in SIGNAL_EXCLUDE_FILES
        or normalized.startswith(SIGNAL_EXCLUDE_PREFIXES)
        or any(part in SIGNAL_EXCLUDE_DIR_PARTS for part in parts)
        or any(marker in normalized for marker in SIGNAL_EXCLUDE_PATH_MARKERS)
    )


def is_signal_source_file(path: Path, rel: str) -> bool:
    if is_signal_excluded(rel):
        return False
    if path.suffix.lower() in CODE_GRAPH_EXTS:
        return True
    return rel in {
        "package.json", "pyproject.toml", "requirements.txt",
        "pages.json", "manifest.json", "mcp.json",
    }


def is_test_path(rel: str) -> bool:
    return bool(TEST_FILE_RE.search(rel.replace("\\", "/")))


def is_low_signal_evidence_path(rel: str) -> bool:
    name = Path(rel).name.lower()
    return name in LOW_SIGNAL_EVIDENCE_FILENAMES or name.startswith(LOW_SIGNAL_EVIDENCE_PREFIXES)


def prioritize_evidence_paths(paths: list[str]) -> list[str]:
    unique = []
    seen = set()
    for rel in paths:
        normalized = rel.replace("\\", "/")
        if normalized in seen:
            continue
        seen.add(normalized)
        unique.append(normalized)

    def priority(rel: str) -> tuple:
        lowered = rel.lower()
        core_source = any(marker in f"/{lowered}" for marker in ("/src/", "/app/"))
        return (
            is_test_path(rel),
            is_low_signal_evidence_path(rel),
            0 if core_source else 1,
            rel.count("/"),
            lowered,
        )

    return sorted(unique, key=priority)


def iter_files(root: Path):
    for path in root.rglob("*"):
        if is_ignored(path.relative_to(root)):
            continue
        if path.is_file():
            if path.name in IGNORE_FILES:
                continue
            yield path


def count_lines(path: Path) -> int:
    if path.suffix.lower() not in TEXT_EXTS:
        return 0
    try:
        with path.open("r", encoding="utf-8", errors="ignore") as f:
            return sum(1 for _ in f)
    except Exception:
        return 0


def load_json(path: Path):
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return None


def read_text_sample(path: Path, max_chars: int = 6000) -> str:
    try:
        return path.read_text(encoding="utf-8", errors="ignore")[:max_chars]
    except Exception:
        return ""


def is_doc_candidate(path: Path, rel: str) -> bool:
    stem = path.stem.upper()
    if path.suffix.lower() not in {".md", ".mdx", ".txt", ".rst"}:
        return False
    if stem in DOC_NAMES:
        return True
    return rel.startswith("docs/") or rel.startswith("doc/")


def first_meaningful_lines(text: str, limit: int = 5) -> list[str]:
    lines = []
    for raw in text.splitlines():
        line = raw.strip().strip("#").strip()
        if not line or line.startswith(("!", "[", "<")):
            continue
        if line in {"---", "..."} or line.startswith(("name:", "description:", "metadata:")):
            continue
        if len(line) > 180:
            line = line[:177] + "..."
        lines.append(line)
        if len(lines) >= limit:
            break
    return lines


def collect_docs(repo: Path, files: list[Path]) -> list[dict]:
    docs = []
    for path in files:
        rel = str(path.relative_to(repo))
        if not is_doc_candidate(path, rel):
            continue
        text = read_text_sample(path)
        if not text:
            continue
        docs.append({
            "path": rel,
            "headings_or_summary_lines": first_meaningful_lines(text),
            "char_sampled": len(text),
        })
    return sorted(docs, key=lambda item: (0 if item["path"].lower().startswith("readme") else 1, item["path"]))[:24]


def extract_metric_candidates(repo: Path, docs: list[dict], max_items: int = 40) -> list[dict]:
    candidates = []
    for doc in docs:
        path = repo / doc["path"]
        text = read_text_sample(path, max_chars=12000)
        for match in METRIC_RE.finditer(text):
            snippet = " ".join(match.group(0).split())
            lowered = snippet.lower()
            start, end = match.span()
            window = " ".join(text[max(0, start - 80): min(len(text), end + 80)].split())
            if (
                len(snippet) < 4
                or "bullet" in lowered
                or not METRIC_CONTEXT_RE.search(snippet)
                or NEGATIVE_METRIC_CONTEXT_RE.search(window)
            ):
                continue
            candidates.append({"source": doc["path"], "text": snippet[:160]})
            if len(candidates) >= max_items:
                return candidates
    return candidates


def detect_tech_keywords(evidence_bits: list[str], manifests: dict, key_files: list[str]) -> list[str]:
    found = set()
    haystack = " ".join(evidence_bits + key_files).lower()
    for manifest in manifests.values():
        if isinstance(manifest, dict):
            for field in ("dependencies", "devDependencies", "scripts"):
                values = manifest.get(field) or []
                if isinstance(values, list):
                    haystack += " " + " ".join(values).lower()
    for needle, label in TECH_KEYWORDS.items():
        if needle.lower() in haystack:
            found.add(label)
    return sorted(found)


def manifest_names(manifests: dict) -> set[str]:
    names = set()
    for manifest in manifests.values():
        if isinstance(manifest, dict):
            for field in ("dependencies", "devDependencies"):
                for value in manifest.get(field) or []:
                    names.add(str(value).lower())
        elif isinstance(manifest, list):
            for item in manifest:
                if not isinstance(item, dict):
                    continue
                for field in ("dependencies", "devDependencies"):
                    for value in item.get(field) or []:
                        names.add(str(value).lower())
    return names


def rel_has_named_file(rels: list[str], file_name: str) -> bool:
    wanted = file_name.strip("/").replace("\\", "/")
    if wanted in rels:
        return True
    if "/" in wanted:
        return any(rel.endswith("/" + wanted) for rel in rels)
    return any(wanted in rel.split("/") for rel in rels)


def dependency_matches(wanted: str, actual: str) -> bool:
    wanted_lower = wanted.lower()
    actual_lower = actual.lower()
    return actual_lower == wanted_lower or actual_lower.startswith(wanted_lower + "/")


def detect_framework_profiles(repo: Path, files: list[Path], manifests: dict) -> list[dict]:
    deps = manifest_names(manifests)
    rels = [
        str(path.relative_to(repo)).replace("\\", "/")
        for path in files
        if not is_signal_excluded(str(path.relative_to(repo)).replace("\\", "/"))
    ]
    sample_text = ""
    for path in files[:300]:
        rel = str(path.relative_to(repo)).replace("\\", "/")
        if is_signal_excluded(rel) or rel.startswith("scripts/"):
            continue
        if path.suffix.lower() in CODE_GRAPH_EXTS or path.name in {"package.json", "pyproject.toml", "requirements.txt"}:
            sample_text += "\n" + read_text_sample(path, max_chars=2500)
            if len(sample_text) > 160000:
                break

    profiles = []
    lower_sample = sample_text.lower()
    for name, spec in FRAMEWORK_DEFINITIONS.items():
        signals = []
        for dep in spec["manifest"]:
            dep_lower = dep.lower()
            if any(dependency_matches(dep_lower, item) for item in deps):
                signals.append(f"dependency:{dep}")
        for file_name in spec["files"]:
            if rel_has_named_file(rels, file_name):
                signals.append(f"file:{file_name}")
        for pattern in spec["patterns"]:
            if re.search(pattern, sample_text, re.I):
                signals.append(f"pattern:{pattern}")
        if name == "Node API" and not any(signal.startswith(("dependency:", "file:")) for signal in signals):
            continue
        if name == "AI Agent":
            has_dependency = any(signal.startswith("dependency:") for signal in signals)
            if not has_dependency and len(signals) < 2:
                continue
        if signals:
            profiles.append({
                "name": name,
                "role": spec["role"],
                "confidence": min(1.0, round(0.35 + 0.2 * len(signals), 2)),
                "signals": signals[:10],
            })
    profiles.sort(key=lambda item: item["confidence"], reverse=True)
    return profiles


def package_dependency_names(manifests: dict) -> set[str]:
    deps = set()
    for manifest in manifests.values():
        if not isinstance(manifest, dict):
            if isinstance(manifest, list):
                for entry in manifest:
                    if not isinstance(entry, dict):
                        continue
                    for field in ("dependencies", "devDependencies"):
                        for item in entry.get(field) or []:
                            deps.add(str(item).lower())
            continue
        for field in ("dependencies", "devDependencies"):
            for item in manifest.get(field) or []:
                deps.add(str(item).lower())
    return deps


def rel_file_list(repo: Path, files: list[Path]) -> list[str]:
    return [str(path.relative_to(repo)).replace("\\", "/") for path in files]


def signal_files(repo: Path, files: list[Path]) -> list[Path]:
    result = []
    for path in files:
        rel = str(path.relative_to(repo)).replace("\\", "/")
        if is_signal_source_file(path, rel):
            result.append(path)
    return result


def limited_source_text(repo: Path, files: list[Path], needles: tuple[str, ...], max_files: int = 400) -> str:
    chunks = []
    scanned = 0
    for path in files:
        rel = str(path.relative_to(repo)).replace("\\", "/")
        lowered = rel.lower()
        if not is_signal_source_file(path, rel):
            continue
        if not any(needle in lowered for needle in needles) and path.suffix.lower() not in CODE_GRAPH_EXTS:
            continue
        scanned += 1
        if scanned > max_files:
            break
        chunks.append(read_text_sample(path, max_chars=12000))
        if sum(len(chunk) for chunk in chunks) > 260000:
            break
    return "\n".join(chunks)


def collect_uniapp_signals(repo: Path, files: list[Path], deps: set[str]) -> dict:
    source_files = signal_files(repo, files)
    rels = rel_file_list(repo, source_files)
    pages_json = load_json(repo / "pages.json") if (repo / "pages.json").exists() else None
    manifest_json = load_json(repo / "manifest.json") if (repo / "manifest.json").exists() else None
    source_text = limited_source_text(repo, source_files, ("pages", "components", "uni", "store", "api", "service"))
    api_counts = Counter(match.group(1) for match in UNI_API_RE.finditer(source_text))
    condition_counts = Counter(match.group(1) for match in UNI_CONDITION_RE.finditer(source_text))
    ui_libraries = sorted(
        item for item in {"uview-ui", "uview-plus", "@dcloudio/uni-ui", "uni-ui"}
        if item in deps or any(item in rel.lower() for rel in rels)
    )
    result: dict = {}
    if isinstance(pages_json, dict):
        pages = pages_json.get("pages") or []
        subpackages = pages_json.get("subPackages") or pages_json.get("subpackages") or []
        tabbar = (pages_json.get("tabBar") or {}).get("list") or []
        result.update({
            "pages_json": "pages.json",
            "page_count": len(pages) if isinstance(pages, list) else 0,
            "subpackages": len(subpackages) if isinstance(subpackages, list) else 0,
            "tabbar_items": len(tabbar) if isinstance(tabbar, list) else 0,
            "example_pages": [
                item.get("path") for item in pages[:10]
                if isinstance(item, dict) and item.get("path")
            ],
        })
    if isinstance(manifest_json, dict):
        platforms = [
            key for key in ("mp-weixin", "mp-alipay", "mp-baidu", "h5", "app-plus")
            if key in manifest_json
        ]
        if platforms:
            result["manifest_platforms"] = platforms
    if api_counts:
        result["uni_api_calls"] = api_counts.most_common(20)
    if condition_counts:
        result["conditional_platforms"] = condition_counts.most_common(20)
    if ui_libraries:
        result["ui_libraries"] = ui_libraries
    return result


def collect_node_backend_signals(repo: Path, files: list[Path], deps: set[str]) -> dict:
    source_files = signal_files(repo, files)
    rels = rel_file_list(repo, source_files)
    backend_deps = sorted(dep for dep in deps if dep in NODE_BACKEND_DEPS or dep.startswith("@nestjs/"))
    buckets = {
        "routes": ["route", "routes", "router"],
        "controllers": ["controller", "controllers"],
        "services": ["service", "services"],
        "middleware": ["middleware", "middlewares", "guard", "guards"],
        "models_or_schema": ["model", "models", "schema", "schemas", "entity", "entities", "prisma"],
        "jobs_or_queues": ["job", "jobs", "queue", "queues", "worker", "workers"],
        "auth": ["auth", "login", "jwt", "passport", "permission", "rbac"],
    }
    candidates = {}
    for bucket, needles in buckets.items():
        matches = prioritize_evidence_paths([
            rel for rel in rels if any(needle in rel.lower() for needle in needles)
        ])
        if matches:
            candidates[bucket] = matches[:12]
    source_hit_count = sum(len(values) for values in candidates.values())
    if not backend_deps:
        return {}
    return {
        "dependencies": backend_deps[:30],
        "confidence": min(1.0, round(0.25 + 0.25 * bool(backend_deps) + 0.08 * min(source_hit_count, 6), 2)),
        "basis": "dependency+source" if backend_deps and source_hit_count else ("dependency_only" if backend_deps else "source_only"),
        "layer_candidates": candidates,
        "database_or_cache": sorted(dep for dep in backend_deps if dep in {"prisma", "@prisma/client", "typeorm", "sequelize", "mongoose", "mysql2", "pg", "redis", "ioredis"})[:20],
        "auth_or_validation": sorted(dep for dep in backend_deps if dep in {"jsonwebtoken", "passport", "zod", "joi"})[:20],
    }


def path_matches_needles(rel: str, needles: list[str]) -> bool:
    lowered = rel.lower()
    for needle in needles:
        item = needle.lower()
        if item in {"ai", "api", "mcp", "rag", "route", "routes", "router"}:
            if re.search(rf"(^|[/_.-]){re.escape(item)}", lowered):
                return True
        elif item in lowered:
            return True
    return False


def collect_python_backend_signals(repo: Path, files: list[Path], deps: set[str]) -> dict:
    source_files = signal_files(repo, files)
    rels = rel_file_list(repo, source_files)
    py_deps = sorted(dep for dep in deps if dep in {"fastapi", "flask", "django", "sqlalchemy", "pydantic", "httpx", "pytest"})
    buckets = {
        "routes": ["routes", "router", "main.py"],
        "proxy_or_gateway": ["proxy", "forwarder", "gateway"],
        "auth": ["auth", "sign", "identity"],
        "quota_or_metering": ["quota", "metering", "usage"],
        "providers": ["provider", "providers", "registry"],
        "tests": ["test_", "tests"],
    }
    candidates = {}
    for bucket, needles in buckets.items():
        matches = prioritize_evidence_paths([
            rel for rel in rels
            if rel.endswith(".py") and path_matches_needles(rel, needles)
        ])
        if matches:
            candidates[bucket] = matches[:12]
    source_hit_count = sum(len(values) for values in candidates.values())
    if not py_deps and source_hit_count < 3:
        return {}
    return {
        "dependencies": py_deps[:30],
        "confidence": min(1.0, round(0.3 + 0.25 * bool(py_deps) + 0.07 * min(source_hit_count, 6), 2)),
        "basis": "dependency+source" if py_deps and source_hit_count else ("dependency_only" if py_deps else "source_only"),
        "layer_candidates": candidates,
    }


def collect_ai_agent_signals(repo: Path, files: list[Path], deps: set[str]) -> dict:
    source_files = signal_files(repo, files)
    rels = rel_file_list(repo, source_files)
    agent_deps = sorted(dep for dep in deps if dep in AI_AGENT_DEPS or dep.startswith("@langchain/"))
    buckets = {
        "agents": ["agent", "agents"],
        "tools": ["tool", "tools", "function"],
        "prompts": ["prompt", "prompts", "system"],
        "workflows": ["workflow", "workflows", "planner", "executor", "graph"],
        "rag_retrieval": ["rag", "retrieval", "retriever", "vector", "embedding"],
        "memory": ["memory", "history", "checkpoint"],
        "mcp": ["mcp", "modelcontextprotocol"],
    }
    file_candidates = {}
    for bucket, needles in buckets.items():
        matches = prioritize_evidence_paths([rel for rel in rels if path_matches_needles(rel, needles)])
        if matches:
            file_candidates[bucket] = matches[:12]
    source_text = limited_source_text(repo, source_files, ("agent", "tool", "prompt", "workflow", "rag", "vector", "memory", "mcp", "llm", "ai"))
    pattern_counts = {
        name: len(pattern.findall(source_text))
        for name, pattern in AI_AGENT_PATTERNS.items()
    }
    pattern_counts = {key: value for key, value in pattern_counts.items() if value}
    source_candidate_count = sum(len(values) for values in file_candidates.values())
    source_hit_count = source_candidate_count + sum(pattern_counts.values())
    if not agent_deps and (len(file_candidates) < 2 or not pattern_counts):
        return {}
    return {
        "dependencies": agent_deps[:30],
        "confidence": min(1.0, round(0.25 + 0.25 * bool(agent_deps) + 0.06 * min(source_hit_count, 8), 2)),
        "basis": "dependency+source" if agent_deps and source_hit_count else ("dependency_only" if agent_deps else "source_only"),
        "file_candidates": file_candidates,
        "pattern_counts": pattern_counts,
    }


def collect_specialized_signals(repo: Path, files: list[Path], manifests: dict) -> dict:
    deps = package_dependency_names(manifests)
    signals = {
        "uniapp": collect_uniapp_signals(repo, files, deps),
        "node_backend": collect_node_backend_signals(repo, files, deps),
        "python_backend": collect_python_backend_signals(repo, files, deps),
        "ai_agent": collect_ai_agent_signals(repo, files, deps),
    }
    return {key: value for key, value in signals.items() if value}


def sensitivity_signals(rel_files: list[str]) -> list[str]:
    signals = []
    for rel in rel_files:
        lowered = rel.lower()
        if any(part in lowered for part in [".env", "secret", "credential", "customer", "internal"]):
            signals.append(rel)
        if len(signals) >= 20:
            break
    return signals


def python_ast_summary(text: str, rel: str) -> dict | None:
    try:
        tree = ast.parse(text)
    except SyntaxError:
        return None

    imports = []
    functions = []
    classes = []
    decorators = []
    route_decorators = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                imports.append(alias.name)
        elif isinstance(node, ast.ImportFrom):
            imports.append(node.module or "")
        elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            functions.append(node.name)
            for dec in node.decorator_list:
                name = ast.unparse(dec) if hasattr(ast, "unparse") else ""
                if name:
                    decorators.append(name[:120])
                    if any(token in name.lower() for token in [".route", ".get", ".post", ".put", ".patch", ".delete"]):
                        route_decorators.append({"function": node.name, "decorator": name[:160]})
        elif isinstance(node, ast.ClassDef):
            classes.append(node.name)
            for dec in node.decorator_list:
                name = ast.unparse(dec) if hasattr(ast, "unparse") else ""
                if name:
                    decorators.append(name[:120])

    return {
        "source": rel,
        "imports": sorted(set(x for x in imports if x))[:30],
        "functions": functions[:40],
        "classes": classes[:30],
        "decorators": sorted(set(decorators))[:30],
        "route_decorators": route_decorators[:30],
    }


def is_code_graph_candidate(path: Path) -> bool:
    return path.suffix.lower() in CODE_GRAPH_EXTS


def infer_file_route(rel: str) -> str | None:
    path = rel.replace("\\", "/")
    if Path(path).suffix.lower() in {".py", ".go", ".java", ".kt", ".rb", ".php"}:
        return None
    for prefix in ("pages/", "views/", "app/", "routes/"):
        if path.startswith(prefix):
            route = path[len(prefix):]
            route = re.sub(r"\.(vue|svelte|jsx?|tsx?|mdx?)$", "", route)
            route = route.replace("/index", "")
            route = re.sub(r"\[([^\]]+)\]", r":\1", route)
            route = "/" + route.strip("/")
            return route if route != "/" else "/"
    return None


def route_matches(text: str, rel: str) -> list[dict]:
    routes = []
    file_route = infer_file_route(rel)
    if file_route:
        routes.append({"source": rel, "method": "file", "path": file_route})
    for match in HTTP_ROUTE_RE.finditer(text):
        groups = match.groups()
        if groups[0]:
            method, route = groups[0], groups[1]
        elif groups[2]:
            method, route = groups[2], groups[3] or "/"
        else:
            method, route = groups[5] or "route", groups[6]
        routes.append({"source": rel, "method": method.upper(), "path": route or "/"})
    for match in ROUTE_PATH_RE.finditer(text):
        routes.append({"source": rel, "method": "client", "path": match.group(1)})
    return routes


def api_call_matches(text: str, rel: str) -> list[dict]:
    calls = []
    for match in API_CALL_RE.finditer(text):
        groups = [group for group in match.groups() if group]
        if not groups:
            continue
        url = groups[-1]
        client = groups[0]
        calls.append({"source": rel, "client": client, "target": url[:160]})
    return calls


def import_targets(text: str, suffix: str) -> list[str]:
    targets = []
    if suffix in {".js", ".jsx", ".ts", ".tsx", ".vue", ".svelte", ".mjs", ".cjs"}:
        targets.extend(match.group(1) for match in JS_IMPORT_RE.finditer(text))
    elif suffix == ".py":
        for left, right in PY_IMPORT_RE.findall(text):
            targets.append(left or right)
    return [target for target in targets if target]


def is_local_import(target: str) -> bool:
    return target.startswith((".", "@/","~/", "#/")) or target.startswith(("src/", "app/", "lib/", "components/", "services/"))


def domain_tokens(rel: str) -> list[str]:
    raw_parts = re.split(r"[/_.\-\[\]{}]+", rel.lower())
    tokens = []
    for part in raw_parts:
        if len(part) < 3 or part in COMMON_DOMAIN_WORDS or part.isdigit():
            continue
        if part not in tokens:
            tokens.append(part)
    return tokens[:6]


def collect_code_graph(repo: Path, files: list[Path], max_files: int = 900) -> dict:
    entrypoints = []
    routes = []
    api_calls = []
    import_edges = []
    ast_summaries = []
    domain_files: dict[str, dict[str, list[str]]] = defaultdict(lambda: defaultdict(list))

    scanned = 0
    for path in files:
        rel = str(path.relative_to(repo))
        if not is_code_graph_candidate(path) or not is_signal_source_file(path, rel):
            continue
        is_test = is_test_path(rel)
        scanned += 1
        if scanned > max_files:
            break
        text = read_text_sample(path, max_chars=20000)
        if not is_test and ENTRYPOINT_RE.search(rel) and len(entrypoints) < 40:
            entrypoints.append(rel)
        if not is_test and path.suffix.lower() == ".py" and len(ast_summaries) < 80:
            summary = python_ast_summary(text, rel)
            if summary and (summary["classes"] or summary["functions"] or summary["route_decorators"]):
                ast_summaries.append(summary)
        if not is_test:
            for route in route_matches(text, rel):
                if len(routes) < 120:
                    routes.append(route)
            for call in api_call_matches(text, rel):
                if len(api_calls) < 120:
                    api_calls.append(call)
        if is_test:
            continue
        for target in import_targets(text, path.suffix.lower()):
            if is_local_import(target) and len(import_edges) < 220:
                import_edges.append({"source": rel, "target": target})

        lowered = rel.lower()
        role = "other"
        if any(part in lowered for part in ["page", "pages", "view", "views", "route", "routes"]):
            role = "page_or_route"
        elif any(part in lowered for part in ["service", "api", "client", "request"]):
            role = "service_or_api"
        elif any(part in lowered for part in ["store", "redux", "pinia", "zustand"]):
            role = "state"
        elif any(part in lowered for part in ["model", "schema", "entity", "repository"]):
            role = "model_or_data"
        elif any(part in lowered for part in ["component", "widget"]):
            role = "component"
        for token in domain_tokens(rel):
            bucket = domain_files[token][role]
            if len(bucket) < 8:
                bucket.append(rel)

    domain_candidates = []
    for domain, groups in domain_files.items():
        score = sum(len(paths) for paths in groups.values())
        if score < 2:
            continue
        domain_candidates.append({
            "domain": domain,
            "score": score,
            "groups": {role: paths for role, paths in groups.items()},
        })
    domain_candidates.sort(key=lambda item: item["score"], reverse=True)

    return {
        "scanned_code_files": min(scanned, max_files),
        "entrypoints": entrypoints[:40],
        "routes": routes[:120],
        "api_calls": api_calls[:120],
        "local_import_edges": import_edges[:220],
        "ast_summaries": ast_summaries[:80],
        "business_flow_candidates": domain_candidates[:30],
    }


def manifest_summary(root: Path) -> dict:
    summaries = {}
    package_json = root / "package.json"
    if package_json.exists():
        data = load_json(package_json) or {}
        deps = sorted(list((data.get("dependencies") or {}).keys()))
        dev_deps = sorted(list((data.get("devDependencies") or {}).keys()))
        summaries["package.json"] = {
            "name": data.get("name"),
            "scripts": sorted((data.get("scripts") or {}).keys()),
            "dependencies": deps[:40],
            "devDependencies": dev_deps[:40],
        }
    requirements = root / "requirements.txt"
    if requirements.exists():
        deps = []
        for raw in read_text_sample(requirements, max_chars=20000).splitlines():
            line = raw.strip()
            if not line or line.startswith("#") or line.startswith("-"):
                continue
            dep = re.split(r"[<>=~!\[]", line, 1)[0].strip()
            if dep:
                deps.append(dep)
        summaries["requirements.txt"] = {"present": True, "dependencies": sorted(set(deps))[:80]}

    pyproject = root / "pyproject.toml"
    if pyproject.exists():
        text = read_text_sample(pyproject, max_chars=40000)
        deps = sorted(set(re.findall(r"['\"]([A-Za-z0-9_.-]+)(?:[<>=~!][^'\"]*)?['\"]", text)))[:120]
        summaries["pyproject.toml"] = {"present": True, "size": pyproject.stat().st_size, "dependencies": deps}

    for name in ["go.mod", "Cargo.toml", "pom.xml"]:
        path = root / name
        if path.exists():
            summaries[name] = {"present": True, "size": path.stat().st_size}
    return summaries


def collect_workspace_projects(root: Path, files: list[Path]) -> list[dict]:
    workspace_manifest_names = {
        "package.json", "pyproject.toml", "requirements.txt", "Cargo.toml",
        "go.mod", "pom.xml", "Dockerfile", "docker-compose.yml", "vite.config.ts",
    }
    grouped: dict[str, set[str]] = defaultdict(set)
    for path in files:
        rel = str(path.relative_to(root)).replace("\\", "/")
        if path.name in workspace_manifest_names and not is_signal_excluded(rel):
            rel_dir = str(path.parent.relative_to(root)).replace("\\", "/") or "."
            grouped[rel_dir].add(path.name)

    projects = []
    for rel_dir, names in sorted(grouped.items(), key=lambda item: (item[0].count("/"), item[0])):
        project_root = root if rel_dir == "." else root / rel_dir
        package = load_json(project_root / "package.json") if "package.json" in names else None
        deps: list[str] = []
        dev_deps: list[str] = []
        scripts: list[str] = []
        package_name = None
        if isinstance(package, dict):
            package_name = package.get("name")
            deps = sorted(list((package.get("dependencies") or {}).keys()))[:60]
            dev_deps = sorted(list((package.get("devDependencies") or {}).keys()))[:60]
            scripts = sorted((package.get("scripts") or {}).keys())[:30]

        py_deps: list[str] = []
        pyproject = project_root / "pyproject.toml"
        if "pyproject.toml" in names and pyproject.exists():
            text = read_text_sample(pyproject, max_chars=40000)
            py_deps = sorted(set(re.findall(r"['\"]([A-Za-z0-9_.-]+)(?:[<>=~!][^'\"]*)?['\"]", text)))[:80]

        all_deps_lower = {item.lower() for item in deps + dev_deps + py_deps}
        project_type = []
        if {"react", "@vitejs/plugin-react", "vite"} & all_deps_lower or "vite.config.ts" in names:
            project_type.append("frontend")
        if {"fastapi", "flask", "django", "sqlalchemy"} & all_deps_lower or "pyproject.toml" in names:
            project_type.append("python-backend")
        if "Cargo.toml" in names or rel_dir.endswith("src-tauri"):
            project_type.append("rust-tauri")
        if {"openai", "anthropic", "@modelcontextprotocol/sdk", "ai"} & all_deps_lower:
            project_type.append("ai-app")

        projects.append({
            "path": rel_dir,
            "name": package_name or (project_root.name if rel_dir != "." else root.name),
            "manifest_files": sorted(names),
            "project_type": project_type or ["unknown"],
            "dependencies": deps[:40] or py_deps[:40],
            "devDependencies": dev_deps[:40],
            "scripts": scripts,
        })
        if len(projects) >= 40:
            break
    return projects


def git_summary(root: Path, author: str | None) -> dict:
    inside = run(["git", "rev-parse", "--is-inside-work-tree"], root) == "true"
    if not inside:
        return {"is_git": False}

    summary: dict = {
        "is_git": True,
        "branch": run(["git", "branch", "--show-current"], root),
        "remote": sanitize_remote(run(["git", "remote", "get-url", "origin"], root)),
        "total_commits": int(run(["git", "rev-list", "--count", "HEAD"], root) or "0"),
    }

    authors = run(["git", "shortlog", "-sne", "HEAD"], root)
    summary["authors"] = [line.strip() for line in authors.splitlines()[:20] if line.strip()]

    if author:
        log_range = ["git", "log", f"--author={author}", "--pretty=format:%H%x09%an%x09%ae%x09%ad%x09%s", "--date=short"]
        commits = run(log_range, root).splitlines()
        summary["selected_author"] = author
        summary["author_commits"] = len([line for line in commits if line.strip()])
        summary["recent_author_commits"] = commits[:30]
        numstat = run(["git", "log", f"--author={author}", "--numstat", "--pretty=format:"], root)
    else:
        summary["selected_author"] = None
        summary["author_commits"] = None
        summary["recent_author_commits"] = []
        numstat = run(["git", "log", "--numstat", "--pretty=format:"], root)

    files = Counter()
    added = deleted = 0
    for line in numstat.splitlines():
        parts = line.split("\t")
        if len(parts) == 3 and parts[0].isdigit() and parts[1].isdigit():
            a, d, file_path = int(parts[0]), int(parts[1]), parts[2]
            added += a
            deleted += d
            files[file_path] += a + d
    summary["lines_added"] = added
    summary["lines_deleted"] = deleted
    summary["top_changed_files"] = files.most_common(30)
    return summary


def sanitize_remote(remote: str) -> str:
    if not remote:
        return ""
    if "@" in remote and ":" in remote:
        return remote.split("@", 1)[-1]
    if "://" in remote:
        scheme, rest = remote.split("://", 1)
        if "@" in rest:
            rest = rest.split("@", 1)[-1]
        return f"{scheme}://{rest}"
    return remote


def pattern_counts(rel_files: list[str]) -> dict:
    counts = {key: 0 for key in PATTERNS}
    examples = {key: [] for key in PATTERNS}
    for rel in rel_files:
        lowered = rel.lower()
        for key, needles in PATTERNS.items():
            if key == "tests":
                matched = is_test_path(rel)
            elif is_test_path(rel):
                matched = False
            else:
                matched = path_matches_needles(rel, needles)
            if matched:
                counts[key] += 1
                if len(examples[key]) < 12:
                    examples[key].append(rel)
    return {"counts": counts, "examples": examples}


def highlight_seeds(evidence: dict) -> list[dict]:
    seeds = []
    counts = evidence["patterns"]["counts"]
    examples = evidence["patterns"]["examples"]
    specialized = evidence.get("specialized_signals") or {}
    mapping = [
        ("工程化与质量", "检测到测试/CI/配置文件，可提炼工程质量、稳定性和协作效率亮点。", ["tests", "ci_devops"]),
        ("前端组件化", "检测到组件/页面结构，可提炼组件复用、页面交付和业务流实现亮点。", ["components", "frontend_pages"]),
        ("接口与服务层", "检测到 API/Service/Controller 结构，可提炼接口封装、业务服务拆分和联调能力。", ["api_routes", "services"]),
        ("权限与安全", "检测到登录、权限、token 或 guard 相关文件，可提炼鉴权和访问控制亮点。", ["auth_security"]),
        ("数据与智能化", "检测到数据分析、图表、模型、prompt 或向量相关文件，可提炼数据/AI/自动化亮点。", ["data_ai"]),
        ("AI Agent 与工具调用", "检测到 Agent、工具调用、Prompt、RAG 或 MCP 相关文件，可提炼智能应用落地亮点。", ["agent_ai"]),
        ("状态管理", "检测到 store/state 相关文件，可提炼复杂状态流转和前端架构亮点。", ["state"]),
    ]
    for category, reason, keys in mapping:
        score = sum(counts.get(key, 0) for key in keys)
        if score:
            seed_examples = []
            for key in keys:
                seed_examples.extend(examples.get(key, [])[:6])
            seeds.append({
                "category": category,
                "reason": reason,
                "evidence_count": score,
                "example_paths": list(dict.fromkeys(seed_examples))[:12],
            })
    if specialized.get("uniapp"):
        uni = specialized["uniapp"]
        paths = ["pages.json"] if uni.get("pages_json") else []
        paths.extend(examples.get("frontend_pages", [])[:6])
        seeds.append({
            "category": "移动端/小程序多端交付",
            "reason": "检测到 UniApp pages.json、manifest、多端条件编译或小程序 API，可提炼多端页面、登录授权、支付、地图、上传等移动端业务亮点。",
            "evidence_count": int(uni.get("page_count") or 0) + len(uni.get("uni_api_calls") or []),
            "example_paths": list(dict.fromkeys(paths))[:12],
        })
    if specialized.get("node_backend"):
        node = specialized["node_backend"]
        candidates = []
        for values in (node.get("layer_candidates") or {}).values():
            candidates.extend(values[:4])
        seeds.append({
            "category": "Node 后端服务设计",
            "reason": "检测到 Node API 依赖、路由/控制器/服务/中间件/模型等分层，可提炼接口设计、鉴权、数据层和任务队列亮点。",
            "evidence_count": len(candidates) + len(node.get("dependencies") or []),
            "example_paths": list(dict.fromkeys(candidates))[:12],
        })
    if specialized.get("python_backend"):
        python = specialized["python_backend"]
        candidates = []
        for values in (python.get("layer_candidates") or {}).values():
            candidates.extend(values[:4])
        seeds.append({
            "category": "Python API / 网关服务",
            "reason": "检测到 FastAPI/Flask/Django、代理转发、鉴权、配额或计量等 Python 后端服务结构，可提炼 API 网关、可靠性和服务治理亮点。",
            "evidence_count": len(candidates) + len(python.get("dependencies") or []),
            "example_paths": list(dict.fromkeys(candidates))[:12],
        })
    if specialized.get("ai_agent"):
        agent = specialized["ai_agent"]
        candidates = []
        for values in (agent.get("file_candidates") or {}).values():
            candidates.extend(values[:4])
        seeds.append({
            "category": "AI Agent 应用落地",
            "reason": "检测到模型调用、Prompt、工具调用、RAG、Memory、Workflow 或 MCP 信号，可提炼 AI 应用工程化落地亮点。",
            "evidence_count": len(candidates) + min(sum((agent.get("pattern_counts") or {}).values()), 50),
            "example_paths": list(dict.fromkeys(candidates))[:12],
        })
    return seeds


def collect(repo: Path, author: str | None) -> dict:
    files = list(iter_files(repo))
    rel_files = [str(path.relative_to(repo)) for path in files]
    signal_source_files = signal_files(repo, files)
    signal_rel_files = [
        str(path.relative_to(repo)).replace("\\", "/")
        for path in signal_source_files
    ]
    ext_counter = Counter(path.suffix.lower() or "[no_ext]" for path in files)
    lang_counter = Counter()
    total_lines = 0
    for path in files:
        ext = path.suffix.lower()
        lines = count_lines(path)
        total_lines += lines
        if ext in LANG_BY_EXT:
            lang_counter[LANG_BY_EXT[ext]] += lines or 1
    signal_lines = sum(count_lines(path) for path in signal_source_files)

    key_files = []
    for name in KEY_FILES:
        p = repo / name
        if p.exists():
            key_files.append(name)

    top_dirs = Counter(rel.split("/", 1)[0] for rel in rel_files if "/" in rel)
    manifests = manifest_summary(repo)
    workspace_projects = collect_workspace_projects(repo, files)
    if workspace_projects:
        manifests["workspace_projects"] = workspace_projects
    docs = collect_docs(repo, files)
    doc_bits = []
    for doc in docs[:12]:
        doc_bits.extend(doc.get("headings_or_summary_lines") or [])

    evidence = {
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "repo": str(repo),
        "project_name": repo.name,
        "files_total": len(files),
        "signal_files_total": len(signal_rel_files),
        "file_index": rel_files[:5000],
        "file_index_truncated": len(rel_files) > 5000,
        "evidence_paths_index": rel_files,
        "signal_policy": {
            "exclude_from_signals_prefixes": list(SIGNAL_EXCLUDE_PREFIXES),
            "exclude_from_signals_dir_parts": sorted(SIGNAL_EXCLUDE_DIR_PARTS),
            "exclude_from_signals_path_markers": list(SIGNAL_EXCLUDE_PATH_MARKERS),
            "exclude_from_signals_files": sorted(SIGNAL_EXCLUDE_FILES),
            "signal_files_total": len(signal_rel_files),
        },
        "lines_total_estimate": total_lines,
        "signal_lines_estimate": signal_lines,
        "extensions": ext_counter.most_common(30),
        "languages_by_lines": lang_counter.most_common(20),
        "top_directories": top_dirs.most_common(30),
        "key_files": key_files,
        "manifests": manifests,
        "docs": docs,
        "framework_profiles": detect_framework_profiles(repo, files, manifests),
        "specialized_signals": collect_specialized_signals(repo, files, manifests),
        "resume_pitch_inputs": {
            "description_candidates": doc_bits[:12],
            "tech_keywords": detect_tech_keywords(doc_bits + signal_rel_files, manifests, key_files),
            "metric_candidates": extract_metric_candidates(repo, docs),
            "sensitivity_signals": sensitivity_signals(rel_files),
            "truth_questions": [
                "你在这个项目中的真实角色/负责边界是什么？",
                "内部指标、客户名称、业务规模或公司细节是否可以写进简历？",
            ],
        },
        "patterns": pattern_counts(signal_rel_files),
        "code_graph": collect_code_graph(repo, files),
        "git": git_summary(repo, author),
    }
    evidence["highlight_seeds"] = highlight_seeds(evidence)
    return evidence


def write_markdown(evidence: dict, out: Path) -> None:
    lines = [
        f"# Project Evidence: {evidence['project_name']}",
        "",
        f"- Repo: `{evidence['repo']}`",
        f"- Generated: {evidence['generated_at']}",
        f"- Files: {evidence['files_total']}",
        f"- Evidence path index: {len(evidence.get('evidence_paths_index') or [])} paths",
        f"- File index truncated: {evidence.get('file_index_truncated')}",
        f"- Estimated text lines: {evidence['lines_total_estimate']}",
        f"- Signal text lines: {evidence.get('signal_lines_estimate', 0)}",
        "",
        "## Languages",
    ]
    for lang, count in evidence["languages_by_lines"][:12]:
        lines.append(f"- {lang}: {count}")
    lines.extend(["", "## Key Files"])
    for item in evidence["key_files"]:
        lines.append(f"- `{item}`")
    pitch = evidence.get("resume_pitch_inputs", {})
    lines.extend(["", "## Resume Pitch Inputs"])
    tech_keywords = pitch.get("tech_keywords") or []
    if tech_keywords:
        lines.append("- Tech keywords: " + ", ".join(tech_keywords[:30]))
    description_candidates = pitch.get("description_candidates") or []
    if description_candidates:
        lines.append("- Description candidates:")
        for item in description_candidates[:8]:
            lines.append(f"  - {item}")
    metric_candidates = pitch.get("metric_candidates") or []
    if metric_candidates:
        lines.append("- Metric candidates from docs:")
        for item in metric_candidates[:10]:
            lines.append(f"  - `{item['source']}`: {item['text']}")
    sensitivity = pitch.get("sensitivity_signals") or []
    if sensitivity:
        lines.append("- Potential disclosure-sensitive paths:")
        for item in sensitivity[:10]:
            lines.append(f"  - `{item}`")
    lines.append("- Truth questions:")
    for item in pitch.get("truth_questions", []):
        lines.append(f"  - {item}")
    profiles = evidence.get("framework_profiles") or []
    signal_policy = evidence.get("signal_policy") or {}
    if signal_policy:
        lines.extend(["", "## Signal Policy"])
        lines.append("- Excluded from framework/business signals: " + ", ".join(signal_policy.get("exclude_from_signals_prefixes", [])))
        extra_parts = signal_policy.get("exclude_from_signals_dir_parts") or []
        if extra_parts:
            lines.append("- Excluded signal directory parts: " + ", ".join(extra_parts))
        markers = signal_policy.get("exclude_from_signals_path_markers") or []
        if markers:
            lines.append("- Excluded signal path markers: " + ", ".join(markers))
        lines.append(f"- Signal files scanned: {signal_policy.get('signal_files_total', 0)}")
    workspace_projects = (evidence.get("manifests") or {}).get("workspace_projects") or []
    if workspace_projects:
        lines.extend(["", "## Workspace Projects"])
        for item in workspace_projects[:12]:
            lines.append(
                f"- `{item.get('path')}` ({', '.join(item.get('project_type') or [])}) "
                f"manifests={', '.join(item.get('manifest_files') or [])}"
            )
    if profiles:
        lines.extend(["", "## Framework Profiles"])
        for item in profiles[:10]:
            lines.append(f"- {item.get('name')} ({item.get('role')}, confidence={item.get('confidence')})")
            for signal in item.get("signals", [])[:6]:
                lines.append(f"  - {signal}")
    specialized = evidence.get("specialized_signals") or {}
    if specialized:
        lines.extend(["", "## Specialized Signals"])
        uni = specialized.get("uniapp") or {}
        if uni:
            lines.append("- UniApp / 小程序:")
            if uni.get("page_count") is not None:
                lines.append(f"  - pages: {uni.get('page_count')}, subpackages: {uni.get('subpackages', 0)}, tabbar: {uni.get('tabbar_items', 0)}")
            for name, count in uni.get("uni_api_calls", [])[:10]:
                lines.append(f"  - uni.{name}: {count}")
            for platform, count in uni.get("conditional_platforms", [])[:8]:
                lines.append(f"  - conditional {platform}: {count}")
            if uni.get("ui_libraries"):
                lines.append("  - UI libraries: " + ", ".join(uni.get("ui_libraries", [])[:8]))
        node = specialized.get("node_backend") or {}
        if node:
            lines.append("- Node Backend:")
            if node.get("dependencies"):
                lines.append("  - dependencies: " + ", ".join(node.get("dependencies", [])[:12]))
            for bucket, values in (node.get("layer_candidates") or {}).items():
                lines.append(f"  - {bucket}: " + ", ".join(f"`{value}`" for value in values[:6]))
        python = specialized.get("python_backend") or {}
        if python:
            lines.append("- Python Backend / API Gateway:")
            if python.get("dependencies"):
                lines.append("  - dependencies: " + ", ".join(python.get("dependencies", [])[:12]))
            for bucket, values in (python.get("layer_candidates") or {}).items():
                lines.append(f"  - {bucket}: " + ", ".join(f"`{value}`" for value in values[:6]))
        agent = specialized.get("ai_agent") or {}
        if agent:
            lines.append("- AI Agent / AI 应用:")
            if agent.get("dependencies"):
                lines.append("  - dependencies: " + ", ".join(agent.get("dependencies", [])[:12]))
            if agent.get("pattern_counts"):
                lines.append("  - patterns: " + ", ".join(f"{key}={value}" for key, value in agent.get("pattern_counts", {}).items()))
            for bucket, values in (agent.get("file_candidates") or {}).items():
                lines.append(f"  - {bucket}: " + ", ".join(f"`{value}`" for value in values[:6]))
    graph = evidence.get("code_graph", {})
    lines.extend(["", "## Code Graph"])
    lines.append(f"- Scanned code files: {graph.get('scanned_code_files', 0)}")
    entrypoints = graph.get("entrypoints") or []
    if entrypoints:
        lines.append("- Entrypoints:")
        for item in entrypoints[:10]:
            lines.append(f"  - `{item}`")
    routes = graph.get("routes") or []
    if routes:
        lines.append("- Route candidates:")
        for item in routes[:12]:
            lines.append(f"  - `{item.get('source')}` {item.get('method')} {item.get('path')}")
    api_calls = graph.get("api_calls") or []
    if api_calls:
        lines.append("- API call candidates:")
        for item in api_calls[:12]:
            lines.append(f"  - `{item.get('source')}` -> {item.get('target')}")
    import_edges = graph.get("local_import_edges") or []
    if import_edges:
        lines.append("- Local import edges:")
        for item in import_edges[:12]:
            lines.append(f"  - `{item.get('source')}` -> `{item.get('target')}`")
    ast_summaries = graph.get("ast_summaries") or []
    if ast_summaries:
        lines.append("- AST summaries:")
        for item in ast_summaries[:8]:
            funcs = ", ".join(item.get("functions", [])[:5])
            classes = ", ".join(item.get("classes", [])[:5])
            lines.append(f"  - `{item.get('source')}` classes=[{classes}] functions=[{funcs}]")
    flow_candidates = graph.get("business_flow_candidates") or []
    if flow_candidates:
        lines.append("- Business flow candidates:")
        for item in flow_candidates[:8]:
            groups = ", ".join(f"{role}:{len(paths)}" for role, paths in (item.get("groups") or {}).items())
            lines.append(f"  - {item.get('domain')} ({groups})")
    lines.extend(["", "## Top Directories"])
    for item, count in evidence["top_directories"][:15]:
        lines.append(f"- `{item}/`: {count} files")
    lines.extend(["", "## Git"])
    git = evidence["git"]
    lines.append(f"- Is Git repo: {git.get('is_git')}")
    if git.get("is_git"):
        lines.append(f"- Branch: {git.get('branch')}")
        lines.append(f"- Total commits: {git.get('total_commits')}")
        if git.get("selected_author"):
            lines.append(f"- Selected author: {git.get('selected_author')}")
            lines.append(f"- Author commits: {git.get('author_commits')}")
        lines.append("- Top authors:")
        for author in git.get("authors", [])[:10]:
            lines.append(f"  - {author}")
    lines.extend(["", "## Highlight Seeds"])
    for seed in evidence["highlight_seeds"]:
        lines.append(f"### {seed['category']}")
        lines.append(f"- Reason: {seed['reason']}")
        lines.append(f"- Evidence count: {seed['evidence_count']}")
        for p in seed["example_paths"][:8]:
            lines.append(f"  - `{p}`")
    out.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo", required=True, help="Local repository/project path")
    parser.add_argument("--output", required=True, help="Output directory")
    parser.add_argument("--author", default=None, help="Optional git author name/email filter")
    args = parser.parse_args()

    repo = Path(args.repo).expanduser().resolve()
    if not repo.exists() or not repo.is_dir():
        raise SystemExit(f"Repo path does not exist or is not a directory: {repo}")
    out = Path(args.output).expanduser().resolve()
    out.mkdir(parents=True, exist_ok=True)

    evidence = collect(repo, args.author)
    (out / "project_evidence.json").write_text(json.dumps(evidence, ensure_ascii=False, indent=2), encoding="utf-8")
    write_markdown(evidence, out / "project_evidence.md")
    print(f"Wrote {out / 'project_evidence.json'}")
    print(f"Wrote {out / 'project_evidence.md'}")


if __name__ == "__main__":
    main()
