from __future__ import annotations

import json
import shutil
import re
import subprocess
import unittest
import uuid
from contextlib import contextmanager
from pathlib import Path

from scripts import validate_repo


PROJECT_ROOT = Path(__file__).resolve().parents[1]
SKILL_DIR = Path("skills") / "examlex"
TEMP_ROOT = PROJECT_ROOT / ".task8-test-tmp"


@contextmanager
def copy_project():
    TEMP_ROOT.mkdir(parents=True, exist_ok=True)
    tempdir = TEMP_ROOT / f"repo-{uuid.uuid4().hex}"
    target = tempdir / "repo"
    try:
        shutil.copytree(
            PROJECT_ROOT,
            target,
            ignore=shutil.ignore_patterns(
                ".git",
                ".venv",
                ".pytest_cache",
                ".worktrees",
                ".task8-test-tmp",
                ".tmp-test",
                "build",
                "dist",
                "*.egg-info",
                "test-artifacts",
                "__pycache__",
                "*.pyc",
            ),
        )
        yield str(tempdir)
    finally:
        shutil.rmtree(tempdir, ignore_errors=True)


class ValidateProjectTests(unittest.TestCase):
    def test_private_prompt_directories_are_ignored_and_cannot_be_tracked(self):
        private_paths = (
            ".examlex-private/study-planner.md",
            "private-prompts/grammar-corrector.md",
        )
        for relative in private_paths:
            with self.subTest(relative=relative):
                completed = subprocess.run(
                    ["git", "check-ignore", "--no-index", "--quiet", "--", relative],
                    cwd=PROJECT_ROOT,
                )
                self.assertEqual(0, completed.returncode)

        errors: list[str] = []
        validate_repo.validate_tracked_private_prompt_assets(
            PROJECT_ROOT,
            errors,
            tracked_files=["README.md", *private_paths],
        )
        self.assertEqual(2, len(errors), errors)
        self.assertTrue(all("private prompt asset" in error for error in errors))

    def test_tutor_role_contract_has_exact_public_safe_roles(self):
        errors: list[str] = []
        validate_repo.validate_tutor_role_contracts(PROJECT_ROOT, errors)
        self.assertEqual([], errors)

        contract_path = (
            PROJECT_ROOT
            / "skills"
            / "examlex"
            / "references"
            / validate_repo.TUTOR_ROLE_CONTRACT_FILENAME
        )
        document = json.loads(contract_path.read_text(encoding="utf-8"))
        self.assertEqual("public-safe", document["mode"])
        placeholders = {
            role["role_id"]: role["placeholder"] for role in document["roles"]
        }
        self.assertEqual(validate_repo.EXPECTED_TUTOR_ROLE_PLACEHOLDERS, placeholders)

    def test_tutor_role_contract_rejects_missing_role(self):
        with copy_project() as temp:
            root = Path(temp) / "repo"
            contract_path = (
                root
                / "skills"
                / "examlex"
                / "references"
                / validate_repo.TUTOR_ROLE_CONTRACT_FILENAME
            )
            document = json.loads(contract_path.read_text(encoding="utf-8"))
            document["roles"].pop()
            contract_path.write_text(
                json.dumps(document, ensure_ascii=False, indent=2) + "\n",
                encoding="utf-8",
            )
            errors: list[str] = []
            validate_repo.validate_tutor_role_contracts(root, errors)

        self.assertTrue(any("exactly eight roles" in error for error in errors))
        self.assertTrue(any("missing roles" in error for error in errors))

    def test_tutor_role_contract_rejects_mode_placeholder_and_empty_field(self):
        with copy_project() as temp:
            root = Path(temp) / "repo"
            contract_path = (
                root
                / "skills"
                / "examlex"
                / "references"
                / validate_repo.TUTOR_ROLE_CONTRACT_FILENAME
            )
            document = json.loads(contract_path.read_text(encoding="utf-8"))
            document["mode"] = "full-local"
            document["roles"][0]["placeholder"] = "incorrect"
            document["roles"][0]["workflow"] = []
            contract_path.write_text(
                json.dumps(document, ensure_ascii=False, indent=2) + "\n",
                encoding="utf-8",
            )
            errors: list[str] = []
            validate_repo.validate_tutor_role_contracts(root, errors)

        self.assertTrue(any("mode must remain public-safe" in error for error in errors))
        self.assertTrue(any("placeholder mismatch" in error for error in errors))
        self.assertTrue(any("non-empty workflow" in error for error in errors))

    def test_standard_learner_artifacts_are_ignored_and_cannot_be_tracked(self):
        artifact_paths = (
            "learner-profile.json",
            "ability-profile.json",
            "ability-history.json",
            "practice-ledger.json",
            "error-summary.json",
            "daily-plan.json",
            "strategy-library.json",
            "writing-versions.json",
            "progress-report.html",
            "backup-2026-07-12.tar.gz",
            "backup-2026-07-12.tar.gz.sha256",
            "strategy-library.json.bak",
            "strategy-library.json.lock",
            "learner-data/private-profile.json",
            "source-corpus/manifest.jsonl",
        )
        for relative in artifact_paths:
            with self.subTest(relative=relative):
                completed = subprocess.run(
                    ["git", "check-ignore", "--no-index", "--quiet", "--", relative],
                    cwd=PROJECT_ROOT,
                )
                self.assertEqual(0, completed.returncode)

        errors = []
        validate_repo.validate_tracked_learner_artifacts(
            PROJECT_ROOT,
            errors,
            tracked_files=[
                "README.md",
                "examples/sample-learner-profile.yaml",
                "practice-ledger.json",
                "learner-data/private-profile.json",
                "source-corpus/manifest.jsonl",
            ],
        )
        self.assertEqual(3, len(errors), errors)
        self.assertTrue(all("learner artifact" in error for error in errors))

    def test_installed_skill_docs_use_the_bundled_runner(self):
        paths = (
            PROJECT_ROOT / "skills/examlex/SKILL.md",
            PROJECT_ROOT / "skills/examlex/references/workflow.md",
            PROJECT_ROOT / "skills/examlex/references/multi-source-distillation.md",
            PROJECT_ROOT / "zh-CN/skill/SKILL.md",
            PROJECT_ROOT / "zh-CN/skill/references/workflow.md",
            PROJECT_ROOT / "zh-CN/skill/references/multi-source-distillation.md",
        )
        for path in paths:
            text = path.read_text(encoding="utf-8")
            with self.subTest(path=path.relative_to(PROJECT_ROOT)):
                self.assertNotIn("python skills/examlex/", text)
                self.assertIn("python run.py", text)
        for command in ("extract", "validate", "commit"):
            with self.subTest(command=command):
                self.assertIn(
                    f"python run.py {command}",
                    (PROJECT_ROOT / "skills/examlex/SKILL.md").read_text(encoding="utf-8"),
                )
    def test_workflows_use_least_privilege_and_immutable_action_pins(self):
        ci = (PROJECT_ROOT / ".github/workflows/ci.yml").read_text(encoding="utf-8")
        codeql = (PROJECT_ROOT / ".github/workflows/codeql.yml").read_text(
            encoding="utf-8"
        )

        self.assertIn("permissions:\n  contents: read", ci)
        uses = re.findall(r"uses:\s*([^\s#]+)", ci + "\n" + codeql)
        self.assertTrue(uses)
        for action in uses:
            self.assertRegex(action, r"@[0-9a-f]{40}$")
        self.assertIn(
            "actions/checkout@9c091bb21b7c1c1d1991bb908d89e4e9dddfe3e0", ci
        )
        self.assertIn(
            "actions/setup-python@ece7cb06caefa5fff74198d8649806c4678c61a1", ci
        )
        self.assertIn(
            "github/codeql-action/init@99df26d4f13ea111d4ec1a7dddef6063f76b97e9",
            codeql,
        )
        self.assertIn(
            "github/codeql-action/analyze@99df26d4f13ea111d4ec1a7dddef6063f76b97e9",
            codeql,
        )

    def test_repository_vocabulary_contract_is_valid(self):
        errors: list[str] = []

        validate_repo.validate_vocab_contracts(PROJECT_ROOT, errors)

        self.assertEqual([], errors)

    def test_repository_source_catalog_contract_is_valid(self):
        errors: list[str] = []

        validate_repo.validate_source_catalog_contracts(PROJECT_ROOT, errors)

        self.assertEqual([], errors)

    def test_source_catalog_rejects_unverified_a_level_claim(self):
        with copy_project() as temp:
            root = Path(temp) / "repo"
            path = root / "skills" / "examlex" / "assets" / "data" / "source-catalog.json"
            catalog = json.loads(path.read_text(encoding="utf-8"))
            catalog["sources"][0]["usage"][0]["evidence"] = "A"
            path.write_text(
                json.dumps(catalog, ensure_ascii=False, indent=2) + "\n",
                encoding="utf-8",
            )
            errors: list[str] = []
            validate_repo.validate_source_catalog_contracts(root, errors)

        self.assertTrue(any("must cite article trace ids" in error for error in errors))

    def test_detects_invalid_packaged_template_contract(self):
        with copy_project() as temp:
            root = Path(temp) / "repo"
            invalid = '{"total_items": 0, "correct_items": 0}\n'
            for relative in (
                "examlex/assets/templates/exercise-record.json",
                "skills/examlex/assets/templates/exercise-record.json",
            ):
                (root / relative).write_text(invalid, encoding="utf-8")

            result = validate_repo.validate_project(root)

        self.assertTrue(
            any("practice template must contain a JSON list" in error for error in result.errors),
            result.errors,
        )

    def test_detects_missing_chinese_document_counterpart(self):
        with copy_project() as temp:
            root = Path(temp) / "repo"
            (root / "zh-CN" / "docs" / "configuration.md").unlink(missing_ok=True)

            result = validate_repo.validate_project(root)

        self.assertTrue(
            any(
                "missing Chinese documentation counterpart" in error
                and "zh-CN/docs/configuration.md" in error
                for error in result.errors
            )
        )

    def test_detects_external_url_in_published_markdown(self):
        with copy_project() as temp:
            root = Path(temp) / "repo"
            readme = root / "README.md"
            marker = "https" + "://example.invalid/source"
            readme.write_text(
                readme.read_text(encoding="utf-8") + f"\n{marker}\n",
                encoding="utf-8",
            )

            result = validate_repo.validate_project(root)

        self.assertTrue(any("external URL" in error for error in result.errors))

    def test_allowed_url_prefix_cannot_hide_bare_external_url(self):
        with copy_project() as temp:
            root = Path(temp) / "repo"
            readme = root / "README.md"
            readme.write_text(
                readme.read_text(encoding="utf-8")
                + "\nhttps://github.com/SFEW888/ExamLex.evil.invalid\n",
                encoding="utf-8",
            )
            result = validate_repo.validate_project(root)

        self.assertTrue(any("external URL" in error for error in result.errors))

    def test_allowed_badge_prefix_cannot_hide_markdown_external_url(self):
        with copy_project() as temp:
            root = Path(temp) / "repo"
            readme = root / "README.md"
            readme.write_text(
                readme.read_text(encoding="utf-8")
                + "\n[bad](https://img.shields.io/badge/License-MIT-yellow.svg.evil)\n",
                encoding="utf-8",
            )
            result = validate_repo.validate_project(root)

        self.assertTrue(any("external URL" in error for error in result.errors))

    def test_allows_project_status_badges_in_bilingual_readmes(self):
        result = validate_repo.validate_project(PROJECT_ROOT)

        badge_errors = [
            error
            for error in result.errors
            if "badge.svg" in error or "img.shields.io" in error
        ]
        self.assertEqual([], badge_errors)

    def test_validator_does_not_require_an_english_readme_roadmap(self):
        result = validate_repo.validate_project(PROJECT_ROOT)

        self.assertFalse(any("README.md must include ## Roadmap" in error for error in result.errors))

    def test_detects_broken_local_markdown_link(self):
        with copy_project() as temp:
            root = Path(temp) / "repo"
            readme = root / "README.md"
            readme.write_text(
                readme.read_text(encoding="utf-8")
                + "\n[missing](docs/not-present.md)\n",
                encoding="utf-8",
            )

            result = validate_repo.validate_project(root)

        self.assertTrue(
            any("broken local Markdown link" in error for error in result.errors)
        )

    def test_public_documentation_names_the_canonical_repository(self):
        readme = (PROJECT_ROOT / "README.md").read_text(encoding="utf-8")
        zh_readme = (PROJECT_ROOT / "zh-CN" / "README.md").read_text(encoding="utf-8")
        env_example = (PROJECT_ROOT / ".env.example").read_text(encoding="utf-8")

        repository_url = "https://github.com/SFEW888/ExamLex"
        for text in (readme, zh_readme):
            self.assertNotIn("your-org", text)
            self.assertIn(repository_url, text)
        self.assertIn("SILICONFLOW_API_KEY=", env_example)
        self.assertIn("EXAMLEX_PYTHON=python", env_example)
        self.assertNotIn("EXAMLEX_PROMPT_MODE", env_example)

    def test_public_agent_and_cli_install_contract_is_documented(self):
        repository_url = "https://github.com/SFEW888/ExamLex"
        git_install = f"git+{repository_url}.git"
        documents = [
            PROJECT_ROOT / "README.md",
            PROJECT_ROOT / "zh-CN" / "README.md",
            PROJECT_ROOT / "docs" / "getting-started.md",
            PROJECT_ROOT / "zh-CN" / "docs" / "getting-started.md",
        ]

        for path in documents:
            with self.subTest(path=path.relative_to(PROJECT_ROOT)):
                text = path.read_text(encoding="utf-8")
                self.assertIn(repository_url, text)
                self.assertIn("git clone", text)
                self.assertIn(git_install, text)

        pyproject = (PROJECT_ROOT / "pyproject.toml").read_text(encoding="utf-8")
        self.assertIn('[project.urls]', pyproject)
        self.assertIn(repository_url, pyproject)

        for installer in ("install.ps1", "install.sh"):
            with self.subTest(installer=installer):
                text = (PROJECT_ROOT / installer).read_text(encoding="utf-8")
                self.assertIn(repository_url, text)
                self.assertIn("help", text.lower())

    def test_agent_entrypoints_reference_the_public_repository(self):
        repository_url = "https://github.com/SFEW888/ExamLex"
        documents = [
            PROJECT_ROOT / "SKILL.md",
            PROJECT_ROOT / "integrations" / "claude-code" / "README.md",
            PROJECT_ROOT / "integrations" / "codex-cli" / "README.md",
            PROJECT_ROOT / "integrations" / "codex-app" / "README.md",
            PROJECT_ROOT / "zh-CN" / "integrations" / "claude-code.md",
            PROJECT_ROOT / "zh-CN" / "integrations" / "codex-cli.md",
            PROJECT_ROOT / "zh-CN" / "integrations" / "codex-app.md",
        ]

        for path in documents:
            with self.subTest(path=path.relative_to(PROJECT_ROOT)):
                text = path.read_text(encoding="utf-8")
                self.assertIn(repository_url, text)
                self.assertNotIn("unpublished", text.lower())
                self.assertNotIn("尚未发布", text)

    def test_bilingual_docs_document_video_toolchain(self):
        documents = [
            PROJECT_ROOT / "README.md",
            PROJECT_ROOT / "zh-CN" / "README.md",
            PROJECT_ROOT / "docs" / "getting-started.md",
            PROJECT_ROOT / "zh-CN" / "docs" / "getting-started.md",
            PROJECT_ROOT / "docs" / "configuration.md",
            PROJECT_ROOT / "zh-CN" / "docs" / "configuration.md",
        ]

        for path in documents:
            with self.subTest(path=path.relative_to(PROJECT_ROOT)):
                text = path.read_text(encoding="utf-8")
                self.assertIn("yt-dlp", text)
                self.assertIn("ffmpeg", text)
                self.assertIn("whisper", text.lower())
                self.assertIn("SILICONFLOW_API_KEY", text)

    def test_bilingual_readmes_link_to_official_dependency_sites(self):
        official_links = {
            "https://github.com/yt-dlp/yt-dlp",
            "https://ffmpeg.org/download.html",
            "https://github.com/openai/whisper",
            "https://poppler.freedesktop.org/",
            "https://calibre-ebook.com/download",
        }
        readmes = [
            PROJECT_ROOT / "README.md",
            PROJECT_ROOT / "zh-CN" / "README.md",
        ]

        for path in readmes:
            with self.subTest(path=path.relative_to(PROJECT_ROOT)):
                text = path.read_text(encoding="utf-8")
                for link in official_links:
                    self.assertIn(link, text)

        result = validate_repo.validate_project(PROJECT_ROOT)
        self.assertEqual([], result.errors)

    def test_bilingual_readmes_cover_the_current_feature_contract(self):
        readmes = {
            PROJECT_ROOT / "README.md": (
                "### Installation Verification",
                "## Workflow",
                "## Use Cases",
                "### Design Principles",
                "## Data Model",
            ),
            PROJECT_ROOT / "zh-CN" / "README.md": (
                "### 安装后验证",
                "## 使用流程",
                "## 适用场景",
                "### 设计原则",
                "## 数据模型",
            ),
        }
        shared_markers = (
            "Python 3.10",
            "Python 3.11",
            "Python 3.12",
            "Python 3.13",
            "examlex backup",
            "examlex report",
            "exercise-record.json",
            "writing-version-record.yaml",
            "strategy-library.json",
            "examlex ops-check",
        )

        for path, language_markers in readmes.items():
            with self.subTest(path=path.relative_to(PROJECT_ROOT)):
                text = path.read_text(encoding="utf-8")
                for marker in (*language_markers, *shared_markers):
                    self.assertIn(marker, text)

    def test_bilingual_readmes_have_current_badges_and_language_switches(self):
        common_badges = (
            "https://github.com/SFEW888/ExamLex/actions/workflows/ci.yml/badge.svg",
            "https://github.com/SFEW888/ExamLex/actions/workflows/codeql.yml/badge.svg",
            "https://img.shields.io/badge/Python-3.10--3.13-blue.svg",
        )
        readme_contracts = {
            PROJECT_ROOT / "README.md": (
                "[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)",
                "[![Skills](https://img.shields.io/badge/Skills-9-brightgreen.svg)](#tutor-roles)",
                "[![Platforms](https://img.shields.io/badge/Platforms-4-blue.svg)](#platform-integration)",
                "[简体中文](zh-CN/README.md)",
            ),
            PROJECT_ROOT / "zh-CN" / "README.md": (
                "[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](../LICENSE)",
                "[![Skills](https://img.shields.io/badge/Skills-9-brightgreen.svg)](#八个助教角色)",
                "[![Platforms](https://img.shields.io/badge/Platforms-4-blue.svg)](#平台集成)",
                "[English](../README.md)",
            ),
        }

        for path, local_markers in readme_contracts.items():
            with self.subTest(path=path.relative_to(PROJECT_ROOT)):
                text = path.read_text(encoding="utf-8")
                for marker in (*common_badges, *local_markers):
                    self.assertIn(marker, text)

    def test_bilingual_readme_openings_list_all_supported_exams(self):
        readmes = (
            PROJECT_ROOT / "README.md",
            PROJECT_ROOT / "zh-CN" / "README.md",
        )

        for path in readmes:
            with self.subTest(path=path.relative_to(PROJECT_ROOT)):
                opening = "\n".join(path.read_text(encoding="utf-8").splitlines()[:30])
                for exam in ("CET-4", "CET-6", "TEM-4", "TEM-8", "Postgraduate English"):
                    self.assertIn(exam, opening)

    def test_bilingual_public_docs_omit_roadmap(self):
        readme = (PROJECT_ROOT / "README.md").read_text(encoding="utf-8")
        zh_readme = (PROJECT_ROOT / "zh-CN" / "README.md").read_text(encoding="utf-8")
        zh_optimization = (
            PROJECT_ROOT / "zh-CN" / "docs" / "optimization-plan.md"
        ).read_text(encoding="utf-8")

        self.assertNotIn("## Roadmap", readme)
        self.assertNotIn("[Roadmap]", readme)
        self.assertNotIn("路线图", zh_readme)
        self.assertNotIn("路线图", zh_optimization)
        self.assertFalse((PROJECT_ROOT / "docs" / "roadmap.md").exists())
        self.assertFalse((PROJECT_ROOT / "zh-CN" / "docs" / "roadmap.md").exists())

    def test_internal_bilingual_sync_plan_is_not_published(self):
        plan = PROJECT_ROOT / "docs" / "plans" / "2026-07-11-bilingual-documentation-sync.md"

        self.assertFalse(plan.exists())

    def test_bilingual_reference_pairs_cover_current_operational_contracts(self):
        document_contracts = {
            (
                PROJECT_ROOT / "docs" / "configuration.md",
                PROJECT_ROOT / "zh-CN" / "docs" / "configuration.md",
            ): ("darwin_max_rounds", "sessions_root", "ffmpeg_path", "to_dict()"),
            (
                PROJECT_ROOT / "skills" / "examlex" / "references" / "data-model.md",
                PROJECT_ROOT / "zh-CN" / "skill" / "references" / "data-model.md",
            ): ("strategy-library.json", "approval_evidence", "strategy_sha256", "lifecycle_status", "revisions"),
            (
                PROJECT_ROOT / "skills" / "examlex" / "references" / "multi-source-distillation.md",
                PROJECT_ROOT / "zh-CN" / "skill" / "references" / "multi-source-distillation.md",
            ): ("validation_report.json", "evaluation.json", "strategy_sha256", "approval_evidence", "%LOCALAPPDATA%"),
            (
                PROJECT_ROOT / "skills" / "examlex" / "references" / "workflow.md",
                PROJECT_ROOT / "zh-CN" / "skill" / "references" / "workflow.md",
            ): (
                "python run.py extract",
                "python run.py validate",
                "python run.py commit",
                "approved",
            ),
            (
                PROJECT_ROOT
                / "skills"
                / "examlex"
                / "references"
                / "answer-explanation-standard.md",
                PROJECT_ROOT
                / "zh-CN"
                / "skill"
                / "references"
                / "answer-explanation-standard.md",
            ): (
                "CET4",
                "CET6",
                "POSTGRADUATE_ENGLISH",
                "TEM4",
                "TEM8",
                "answer_key",
                "question_translation",
                "option_translation",
                "evidence_anchor",
                "evidence_scope",
                "evidence_translation",
                "distractor_analysis",
                "error_tag",
                "learner_retry",
                "reference_translation",
                "idea_bank",
                "topic_vocabulary",
                "reusable_templates",
                "sentence_intent_analysis",
                "clause_map",
                "keyword_deliberation",
                "translation_build",
                "Section A",
                "Section B",
                "Section C",
            ),
            (
                PROJECT_ROOT / "docs" / "usage.md",
                PROJECT_ROOT / "zh-CN" / "docs" / "usage.md",
            ): ("--plan-task-index", "writing-version", "summarize-errors", "backup"),
            (
                PROJECT_ROOT / "docs" / "tem4.md",
                PROJECT_ROOT / "zh-CN" / "docs" / "tem4.md",
            ): ("examlex check", "examlex plan", "tem4-core-100.json"),
            (
                PROJECT_ROOT / "docs" / "tem8.md",
                PROJECT_ROOT / "zh-CN" / "docs" / "tem8.md",
            ): ("examlex check", "examlex plan", "tem8-core-100.json", "examlex log"),
        }

        for paths, markers in document_contracts.items():
            for path in paths:
                with self.subTest(path=path.relative_to(PROJECT_ROOT)):
                    text = path.read_text(encoding="utf-8")
                    for marker in markers:
                        self.assertIn(marker, text)

    def test_detects_remote_install_placeholder(self):
        with copy_project() as temp:
            root = Path(temp) / "repo"
            readme = root / "README.md"
            readme.write_text(
                readme.read_text(encoding="utf-8") + "\nyour-org/examlex\n",
                encoding="utf-8",
            )

            result = validate_repo.validate_project(root)

        self.assertTrue(any("remote install placeholder" in e for e in result.errors))

    def test_current_repo_uses_examlex_identity(self):
        result = validate_repo.validate_project(PROJECT_ROOT)

        self.assertEqual([], result.errors)
        self.assertTrue((PROJECT_ROOT / "examlex" / "__init__.py").is_file())
        self.assertTrue((PROJECT_ROOT / "skills" / "examlex" / "SKILL.md").is_file())

    def test_detects_legacy_product_identifier(self):
        with copy_project() as temp:
            root = Path(temp) / "repo"
            legacy = "english" + "-exam-ai-tutor"
            (root / "legacy-product-name.txt").write_text(legacy, encoding="utf-8")

            result = validate_repo.validate_project(root)

        self.assertTrue(
            any("legacy product identifier" in error for error in result.errors)
        )

    def test_current_repo_is_valid_without_readme_warning(self):
        result = validate_repo.validate_project(PROJECT_ROOT)

        self.assertEqual([], result.errors)
        self.assertEqual([], result.warnings)

    def test_ignores_local_git_worktrees(self):
        with copy_project() as temp:
            root = Path(temp) / "repo"
            worktree_readme = root / ".worktrees" / "stale" / "README.md"
            worktree_readme.parent.mkdir(parents=True)
            remote_url = "https" + "://example.invalid/source"
            legacy_name = "english" + "-exam-ai-tutor"
            worktree_readme.write_text(
                f"{remote_url}\n{legacy_name}\n",
                encoding="utf-8",
            )

            result = validate_repo.validate_project(root)

        self.assertEqual([], result.errors)
        self.assertEqual([], result.warnings)

    def test_reports_missing_required_portable_directory(self):
        with copy_project() as temp:
            root = Path(temp) / "repo"
            shutil.rmtree(root / SKILL_DIR / "assets")

            result = validate_repo.validate_project(root)

        self.assertTrue(any("assets" in error for error in result.errors))

    def test_detects_forbidden_private_prompt_sentence(self):
        with copy_project() as temp:
            root = Path(temp) / "repo"
            skill = root / SKILL_DIR / "SKILL.md"
            skill.write_text(
                skill.read_text(encoding="utf-8")
                + "\n"
                + " ".join(("Act as a strict", "but helpful English", "grammar teacher"))
                + "\n",
                encoding="utf-8",
            )

            result = validate_repo.validate_project(root)

        self.assertTrue(any("forbidden private prompt" in error for error in result.errors))

    def test_detects_metadata_issue(self):
        with copy_project() as temp:
            root = Path(temp) / "repo"
            skill = root / SKILL_DIR / "SKILL.md"
            skill.write_text(
                "---\nname: examlex\ndescription: Supports exams.\n---\n\n# Skill\n",
                encoding="utf-8",
            )

            result = validate_repo.validate_project(root)

        self.assertTrue(any("description" in error and "Use when" in error for error in result.errors))

    def test_detects_mirror_mismatch(self):
        with copy_project() as temp:
            root = Path(temp) / "repo"
            script = root / "skills" / "examlex" / "scripts" / "record_practice.py"
            script.write_text(script.read_text(encoding="utf-8") + "\n# mismatch\n", encoding="utf-8")

            result = validate_repo.validate_project(root)

        self.assertTrue(any("mirror mismatch" in error for error in result.errors))

    def test_detects_extra_generated_python_file(self):
        with copy_project() as temp:
            root = Path(temp) / "repo"
            extra = root / "examlex" / "scripts" / "manual-only.py"
            extra.write_text("VALUE = 1\n", encoding="utf-8")

            result = validate_repo.validate_project(root)

        self.assertIn(
            "extra generated Python file: scripts/manual-only.py",
            result.errors,
        )

    def test_detects_resource_mirror_mismatch(self):
        with copy_project() as temp:
            root = Path(temp) / "repo"
            package_asset = root / "examlex" / "assets" / "data" / "vocab-test-words.json"
            package_asset.parent.mkdir(parents=True, exist_ok=True)
            package_asset.write_text("{}\n", encoding="utf-8")

            result = validate_repo.validate_project(root)

        self.assertTrue(
            any("resource mirror mismatch" in error for error in result.errors)
        )

    def test_importable_package_contains_skill_references(self):
        package_reference = (
            PROJECT_ROOT / "examlex" / "references" / "darwin-rubric.md"
        )

        self.assertTrue(package_reference.is_file(), str(package_reference))

    def test_detects_reference_mirror_mismatch(self):
        with copy_project() as temp:
            root = Path(temp) / "repo"
            package_reference = (
                root / "examlex" / "references" / "darwin-rubric.md"
            )
            package_reference.write_text("# mismatch\n", encoding="utf-8")

            result = validate_repo.validate_project(root)

        self.assertTrue(
            any(
                "resource mirror mismatch: references/darwin-rubric.md" in error
                for error in result.errors
            )
        )

    def test_detects_missing_github_health_file(self):
        with copy_project() as temp:
            root = Path(temp) / "repo"
            (root / "SECURITY.md").unlink(missing_ok=True)

            result = validate_repo.validate_project(root)

        self.assertTrue(any("Missing GitHub health file: SECURITY.md" in error for error in result.errors))

    def test_detects_missing_github_issue_template(self):
        with copy_project() as temp:
            root = Path(temp) / "repo"
            (root / ".github" / "ISSUE_TEMPLATE" / "bug_report.yml").unlink(missing_ok=True)

            result = validate_repo.validate_project(root)

        self.assertTrue(any("Missing GitHub issue template" in error for error in result.errors))

    def test_detects_missing_ci_workflow(self):
        with copy_project() as temp:
            root = Path(temp) / "repo"
            (root / ".github" / "workflows" / "ci.yml").unlink(missing_ok=True)

            result = validate_repo.validate_project(root)

        self.assertTrue(any("Missing GitHub workflow" in error for error in result.errors))

    def test_detects_missing_editorconfig(self):
        with copy_project() as temp:
            root = Path(temp) / "repo"
            (root / ".editorconfig").unlink(missing_ok=True)

            result = validate_repo.validate_project(root)

        self.assertTrue(any("Missing project quality file: .editorconfig" in error for error in result.errors))

    def test_detects_missing_env_example(self):
        with copy_project() as temp:
            root = Path(temp) / "repo"
            (root / ".env.example").unlink(missing_ok=True)

            result = validate_repo.validate_project(root)

        self.assertTrue(any("Missing project quality file: .env.example" in error for error in result.errors))

    def test_detects_missing_secret_baseline(self):
        with copy_project() as temp:
            root = Path(temp) / "repo"
            (root / ".secrets.baseline").unlink(missing_ok=True)

            result = validate_repo.validate_project(root)

        self.assertTrue(
            any("Missing project quality file: .secrets.baseline" in error for error in result.errors)
        )

    def test_detects_nonportable_secret_baseline(self):
        with copy_project() as temp:
            root = Path(temp) / "repo"
            baseline_path = root / ".secrets.baseline"
            baseline = json.loads(baseline_path.read_text(encoding="utf-8"))
            filename = next(iter(baseline["results"]))
            findings = baseline["results"].pop(filename)
            findings[0]["filename"] = filename.replace("/", "\\")
            baseline["results"][filename.replace("/", "\\")] = findings
            baseline_path.write_text(json.dumps(baseline), encoding="utf-8")

            result = validate_repo.validate_project(root)

        self.assertTrue(any("portable forward slashes" in error for error in result.errors))

    def test_detects_unaudited_secret_baseline_finding(self):
        with copy_project() as temp:
            root = Path(temp) / "repo"
            baseline_path = root / ".secrets.baseline"
            baseline = json.loads(baseline_path.read_text(encoding="utf-8"))
            filename = next(iter(baseline["results"]))
            baseline["results"][filename][0]["is_secret"] = True
            baseline_path.write_text(json.dumps(baseline), encoding="utf-8")

            result = validate_repo.validate_project(root)

        self.assertTrue(any("not audited false-positive" in error for error in result.errors))

    def test_detects_missing_public_install_entrypoint(self):
        with copy_project() as temp:
            root = Path(temp) / "repo"
            (root / "install.sh").unlink(missing_ok=True)

            result = validate_repo.validate_project(root)

        self.assertTrue(any("Missing required root file: install.sh" in error for error in result.errors))

    def test_detects_missing_root_skill_for_one_line_installers(self):
        with copy_project() as temp:
            root = Path(temp) / "repo"
            (root / "SKILL.md").unlink(missing_ok=True)

            result = validate_repo.validate_project(root)

        self.assertTrue(any("Missing required root file: SKILL.md" in error for error in result.errors))

    def test_detects_missing_cli_reference(self):
        with copy_project() as temp:
            root = Path(temp) / "repo"
            (root / "cli-reference.md").unlink(missing_ok=True)

            result = validate_repo.validate_project(root)

        self.assertTrue(any("Missing required root file: cli-reference.md" in error for error in result.errors))

    def test_detects_missing_examlex_bash_wrapper(self):
        with copy_project() as temp:
            root = Path(temp) / "repo"
            (root / "bin" / "examlex").unlink(missing_ok=True)

            result = validate_repo.validate_project(root)

        self.assertTrue(any("Missing user CLI wrapper: bin/examlex" in error for error in result.errors))

    def test_detects_missing_examlex_powershell_wrapper(self):
        with copy_project() as temp:
            root = Path(temp) / "repo"
            (root / "bin" / "examlex.ps1").unlink(missing_ok=True)

            result = validate_repo.validate_project(root)

        self.assertTrue(any("Missing user CLI wrapper: bin/examlex.ps1" in error for error in result.errors))

    def test_detects_missing_quality_documentation(self):
        with copy_project() as temp:
            root = Path(temp) / "repo"
            (root / "docs" / "getting-started.md").unlink(missing_ok=True)

            result = validate_repo.validate_project(root)

        self.assertTrue(any("Missing quality documentation" in error for error in result.errors))

    def test_detects_missing_codeql_workflow(self):
        with copy_project() as temp:
            root = Path(temp) / "repo"
            (root / ".github" / "workflows" / "codeql.yml").unlink(missing_ok=True)

            result = validate_repo.validate_project(root)

        self.assertTrue(any("Missing GitHub workflow" in error for error in result.errors))

    def test_github_workflows_use_current_node_runtime_actions(self):
        ci = (PROJECT_ROOT / ".github" / "workflows" / "ci.yml").read_text(
            encoding="utf-8"
        )
        codeql = (
            PROJECT_ROOT / ".github" / "workflows" / "codeql.yml"
        ).read_text(encoding="utf-8")

        self.assertIn("actions/checkout@9c091bb21b7c1c1d1991bb908d89e4e9dddfe3e0 # v7", ci)
        self.assertIn("actions/setup-python@ece7cb06caefa5fff74198d8649806c4678c61a1 # v6", ci)
        self.assertIn("actions/checkout@9c091bb21b7c1c1d1991bb908d89e4e9dddfe3e0 # v7", codeql)
        self.assertIn("github/codeql-action/init@99df26d4f13ea111d4ec1a7dddef6063f76b97e9 # v4", codeql)
        self.assertIn("github/codeql-action/analyze@99df26d4f13ea111d4ec1a7dddef6063f76b97e9 # v4", codeql)

    def test_ci_covers_supported_python_versions_and_platforms(self):
        ci = (PROJECT_ROOT / ".github" / "workflows" / "ci.yml").read_text(
            encoding="utf-8"
        )
        self.assertIn("os: [ubuntu-latest, windows-latest]", ci)
        self.assertIn(
            'python-version: ["3.10", "3.11", "3.12", "3.13"]',
            ci,
        )
        self.assertIn("fail-fast: false", ci)
        self.assertIn("python -m coverage report", ci)
        self.assertIn("python -m ruff check .", ci)
        self.assertIn("needs: [quality, test]", ci)
        self.assertEqual(1, ci.count("python -m build"))

    def test_detects_missing_readme_quality_section(self):
        with copy_project() as temp:
            root = Path(temp) / "repo"
            readme = root / "README.md"
            readme.write_text("# ExamLex\n", encoding="utf-8")

            result = validate_repo.validate_project(root)

        self.assertTrue(any("README.md must include" in error for error in result.errors))

    def test_detects_readme_without_public_skill_install_flow(self):
        with copy_project() as temp:
            root = Path(temp) / "repo"
            readme = root / "README.md"
            text = readme.read_text(encoding="utf-8")
            text = text.replace("python -m pip install -e .", "python -m pip --version")
            readme.write_text(text, encoding="utf-8")

            result = validate_repo.validate_project(root)

        self.assertTrue(any("README.md Quick Start must explain Skill installation" in error for error in result.errors))

    def test_detects_readme_without_agent_skill_invocation_flow(self):
        with copy_project() as temp:
            root = Path(temp) / "repo"
            readme = root / "README.md"
            text = readme.read_text(encoding="utf-8")
            text = text.replace("/grammar-corrector", "/grammar-check")
            readme.write_text(text, encoding="utf-8")

            result = validate_repo.validate_project(root)

        self.assertTrue(any("README.md must explain Agent Skill invocation" in error for error in result.errors))

    def test_detects_dollar_style_readme_skill_invocation(self):
        with copy_project() as temp:
            root = Path(temp) / "repo"
            readme = root / "README.md"
            readme.write_text(readme.read_text(encoding="utf-8") + "\n" + "$" + "grammar-corrector\n", encoding="utf-8")

            result = validate_repo.validate_project(root)

        self.assertTrue(any("slash Skill invocation" in error for error in result.errors))

    def test_detects_dollar_style_skill_invocation_outside_readme(self):
        with copy_project() as temp:
            root = Path(temp) / "repo"
            usage = root / "docs" / "usage.md"
            usage.write_text(usage.read_text(encoding="utf-8") + "\n" + "$" + "learning-planner\n", encoding="utf-8")

            result = validate_repo.validate_project(root)

        self.assertTrue(any("forbidden dollar-style Skill call" in error for error in result.errors))

    def test_detects_missing_shortcut_skill(self):
        with copy_project() as temp:
            root = Path(temp) / "repo"
            shutil.rmtree(root / "skills" / "grammar-corrector")

            result = validate_repo.validate_project(root)

        self.assertTrue(any("Missing shortcut Skill" in error for error in result.errors))

    def test_detects_shortcut_skill_metadata_mismatch(self):
        with copy_project() as temp:
            root = Path(temp) / "repo"
            shortcut = root / "skills" / "grammar-corrector" / "SKILL.md"
            shortcut.write_text("---\nname: grammar-check\ndescription: Supports grammar.\n---\n", encoding="utf-8")

            result = validate_repo.validate_project(root)

        self.assertTrue(any("Shortcut Skill grammar-corrector" in error for error in result.errors))

    def test_detects_local_machine_path_in_public_docs(self):
        with copy_project() as temp:
            root = Path(temp) / "repo"
            readme = root / "README.md"
            local_path = "D:" + "\\workspace\\." + "worktrees\\examlex"
            readme.write_text(
                readme.read_text(encoding="utf-8") + f"\n{local_path}\n",
                encoding="utf-8",
            )

            result = validate_repo.validate_project(root)

        self.assertTrue(
            any("Public-safety scan found local Git worktree path" in error for error in result.errors)
        )

    def test_public_safety_scan_detects_user_home_paths_cross_platform(self):
        examples = (
            "C:" + "\\Users\\alice\\workspace\\project",
            "/" + "home/alice/workspace/project",
        )
        for local_path in examples:
            with self.subTest(local_path=local_path), copy_project() as temp:
                root = Path(temp) / "repo"
                readme = root / "README.md"
                readme.write_text(
                    readme.read_text(encoding="utf-8") + f"\n{local_path}\n",
                    encoding="utf-8",
                )

                result = validate_repo.validate_project(root)

            self.assertTrue(any("Public-safety scan found" in error for error in result.errors))

    def test_public_safety_scan_detects_tokens_without_echoing_them(self):
        fixture_value = "github" + "_pat_" + "A" * 32
        with copy_project() as temp:
            root = Path(temp) / "repo"
            readme = root / "README.md"
            readme.write_text(
                readme.read_text(encoding="utf-8") + f"\n{fixture_value}\n",
                encoding="utf-8",
            )

            result = validate_repo.validate_project(root)

        matching = [error for error in result.errors if "GitHub access token" in error]
        self.assertTrue(matching)
        self.assertTrue(all(fixture_value not in error for error in matching))

    def test_public_safety_scan_detects_credentialed_proxy_without_echoing_it(self):
        fixture_value = "https" + "://alice:private-value@proxy.invalid:8443"
        with copy_project() as temp:
            root = Path(temp) / "repo"
            env_example = root / ".env.example"
            env_example.write_text(
                env_example.read_text(encoding="utf-8") + f"\nHTTPS_PROXY={fixture_value}\n",
                encoding="utf-8",
            )

            result = validate_repo.validate_project(root)

        matching = [error for error in result.errors if "credential-bearing proxy URL" in error]
        self.assertTrue(matching)
        self.assertTrue(all(fixture_value not in error for error in matching))


if __name__ == "__main__":
    unittest.main()
