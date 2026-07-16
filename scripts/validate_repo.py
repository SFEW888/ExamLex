from __future__ import annotations

import argparse
import ast
import hashlib
import json
import os
import re
import subprocess
from dataclasses import asdict, dataclass, field
from pathlib import Path
from urllib.parse import unquote, urlsplit, urlunsplit


SKILL_NAME = "examlex"
IMPORTABLE_NAME = "examlex"
LEGACY_IDENTIFIERS = (
    "english" + "-exam-ai-tutor",
    "english" + "_exam_ai_tutor",
    "english" + "-exam-tutor",
    "ENGLISH" + "_EXAM_TUTOR",
    "TUTOR" + "_YTDLP_COOKIES_FROM_BROWSER",
    "tutor" + " backup",
    "tutor" + " cron-create",
)
SKILL_ALIASES = {
    "culture-guide",
    "grammar-corrector",
    "learning-planner",
    "polish-wizard",
    "reading-navigator",
    "scenario-dialog",
    "structure-planner",
    "vocabulary-builder",
}
FORBIDDEN_PRIVATE_PROMPT = " ".join(("Act as a strict", "but helpful English", "grammar teacher"))
MARKDOWN_LINK_RE = re.compile(r"!?\[[^\]]*\]\(([^)\n]+)\)")
EXTERNAL_URL_RE = re.compile(r"https?://[A-Za-z0-9._~:/?#@!$&*+,;=%-]+")
REPOSITORY_URL = "https://github.com/SFEW888/ExamLex"
ALLOWED_EXTERNAL_URLS = {
    REPOSITORY_URL,
    f"{REPOSITORY_URL}.git",
    f"{REPOSITORY_URL}/issues",
    "https://github.com/yt-dlp/yt-dlp",
    "https://ffmpeg.org/download.html",
    "https://github.com/openai/whisper",
    "https://poppler.freedesktop.org/",
    "https://calibre-ebook.com/download",
}
README_BADGE_URLS = {
    f"{REPOSITORY_URL}/actions/workflows/ci.yml",
    f"{REPOSITORY_URL}/actions/workflows/ci.yml/badge.svg",
    f"{REPOSITORY_URL}/actions/workflows/codeql.yml",
    f"{REPOSITORY_URL}/actions/workflows/codeql.yml/badge.svg",
    "https://img.shields.io/badge/License-MIT-yellow.svg",
    "https://img.shields.io/badge/Python-3.10--3.13-blue.svg",
    "https://img.shields.io/badge/Platforms-4-blue.svg",
    "https://img.shields.io/badge/Skills-9-brightgreen.svg",
    "https://www.python.org/",
}
README_BADGE_PATHS = {
    Path("README.md"),
    Path("zh-CN/README.md"),
}
EXPECTED_REFERENCES = {
    "assistant-roster.md",
    "data-model.md",
    "error-taxonomy.md",
    "exam-profiles.md",
    "prompt-modes.md",
    "source-collection.md",
    "tutor-runtime.md",
    "workflow.md",
}
TUTOR_ROLE_CONTRACT_FILENAME = "tutor-role-contracts.json"
EXPECTED_TUTOR_ROLE_PLACEHOLDERS = {
    "study-planner": "[PRIVATE_PROMPT_PLACEHOLDER: study-planner]",
    "vocabulary-expander": "[PRIVATE_PROMPT_PLACEHOLDER: vocabulary-expander]",
    "reading-navigator": "[PRIVATE_PROMPT_PLACEHOLDER: reading-navigator]",
    "structure-planner": "[PRIVATE_PROMPT_PLACEHOLDER: structure-planner]",
    "grammar-corrector": "[PRIVATE_PROMPT_PLACEHOLDER: grammar-corrector]",
    "polishing-editor": "[PRIVATE_PROMPT_PLACEHOLDER: polishing-editor]",
    "situational-dialogue": "[PRIVATE_PROMPT_PLACEHOLDER: situational-dialogue]",
    "culture-guide": "[PRIVATE_PROMPT_PLACEHOLDER: culture-guide]",
}
TUTOR_ROLE_REQUIRED_LIST_FIELDS = {
    "capabilities",
    "workflow",
    "output_contract",
    "boundaries",
}
PRIVATE_PROMPT_DIRECTORY_NAMES = {".examlex-private", "private-prompts"}
EXPECTED_AUTOMATION_SCRIPTS = {
    "analyze_trends.py",
    "backup_data.py",
    "cleanup_sessions.py",
    "common.py",
    "generate_daily_plan.py",
    "ingest_strategy.py",
    "list_strategies.py",
    "manage_writing_versions.py",
    "record_practice.py",
    "score_writing_rubric.py",
    "monitor_capacity.py",
    "strategy_database.py",
    "strategy_sqlite.py",
    "summarize_errors.py",
    "tag_error.py",
    "update_ability_profile.py",
    "validate_exam_artifact.py",
    "validate_strategy.py",
    "validate_profile.py",
    "vocabulary_block.py",
}
EXPECTED_GITHUB_HEALTH_FILES = {
    "CODE_OF_CONDUCT.md",
    "CONTRIBUTING.md",
    "SECURITY.md",
}
EXPECTED_GITHUB_ISSUE_TEMPLATES = {
    ".github/ISSUE_TEMPLATE/bug_report.yml",
    ".github/ISSUE_TEMPLATE/feature_request.yml",
    ".github/ISSUE_TEMPLATE/question.yml",
}
EXPECTED_GITHUB_WORKFLOWS = {
    ".github/workflows/codeql.yml",
    ".github/workflows/ci.yml",
}
EXPECTED_PROJECT_QUALITY_FILES = {
    ".editorconfig",
    ".env.example",
    ".gitattributes",
    ".secrets.baseline",
}
EXPECTED_QUALITY_DOCS = {
    "docs/configuration.md",
    "docs/development.md",
    "docs/getting-started.md",
    "docs/release.md",
    "docs/troubleshooting.md",
}
EXPECTED_README_SECTIONS = {
    "## Features",
    "## Requirements",
    "## Quick Start",
    "## Configuration",
    "## Usage",
    "## Repository Layout",
    "## Testing And Validation",
    "## Contributing",
    "## License",
}
EXPECTED_README_SKILL_INSTALL_MARKERS = {
    "git clone https://github.com/SFEW888/ExamLex.git",
    "git+https://github.com/SFEW888/ExamLex.git",
    "python -m pip install -e .",
    "install.sh",
    "install.ps1",
    "skills\\examlex",
}
EXPECTED_README_AGENT_CALL_MARKERS = {
    "/examlex",
    "/grammar-corrector",
    "/learning-planner",
}
FORBIDDEN_AGENT_CALL_MARKERS = {
    "$" + "examlex",
    "$" + "grammar-corrector",
    "$" + "learning-planner",
    "$" + "vocabulary-builder",
    "$" + "reading-navigator",
    "$" + "structure-planner",
    "$" + "polish-wizard",
    "$" + "scenario-dialog",
    "$" + "culture-guide",
}
PUBLIC_SAFETY_PATTERNS = {
    "Windows user-home path": re.compile(
        r"(?i)(?<![A-Za-z0-9_])[A-Z]:[\\/]Users[\\/][^\\/\s\"']+"
    ),
    "POSIX user-home path": re.compile(
        r"(?<![A-Za-z0-9_])/(?:home|Users)/[^/\s\"']+"
    ),
    "local Git worktree path": re.compile(
        r"(?i)(?:[A-Z]:)?(?:[^\r\n\"']*[\\/])?\.worktrees[\\/][^\s\"']+"
    ),
    "credential-bearing proxy URL": re.compile(
        r"(?i)\b(?:https?|socks5h?)://[^\s/:@]+:[^\s/@]+@[^\s/]+"
    ),
    "private key material": re.compile(
        r"-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----"
    ),
    "GitHub access token": re.compile(
        r"\b(?:github_pat_[A-Za-z0-9_]{20,}|gh[pousr]_[A-Za-z0-9]{20,})\b"
    ),
    "AWS access key": re.compile(r"\bAKIA[A-Z0-9]{16}\b"),
    "API key": re.compile(r"\bsk-[A-Za-z0-9_-]{16,}\b"),
}
PUBLIC_SAFETY_PLACEHOLDER_MARKERS = (
    "example",
    "dummy",
    "placeholder",
    "replace",
    "changeme",
    "your-",
    "test",
)
LEARNER_ARTIFACT_NAMES = {
    "ability-history.json",
    "ability-profile.json",
    "daily-plan.json",
    "error-summary.json",
    "learner-profile.json",
    "practice-ledger.json",
    "progress-report.html",
    "strategy-library.json",
    "writing-versions.json",
}
LEARNER_ARTIFACT_ALLOWED_PARTS = {"examples", "fixtures", "templates"}
LOCAL_DATA_DIRECTORY_NAMES = {"learner-data", "source-corpus"}
BACKUP_ARTIFACT_RE = re.compile(r"^backup-.+\.tar\.gz(?:\.sha256)?$")


@dataclass
class ValidationResult:
    root: str
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)

    @property
    def ok(self) -> bool:
        return not self.errors


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def validate_tracked_learner_artifacts(
    root: Path,
    errors: list[str],
    tracked_files: list[str] | None = None,
) -> None:
    """Reject tracked learner data while allowing maintained sample resources."""
    root = Path(root).resolve()
    if tracked_files is None:
        if not (root / ".git").exists():
            return
        try:
            completed = subprocess.run(
                ["git", "-C", str(root), "ls-files", "-z"],
                check=True,
                capture_output=True,
                text=True,
            )
        except (OSError, subprocess.CalledProcessError) as exc:
            errors.append(f"Could not inspect tracked learner artifacts: {exc}")
            return
        tracked_files = [path for path in completed.stdout.split("\0") if path]

    for tracked in tracked_files:
        relative = Path(tracked.replace("\\", "/"))
        parts = set(relative.parts)
        if parts.intersection(LEARNER_ARTIFACT_ALLOWED_PARTS):
            continue
        name = relative.name
        is_private_directory = bool(relative.parts) and relative.parts[0] in LOCAL_DATA_DIRECTORY_NAMES
        is_standard_name = name in LEARNER_ARTIFACT_NAMES
        is_backup = BACKUP_ARTIFACT_RE.fullmatch(name) is not None
        is_sidecar = name.endswith((".bak", ".lock", ".tmp"))
        if is_private_directory or is_standard_name or is_backup or is_sidecar:
            errors.append(f"tracked learner artifact is forbidden: {relative.as_posix()}")


def validate_tracked_private_prompt_assets(
    root: Path,
    errors: list[str],
    tracked_files: list[str] | None = None,
) -> None:
    """Reject tracked external private prompt directories."""
    root = Path(root).resolve()
    if tracked_files is None:
        if not (root / ".git").exists():
            return
        try:
            completed = subprocess.run(
                ["git", "-C", str(root), "ls-files", "-z"],
                check=True,
                capture_output=True,
                text=True,
            )
        except (OSError, subprocess.CalledProcessError) as exc:
            errors.append(f"Could not inspect tracked private prompt assets: {exc}")
            return
        tracked_files = [path for path in completed.stdout.split("\0") if path]

    for tracked in tracked_files:
        relative = Path(tracked.replace("\\", "/"))
        if relative.parts and relative.parts[0] in PRIVATE_PROMPT_DIRECTORY_NAMES:
            errors.append(
                f"tracked private prompt asset is forbidden: {relative.as_posix()}"
            )


def validate_tutor_role_contracts(root: Path, errors: list[str]) -> None:
    """Validate the canonical public-safe contract for exactly eight tutor roles."""
    contract_path = (
        Path(root)
        / "skills"
        / SKILL_NAME
        / "references"
        / TUTOR_ROLE_CONTRACT_FILENAME
    )
    if not contract_path.is_file():
        errors.append(
            "Missing required reference: "
            f"references/{TUTOR_ROLE_CONTRACT_FILENAME}"
        )
        return
    try:
        document = json.loads(contract_path.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        errors.append(f"Tutor role contract is not valid UTF-8 JSON: {exc}")
        return
    if not isinstance(document, dict):
        errors.append("Tutor role contract root must be an object.")
        return
    if document.get("schema_version") != "1.0":
        errors.append("Tutor role contract schema_version must be 1.0.")
    if document.get("mode") != "public-safe":
        errors.append("Tutor role contract mode must remain public-safe.")

    roles = document.get("roles")
    if not isinstance(roles, list):
        errors.append("Tutor role contract roles must be an array.")
        return
    if len(roles) != len(EXPECTED_TUTOR_ROLE_PLACEHOLDERS):
        errors.append("Tutor role contract must contain exactly eight roles.")

    seen: set[str] = set()
    for role in roles:
        if not isinstance(role, dict):
            errors.append("Each tutor role contract must be an object.")
            continue
        role_id = role.get("role_id")
        if not isinstance(role_id, str) or role_id not in EXPECTED_TUTOR_ROLE_PLACEHOLDERS:
            errors.append(f"Tutor role contract has unknown role_id: {role_id}")
            continue
        if role_id in seen:
            errors.append(f"Tutor role contract has duplicate role_id: {role_id}")
            continue
        seen.add(role_id)
        if role.get("placeholder") != EXPECTED_TUTOR_ROLE_PLACEHOLDERS[role_id]:
            errors.append(f"Tutor role contract placeholder mismatch: {role_id}")
        for field_name in ("display_name", "mission"):
            value = role.get(field_name)
            if not isinstance(value, str) or not value.strip():
                errors.append(
                    f"Tutor role contract {role_id} requires non-empty {field_name}."
                )
        for field_name in sorted(TUTOR_ROLE_REQUIRED_LIST_FIELDS):
            value = role.get(field_name)
            if (
                not isinstance(value, list)
                or not value
                or any(not isinstance(item, str) or not item.strip() for item in value)
            ):
                errors.append(
                    f"Tutor role contract {role_id} requires non-empty {field_name}."
                )

    missing = sorted(EXPECTED_TUTOR_ROLE_PLACEHOLDERS.keys() - seen)
    if missing:
        errors.append("Tutor role contract is missing roles: " + ", ".join(missing))


def _normalize_external_url(url: str) -> str:
    parts = urlsplit(url)
    return urlunsplit(
        (parts.scheme.lower(), parts.netloc.lower(), parts.path, parts.query, parts.fragment)
    )


def extract_external_urls(text: str) -> set[str]:
    urls: set[str] = set()
    for match in EXTERNAL_URL_RE.finditer(text):
        candidate = match.group(0).rstrip(").,;:!?]}`")
        if candidate:
            urls.add(_normalize_external_url(candidate))
    return urls


def parse_front_matter(text: str) -> dict[str, str]:
    text = text.lstrip("\ufeff")
    if not text.startswith("---\n"):
        return {}
    end = text.find("\n---", 4)
    if end == -1:
        return {}
    metadata: dict[str, str] = {}
    for line in text[4:end].splitlines():
        if ":" not in line:
            continue
        key, value = line.split(":", 1)
        metadata[key.strip()] = value.strip().strip("'\"")
    return metadata


def read_pyproject_prompt_mode(pyproject: Path) -> str | None:
    if not pyproject.exists():
        return None
    text = pyproject.read_text(encoding="utf-8")
    match = re.search(r'^\s*prompt-mode\s*=\s*["\']([^"\']+)["\']', text, flags=re.MULTILINE)
    return match.group(1) if match else None


def literal_dict_assignment(source: str, name: str) -> dict[str, object] | None:
    tree = ast.parse(source)
    for node in tree.body:
        if isinstance(node, ast.Assign):
            if any(isinstance(target, ast.Name) and target.id == name for target in node.targets):
                value = ast.literal_eval(node.value)
                return value if isinstance(value, dict) else None
    return None


def validate_writing_article_omission(common_path: Path, errors: list[str]) -> None:
    if not common_path.exists():
        errors.append(f"Missing common.py for invariant check: {common_path}")
        return
    source = common_path.read_text(encoding="utf-8")
    try:
        mapping = literal_dict_assignment(source, "ERROR_TAG_TO_ABILITY")
    except (SyntaxError, ValueError) as exc:
        errors.append(f"Could not parse ERROR_TAG_TO_ABILITY in {common_path}: {exc}")
        return
    if mapping is None:
        errors.append("ERROR_TAG_TO_ABILITY is missing from common.py.")
        return
    omission = mapping.get("WRITING_ARTICLE_OMISSION")
    language_accuracy = mapping.get("WRITING_LANGUAGE_ACCURACY_FAIL")
    if omission is None:
        errors.append("WRITING_ARTICLE_OMISSION is missing from ERROR_TAG_TO_ABILITY.")
        return
    if not isinstance(omission, tuple) or len(omission) != 2 or omission[0] != "writing":
        errors.append("WRITING_ARTICLE_OMISSION must map to the writing module.")
    if language_accuracy is not None and omission != language_accuracy:
        errors.append("WRITING_ARTICLE_OMISSION must map to the same writing/language accuracy ability as WRITING_LANGUAGE_ACCURACY_FAIL.")


def validate_resource_mirror(skill_dir: Path, importable_dir: Path, errors: list[str]) -> None:
    """Reject duplicated package resources; canonical data stays in the Skill tree."""
    for relative in ("SKILL.md", "assets", "references"):
        if (importable_dir / relative).exists():
            errors.append(f"duplicated package resource: {relative}")
    if not (skill_dir / "__init__.py").is_file():
        errors.append("canonical Skill package is missing __init__.py")


def validate_python_mirror(
    skill_dir: Path,
    importable_dir: Path,
    errors: list[str],
) -> None:
    """Require a thin import bridge instead of a second Python implementation."""
    target_root = importable_dir / "scripts"
    target_files = {
        path.relative_to(target_root): path
        for path in target_root.rglob("*.py")
        if "__pycache__" not in path.parts
    }
    if set(target_files) != {Path("__init__.py")}:
        extras = sorted(path.as_posix() for path in target_files if path != Path("__init__.py"))
        errors.append(f"thin package contains mirrored Python files: {extras}")
    bridge = target_root / "__init__.py"
    try:
        bridge_text = bridge.read_text(encoding="utf-8")
    except OSError:
        bridge_text = ""
    if "skills.examlex" not in bridge_text or "__path__" not in bridge_text:
        errors.append("thin package script bridge is invalid")
    for filename in ("cli.py", "run.py"):
        target = importable_dir / filename
        try:
            text = target.read_text(encoding="utf-8")
        except OSError:
            text = ""
        if "skills.examlex" not in text:
            errors.append(f"thin package wrapper is invalid: {filename}")


IGNORED_TREE_PARTS = {
    ".git",
    ".pytest_cache",
    ".task8-test-tmp",
    ".tmp-test",
    ".venv",
    ".worktrees",
    "build",
    "dist",
    "test-artifacts",
    "__pycache__",
}


def _project_files(root: Path) -> list[Path]:
    """Inventory maintained files once while pruning ignored directory trees."""
    files: list[Path] = []
    for current, directories, filenames in os.walk(root):
        directories[:] = [
            name for name in directories if name not in IGNORED_TREE_PARTS
        ]
        current_path = Path(current)
        files.extend(current_path / name for name in filenames)
    return sorted(files)


def _maintained_markdown_files(
    root: Path,
    project_files: list[Path] | None = None,
) -> list[Path]:
    """Return maintained Markdown, excluding generated and internal planning trees."""
    files: list[Path] = []
    for path in project_files if project_files is not None else _project_files(root):
        if path.suffix.lower() != ".md":
            continue
        relative = path.relative_to(root)
        if relative.parts[:2] == ("docs", "superpowers"):
            continue
        files.append(path)
    return sorted(files)


def _validate_matching_basenames(
    root: Path,
    english_dir: Path,
    chinese_dir: Path,
    label: str,
    errors: list[str],
) -> None:
    english = {path.name for path in english_dir.glob("*.md") if path.is_file()}
    chinese = {path.name for path in chinese_dir.glob("*.md") if path.is_file()}
    for name in sorted(english - chinese):
        missing = (chinese_dir / name).relative_to(root).as_posix()
        errors.append(
            f"missing Chinese documentation counterpart for {label}/{name}: "
            f"{missing}"
        )
    for name in sorted(chinese - english):
        missing = (english_dir / name).relative_to(root).as_posix()
        errors.append(
            f"missing English documentation counterpart for {label}/{name}: "
            f"{missing}"
        )


def _markdown_link_target(raw_target: str) -> str:
    target = raw_target.strip()
    if target.startswith("<") and ">" in target:
        return target[1:target.index(">")]
    return target.split(maxsplit=1)[0] if target else ""


def validate_documentation(
    root: Path,
    errors: list[str],
    *,
    markdown_files: list[Path] | None = None,
    text_cache: dict[Path, str] | None = None,
) -> None:
    """Validate bilingual coverage, offline policy, and local link targets."""
    _validate_matching_basenames(
        root, root / "docs", root / "zh-CN" / "docs", "docs", errors
    )
    _validate_matching_basenames(
        root,
        root / "skills" / SKILL_NAME / "references",
        root / "zh-CN" / "skill" / "references",
        "Skill references",
        errors,
    )

    for relative in (
        Path("zh-CN/README.md"),
        Path("zh-CN/skill/SKILL.md"),
        Path("zh-CN/cli-reference.md"),
    ):
        if not (root / relative).is_file():
            errors.append(
                "missing Chinese documentation counterpart: " + relative.as_posix()
            )

    for platform in ("claude-code", "codex-app", "codex-cli", "cursor"):
        english = root / "integrations" / platform / "README.md"
        chinese = root / "zh-CN" / "integrations" / f"{platform}.md"
        if english.is_file() and not chinese.is_file():
            errors.append(
                "missing Chinese documentation counterpart for integration: "
                + chinese.relative_to(root).as_posix()
            )
        if chinese.is_file() and not english.is_file():
            errors.append(
                "missing English documentation counterpart for integration: "
                + english.relative_to(root).as_posix()
            )

    maintained_files = (
        markdown_files
        if markdown_files is not None
        else _maintained_markdown_files(root)
    )
    for markdown_file in maintained_files:
        relative = markdown_file.relative_to(root)
        text = (
            text_cache[markdown_file]
            if text_cache is not None and markdown_file in text_cache
            else markdown_file.read_text(encoding="utf-8")
        )
        allowed_urls = ALLOWED_EXTERNAL_URLS
        if relative in README_BADGE_PATHS:
            allowed_urls = ALLOWED_EXTERNAL_URLS | README_BADGE_URLS
        normalized_allowed_urls = {
            _normalize_external_url(allowed_url) for allowed_url in allowed_urls
        }
        disallowed_urls = extract_external_urls(text) - normalized_allowed_urls
        if disallowed_urls:
            errors.append(
                f"external URL is forbidden in maintained Markdown: {relative.as_posix()}"
                f" -> {sorted(disallowed_urls)[0]}"
            )

        for match in MARKDOWN_LINK_RE.finditer(text):
            target = _markdown_link_target(match.group(1))
            if not target or target.startswith("#"):
                continue
            if re.match(r"^[A-Za-z][A-Za-z0-9+.-]*:", target):
                if target in allowed_urls:
                    continue
                errors.append(
                    f"external URL is forbidden in maintained Markdown: "
                    f"{relative.as_posix()} -> {target}"
                )
                continue
            path_text = unquote(target.split("#", 1)[0])
            if not path_text:
                continue
            resolved = (markdown_file.parent / path_text).resolve()
            try:
                resolved.relative_to(root)
            except ValueError:
                errors.append(
                    f"broken local Markdown link in {relative.as_posix()}: {target}"
                )
                continue
            if not resolved.exists():
                errors.append(
                    f"broken local Markdown link in {relative.as_posix()}: {target}"
                )


def validate_template_contracts(root: Path, errors: list[str]) -> None:
    templates = root / "skills" / SKILL_NAME / "assets" / "templates"
    try:
        ability = json.loads((templates / "ability-profile.yaml").read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        errors.append(f"ability-profile template is not valid JSON-compatible YAML: {exc}")
    else:
        modules = ability.get("modules") if isinstance(ability, dict) else None
        if not isinstance(modules, dict) or not all(
            isinstance(nodes, list)
            and all(
                isinstance(node, dict)
                and isinstance(node.get("node"), str)
                and bool(node["node"].strip())
                for node in nodes
            )
            for nodes in modules.values()
        ):
            errors.append("ability-profile template modules must contain ability-node objects")

    for filename in ("exercise-record.json", "exercise-record.yaml"):
        try:
            ledger = json.loads((templates / filename).read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            errors.append(f"practice template {filename} is not valid JSON-compatible YAML: {exc}")
        else:
            if not isinstance(ledger, list):
                errors.append(f"practice template must contain a JSON list: {filename}")

    filename = "writing-version-record.yaml"
    try:
        versions = json.loads((templates / filename).read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        errors.append(f"writing template is not valid JSON-compatible YAML: {exc}")
    else:
        if not isinstance(versions, list):
            errors.append("writing template must contain a JSON list")


def validate_vocab_contracts(root: Path, errors: list[str]) -> None:
    vocab_dir = root / "skills" / SKILL_NAME / "assets" / "data" / "vocabulary"
    try:
        index = json.loads((vocab_dir / "index.json").read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        errors.append(f"vocabulary index is not valid JSON: {exc}")
        return
    if not isinstance(index, dict):
        errors.append("vocabulary index must contain an object")
        return

    expected_starters = {
        "cet4-starter",
        "cet6-starter",
        "postgraduate-starter",
        "tem4-starter",
        "tem8-starter",
    }
    expected_extended = {
        "cet4-core-extended",
        "cet6-core-extended",
        "postgraduate-core-extended",
    }
    missing = (expected_starters | expected_extended) - set(index)
    if missing:
        errors.append(f"vocabulary index is missing required pools: {sorted(missing)}")

    for misleading in (
        "cet4-core-2000.json",
        "cet6-core-1500.json",
        "postgraduate-core-1000.json",
        "tem4-core-2000.json",
        "tem8-core-2000.json",
    ):
        if (vocab_dir / misleading).exists():
            errors.append(f"misleading duplicate vocabulary file must be removed: {misleading}")

    for key, metadata in index.items():
        if not isinstance(metadata, dict):
            errors.append(f"vocabulary index entry must be an object: {key}")
            continue
        filename = metadata.get("path")
        if not isinstance(filename, str):
            errors.append(f"vocabulary index entry has no path: {key}")
            continue
        match = re.search(r"-(\d+)\.json$", filename)
        if match is None:
            errors.append(f"canonical vocabulary filename must end with its count: {filename}")
            continue
        try:
            entries = json.loads((vocab_dir / filename).read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            errors.append(f"canonical vocabulary file is invalid: {filename}: {exc}")
            continue
        expected_count = int(match.group(1))
        if not isinstance(entries, list) or len(entries) != expected_count:
            errors.append(f"canonical vocabulary filename count mismatch: {filename}")
            continue
        if metadata.get("count") != expected_count:
            errors.append(f"vocabulary index count mismatch: {filename}")
        scope = metadata.get("scope")
        if scope not in {"curated_starter", "verified_extended"}:
            errors.append(f"unsupported vocabulary pool scope: {key}: {scope}")
        if "source" in metadata or "legacy_paths" in metadata:
            errors.append(f"vocabulary metadata contains deprecated source/legacy fields: {key}")
        verification = metadata.get("verification")
        if not isinstance(verification, dict):
            errors.append(f"vocabulary pool has no verification record: {key}")
            continue
        required_verification = {
            "origin_class",
            "method",
            "verified_on",
            "content_sha256",
        }
        if not required_verification.issubset(verification):
            errors.append(f"vocabulary verification record is incomplete: {key}")
            continue
        actual_sha256 = hashlib.sha256((vocab_dir / filename).read_bytes()).hexdigest()
        if verification.get("content_sha256") != actual_sha256:
            errors.append(f"vocabulary content hash mismatch: {filename}")
        words = [entry.get("word", "").casefold() for entry in entries]
        if len(words) != len(set(words)):
            errors.append(f"vocabulary pool contains duplicate words: {filename}")
        ranks = [entry.get("frequency_rank") for entry in entries]
        if ranks != list(range(1, expected_count + 1)):
            errors.append(f"vocabulary frequency ranks must be continuous: {filename}")


def validate_source_catalog_contracts(root: Path, errors: list[str]) -> None:
    catalog_path = (
        root / "skills" / SKILL_NAME / "assets" / "data" / "source-catalog.json"
    )
    try:
        raw = catalog_path.read_text(encoding="utf-8")
        catalog = json.loads(raw)
    except (OSError, json.JSONDecodeError) as exc:
        errors.append(f"source catalog is not valid JSON: {exc}")
        return
    if not isinstance(catalog, dict) or catalog.get("schema_version") != 1:
        errors.append("source catalog schema_version must be 1")
        return
    levels = catalog.get("evidence_levels")
    if not isinstance(levels, dict) or set(levels) != {"S", "A", "B", "C", "R"}:
        errors.append("source catalog must define S/A/B/C/R evidence levels")
    sources = catalog.get("sources")
    if not isinstance(sources, list) or len(sources) < 50:
        errors.append("source catalog must contain at least 50 merged media sources")
        return
    references = catalog.get("reference_corpora")
    if not isinstance(references, list) or len(references) < 15:
        errors.append("source catalog must contain at least 15 R-level reference corpora")
    required_ids = {
        "atlantic",
        "bbc",
        "christian-science-monitor",
        "economist",
        "guardian",
        "nature",
        "npr",
        "scientific-american",
        "ted-talks",
    }
    source_ids: set[str] = set()
    feed_ids: set[str] = set()
    for source in sources:
        if not isinstance(source, dict):
            errors.append("source catalog entries must be objects")
            continue
        source_id = source.get("source_id")
        if not isinstance(source_id, str) or not source_id:
            errors.append("source catalog entry has no source_id")
            continue
        if source_id in source_ids:
            errors.append(f"source catalog has duplicate source_id: {source_id}")
        source_ids.add(source_id)
        domains = source.get("domains")
        if not isinstance(domains, list) or not domains:
            errors.append(f"source catalog entry has no domains: {source_id}")
            domains = []
        usage_entries = source.get("usage")
        if not isinstance(usage_entries, list) or not usage_entries:
            errors.append(f"source catalog entry has no exam usage: {source_id}")
            usage_entries = []
        for usage in usage_entries:
            if not isinstance(usage, dict):
                errors.append(f"source catalog usage must be an object: {source_id}")
                continue
            evidence = usage.get("evidence")
            if evidence not in {"A", "B", "C"}:
                errors.append(f"source catalog named source has invalid evidence: {source_id}")
            if evidence == "A" and not usage.get("trace_ids"):
                errors.append(
                    f"source catalog A-level usage must cite article trace ids: {source_id}"
                )
        for feed in source.get("feeds", []):
            if not isinstance(feed, dict):
                errors.append(f"source feed must be an object: {source_id}")
                continue
            feed_id = feed.get("feed_id")
            if not isinstance(feed_id, str) or not feed_id:
                errors.append(f"source feed has no feed_id: {source_id}")
                continue
            if feed_id in feed_ids:
                errors.append(f"source catalog has duplicate feed_id: {feed_id}")
            feed_ids.add(feed_id)
            try:
                parts = urlsplit(str(feed.get("url", "")))
            except ValueError:
                parts = None
            if parts is None or parts.scheme != "https" or not parts.hostname:
                errors.append(f"source feed must use HTTPS: {feed_id}")
                continue
            host = parts.hostname.lower().rstrip(".")
            if not any(host == domain or host.endswith("." + domain) for domain in domains):
                errors.append(f"source feed host is outside maintained domains: {feed_id}")
    missing = required_ids - source_ids
    if missing:
        errors.append(f"source catalog is missing required merged sources: {sorted(missing)}")
    if "%" in raw or re.search(r"\bpercent(?:age)?\b", raw, re.IGNORECASE):
        errors.append("source catalog must not contain unsupported percentage claims")


def validate_project(root: str | Path) -> ValidationResult:
    root_path = Path(root).resolve()
    result = ValidationResult(root=str(root_path))
    errors = result.errors
    warnings = result.warnings
    project_files = _project_files(root_path)
    text_cache: dict[Path, str] = {}

    for filename in ("LICENSE", "pyproject.toml", "SKILL.md", "install.sh", "install.ps1", "cli-reference.md"):
        if not (root_path / filename).is_file():
            errors.append(f"Missing required root file: {filename}")
    for relative in ("bin/examlex", "bin/examlex.ps1"):
        if not (root_path / relative).is_file():
            errors.append(f"Missing user CLI wrapper: {relative}")
    if not (root_path / "README.md").is_file():
        warnings.append("README.md is not present yet; Task 9 may add it, so this is a warning only.")
    else:
        readme_text = (root_path / "README.md").read_text(encoding="utf-8")
        for marker in ("your-org",):
            if marker in readme_text:
                errors.append(f"README.md contains remote install placeholder: {marker}")
        for section in sorted(EXPECTED_README_SECTIONS):
            if section not in readme_text:
                errors.append(f"README.md must include {section}.")
        for marker in sorted(EXPECTED_README_SKILL_INSTALL_MARKERS):
            if marker not in readme_text:
                errors.append(f"README.md Quick Start must explain Skill installation marker: {marker}")
        for marker in sorted(EXPECTED_README_AGENT_CALL_MARKERS):
            if marker not in readme_text:
                errors.append(f"README.md must explain Agent Skill invocation marker: {marker}")
        for marker in sorted(FORBIDDEN_AGENT_CALL_MARKERS):
            if marker in readme_text:
                errors.append(f"README.md must use slash Skill invocation, not {marker}.")
    for filename in sorted(EXPECTED_PROJECT_QUALITY_FILES):
        if not (root_path / filename).is_file():
            errors.append(f"Missing project quality file: {filename}")
    secret_baseline_path = root_path / ".secrets.baseline"
    if secret_baseline_path.is_file():
        try:
            secret_baseline = json.loads(secret_baseline_path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            errors.append("Secret baseline must be valid UTF-8 JSON.")
        else:
            secret_results = secret_baseline.get("results")
            if not isinstance(secret_results, dict):
                errors.append("Secret baseline results must be an object.")
            else:
                for baseline_filename, findings in secret_results.items():
                    if not isinstance(baseline_filename, str) or "\\" in baseline_filename:
                        errors.append("Secret baseline paths must use portable forward slashes.")
                        continue
                    if not isinstance(findings, list):
                        errors.append(
                            f"Secret baseline findings must be a list: {baseline_filename}"
                        )
                        continue
                    for finding in findings:
                        if not isinstance(finding, dict):
                            errors.append(
                                f"Secret baseline finding must be an object: {baseline_filename}"
                            )
                            continue
                        if finding.get("filename") != baseline_filename:
                            errors.append(
                                f"Secret baseline filename mismatch: {baseline_filename}"
                            )
                        if not re.fullmatch(
                            r"[0-9a-f]{40}", str(finding.get("hashed_secret", ""))
                        ):
                            errors.append(
                                f"Secret baseline must contain SHA-1 hashes only: {baseline_filename}"
                            )
                        if finding.get("is_secret") is not False:
                            errors.append(
                                f"Secret baseline finding is not audited false-positive: {baseline_filename}"
                            )
                        if "secret" in finding:
                            errors.append(
                                f"Secret baseline must not contain raw values: {baseline_filename}"
                            )
    for relative in sorted(EXPECTED_QUALITY_DOCS):
        if not (root_path / relative).is_file():
            errors.append(f"Missing quality documentation: {relative}")
    for filename in sorted(EXPECTED_GITHUB_HEALTH_FILES):
        if not (root_path / filename).is_file():
            errors.append(f"Missing GitHub health file: {filename}")
    for relative in sorted(EXPECTED_GITHUB_ISSUE_TEMPLATES):
        if not (root_path / relative).is_file():
            errors.append(f"Missing GitHub issue template: {relative}")
    for relative in sorted(EXPECTED_GITHUB_WORKFLOWS):
        if not (root_path / relative).is_file():
            errors.append(f"Missing GitHub workflow: {relative}")
    if not (root_path / ".github" / "PULL_REQUEST_TEMPLATE.md").is_file():
        errors.append("Missing GitHub pull request template: .github/PULL_REQUEST_TEMPLATE.md")

    skill_dir = root_path / "skills" / SKILL_NAME
    importable_dir = root_path / IMPORTABLE_NAME
    for relative in (
        Path("skills") / SKILL_NAME / "SKILL.md",
        Path("scripts"),
        Path("skills") / SKILL_NAME / "scripts",
        Path("skills") / SKILL_NAME / "references",
        Path("skills") / SKILL_NAME / "assets",
    ):
        if not (root_path / relative).exists():
            errors.append(f"Missing required path: {relative.as_posix()}")

    for filename in ("README.md", "INSTALL.md"):
        if (skill_dir / filename).exists():
            errors.append(f"Portable Skill must not contain {filename}.")

    references_dir = skill_dir / "references"
    for filename in sorted(EXPECTED_REFERENCES):
        if not (references_dir / filename).is_file():
            errors.append(f"Missing required reference: references/{filename}")
    validate_tutor_role_contracts(root_path, errors)

    skill_file = skill_dir / "SKILL.md"
    if skill_file.exists():
        skill_text = skill_file.read_text(encoding="utf-8")
        metadata = parse_front_matter(skill_text)
        if not metadata.get("name"):
            errors.append("SKILL.md YAML front matter must include name.")
        description = metadata.get("description", "")
        if not description:
            errors.append("SKILL.md YAML front matter must include description.")
        elif not description.startswith("Use when"):
            errors.append("SKILL.md description must start with 'Use when'.")
    else:
        skill_text = ""

    for alias in sorted(SKILL_ALIASES):
        alias_file = root_path / "skills" / alias / "SKILL.md"
        if not alias_file.is_file():
            errors.append(f"Missing shortcut Skill: skills/{alias}/SKILL.md")
            continue
        alias_text = alias_file.read_text(encoding="utf-8")
        alias_metadata = parse_front_matter(alias_text)
        if alias_metadata.get("name") != alias:
            errors.append(f"Shortcut Skill {alias} must have matching name metadata.")
        description = alias_metadata.get("description", "")
        if not description.startswith("Use when"):
            errors.append(f"Shortcut Skill {alias} description must start with 'Use when'.")
        if SKILL_NAME not in alias_text:
            errors.append(f"Shortcut Skill {alias} must route back to {SKILL_NAME}.")

    for path in project_files:
        relative_path = path.relative_to(root_path)
        try:
            text = path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            continue
        text_cache[path] = text
        if FORBIDDEN_PRIVATE_PROMPT in text:
            errors.append(f"Found forbidden private prompt sentence in {path.relative_to(root_path).as_posix()}.")
        for identifier in LEGACY_IDENTIFIERS:
            if identifier in text:
                errors.append(
                    "legacy product identifier found in "
                    f"{relative_path.as_posix()}: {identifier}"
                )
        for marker in sorted(FORBIDDEN_AGENT_CALL_MARKERS):
            if marker in text:
                errors.append(f"Found forbidden dollar-style Skill call in {path.relative_to(root_path).as_posix()}: {marker}")
        for rule_name, pattern in PUBLIC_SAFETY_PATTERNS.items():
            for match in pattern.finditer(text):
                if any(
                    marker in match.group(0).lower()
                    for marker in PUBLIC_SAFETY_PLACEHOLDER_MARKERS
                ):
                    continue
                line_number = text.count("\n", 0, match.start()) + 1
                errors.append(
                    "Public-safety scan found "
                    f"{rule_name} in {relative_path.as_posix()}:{line_number}."
                )

    prompt_mode = read_pyproject_prompt_mode(root_path / "pyproject.toml")
    if prompt_mode != "public-safe":
        errors.append("pyproject.toml [tool.examlex] prompt-mode must remain public-safe.")

    portable_scripts = skill_dir / "scripts"
    for script_name in sorted(EXPECTED_AUTOMATION_SCRIPTS):
        portable = portable_scripts / script_name
        if not portable.is_file():
            errors.append(f"Missing portable automation script: {portable.relative_to(root_path).as_posix()}")

    validate_resource_mirror(skill_dir, importable_dir, errors)
    validate_python_mirror(skill_dir, importable_dir, errors)
    validate_writing_article_omission(portable_scripts / "common.py", errors)
    validate_template_contracts(root_path, errors)
    validate_vocab_contracts(root_path, errors)
    validate_source_catalog_contracts(root_path, errors)
    validate_documentation(
        root_path,
        errors,
        markdown_files=_maintained_markdown_files(root_path, project_files),
        text_cache=text_cache,
    )
    validate_tracked_learner_artifacts(root_path, errors)
    validate_tracked_private_prompt_assets(root_path, errors)
    return result


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Validate this public-safe Skill and automation repository.")
    parser.add_argument("--root", type=Path, default=Path.cwd(), help="Repository root to validate.")
    parser.add_argument("--json", action="store_true", help="Print machine-readable JSON.")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    result = validate_project(args.root)
    if args.json:
        data = asdict(result)
        data["root"] = "."
        data["ok"] = result.ok
        print(json.dumps(data, ensure_ascii=False, indent=2))
    else:
        if result.ok:
            print("Repository validation passed.")
        else:
            print("Repository validation failed.")
        for warning in result.warnings:
            print(f"WARNING: {warning}")
        for error in result.errors:
            print(f"ERROR: {error}")
    return 0 if result.ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
