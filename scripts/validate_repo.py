from __future__ import annotations

import argparse
import ast
import hashlib
import json
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
    "workflow.md",
}
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
    "summarize_errors.py",
    "tag_error.py",
    "update_ability_profile.py",
    "validate_strategy.py",
    "validate_profile.py",
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
FORBIDDEN_PUBLIC_PATH_MARKERS = {
    "D:\\Codex_project",
    "C:\\Users\\Lenovo",
}
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
        is_private_directory = bool(relative.parts) and relative.parts[0] == "learner-data"
        is_standard_name = name in LEARNER_ARTIFACT_NAMES
        is_backup = BACKUP_ARTIFACT_RE.fullmatch(name) is not None
        is_sidecar = name.endswith((".bak", ".lock", ".tmp"))
        if is_private_directory or is_standard_name or is_backup or is_sidecar:
            errors.append(f"tracked learner artifact is forbidden: {relative.as_posix()}")


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
    """Require package resources to exactly mirror the portable Skill resources."""
    skill_file = skill_dir / "SKILL.md"
    package_skill = importable_dir / "SKILL.md"
    if not package_skill.is_file() or sha256(skill_file) != sha256(package_skill):
        errors.append("resource mirror mismatch: SKILL.md")

    for directory_name in ("assets", "references"):
        skill_resources = skill_dir / directory_name
        package_resources = importable_dir / directory_name
        source_files = {
            path.relative_to(skill_resources): path
            for path in skill_resources.rglob("*")
            if path.is_file()
        }
        package_files = (
            {
                path.relative_to(package_resources): path
                for path in package_resources.rglob("*")
                if path.is_file()
            }
            if package_resources.exists()
            else {}
        )

        for relative, source in sorted(source_files.items()):
            package_file = package_files.get(relative)
            if package_file is None or sha256(source) != sha256(package_file):
                errors.append(
                    f"resource mirror mismatch: {directory_name}/{relative.as_posix()}"
                )
        for relative in sorted(package_files.keys() - source_files.keys()):
            errors.append(
                f"extra package resource: {directory_name}/{relative.as_posix()}"
            )


def _maintained_markdown_files(root: Path) -> list[Path]:
    """Return maintained Markdown, excluding generated and internal planning trees."""
    ignored_parts = {
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
    files: list[Path] = []
    for path in root.rglob("*.md"):
        relative = path.relative_to(root)
        if ignored_parts.intersection(relative.parts):
            continue
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


def validate_documentation(root: Path, errors: list[str]) -> None:
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

    for markdown_file in _maintained_markdown_files(root):
        relative = markdown_file.relative_to(root)
        text = markdown_file.read_text(encoding="utf-8")
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
    templates = root / IMPORTABLE_NAME / "assets" / "templates"
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
        if metadata.get("scope") != "curated_starter":
            errors.append(f"vocabulary index scope must be curated_starter: {key}")
        legacy_paths = metadata.get("legacy_paths")
        if not isinstance(legacy_paths, list) or not legacy_paths:
            errors.append(f"vocabulary index must list legacy_paths: {key}")
            continue
        for legacy_path in legacy_paths:
            try:
                legacy_entries = json.loads(
                    (vocab_dir / legacy_path).read_text(encoding="utf-8")
                )
            except (OSError, json.JSONDecodeError) as exc:
                errors.append(f"legacy vocabulary file is invalid: {legacy_path}: {exc}")
                continue
            if legacy_entries != entries:
                errors.append(
                    f"legacy vocabulary data differs from canonical file: {legacy_path}"
                )


def validate_project(root: str | Path) -> ValidationResult:
    root_path = Path(root).resolve()
    result = ValidationResult(root=str(root_path))
    errors = result.errors
    warnings = result.warnings

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

    ignored_parts = {
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
    for path in root_path.rglob("*"):
        relative_path = path.relative_to(root_path)
        if ignored_parts.intersection(relative_path.parts) or path.is_dir():
            continue
        try:
            text = path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            continue
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
        if path.suffix.lower() in {".md", ".yml", ".yaml", ".toml", ".json"}:
            for marker in sorted(FORBIDDEN_PUBLIC_PATH_MARKERS):
                if marker in text:
                    errors.append(f"Found local machine path in public documentation must not include local machine path: {path.relative_to(root_path).as_posix()}")

    prompt_mode = read_pyproject_prompt_mode(root_path / "pyproject.toml")
    if prompt_mode != "public-safe":
        errors.append("pyproject.toml [tool.examlex] prompt-mode must remain public-safe.")

    portable_scripts = skill_dir / "scripts"
    importable_scripts = importable_dir / "scripts"
    for script_name in sorted(EXPECTED_AUTOMATION_SCRIPTS):
        portable = portable_scripts / script_name
        importable = importable_scripts / script_name
        if not portable.is_file():
            errors.append(f"Missing portable automation script: {portable.relative_to(root_path).as_posix()}")
            continue
        if not importable.is_file():
            errors.append(f"Missing importable automation script: {importable.relative_to(root_path).as_posix()}")
            continue
        if sha256(portable) != sha256(importable):
            errors.append(f"Automation script mirror mismatch: {script_name}")

    validate_resource_mirror(skill_dir, importable_dir, errors)
    validate_writing_article_omission(portable_scripts / "common.py", errors)
    validate_template_contracts(root_path, errors)
    validate_vocab_contracts(root_path, errors)
    validate_documentation(root_path, errors)
    validate_tracked_learner_artifacts(root_path, errors)
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
