#!/usr/bin/env python3
"""Install an ExamLex wheel in isolation and exercise its runtime contract."""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import tempfile
import venv
from pathlib import Path


def resolve_wheel(value: Path) -> Path:
    path = value.resolve()
    if path.is_dir():
        wheels = sorted(path.glob("examlex-*.whl"))
        if len(wheels) != 1:
            raise ValueError(f"Expected exactly one ExamLex wheel in {path}, found {len(wheels)}")
        return wheels[0]
    if not path.is_file() or path.suffix != ".whl":
        raise ValueError(f"Wheel not found: {path}")
    return path


def run_checked(command: list[str], cwd: Path, env: dict[str, str]) -> subprocess.CompletedProcess[str]:
    result = subprocess.run(
        command,
        cwd=cwd,
        env=env,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )
    if result.returncode != 0:
        raise RuntimeError(
            f"Command failed ({result.returncode}): {' '.join(command)}\n"
            f"stdout:\n{result.stdout}\nstderr:\n{result.stderr}"
        )
    return result


def smoke_test(wheel: Path) -> dict[str, object]:
    with tempfile.TemporaryDirectory(prefix="examlex-wheel-smoke-") as temp:
        root = Path(temp)
        venv_dir = root / "venv"
        runtime_dir = root / "runtime"
        runtime_dir.mkdir()
        venv.EnvBuilder(with_pip=True, clear=True).create(venv_dir)

        if os.name == "nt":
            python = venv_dir / "Scripts" / "python.exe"
            examlex_command = venv_dir / "Scripts" / "examlex.exe"
        else:
            python = venv_dir / "bin" / "python"
            examlex_command = venv_dir / "bin" / "examlex"

        env = os.environ.copy()
        env["PYTHONUTF8"] = "1"
        run_checked(
            [str(python), "-m", "pip", "install", "--no-deps", str(wheel)],
            runtime_dir,
            env,
        )
        help_result = run_checked([str(examlex_command), "--help"], runtime_dir, env)
        resume_help_result = run_checked(
            [str(examlex_command), "resume", "--help"], runtime_dir, env
        )
        prompt_check_help_result = run_checked(
            [str(examlex_command), "prompt-check", "--help"], runtime_dir, env
        )
        tutor_prepare_help_result = run_checked(
            [str(examlex_command), "tutor-prepare", "--help"], runtime_dir, env
        )
        if "usage: examlex" not in help_result.stdout:
            raise RuntimeError("Installed examlex command did not expose its main help")
        if "usage: examlex resume" not in resume_help_result.stdout:
            raise RuntimeError("Installed examlex command did not expose resume help")
        if "--private-dir" not in prompt_check_help_result.stdout:
            raise RuntimeError("Installed examlex command did not expose prompt-check help")
        if "--request" not in tutor_prepare_help_result.stdout:
            raise RuntimeError("Installed examlex command did not expose tutor-prepare help")
        resource_result = run_checked(
            [
                str(python),
                "-c",
                (
                    "import json; from pathlib import Path; import examlex; "
                    "from examlex.scripts.estimate_vocabulary import _DEFAULT_REF; "
                    "from examlex.scripts.tutor_prompts import load_role_contracts; "
                    "from examlex.scripts.tutor_runtime import prepare_tutor_turn; "
                    "root = Path(examlex.__file__).resolve().parent; "
                    "required = [root / 'SKILL.md', root / 'assets' / 'schemas', "
                    "root / 'assets' / 'templates', root / 'references', _DEFAULT_REF, "
                    "root / 'references' / 'tutor-role-contracts.json', "
                    "root / 'references' / 'tutor-runtime.md']; "
                    "missing = [str(path) for path in required if not path.exists()]; "
                    "assert not missing, missing; assert len(load_role_contracts()) == 8; "
                    "assert prepare_tutor_turn('Correct my grammar', "
                    "role_id='grammar-corrector').clarification_questions; "
                    "print(json.dumps([str(path) for path in required]))"
                ),
            ],
            runtime_dir,
            env,
        )
        vocab_result = run_checked(
            [
                str(examlex_command),
                "vocab",
                "--interactive",
                "--bands",
                "1-1000",
                "--samples-per-band",
                "2",
                "--nonwords-per-band",
                "1",
            ],
            runtime_dir,
            env,
        )
        vocab_payload = json.loads(vocab_result.stdout)
        if len(vocab_payload.get("quiz_words", [])) != 3:
            raise RuntimeError("Vocabulary smoke output did not contain three quiz words")

        return {
            "wheel": str(wheel),
            "console_help": True,
            "resume_help": True,
            "prompt_check_help": True,
            "tutor_prepare_help": True,
            "resources": json.loads(resource_result.stdout),
            "quiz_word_count": len(vocab_payload["quiz_words"]),
        }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Smoke-test an isolated ExamLex wheel installation.")
    parser.add_argument("wheel", type=Path, help="Wheel file or directory containing one ExamLex wheel.")
    args = parser.parse_args(argv)

    try:
        wheel = resolve_wheel(args.wheel)
        result = smoke_test(wheel)
    except (ValueError, RuntimeError, OSError, json.JSONDecodeError) as exc:
        print(f"wheel smoke test failed: {exc}", file=sys.stderr)
        return 1
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
