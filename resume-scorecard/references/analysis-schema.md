# Resume Scorecard Analysis Schema

Create `resume_scorecard_analysis.json` before rendering an HTML report.

## Minimal Command

```bash
python3 <skill_dir>/scripts/validate_scorecard.py \
  --analysis /path/to/resume_scorecard_analysis.json \
  --strict
```

Render:

```bash
python3 <skill_dir>/scripts/render_scorecard_report.py \
  --analysis /path/to/resume_scorecard_analysis.json \
  --output /path/to/resume-scorecard-report.html \
  --auto-redact \
  --strict
```

End-to-end sample:

```bash
python3 <skill_dir>/scripts/validate_scorecard.py \
  --analysis <skill_dir>/examples/complete-analysis-sample.json \
  --strict

python3 <skill_dir>/scripts/render_scorecard_report.py \
  --analysis <skill_dir>/examples/complete-analysis-sample.json \
  --output /tmp/resume-scorecard-sample.html \
  --auto-redact \
  --strict
```

## Required Shape Sketch

The following sketch shows field placement and may abbreviate repeated dimensions. Use `examples/complete-analysis-sample.json` for a strict-valid full example.

```json
{
  "report_title": "简历评分卡报告",
  "score_mode": "standalone",
  "candidate_label": "候选人",
  "target_role": "未指定，按无 JD 单独评分",
  "jd_summary": "未提供 JD，本次只评估简历本体质量与通用投递竞争力。",
  "overall_summary": "这份简历项目经历较强，但量化结果和岗位关键词承接不足。",
  "confidence": "medium",
  "generated_at": "2026-06-29 20:00",
  "resumes": [
    {
      "id": "A",
      "name": "当前简历",
      "source": "resume.md",
      "target_role": "前端开发",
      "target_industry": "互联网 / 软件开发",
      "scoring_context": "无 JD，按前端开发通用岗位预期评分",
      "total_score": 82,
      "band": "A",
      "score_summary": "整体可投，但还不是 90+，主要扣分来自项目结果量化不足和技能证据分散。",
      "experience_benchmark": {
        "estimated_years": 2,
        "current_band": "1-3 年",
        "next_band": "3-5 年",
        "benchmark_note": "该均分是本 skill 基于 100 分评分尺标设定的经验段参考基准，用于横向对标，不代表招聘市场真实统计均值。",
        "basis": [
          "简历显示约 2 年前端相关实习/工作经历"
        ],
        "bands": [
          {
            "band": "1-3 年",
            "average_score": 72,
            "competitive_score": 80,
            "excellent_score": 88,
            "candidate_delta": 10,
            "expectations": "需要真实项目、明确个人边界、若干量化结果和清晰岗位主线。"
          },
          {
            "band": "3-5 年",
            "average_score": 78,
            "competitive_score": 85,
            "excellent_score": 90,
            "candidate_delta": 4,
            "expectations": "需要独立模块 ownership、业务影响、跨团队协作、技术取舍和稳定交付证据。"
          }
        ],
        "interpretation": "这份简历高于 1-3 年参考均分，也略高于 3-5 年参考均分；若要按 3-5 年强竞争力包装，还需要补足独立负责范围和业务结果口径。"
      },
      "presentation_review": {
        "score": 78,
        "band": "B",
        "confidence": "medium",
        "layout_evidence": "extracted_text",
        "summary": "整体结构清楚，但信息密度偏高，模块层级不够利于 10 秒扫描。",
        "criteria": [
          {
            "name": "信息层级与首屏抓取",
            "score": 18,
            "max_score": 25,
            "rationale": "首屏能看出目标岗位，但核心成果没有足够突出。",
            "evidence": ["顶部有目标岗位", "项目标题明确"],
            "deductions": ["摘要偏长，最强成果未前置"]
          },
          {
            "name": "版面密度与留白",
            "score": 15,
            "max_score": 20,
            "rationale": "内容可读，但 bullet 密度偏高，留白不足。",
            "evidence": ["模块边界清楚"],
            "deductions": ["部分项目描述连续堆叠，扫读成本偏高"]
          },
          {
            "name": "字体、字号、对齐与一致性",
            "score": 12,
            "max_score": 15,
            "rationale": "标题、日期和项目块基本一致，但局部标点和技术栈格式不统一。",
            "evidence": ["多数模块标题样式一致"],
            "deductions": ["日期、技术栈和项目标题格式可以进一步统一"]
          },
          {
            "name": "模块组织与视觉引导",
            "score": 12,
            "max_score": 15,
            "rationale": "模块顺序基本符合前端岗位阅读习惯，但强项目可以更靠前。",
            "evidence": ["教育、技能、项目模块完整"],
            "deductions": ["最强项目没有在首屏附近形成视觉锚点"]
          },
          {
            "name": "ATS/机器解析友好度",
            "score": 13,
            "max_score": 15,
            "rationale": "文本结构大体标准，机器解析风险不高。",
            "evidence": ["使用常规模块名称"],
            "deductions": ["仍需确认导出 PDF 后文本可复制且阅读顺序正确"]
          },
          {
            "name": "专业感与岗位气质",
            "score": 8,
            "max_score": 10,
            "rationale": "整体偏专业，符合技术岗简历的克制风格。",
            "evidence": ["没有过度装饰"],
            "deductions": ["成果层级不够突出，第一眼冲击力有限"]
          }
        ],
        "strengths": [
          "模块边界清楚，阅读顺序基本稳定"
        ],
        "issues": [
          "首屏没有把最强项目和量化成果做视觉突出"
        ],
        "lift_actions": [
          "把最强项目压缩为 3 行结果型摘要",
          "统一日期、项目标题和技术栈格式"
        ],
        "ats_layout_notes": [
          "确认导出 PDF 后文本可复制；避免把联系方式放在不可解析文本框中"
        ]
      },
      "dimensions": [
        {
          "name": "目标定位与岗位对齐",
          "score": 12,
          "max_score": 15,
          "rationale": "目标岗位基本清晰，但摘要和项目排序没有完全围绕前端开发展开。",
          "evidence": ["求职意向写明前端开发", "项目经历包含 Vue/uni-app"],
          "deductions": ["顶部摘要未突出最强项目或核心技术栈"],
          "lift_actions": ["把目标岗位和 2-3 个核心技术关键词放到首屏，可提升 1-2 分"]
        }
      ],
      "strengths": [
        "项目数量和技术栈与目标岗位相关"
      ],
      "weaknesses": [
        "多数项目 bullet 缺少量化结果或业务规模"
      ],
      "red_flags": [
        {
          "severity": "medium",
          "title": "技能列表缺少项目佐证",
          "detail": "部分技能只在技能栏出现，经历中没有对应证据。",
          "evidence": ["技能栏列出 Redis，但项目经历未出现 Redis 使用场景"]
        }
      ],
      "ats_notes": [
        "建议使用标准章节名：教育经历、专业技能、项目经历、实习经历"
      ],
      "jd_fit": {
        "score": 76,
        "must_have_coverage": "中",
        "matched_keywords": ["Vue", "TypeScript", "小程序"],
        "missing_keywords": ["工程化", "性能优化", "组件库"],
        "notes": ["JD 未提供时可省略或写通用判断"]
      },
      "interview_risks": [
        "如果被追问性能优化效果，当前简历缺少测量方法和前后对比"
      ],
      "score_lifts": [
        {
          "action": "为 2 个核心项目补充规模、结果或可验证产出",
          "estimated_gain": "+4-6",
          "effort": "medium",
          "why": "能同时提高证据强度和面试可防守性"
        }
      ]
    }
  ],
  "comparison": {
    "winner": "A",
    "context_type": "same_target",
    "reason": "A 版目标更清晰，项目证据更强。",
      "delta_summary": [
      "A 比 B 高 6 分，主要来自项目深度和 ATS 可读性。"
    ],
    "normalized_axes": [
      {
        "axis": "Evidence density",
        "winner": "A",
        "scores": {"A": "high", "B": "medium"},
        "reason": "A 的项目结果和个人贡献证据更密集。"
      }
    ],
    "best_for": [
      {"scenario": "投前端工程岗", "resume_id": "A", "reason": "技术关键词和项目顺序更贴合"}
    ]
  },
  "missing_information": [
    "未提供目标 JD，因此关键词覆盖只能按通用岗位判断"
  ]
}
```

## Field Rules

- `score_mode`: use `standalone`, `jd_fit`, `comparison`, or `cross_industry_comparison` for new reports. `single` is legacy-compatible only; do not use it for new JSON.
- If there is no JD but a `target_role` is provided, still use `standalone`; set `target_role` and explain the role-market basis in `resumes[].scoring_context`.
- `confidence`: use `high`, `medium`, or `low`.
- `resumes`: must contain at least one resume object.
- `resumes[].target_role`: optional but recommended, and required in cross-industry comparisons when the target differs by resume.
- `resumes[].target_industry`: optional but recommended for cross-industry comparisons.
- `resumes[].scoring_context`: explain whether the resume was scored against a JD, role-market expectation, or universal baseline.
- `total_score`: 0-100. Keep it consistent with dimension scores.
- Do not create a separate `baseline_resume_score`; no-JD scoring still writes the main score to `total_score`.
- `band`: may be omitted; renderer can infer it.
- `experience_benchmark`: optional but recommended whenever years can be inferred or provided. Include the current experience band and the next higher band. If experience is unknown, omit it or set `estimated_years` to `"unknown"` and explain in `missing_information`.
- `experience_benchmark.estimated_years`: numeric years or `"unknown"`. Do not over-precision; `2`, `2.5`, or `"unknown"` is enough.
- `experience_benchmark.bands[]`: include at least two rows when known: current band and next higher band.
- `experience_benchmark.bands[].average_score`: internal benchmark average for that experience band.
- `experience_benchmark.bands[].candidate_delta`: `total_score - average_score`. May be omitted if experience or total score is unknown.
- `presentation_review`: optional but recommended whenever PDF/DOCX layout evidence, rendered pages, or structural signals are available.
- `presentation_review.score`: separate 0-100 presentation/layout score. Do not add it to `total_score`.
- `presentation_review.band`: optional; renderer can infer it from `presentation_review.score`.
- `presentation_review.confidence`: use `high`, `medium`, or `low`. Use `high` only when rendered layout or reliable PDF/DOCX evidence is available.
- `presentation_review.layout_evidence`: use `rendered_file`, `file_structure`, `extracted_text`, `pasted_text`, or `ocr_only`. Use `references/input-parsing.md` for score caps; validator warns when the presentation score exceeds the cap for the declared evidence level.
- `presentation_review.criteria[]`: recommended. The sum of `max_score` should be 100 when criteria are included.
- `presentation_review.criteria[].score` and `max_score`: numeric; score must be between 0 and max_score.
- `presentation_review.strengths`, `issues`, `lift_actions`, and `ats_layout_notes`: lists of concise, evidence-based observations. Do not include private contact details.
- `dimensions`: required for each resume. The sum of `max_score` should be 100 in strict reports.
- `red_flags.severity`: use `high`, `medium`, or `low`.
- `score_lifts.estimated_gain`: write ranges like `+2-4`, not guaranteed outcomes.
- `comparison`: required when `score_mode` is `comparison` / `cross_industry_comparison` or when `resumes` has more than one item.
- `comparison.context_type`: use `same_target`, `same_industry`, `cross_role`, `cross_industry`, or `universal_baseline`.
- For cross-industry comparisons, include scenario-specific winners in `comparison.best_for` rather than only one absolute winner.
- For cross-industry comparisons, include `comparison.normalized_axes[]` to make the normalized quality comparison reproducible. Each item should include `axis`, `winner`, optional `scores`, and `reason`.
- Do not include private phone numbers, email addresses, exact addresses, ID numbers, or private URLs in report fields. Validator warnings are blocking in `--strict`; use `--redacted-output` on `validate_scorecard.py` or `--auto-redact` on `render_scorecard_report.py` to generate a sanitized artifact.

## Recommended Chinese Dimension Names

- `目标定位与岗位对齐`
- `证据强度与量化结果`
- `经历/项目深度`
- `岗位能力与技能信号`
- `结构、ATS 与可读性`
- `可信度与面试可防守性`

## Recommended Chinese Presentation Criteria Names

- `信息层级与首屏抓取`
- `版面密度与留白`
- `字体、字号、对齐与一致性`
- `模块组织与视觉引导`
- `ATS/机器解析友好度`
- `专业感与岗位气质`
