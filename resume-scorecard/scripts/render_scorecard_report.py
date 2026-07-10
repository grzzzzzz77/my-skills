#!/usr/bin/env python3
"""Render a resume-scorecard v2 HTML report."""

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

from validate_scorecard import format_findings, redact_payload, validate_analysis_payload


AXIS_LABELS = {
    "career_capital": "履历含金量",
    "communication_quality": "内容表达质量",
    "presentation_quality": "排版布局质量",
    "jd_fit": "JD 匹配度",
}
AXIS_ORDER = ("career_capital", "communication_quality", "presentation_quality", "jd_fit")


def h(value: Any) -> str:
    return html.escape("" if value is None else str(value), quote=True)


def as_list(value: Any) -> list:
    if value is None:
        return []
    return value if isinstance(value, list) else [value]


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
    try:
        return float(str(value))
    except Exception:
        return fallback


def shown_score(value: Any) -> str:
    score = score_number(value)
    return str(int(score)) if score.is_integer() else str(round(score, 1))


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


def table_scroll(table_html: str) -> str:
    return f'<div class="table-scroll">{table_html}</div>'


def render_meta(analysis: dict) -> str:
    generated = analysis.get("generated_at") or datetime.now().strftime("%Y-%m-%d %H:%M")
    chips = [
        ("Schema", analysis.get("schema_version") or "2.0"),
        ("评分模式", analysis.get("score_mode") or "standalone"),
        ("目标岗位", analysis.get("target_role") or "未指定"),
        ("JD", "已提供" if analysis.get("jd_provided") else "未提供"),
        ("总体置信度", analysis.get("confidence") or "medium"),
        ("生成时间", generated),
    ]
    if analysis.get("candidate_label"):
        chips.insert(0, ("对象", analysis.get("candidate_label")))
    return "".join(f'<span class="chip"><strong>{h(label)}:</strong> {h(value)}</span>' for label, value in chips)


def render_axis_mini(axis_name: str, axis: dict) -> str:
    score = score_number(axis.get("score"))
    note = ""
    if axis_name == "presentation_quality":
        note = f" · {h(axis.get('layout_evidence') or '未标注证据')}"
    if axis_name == "jd_fit":
        note = f" · {h(axis.get('must_have_coverage') or '未标注覆盖')}"
    return f"""
    <div class="axis-mini">
      <div class="axis-mini-head"><span>{h(AXIS_LABELS[axis_name])}</span><strong>{h(shown_score(score))}</strong></div>
      <div class="bar"><span style="width:{max(0, min(100, score)):.1f}%"></span></div>
      <p class="muted">{h(axis.get('band') or '')} · 置信度 {h(axis.get('confidence') or 'medium')}{note}</p>
    </div>
    """


def render_score_cards(resumes: list[dict]) -> str:
    cards = []
    for resume in resumes:
        core = score_number(resume.get("core_score"))
        axes = resume.get("score_axes") if isinstance(resume.get("score_axes"), dict) else {}
        axis_html = "".join(render_axis_mini(name, axes[name]) for name in AXIS_ORDER if isinstance(axes.get(name), dict))
        coverage = resume.get("evidence_coverage") if isinstance(resume.get("evidence_coverage"), dict) else {}
        context = " · ".join(
            str(value)
            for value in (resume.get("target_role"), resume.get("role_family"), resume.get("candidate_stage"))
            if value
        )
        cards.append(f"""
        <article class="card score-card">
          <div class="top">
            <div><h3>{h(resume.get('name') or resume.get('id') or '简历')}</h3><p class="muted">{h(context)}</p></div>
            <span class="band{band_class(core)}">{h(resume.get('band') or '')}</span>
          </div>
          <div class="core-row">
            <div><div class="eyebrow">核心竞争力</div><div class="score">{h(shown_score(core))}</div></div>
            <div class="formula">履历含金量 70% + 内容表达 30%<br>排版与 JD 不进入核心分</div>
          </div>
          <div class="bar core-bar"><span style="width:{max(0, min(100, core)):.1f}%"></span></div>
          <p>{h(resume.get('score_summary') or '')}</p>
          <div class="axis-grid">{axis_html}</div>
          <div class="coverage"><strong>证据覆盖：</strong>{h(coverage.get('score') or '未估')}/100 · {h(coverage.get('status') or '未标注')} · {h(coverage.get('summary') or '')}</div>
        </article>
        """)
    return "".join(cards)


def render_axis_sections(resumes: list[dict]) -> str:
    blocks = []
    for resume in resumes:
        axes = resume.get("score_axes") if isinstance(resume.get("score_axes"), dict) else {}
        for axis_name in AXIS_ORDER:
            axis = axes.get(axis_name)
            if not isinstance(axis, dict):
                continue
            score = score_number(axis.get("score"))
            dimensions = []
            for dim in as_list(axis.get("dimensions")):
                if not isinstance(dim, dict):
                    continue
                dim_score = score_number(dim.get("score"))
                max_score = max(1.0, score_number(dim.get("max_score"), 1.0))
                percent = max(0, min(100, dim_score / max_score * 100))
                dimensions.append(f"""
                <div class="dimension">
                  <div class="dim-head"><strong>{h(dim.get('name') or dim.get('id'))}</strong><span class="dim-score">{h(dim.get('score'))}/{h(dim.get('max_score'))}</span></div>
                  <div class="bar"><span style="width:{percent:.1f}%"></span></div>
                  <p>{h(dim.get('rationale') or '')}</p>
                  <p class="muted">置信度：{h(dim.get('confidence') or 'medium')}</p>
                  <div class="two-col compact">
                    <details open><summary>正向证据</summary>{ul(dim.get('evidence'), '暂无充分证据')}</details>
                    <details><summary>证据缺口</summary>{ul(dim.get('gaps'), '无材料性缺口')}</details>
                  </div>
                  <details><summary>提升动作</summary>{ul(dim.get('lift_actions'), '暂无')}</details>
                </div>
                """)
            extra = ""
            if axis_name == "presentation_quality":
                extra = f"""
                <div class="callout"><strong>版式证据：</strong>{h(axis.get('layout_evidence') or '未标注')}。该分数独立于核心分。</div>
                <div class="two-col"><div><h4>外观优势</h4>{ul(axis.get('strengths'))}</div><div><h4>版式问题</h4>{ul(axis.get('issues'))}</div><div><h4>版式动作</h4>{ul(axis.get('lift_actions'))}</div><div><h4>ATS 版式备注</h4>{ul(axis.get('ats_layout_notes'))}</div></div>
                """
            elif axis_name == "jd_fit":
                extra = f"""
                <div class="callout"><strong>硬性条件覆盖：</strong>{h(axis.get('must_have_coverage') or '未标注')}。JD 分独立于核心分。</div>
                <div class="two-col"><div><h4>命中项</h4>{ul(axis.get('matched_keywords'))}</div><div><h4>缺失项</h4>{ul(axis.get('missing_keywords'))}</div></div>
                """
            blocks.append(f"""
            <article class="card axis-card">
              <div class="top"><div><h3>{h(resume.get('name') or resume.get('id'))} · {h(AXIS_LABELS[axis_name])}</h3><p>{h(axis.get('summary') or '')}</p></div><div class="axis-score"><span class="band{band_class(score)}">{h(axis.get('band') or '')}</span><strong>{h(shown_score(score))}</strong></div></div>
              {extra}
              {''.join(dimensions)}
            </article>
            """)
    return "".join(blocks)


def render_issue_ledger(resumes: list[dict]) -> str:
    rows = []
    for resume in resumes:
        for issue in as_list(resume.get("issue_ledger")):
            if not isinstance(issue, dict):
                continue
            cross = ", ".join(str(item) for item in as_list(issue.get("cross_references"))) or "—"
            rows.append(
                "<tr>"
                f"<td>{h(resume.get('id'))}</td>"
                f"<td><code>{h(issue.get('issue_id'))}</code><br><strong>{h(issue.get('title'))}</strong></td>"
                f"<td><span class=\"tag {h(issue.get('severity') or 'medium')}\">{h(issue.get('kind'))}</span></td>"
                f"<td>{h(issue.get('primary_axis'))}<br>{h(issue.get('primary_dimension'))}</td>"
                f"<td>{h(issue.get('points'))}</td>"
                f"<td>{h(issue.get('detail'))}{ul(issue.get('evidence'), '暂无证据')}</td>"
                f"<td>{h(cross)}</td>"
                "</tr>"
            )
    if not rows:
        return '<div class="card empty">暂无材料性问题台账。</div>'
    table = "<table><thead><tr><th>版本</th><th>问题</th><th>类型</th><th>唯一计分位置</th><th>分值影响</th><th>说明与证据</th><th>仅引用</th></tr></thead><tbody>" + "".join(rows) + "</tbody></table>"
    return table_scroll(table)


def render_stage_benchmarks(resumes: list[dict]) -> str:
    blocks = []
    for resume in resumes:
        benchmark = resume.get("stage_benchmark")
        if not isinstance(benchmark, dict):
            continue
        rows = []
        for row in as_list(benchmark.get("stages")):
            if not isinstance(row, dict):
                continue
            rows.append(
                "<tr>"
                f"<td>{h(row.get('stage'))}</td><td>{h(row.get('reference_score'))}</td>"
                f"<td>{h(row.get('strong_score'))}</td><td>{h(row.get('exceptional_score'))}</td>"
                f"<td>{h(row.get('candidate_delta'))}</td><td>{ul(row.get('expectations'))}</td>"
                "</tr>"
            )
        table = "<table><thead><tr><th>阶段</th><th>参考线</th><th>强水平</th><th>卓越线</th><th>候选人差值</th><th>期望</th></tr></thead><tbody>" + "".join(rows) + "</tbody></table>"
        blocks.append(f"""
        <article class="card"><h3>{h(resume.get('name') or resume.get('id'))}</h3>
          <p>{h(benchmark.get('interpretation') or '')}</p>{table_scroll(table)}
          <p class="muted">{h(benchmark.get('note') or '内部阶段期望锚点，不是市场平均值或百分位。')}</p>
        </article>
        """)
    if not blocks:
        return ""
    return '<section class="section"><h2>阶段期望锚点</h2><div class="callout">仅基于履历含金量，用于内部尺标校准；不代表市场平均值、排名或百分位。</div><div class="grid">' + "".join(blocks) + "</div></section>"


def render_comparison(analysis: dict) -> str:
    comp = analysis.get("comparison")
    if not isinstance(comp, dict):
        return ""
    axis_rows = []
    for axis in as_list(comp.get("normalized_axes")):
        if not isinstance(axis, dict):
            continue
        scores = axis.get("scores") if isinstance(axis.get("scores"), dict) else {}
        score_text = "；".join(f"{key}: {value}" for key, value in scores.items())
        axis_rows.append(f"<tr><td>{h(axis.get('axis'))}</td><td>{h(axis.get('winner') or 'tie')}</td><td>{h(score_text)}</td><td>{h(axis.get('confidence') or '')}</td><td>{h(axis.get('reason'))}</td></tr>")
    best_rows = []
    for item in as_list(comp.get("best_for")):
        if isinstance(item, dict):
            best_rows.append(f"<tr><td>{h(item.get('scenario'))}</td><td>{h(item.get('resume_id'))}</td><td>{h(item.get('reason'))}</td></tr>")
    axes_table = table_scroll("<table><thead><tr><th>比较轴</th><th>领先/并列</th><th>数值</th><th>置信度</th><th>原因</th></tr></thead><tbody>" + "".join(axis_rows) + "</tbody></table>") if axis_rows else ""
    best_table = table_scroll("<table><thead><tr><th>场景</th><th>推荐版本</th><th>原因</th></tr></thead><tbody>" + "".join(best_rows) + "</tbody></table>") if best_rows else ""
    return f"""
    <section class="section"><h2>版本对比</h2><div class="card">
      <p class="muted">对比类型：{h(comp.get('context_type'))}</p>
      <p><strong>结论：</strong>{h(comp.get('winner') or '按场景判断')}</p><p>{h(comp.get('reason'))}</p>
      {ul(comp.get('delta_summary'), '暂无分差说明')}{axes_table}{best_table}
    </div></section>
    """


def render_risks(resumes: list[dict]) -> str:
    blocks = []
    for resume in resumes:
        flags = as_list(resume.get("red_flags"))
        risks = as_list(resume.get("interview_risks"))
        if flags or risks:
            blocks.append(f"<h4>{h(resume.get('name') or resume.get('id'))}</h4>{ul(flags, '暂无红旗')}{ul(risks, '暂无面试风险引用')}")
    return "".join(blocks) or '<div class="empty">暂无明显矛盾或高风险项。</div>'


def render_ats(resumes: list[dict]) -> str:
    blocks = []
    for resume in resumes:
        notes = as_list(resume.get("ats_notes"))
        if notes:
            blocks.append(f"<h4>{h(resume.get('name') or resume.get('id'))}</h4>{ul(notes)}")
    return "".join(blocks) or '<div class="empty">暂无 ATS 备注。</div>'


def render_lifts(resumes: list[dict]) -> str:
    cards = []
    for resume in resumes:
        for lift in as_list(resume.get("score_lifts")):
            if not isinstance(lift, dict):
                continue
            cards.append(f"""
            <article class="card"><span class="tag">{h(resume.get('id'))} · {h(AXIS_LABELS.get(lift.get('axis'), lift.get('axis')))}</span>
              <h3>{h(lift.get('action'))}</h3><p>{h(lift.get('why'))}</p>
              <p class="muted">预计区间：{h(lift.get('estimated_gain'))} · 工作量：{h(lift.get('effort') or '未估')}</p>
            </article>
            """)
    return "".join(cards) or '<div class="card empty">暂无提分杠杆。</div>'


def render_missing(analysis: dict) -> str:
    return f"<p><strong>总体置信度：</strong>{h(analysis.get('confidence') or 'medium')}</p>{ul(analysis.get('missing_information'), '暂无缺失信息')}"


def render_report(analysis: dict, template: str) -> str:
    resumes = [item for item in as_list(analysis.get("resumes")) if isinstance(item, dict)]
    replacements = {
        "REPORT_TITLE": h(analysis.get("report_title") or "简历多轴评分卡报告"),
        "OVERALL_SUMMARY": h(analysis.get("overall_summary") or "暂无总体结论。"),
        "META_CHIPS": render_meta(analysis),
        "SCORE_CARDS": render_score_cards(resumes),
        "STAGE_BENCHMARK_SECTION": render_stage_benchmarks(resumes),
        "COMPARISON_SECTION": render_comparison(analysis),
        "AXIS_SECTIONS": render_axis_sections(resumes),
        "ISSUE_LEDGER": render_issue_ledger(resumes),
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
    parser.add_argument("--analysis", required=True)
    parser.add_argument("--output", required=True)
    parser.add_argument("--template")
    parser.add_argument("--strict", action="store_true")
    parser.add_argument("--auto-redact", action="store_true")
    args = parser.parse_args()

    analysis = load_json(Path(args.analysis).expanduser().resolve())
    if args.auto_redact:
        analysis = redact_payload(analysis)
    if args.strict:
        findings = validate_analysis_payload(analysis)
        if findings:
            print(format_findings(findings))
            raise SystemExit(1)

    skill_dir = Path(__file__).resolve().parents[1]
    template_path = Path(args.template).expanduser().resolve() if args.template else skill_dir / "assets" / "report-template.html"
    template = template_path.read_text(encoding="utf-8")
    output = Path(args.output).expanduser().resolve()
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(render_report(analysis, template), encoding="utf-8")
    print(f"Wrote {output}")


if __name__ == "__main__":
    main()
