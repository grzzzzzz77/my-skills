---
name: contrib-skill
description: Analyze a local Git repository's contribution history and generate evidence-backed project summaries, resume bullets, interview scripts, and claim-risk reports. Use when the user wants to understand what someone contributed to a codebase, package real project experience for a resume, prepare interview talking points, or audit whether contribution claims are safe under background checks.
---

# contrib-skill

Use this skill when the user wants to turn Git history into credible career material:

- analyze a local repository's project background, architecture, tech stack, and contributor activity
- summarize a specific author's real contributions from commits and diffs
- generate evidence-backed resume bullets and STAR/project descriptions
- prepare interview scripts, technical challenge explanations, and follow-up answers
- check whether a resume claim is `safe`, `needs_confirmation`, or `risky`

This skill must not fabricate metrics or ownership claims. Keep strong wording such as "led", "owned", "built from scratch", or "independently responsible for" only when the generated report has strong Git evidence. When evidence is weak, use conservative wording like "participated in", "contributed to", or "assisted with".

## Setup

The repository is a Python package and requires Python 3.10+ plus `git`.

From this skill directory:

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
```

If dependencies are already installed, use the existing environment. Do not install dependencies without user approval when the current environment requires approval.

## Main Command

Run the CLI against a local Git repository:

```bash
contrib-skill analyze --repo /path/to/project --author "Author Name" --mode full
```

Useful options:

- `--repo`: target Git repository, defaults to current directory
- `--author`: target author name or email, matched case-insensitively as a substring
- `--all-authors`: analyze every author; resume material defaults to the top committer
- `--base` / `--branch`: analyze only the `base..branch` commit range
- `--since` / `--until`: date window, such as `2025-01-01`
- `--mode`: `full`, `resume`, `interview`, `audit`, or `strict`
- `--target-role`: tailor resume material to a role
- `--output`: output directory, defaults to `./contrib_output`
- `--include-diff`: keep per-file numstat in `evidence.json`
- `--strict`: keep only evidence-backed safe claims

## Output

The tool writes a `contrib_output/` directory containing:

- `evidence.json` and `metrics.json`
- project overview and architecture analysis
- Git history and author contribution summaries
- key commit analysis
- resume bullets
- interview script
- claim-risk report
- `full_report.md`

After running it, summarize the safest findings first: verified contributions, suggested resume wording, interview talking points, and risky claims to avoid.

## Safety Rules

- Do not present heuristic business or architecture inference as fact; preserve confidence labels.
- Do not invent performance, scale, revenue, user, or team-size numbers.
- Do not upgrade `needs_confirmation` or `risky` claims into safe resume language.
- When the target author is ambiguous, show the available Git authors and ask the user which one to analyze.
