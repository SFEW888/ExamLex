"""Local-first ExamLex web workspace.

The web adapter intentionally uses only the Python standard library.  It keeps
the public content bundle read-only and stores learner state in a separate
JSON file, with uploaded documents quarantined until a future ingest step.
"""

from __future__ import annotations

import argparse
import calendar
import hashlib
import io
import json
import mimetypes
import os
import re
import secrets
import threading
import uuid
import zipfile
from datetime import date, datetime, timedelta, timezone
from email.parser import BytesParser
from email.policy import default
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any
from urllib.parse import parse_qs, unquote, urlparse

from .common import ABILITY_TREE, ALL_EXAMS, ERROR_TAG_TO_ABILITY, atomic_save_data, load_data, validate_error_tags
from .analyze_trends import analyze_trends
from .generate_daily_plan import generate_daily_plan
from .update_ability_profile import update_ability_profile
from .validate_profile import validate_profile
from .source_catalog import filter_sources, load_source_catalog
from ..agents.runtime import MODULES, PROVIDERS, generate_questions, prompt_library_stats, prompt_templates_for, run_agent

try:  # Optional official FSRS implementation; fallback keeps the app offline-capable.
    from fsrs import Card as FSRSCard
    from fsrs import Rating as FSRSRating
    from fsrs import Scheduler as FSRSScheduler
except ImportError:  # pragma: no cover - depends on the selected install profile
    FSRSCard = None
    FSRSRating = None
    FSRSScheduler = None


SKILL_ROOT = Path(__file__).resolve().parents[1]
CONTENT_PATH = SKILL_ROOT / "assets" / "data" / "study-content.json"
SOURCE_CATALOG_PATH = SKILL_ROOT / "assets" / "data" / "source-catalog.json"
ARTIFACT_PROFILES_PATH = SKILL_ROOT / "assets" / "data" / "exam-artifact-profiles.json"
WEB_ROOT = SKILL_ROOT / "assets" / "web"
DEFAULT_DATA_ROOT = Path(os.environ.get("EXAMLEX_DATA_DIR", Path.home() / ".examlex" / "web"))
MAX_UPLOAD_BYTES = 20 * 1024 * 1024
ALLOWED_EXTENSIONS = {".doc", ".docx", ".xls", ".xlsx", ".pdf", ".txt", ".md", ".markdown", ".png", ".jpg", ".jpeg", ".webp"}
PROVIDER_IDS = {"openai", "deepseek", "kimi", "qwen", "glm", "claude", "local", "custom"}
RATINGS = {"again", "hard", "good", "easy"}
INTERVALS_MINUTES = [0, 10, 24 * 60, 2 * 24 * 60, 4 * 24 * 60, 7 * 24 * 60, 15 * 24 * 60, 30 * 24 * 60]
MAX_PREVIEW_MEMBER_BYTES = 2 * 1024 * 1024


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


def iso_now() -> str:
    return utc_now().isoformat().replace("+00:00", "Z")


def today_local() -> str:
    return datetime.now().astimezone().date().isoformat()


def parse_iso(value: str | None) -> datetime:
    if not value:
        return utc_now()
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return utc_now()
    return parsed if parsed.tzinfo else parsed.replace(tzinfo=timezone.utc)


def safe_json_body(handler: BaseHTTPRequestHandler) -> dict[str, Any]:
    length_header = handler.headers.get("Content-Length", "0")
    try:
        length = int(length_header)
    except ValueError as exc:
        raise ValueError("invalid content length") from exc
    if length < 0 or length > MAX_UPLOAD_BYTES:
        raise ValueError("request body is too large")
    raw = handler.rfile.read(length)
    if not raw:
        return {}
    value = json.loads(raw.decode("utf-8"))
    if not isinstance(value, dict):
        raise ValueError("JSON body must be an object")
    return value


def month_key(year: int, month: int) -> str:
    if month < 1 or month > 12:
        raise ValueError("month must be between 1 and 12")
    return f"{year:04d}-{month:02d}"


def requested_month(query: dict[str, list[str]]) -> tuple[int, int]:
    now = datetime.now().astimezone()
    try:
        year = int(query.get("year", [str(now.year)])[0])
        month = int(query.get("month", [str(now.month)])[0])
        month_key(year, month)
        return year, month
    except (TypeError, ValueError):
        return now.year, now.month


def validate_exam(exam: str | None) -> str:
    value = (exam or "CET4").upper()
    if value not in ALL_EXAMS:
        raise ValueError(f"unsupported exam: {value}")
    return value


def default_tasks(exam: str) -> list[dict[str, Any]]:
    return [
        {"id": f"{exam.lower()}-writing", "exam": exam, "module": "writing", "title": "写作：题型审题与首段改写", "minutes": 30, "completion": {"kind": "practice", "module": "writing"}, "done": False},
        {"id": f"{exam.lower()}-listening", "exam": exam, "module": "listening", "title": "听力：精听一段并记录转折", "minutes": 25, "completion": {"kind": "practice", "module": "listening"}, "done": False},
        {"id": f"{exam.lower()}-reading", "exam": exam, "module": "reading", "title": "阅读：完成一组定位与同义替换", "minutes": 35, "completion": {"kind": "practice", "module": "reading"}, "done": False},
        {"id": f"{exam.lower()}-vocabulary", "exam": exam, "module": "vocabulary", "title": "词汇：复习今日到期记忆卡", "minutes": 20, "completion": {"kind": "review_or_practice", "module": "vocabulary"}, "done": False},
    ]


def default_cards(exam: str) -> list[dict[str, Any]]:
    # Cards are learner-generated.  Do not seed a fixed review queue.
    return []


def default_profile(exam: str) -> dict[str, Any]:
    # Do not present a guessed level or target as the learner's own assessment.
    # The planner can still use the time budget until the learner completes the
    # profile form; level/target remain explicitly unset in that state.
    return {
        "learner_id": "local-learner",
        "exam_type": exam,
        "foundation_level": None,
        "target_band": None,
        "daily_time_budget_minutes": 90,
        "self_strengths": [],
        "self_gaps": [],
        "self_assessment_updated_at": None,
    }


def _profile_bullets(value: Any) -> list[str]:
    """Normalize self-reported strengths/gaps without storing unbounded text."""
    if isinstance(value, str):
        values = re.split(r"[,，;；\r\n]+", value)
    elif isinstance(value, list):
        values = value
    else:
        values = []
    result: list[str] = []
    for item in values:
        text = str(item).strip()
        if text and text not in result:
            result.append(text[:80])
        if len(result) >= 8:
            break
    return result


def default_ability() -> dict[str, Any]:
    return {"modules": {module: [{"node": node, "level": 2, "status": "needs_work", "stats": {"total_items": 0, "correct_items": 0, "error_count": 0, "accuracy": None}} for node in nodes] for module, nodes in ABILITY_TREE.items()}}


def extract_preview(filename: str, content: bytes, limit: int = 1500) -> str:
    """Extract a small, non-authoritative hint for routing an upload.

    Binary formats are intentionally best-effort: no OCR or document parser is
    run in the request path, so an uncertain result remains pending review.
    """
    suffix = Path(filename).suffix.lower()
    if suffix in {".txt", ".md", ".markdown"}:
        return content[:limit].decode("utf-8", errors="ignore")
    if suffix == ".docx":
        try:
            with zipfile.ZipFile(io.BytesIO(content)) as archive:
                info = archive.getinfo("word/document.xml")
                if info.file_size > MAX_PREVIEW_MEMBER_BYTES:
                    return ""
                xml = archive.read(info).decode("utf-8", errors="ignore")
            return re.sub(r"<[^>]+>", " ", xml)[:limit]
        except (KeyError, OSError, zipfile.BadZipFile):
            return ""
    if suffix in {".xlsx", ".xls"}:
        try:
            with zipfile.ZipFile(io.BytesIO(content)) as archive:
                names = [name for name in archive.namelist() if name.endswith("sharedStrings.xml")]
                if names:
                    info = archive.getinfo(names[0])
                    if info.file_size > MAX_PREVIEW_MEMBER_BYTES:
                        return ""
                    xml = archive.read(info).decode("utf-8", errors="ignore")
                    return re.sub(r"<[^>]+>", " ", xml)[:limit]
        except (OSError, zipfile.BadZipFile):
            return ""
    if suffix == ".pdf":
        return content[:limit].decode("latin-1", errors="ignore")
    return ""


def classify_upload(filename: str, preview: str) -> dict[str, Any]:
    name = filename.lower()
    text = preview.lower()
    haystack = f"{name} {text}"
    # The filename is the primary domain signal.  This prevents a translation
    # handout containing isolated words from being routed to vocabulary, and a
    # writing handout containing sentences from being routed by sentence shape.
    domains = []
    domain_rules = {
        "writing": ("写作", "作文", "金句", "模板", "范文", "writing", "essay"),
        "translation": ("翻译", "中译英", "英译中", "translation"),
        "listening": ("听力", "精听", "新闻听力", "长对话", "listening"),
        "reading": ("阅读", "仔细阅读", "长篇阅读", "词汇理解", "reading"),
        "vocabulary": ("词汇", "单词", "词组", "短语", "高频词", "核心词", "大纲词", "vocab", "phrase"),
    }
    for domain, keywords in domain_rules.items():
        if any(keyword in name for keyword in keywords):
            domains.append(domain)
    if not domains:
        strong_content_rules = {
            "writing": ("作文模板", "写作模板", "高分金句", "写作题型", "议论文范文"),
            "translation": ("翻译常用词句", "翻译常用词语", "中译英技巧", "英译汉技巧"),
            "listening": ("听力题型", "听力之短篇新闻", "听力之长对话", "听力之篇章"),
            "reading": ("阅读题型", "阅读之仔细阅读", "阅读之长篇阅读", "阅读之词汇理解"),
            "vocabulary": ("高频词汇", "核心词汇", "大纲词汇"),
        }
        for domain, phrases in strong_content_rules.items():
            if any(phrase in text for phrase in phrases):
                domains.append(domain)
    strategy_signal = ("方法论", "策略", "指南", "攻略", "methodology", "strategy")
    if any(keyword in name for keyword in strategy_signal) and not any(keyword in name for keyword in ("模板", "金句", "范文")):
        return {"category": "strategy_ingest", "target": "strategy_queue", "target_module": None, "content_kind": "methodology", "confidence": "high" if preview else "medium", "status": "pending_review", "note": "进入 ExamLex continuous learning 队列，先蒸馏、验证，再供讲题和错题分析引用。"}
    # Paper provenance takes precedence over a section word in the filename:
    # “阅读模拟题” is a simulation, not reading-course material, and “真题阅读”
    # is a past-paper candidate that must pass source verification.
    if any(word in haystack for word in ("真题", "历年", "past paper", "official")):
        return {"category": "candidate_official_past_paper", "target": "past_paper_candidates", "target_module": domains[0] if len(domains) == 1 else None, "content_kind": "past_paper", "confidence": "medium" if preview else "low", "status": "pending_review", "note": "仅进入待核验真题候选区，不会自动发布为官方真题。"}
    if any(word in haystack for word in ("模拟", "模拟题", "mock", "simulation", "练习卷")):
        return {"category": "simulation_not_official", "target": "simulations", "target_module": domains[0] if len(domains) == 1 else None, "content_kind": "simulation_paper", "confidence": "medium" if preview else "low", "status": "pending_review", "note": "模拟材料永久标记为非官方，进入私有训练队列。"}
    if len(domains) == 1:
        domain = domains[0]
        if domain == "writing":
            kind = "template" if any(word in haystack for word in ("模板", "结构图")) else "high_score_expression" if any(word in haystack for word in ("金句", "表达")) else "sample_essay" if "范文" in haystack else "writing_material"
            return {"category": "writing_ingest", "target": "writing_content", "target_module": "writing", "content_kind": kind, "confidence": "high" if preview else "medium", "status": "pending_review", "note": "写作资料按文件主题路由；金句、模板和范文不会被拆到词汇模块。"}
        if domain == "translation":
            kind = "phrase_bank" if any(word in haystack for word in ("词语", "词句", "常用词", "表达", "短语")) else "translation_material"
            return {"category": "translation_ingest", "target": "translation_content", "target_module": "translation", "content_kind": kind, "confidence": "high" if preview else "medium", "status": "pending_review", "note": "翻译资料中的词语、句子和表达保留在翻译板块。"}
        if domain in {"listening", "reading", "vocabulary"}:
            return {"category": f"{domain}_ingest", "target": f"{domain}_content", "target_module": domain, "content_kind": "source_material", "confidence": "high" if preview else "medium", "status": "pending_review", "note": "按文件主题进入对应能力模块，等待人工确认后吸收。"}
    if any(word in haystack for word in ("方法论", "方法", "技巧", "策略", "指南", "讲义", "攻略", "strategy", "method")):
        return {"category": "strategy_ingest", "target": "strategy_queue", "target_module": None, "content_kind": "methodology", "confidence": "medium" if preview else "low", "status": "pending_review", "note": "进入 ExamLex continuous learning 队列，先蒸馏、验证，再供讲题和错题分析引用。"}
    return {"category": "needs_user_confirmation", "target": "ingest_queue", "target_module": None, "content_kind": "unknown", "confidence": "low", "status": "pending_review", "note": "缺少明确的文件主题，需人工选择目标模块后再处理。"}


def _search_terms(value: str) -> set[str]:
    """Return small lexical terms for the local, dependency-free RAG index."""
    words = set(re.findall(r"[A-Za-z][A-Za-z'-]{1,}|[\u4e00-\u9fff]{2,}", value.lower()))
    return {word for word in words if len(word) > 1}


def _compact_snippet(value: str, limit: int = 360) -> str:
    value = re.sub(r"\s+", " ", str(value or "")).strip()
    return value if len(value) <= limit else value[: limit - 1].rstrip() + "…"


class WebStore:
    def __init__(self, root: str | Path | None = None):
        self.root = Path(root or DEFAULT_DATA_ROOT).expanduser().resolve()
        self.root.mkdir(parents=True, exist_ok=True)
        self.quarantine = self.root / "quarantine"
        self.quarantine.mkdir(parents=True, exist_ok=True)
        self.path = self.root / "state.json"
        self._lock = threading.RLock()
        self.content = load_data(CONTENT_PATH)
        self.state = self._load_state()
        for exam in self.content["exam_order"]:
            self.state.setdefault("tasks", {}).setdefault(exam, default_tasks(exam))
            self.state.setdefault("cards", {}).setdefault(exam, default_cards(exam))
            self.ensure_exam_state(exam)
        for key, default_value in (("practice", []), ("activity", {}), ("reviews", []), ("uploads", []), ("providers", []), ("agent_runs", []), ("focus_sessions", []), ("memory_candidates", []), ("practice_sessions", []), ("content_pipeline", [])):
            self.state.setdefault(key, default_value)

    def _load_state(self) -> dict[str, Any]:
        if self.path.exists():
            try:
                value = load_data(self.path)
                if isinstance(value, dict) and value.get("schema_version") == 1:
                    return value
            except (OSError, json.JSONDecodeError):
                pass
        return {
            "schema_version": 1,
            "tasks": {exam: default_tasks(exam) for exam in self.content["exam_order"]},
            "practice": [],
            "activity": {},
            "cards": {exam: default_cards(exam) for exam in self.content["exam_order"]},
            "reviews": [],
            "uploads": [],
            "profiles": {exam: default_profile(exam) for exam in self.content["exam_order"]},
            "abilities": {exam: default_ability() for exam in self.content["exam_order"]},
            "ingest_queue": [],
            "past_paper_candidates": [],
            "simulations": [],
            "vocabulary_sources": [],
            "strategy_queue": [],
            "module_content_queue": [],
            "strategy_library": {"schema_version": 1, "strategies": []},
            "providers": [],
            "agent_runs": [],
            "focus_sessions": [],
            "memory_candidates": [],
            "practice_sessions": [],
            "content_pipeline": [],
        }

    def save(self) -> None:
        with self._lock:
            atomic_save_data(self.path, self.state)

    def ensure_exam_state(self, exam: str) -> None:
        self.state.setdefault("profiles", {}).setdefault(exam, default_profile(exam))
        self.state.setdefault("abilities", {}).setdefault(exam, default_ability())
        self.state.setdefault("ingest_queue", [])
        self.state.setdefault("past_paper_candidates", [])
        self.state.setdefault("simulations", [])
        self.state.setdefault("vocabulary_sources", [])
        self.state.setdefault("strategy_queue", [])
        self.state.setdefault("module_content_queue", [])
        self.state.setdefault("strategy_library", {"schema_version": 1, "strategies": []})
        self.state.setdefault("memory_candidates", [])
        self.state.setdefault("practice_sessions", [])
        self.state.setdefault("content_pipeline", [])

    def exams(self) -> list[dict[str, Any]]:
        return [{"id": exam, **{k: v for k, v in self.content["exams"][exam].items() if k in {"title", "short_title", "content_status", "content_note", "target_bands", "module_order"}}} for exam in self.content["exam_order"]]

    def exam(self, exam: str) -> dict[str, Any]:
        value = validate_exam(exam)
        self.ensure_exam_state(value)
        return self.content["exams"][value]

    def _activity(self, day: str) -> dict[str, Any]:
        entry = self.state["activity"].setdefault(day, {"minutes": 0, "tasks": 0, "items": 0, "correct": 0, "sessions": 0, "exams": {}})
        return entry

    def add_activity(self, day: str, *, exam: str | None = None, minutes: int = 0, tasks: int = 0, items: int = 0, correct: int = 0, sessions: int = 0) -> None:
        root = self._activity(day)
        entry = root if not exam else root.setdefault("exams", {}).setdefault(exam, {"minutes": 0, "tasks": 0, "items": 0, "correct": 0, "sessions": 0})
        for key, value in {"minutes": minutes, "tasks": tasks, "items": items, "correct": correct, "sessions": sessions}.items():
            entry[key] = max(0, int(entry.get(key, 0)) + int(value))

    @staticmethod
    def activity_score(entry: dict[str, Any]) -> float:
        return round(float(entry.get("minutes", 0)) + float(entry.get("tasks", 0)) * 10 + float(entry.get("items", 0)) * 0.5, 1)

    @staticmethod
    def activity_level(score: float) -> int:
        if score <= 0:
            return 0
        if score < 20:
            return 1
        if score < 45:
            return 2
        if score < 80:
            return 3
        return 4

    def heatmap(self, year: int, month: int, exam: str | None = None) -> dict[str, Any]:
        key = month_key(year, month)
        days = []
        for day_number in range(1, calendar.monthrange(year, month)[1] + 1):
            day = f"{key}-{day_number:02d}"
            root_entry = self.state["activity"].get(day, {})
            entry = dict(root_entry.get("exams", {}).get(exam, {})) if exam and root_entry.get("exams") else dict(root_entry)
            score = self.activity_score(entry)
            days.append({"date": day, "minutes": int(entry.get("minutes", 0)), "tasks": int(entry.get("tasks", 0)), "items": int(entry.get("items", 0)), "correct": int(entry.get("correct", 0)), "sessions": int(entry.get("sessions", 0)), "score": score, "level": self.activity_level(score)})
        return {"year": year, "month": month, "month_key": key, "days": days, "legend": [{"level": i, "label": label} for i, label in enumerate(["无记录", "起步", "稳定", "集中", "高强度"])], "history_months": sorted({day[:7] for day in self.state["activity"]})}

    def summary(self, exam: str, year: int, month: int) -> dict[str, Any]:
        tasks = self.tasks_for(exam)
        today = today_local()
        root_entry = self.state["activity"].get(today, {})
        today_entry = root_entry.get("exams", {}).get(exam, {}) if root_entry.get("exams") else root_entry
        due = [card for card in self.state["cards"].get(exam, []) if parse_iso(card.get("due_at")) <= utc_now()]
        practice = [item for item in self.state["practice"] if item.get("exam") == exam]
        total_items = sum(int(item.get("total_items", 0)) for item in practice)
        correct_items = sum(int(item.get("correct_items", 0)) for item in practice)
        completed = sum(1 for task in tasks if task.get("done"))
        return {"date": today, "minutes": int(today_entry.get("minutes", 0)), "completed_tasks": completed, "task_total": len(tasks), "due_cards": len(due), "practice_sessions": len(practice), "accuracy": round(correct_items / total_items * 100, 1) if total_items else None, "heatmap": self.heatmap(year, month, exam), "mastery": self.mastery(exam)}

    def tasks_for(self, exam: str) -> list[dict[str, Any]]:
        """Return today's evidence-backed task snapshot.

        A task is complete when the corresponding practice or review event was
        recorded today.  ``done_on`` is only read as a compatibility fallback
        for state files created by the old checkbox UI; new UI code never writes
        it directly.
        """
        today = today_local()
        tasks = self.state["tasks"].setdefault(exam, default_tasks(exam))
        practices = [item for item in self.state.get("practice", []) if item.get("exam") == exam and item.get("date") == today and int(item.get("total_items", 0)) > 0]
        reviews = [item for item in self.state.get("reviews", []) if item.get("exam") == exam and str(item.get("created_at", ""))[:10] == today]
        card_modules = {card.get("id"): card.get("module") for card in self.state.get("cards", {}).get(exam, [])}
        review_modules = {card_modules.get(item.get("card_id")) for item in reviews}
        snapshot = []
        for task in tasks:
            value = dict(task)
            rule = value.get("completion") or {"kind": "practice", "module": value.get("module")}
            module = rule.get("module")
            matching_practice = [item for item in practices if item.get("module") == module]
            kind = rule.get("kind")
            if kind == "review_or_practice":
                evidence = bool(matching_practice or module in review_modules or (module == "vocabulary" and reviews))
            else:
                evidence = bool(matching_practice)
            legacy = value.get("done_on") == today
            value["done"] = bool(evidence or legacy)
            value["completion_source"] = "evidence" if evidence else "legacy_manual" if legacy else "pending"
            if evidence:
                value["done_reason"] = f"今日已有{len(matching_practice)}条{module}练习记录" if matching_practice else "今日已有记忆卡复习记录"
            elif legacy:
                value["done_reason"] = "兼容旧版本手工记录"
            else:
                value["done_reason"] = "完成对应练习后自动更新"
            snapshot.append(value)
        return snapshot

    def mastery(self, exam: str) -> list[dict[str, Any]]:
        # No practice evidence means no mastery claim; start at zero instead of
        # presenting a subjective default score.
        base = {module: 0 for module in ["writing", "listening", "reading", "translation", "vocabulary", "basics"]}
        for item in self.state["practice"]:
            if item.get("exam") != exam:
                continue
            module = item.get("module")
            if module not in base:
                continue
            total = int(item.get("total_items", 0))
            correct = int(item.get("correct_items", 0))
            if total:
                base[module] = round((base[module] * 0.75) + (correct / total * 100 * 0.25))
        labels = {"writing": "写作", "listening": "听力", "reading": "阅读", "translation": "翻译", "vocabulary": "词汇", "basics": "基础知识"}
        return [{"module": module, "title": labels[module], "score": score} for module, score in base.items()]

    def ledger(self, exam: str | None = None) -> list[dict[str, Any]]:
        return [item for item in self.state["practice"] if exam is None or item.get("exam") == exam]

    def practice_records(self, exam: str, kind: str = "all") -> list[dict[str, Any]]:
        """Return practice records for one exam and an explicit source boundary."""
        statuses = {
            "official": {"verified_official"},
            "simulation": {"simulation_not_official", "ai_generated_simulation"},
            "all": None,
        }
        selected = statuses.get(str(kind or "all").lower())
        if selected is None and str(kind or "all").lower() not in statuses:
            raise ValueError("kind must be official, simulation or all")
        return [
            dict(item)
            for item in self.ledger(validate_exam(exam))
            if selected is None or item.get("source_status") in selected
        ]

    def error_summary(self, exam: str) -> dict[str, Any]:
        by_tag: dict[str, dict[str, Any]] = {}
        for record in self.ledger(exam):
            for tag in record.get("error_tags", []):
                if tag not in ERROR_TAG_TO_ABILITY:
                    continue
                entry = by_tag.setdefault(tag, {"count": 0, "module": ERROR_TAG_TO_ABILITY[tag][0], "dimension": ERROR_TAG_TO_ABILITY[tag][1], "last_practice_date": record.get("date")})
                entry["count"] += 1
                if str(record.get("date", "")) > str(entry.get("last_practice_date", "")):
                    entry["last_practice_date"] = record.get("date")
        ranked = sorted(by_tag.items(), key=lambda item: (-item[1]["count"], item[0]))
        return {"exam": exam, "total_records": len(self.ledger(exam)), "by_tag": dict(ranked), "top_risks": [{"tag": tag, **data} for tag, data in ranked[:3]]}

    def plan(self, exam: str) -> dict[str, Any]:
        self.ensure_exam_state(exam)
        profile = self.state["profiles"][exam]
        ability = self.state["abilities"][exam]
        error_summary = self.error_summary(exam)
        try:
            return generate_daily_plan(profile, ability, error_summary, self.state.get("strategy_library"))
        except (TypeError, ValueError):
            return {"plan_id": f"{exam.lower()}-{today_local()}", "exam_type": exam, "daily_time_budget_minutes": 90, "total_planned_minutes": 90, "tasks": [{"module": "vocabulary", "focus": "review", "minutes": 20, "reason": "default constrained allocation"}, {"module": "reading", "focus": "定位能力", "minutes": 35, "reason": "default constrained allocation"}, {"module": "listening", "focus": "关键词捕捉", "minutes": 35, "reason": "default constrained allocation"}]}

    def profile_diagnosis(self, exam: str) -> dict[str, Any]:
        """Return an evidence-backed learner portrait for the dashboard."""
        value = validate_exam(exam)
        self.ensure_exam_state(value)
        profile = dict(self.state["profiles"][value])
        self_assessment_configured = bool(
            profile.get("self_assessment_updated_at")
            and profile.get("foundation_level")
            and profile.get("target_band")
        )
        self_assessment = {
            "configured": self_assessment_configured,
            "foundation_level": profile.get("foundation_level") if self_assessment_configured else None,
            "target_band": profile.get("target_band") if self_assessment_configured else None,
            "strengths": _profile_bullets(profile.get("self_strengths")),
            "gaps": _profile_bullets(profile.get("self_gaps")),
            "daily_time_budget_minutes": profile.get("daily_time_budget_minutes"),
            "updated_at": profile.get("self_assessment_updated_at"),
        }
        ledger = self.ledger(value)
        assessment_source_statuses = {"verified_official", "simulation_not_official", "ai_generated_simulation"}
        assessment_records = [item for item in ledger if item.get("source_status") in assessment_source_statuses]
        assessment_rounds = len(assessment_records)
        assessment_required_rounds = 3
        assessment_ready = assessment_rounds >= assessment_required_rounds
        # The radar and diagnosis are claims about exam performance, so keep
        # them empty until three submitted full-paper records exist.  Other
        # counters below remain live so the learner can still track practice.
        mastery = self.mastery(value) if assessment_ready else []
        risks = self.error_summary(value)["top_risks"] if assessment_ready else []
        focus_minutes = sum(int(item.get("duration_seconds", 0)) // 60 for item in self.state.get("focus_sessions", []) if item.get("exam") == value)
        practice_minutes = sum(int(item.get("duration_minutes", 0)) for item in ledger)
        practice_items = sum(int(item.get("total_items", 0)) for item in ledger)
        practice_correct = sum(int(item.get("correct_items", 0)) for item in ledger)
        official_records = [item for item in ledger if item.get("source_status") == "verified_official"]
        simulation_records = [item for item in ledger if item.get("source_status") in {"simulation_not_official", "ai_generated_simulation"}]
        system_stats = {
            "learning_minutes": practice_minutes + focus_minutes,
            "practice_items": practice_items,
            "practice_correct": practice_correct,
            "practice_accuracy": round(practice_correct / practice_items * 100, 1) if practice_items else None,
            "practice_records": len(ledger),
            "official_paper_records": len(official_records),
            "simulation_records": len(simulation_records),
            "assessment_rounds": assessment_rounds,
            "assessment_required_rounds": assessment_required_rounds,
            "assessment_ready": assessment_ready,
            "source": "practice_ledger_and_focus_sessions",
        }
        totals: dict[str, list[int]] = {}
        for record in ledger:
            module = str(record.get("module", "other"))
            totals.setdefault(module, [0, 0])
            totals[module][0] += int(record.get("total_items", 0))
            totals[module][1] += int(record.get("correct_items", 0))
        module_accuracy = {module: round(correct / total * 100, 1) if total else None for module, (total, correct) in totals.items()}
        system_stats["module_accuracy"] = module_accuracy
        scored = [(item["title"], item["score"]) for item in mastery]
        strengths = [title for title, _ in sorted(scored, key=lambda item: -item[1])[:2]] if assessment_ready else []
        gaps = [title for title, _ in sorted(scored, key=lambda item: item[1])[:2]] if assessment_ready else []
        if not assessment_ready:
            diagnosis = f"无（完成真题或模拟卷测试 {assessment_rounds}/{assessment_required_rounds} 轮后，系统才会生成评估。）"
        elif risks:
            diagnosis = f"当前优先处理 {risks[0]['tag']}，它已出现 {risks[0]['count']} 次；同时维持 {', '.join(str(item) for item in strengths)}。"
        else:
            diagnosis = f"当前基础稳定，优先巩固 {', '.join(str(item) for item in gaps)}，并用真题语境验证迁移。"
        system_assessment = {
            "status": "evidence_based" if assessment_ready else "insufficient_evidence",
            "method": "三轮真题或模拟卷提交结果、正确率、耗时和错误标签的系统分析",
            "target_band": self_assessment.get("target_band"),
            "mastery": mastery,
            "strengths": strengths,
            "gaps": gaps,
            "risks": risks,
            "evidence_records": assessment_rounds,
            "practice_records": len(ledger),
            "assessment_required_rounds": assessment_required_rounds,
            "assessment_ready": assessment_ready,
            "evaluated_at": iso_now(),
        }
        return {
            "exam": value,
            "profile": profile,
            "self_assessment": self_assessment,
            "system_assessment": system_assessment,
            "system_stats": system_stats,
            # Keep these fields for existing dashboard consumers.
            "mastery": mastery,
            "module_accuracy": module_accuracy,
            "strengths": strengths,
            "gaps": gaps,
            "risks": risks,
            "diagnosis": diagnosis,
            "evidence_records": assessment_rounds,
            "generated_at": iso_now(),
        }

    def period_plan(self, exam: str, period: str = "day") -> dict[str, Any]:
        value = validate_exam(exam)
        period = str(period or "day").lower()
        if period not in {"day", "week", "month"}:
            raise ValueError("period must be day, week or month")
        daily = self.plan(value)
        if period == "day":
            return {"period": period, **daily}
        multiplier = 7 if period == "week" else 30
        tasks = []
        for task in daily.get("tasks", []):
            item = dict(task)
            item["minutes"] = int(item.get("minutes", 0))
            item["recommended_days"] = multiplier
            item["period_minutes"] = item["minutes"] * multiplier
            tasks.append(item)
        return {"period": period, "exam_type": value, "plan_id": f"{value.lower()}-{today_local()}-{period}", "daily_time_budget_minutes": daily.get("daily_time_budget_minutes", 90), "total_planned_minutes": sum(int(item.get("period_minutes", 0)) for item in tasks), "tasks": tasks, "basis": "由画像、错误证据和专项能力节点生成"}

    def module_trends(self, exam: str, period: str = "month") -> dict[str, Any]:
        value = validate_exam(exam)
        period = str(period or "month").lower()
        length = {"day": 1, "week": 7, "month": 30}.get(period)
        if length is None:
            raise ValueError("period must be day, week or month")
        end = date.fromisoformat(today_local())
        days = [(end - timedelta(days=length - 1 - i)).isoformat() for i in range(length)]
        modules = ["writing", "listening", "reading", "translation", "vocabulary", "basics"]
        series = []
        for module in modules:
            values = []
            for day in days:
                records = [item for item in self.ledger(value) if item.get("module") == module and item.get("date") == day]
                total = sum(int(item.get("total_items", 0)) for item in records)
                correct = sum(int(item.get("correct_items", 0)) for item in records)
                values.append(round(correct / total * 100, 1) if total else None)
            series.append({"module": module, "values": values, "has_data": any(item is not None for item in values)})
        return {"exam": value, "period": period, "days": days, "series": series}

    def ai_summary(self, exam: str, day: str | None = None) -> dict[str, Any]:
        value = validate_exam(exam)
        target = str(day or today_local())
        date.fromisoformat(target)
        records = [item for item in self.ledger(value) if item.get("date") == target]
        total = sum(int(item.get("total_items", 0)) for item in records)
        correct = sum(int(item.get("correct_items", 0)) for item in records)
        minutes = sum(int(item.get("duration_minutes", 0)) for item in records)
        diagnosis = self.profile_diagnosis(value)
        if not records:
            text = "今天还没有可分析的专项练习证据。建议先完成词汇复习和一组阅读定位题。"
        else:
            accuracy = round(correct / total * 100, 1) if total else 0
            text = f"今天完成 {len(records)} 次专项练习，共 {total} 题，正确率 {accuracy}%，记录学习 {minutes} 分钟。"
            if diagnosis["risks"]:
                text += f" 当前最需要处理的是 {diagnosis['risks'][0]['tag']}。"
        mode = "deterministic"
        configured = next((item for item in self.state.get("providers", []) if item.get("provider_id") in PROVIDERS and (item.get("provider_id") != "custom" or item.get("endpoint"))), None)
        if configured:
            try:
                model_run = run_agent(module="planner", exam=value, input_text=text, context={"date": target, "records": records[-20:], "diagnosis": diagnosis}, provider=configured.get("provider_id"), model=configured.get("model") or None, api_key_env=configured.get("api_key_env") or None, endpoint=configured.get("endpoint") or None, use_model=True)
                if model_run.get("mode") == "model":
                    findings = model_run.get("output", {}).get("findings", [])
                    if findings:
                        text = " ".join(str(item) for item in findings[:4])
                        mode = "model"
            except Exception:
                pass
        return {"exam": value, "date": target, "mode": mode, "summary": text, "next_day": self.period_plan(value, "day"), "next_week": self.period_plan(value, "week"), "next_month": self.period_plan(value, "month"), "evidence_records": len(records)}

    def ribbon(self, exam: str) -> list[dict[str, Any]]:
        events: list[dict[str, Any]] = []
        for item in self.ledger(exam):
            events.append({"id": item["id"], "date": item.get("date"), "kind": "practice", "module": item.get("module"), "label": f"练习 {item.get('correct_items', 0)}/{item.get('total_items', 0)}", "score": round(float(item.get("correct_items", 0)) / max(1, int(item.get("total_items", 0))) * 100)})
            for tag in item.get("error_tags", []):
                events.append({"id": f"{item['id']}-{tag}", "date": item.get("date"), "kind": "error", "module": ERROR_TAG_TO_ABILITY.get(tag, (item.get("module"), ""))[0], "label": tag, "score": 0})
        for item in self.state["reviews"]:
            if item.get("exam") == exam:
                events.append({"id": item["id"], "date": item.get("created_at", "")[:10], "kind": "review", "module": "memory", "label": f"复习 {item.get('rating')}", "score": item.get("new_stage", 0)})
        return sorted(events, key=lambda item: (item.get("date", ""), item.get("id", "")))[-24:]

    def node_analysis(self, exam: str, module: str | None = None) -> dict[str, Any]:
        summary = self.error_summary(exam)
        risks = [item for item in summary["top_risks"] if not module or item["module"] == module]
        evidence = [{"record_id": item["id"], "date": item.get("date"), "module": item.get("module"), "error_tags": item.get("error_tags", []), "correct_items": item.get("correct_items"), "total_items": item.get("total_items")} for item in self.ledger(exam) if not module or item.get("module") == module]
        return {"exam": exam, "module": module, "risks": risks, "evidence": evidence[-20:], "explanation": "优先级由错误重复次数和现有能力节点共同决定；每条结论都保留练习记录作为证据。"}

    def save_profile(self, payload: dict[str, Any]) -> dict[str, Any]:
        exam = validate_exam(payload.get("exam_type"))
        existing = dict(self.state.setdefault("profiles", {}).get(exam) or default_profile(exam))
        profile = {
            **existing,
            "learner_id": str(payload.get("learner_id", existing.get("learner_id", "local-learner"))).strip() or "local-learner",
            "exam_type": exam,
            "foundation_level": payload.get("foundation_level", existing.get("foundation_level")),
            "target_band": payload.get("target_band", existing.get("target_band")),
            "daily_time_budget_minutes": payload.get("daily_time_budget_minutes", existing.get("daily_time_budget_minutes", 90)),
            "self_strengths": _profile_bullets(payload.get("self_strengths", existing.get("self_strengths"))),
            "self_gaps": _profile_bullets(payload.get("self_gaps", existing.get("self_gaps"))),
            "self_assessment_updated_at": iso_now(),
        }
        errors = validate_profile(profile)
        if errors:
            raise ValueError("; ".join(errors))
        self.state.setdefault("profiles", {})[exam] = profile
        self.save()
        return profile

    def toggle_task(self, exam: str, task_id: str, done: bool | None = None) -> dict[str, Any]:
        for task in self.state["tasks"].get(exam, []):
            if task.get("id") == task_id:
                next_value = not bool(task.get("done")) if done is None else bool(done)
                if next_value != bool(task.get("done")):
                    task["done"] = next_value
                    if next_value:
                        task["done_on"] = today_local()
                        self.add_activity(today_local(), exam=exam, minutes=int(task.get("minutes", 0)), tasks=1, sessions=1)
                    else:
                        task.pop("done_on", None)
                        self.add_activity(today_local(), exam=exam, minutes=-int(task.get("minutes", 0)), tasks=-1, sessions=-1)
                self.save()
                return task
        raise KeyError("task not found")

    def record_practice(self, payload: dict[str, Any]) -> dict[str, Any]:
        exam = validate_exam(payload.get("exam"))
        module = str(payload.get("module", "")).strip()
        if not module:
            raise ValueError("module is required")
        total = int(payload.get("total_items", 0))
        if total <= 0:
            raise ValueError("total_items must be a positive integer")
        correct = max(0, min(total, int(payload.get("correct_items", 0))))
        minutes = max(0, int(payload.get("duration_minutes", 0)))
        day = str(payload.get("date") or today_local())
        date.fromisoformat(day)
        if day > today_local():
            raise ValueError("future practice dates are not accepted")
        raw_tags = payload.get("error_tags", [])
        if not isinstance(raw_tags, list) or not all(isinstance(tag, str) for tag in raw_tags):
            raise ValueError("error_tags must be a list of strings")
        unknown = validate_error_tags(raw_tags)
        if unknown:
            raise ValueError(f"unknown error tags: {', '.join(unknown)}")
        # A direct practice record is a专项练习 by default.  It must not be
        # counted as a full-paper simulation unless the session explicitly
        # supplies a simulation source status.
        source_status = str(payload.get("source_status", "learner_practice")).strip() or "learner_practice"
        if source_status not in {"learner_practice", "verified_official", "simulation_not_official", "ai_generated_simulation"}:
            raise ValueError("unsupported source_status")
        record = {"id": uuid.uuid4().hex, "exam": exam, "module": module, "task_id": str(payload.get("task_id", f"web-{module}")), "title": str(payload.get("title", "")).strip()[:200], "source_id": str(payload.get("source_id", "")).strip()[:200], "paper_kind": str(payload.get("paper_kind", "")).strip()[:40], "total_items": total, "correct_items": correct, "duration_minutes": minutes, "date": day, "error_tags": raw_tags, "timed": bool(payload.get("timed", False)), "source_status": source_status, "created_at": iso_now()}
        self.state["practice"].append(record)
        self.add_activity(day, exam=exam, minutes=minutes, items=total, correct=correct, sessions=1)
        self._create_practice_card(record)
        self.save()
        return record

    def create_practice_session(self, payload: dict[str, Any]) -> dict[str, Any]:
        """Create a private practice session with an explicit source boundary."""
        exam = validate_exam(payload.get("exam"))
        kind = str(payload.get("kind", "mock")).lower()
        module = str(payload.get("module", "reading")).lower()
        if module not in {"writing", "listening", "reading", "translation", "vocabulary", "basics"}:
            raise ValueError("unsupported practice module")
        is_full_paper = False
        scope = str(payload.get("scope", "")).lower()
        if kind == "past":
            verified = [item for item in self.state.get("past_paper_candidates", []) if item.get("exam") == exam and item.get("status") == "verified_official"]
            if not verified:
                raise ValueError("no verified official past paper is available")
            source_status = "verified_official"
            requested_source = str(payload.get("source_id") or "")
            selected = next((item for item in verified if item.get("id") == requested_source or item.get("upload_id") == requested_source), verified[0])
            source_id = str(selected.get("id"))
            module = "full_paper"
            is_full_paper = True
            timer_mode, limit = "countdown", 125 * 60
        elif kind == "module":
            source_status = "learner_practice"
            source_id = str(payload.get("source_id") or "module-practice")
            timer_mode, limit = "countup", None
        elif kind == "upload":
            requested_source = str(payload.get("source_id") or "")
            simulation = next((item for item in self.state.get("simulations", []) if item.get("exam") == exam and (item.get("id") == requested_source or item.get("upload_id") == requested_source)), None)
            if simulation:
                if simulation.get("status") != "ready_private":
                    raise ValueError("uploaded simulation has not passed the pipeline validation gate")
                source_status = "simulation_not_official"
                source_id = str(simulation.get("id"))
                module = "full_paper"
                is_full_paper = True
                timer_mode, limit = "countdown", 125 * 60
            else:
                # Module-scoped uploads are learner practice, not simulations.
                # They become selectable only after the same pipeline commit gate.
                uploaded = next((item for item in self.state.get("module_content_queue", []) if item.get("exam") == exam and item.get("target_module") == module and (item.get("id") == requested_source or item.get("upload_id") == requested_source)), None)
                if not uploaded or uploaded.get("status") not in {"ready_private", "committed"}:
                    raise ValueError("uploaded practice has not passed the pipeline validation gate")
                source_status = "learner_practice"
                source_id = str(uploaded.get("id") or uploaded.get("upload_id"))
                timer_mode, limit = "countup", None
        else:
            source_status = "ai_generated_simulation" if kind == "ai" else "simulation_not_official"
            source_id = str(payload.get("source_id") or "private-simulation")
            if kind == "ai" and scope == "full_paper":
                module = "full_paper"
                is_full_paper = True
            timer_mode, limit = "countdown", 125 * 60
        try:
            question_count = min(60, max(1, int(payload.get("question_count", 20 if is_full_paper else 5))))
        except (TypeError, ValueError):
            question_count = 5
        if is_full_paper:
            question_count = max(20, question_count)
        difficulty = str(payload.get("difficulty", "standard")).lower()
        if difficulty not in {"basic", "standard", "advanced"}:
            difficulty = "standard"
        focus = str(payload.get("focus", "")).strip()[:240]
        generation_mode = "deterministic"
        generation_provider = None
        generation_sources = []
        questions = self._generated_questions(module, count=question_count, difficulty=difficulty, focus=focus)
        if kind == "ai":
            rag = self.retrieve_agent_sources(exam, module, focus)
            generation_sources = rag.get("source_ids", [])
            configured = next((item for item in self.state.get("providers", []) if item.get("provider_id") in PROVIDERS and (item.get("provider_id") != "custom" or item.get("endpoint"))), None)
            if configured:
                generated = generate_questions(module=module, exam=exam, count=question_count, difficulty=difficulty, focus=focus, context={"rag": rag, "source_ids": generation_sources}, provider=configured.get("provider_id"), model=configured.get("model") or None, api_key_env=configured.get("api_key_env") or None, endpoint=configured.get("endpoint") or None, use_model=True)
                if generated and len(generated.get("questions", [])) == question_count:
                    questions = generated["questions"]
                    generation_mode = "model"
                    generation_provider = configured.get("provider_id")
            if generation_mode != "model":
                generation_sources = generation_sources[:10]
        session = {"id": uuid.uuid4().hex, "exam": exam, "kind": kind, "module": module, "source_id": source_id, "source_status": source_status, "generation_request": {"difficulty": difficulty, "focus": focus, "question_count": question_count, "mode": generation_mode, "provider": generation_provider, "source_ids": generation_sources, "validation": "structured_questions_checked"} if kind == "ai" else None, "questions": questions, "answers": {}, "status": "active", "timer_mode": timer_mode, "limit_seconds": limit, "started_at": iso_now(), "overtime_seconds": 0}
        self.state.setdefault("practice_sessions", []).append(session)
        self.state["practice_sessions"] = self.state["practice_sessions"][-100:]
        self.save()
        return self._public_session(session)

    @staticmethod
    def _generated_questions(module: str, count: int = 5, difficulty: str = "standard", focus: str = "") -> list[dict[str, Any]]:
        bank = {
            "reading": {"prompt": "The passage suggests that effective practice should be ____.", "options": ["evidence-based", "random", "delayed", "optional"], "answer_index": 0, "explanation": "文中强调根据证据调整练习。"},
            "listening": {"prompt": "Which signal most often introduces a contrast in a lecture?", "options": ["however", "first", "also", "finally"], "answer_index": 0, "explanation": "however 是典型转折信号。"},
            "vocabulary": {"prompt": "Choose the closest meaning of 'retain'.", "options": ["保持", "拒绝", "拆分", "替换"], "answer_index": 0, "explanation": "retain = keep or continue to have。"},
            "basics": {"prompt": "In 'She reads carefully', 'carefully' is a(n) ____.", "options": ["adverb", "noun", "verb", "adjective"], "answer_index": 0, "explanation": "carefully 修饰动词 reads，是副词。"},
            "translation": {"prompt": "Translate: '证据应当支持你的结论。'", "answer": "Evidence should support your conclusion.", "explanation": "保证主干 evidence + should support + conclusion。"},
            "writing": {"prompt": "Write one sentence introducing the main argument about evidence-based learning.", "answer": "Evidence-based learning helps students improve efficiently.", "explanation": "句子应包含明确主语、谓语和中心论点。"},
        }
        if module == "full_paper":
            paper_bank = [
                ("听力", bank["listening"]),
                ("阅读", bank["reading"]),
                ("词汇", bank["vocabulary"]),
                ("翻译", bank["translation"]),
                ("写作", bank["writing"]),
            ]
        else:
            paper_bank = [("专项", bank[module])]
        prompt_suffix = f"（难度：{difficulty}）"
        if focus:
            prompt_suffix += f" 重点：{focus}"
        questions = []
        for index in range(max(1, count)):
            section, template = paper_bank[index % len(paper_bank)]
            prompt = template["prompt"]
            if index:
                prompt = f"{prompt} · 变式 {index + 1}"
            if module == "full_paper":
                prompt = f"[{section}] {prompt}"
            questions.append({"id": f"q-{uuid.uuid4().hex[:10]}", "type": "text" if "answer" in template and "options" not in template else "choice", "prompt": prompt + prompt_suffix, "options": template.get("options", []), "answer_index": template.get("answer_index"), "answer": template.get("answer"), "explanation": template["explanation"]})
        return questions

    @staticmethod
    def _public_session(session: dict[str, Any]) -> dict[str, Any]:
        value = dict(session)
        value["questions"] = [{key: item[key] for key in ("id", "type", "prompt", "options")} for item in session.get("questions", [])]
        value.pop("answers", None)
        return value

    def submit_practice_session(self, payload: dict[str, Any]) -> dict[str, Any]:
        session_id = str(payload.get("session_id", ""))
        session = next((item for item in self.state.get("practice_sessions", []) if item.get("id") == session_id), None)
        if not session:
            raise KeyError("practice session not found")
        if session.get("status") == "submitted":
            return {"session": self._public_session(session), "result": session.get("result", {})}
        answers = payload.get("answers") if isinstance(payload.get("answers"), dict) else {}
        session["answers"] = {str(key): value for key, value in answers.items()}
        correct = 0
        feedback = []
        for question in session.get("questions", []):
            actual = session["answers"].get(question["id"])
            expected = question.get("answer_index") if question.get("type") == "choice" else question.get("answer", "")
            if question.get("type") == "choice":
                ok = str(actual) == str(expected)
            else:
                text = str(actual or "").strip().lower()
                ok = len(text) >= 12 and any(token in text for token in ("evidence", "support", "结论", "conclusion"))
            if ok:
                correct += 1
            feedback.append({"question_id": question["id"], "correct": ok, "expected": expected, "explanation": question.get("explanation", "")})
        total = len(session.get("questions", []))
        session["status"] = "submitted"
        session["submitted_at"] = iso_now()
        session["result"] = {"total": total, "correct": correct, "accuracy": round(correct / total * 100, 1) if total else 0, "feedback": feedback}
        default_errors = {"writing": "WRITING_TASK_RESPONSE_WEAK", "listening": "LISTENING_KEYWORD_MISS", "reading": "READING_LOCATION_FAIL", "translation": "TRANSLATION_GRAMMAR_FAIL", "vocabulary": "VOCAB_MEANING_RECOGNITION_FAIL", "basics": "LANG_GRAMMAR_SELECT_FAIL"}
        error_tags = [] if correct == total else [default_errors.get(session["module"], "READING_LOCATION_FAIL")]
        record = self.record_practice({"exam": session["exam"], "module": session["module"], "total_items": total, "correct_items": correct, "duration_minutes": max(1, int((parse_iso(session.get("submitted_at")) - parse_iso(session.get("started_at"))).total_seconds() // 60)), "source_status": session["source_status"], "source_id": session.get("source_id"), "paper_kind": session.get("kind"), "title": f"{session.get('kind', 'simulation')} · {session.get('source_id') or session.get('module')}"[:200], "error_tags": error_tags})
        session["practice_record_id"] = record["id"]
        self.save()
        return {"session": self._public_session(session), "result": session["result"], "record": record}

    def continue_after_timeout(self, payload: dict[str, Any]) -> dict[str, Any]:
        session_id = str(payload.get("session_id", ""))
        session = next((item for item in self.state.get("practice_sessions", []) if item.get("id") == session_id), None)
        if not session:
            raise KeyError("practice session not found")
        if session.get("status") == "submitted":
            return {"session": self._public_session(session)}
        session["status"] = "overtime"
        session["overtime_seconds"] = max(0, int(payload.get("overtime_seconds", 0)))
        self.save()
        return {"session": self._public_session(session), "message": "已进入超时答题，提交时会保留超时时长。"}

    def _create_practice_card(self, record: dict[str, Any]) -> dict[str, Any]:
        """Create one traceable card from a recorded practice event."""
        module = str(record.get("module", "vocabulary"))
        tags = record.get("error_tags") or []
        focus = str(tags[0]) if tags else "本次练习的核心考点"
        card = {"id": uuid.uuid4().hex, "exam": record["exam"], "module": module, "type": module, "front": f"{module} 复盘：{focus}是什么？", "back": f"来源于 {record.get('date')} 的 {module} 练习（{record.get('correct_items', 0)}/{record.get('total_items', 0)}）。请结合原题和错误证据复述考点，再补充正确做法。", "hint": "先回忆，再回到原题核对证据。", "stage": 0, "due_at": iso_now(), "lapses": 0, "review_keys": [], "source_kind": "practice", "source_id": record["id"]}
        self.state.setdefault("cards", {}).setdefault(record["exam"], []).append(card)
        return card

    def confirm_memory_candidate(self, upload_id: str, exam: str) -> dict[str, Any]:
        """Promote a quarantined upload candidate into the review queue."""
        candidate = next((item for item in self.state.get("memory_candidates", []) if item.get("upload_id") == upload_id and item.get("exam") == exam), None)
        if not candidate:
            raise KeyError("memory candidate not found")
        if candidate.get("status") == "confirmed" and candidate.get("card_id"):
            return next(card for card in self.state["cards"][exam] if card.get("id") == candidate["card_id"])
        card = {"id": uuid.uuid4().hex, "exam": exam, "module": candidate.get("module") or "vocabulary", "type": candidate.get("module") or "vocabulary", "front": candidate["front"], "back": candidate["back"], "hint": "回到上传资料核对原文，再给自己评分。", "stage": 0, "due_at": iso_now(), "lapses": 0, "review_keys": [], "source_kind": "upload", "source_id": upload_id}
        self.state.setdefault("cards", {}).setdefault(exam, []).append(card)
        candidate["status"] = "confirmed"
        candidate["card_id"] = card["id"]
        self.save()
        return card

    def due_cards(self, exam: str, include_future: bool = False) -> list[dict[str, Any]]:
        now = utc_now()
        cards = []
        for card in self.state["cards"].get(exam, []):
            if include_future or parse_iso(card.get("due_at")) <= now:
                value = {k: v for k, v in card.items() if k not in {"review_keys"}}
                value["is_due"] = parse_iso(card.get("due_at")) <= now
                cards.append(value)
        cards.sort(key=lambda item: item.get("due_at", ""))
        return cards

    def review_card(self, exam: str, card_id: str, rating: str, key: str | None) -> dict[str, Any]:
        rating = rating.lower()
        if rating not in RATINGS:
            raise ValueError("rating must be again, hard, good, or easy")
        for card in self.state["cards"].get(exam, []):
            if card.get("id") != card_id:
                continue
            review_key = key or secrets.token_urlsafe(12)
            if review_key in card.setdefault("review_keys", []):
                return {"card": {k: v for k, v in card.items() if k != "review_keys"}, "idempotent": True}
            old_stage = int(card.get("stage", 0))
            fsrs_result = self._review_with_fsrs(card, rating)
            if rating == "again":
                card["lapses"] = int(card.get("lapses", 0)) + 1
            if fsrs_result:
                new_stage, due = fsrs_result
            elif rating == "again":
                new_stage = 0
                due = utc_now() + timedelta(minutes=10)
            elif rating == "hard":
                new_stage = old_stage
                due = utc_now() + timedelta(minutes=max(10, int((INTERVALS_MINUTES[min(old_stage, len(INTERVALS_MINUTES) - 1)] or 10) * 0.5)))
            elif rating == "good":
                new_stage = min(old_stage + 1, len(INTERVALS_MINUTES) - 1)
                due = utc_now() + timedelta(minutes=INTERVALS_MINUTES[new_stage])
            else:
                new_stage = min(old_stage + 2, len(INTERVALS_MINUTES) - 1)
                due = utc_now() + timedelta(minutes=min(60 * 24, max(10, int((INTERVALS_MINUTES[new_stage] or 10) * 1.5))))
            card["stage"] = new_stage
            card["due_at"] = due.isoformat().replace("+00:00", "Z")
            card["review_keys"].append(review_key)
            self.state["reviews"].append({"id": uuid.uuid4().hex, "card_id": card_id, "exam": exam, "module": card.get("module", "vocabulary"), "rating": rating, "old_stage": old_stage, "new_stage": new_stage, "due_at": card["due_at"], "idempotency_key": review_key, "created_at": iso_now()})
            self.save()
            return {"card": {k: v for k, v in card.items() if k != "review_keys"}, "idempotent": False}
        raise KeyError("card not found")

    @staticmethod
    def _review_with_fsrs(card: dict[str, Any], rating: str) -> tuple[int, datetime] | None:
        """Use the official FSRS scheduler when installed, otherwise return None."""
        if not (FSRSCard and FSRSRating and FSRSScheduler):
            return None
        try:
            fsrs_card = FSRSCard.from_dict(card["fsrs"]) if card.get("fsrs") else FSRSCard()
            scheduler = FSRSScheduler(enable_fuzzing=False)
            fsrs_rating = {"again": FSRSRating.Again, "hard": FSRSRating.Hard, "good": FSRSRating.Good, "easy": FSRSRating.Easy}[rating]
            updated, _log = scheduler.review_card(fsrs_card, fsrs_rating)
            card["fsrs"] = updated.to_dict()
            card["due_at"] = updated.due.isoformat().replace("+00:00", "Z")
            card["fsrs_state"] = int(updated.state.value)
            return int(updated.state.value), updated.due
        except (KeyError, TypeError, ValueError, AttributeError):
            return None

    def upload(self, filename: str, content: bytes, content_type: str | None, exam: str, module_hint: str | None = None) -> dict[str, Any]:
        original = Path(filename).name
        suffix = Path(original).suffix.lower()
        if suffix not in ALLOWED_EXTENSIONS:
            raise ValueError("unsupported file type")
        if len(content) > MAX_UPLOAD_BYTES:
            raise ValueError("file is too large")
        upload_id = uuid.uuid4().hex
        safe_name = re.sub(r"[^A-Za-z0-9._-]+", "_", original).strip("._") or "upload"
        target = (self.quarantine / f"{upload_id}_{safe_name}").resolve()
        if self.quarantine not in target.parents:
            raise ValueError("invalid upload path")
        target.write_bytes(content)
        preview = extract_preview(original, content)
        classification = classify_upload(original, preview)
        # A file submitted from a named专项训练 page is an explicit learner
        # practice set. Keep that user intent and its module attribution rather
        # than guessing from short filenames or individual sentences. Full
        # papers continue to be uploaded from the dedicated真题/模拟题 pages.
        hint = str(module_hint or "").strip().lower()
        if hint in {"writing", "listening", "reading", "translation", "vocabulary", "basics"}:
            classification = {
                "category": "module_practice_upload",
                "target": "module_practice",
                "target_module": hint,
                "content_kind": "practice_questions",
                "confidence": "user_declared",
                "status": "pending_review",
                "note": "从专项训练入口提交，按当前专项作为私有练习题处理；不提升为真题或模拟整卷。",
            }
        item = {"id": upload_id, "exam": exam, "filename": original, "stored_name": target.name, "bytes": len(content), "content_type": content_type or mimetypes.guess_type(original)[0] or "application/octet-stream", "status": "quarantined", "classification": classification, "preview_available": bool(preview), "preview": _compact_snippet(preview, 1500), "sha256": hashlib.sha256(content).hexdigest(), "created_at": iso_now()}
        self.state["uploads"].append(item)
        queue_item = {"id": uuid.uuid4().hex, "upload_id": upload_id, "exam": exam, "category": classification["category"], "target": classification["target"], "target_module": classification.get("target_module"), "content_kind": classification.get("content_kind"), "status": "pending_review", "created_at": iso_now()}
        self.state["ingest_queue"].append(queue_item)
        pipeline = {
            "upload_id": upload_id,
            "exam": exam,
            "stages": [
                {"name": "quarantine", "status": "done", "at": iso_now()},
                {"name": "classify", "status": "done", "at": iso_now(), "category": classification["category"]},
                {"name": "extract", "status": "pending"},
                {"name": "distill", "status": "pending"},
                {"name": "validate", "status": "pending"},
                {"name": "commit", "status": "pending"},
            ],
            "current_stage": "extract",
            "checkpoint": f"upload:{upload_id}:classify",
            "errors": [],
            "updated_at": iso_now(),
        }
        self.state["content_pipeline"].append(pipeline)
        # Route the material into an explicit, auditable queue.  Only user-
        # uploaded simulations are ready for private practice; all other
        # classes require a later confirmation or evidence verification step.
        if classification["category"] == "simulation_not_official":
            self.state["simulations"].append({"id": uuid.uuid4().hex, "upload_id": upload_id, "exam": exam, "filename": original, "module": classification.get("target_module") or "reading", "status": "pending_pipeline", "source_status": "simulation_not_official", "created_at": iso_now()})
        elif classification["category"] == "candidate_official_past_paper":
            self.state["past_paper_candidates"].append({"id": uuid.uuid4().hex, "upload_id": upload_id, "exam": exam, "status": "pending_source_verification", "source_status": "candidate_official_past_paper", "created_at": iso_now()})
        elif classification["category"] == "vocabulary_ingest":
            self.state["vocabulary_sources"].append({"id": uuid.uuid4().hex, "upload_id": upload_id, "exam": exam, "status": "draft", "source_status": "user_upload_draft", "created_at": iso_now()})
        elif classification["category"] == "strategy_ingest":
            self.state["strategy_queue"].append({"id": uuid.uuid4().hex, "upload_id": upload_id, "exam": exam, "status": "pending_distillation", "pipeline_stage": "extract", "next_action": "distill_validate_commit", "distillation_method": "book" if suffix in {".pdf", ".doc", ".docx"} else "direct", "created_at": iso_now()})
        elif classification["category"].endswith("_ingest") or classification["category"] == "module_practice_upload":
            self.state["module_content_queue"].append({"id": uuid.uuid4().hex, "upload_id": upload_id, "exam": exam, "target_module": classification.get("target_module"), "content_kind": classification.get("content_kind"), "status": "draft", "source_status": "user_upload_draft", "created_at": iso_now()})
        if classification.get("target_module") in {"writing", "listening", "reading", "translation", "vocabulary"}:
            self.state.setdefault("memory_candidates", []).append({"id": uuid.uuid4().hex, "upload_id": upload_id, "exam": exam, "module": classification["target_module"], "status": "pending_confirmation", "front": f"资料考点：{original}", "back": "请先确认资料内容和来源，再把其中一个可复习考点写成自己的话。", "created_at": iso_now()})
        self.save()
        return {**item, "queue": queue_item, "pipeline": pipeline}

    def pipeline(self, upload_id: str) -> dict[str, Any]:
        value = str(upload_id).strip()
        item = next((entry for entry in self.state.get("content_pipeline", []) if entry.get("upload_id") == value), None)
        if not item:
            raise KeyError("upload pipeline not found")
        return item

    @staticmethod
    def _set_pipeline_stage(pipeline: dict[str, Any], name: str, status: str, **extra: Any) -> None:
        stage = next((entry for entry in pipeline.get("stages", []) if entry.get("name") == name), None)
        if stage is None:
            stage = {"name": name}
            pipeline.setdefault("stages", []).append(stage)
        stage.update({"status": status, "at": iso_now(), **extra})

    def run_pipeline(self, upload_id: str, action: str = "auto") -> dict[str, Any]:
        """Advance one quarantined upload through the auditable content gates.

        The web adapter deliberately keeps extraction lightweight and never
        promotes an upload to official material.  Full parsers/OCR can be
        attached later without changing the checkpoint contract.
        """
        pipeline = self.pipeline(upload_id)
        upload = next((entry for entry in self.state.get("uploads", []) if entry.get("id") == upload_id), None)
        if not upload:
            raise KeyError("upload not found")
        requested = str(action or "auto").lower()
        allowed = {"auto", "extract", "distill", "validate", "commit"}
        if requested not in allowed:
            raise ValueError("action must be auto, extract, distill, validate or commit")
        classification = upload.get("classification") or {}
        suffix = Path(upload.get("filename", "")).suffix.lower()
        if requested in {"auto", "extract"}:
            preview = str(upload.get("preview", ""))
            if not preview:
                stored = self.quarantine / str(upload.get("stored_name", ""))
                if stored.is_file():
                    preview = extract_preview(upload.get("filename", ""), stored.read_bytes())
            upload["extracted_text"] = _compact_snippet(preview, 10000)
            upload["extract_status"] = "done" if preview else "needs_parser"
            self._set_pipeline_stage(pipeline, "extract", "done" if preview else "blocked", chars=len(preview), parser="preview" if preview else "pending_document_parser")
            pipeline["current_stage"] = "distill" if preview else "extract"
            pipeline["checkpoint"] = f"upload:{upload_id}:extract"
            if requested == "extract" and not preview:
                pipeline["errors"] = ["当前文件没有可安全提取的文本，需接入文档解析/OCR后继续。"]
                self.save()
                return pipeline
        if requested in {"auto", "distill"}:
            text = upload.get("extracted_text", "")
            steps = [line.strip(" -·") for line in re.split(r"[\r\n。；;]+", text) if line.strip()][:12]
            artifact = {
                "artifact_type": "strategy" if classification.get("category") == "strategy_ingest" else "content_extract",
                "title": Path(upload.get("filename", "upload")).stem,
                "content_kind": classification.get("content_kind", "unknown"),
                "text": text,
                "steps": steps,
                "source_provenance": {"upload_id": upload_id, "filename": upload.get("filename"), "sha256": upload.get("sha256"), "source_status": "quarantined"},
                "evidence_roles": ["S", "A", "B", "C", "R"],
            }
            upload["distilled_artifact"] = artifact
            upload["distill_status"] = "done" if text else "blocked"
            self._set_pipeline_stage(pipeline, "distill", "done" if text else "blocked", method="direct" if suffix in {".txt", ".md", ".markdown"} else "preview_only")
            pipeline["current_stage"] = "validate" if text else "distill"
            pipeline["checkpoint"] = f"upload:{upload_id}:distill"
        if requested in {"auto", "validate"}:
            artifact = upload.get("distilled_artifact") or {}
            checks = {
                "has_source_hash": bool(upload.get("sha256")),
                "has_extract": bool(artifact.get("text")),
                "classification_present": bool(classification.get("category")),
                "official_boundary": classification.get("category") != "candidate_official_past_paper" or upload.get("source_status") == "verified_official",
            }
            valid = all(checks.values())
            upload["validation"] = {"status": "passed" if valid else "needs_review", "checks": checks, "standard": "ExamLex evidence-bound artifact gate"}
            self._set_pipeline_stage(pipeline, "validate", "done" if valid else "blocked", checks=checks)
            pipeline["current_stage"] = "commit" if valid else "validate"
            pipeline["checkpoint"] = f"upload:{upload_id}:validate"
        if requested in {"auto", "commit"}:
            validation = upload.get("validation") or {}
            if validation.get("status") != "passed":
                self._set_pipeline_stage(pipeline, "commit", "blocked", reason="validation gate has not passed")
                pipeline["errors"] = ["校验未通过，不能提交入库；请先完成解析、蒸馏和来源核验。"]
            else:
                category = classification.get("category")
                if category == "candidate_official_past_paper" and upload.get("source_status") != "verified_official":
                    self._set_pipeline_stage(pipeline, "commit", "blocked", reason="past paper source is not verified")
                    pipeline["errors"] = ["真题必须先完成来源核验，不能自动进入官方真题。"]
                else:
                    upload["status"] = "committed"
                    queue = next((entry for entry in self.state.get("ingest_queue", []) if entry.get("upload_id") == upload_id), None)
                    if queue:
                        queue["status"] = "committed"
                        queue["committed_at"] = iso_now()
                    for item in self.state.get("simulations", []):
                        if item.get("upload_id") == upload_id:
                            item["status"] = "ready_private"
                    for item in self.state.get("module_content_queue", []):
                        if item.get("upload_id") == upload_id:
                            item["status"] = "ready_private"
                            item["source_status"] = "user_upload"
                    self._set_pipeline_stage(pipeline, "commit", "done", target=classification.get("target"))
                    pipeline["current_stage"] = "complete"
                    pipeline["checkpoint"] = f"upload:{upload_id}:commit"
                    pipeline["errors"] = []
        pipeline["updated_at"] = iso_now()
        self.save()
        return pipeline

    def verify_past_source(self, upload_id: str, evidence_level: str, source_name: str, source_url: str = "", note: str = "") -> dict[str, Any]:
        upload = next((entry for entry in self.state.get("uploads", []) if entry.get("id") == upload_id), None)
        if not upload:
            raise KeyError("upload not found")
        classification = upload.get("classification") or {}
        if classification.get("category") != "candidate_official_past_paper":
            raise ValueError("only a past paper candidate can be source verified")
        level = str(evidence_level or "").upper()
        if level not in {"S", "A"}:
            raise ValueError("official past paper verification requires S or A evidence")
        if not str(source_name).strip() or (level == "A" and not str(source_url).strip()):
            raise ValueError("source name is required; A-level evidence also requires source URL")
        upload["source_status"] = "verified_official"
        upload["source_provenance"] = {"source_name": str(source_name).strip(), "source_url": str(source_url).strip(), "evidence_level": level, "note": str(note).strip()[:500], "verified_at": iso_now()}
        for candidate in self.state.get("past_paper_candidates", []):
            if candidate.get("upload_id") == upload_id:
                candidate.update({"status": "verified_official", "source_status": "verified_official", "source_provenance": upload["source_provenance"]})
        pipeline = self.pipeline(upload_id)
        pipeline["source_provenance"] = upload["source_provenance"]
        pipeline["updated_at"] = iso_now()
        self.save()
        return {"upload": upload, "pipeline": pipeline}

    def source_catalog(self, exam: str | None = None, section: str | None = None) -> dict[str, Any]:
        catalog = load_source_catalog(SOURCE_CATALOG_PATH)
        family = "cet" if str(exam or "").upper() in {"CET4", "CET6"} else "postgraduate" if str(exam or "").upper() == "POSTGRADUATE_ENGLISH" else None
        sources = filter_sources(catalog, exam=family, section=section or None)
        return {"schema_version": catalog.get("schema_version"), "scope": catalog.get("catalog_scope"), "evidence_levels": catalog.get("evidence_levels"), "collection_defaults": catalog.get("collection_defaults"), "sources": sources, "source_count": len(sources), "disclaimer": "题源目录只标记来源证据等级；没有文章级核验的资料不会被当作官方真题。"}

    def artifact_rules(self, exam: str) -> dict[str, Any]:
        value = validate_exam(exam)
        profiles = load_data(ARTIFACT_PROFILES_PATH)
        return {"exam": value, "profiles": profiles.get("profiles", {}).get(value, {}), "validation_standard": "ExamLex comprehensive artifact validation: answer uniqueness, evidence binding, source notes and detailed explanations."}

    def providers(self) -> list[dict[str, Any]]:
        result = []
        for item in self.state["providers"]:
            value = {k: v for k, v in item.items() if k != "api_key"}
            spec = PROVIDERS.get(item.get("provider_id"), {})
            env_name = item.get("api_key_env") or (spec.env_key if spec else "EXAMLEX_CUSTOM_API_KEY")
            value["available"] = bool(os.environ.get(env_name)) and (item.get("provider_id") != "custom" or bool(item.get("endpoint")))
            result.append(value)
        return result

    def retrieve_agent_sources(self, exam: str, module: str | None, query: str = "") -> dict[str, Any]:
        """Build a local lexical RAG result from ExamLex-owned evidence.

        The index is intentionally rebuilt from the read-only content bundle
        and learner state on each request. It avoids a hidden database,
        respects quarantine/source status, and keeps every result traceable.
        """
        value = validate_exam(exam)
        requested_module = str(module or "").strip().lower()
        terms = _search_terms(query)
        candidates: list[dict[str, Any]] = []

        def add(source_id: str, source_type: str, title: str, text: str, source_status: str, source_module: str | None = None) -> None:
            snippet = _compact_snippet(text)
            if not snippet:
                return
            haystack = f"{title} {snippet}".lower()
            overlap = len(terms & _search_terms(haystack))
            scene_bonus = 3 if requested_module and source_module == requested_module else 0
            candidates.append({"source_id": source_id, "source_type": source_type, "title": title, "snippet": snippet, "source_status": source_status, "module": source_module, "_score": overlap * 5 + scene_bonus})

        exam_data = self.content["exams"][value]
        for module_key, module_data in exam_data.get("modules", {}).items():
            for lesson in module_data.get("lessons", []):
                add(f"content:{value}:{lesson.get('id')}", "lesson", lesson.get("title", module_key), f"{module_data.get('overview', '')} {lesson.get('summary', '')} {'；'.join(lesson.get('checkpoints', []))}", module_data.get("source_status", "content_bundle"), module_key)
        for group in self.content.get("shared_basics", {}).get("groups", []):
            add(f"basics:{group.get('id')}", "basics", group.get("title", "基础知识"), "；".join(group.get("items", [])), "available_all_tracks", "basics")
        for card in self.state.get("cards", {}).get(value, []):
            add(f"card:{card.get('id')}", "memory_card", card.get("front", "记忆卡"), f"{card.get('back', '')} {card.get('hint', '')}", card.get("source_kind", "learner_generated"), card.get("module"))
        for record in self.ledger(value)[-40:]:
            add(f"practice:{record.get('id')}", "practice", f"{record.get('module', '练习')} 练习记录", f"正确 {record.get('correct_items', 0)}/{record.get('total_items', 0)}，错误标签：{'、'.join(record.get('error_tags', []))}", "learner_practice", record.get("module"))
        for item in self.state.get("uploads", []):
            if item.get("exam") != value:
                continue
            classification = item.get("classification") or {}
            add(f"upload:{item.get('id')}", "upload", item.get("filename", "上传资料"), item.get("preview", "") or classification.get("note", ""), "quarantined" if item.get("status") == "quarantined" else item.get("status", "user_upload_draft"), classification.get("target_module"))
        for item in self.state.get("strategy_queue", []):
            if item.get("exam") == value:
                add(f"strategy:{item.get('id')}", "strategy", "持续学习方法论", f"状态：{item.get('status')}，下一步：{item.get('next_action')}", "pending_distillation", None)

        candidates.sort(key=lambda item: (-item["_score"], item["source_type"], item["source_id"]))
        results = [{key: item[key] for key in ("source_id", "source_type", "title", "snippet", "source_status", "module")} for item in candidates[:10]]
        return {"query": query[:500], "exam": value, "module": requested_module or None, "results": results, "source_ids": [item["source_id"] for item in results], "total_indexed": len(candidates), "disclaimer": "检索结果仅来自 ExamLex 本地资料与学习记录；quarantined / draft 内容未视为已核验官方资料。"}

    @staticmethod
    def resolve_agent_module(module: str | None, path: str | None = None, input_text: str = "") -> str:
        value = str(module or "").strip().lower()
        if value in MODULES:
            return value
        haystack = f"{path or ''} {input_text}".lower()
        for candidate in ("writing", "listening", "reading", "translation", "vocabulary", "error_review", "planner"):
            aliases = {candidate, {"error_review": "错题", "planner": "计划"}.get(candidate, "")}
            if any(alias and alias in haystack for alias in aliases):
                return candidate
        return "planner"

    def save_provider(self, payload: dict[str, Any]) -> dict[str, Any]:
        provider_id = str(payload.get("provider_id", "")).lower()
        if provider_id not in PROVIDER_IDS:
            raise ValueError("unsupported provider")
        endpoint = str(payload.get("endpoint", "")).strip()
        if endpoint and not (endpoint.startswith("https://") or endpoint.startswith("http://127.0.0.1") or endpoint.startswith("http://localhost")):
            raise ValueError("endpoint must use HTTPS or local development HTTP")
        model = str(payload.get("model", "")).strip()[:120]
        api_key_env = str(payload.get("api_key_env", "")).strip()
        if api_key_env and not re.fullmatch(r"[A-Z][A-Z0-9_]{2,63}", api_key_env):
            raise ValueError("api_key_env must be an environment variable name")
        item = {"provider_id": provider_id, "endpoint": endpoint, "model": model, "api_key_env": api_key_env, "updated_at": iso_now()}
        self.state["providers"] = [existing for existing in self.state["providers"] if existing.get("provider_id") != provider_id]
        self.state["providers"].append(item)
        self.save()
        return item

    def agent_manifest(self) -> list[dict[str, Any]]:
        return [{"id": module, **config} for module, config in MODULES.items()]

    def agent_capabilities(self) -> dict[str, Any]:
        configured = {item.get("provider_id"): item for item in self.providers()}
        models = [{"id": "offline", "label": "ExamLex 本地模式", "level": "基础", "provider": None, "model": None, "available": True, "description": "无需密钥，使用本地证据检索和确定性教练规则。"}]
        for provider_id, spec in PROVIDERS.items():
            if provider_id == "custom":
                continue
            saved = configured.get(provider_id, {})
            env_name = saved.get("api_key_env") or spec.env_key
            models.append({"id": provider_id, "label": provider_id.upper(), "level": "增强", "provider": provider_id, "model": saved.get("model") or spec.model, "available": bool(os.environ.get(env_name)), "description": f"使用 {env_name} 环境变量中的 API Key；未配置时自动回退本地模式。"})
        custom = configured.get("custom")
        if custom:
            env_name = custom.get("api_key_env") or "EXAMLEX_CUSTOM_API_KEY"
            models.append({"id": "custom", "label": "自定义中转", "level": "增强", "provider": "custom", "model": custom.get("model") or "custom-model", "available": bool(custom.get("endpoint")) and bool(os.environ.get(env_name)), "description": f"使用已保存的 endpoint 和 {env_name} 环境变量；未配置时自动回退本地模式。"})
        return {"default_mode": "offline", "models": models, "rag": {"enabled": True, "scope": ["exam_content", "shared_basics", "practice", "memory_cards", "uploads", "strategy_queue"], "max_results": 10}, "prompt_library": prompt_library_stats()}

    def run_agent(self, payload: dict[str, Any]) -> dict[str, Any]:
        exam = validate_exam(payload.get("exam"))
        module = self.resolve_agent_module(payload.get("module"), payload.get("path"), str(payload.get("input", payload.get("input_text", ""))))
        context = payload.get("context") if isinstance(payload.get("context"), dict) else {}
        rag = self.retrieve_agent_sources(exam, module, str(payload.get("input", payload.get("input_text", ""))))
        explicit_sources = [str(item) for item in (payload.get("source_ids") or []) if str(item).strip()]
        rag["source_ids"] = list(dict.fromkeys(explicit_sources + rag["source_ids"]))
        context = {**context, "rag": rag, "source_ids": rag["source_ids"]}
        provider_id = str(payload.get("provider", "")).strip().lower() or None
        saved_provider = next((item for item in self.state.get("providers", []) if item.get("provider_id") == provider_id), {})
        result = run_agent(
            module=module,
            exam=exam,
            input_text=str(payload.get("input", payload.get("input_text", ""))),
            context=context,
            provider=provider_id,
            model=str(payload.get("model", "")).strip() or None,
            api_key_env=saved_provider.get("api_key_env") or None,
            endpoint=saved_provider.get("endpoint") or None,
            use_model=bool(payload.get("use_model", False)),
        )
        record = {**result, "scene": module, "rag": rag, "created_at": iso_now()}
        self.state.setdefault("agent_runs", []).append(record)
        self.state["agent_runs"] = self.state["agent_runs"][-100:]
        self.save()
        return record

    def agent_runs(self, exam: str, module: str | None = None) -> list[dict[str, Any]]:
        return [item for item in self.state.get("agent_runs", []) if item.get("exam") == exam and (not module or item.get("module") == module)]

    def heatmap_year(self, exam: str, year: int | None = None) -> dict[str, Any]:
        value = int(year or datetime.now().astimezone().year)
        days: list[dict[str, Any]] = []
        for month in range(1, 13):
            days.extend(self.heatmap(value, month, exam)["days"])
        return {"exam": exam, "year": value, "days": days, "start_weekday": date(value, 1, 1).weekday(), "total_minutes": sum(item["minutes"] for item in days), "active_days": sum(1 for item in days if item["score"] > 0), "legend": [{"level": i, "label": label} for i, label in enumerate(["无记录", "起步", "稳定", "集中", "高强度"])], "history_years": sorted({int(day[:4]) for day in self.state["activity"] if str(day)[:4].isdigit()})}

    def record_focus(self, payload: dict[str, Any]) -> dict[str, Any]:
        exam = validate_exam(payload.get("exam"))
        raw_seconds = payload.get("duration_seconds")
        if raw_seconds is None:
            raw_seconds = int(payload.get("minutes", 0)) * 60
        seconds = int(raw_seconds)
        if seconds < 60 or seconds > 8 * 60 * 60:
            raise ValueError("duration_seconds must be between 60 and 28800")
        minutes = seconds // 60
        day = str(payload.get("date") or today_local())
        date.fromisoformat(day)
        if day > today_local():
            raise ValueError("future focus dates are not accepted")
        record = {"id": uuid.uuid4().hex, "exam": exam, "minutes": minutes, "duration_seconds": seconds, "module": str(payload.get("module", "focus")).strip() or "focus", "planned_minutes": max(0, int(payload.get("planned_minutes", 0))), "completed": bool(payload.get("completed", False)), "date": day, "created_at": iso_now()}
        self.state.setdefault("focus_sessions", []).append(record)
        self.add_activity(day, exam=exam, minutes=minutes, sessions=1)
        self.save()
        return record


class ExamLexHandler(BaseHTTPRequestHandler):
    server_version = "ExamLexLocal/1.0"

    @property
    def store(self) -> WebStore:
        return self.server.store  # type: ignore[attr-defined]

    def log_message(self, format: str, *args: Any) -> None:
        return

    def send_json(self, value: Any, status: int = HTTPStatus.OK) -> None:
        payload = json.dumps(value, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Cache-Control", "no-store")
        self.send_header("X-Content-Type-Options", "nosniff")
        self.send_header("X-Frame-Options", "DENY")
        self.send_header("Content-Length", str(len(payload)))
        self.end_headers()
        self.wfile.write(payload)

    def error(self, status: int, message: str) -> None:
        self.send_json({"error": message}, status)

    def do_GET(self) -> None:  # noqa: N802
        parsed = urlparse(self.path)
        path = unquote(parsed.path)
        query = parse_qs(parsed.query)
        try:
            if path == "/api/health":
                return self.send_json({"ok": True, "service": "examlex-web", "schema_version": 1, "storage": "ready", "private_mode": True, "source_index": "not_exposed", "background_capabilities": ["source-collection", "video-processing", "backup-restore"]})
            if path == "/api/exams":
                return self.send_json({"exam_order": self.store.content["exam_order"], "exams": self.store.exams()})
            if path == "/api/bootstrap":
                exam = validate_exam(query.get("exam", ["CET4"])[0])
                year, month = requested_month(query)
                return self.send_json({"exam": exam, "exam_info": self.store.exam(exam), "shared_basics": self.store.content["shared_basics"], "tasks": self.store.tasks_for(exam), "cards": self.store.due_cards(exam), "ribbon": self.store.ribbon(exam), "summary": self.store.summary(exam, year, month), "providers": self.store.providers()})
            if path == "/api/content":
                exam = validate_exam(query.get("exam", ["CET4"])[0])
                module = query.get("module", [""])[0]
                modules = self.store.exam(exam)["modules"]
                if module and module not in modules:
                    return self.error(HTTPStatus.NOT_FOUND, "module not found")
                return self.send_json({"exam": exam, "modules": modules if not module else {module: modules[module]}})
            if path == "/api/heatmap":
                exam = validate_exam(query.get("exam", ["CET4"])[0])
                year, month = requested_month(query)
                return self.send_json(self.store.heatmap(year, month, exam))
            if path == "/api/heatmap/year":
                exam = validate_exam(query.get("exam", ["CET4"])[0])
                try:
                    year = int(query.get("year", [str(datetime.now().astimezone().year)])[0])
                except (TypeError, ValueError):
                    year = datetime.now().astimezone().year
                if year < 2000 or year > 2100:
                    return self.error(HTTPStatus.BAD_REQUEST, "year must be between 2000 and 2100")
                return self.send_json(self.store.heatmap_year(exam, year))
            if path == "/api/memory-cards":
                exam = validate_exam(query.get("exam", ["CET4"])[0])
                include_future = query.get("all", ["0"])[0] == "1"
                return self.send_json({"exam": exam, "cards": self.store.due_cards(exam, include_future=include_future), "candidates": [item for item in self.store.state.get("memory_candidates", []) if item.get("exam") == exam]})
            if path == "/api/ribbon":
                exam = validate_exam(query.get("exam", ["CET4"])[0])
                return self.send_json({"exam": exam, "nodes": self.store.ribbon(exam)})
            if path == "/api/profile":
                exam = validate_exam(query.get("exam", ["CET4"])[0])
                self.store.ensure_exam_state(exam)
                return self.send_json({"profile": self.store.state["profiles"][exam]})
            if path == "/api/plan":
                exam = validate_exam(query.get("exam", ["CET4"])[0])
                return self.send_json(self.store.plan(exam))
            if path == "/api/profile/diagnosis":
                exam = validate_exam(query.get("exam", ["CET4"])[0])
                return self.send_json(self.store.profile_diagnosis(exam))
            if path == "/api/plans":
                exam = validate_exam(query.get("exam", ["CET4"])[0])
                return self.send_json(self.store.period_plan(exam, query.get("period", ["day"])[0]))
            if path == "/api/errors":
                exam = validate_exam(query.get("exam", ["CET4"])[0])
                return self.send_json(self.store.error_summary(exam))
            if path == "/api/node-analysis":
                exam = validate_exam(query.get("exam", ["CET4"])[0])
                return self.send_json(self.store.node_analysis(exam, query.get("module", [None])[0]))
            if path == "/api/trends":
                exam = validate_exam(query.get("exam", ["CET4"])[0])
                period = query.get("period", ["month"])[0]
                return self.send_json({"exam": exam, **analyze_trends(ledger=self.store.ledger(exam)), "specialized": self.store.module_trends(exam, period)})
            if path == "/api/trends/specialized":
                exam = validate_exam(query.get("exam", ["CET4"])[0])
                return self.send_json(self.store.module_trends(exam, query.get("period", ["month"])[0]))
            if path == "/api/practice/records":
                exam = validate_exam(query.get("exam", ["CET4"])[0])
                kind = query.get("kind", ["all"])[0]
                return self.send_json({"exam": exam, "kind": kind, "records": self.store.practice_records(exam, kind)})
            if path == "/api/uploads":
                exam = validate_exam(query.get("exam", ["CET4"])[0])
                uploads = [item for item in self.store.state["uploads"] if item.get("exam") == exam]
                upload_by_id = {item.get("id"): item for item in uploads}
                candidates = []
                for item in self.store.state["past_paper_candidates"]:
                    if item.get("exam") != exam:
                        continue
                    value = dict(item)
                    source = upload_by_id.get(item.get("upload_id"), {})
                    value.setdefault("filename", source.get("filename"))
                    value.setdefault("module", (source.get("classification") or {}).get("target_module"))
                    candidates.append(value)
                simulations = []
                for item in self.store.state["simulations"]:
                    if item.get("exam") != exam:
                        continue
                    value = dict(item)
                    source = upload_by_id.get(item.get("upload_id"), {})
                    value.setdefault("filename", source.get("filename"))
                    value.setdefault("module", (source.get("classification") or {}).get("target_module") or "reading")
                    simulations.append(value)
                return self.send_json({"exam": exam, "uploads": uploads, "queue": [item for item in self.store.state["ingest_queue"] if item.get("exam") == exam], "pipelines": [item for item in self.store.state.get("content_pipeline", []) if item.get("exam") == exam], "past_paper_candidates": candidates, "simulations": simulations, "vocabulary_sources": [item for item in self.store.state["vocabulary_sources"] if item.get("exam") == exam], "strategy_queue": [item for item in self.store.state["strategy_queue"] if item.get("exam") == exam], "module_content_queue": [item for item in self.store.state.get("module_content_queue", []) if item.get("exam") == exam]})
            if path == "/api/pipeline":
                upload_id = query.get("upload_id", [""])[0]
                return self.send_json({"pipeline": self.store.pipeline(upload_id)})
            if path == "/api/sources/catalog":
                exam = query.get("exam", [None])[0]
                return self.send_json(self.store.source_catalog(exam, query.get("section", [None])[0]))
            if path == "/api/artifacts/rules":
                exam = validate_exam(query.get("exam", ["CET4"])[0])
                return self.send_json(self.store.artifact_rules(exam))
            if path == "/api/summary":
                exam = validate_exam(query.get("exam", ["CET4"])[0])
                year, month = requested_month(query)
                return self.send_json(self.store.summary(exam, year, month))
            if path == "/api/summary/ai":
                exam = validate_exam(query.get("exam", ["CET4"])[0])
                return self.send_json(self.store.ai_summary(exam, query.get("date", [today_local()])[0]))
            if path == "/api/achievements":
                return self.send_json({"rank": "青铜·起步", "streak": 0, "badges": [{"id": "first-route", "title": "第一次完成路线", "unlocked": False}, {"id": "seven-days", "title": "连续七日", "unlocked": False}, {"id": "source-trace", "title": "证据回溯", "unlocked": False}]})
            if path == "/api/agent/manifest":
                return self.send_json({"agents": self.store.agent_manifest(), "capabilities": self.store.agent_capabilities(), "runtime": "langgraph_optional", "offline_mode": True})
            if path == "/api/agent/context":
                exam = validate_exam(query.get("exam", ["CET4"])[0])
                module = query.get("module", [None])[0]
                search = query.get("q", [""])[0]
                return self.send_json(self.store.retrieve_agent_sources(exam, module, search))
            if path == "/api/agent/prompts":
                module = self.store.resolve_agent_module(query.get("module", [None])[0])
                return self.send_json({"module": module, "prompts": prompt_templates_for(module), "library": prompt_library_stats()})
            if path == "/api/agent/runs":
                exam = validate_exam(query.get("exam", ["CET4"])[0])
                return self.send_json({"exam": exam, "runs": self.store.agent_runs(exam, query.get("module", [None])[0])[-50:]})
            if path == "/api/practice/session":
                return self.error(HTTPStatus.METHOD_NOT_ALLOWED, "use POST to create a practice session")
            if path.startswith("/api/providers"):
                return self.send_json({"providers": self.store.providers()})
            return self.serve_static(path)
        except ValueError as exc:
            return self.error(HTTPStatus.BAD_REQUEST, str(exc))
        except KeyError as exc:
            return self.error(HTTPStatus.NOT_FOUND, str(exc).strip("'"))
        except Exception as exc:  # pragma: no cover - final boundary
            return self.error(HTTPStatus.INTERNAL_SERVER_ERROR, str(exc))

    def do_POST(self) -> None:  # noqa: N802
        parsed = urlparse(self.path)
        path = unquote(parsed.path)
        try:
            if path == "/api/tasks/toggle":
                body = safe_json_body(self)
                exam = validate_exam(body.get("exam"))
                with self.store._lock:
                    task = self.store.toggle_task(exam, str(body.get("task_id", "")), body.get("done"))
                return self.send_json({"task": task, "summary": self.store.summary(exam, *requested_month({}))})
            if path == "/api/practice/record":
                body = safe_json_body(self)
                with self.store._lock:
                    record = self.store.record_practice(body)
                return self.send_json({"record": record, "summary": self.store.summary(record["exam"], *requested_month({}))}, HTTPStatus.CREATED)
            if path == "/api/practice/session":
                with self.store._lock:
                    session = self.store.create_practice_session(safe_json_body(self))
                return self.send_json({"session": session}, HTTPStatus.CREATED)
            if path == "/api/practice/session/submit":
                with self.store._lock:
                    result = self.store.submit_practice_session(safe_json_body(self))
                return self.send_json(result)
            if path == "/api/practice/session/timeout":
                with self.store._lock:
                    result = self.store.continue_after_timeout(safe_json_body(self))
                return self.send_json(result)
            if path == "/api/focus/session":
                with self.store._lock:
                    record = self.store.record_focus(safe_json_body(self))
                return self.send_json({"session": record, "summary": self.store.summary(record["exam"], *requested_month({}))}, HTTPStatus.CREATED)
            if path == "/api/profile":
                with self.store._lock:
                    profile = self.store.save_profile(safe_json_body(self))
                return self.send_json({"profile": profile})
            if path == "/api/memory/review":
                body = safe_json_body(self)
                exam = validate_exam(body.get("exam"))
                with self.store._lock:
                    result = self.store.review_card(exam, str(body.get("card_id", "")), str(body.get("rating", "")), body.get("idempotency_key"))
                return self.send_json(result)
            if path == "/api/memory-cards/confirm":
                body = safe_json_body(self)
                exam = validate_exam(body.get("exam"))
                with self.store._lock:
                    card = self.store.confirm_memory_candidate(str(body.get("upload_id", "")), exam)
                return self.send_json({"card": card}, HTTPStatus.CREATED)
            if path == "/api/providers":
                with self.store._lock:
                    provider = self.store.save_provider(safe_json_body(self))
                return self.send_json({"provider": provider})
            if path == "/api/upload":
                return self.handle_upload()
            if path == "/api/pipeline/run":
                body = safe_json_body(self)
                with self.store._lock:
                    pipeline = self.store.run_pipeline(str(body.get("upload_id", "")), str(body.get("action", "auto")))
                return self.send_json({"pipeline": pipeline})
            if path == "/api/pipeline/verify":
                body = safe_json_body(self)
                with self.store._lock:
                    result = self.store.verify_past_source(str(body.get("upload_id", "")), str(body.get("evidence_level", "")), str(body.get("source_name", "")), str(body.get("source_url", "")), str(body.get("note", "")))
                return self.send_json(result)
            if path == "/api/agent/run":
                with self.store._lock:
                    result = self.store.run_agent(safe_json_body(self))
                return self.send_json({"run": result})
            return self.error(HTTPStatus.NOT_FOUND, "unknown endpoint")
        except (ValueError, json.JSONDecodeError) as exc:
            return self.error(HTTPStatus.BAD_REQUEST, str(exc))
        except KeyError as exc:
            return self.error(HTTPStatus.NOT_FOUND, str(exc).strip("'"))
        except Exception as exc:  # pragma: no cover - final boundary
            return self.error(HTTPStatus.INTERNAL_SERVER_ERROR, str(exc))

    def handle_upload(self) -> None:
        content_type = self.headers.get("Content-Type", "")
        if not content_type.startswith("multipart/form-data"):
            return self.error(HTTPStatus.BAD_REQUEST, "upload requires multipart/form-data")
        length = int(self.headers.get("Content-Length", "0"))
        if length <= 0 or length > MAX_UPLOAD_BYTES + 1024 * 1024:
            return self.error(HTTPStatus.BAD_REQUEST, "invalid upload size")
        raw = self.rfile.read(length)
        message = BytesParser(policy=default).parsebytes(b"Content-Type: " + content_type.encode() + b"\r\n\r\n" + raw)
        query = parse_qs(urlparse(self.path).query)
        exam = validate_exam(query.get("exam", ["CET4"])[0])
        module_hint = query.get("module", [None])[0]
        for part in message.iter_parts():
            if part.get_filename() is None:
                continue
            filename = part.get_filename()
            with self.store._lock:
                item = self.store.upload(filename, part.get_payload(decode=True) or b"", part.get_content_type(), exam, module_hint)
            return self.send_json({"upload": item}, HTTPStatus.CREATED)
        return self.error(HTTPStatus.BAD_REQUEST, "file field is required")

    def serve_static(self, path: str) -> None:
        relative = "index.html" if path in {"", "/"} else path.lstrip("/")
        target = (WEB_ROOT / relative).resolve()
        if WEB_ROOT.resolve() not in target.parents and target != WEB_ROOT.resolve():
            return self.error(HTTPStatus.NOT_FOUND, "not found")
        if not target.is_file():
            return self.error(HTTPStatus.NOT_FOUND, "not found")
        data = target.read_bytes()
        self.send_response(HTTPStatus.OK)
        self.send_header("Content-Type", mimetypes.guess_type(target.name)[0] or "application/octet-stream")
        self.send_header("Content-Security-Policy", "default-src 'self'; img-src 'self' data:; connect-src 'self'; style-src 'self' 'unsafe-inline'; script-src 'self'; frame-ancestors 'none'")
        self.send_header("X-Content-Type-Options", "nosniff")
        self.send_header("X-Frame-Options", "DENY")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)


class ExamLexHTTPServer(ThreadingHTTPServer):
    allow_reuse_address = True

    def __init__(self, address: tuple[str, int], store: WebStore):
        super().__init__(address, ExamLexHandler)
        self.store = store


def create_server(host: str = "127.0.0.1", port: int = 8765, data_dir: str | Path | None = None) -> ExamLexHTTPServer:
    return ExamLexHTTPServer((host, port), WebStore(data_dir))


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Run the local ExamLex web workspace.")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8765)
    parser.add_argument("--data-dir", default=None)
    args = parser.parse_args(argv)
    server = create_server(args.host, args.port, args.data_dir)
    print(f"ExamLex web workspace: http://{args.host}:{server.server_port}/")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
