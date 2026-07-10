#!/usr/bin/env python3
"""Validate project_resume_analysis.json for project-to-resume."""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
from typing import Any


RISK_VALUES = {"safe", "needs_confirmation", "risky"}
READINESS_VALUES = {"direct", "rewrite", "confirm", "idea"}
STAR_KEYS = ("situation", "task", "action", "result", "tradeoff")
TECH_BUSINESS_KEYS = ("technical_mechanism", "technical_difficulty", "business_value")
INTERVIEW_STORY_KEYS = (
    "title",
    "detail_anchor",
    "hardest_question",
    "answer_outline",
    "alternatives",
    "failure_boundary",
    "verification",
)
HIGHLIGHT_SCORE_KEYS = (
    "business_relevance",
    "technical_difficulty",
    "evidence_strength",
    "resume_readability",
    "differentiation",
    "handoff_readiness",
)
PROJECT_SCORE_LIMITS = {
    "technical_depth": 25,
    "ai_or_rarity_signal": 20,
    "business_completeness": 15,
    "evidence_and_quality": 15,
    "resume_readability": 15,
    "interview_expansion": 10,
}
LOGIC_CHAIN_TEXT_KEYS = (
    "plain_summary",
    "beginner_context",
    "problem",
    "trigger",
    "closure",
    "difficulty",
    "resume_connection",
    "limits",
)
DETAIL_ANCHOR_RE = re.compile(r"^[a-z0-9][a-z0-9_-]{1,80}$")

SENSITIVE_RE = re.compile(
    r"(?i)(password|passwd|secret|api[_-]?key|access[_-]?key|private[_-]?key|"
    r"credential|cookie|authorization|bearer|客户名称|客户名|内部客户|真实客户|"
    r"手机号|身份证|银行卡|邮箱[:：]|内网|生产库)"
)
TOKEN_SECRET_RE = re.compile(
    r"(?i)("
    r"(?:api|auth|access|refresh|id|private|secret)[_-]?token\s*[:=]\s*['\"][A-Za-z0-9._/+=-]{12,}['\"]|"
    r"token\s*[:=]\s*['\"][A-Za-z0-9._/+=-]{16,}['\"]|"
    r"bearer\s+[A-Za-z0-9._/+=-]{12,}|"
    r"(?:hardcode|hard-coded|leak|泄露|明文|硬编码|凭证|密钥)[^。；;\\n]{0,30}token"
    r")"
)

HIGH_OWNERSHIP_RE = re.compile(r"主导|全盘|独立负责|Owner|从\s*0\s*到\s*1|核心负责人", re.I)
UNCONFIRMED_METRIC_RE = re.compile(r"提升\s*\d|降低\s*\d|减少\s*\d|缩短\s*\d|增长\s*\d|\d+\s*%")
VAGUE_IMPACT_RE = re.compile(
    r"(?:提升|优化|改善|增强).{0,12}(?:效率|体验|性能|质量|稳定性|可维护性|业务价值)"
)
ROLE_AS_TRIGGER_RE = re.compile(r"^(?:负责|参与|配合|建设|开发|实现|封装|设计|优化|维护|完成)")
GENERIC_TEXT_RE = re.compile(
    r"^(?:(?:负责|参与|完成|实现|开发|优化|支持|建设|维护|封装)(?:了)?)?"
    r"(?:相关|某个|核心|业务)?(?:项目|系统|模块|功能|代码|需求|工作)(?:开发|建设|实现)?"
    r"(?:[,，；;。.]?(?:有一定技术难度|提升(?:了)?(?:业务)?(?:价值|效率|体验|性能|稳定性)|支持业务发展))?[。.]?$"
)
MECHANISM_SIGNAL_RE = re.compile(
    r"路由|守卫|状态机|缓存|队列|重试|幂等|事务|锁|分页|虚拟列表|防抖|节流|拦截|"
    r"映射|解析|校验|协议|适配|编排|抽象|分层|网关|索引|检索|向量|提示词|上下文|"
    r"工具调用|模型|流式|WebSocket|SSE|MCP|RAG|API|IPC|AST|ORM|组件|服务层|请求层|"
    r"持久化|降级|兜底|并发|批处理|权限|鉴权|RBAC|签名|上传|序列化|Schema|SQL|Redis",
    re.I,
)
DIFFICULTY_SIGNAL_RE = re.compile(
    r"竞态|过期响应|stale|并发|一致性|边界|异常|失败|超时|重试|幂等|回滚|降级|兜底|"
    r"兼容|乱序|顺序|重复|刷新|死循环|越权|噪音|成本|延迟|性能|内存|状态|多角色|"
    r"多模块|跨系统|取舍|trade.?off|脏数据|缺失|格式差异|长会话|回归|误差|安全|可靠性|耦合",
    re.I,
)
VALUE_SIGNAL_RE = re.compile(
    r"用户|业务|运营|客服|开发|维护|交付|迭代|定位|复用|人工|成本|效率|风险|体验|"
    r"可用|可维护|稳定|准确|可解释|权限|流程|页面|服务|系统|下游|回归",
    re.I,
)
PATH_EXT_RE = re.compile(
    r"\.(vue|svelte|jsx?|tsx?|mjs|cjs|py|go|rs|java|kt|swift|php|rb|cs|json|ya?ml|toml|md|mdx|html|css|scss|sql|sh)$",
    re.I,
)
PATH_PREFIX_RE = re.compile(
    r"^(src|app|apps|pages|views|components|widgets|routes|api|server|services|store|stores|lib|libs|"
    r"models|schemas|tests?|__tests__|docs?|references|scripts|config|configs|uni_modules|packages|tools|agents)/",
    re.I,
)


def load_json(path: Path) -> dict:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except Exception as exc:
        raise SystemExit(f"Cannot read JSON {path}: {exc}") from exc
    if not isinstance(data, dict):
        raise SystemExit("analysis JSON root must be an object")
    return data


def as_list(value: Any) -> list:
    if value is None:
        return []
    if isinstance(value, list):
        return value
    return [value]


def is_nonempty_text(value: Any) -> bool:
    return isinstance(value, str) and bool(value.strip())


def compact_text(value: Any) -> str:
    return re.sub(r"[\s，。；：、,.!?！？:;`'\"（）()\[\]{}]+", "", str(value or "")).lower()


def is_generic_text(value: Any) -> bool:
    text = str(value or "").strip()
    compact = compact_text(text)
    return bool(
        not compact
        or compact in {
            "负责模块开发",
            "参与项目开发提升效率",
            "有一定技术难度",
            "提升业务价值",
            "支持业务发展",
            "完成相关功能",
        }
        or GENERIC_TEXT_RE.fullmatch(text)
    )


def text_is_duplicate(left: Any, right: Any) -> bool:
    left_text = compact_text(left)
    right_text = compact_text(right)
    return bool(left_text and left_text == right_text)


def is_number(value: Any) -> bool:
    return isinstance(value, (int, float)) and not isinstance(value, bool)


def role_is_confirmed(value: Any) -> bool:
    text = str(value or "").strip().lower()
    if not text or any(marker in text for marker in ("未确认", "未知", "unknown", "默认使用保守", "待确认")):
        return False
    return any(marker in text for marker in ("已确认", "用户确认", "git", "owner", "主导", "独立负责", "模块负责人"))


def verified_metric_corpus(analysis: dict) -> str:
    strategy = analysis.get("metric_strategy")
    if not isinstance(strategy, dict):
        return ""
    values = []
    for item in as_list(strategy.get("verified_metrics")):
        if isinstance(item, dict):
            if item.get("usable_in_safe_bullet") is True:
                values.extend(str(value) for value in item.values() if value not in (None, ""))
        elif str(item).strip():
            values.append(str(item))
    return compact_text(" ".join(values))


def impact_metric_is_verified(bullet: str, metric_corpus: str) -> bool:
    numbers = re.findall(r"\d+(?:\.\d+)?\s*(?:%|ms|秒|分钟|小时|天|万|k|m|qps|rps)?", bullet, re.I)
    normalized = [compact_text(value) for value in numbers if compact_text(value)]
    return bool(normalized and metric_corpus and all(value in metric_corpus for value in normalized))


def add(findings: list[dict], level: str, path: str, message: str) -> None:
    findings.append({"level": level, "path": path, "message": message})


def contains_sensitive_text(text: str) -> bool:
    return bool(SENSITIVE_RE.search(text) or TOKEN_SECRET_RE.search(text))


def load_evidence_context(path: Path | None) -> dict:
    if path is None:
        return {}
    evidence = load_json(path)
    path_source = evidence.get("evidence_paths_index") or evidence.get("file_index")
    file_index = {str(item).replace("\\", "/").lstrip("./") for item in as_list(path_source)}
    for item in as_list(evidence.get("key_files")):
        if str(item).strip():
            file_index.add(str(item).replace("\\", "/").lstrip("./"))
    for doc in as_list(evidence.get("docs")):
        if isinstance(doc, dict) and str(doc.get("path", "")).strip():
            file_index.add(str(doc["path"]).replace("\\", "/").lstrip("./"))
    return {"repo": evidence.get("repo") or "", "file_index": file_index}


def normalize_evidence_path(value: Any, repo: str = "") -> str:
    text = str(value or "").strip().strip("`").strip()
    if not text:
        return ""
    text = text.replace("\\", "/")
    text = re.sub(r"^file://", "", text)
    text = re.sub(r"^['\"]|['\"]$", "", text)
    text = re.sub(r":\d+(?::\d+)?$", "", text)
    text = re.split(r"\s+(?:->|=>|\(|\[)", text, 1)[0].strip()
    text = text.lstrip("./")
    if repo:
        repo_norm = repo.replace("\\", "/").rstrip("/") + "/"
        if text.startswith(repo_norm):
            text = text[len(repo_norm):]
    return text.strip("/")


def is_path_like_evidence(value: Any) -> bool:
    text = normalize_evidence_path(value)
    if not text or text.startswith(("http://", "https://")):
        return False
    if " " in text and "/" not in text:
        return False
    return "/" in text or bool(PATH_EXT_RE.search(text)) or bool(PATH_PREFIX_RE.search(text))


def evidence_path_exists(value: Any, context: dict) -> bool:
    file_index = context.get("file_index") or set()
    repo = str(context.get("repo") or "")
    candidate = normalize_evidence_path(value, repo)
    if not candidate:
        return False
    if candidate in file_index:
        return True
    directory = candidate.rstrip("/") + "/"
    if any(path.startswith(directory) for path in file_index):
        return True
    return False


def validate_evidence_paths(evidence: list[Any], path: str, context: dict, findings: list[dict]) -> None:
    if not context:
        return
    for item_index, item in enumerate(evidence):
        if not is_path_like_evidence(item):
            continue
        if not evidence_path_exists(item, context):
            add(
                findings,
                "error",
                f"{path}.evidence[{item_index}]",
                "evidence path is not present in project_evidence.json file_index/key_files/docs",
            )


def validate_logic_chain(
    chain: Any,
    path: str,
    context: dict,
    findings: list[dict],
    safe_bullet: str = "",
    interview: dict | None = None,
    semantic_checks: bool = True,
) -> None:
    if not isinstance(chain, dict):
        add(findings, "warning", f"{path}.logic_chain", "logic_chain is recommended for quick output and required for standard/strict reports")
        return

    missing = [key for key in LOGIC_CHAIN_TEXT_KEYS if not is_nonempty_text(chain.get(key))]
    if missing:
        add(findings, "warning", f"{path}.logic_chain", "missing logic-chain fields: " + ", ".join(missing))

    if semantic_checks:
        for key in LOGIC_CHAIN_TEXT_KEYS:
            value = chain.get(key)
            if is_nonempty_text(value) and is_generic_text(value):
                add(findings, "warning", f"{path}.logic_chain.{key}", f"{key} is too generic to explain the evidence chain")

        if text_is_duplicate(chain.get("plain_summary"), safe_bullet):
            add(findings, "warning", f"{path}.logic_chain.plain_summary", "plain_summary should explain the highlight for a beginner, not repeat safe_bullet verbatim")
        if text_is_duplicate(chain.get("beginner_context"), chain.get("problem")):
            add(findings, "warning", f"{path}.logic_chain.problem", "problem should name the specific conflict or risk, not repeat beginner_context")

        trigger = str(chain.get("trigger") or "").strip()
        if trigger and ROLE_AS_TRIGGER_RE.search(trigger):
            add(findings, "warning", f"{path}.logic_chain.trigger", "trigger should describe a user/system event, request, job, or state transition instead of the candidate's responsibility")
        if interview and text_is_duplicate(trigger, interview.get("task")):
            add(findings, "warning", f"{path}.logic_chain.trigger", "trigger duplicates interview.task; describe what starts the runtime flow")

    steps = [step for step in as_list(chain.get("flow_steps")) if step]
    if len(steps) < 3:
        add(findings, "warning", f"{path}.logic_chain.flow_steps", "use at least 3 flow steps to show trigger, processing, and closure")

    step_explanations = []
    for step_index, step in enumerate(steps):
        step_path = f"{path}.logic_chain.flow_steps[{step_index}]"
        if isinstance(step, dict):
            if not is_nonempty_text(step.get("step")):
                add(findings, "warning", f"{step_path}.step", "flow step should name the stage")
            if not is_nonempty_text(step.get("explanation")):
                add(findings, "warning", f"{step_path}.explanation", "flow step should explain what happens")
            else:
                explanation = str(step.get("explanation")).strip()
                step_explanations.append(explanation)
                if semantic_checks and (len(compact_text(explanation)) < 12 or is_generic_text(explanation)):
                    add(findings, "warning", f"{step_path}.explanation", "flow step is too generic; name the state/data transition, mechanism, or returned output")
            step_evidence = [x for x in as_list(step.get("evidence") or step.get("evidence_paths")) if str(x).strip()]
            if not step_evidence:
                add(findings, "warning", f"{step_path}.evidence", "flow step should include evidence when possible")
            else:
                validate_evidence_paths(step_evidence, f"{step_path}", context, findings)
        elif not is_nonempty_text(step):
            add(findings, "warning", step_path, "flow step should be text or an object")

    compact_steps = [compact_text(value) for value in step_explanations if compact_text(value)]
    if semantic_checks and len(compact_steps) != len(set(compact_steps)):
        add(findings, "warning", f"{path}.logic_chain.flow_steps", "flow-step explanations should not repeat the same sentence")

    evidence_map = chain.get("evidence_map")
    if evidence_map is not None:
        for item_index, item in enumerate(as_list(evidence_map)):
            if isinstance(item, dict):
                mapped = [x for x in as_list(item.get("evidence") or item.get("evidence_paths")) if str(x).strip()]
                validate_evidence_paths(mapped, f"{path}.logic_chain.evidence_map[{item_index}]", context, findings)


def validate_highlight_score(item: dict, path: str, findings: list[dict]) -> None:
    score = item.get("score")
    if not is_number(score):
        add(findings, "warning", f"{path}.score", "score should be a numeric 0-20 highlight score")
        return
    if score < 0 or score > 20:
        add(findings, "error", f"{path}.score", "score must be between 0 and 20")

    breakdown = item.get("score_breakdown")
    if breakdown is None:
        return
    if not isinstance(breakdown, dict):
        add(findings, "error", f"{path}.score_breakdown", "score_breakdown must be an object")
        return
    missing = [key for key in HIGHLIGHT_SCORE_KEYS if key not in breakdown]
    if missing:
        add(findings, "warning", f"{path}.score_breakdown", "missing score dimensions: " + ", ".join(missing))
        return
    total = 0
    for key in HIGHLIGHT_SCORE_KEYS:
        value = breakdown.get(key)
        if not is_number(value) or not 0 <= value <= 3:
            add(findings, "error", f"{path}.score_breakdown.{key}", "highlight dimension must be between 0 and 3")
        else:
            total += value
    bonus = breakdown.get("ai_application_bonus", 0)
    if not is_number(bonus) or not 0 <= bonus <= 2:
        add(findings, "error", f"{path}.score_breakdown.ai_application_bonus", "AI application bonus must be between 0 and 2")
    else:
        total += bonus
    if is_number(score) and total != score:
        add(findings, "warning", f"{path}.score", f"score {score} does not equal score_breakdown total {total}")


def validate_highlight_semantics(item: dict, path: str, findings: list[dict]) -> None:
    risk = item.get("risk")
    readiness = item.get("readiness")
    if risk != "safe" or readiness not in {"direct", "rewrite"}:
        return

    title = str(item.get("title") or "").strip()
    mechanism = str(item.get("technical_mechanism") or "").strip()
    difficulty = str(item.get("technical_difficulty") or "").strip()
    value = str(item.get("business_value") or "").strip()
    bullet = str(item.get("safe_bullet") or "").strip()

    if title and not MECHANISM_SIGNAL_RE.search(title):
        add(findings, "warning", f"{path}.title", "title should expose a concrete technical mechanism before the business module")

    if len(compact_text(mechanism)) < 14 or is_generic_text(mechanism) or not MECHANISM_SIGNAL_RE.search(mechanism):
        add(findings, "warning", f"{path}.technical_mechanism", "technical_mechanism must name concrete code-level mechanisms or abstractions")
    if (
        len(compact_text(difficulty)) < 14
        or is_generic_text(difficulty)
        or difficulty.startswith(("能体现", "体现了", "展示了"))
        or not DIFFICULTY_SIGNAL_RE.search(difficulty)
    ):
        add(findings, "warning", f"{path}.technical_difficulty", "technical_difficulty must name a failure mode, edge case, state pressure, integration boundary, or tradeoff")
    if len(compact_text(value)) < 12 or is_generic_text(value) or not VALUE_SIGNAL_RE.search(value):
        add(findings, "warning", f"{path}.business_value", "business_value must name the protected user, workflow, engineering outcome, or business consequence")

    bullet_length = len(compact_text(bullet))
    if bullet_length < 28:
        add(findings, "warning", f"{path}.safe_bullet", "resume-ready safe bullet is too short to show mechanism, scope, and value")
    elif bullet_length > 115:
        add(findings, "warning", f"{path}.safe_bullet", "safe bullet is too long for a scannable resume; keep evidence detail in logic_chain")
    if is_generic_text(bullet) or not MECHANISM_SIGNAL_RE.search(bullet):
        add(findings, "warning", f"{path}.safe_bullet", "safe bullet is too generic; include a concrete mechanism and protected scenario")
    if VAGUE_IMPACT_RE.search(bullet) and not re.search(r"\d", bullet):
        add(findings, "warning", f"{path}.safe_bullet", "avoid unmeasured '提升/优化效率或体验'; use code-derived scope or a directly implied risk reduction")


def validate_highlight(
    item: Any,
    index: int,
    findings: list[dict],
    evidence_context: dict | None = None,
    confirmed_role: bool = False,
    verified_metrics: str = "",
) -> None:
    path = f"highlights[{index}]"
    if not isinstance(item, dict):
        add(findings, "error", path, "highlight must be an object")
        return

    for key in ("title", "category", "safe_bullet", "why"):
        if not is_nonempty_text(item.get(key)):
            add(findings, "error", f"{path}.{key}", f"{key} is required")

    for key in TECH_BUSINESS_KEYS:
        if not is_nonempty_text(item.get(key)):
            add(
                findings,
                "warning",
                f"{path}.{key}",
                f"{key} is required for technical-business balanced strict reports",
            )

    validate_highlight_score(item, path, findings)
    validate_highlight_semantics(item, path, findings)

    risk = item.get("risk")
    if risk not in RISK_VALUES:
        add(findings, "error", f"{path}.risk", f"risk must be one of {sorted(RISK_VALUES)}")

    readiness = item.get("readiness")
    if readiness not in READINESS_VALUES:
        add(findings, "error", f"{path}.readiness", f"readiness must be one of {sorted(READINESS_VALUES)}")

    evidence = [x for x in as_list(item.get("evidence")) if str(x).strip()]
    if not evidence:
        add(findings, "error", f"{path}.evidence", "at least one evidence path/count/signal is required")
    else:
        validate_evidence_paths(evidence, path, evidence_context or {}, findings)

    anchor = item.get("detail_anchor")
    if not is_nonempty_text(anchor):
        add(findings, "warning", f"{path}.detail_anchor", "detail_anchor is required for anchor-linked highlight details")
    elif not DETAIL_ANCHOR_RE.match(str(anchor).strip()):
        add(findings, "warning", f"{path}.detail_anchor", "detail_anchor should be lowercase URL-safe text, e.g. permission-access-control")

    interview = item.get("interview") or item.get("star")
    validate_logic_chain(
        item.get("logic_chain"),
        path,
        evidence_context or {},
        findings,
        str(item.get("safe_bullet") or ""),
        interview if isinstance(interview, dict) else None,
        item.get("risk") == "safe" and item.get("readiness") in {"direct", "rewrite"},
    )

    bullet = str(item.get("safe_bullet") or "")
    if contains_sensitive_text(bullet):
        add(findings, "error", f"{path}.safe_bullet", "safe_bullet appears to contain sensitive data or secrets")

    if risk == "safe" and UNCONFIRMED_METRIC_RE.search(bullet) and not impact_metric_is_verified(bullet, verified_metrics):
        add(findings, "warning", f"{path}.safe_bullet", "safe bullet contains a numeric improvement; ensure it is verified or move it to enhanced_bullet")

    if risk == "safe" and HIGH_OWNERSHIP_RE.search(bullet) and not confirmed_role:
        add(findings, "warning", f"{path}.safe_bullet", "high-ownership wording requires confirmed role evidence")

    if risk == "needs_confirmation" and not is_nonempty_text(item.get("enhanced_bullet")):
        add(findings, "warning", f"{path}.enhanced_bullet", "needs_confirmation highlights should include an enhanced_bullet")

    if risk in {"needs_confirmation", "risky"} and not [x for x in as_list(item.get("data_to_confirm")) if str(x).strip()]:
        add(findings, "warning", f"{path}.data_to_confirm", "confirmation-dependent highlights should list data_to_confirm")

    if not isinstance(interview, dict):
        add(findings, "error", f"{path}.interview", "interview must be a STAR object")
    else:
        missing = [key for key in STAR_KEYS if not is_nonempty_text(interview.get(key))]
        if missing:
            add(findings, "error", f"{path}.interview", "missing STAR fields: " + ", ".join(missing))


def scan_sensitive_values(value: Any, findings: list[dict], path: str = "$") -> None:
    if isinstance(value, dict):
        for key, child in value.items():
            if key in {"role_assumption", "disclosure_assumption", "data_to_confirm"}:
                continue
            scan_sensitive_values(child, findings, f"{path}.{key}")
    elif isinstance(value, list):
        for index, child in enumerate(value):
            scan_sensitive_values(child, findings, f"{path}[{index}]")
    elif isinstance(value, str) and contains_sensitive_text(value):
        add(findings, "warning", path, "text may contain secrets, credentials, or disclosure-sensitive details")


def validate_project_score(score: Any, findings: list[dict]) -> None:
    if score in (None, {}):
        return
    if not isinstance(score, dict):
        add(findings, "error", "project_score", "project_score must be an object")
        return

    safe_score = score.get("evidence_safe_score")
    potential_score = score.get("potential_score")
    for key, value in (("evidence_safe_score", safe_score), ("potential_score", potential_score)):
        if not is_number(value) or not 0 <= value <= 100:
            add(findings, "error", f"project_score.{key}", f"{key} must be between 0 and 100")
    if is_number(safe_score) and is_number(potential_score) and potential_score < safe_score:
        add(findings, "error", "project_score.potential_score", "potential_score cannot be lower than evidence_safe_score")

    breakdown = score.get("score_breakdown_100")
    if not isinstance(breakdown, dict):
        add(findings, "warning", "project_score.score_breakdown_100", "project score should include the six-dimension 100-point breakdown")
    else:
        total = 0
        for key, limit in PROJECT_SCORE_LIMITS.items():
            value = breakdown.get(key)
            if not is_number(value) or not 0 <= value <= limit:
                add(findings, "error", f"project_score.score_breakdown_100.{key}", f"{key} must be between 0 and {limit}")
            else:
                total += value
        if is_number(safe_score) and total != safe_score:
            add(findings, "warning", "project_score.evidence_safe_score", f"evidence_safe_score {safe_score} does not equal breakdown total {total}")

    if is_number(safe_score) and safe_score < 90 and is_number(potential_score) and potential_score >= 90:
        if not is_nonempty_text(score.get("score_ceiling_reason")):
            add(findings, "warning", "project_score.score_ceiling_reason", "explain why evidence-safe score remains below 90")


def validate_safe_bullet_projection(
    analysis: dict,
    highlights: list[dict],
    findings: list[dict],
    confirmed_role: bool,
    verified_metrics: str,
) -> None:
    configured = [str(value).strip() for value in as_list(analysis.get("safe_bullets")) if str(value).strip()]
    if not configured:
        return
    if len(configured) != len(set(configured)):
        add(findings, "warning", "safe_bullets", "safe_bullets contains duplicates")
    safe_sources = {
        str(item.get("safe_bullet") or "").strip()
        for item in highlights
        if isinstance(item, dict) and item.get("risk") == "safe" and str(item.get("safe_bullet") or "").strip()
    }
    for index, bullet in enumerate(configured):
        if bullet not in safe_sources:
            add(
                findings,
                "error",
                f"safe_bullets[{index}]",
                "top-level safe bullet must exactly match a risk=safe highlight; unmatched copy cannot enter the direct-paste section",
            )
        if HIGH_OWNERSHIP_RE.search(bullet) and not confirmed_role:
            add(findings, "warning", f"safe_bullets[{index}]", "high-ownership wording must be validated on the source highlight")
        if UNCONFIRMED_METRIC_RE.search(bullet) and not impact_metric_is_verified(bullet, verified_metrics):
            add(findings, "warning", f"safe_bullets[{index}]", "numeric improvement must be verified on the source highlight")


def validate_interview_stories(stories: Any, safe_highlights: list[dict], findings: list[dict]) -> None:
    story_list = [item for item in as_list(stories) if item]
    expected = min(3, len(safe_highlights))
    if expected and len(story_list) < expected:
        add(findings, "warning", "interview_stories", f"include at least {expected} interview deep dives for the strongest safe highlights")
    safe_anchors = {
        str(item.get("detail_anchor") or "").strip()
        for item in safe_highlights
        if str(item.get("detail_anchor") or "").strip()
    }
    for index, story in enumerate(story_list):
        path = f"interview_stories[{index}]"
        if not isinstance(story, dict):
            add(findings, "warning", path, "interview story should be a structured deep-dive object")
            continue
        missing = [key for key in INTERVIEW_STORY_KEYS if not is_nonempty_text(story.get(key))]
        if missing:
            add(findings, "warning", path, "missing interview deep-dive fields: " + ", ".join(missing))
        anchor = str(story.get("detail_anchor") or "").strip()
        if anchor and anchor not in safe_anchors:
            add(findings, "warning", f"{path}.detail_anchor", "interview story should link to a risk=safe highlight anchor")
        questions = [str(value).strip() for value in as_list(story.get("follow_up_questions")) if str(value).strip()]
        if len(questions) < 2:
            add(findings, "warning", f"{path}.follow_up_questions", "include at least two likely interviewer follow-up questions")
        for key in ("hardest_question", "answer_outline", "alternatives", "failure_boundary", "verification"):
            value = story.get(key)
            if is_nonempty_text(value) and (len(compact_text(value)) < 12 or is_generic_text(value)):
                add(findings, "warning", f"{path}.{key}", f"{key} is too generic for interview preparation")


def validate_analysis_payload(analysis: dict, evidence_context: dict | None = None) -> list[dict]:
    findings: list[dict] = []
    confirmed_role = role_is_confirmed(analysis.get("role_assumption"))
    verified_metrics = verified_metric_corpus(analysis)

    for key in ("project_name", "summary", "target_role", "readiness", "role_assumption", "disclosure_assumption"):
        if not is_nonempty_text(analysis.get(key)):
            add(findings, "error", key, f"{key} is required")

    keywords = [x for x in as_list(analysis.get("keywords")) if str(x).strip()]
    if not keywords:
        add(findings, "warning", "keywords", "keywords should include role-relevant technologies or domain terms")

    facts = analysis.get("facts")
    if not isinstance(facts, (list, dict)) or not facts:
        add(findings, "error", "facts", "facts must include business/module/API/data-flow evidence")

    validate_project_score(analysis.get("project_score"), findings)

    if is_nonempty_text(analysis.get("prompt_pack")):
        add(findings, "warning", "prompt_pack", "custom prompt_pack is not trusted in strict reports; the renderer derives it from validated highlights")

    highlights = analysis.get("highlights")
    if not isinstance(highlights, list) or not highlights:
        add(findings, "error", "highlights", "at least one highlight is required")
    else:
        anchors: dict[str, int] = {}
        for index, item in enumerate(highlights):
            validate_highlight(item, index, findings, evidence_context, confirmed_role, verified_metrics)
            if isinstance(item, dict) and is_nonempty_text(item.get("detail_anchor")):
                anchor = str(item["detail_anchor"]).strip()
                if anchor in anchors:
                    add(findings, "warning", f"highlights[{index}].detail_anchor", f"duplicate detail_anchor also used by highlights[{anchors[anchor]}]")
                else:
                    anchors[anchor] = index

    safe_highlights = [
        item for item in highlights or []
        if isinstance(item, dict) and item.get("risk") == "safe" and is_nonempty_text(item.get("safe_bullet"))
    ]
    if highlights and not safe_highlights:
        add(findings, "warning", "highlights", "no safe highlight found; final report may have no directly usable resume bullet")

    validate_safe_bullet_projection(analysis, highlights or [], findings, confirmed_role, verified_metrics)
    validate_interview_stories(analysis.get("interview_stories"), safe_highlights, findings)

    scan_sensitive_values(analysis, findings)

    return findings


def format_findings(findings: list[dict]) -> str:
    if not findings:
        return "analysis validation passed"
    lines = []
    for item in findings:
        lines.append(f"[{item['level'].upper()}] {item['path']}: {item['message']}")
    return "\n".join(lines)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--analysis", required=True, help="project_resume_analysis.json")
    parser.add_argument("--evidence", help="Optional project_evidence.json for strict evidence path checks")
    parser.add_argument("--strict", action="store_true", help="Exit non-zero on warnings as well as errors")
    args = parser.parse_args()

    analysis = load_json(Path(args.analysis).expanduser().resolve())
    evidence_context = load_evidence_context(Path(args.evidence).expanduser().resolve()) if args.evidence else {}
    findings = validate_analysis_payload(analysis, evidence_context)
    print(format_findings(findings))
    has_error = any(item["level"] == "error" for item in findings)
    has_warning = any(item["level"] == "warning" for item in findings)
    if has_error or (args.strict and has_warning):
        raise SystemExit(1)


if __name__ == "__main__":
    main()
