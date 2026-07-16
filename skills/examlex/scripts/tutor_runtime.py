"""Route short tutor requests and hand private prompts to a trusted provider."""

from __future__ import annotations

import hashlib
import json
import os
import re
import stat
import tempfile
from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Literal, Protocol

from .tutor_prompts import (
    ROLE_IDS,
    PromptAssetError,
    audit_private_prompt_directory,
    compose_tutor_pipeline,
)


PRIVATE_PROMPT_ENV = "EXAMLEX_PRIVATE_PROMPT_DIR"
PROMPT_CONFIG_FILENAME = "prompt-config.json"
MAX_PROMPT_CONFIG_BYTES = 16 * 1024
MAX_REQUEST_BYTES = 32 * 1024
MAX_PROVIDER_RESPONSE_BYTES = 256 * 1024
MAX_CLARIFICATION_QUESTIONS = 2
CLARIFICATION_FIELDS = (
    "exam",
    "study_context",
    "material",
    "target",
    "reading_goal",
    "task",
    "register",
    "scenario",
    "level",
    "culture_topic",
    "region",
)

ROLE_ALIASES = {
    "learning-planner": "study-planner",
    "vocabulary-builder": "vocabulary-expander",
    "reading-navigator": "reading-navigator",
    "structure-planner": "structure-planner",
    "grammar-corrector": "grammar-corrector",
    "polish-wizard": "polishing-editor",
    "scenario-dialog": "situational-dialogue",
    "culture-guide": "culture-guide",
}

_ROLE_KEYWORDS = {
    "study-planner": (
        "学习计划", "学习规划", "备考计划", "复习计划", "时间安排",
        "study plan", "learning plan", "schedule", "备考", "规划",
    ),
    "vocabulary-expander": (
        "词汇", "单词", "搭配", "近义词", "反义词", "词根", "短语",
        "vocabulary", "word", "collocation", "synonym", "phrase", "spelling",
    ),
    "reading-navigator": (
        "阅读理解", "长难句", "主旨", "推断题", "定位题", "文章理解",
        "reading", "passage", "inference", "main idea", "scan", "skim",
    ),
    "structure-planner": (
        "文章结构", "写作结构", "提纲", "论点", "主题句", "段落结构",
        "outline", "thesis", "structure", "topic sentence", "argument",
    ),
    "grammar-corrector": (
        "语法", "纠错", "改错", "冠词", "时态", "介词", "主谓一致",
        "grammar", "correct my", "grammatical", "tense", "article", "preposition",
    ),
    "polishing-editor": (
        "润色", "改写", "地道表达", "正式表达", "简洁", "语气",
        "polish", "rewrite", "refine", "natural", "formal", "concise", "tone",
    ),
    "situational-dialogue": (
        "情景对话", "角色扮演", "口语练习", "面试对话", "谈判", "投诉对话",
        "role play", "role-play", "dialogue", "conversation", "interview", "speaking",
    ),
    "culture-guide": (
        "文化差异", "俚语", "礼仪", "潜台词", "讽刺", "文化背景",
        "culture", "slang", "etiquette", "sarcasm", "implicature", "idiom",
    ),
}

_PIPELINE_PRIORITY = {
    "study-planner": 0,
    "vocabulary-expander": 1,
    "reading-navigator": 2,
    "structure-planner": 3,
    "grammar-corrector": 4,
    "polishing-editor": 5,
    "situational-dialogue": 6,
    "culture-guide": 7,
}


def _compile_keyword_matcher(keyword: str) -> tuple[re.Pattern[str] | str, int]:
    """Precompute a keyword's matcher and score weight once at module load.

    ASCII keywords become a compiled word-boundary regex (spaces match runs of
    whitespace); non-ASCII keywords use a plain substring test. The weight
    matches the previous inline rule: multi-word or >=4-char keywords score 2.
    """
    lowered = keyword.lower()
    weight = 2 if (" " in keyword or len(keyword) >= 4) else 1
    if lowered.isascii():
        expression = r"\b" + re.escape(lowered).replace(r"\ ", r"\s+") + r"\b"
        return (re.compile(expression, re.IGNORECASE), weight)
    return (lowered, weight)


# Build every role's (matcher, weight) pairs once instead of re-escaping,
# re-lowering, and recomputing weights on every route_tutor_roles call (a
# per-turn hot path over ~96 keywords).
_ROLE_KEYWORD_MATCHERS: dict[str, tuple[tuple[re.Pattern[str] | str, int], ...]] = {
    role_id: tuple(_compile_keyword_matcher(keyword) for keyword in keywords)
    for role_id, keywords in _ROLE_KEYWORDS.items()
}

_EXAM_RE = re.compile(
    r"(?i)\b(?:cet[- ]?[46]|tem[- ]?[48]|postgraduate english)\b|"
    r"四级|六级|专四|专八|考研英语"
)
_TIME_RE = re.compile(
    r"(?i)(?:\d+(?:\.\d+)?\s*(?:分钟|小时|天|周|月|minute|hour|day|week|month)s?"
    r"|每天|每周|截止|考试日期|deadline)"
)
_LEVEL_RE = re.compile(
    r"(?i)(?:基础|水平|当前分数|目标分数|零基础|薄弱|score|band|beginner|"
    r"intermediate|advanced|level)"
)
_REGISTER_RE = re.compile(
    r"(?i)(?:受众|语气|正式|学术|商务|邮件|作文|演讲|audience|tone|formal|"
    r"academic|business|email|essay|speech)"
)
_REGION_RE = re.compile(
    r"(?i)(?:美国|英国|加拿大|澳大利亚|新西兰|地区|场合|美式|英式|"
    r"american|british|canadian|australian|region|setting)"
)
_READING_GOAL_RE = re.compile(
    r"(?i)(?:速度|主旨|推断|定位|长难句|同义改写|speed|main idea|inference|"
    r"locating|syntax|paraphrase)"
)
_ENGLISH_TOKEN_RE = re.compile(r"\b[A-Za-z][A-Za-z'-]*\b")
_CHINESE_RE = re.compile(r"[\u3400-\u9fff]")


class TutorRuntimeError(RuntimeError):
    """Raised for provider, response, or privacy-boundary failures."""


class TutorProvider(Protocol):
    """Trusted host boundary; private prompts never pass through the CLI."""

    privacy_boundary: Literal["local", "remote"]

    def generate(
        self,
        *,
        system_prompt: str,
        user_message: str,
        metadata: Mapping[str, Any],
    ) -> str:
        """Return one learner-facing answer without exposing the system prompt."""


@dataclass(frozen=True, slots=True)
class TutorTurnDecision:
    """Public-safe routing and clarification decision for one learner turn."""

    role_ids: tuple[str, ...]
    clarification_questions: tuple[str, ...]
    clarification_fields: tuple[str, ...]
    recognized_context_fields: tuple[str, ...]
    _user_request: str = field(repr=False)
    _structured_context: Mapping[str, Any] = field(repr=False)

    @property
    def user_request(self) -> str:
        return self._user_request

    @property
    def structured_context(self) -> Mapping[str, Any]:
        return self._structured_context

    def safe_manifest(self) -> dict[str, Any]:
        """Return routing metadata without request text, context values, or local paths."""
        return {
            "schema_version": "1.0",
            "primary_role": self.role_ids[0],
            "role_sequence": list(self.role_ids),
            "recognized_context_fields": list(self.recognized_context_fields),
            "clarification_questions": list(self.clarification_questions),
            "clarification_fields": list(self.clarification_fields),
            "clarification_question_count": len(self.clarification_questions),
            "ready": not self.clarification_questions,
            "provider_required": not self.clarification_questions,
            "private_prompt_loaded": False,
        }


@dataclass(frozen=True, slots=True)
class TutorTurnResult:
    """Learner-facing answer plus safe runtime metadata."""

    role_ids: tuple[str, ...]
    mode: Literal["clarification", "full-local"]
    provider_called: bool
    prompt_sha256: str | None
    _answer: str = field(repr=False)

    @property
    def answer(self) -> str:
        return self._answer

    def safe_manifest(self) -> dict[str, Any]:
        return {
            "schema_version": "1.0",
            "mode": self.mode,
            "primary_role": self.role_ids[0],
            "role_sequence": list(self.role_ids),
            "provider_called": self.provider_called,
            "private_prompt_loaded": self.mode == "full-local",
            "prompt_sha256": self.prompt_sha256,
        }


def _safe_home() -> Path:
    try:
        return Path.home()
    except (KeyError, RuntimeError):
        expanded = os.path.expanduser("~")
        return Path(expanded if expanded and expanded != "~" else os.getcwd())


def default_prompt_config_path() -> Path:
    return _safe_home() / ".examlex" / PROMPT_CONFIG_FILENAME


def _is_link_or_reparse(path: Path) -> bool:
    metadata = path.lstat()
    reparse_flag = getattr(stat, "FILE_ATTRIBUTE_REPARSE_POINT", 0)
    attributes = getattr(metadata, "st_file_attributes", 0)
    return path.is_symlink() or bool(reparse_flag and attributes & reparse_flag)


def _read_prompt_config(path: Path) -> dict[str, Any]:
    try:
        metadata = path.lstat()
    except FileNotFoundError:
        return {}
    except OSError as exc:
        raise PromptAssetError("Cannot safely inspect prompt configuration") from exc
    try:
        if _is_link_or_reparse(path):
            raise PromptAssetError("Prompt configuration must not be a link")
        if not stat.S_ISREG(metadata.st_mode):
            raise PromptAssetError("Prompt configuration must be a regular file")
        if metadata.st_size > MAX_PROMPT_CONFIG_BYTES:
            raise PromptAssetError("Prompt configuration is too large")
        document = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise PromptAssetError("Prompt configuration is invalid JSON") from exc
    except UnicodeDecodeError as exc:
        raise PromptAssetError("Prompt configuration must be UTF-8") from exc
    except OSError as exc:
        raise PromptAssetError("Cannot safely read prompt configuration") from exc
    if not isinstance(document, dict) or document.get("schema_version") != "1.0":
        raise PromptAssetError("Prompt configuration schema is invalid")
    return document


def _forbidden_prompt_roots() -> tuple[Path, ...]:
    module_path = Path(__file__).resolve()
    roots = {module_path.parents[1]}
    for parent in module_path.parents:
        if (parent / "pyproject.toml").is_file() or (parent / ".git").exists():
            roots.add(parent)
            break
    return tuple(roots)


def _reject_internal_prompt_root(root: Path) -> None:
    resolved = root.resolve()
    for forbidden in _forbidden_prompt_roots():
        forbidden_resolved = forbidden.resolve()
        if resolved == forbidden_resolved or forbidden_resolved in resolved.parents:
            raise PromptAssetError("Private prompt directory must stay outside ExamLex")


def resolve_private_prompt_directory(
    explicit: str | Path | None = None,
    *,
    config_path: str | Path | None = None,
) -> Path:
    """Resolve explicit, environment, then saved full-local prompt configuration."""
    candidate: str | Path | None = explicit
    if candidate is None:
        candidate = os.environ.get(PRIVATE_PROMPT_ENV) or None
    if candidate is None:
        config = _read_prompt_config(
            Path(config_path) if config_path is not None else default_prompt_config_path()
        )
        candidate = config.get("private_prompt_dir")
    if not isinstance(candidate, (str, Path)) or not str(candidate).strip():
        raise PromptAssetError(
            "Private prompt directory is not configured; run prompt-check --save"
        )
    root = Path(candidate).expanduser()
    if not root.is_dir():
        raise PromptAssetError("Configured private prompt directory is unavailable")
    try:
        if _is_link_or_reparse(root):
            raise PromptAssetError("Private prompt directory must not be a link")
    except OSError as exc:
        raise PromptAssetError("Cannot safely inspect private prompt directory") from exc
    _reject_internal_prompt_root(root)
    return root.resolve()


def save_private_prompt_directory(
    prompt_dir: str | Path,
    *,
    config_path: str | Path | None = None,
) -> None:
    """Validate all eight prompts and atomically save their external directory."""
    candidate = Path(prompt_dir).expanduser()
    if not candidate.is_dir():
        raise PromptAssetError("Private prompt directory is unavailable")
    try:
        if _is_link_or_reparse(candidate):
            raise PromptAssetError("Private prompt directory must not be a link")
    except OSError as exc:
        raise PromptAssetError("Cannot safely inspect private prompt directory") from exc
    root = candidate.resolve()
    _reject_internal_prompt_root(root)
    audit_private_prompt_directory(root)
    target = Path(config_path) if config_path is not None else default_prompt_config_path()
    parent = target.parent
    parent.mkdir(parents=True, exist_ok=True)
    try:
        target_present = target.exists() or target.is_symlink()
        if _is_link_or_reparse(parent) or (
            target_present and _is_link_or_reparse(target)
        ):
            raise PromptAssetError("Prompt configuration path must not be a link")
    except OSError as exc:
        raise PromptAssetError("Cannot safely inspect prompt configuration path") from exc
    payload = json.dumps(
        {"schema_version": "1.0", "private_prompt_dir": str(root)},
        ensure_ascii=False,
        indent=2,
    ) + "\n"
    temporary: Path | None = None
    try:
        with tempfile.NamedTemporaryFile(
            mode="w",
            encoding="utf-8",
            dir=parent,
            prefix=target.name + ".",
            suffix=".tmp",
            delete=False,
        ) as stream:
            temporary = Path(stream.name)
            os.chmod(temporary, 0o600)
            stream.write(payload)
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary, target)
        temporary = None
    except OSError as exc:
        raise PromptAssetError("Cannot safely save prompt configuration") from exc
    finally:
        if temporary is not None:
            temporary.unlink(missing_ok=True)


def _matcher_present(normalized: str, matcher: re.Pattern[str] | str) -> bool:
    if isinstance(matcher, str):
        return matcher in normalized
    return matcher.search(normalized) is not None


def _normalize_explicit_role(role_id: str) -> str:
    normalized = role_id.strip().lower()
    normalized = ROLE_ALIASES.get(normalized, normalized)
    if normalized not in ROLE_IDS:
        raise PromptAssetError(f"Unknown tutor role: {role_id}")
    return normalized


def _validate_request(request: str) -> str:
    if not isinstance(request, str) or not request.strip():
        raise PromptAssetError("Tutor request must not be empty")
    normalized = request.strip().replace("\r\n", "\n").replace("\r", "\n")
    if len(normalized.encode("utf-8")) > MAX_REQUEST_BYTES:
        raise PromptAssetError(f"Tutor request exceeds {MAX_REQUEST_BYTES} bytes")
    if any(ord(character) < 32 and character not in "\n\t" for character in normalized):
        raise PromptAssetError("Tutor request contains unsafe control characters")
    return normalized


def route_tutor_roles(request: str, explicit_role: str | None = None) -> tuple[str, ...]:
    """Select one to three roles from a short Chinese or English request."""
    normalized = _validate_request(request).lower()
    if explicit_role and explicit_role.lower() != "auto":
        return (_normalize_explicit_role(explicit_role),)
    scored: list[tuple[str, int]] = []
    for role_id, matchers in _ROLE_KEYWORD_MATCHERS.items():
        score = sum(
            weight for matcher, weight in matchers if _matcher_present(normalized, matcher)
        )
        if score:
            scored.append((role_id, score))
    if not scored:
        return ("study-planner",)
    scored.sort(key=lambda item: (-item[1], _PIPELINE_PRIORITY[item[0]]))
    top_score = scored[0][1]
    selected = [
        role_id
        for role_id, score in scored
        if score >= max(2, (top_score + 1) // 2)
    ][:3]
    selected.sort(key=lambda selected_role: _PIPELINE_PRIORITY[selected_role])
    return tuple(selected)


def _has_context_value(context: Mapping[str, Any], names: set[str]) -> bool:
    for key, value in context.items():
        normalized_key = str(key).lower().replace("-", "_")
        if normalized_key in names and value not in (None, "", [], {}):
            return True
    return False


def _has_substantive_english(request: str) -> bool:
    excluded = {
        "cet", "tem", "english", "grammar", "reading", "writing", "vocabulary",
        "polish", "rewrite", "please", "help", "practice", "plan", "study",
    }
    tokens = [
        token.lower()
        for token in _ENGLISH_TOKEN_RE.findall(request)
        if token.lower() not in excluded
    ]
    return len(tokens) >= 3


def _known_signals(request: str, context: Mapping[str, Any]) -> dict[str, bool]:
    has_material = _has_context_value(
        context,
        {"learner_text", "source_text", "passage", "draft", "task_text", "prompt"},
    ) or _has_substantive_english(request)
    scenario_specific = re.search(
        r"(?i)(?:面试|谈判|投诉|餐厅|机场|会议|演讲|医生|networking|restaurant|"
        r"airport|meeting|doctor|negotiation|complaint)",
        request,
    ) is not None
    culture_specific = re.search(
        r"(?i)(?:俚语|礼仪|潜台词|讽刺|手势|节日|称呼|slang|etiquette|sarcasm|"
        r"gesture|holiday|idiom)",
        request,
    ) is not None
    has_level = bool(_LEVEL_RE.search(request)) or _has_context_value(
        context, {"level", "foundation_level", "current_score"}
    )
    has_schedule = bool(_TIME_RE.search(request)) or _has_context_value(
        context, {"deadline", "time_budget", "available_time"}
    )
    return {
        "exam": bool(_EXAM_RE.search(request))
        or _has_context_value(context, {"exam", "exam_type", "target_exam"}),
        "study_context": has_level and has_schedule,
        "level": has_level,
        "material": has_material,
        "target": has_material
        or _has_context_value(context, {"target_words", "words", "topic"}),
        "task": has_material
        or _has_context_value(context, {"topic", "task", "task_prompt", "writing_prompt"}),
        "register": bool(_REGISTER_RE.search(request))
        or _has_context_value(context, {"audience", "register", "tone", "genre"}),
        "reading_goal": bool(_READING_GOAL_RE.search(request))
        or _has_context_value(context, {"reading_goal", "focus"}),
        "scenario": scenario_specific
        or _has_context_value(context, {"scenario", "setting", "roles"}),
        "culture_topic": culture_specific
        or _has_context_value(context, {"expression", "culture_topic", "topic"}),
        "region": bool(_REGION_RE.search(request))
        or _has_context_value(context, {"region", "locale", "setting"}),
    }


def _question_catalog(chinese: bool) -> dict[str, str]:
    if chinese:
        return {
            "exam": "你的目标考试、目标分数和预计考试日期分别是什么？",
            "study_context": "你目前的大致水平，以及每天或每周可稳定投入多少时间？",
            "material": "请贴出需要处理的原文、题目或你的当前答案。",
            "target": "本轮希望掌握哪些单词、主题或原文中的词汇？",
            "reading_goal": "本轮最想解决速度、主旨、推断、定位还是长难句中的哪一项？",
            "task": "请提供题目、写作任务或希望表达的核心观点。",
            "register": "目标受众、体裁、字数和期望语气是什么？",
            "scenario": "希望练习什么场景，你和对方分别扮演什么角色？",
            "level": "你的英语水平大致如何，希望对话难度达到什么程度？",
            "culture_topic": "想了解哪个具体表达、行为、事件或文化现象？",
            "region": "关注哪个英语地区、年代和正式程度？",
        }
    return {
        "exam": "What exam, target score, and test date are you preparing for?",
        "study_context": "What is your current level and sustainable study time?",
        "material": "Please provide the source text, question, or your current answer.",
        "target": "Which words, topic, or source passage should we work on?",
        "reading_goal": "Should we prioritize speed, main ideas, inference, evidence, or syntax?",
        "task": "Please provide the task, topic, or central idea you want to express.",
        "register": "What audience, genre, length, and tone should the answer target?",
        "scenario": "Which scenario should we practise, and what roles should we take?",
        "level": "What is your current level and desired dialogue difficulty?",
        "culture_topic": "Which expression, behavior, event, or reference should we examine?",
        "region": "Which English-speaking region, period, and formality level matter?",
    }


def _requirements_for_role(role_id: str, signals: Mapping[str, bool]) -> tuple[str, ...]:
    if role_id == "study-planner":
        return ("exam", "study_context")
    if role_id == "vocabulary-expander":
        return ("target",)
    if role_id == "reading-navigator":
        return ("material", "reading_goal") if signals["material"] else ("material",)
    if role_id == "structure-planner":
        return ("task", "register")
    if role_id == "grammar-corrector":
        return ("material",)
    if role_id == "polishing-editor":
        return ("material", "register")
    if role_id == "situational-dialogue":
        return ("scenario", "level")
    return ("culture_topic", "region")


def prepare_tutor_turn(
    request: str,
    *,
    role_id: str | None = None,
    context: Mapping[str, Any] | None = None,
    asked_fields: Sequence[str] = (),
) -> TutorTurnDecision:
    """Route one turn and ask no more than two material questions together."""
    normalized_request = _validate_request(request)
    safe_context = dict(context or {})
    selected_roles = route_tutor_roles(normalized_request, role_id)
    signals = _known_signals(normalized_request, safe_context)
    already_asked = {str(field_name) for field_name in asked_fields}
    catalog = _question_catalog(_CHINESE_RE.search(normalized_request) is not None)
    question_fields: list[str] = []
    for selected_role in selected_roles:
        for required_field in _requirements_for_role(selected_role, signals):
            if (
                not signals[required_field]
                and required_field not in already_asked
                and required_field not in question_fields
            ):
                question_fields.append(required_field)
            if len(question_fields) >= MAX_CLARIFICATION_QUESTIONS:
                break
        if len(question_fields) >= MAX_CLARIFICATION_QUESTIONS:
            break
    questions = tuple(catalog[field_name] for field_name in question_fields)
    return TutorTurnDecision(
        role_ids=selected_roles,
        clarification_questions=questions,
        clarification_fields=tuple(question_fields),
        recognized_context_fields=tuple(sorted(str(key) for key in safe_context)),
        _user_request=normalized_request,
        _structured_context=safe_context,
    )


def _clarification_answer(questions: Sequence[str]) -> str:
    return "\n".join(f"{index}. {question}" for index, question in enumerate(questions, 1))


def _assert_safe_provider_answer(answer: str, system_prompt: str) -> str:
    if not isinstance(answer, str) or not answer.strip():
        raise TutorRuntimeError("Tutor provider returned no usable answer")
    normalized = answer.strip()
    if len(normalized.encode("utf-8")) > MAX_PROVIDER_RESPONSE_BYTES:
        raise TutorRuntimeError("Tutor provider response is too large")
    forbidden_markers = (
        "ExamLex private tutor runtime",
        "ExamLex operational overlay",
        "PRIVATE_PROMPT_PLACEHOLDER",
    )
    if any(marker in normalized for marker in forbidden_markers):
        raise TutorRuntimeError("Tutor provider response failed the prompt-leak check")
    if system_prompt in normalized:
        raise TutorRuntimeError("Tutor provider response failed the prompt-leak check")
    prompt_lines = {
        line.strip()
        for line in system_prompt.splitlines()
        if len(line.strip()) >= 80
    }
    if any(line in normalized for line in prompt_lines):
        raise TutorRuntimeError("Tutor provider response failed the prompt-leak check")
    collapsed_prompt = re.sub(r"\s+", " ", system_prompt).strip()
    collapsed_answer = re.sub(r"\s+", " ", normalized).strip()
    chunk_size = 96
    chunk_step = 24
    prompt_chunks = {
        collapsed_prompt[index : index + chunk_size]
        for index in range(0, max(0, len(collapsed_prompt) - chunk_size + 1), chunk_step)
    }
    if any(chunk in collapsed_answer for chunk in prompt_chunks):
        raise TutorRuntimeError("Tutor provider response failed the prompt-leak check")
    return normalized


def run_tutor_turn(
    provider: TutorProvider,
    request: str,
    *,
    private_prompt_dir: str | Path | None = None,
    role_id: str | None = None,
    context: Mapping[str, Any] | None = None,
    asked_fields: Sequence[str] = (),
    config_path: str | Path | None = None,
    allow_remote_provider: bool = False,
) -> TutorTurnResult:
    """Run a private turn without exposing prompts through files, stdout, or metadata."""
    decision = prepare_tutor_turn(
        request,
        role_id=role_id,
        context=context,
        asked_fields=asked_fields,
    )
    if decision.clarification_questions:
        return TutorTurnResult(
            role_ids=decision.role_ids,
            mode="clarification",
            provider_called=False,
            prompt_sha256=None,
            _answer=_clarification_answer(decision.clarification_questions),
        )
    boundary = getattr(provider, "privacy_boundary", None)
    if boundary not in {"local", "remote"}:
        raise TutorRuntimeError("Tutor provider must declare its privacy boundary")
    if boundary == "remote" and not allow_remote_provider:
        raise TutorRuntimeError("Remote tutor provider requires explicit authorization")

    prompt_root = resolve_private_prompt_directory(
        private_prompt_dir,
        config_path=config_path,
    )
    audit_private_prompt_directory(prompt_root)
    runtime_context = {
        **decision.structured_context,
        "selected_role_sequence": list(decision.role_ids),
        "interaction_policy": {
            "maximum_clarification_questions": MAX_CLARIFICATION_QUESTIONS,
            "ask_questions_together": True,
            "do_not_repeat_known_questions": True,
            "proceed_with_stated_assumptions_if_declined": True,
            "give_immediate_partial_value_when_safe": True,
        },
    }
    system_prompt = compose_tutor_pipeline(
        prompt_root,
        decision.role_ids,
        context=runtime_context,
    )
    prompt_digest = hashlib.sha256(system_prompt.encode("utf-8")).hexdigest()
    provider_metadata = {
        **decision.safe_manifest(),
        "mode": "full-local",
        "private_prompt_loaded": True,
        "prompt_sha256": prompt_digest,
    }
    try:
        answer = provider.generate(
            system_prompt=system_prompt,
            user_message=decision.user_request,
            metadata=provider_metadata,
        )
    except Exception:
        raise TutorRuntimeError("Tutor provider failed without returning an answer") from None
    safe_answer = _assert_safe_provider_answer(answer, system_prompt)
    return TutorTurnResult(
        role_ids=decision.role_ids,
        mode="full-local",
        provider_called=True,
        prompt_sha256=prompt_digest,
        _answer=safe_answer,
    )
