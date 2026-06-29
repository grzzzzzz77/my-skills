#!/usr/bin/env python3
"""Render a project-to-resume HTML report and prompt pack.

This script is intentionally dependency-free. The agent still performs deep
project understanding, but the final report assembly is deterministic.
"""

from __future__ import annotations

import argparse
import html
import json
import re
import shutil
import subprocess
import sys
from datetime import datetime
from pathlib import Path
from typing import Any

SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

from validate_analysis import format_findings, load_evidence_context, validate_analysis_payload


RISK_LABELS = {
    "safe": "可直接写",
    "needs_confirmation": "需确认数据",
    "risky": "不要直接写",
}

READINESS_LABELS = {
    "direct": "直接可用",
    "rewrite": "适合改写",
    "confirm": "确认后使用",
    "idea": "仅作思路",
}


def h(value: Any) -> str:
    return html.escape("" if value is None else str(value), quote=True)


def load_json(path: Path) -> dict:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except Exception as exc:
        raise SystemExit(f"Cannot read JSON {path}: {exc}") from exc
    if not isinstance(data, dict):
        raise SystemExit(f"JSON root must be an object: {path}")
    return data


def as_list(value: Any) -> list:
    if value is None:
        return []
    if isinstance(value, list):
        return value
    return [value]


def first_text(values: list[Any], fallback: str) -> str:
    for value in values:
        if isinstance(value, str) and value.strip():
            return value.strip()
    return fallback


def normalize_highlight(item: dict, index: int) -> dict:
    risk = item.get("risk") or item.get("risk_label") or "needs_confirmation"
    if risk not in RISK_LABELS:
        risk = "needs_confirmation"
    readiness = item.get("readiness") or "confirm"
    if readiness not in READINESS_LABELS:
        readiness = "confirm"
    return {
        "title": item.get("title") or f"候选亮点 {index + 1}",
        "category": item.get("category") or "未分类",
        "score": item.get("score") or item.get("readiness_score") or "",
        "risk": risk,
        "readiness": readiness,
        "evidence": as_list(item.get("evidence") or item.get("evidence_paths")),
        "safe_bullet": item.get("safe_bullet") or item.get("bullet") or "",
        "enhanced_bullet": item.get("enhanced_bullet") or "",
        "why": item.get("why") or item.get("value") or "",
        "interview": item.get("interview") or item.get("star") or {},
        "data_to_confirm": as_list(item.get("data_to_confirm")),
        "usage": item.get("usage") or item.get("downstream_usage") or "",
        "score_breakdown": item.get("score_breakdown") if isinstance(item.get("score_breakdown"), dict) else {},
        "score_rationale": item.get("score_rationale") or "",
        "_source_index": index,
    }


def score_value(item: dict) -> int:
    raw = item.get("score")
    if isinstance(raw, (int, float)):
        return int(raw)
    match = re.search(r"\d+", str(raw or ""))
    return int(match.group(0)) if match else 0


def project_is_ai_application(evidence: dict, analysis: dict) -> bool:
    specialized = evidence.get("specialized_signals") or {}
    if specialized.get("ai_agent"):
        return True
    profiles = evidence.get("framework_profiles") or []
    if any("ai" in str(item.get("name", "")).lower() or "agent" in str(item.get("name", "")).lower() for item in profiles):
        return True
    text = " ".join(
        [
            str(analysis.get("project_name", "")),
            str(analysis.get("summary", "")),
            " ".join(str(x) for x in as_list(analysis.get("keywords"))),
        ]
    ).lower()
    return any(term in text for term in ["ai", "agent", "llm", "mcp", "rag", "memory", "模型", "智能体", "记忆"])


AI_TIER_A_TERMS = [
    "agent", "智能体", "记忆", "memory", "上下文", "context", "prompt", "提示词",
    "tool", "工具调用", "mcp", "rag", "检索", "模型路由", "provider", "guardrail", "评测",
]
AI_TIER_B_TERMS = [
    "stream", "流式", "长会话", "消息协议", "markdown", "渲染", "conversation", "会话",
    "websocket", "sse", "stdin", "stdout", "stream-json",
]
AI_TIER_C_TERMS = [
    "结果页", "表单", "上传", "支付", "埋点", "可观测", "业务", "workflow", "流程",
]


def ai_priority(item: dict, enabled: bool) -> int:
    if not enabled:
        return 0
    text = " ".join(
        str(item.get(key, ""))
        for key in ("title", "category", "safe_bullet", "enhanced_bullet", "why")
    ).lower()
    if any(term.lower() in text for term in AI_TIER_A_TERMS):
        return 3
    if any(term.lower() in text for term in AI_TIER_B_TERMS):
        return 2
    if any(term.lower() in text for term in AI_TIER_C_TERMS):
        return 1
    return 0


def sort_highlights(highlights: list[dict], evidence: dict, analysis: dict) -> list[dict]:
    is_ai = project_is_ai_application(evidence, analysis)
    risk_order = {"safe": 0, "needs_confirmation": 1, "risky": 2}
    readiness_order = {"direct": 0, "rewrite": 1, "confirm": 2, "idea": 3}
    return sorted(
        highlights,
        key=lambda item: (
            risk_order.get(item.get("risk"), 1),
            -score_value(item),
            -ai_priority(item, is_ai),
            readiness_order.get(item.get("readiness"), 2),
            item.get("_source_index", 0),
        ),
    )


def draft_highlights_from_evidence(evidence: dict) -> list[dict]:
    highlights = []
    for seed in evidence.get("highlight_seeds", []):
        paths = seed.get("example_paths") or []
        category = seed.get("category") or "候选亮点"
        highlights.append(normalize_highlight({
            "title": category,
            "category": category,
            "risk": "needs_confirmation",
            "readiness": "confirm",
            "score": seed.get("evidence_count"),
            "evidence": paths,
            "safe_bullet": f"围绕「{category}」存在可提炼线索，需要继续读取相关模块后再写成最终简历 bullet。",
            "enhanced_bullet": "确认个人负责边界、生产使用情况和真实业务指标后，可进一步写成结果导向表达。",
            "why": seed.get("reason", ""),
            "data_to_confirm": ["个人负责边界", "是否上线/生产使用", "是否有可公开业务或效率指标"],
            "usage": "confirmation_needed",
        }, len(highlights)))
    return highlights


def build_metric_cards(evidence: dict, analysis: dict) -> str:
    git = evidence.get("git") or {}
    languages = evidence.get("languages_by_lines") or []
    cards = [
        ("文件数", evidence.get("files_total", 0), "纳入扫描的项目文件"),
        ("估算代码/文本行", evidence.get("lines_total_estimate", 0), "用于判断项目规模"),
        ("主要语言", len(languages), "按行数统计的语言/文件类型"),
        ("Git 提交", git.get("total_commits", 0) if git.get("is_git") else "无 Git", "仓库历史信号"),
    ]
    for item in as_list(analysis.get("metric_cards")):
        if isinstance(item, dict):
            cards.append((item.get("label", ""), item.get("value", ""), item.get("note", "")))
    return "\n".join(
        f'<article class="stat-card"><strong>{h(value)}</strong><span>{h(label)} · {h(note)}</span></article>'
        for label, value, note in cards[:8]
    )


def render_value(value: Any) -> str:
    if isinstance(value, list):
        return "<ul>" + "".join(f"<li>{h(item)}</li>" for item in value if str(item).strip()) + "</ul>"
    return h(value)


def build_project_facts(evidence: dict, analysis: dict) -> str:
    pitch = evidence.get("resume_pitch_inputs") or {}
    git = evidence.get("git") or {}
    facts = analysis.get("facts")
    if isinstance(facts, dict):
        fact_items = [{"label": key, "value": value} for key, value in facts.items()]
    elif isinstance(facts, list):
        fact_items = facts
    else:
        fact_items = []
    defaults = [
        {"label": "项目名称", "value": analysis.get("project_name") or evidence.get("project_name")},
        {"label": "一句话概述", "value": analysis.get("summary") or first_text(pitch.get("description_candidates", []), "待根据 README/docs 和核心代码补充。")},
        {"label": "目标岗位", "value": analysis.get("target_role") or "未指定"},
        {"label": "角色边界", "value": analysis.get("role_assumption") or "未确认，默认使用保守表述。"},
        {"label": "公开边界", "value": analysis.get("disclosure_assumption") or "未确认，不暴露内部指标、客户名和敏感细节。"},
        {"label": "技术关键词", "value": analysis.get("keywords") or pitch.get("tech_keywords") or []},
    ]
    if git.get("is_git"):
        defaults.append({"label": "Git 信号", "value": [
            f"总提交数：{git.get('total_commits')}",
            f"当前分支：{git.get('branch') or '未知'}",
            f"选择作者：{git.get('selected_author') or '未指定'}",
        ]})
    fact_items = defaults + [item for item in fact_items if isinstance(item, dict)]
    return "\n".join(
        f'<div class="fact"><strong>{h(item.get("label", ""))}</strong><div>{render_value(item.get("value", ""))}</div></div>'
        for item in fact_items
    )


def build_filter_buttons(highlights: list[dict], field: str, labels: dict | None = None) -> str:
    values = []
    for item in highlights:
        value = item.get(field)
        if value and value not in values:
            values.append(value)
    rows = []
    for value in values:
        label = labels.get(value, value) if labels else value
        rows.append(
            f'<button class="filter-chip" data-filter-kind="{h(field)}" '
            f'data-filter-value="{h(value)}" type="button">{h(label)}</button>'
        )
    return "\n".join(rows)


def build_safe_bullets(highlights: list[dict], analysis: dict) -> tuple[str, int]:
    bullets = [str(item).strip() for item in as_list(analysis.get("safe_bullets")) if str(item).strip()]
    if not bullets:
        bullets = [
            item["safe_bullet"].strip()
            for item in highlights
            if item["risk"] == "safe" and item.get("safe_bullet", "").strip()
        ]
    if not bullets:
        bullets = ["暂无可直接粘贴的安全 bullet。请先补充结构化分析或确认个人负责边界。"]
    text = "\n".join(f"- {bullet}" for bullet in bullets)
    return h(text), len(bullets)


def build_confirmation_items(highlights: list[dict], analysis: dict) -> str:
    rows = []
    for item in as_list(analysis.get("confirmation_items")):
        if isinstance(item, str):
            rows.append(f'<div class="enhanced-item">{h(item)}</div>')
        elif isinstance(item, dict):
            rows.append(
                f'<div class="enhanced-item"><strong>{h(item.get("title", "待确认"))}</strong><br>'
                f'{h(item.get("text", ""))}</div>'
            )
    for item in highlights:
        if item["risk"] == "needs_confirmation" and item.get("enhanced_bullet"):
            confirm = "；".join(str(x) for x in item.get("data_to_confirm", []) if str(x).strip())
            rows.append(
                f'<div class="enhanced-item"><strong>{h(item["title"])}</strong><br>{h(item["enhanced_bullet"])}'
                f'<br><span class="needs_confirmation">需确认：{h(confirm or "真实数据/负责边界")}</span></div>'
            )
    return "\n".join(rows) or '<div class="enhanced-item">暂无增强版 bullet。</div>'


def render_interview_notes(notes: Any) -> str:
    if isinstance(notes, dict):
        labels = [
            ("situation", "背景"),
            ("task", "任务"),
            ("action", "行动"),
            ("result", "结果"),
            ("tradeoff", "取舍"),
        ]
        items = [f"<li><strong>{label}：</strong>{h(notes.get(key, ''))}</li>" for key, label in labels if notes.get(key)]
        return "<ul>" + "".join(items) + "</ul>" if items else ""
    if isinstance(notes, list):
        return "<ul>" + "".join(f"<li>{h(item)}</li>" for item in notes) + "</ul>"
    return h(notes)


def build_highlight_cards(highlights: list[dict]) -> str:
    rows = []
    for item in highlights:
        evidence = as_list(item.get("evidence"))
        data_to_confirm = as_list(item.get("data_to_confirm"))
        evidence_html = "<ul>" + "".join(f"<li><code>{h(path)}</code></li>" for path in evidence[:8]) + "</ul>" if evidence else "<div class=\"interview-notes\">未提供</div>"
        confirm_html = "；".join(str(x) for x in data_to_confirm if str(x).strip()) or "无"
        score_breakdown = item.get("score_breakdown") or {}
        score_parts = []
        if isinstance(score_breakdown, dict):
            score_labels = {
                "business_relevance": "业务相关",
                "technical_difficulty": "技术难度",
                "evidence_strength": "证据强度",
                "resume_readability": "简历可读",
                "differentiation": "差异化",
                "handoff_readiness": "交付可用",
                "ai_application_bonus": "AI 加权",
            }
            for key, label in score_labels.items():
                if key in score_breakdown:
                    score_parts.append(f"{label}:{score_breakdown[key]}")
        score_detail_html = ""
        if item.get("score_rationale") or score_parts:
            score_detail_html = (
                f'<div class="aside-box"><strong>评分依据</strong>'
                f'{h(item.get("score_rationale") or "；".join(score_parts))}'
                f'</div>'
            )
        rows.append(f"""
          <article class="highlight-card" data-category="{h(item['category'])}" data-risk="{h(item['risk'])}" data-readiness="{h(item['readiness'])}">
            <div class="card-main">
              <div>
                <div class="card-title-row">
                  <h3>{h(item['title'])}</h3>
                </div>
                <div class="card-tags">
                  <span class="tag">{h(item['category'])}</span>
                  <span class="tag {h(item['risk'])}">{h(RISK_LABELS[item['risk']])}</span>
                  <span class="tag">{h(READINESS_LABELS[item['readiness']])}</span>
                  <span class="tag">评分：{h(item.get('score') or '未评')}</span>
                </div>
                <p class="card-value">{h(item.get('why') or '待补充')}</p>
                <div class="bullet-compare">
                  <div class="bullet-block"><strong>安全版</strong>{h(item.get('safe_bullet') or '待补充')}</div>
                  <div class="bullet-block"><strong>增强版</strong>{h(item.get('enhanced_bullet') or '待确认数据后再写')}</div>
                </div>
              </div>
              <aside class="card-aside">
                <div class="aside-box"><strong>亮点评分</strong>{h(item.get('score') or '未评')}</div>
                <div class="aside-box"><strong>待确认</strong>{h(confirm_html)}</div>
                <div class="aside-box"><strong>下游用途</strong>{h(item.get('usage') or '按风险标签决定')}</div>
                {score_detail_html}
              </aside>
            </div>
            <div class="card-details">
              <details>
                <summary>证据路径</summary>
                {evidence_html}
              </details>
              <details>
                <summary>面试 STAR / 取舍</summary>
                <div class="interview-notes">{render_interview_notes(item.get('interview')) or '待补充'}</div>
              </details>
            </div>
          </article>
        """)
    return "\n".join(rows) or '<div class="empty-state" style="display:block">暂无亮点卡片。请补充 project_resume_analysis.json。</div>'


def build_interview_stories(highlights: list[dict], analysis: dict) -> str:
    stories = as_list(analysis.get("interview_stories"))
    rows = []
    for story in stories:
        if isinstance(story, dict):
            rows.append(f'<article class="story-card"><strong>{h(story.get("title", "面试故事"))}</strong>{render_interview_notes(story.get("notes") or story)}</article>')
        elif str(story).strip():
            rows.append(f'<article class="story-card">{h(story)}</article>')
    if not rows:
        for item in highlights[:5]:
            notes = render_interview_notes(item.get("interview"))
            if notes:
                rows.append(f'<article class="story-card"><strong>{h(item["title"])}</strong>{notes}</article>')
    return "\n".join(rows) or '<article class="story-card">暂无 STAR 面试故事。</article>'


def build_evidence_appendix(evidence: dict) -> str:
    rows = []
    graph = evidence.get("code_graph") or {}
    profiles = evidence.get("framework_profiles") or []
    specialized = evidence.get("specialized_signals") or {}
    uni = specialized.get("uniapp") or {}
    node = specialized.get("node_backend") or {}
    agent = specialized.get("ai_agent") or {}
    specialized_rows = []
    if uni:
        specialized_rows.append(
            "UniApp: pages={pages}, subpackages={subpackages}, APIs={apis}".format(
                pages=uni.get("page_count", 0),
                subpackages=uni.get("subpackages", 0),
                apis=", ".join(f"uni.{name}:{count}" for name, count in (uni.get("uni_api_calls") or [])[:8]) or "无",
            )
        )
    if node:
        specialized_rows.append("Node 后端依赖: " + ", ".join((node.get("dependencies") or [])[:12]))
    if agent:
        patterns = agent.get("pattern_counts") or {}
        specialized_rows.append("AI Agent 信号: " + ", ".join(f"{key}={value}" for key, value in patterns.items()))
    for name, value in [
        ("关键文件", evidence.get("key_files")),
        ("主要目录", [f"{name}/: {count} files" for name, count in evidence.get("top_directories", [])[:12]]),
        ("文档来源", [doc.get("path") for doc in evidence.get("docs", [])[:12]]),
        ("框架识别", [f"{item.get('name')} ({item.get('role')}, confidence={item.get('confidence')})" for item in profiles[:12]]),
        ("专项识别", specialized_rows),
        ("入口文件", graph.get("entrypoints")),
        ("路由候选", [f"{item.get('method')} {item.get('path')} ({item.get('source')})" for item in graph.get("routes", [])[:12]]),
        ("API 调用候选", [f"{item.get('source')} -> {item.get('target')}" for item in graph.get("api_calls", [])[:12]]),
        ("AST 摘要", [f"{item.get('source')} classes={','.join(item.get('classes', [])[:4])} functions={','.join(item.get('functions', [])[:6])}" for item in graph.get("ast_summaries", [])[:12]]),
        ("业务流候选", [f"{item.get('domain')}: {item.get('score')}" for item in graph.get("business_flow_candidates", [])[:12]]),
        ("高风险披露路径", (evidence.get("resume_pitch_inputs") or {}).get("sensitivity_signals")),
    ]:
        values = [str(item) for item in as_list(value) if str(item).strip()]
        rows.append(f"<tr><th>{h(name)}</th><td>{'<br>'.join(h(item) for item in values) if values else '无'}</td></tr>")
    rows.append("<tr><th>安全说明</th><td>报告未复制仓库中的密钥、凭证或敏感源码全文；敏感路径只作为风险提醒。</td></tr>")
    return "<table>" + "".join(rows) + "</table>"


def build_prompt_pack(evidence: dict, analysis: dict, highlights: list[dict]) -> str:
    if isinstance(analysis.get("prompt_pack"), str) and analysis["prompt_pack"].strip():
        return analysis["prompt_pack"].strip()
    project_name = analysis.get("project_name") or evidence.get("project_name") or "未命名项目"
    pitch = evidence.get("resume_pitch_inputs") or {}
    safe_bullets = [
        item["safe_bullet"].strip()
        for item in highlights
        if item["risk"] == "safe" and item.get("safe_bullet", "").strip()
    ]
    enhanced = [
        item["enhanced_bullet"].strip()
        for item in highlights
        if item.get("enhanced_bullet", "").strip()
    ]
    risky = [
        item["safe_bullet"].strip()
        for item in highlights
        if item["risk"] == "risky" and item.get("safe_bullet", "").strip()
    ]
    keywords = analysis.get("keywords") or pitch.get("tech_keywords") or []
    facts = [
        f"【项目名称】{project_name}",
        f"【一句话概述】{analysis.get('summary') or first_text(pitch.get('description_candidates', []), '待补充')}",
        f"【目标岗位】{analysis.get('target_role') or '待补充'}",
        f"【我的角色/边界】{analysis.get('role_assumption') or '未确认，请使用保守表述'}",
        f"【是否可公开的边界】{analysis.get('disclosure_assumption') or '未确认，不要写内部指标、客户名或敏感细节'}",
        "【技术栈与关键词】" + ("、".join(str(x) for x in keywords) if keywords else "待补充"),
    ]
    def bullet_section(title: str, values: list[str], fallback: str) -> str:
        body = "\n".join(f"- {value}" for value in values if value) or f"- {fallback}"
        return f"{title}\n{body}"
    return "\n\n".join([
        "我想把一个项目写进简历。请你结合我下面附上的原始简历，把这个项目用合适的措辞和详略融入进去，并输出一版完整的新简历。",
        "写作要求：\n1. 风格、语言、人称、bullet 详略与我的原始简历保持一致。\n2. 用“动作 + 技术/方法 + 业务对象 + 规模/指标 + 结果”组织，不要写成功能清单。\n3. 只能使用下方提供的事实和数字，不要编造用户量、收益、性能提升、团队规模等信息。\n4. 对“需要确认”的指标或角色表述，不要直接写成事实。",
        "\n".join(facts),
        bullet_section("【可直接写入简历的 bullet】", safe_bullets, "暂无，请先补充可证实的项目贡献。"),
        bullet_section("【增强版 bullet，需要我确认数据后再用】", enhanced, "暂无。"),
        bullet_section("【不要直接写的高风险表述】", risky, "暂无。"),
        bullet_section("【待我确认的问题】", pitch.get("truth_questions") or [], "个人负责边界、是否可公开内部指标。"),
        "请基于以上项目信息与我的原始简历，输出新版完整简历。",
    ])


def render_report(evidence: dict, analysis: dict, template: str) -> tuple[str, str]:
    highlights = [normalize_highlight(item, i) for i, item in enumerate(as_list(analysis.get("highlights")) if analysis.get("highlights") else []) if isinstance(item, dict)]
    if not highlights:
        highlights = draft_highlights_from_evidence(evidence)
    highlights = sort_highlights(highlights, evidence, analysis)
    prompt_pack = build_prompt_pack(evidence, analysis, highlights)
    safe_bullets_html, safe_count = build_safe_bullets(highlights, analysis)
    replacements = {
        "PROJECT_NAME": h(analysis.get("project_name") or evidence.get("project_name") or "未命名项目"),
        "SUMMARY": h(analysis.get("summary") or first_text((evidence.get("resume_pitch_inputs") or {}).get("description_candidates", []), "已完成项目证据扫描，请补充结构化分析后生成最终简历亮点。")),
        "TARGET_ROLE": h(analysis.get("target_role") or "未指定"),
        "GENERATED_AT": h(analysis.get("generated_at") or datetime.now().strftime("%Y-%m-%d %H:%M")),
        "REPO_PATH": h(evidence.get("repo", "")),
        "READINESS": h(analysis.get("readiness") or "需结合结构化分析确认"),
        "METRIC_CARDS": build_metric_cards(evidence, analysis),
        "CATEGORY_FILTERS": build_filter_buttons(highlights, "category"),
        "READINESS_FILTERS": build_filter_buttons(highlights, "readiness", READINESS_LABELS),
        "PROJECT_FACTS": build_project_facts(evidence, analysis),
        "SAFE_COUNT": h(safe_count),
        "SAFE_BULLETS": safe_bullets_html,
        "CONFIRMATION_ITEMS": build_confirmation_items(highlights, analysis),
        "HIGHLIGHT_CARDS": build_highlight_cards(highlights),
        "PITCH_PROMPT": h(prompt_pack),
        "INTERVIEW_STORIES": build_interview_stories(highlights, analysis),
        "EVIDENCE_APPENDIX": build_evidence_appendix(evidence),
    }
    output = template
    for key, value in replacements.items():
        output = output.replace("{{" + key + "}}", str(value))
    unresolved = sorted(set(re.findall(r"\{\{[A-Z0-9_]+\}\}", output)))
    if unresolved:
        raise SystemExit("Unresolved placeholders in report: " + ", ".join(unresolved))
    return output, prompt_pack


def copy_to_clipboard(text: str) -> bool:
    tool = shutil.which("pbcopy")
    if not tool:
        return False
    subprocess.run([tool], input=text, text=True, check=False)
    return True


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--evidence", required=True, help="project_evidence.json from collect_project_evidence.py")
    parser.add_argument("--analysis", help="project_resume_analysis.json written by the agent")
    parser.add_argument("--template", help="HTML template path; defaults to assets/report-template.html")
    parser.add_argument("--output", required=True, help="Output HTML report path")
    parser.add_argument("--prompt-output", help="Output downstream prompt pack text path")
    parser.add_argument("--copy-prompt", action="store_true", help="Copy prompt pack to macOS clipboard when pbcopy is available")
    parser.add_argument("--strict", action="store_true", help="Validate analysis JSON and fail on warnings/errors before rendering")
    args = parser.parse_args()

    evidence_path = Path(args.evidence).expanduser().resolve()
    evidence = load_json(evidence_path)
    analysis = load_json(Path(args.analysis).expanduser().resolve()) if args.analysis else {}
    if args.strict:
        if not args.analysis:
            raise SystemExit("--strict requires --analysis")
        findings = validate_analysis_payload(analysis, load_evidence_context(evidence_path))
        errors = [item for item in findings if item["level"] == "error"]
        warnings = [item for item in findings if item["level"] == "warning"]
        if findings:
            print(format_findings(findings))
        if errors or warnings:
            raise SystemExit(1)

    skill_dir = Path(__file__).resolve().parents[1]
    template_path = Path(args.template).expanduser().resolve() if args.template else skill_dir / "assets" / "report-template.html"
    template = template_path.read_text(encoding="utf-8")
    html_text, prompt_pack = render_report(evidence, analysis, template)

    output = Path(args.output).expanduser().resolve()
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(html_text, encoding="utf-8")

    prompt_output = Path(args.prompt_output).expanduser().resolve() if args.prompt_output else output.with_name(output.stem + "-resume-project-pitch.txt")
    prompt_output.write_text(prompt_pack + "\n", encoding="utf-8")

    copied = copy_to_clipboard(prompt_pack) if args.copy_prompt else False
    print(f"Wrote {output}")
    print(f"Wrote {prompt_output}")
    if args.copy_prompt:
        print("Copied prompt pack to clipboard" if copied else "Clipboard tool not available; prompt pack saved only")


if __name__ == "__main__":
    main()
