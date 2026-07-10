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
        resource_result = run_checked(
            [
                str(python),
                "-c",
                (
                    "from examlex.scripts.estimate_vocabulary import _DEFAULT_REF; "
                    "assert _DEFAULT_REF.is_file(), _DEFAULT_REF; print(_DEFAULT_REF)"
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
            "console_help": "usage: examlex" in help_result.stdout,
            "resource": resource_result.stdout.strip(),
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
