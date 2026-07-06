from __future__ import annotations

import argparse
import ast
import hashlib
import json
import re
from dataclasses import asdict, dataclass, field
from pathlib import Path


SKILL_NAME = "english-exam-ai-tutor"
IMPORTABLE_NAME = "english_exam_ai_tutor"
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
}
EXPECTED_QUALITY_DOCS = {
    "docs/configuration.md",
    "docs/development.md",
    "docs/getting-started.md",
    "docs/release.md",
    "docs/roadmap.md",
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
    "## Roadmap",
    "## Contributing",
    "## License",
}
EXPECTED_README_SKILL_INSTALL_MARKERS = {
    "npx skills add",
    "install.sh",
    "install.ps1",
    "$HOME\\.agents\\skills",
    ".agents\\skills",
    "$HOME\\.claude\\skills",
    ".claude\\skills",
    "skills\\english-exam-ai-tutor",
}
EXPECTED_README_AGENT_CALL_MARKERS = {
    "/english-exam-ai-tutor",
    "/grammar-corrector",
    "/learning-planner",
}
FORBIDDEN_AGENT_CALL_MARKERS = {
    "$" + "english-exam-ai-tutor",
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


def validate_project(root: str | Path) -> ValidationResult:
    root_path = Path(root).resolve()
    result = ValidationResult(root=str(root_path))
    errors = result.errors
    warnings = result.warnings

    for filename in ("LICENSE", "pyproject.toml", "SKILL.md", "install.sh", "install.ps1", "cli-reference.md"):
        if not (root_path / filename).is_file():
            errors.append(f"Missing required root file: {filename}")
    for relative in ("bin/tutor", "bin/tutor.ps1"):
        if not (root_path / relative).is_file():
            errors.append(f"Missing user CLI wrapper: {relative}")
    if not (root_path / "README.md").is_file():
        warnings.append("README.md is not present yet; Task 9 may add it, so this is a warning only.")
    else:
        readme_text = (root_path / "README.md").read_text(encoding="utf-8")
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
    importable_dir = root_path / "skills" / IMPORTABLE_NAME
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
        if "english-exam-ai-tutor" not in alias_text:
            errors.append(f"Shortcut Skill {alias} must route back to english-exam-ai-tutor.")

    for path in root_path.rglob("*"):
        if "test-artifacts" in path.parts or path.is_dir():
            continue
        try:
            text = path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            continue
        if FORBIDDEN_PRIVATE_PROMPT in text:
            errors.append(f"Found forbidden private prompt sentence in {path.relative_to(root_path).as_posix()}.")
        for marker in sorted(FORBIDDEN_AGENT_CALL_MARKERS):
            if marker in text:
                errors.append(f"Found forbidden dollar-style Skill call in {path.relative_to(root_path).as_posix()}: {marker}")
        if path.suffix.lower() in {".md", ".yml", ".yaml", ".toml", ".json"}:
            for marker in sorted(FORBIDDEN_PUBLIC_PATH_MARKERS):
                if marker in text:
                    errors.append(f"Found local machine path in public documentation must not include local machine path: {path.relative_to(root_path).as_posix()}")

    prompt_mode = read_pyproject_prompt_mode(root_path / "pyproject.toml")
    if prompt_mode != "public-safe":
        errors.append("pyproject.toml [tool.english-exam-ai-tutor] prompt-mode must remain public-safe.")

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

    validate_writing_article_omission(portable_scripts / "common.py", errors)
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
