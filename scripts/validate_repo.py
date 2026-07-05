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
    "common.py",
    "generate_daily_plan.py",
    "manage_writing_versions.py",
    "record_practice.py",
    "score_writing_rubric.py",
    "summarize_errors.py",
    "tag_error.py",
    "update_ability_profile.py",
    "validate_profile.py",
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

    for filename in ("LICENSE", "pyproject.toml"):
        if not (root_path / filename).is_file():
            errors.append(f"Missing required root file: {filename}")
    if not (root_path / "README.md").is_file():
        warnings.append("README.md is not present yet; Task 9 may add it, so this is a warning only.")

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

    for path in root_path.rglob("*"):
        if "test-artifacts" in path.parts or path.is_dir():
            continue
        try:
            text = path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            continue
        if FORBIDDEN_PRIVATE_PROMPT in text:
            errors.append(f"Found forbidden private prompt sentence in {path.relative_to(root_path).as_posix()}.")

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
