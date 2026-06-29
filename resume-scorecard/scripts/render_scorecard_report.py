#!/usr/bin/env python3
"""Render a resume-scorecard HTML report from structured JSON."""

from __future__ import annotations

import argparse
import html
import json
import re
import sys
from datetime import datetime
from pathlib import Path
from typing import Any

SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

from validate_scorecard import format_findings, validate_analysis_payload


def h(value: Any) -> str:
    return html.escape("" if value is None else str(value), quote=True)


def as_list(value: Any) -> list:
    if value is None:
        return []
    if isinstance(value, list):
        return value
    return [value]


def load_json(path: Path) -> dict:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except Exception as exc:
        raise SystemExit(f"Cannot read JSON {path}: {exc}") from exc
    if not isinstance(data, dict):
        raise SystemExit("analysis JSON root must be an object")
    return data


def score_number(value: Any, fallback: float = 0.0) -> float:
    if isinstance(value, bool):
        return fallback
    if isinstance(value, (int, float)):
        return float(value)
    match = re.search(r"-?\d+(?:\.\d+)?", str(value or ""))
    return float(match.group(0)) if match else fallback


def infer_band(score: float) -> str:
    if score >= 90:
        return "A+"
    if score >= 80:
        return "A"
    if score >= 70:
        return "B"
    if score >= 60:
        return "C"
    return "D"


def band_class(score: float) -> str:
    if score >= 80:
        return ""
    if score >= 60:
        return " mid"
    return " low"


def ul(items: Any, empty: str = "暂无") -> str:
    values = [str(item).strip() for item in as_list(items) if str(item).strip()]
    if not values:
        return f'<div class="empty">{h(empty)}</div>'
    return "<ul>" + "".join(f"<li>{h(item)}</li>" for item in values) + "</ul>"


def render_meta(analysis: dict) -> str:
    generated = analysis.get("generated_at") or datetime.now().strftime("%Y-%m-%d %H:%M")
    chips = [
        ("目标岗位", analysis.get("target_role") or "未指定"),
        ("评分模式", analysis.get("score_mode") or "single"),
        ("置信度", analysis.get("confidence") or "medium"),
        ("生成时间", generated),
    ]
    if analysis.get("candidate_label"):
        chips.insert(0, ("对象", analysis.get("candidate_label")))
    if analysis.get("jd_summary"):
        chips.append(("JD", analysis.get("jd_summary")))
    return "\n".join(f'<span class="chip"><strong>{h(label)}:</strong> {h(value)}</span>' for label, value in chips)


def render_score_cards(resumes: list[dict]) -> str:
    rows = []
    for item in resumes:
        total = score_number(item.get("total_score"))
        band = item.get("band") or infer_band(total)
        jd_fit = item.get("jd_fit") if isinstance(item.get("jd_fit"), dict) else {}
        context_bits = []
        if item.get("target_role"):
            context_bits.append(f"目标：{item.get('target_role')}")
        if item.get("target_industry"):
            context_bits.append(f"行业：{item.get('target_industry')}")
        if item.get("scoring_context"):
            context_bits.append(str(item.get("scoring_context")))
        context_html = ""
        if context_bits:
            context_html = '<p class="muted">' + h(" · ".join(context_bits)) + "</p>"
        jd_score = jd_fit.get("score")
        jd_html = ""
        if jd_score not in (None, ""):
            jd_html = f'<p class="muted">JD 匹配分：<strong>{h(jd_score)}</strong> · 覆盖度：{h(jd_fit.get("must_have_coverage") or "未标注")}</p>'
        rows.append(f"""
        <article class="card score-card">
          <div class="top">
            <div>
              <h3>{h(item.get("name") or item.get("id") or "简历")}</h3>
              <p class="muted">{h(item.get("source") or "")}</p>
            </div>
            <span class="band{band_class(total)}">{h(band)}</span>
          </div>
          <div class="score">{h(int(total) if total.is_integer() else round(total, 1))}</div>
          <div class="bar"><span style="width:{max(0, min(100, total)):.1f}%"></span></div>
          {context_html}
          <p>{h(item.get("score_summary") or "暂无评分摘要。")}</p>
          {jd_html}
        </article>
        """)
    return "\n".join(rows)


def comparison_from_scores(resumes: list[dict]) -> dict:
    if len(resumes) < 2:
        return {}
    ranked = sorted(resumes, key=lambda item: score_number(item.get("total_score")), reverse=True)
    top = ranked[0]
    second = ranked[1]
    delta = score_number(top.get("total_score")) - score_number(second.get("total_score"))
    return {
        "winner": top.get("id") or top.get("name"),
        "reason": f"{top.get('name') or top.get('id')} 总分领先 {delta:g} 分。",
        "delta_summary": [f"{top.get('name') or top.get('id')}：{top.get('total_score')}；{second.get('name') or second.get('id')}：{second.get('total_score')}。"],
        "best_for": [],
    }


def render_comparison(analysis: dict, resumes: list[dict]) -> str:
    comp = analysis.get("comparison") if isinstance(analysis.get("comparison"), dict) else {}
    if not comp:
        comp = comparison_from_scores(resumes)
    if not comp:
        return ""
    best_for_rows = []
    for item in as_list(comp.get("best_for")):
        if isinstance(item, dict):
            best_for_rows.append(
                f"<tr><td>{h(item.get('scenario'))}</td><td>{h(item.get('resume_id'))}</td><td>{h(item.get('reason'))}</td></tr>"
            )
        elif str(item).strip():
            best_for_rows.append(f"<tr><td colspan=\"3\">{h(item)}</td></tr>")
    table = ""
    if best_for_rows:
        table = (
            "<table><thead><tr><th>场景</th><th>推荐版本</th><th>原因</th></tr></thead><tbody>"
            + "".join(best_for_rows)
            + "</tbody></table>"
        )
    return f"""
    <section class="section">
      <h2>版本对比</h2>
      <div class="card">
        <p class="muted">对比类型：{h(comp.get("context_type") or "未标注")}</p>
        <p><strong>推荐版本：</strong>{h(comp.get("winner") or "未判定")}</p>
        <p>{h(comp.get("reason") or "")}</p>
        {ul(comp.get("delta_summary"), "暂无分差说明")}
        {table}
      </div>
    </section>
    """


def render_dimension_sections(resumes: list[dict]) -> str:
    blocks = []
    for resume in resumes:
        dims = []
        for dim in as_list(resume.get("dimensions")):
            if not isinstance(dim, dict):
                continue
            score = score_number(dim.get("score"))
            max_score = max(1.0, score_number(dim.get("max_score"), 1.0))
            percent = max(0.0, min(100.0, score / max_score * 100.0))
            dims.append(f"""
            <div class="dimension">
              <div class="dim-head">
                <strong>{h(dim.get("name"))}</strong>
                <span class="dim-score">{h(dim.get("score"))}/{h(dim.get("max_score"))}</span>
              </div>
              <div class="bar"><span style="width:{percent:.1f}%"></span></div>
              <p>{h(dim.get("rationale") or "")}</p>
              <details open><summary>证据</summary>{ul(dim.get("evidence"))}</details>
              <details><summary>扣分点</summary>{ul(dim.get("deductions"), "无明显扣分")}</details>
              <details><summary>提分动作</summary>{ul(dim.get("lift_actions"), "暂无")}</details>
            </div>
            """)
        blocks.append(f"""
        <article class="card">
          <h3>{h(resume.get("name") or resume.get("id") or "简历")}</h3>
          {''.join(dims) or '<div class="empty">暂无维度评分。</div>'}
        </article>
        """)
    return "\n".join(blocks)


def render_risks(resumes: list[dict]) -> str:
    rows = []
    for resume in resumes:
        for flag in as_list(resume.get("red_flags")):
            if isinstance(flag, dict):
                severity = str(flag.get("severity") or "medium")
                rows.append(f"""
                <div>
                  <span class="tag {h(severity)}">{h(severity)}</span>
                  <strong>{h(resume.get("id"))} · {h(flag.get("title") or "风险")}</strong>
                  <p>{h(flag.get("detail") or "")}</p>
                  {ul(flag.get("evidence"), "无额外证据")}
                </div>
                """)
            elif str(flag).strip():
                rows.append(f"<p>{h(resume.get('id'))} · {h(flag)}</p>")
        for risk in as_list(resume.get("interview_risks")):
            if str(risk).strip():
                rows.append(f"<p><span class=\"tag medium\">interview</span><strong>{h(resume.get('id'))}</strong> · {h(risk)}</p>")
    return "\n".join(rows) or '<div class="empty">暂无明显可信度或面试风险。</div>'


def render_ats(resumes: list[dict]) -> str:
    rows = []
    for resume in resumes:
        notes = [str(item).strip() for item in as_list(resume.get("ats_notes")) if str(item).strip()]
        jd_fit = resume.get("jd_fit") if isinstance(resume.get("jd_fit"), dict) else {}
        if jd_fit:
            matched = ", ".join(str(x) for x in as_list(jd_fit.get("matched_keywords")) if str(x).strip())
            missing = ", ".join(str(x) for x in as_list(jd_fit.get("missing_keywords")) if str(x).strip())
            if matched:
                notes.append(f"已命中关键词：{matched}")
            if missing:
                notes.append(f"缺失关键词：{missing}")
            for note in as_list(jd_fit.get("notes")):
                if str(note).strip():
                    notes.append(str(note))
        if notes:
            rows.append(f"<h4>{h(resume.get('name') or resume.get('id'))}</h4>{ul(notes)}")
    return "\n".join(rows) or '<div class="empty">暂无 ATS 或 JD 关键词备注。</div>'


def render_lifts(resumes: list[dict]) -> str:
    cards = []
    for resume in resumes:
        for item in as_list(resume.get("score_lifts")):
            if isinstance(item, dict):
                cards.append(f"""
                <article class="card">
                  <span class="tag">{h(resume.get("id"))}</span>
                  <strong>{h(item.get("action") or "提分动作")}</strong>
                  <p>{h(item.get("why") or "")}</p>
                  <p class="muted">预计提分：{h(item.get("estimated_gain") or "未估")} · 工作量：{h(item.get("effort") or "未估")}</p>
                </article>
                """)
            elif str(item).strip():
                cards.append(f'<article class="card"><span class="tag">{h(resume.get("id"))}</span>{h(item)}</article>')
    return "\n".join(cards) or '<div class="card empty">暂无提分杠杆。</div>'


def render_missing(analysis: dict) -> str:
    missing = ul(analysis.get("missing_information"), "暂无缺失信息。")
    return f"<p><strong>置信度：</strong>{h(analysis.get('confidence') or 'medium')}</p>{missing}"


def render_report(analysis: dict, template: str) -> str:
    resumes = [item for item in as_list(analysis.get("resumes")) if isinstance(item, dict)]
    replacements = {
        "REPORT_TITLE": h(analysis.get("report_title") or "简历评分卡报告"),
        "OVERALL_SUMMARY": h(analysis.get("overall_summary") or "暂无总体结论。"),
        "META_CHIPS": render_meta(analysis),
        "SCORE_CARDS": render_score_cards(resumes),
        "COMPARISON_SECTION": render_comparison(analysis, resumes),
        "DIMENSION_SECTIONS": render_dimension_sections(resumes),
        "RISK_ITEMS": render_risks(resumes),
        "ATS_ITEMS": render_ats(resumes),
        "LIFT_ITEMS": render_lifts(resumes),
        "MISSING_INFORMATION": render_missing(analysis),
    }
    output = template
    for key, value in replacements.items():
        output = output.replace("{{" + key + "}}", str(value))
    unresolved = sorted(set(re.findall(r"\{\{[A-Z0-9_]+\}\}", output)))
    if unresolved:
        raise SystemExit("Unresolved placeholders in report: " + ", ".join(unresolved))
    return output


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--analysis", required=True, help="resume_scorecard_analysis.json")
    parser.add_argument("--output", required=True, help="Output HTML path")
    parser.add_argument("--template", help="Optional template path")
    parser.add_argument("--strict", action="store_true", help="Validate and fail on warnings/errors")
    args = parser.parse_args()

    analysis_path = Path(args.analysis).expanduser().resolve()
    analysis = load_json(analysis_path)
    if args.strict:
        findings = validate_analysis_payload(analysis)
        errors = [item for item in findings if item["level"] == "error"]
        warnings = [item for item in findings if item["level"] == "warning"]
        if findings:
            print(format_findings(findings))
        if errors or warnings:
            raise SystemExit(1)

    skill_dir = Path(__file__).resolve().parents[1]
    template_path = Path(args.template).expanduser().resolve() if args.template else skill_dir / "assets" / "report-template.html"
    template = template_path.read_text(encoding="utf-8")
    html_text = render_report(analysis, template)

    output = Path(args.output).expanduser().resolve()
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(html_text, encoding="utf-8")
    print(f"Wrote {output}")


if __name__ == "__main__":
    main()
