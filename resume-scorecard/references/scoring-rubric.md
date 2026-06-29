# Resume Scorecard Rubric

Use this rubric to score resume competitiveness. The score is diagnostic, not a hiring probability.

## Default 100-Point Rubric

| Dimension | Points | What It Measures |
|---|---:|---|
| Target clarity and role alignment | 15 | Whether the resume has a clear target, role-relevant headline/summary, and a consistent story for the intended role. |
| Evidence strength and quantified impact | 20 | Whether bullets contain concrete actions, scope, results, metrics, artifacts, or proof instead of generic responsibilities. |
| Experience and project depth | 20 | Whether work/projects show real complexity, ownership boundary, business scenario, technical depth, and interview-expandable stories. |
| Role competency and skill signal | 15 | Whether skills and keywords match the role and are backed by experience/projects, not just listed. |
| Structure, ATS, and scanability | 15 | Whether the resume is readable in 6-10 seconds, follows standard sections, and is likely ATS-friendly. |
| Credibility and interview defensibility | 15 | Whether claims are truthful, consistent, risk-aware, and survivable under follow-up. |

## JD-Fit Mode Adjustment

When a JD is provided, keep the 100-point total but interpret dimensions this way:

| Dimension | Points | JD-Fit Interpretation |
|---|---:|---|
| Target clarity and role alignment | 15 | Does the top third clearly answer this JD's target role? |
| Evidence strength and quantified impact | 20 | Are relevant achievements concrete enough for this JD's seniority and business expectations? |
| Experience and project depth | 20 | Do the strongest experiences map to the JD's core work rather than adjacent/noisy work? |
| Role competency and skill signal | 15 | Must-have and preferred keywords covered naturally in skills and experience. |
| Structure, ATS, and scanability | 15 | ATS parsing, section names, keyword placement, length, and recruiter scanning. |
| Credibility and interview defensibility | 15 | Risk that the resume overclaims JD fit, ownership, or metrics. |

## Standalone No-JD Scoring

Use this when the user provides a resume but no JD. This is allowed and should not be treated as incomplete. Score the resume as a standalone artifact:

- Does the resume declare a coherent direction by itself?
- Does the top third let a recruiter understand the candidate in 6-10 seconds?
- Are experiences written with action, method, scope, and result?
- Are projects/work experiences deep enough to survive interviews?
- Are skills supported by bullets?
- Is the layout ATS-safe and readable?
- Are claims credible without needing hidden context?

If no target role is provided, use universal resume quality and market-readiness. Do not deduct for missing JD-specific keywords. Instead mark confidence as `medium` and state that JD-fit cannot be assessed.

Suggested standalone language:

```text
本次为无 JD 单独评分，分数代表简历本体质量与通用投递竞争力，不代表某个具体岗位的匹配概率。
```

## Cross-Industry Comparison

Use this when comparing resumes for different roles, industries, or career directions, such as "前端简历 vs 产品简历" or "技术岗简历 vs 运营岗简历".

Do not force both resumes into one JD. Score each resume in one of two ways:

1. **Own-target scoring**: each resume is scored against its declared role/industry.
2. **Universal baseline scoring**: if targets are unclear, score both on universal resume quality: clarity, evidence density, depth, scanability, and credibility.

Then compare normalized dimensions:

- Evidence density: which resume proves claims better?
- Market clarity: which resume makes its target clearer?
- Transferability: which resume has stronger reusable skills across industries?
- Risk level: which resume is more likely to fail under interview follow-up?
- Upgrade path: which resume can reach 85/90+ with less work?

Winner language must be scenario-specific:

```text
如果目标是技术岗，A 更强；如果目标是泛运营/产品转向，B 的叙事更顺。但按通用简历质量，A 的证据密度和面试可防守性更高。
```

Avoid:

```text
A 简历一定比 B 简历好。
```

## Score Bands

| Score | Band | Meaning |
|---:|---|---|
| 90-100 | A+ | Strong submit-ready resume for the target. Only minor polish remains. |
| 80-89 | A | Competitive, but one or two meaningful gaps prevent top-tier confidence. |
| 70-79 | B | Usable, but needs targeted work before serious applications. |
| 60-69 | C | Significant rebuild needed; likely underperforms against comparable candidates. |
| <60 | D | Not ready for this target; foundational content or positioning is missing. |

## 90+ Gate

A resume should not exceed 90 unless most of these are true:

- Target role is clear in the top third.
- At least 60-70% of major bullets have action + method + scope/result.
- Strongest projects or work experiences have credible ownership and depth.
- Key skills are evidenced in experience, not only listed.
- Formatting is ATS-safe and easy to scan.
- Claims do not depend on unverifiable inflated metrics.
- For JD mode, must-have requirements are substantially covered.

Common reasons to cap at 89:

- Good experience but weak metrics or proof.
- Strong project list but unclear personal contribution.
- Skills match the role but are not tied to bullets.
- Resume is strong generally but not tailored to the provided JD.
- Claims are plausible but would need confirmation in an interview.

## Dimension Anchors

### Target Clarity And Role Alignment (15)

- 13-15: Clear target role, coherent professional story, strongest evidence ordered for the role.
- 10-12: Direction is visible but top third or ordering could be sharper.
- 6-9: Multiple directions mixed together; recruiter must infer the target.
- 0-5: No clear target, or resume points at the wrong role.

### Evidence Strength And Quantified Impact (20)

- 17-20: Achievements include scope, metrics, artifacts, users, systems, or measurable outcomes.
- 13-16: Several concrete bullets, but some important claims lack numbers or results.
- 8-12: Mostly responsibilities with limited evidence.
- 0-7: Generic statements, little proof, no clear outcomes.

### Experience And Project Depth (20)

- 17-20: Experiences show complexity, tradeoffs, end-to-end ownership, and interview-ready stories.
- 13-16: Solid experiences, but depth or ownership is uneven.
- 8-12: Projects/work are present but shallow, school-like, or feature-list heavy.
- 0-7: Little relevant experience for the target.

### Role Competency And Skill Signal (15)

- 13-15: Core skills are role-relevant and evidenced in bullets/projects.
- 10-12: Good skill match but some skills are unsupported.
- 6-9: Skill list is noisy, too broad, or missing important role keywords.
- 0-5: Skills do not match target or cannot be trusted.

### Structure, ATS, And Scanability (15)

- 13-15: Standard sections, strong ordering, readable density, ATS-safe layout.
- 10-12: Generally readable but has length, ordering, or section-name issues.
- 6-9: Dense, inconsistent, hard to scan, or likely ATS-fragile.
- 0-5: Severe formatting or structure problems.

### Credibility And Interview Defensibility (15)

- 13-15: Claims are conservative, consistent, and easy to defend.
- 10-12: Mostly credible with a few unclear ownership/metric risks.
- 6-9: Several claims need proof or could trigger skeptical follow-up.
- 0-5: Obvious overclaiming, contradictions, or unsupported seniority.

## Confidence Levels

- `high`: full resume text plus target role/JD is available; file format/layout evidence is sufficient.
- `medium`: resume text is available but JD, role target, or layout evidence is incomplete.
- `low`: partial text, OCR uncertainty, missing target, or many assumptions.

Report confidence separately from score. A 86 with low confidence means "promising but under-verified", not "definitely A-level".
