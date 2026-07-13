"""Operational readiness checks — 13-point inspection for deployment safety.

Usage: examlex ops-check [--json]
"""

from __future__ import annotations

import json
import os
import platform
import shutil
import sys
import tempfile
import time
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from urllib.error import HTTPError
from urllib.request import HTTPRedirectHandler, Request, build_opener, urlopen

from .config import TutorConfig
from .common import load_data


class _RejectCredentialRedirectHandler(HTTPRedirectHandler):
    """Reject redirects for probes that carry an authorization header."""

    def redirect_request(self, req, fp, code, msg, headers, newurl):  # noqa: ANN001
        return None


def _safe_failure(label: str, exc: BaseException) -> str:
    """Describe a local failure without exposing paths, hosts, or credentials."""
    return f"{label} ({type(exc).__name__})"


# ═══════════════════════════════════════════
# Data structures
# ═══════════════════════════════════════════


@dataclass
class CheckResult:
    name: str
    status: str           # "pass" | "warn" | "fail" | "skip"
    message: str
    detail: dict[str, Any] = field(default_factory=dict)
    remedy: str = ""


@dataclass
class OpsReport:
    timestamp: str
    hostname: str
    platform: str
    python_version: str
    checks: list[CheckResult]
    summary: dict[str, int]

    def all_pass(self) -> bool:
        return self.summary.get("fail", 0) == 0


# ═══════════════════════════════════════════
# 1. Environment & Dependency Check
# ═══════════════════════════════════════════


def check_environment(cfg: TutorConfig) -> CheckResult:
    """Verify Python version, OS, and all external tool dependencies."""
    detail = {
        "python_version": sys.version,
        "platform": platform.platform(),
    }
    warnings = []

    # Python version
    py_ver = sys.version_info
    if py_ver < (3, 10):
        return CheckResult("environment", "fail", "Python 3.10+ required",
                           detail, "Install Python 3.10 or newer")
    if py_ver < (3, 11):
        warnings.append("Python 3.10 is EOL; consider upgrading to 3.11+")

    # External tools
    report = cfg.check_all_dependencies()
    detail["tools_available"] = dict(sorted(report.available.items()))
    detail["tools_missing"] = dict(sorted(report.missing.items()))

    for tool, hint in report.missing.items():
        warnings.append(f"{tool}: not found — {hint}")

    status = "warn" if warnings else "pass"
    return CheckResult("environment", status,
                       f"Python {sys.version.split()[0]}, {len(report.available)}/{len(report.available)+len(report.missing)} tools",
                       detail,
                       "; ".join(warnings) if warnings else "")


# ═══════════════════════════════════════════
# 2. Configuration Validation
# ═══════════════════════════════════════════


def check_config(cfg: TutorConfig) -> CheckResult:
    """Validate configuration integrity."""
    detail = {}
    issues = []

    # Check sessions_root is writable
    try:
        cfg.sessions_root.mkdir(parents=True, exist_ok=True)
        test_file = cfg.sessions_root / ".write_test"
        test_file.write_text("ok")
        test_file.unlink()
        detail["sessions_root_writable"] = True
    except (OSError, PermissionError) as exc:
        issues.append(_safe_failure("sessions_root is not writable", exc))
        detail["sessions_root_writable"] = False

    # Validate Darwin thresholds
    if cfg.darwin_pass_score < 0 or cfg.darwin_pass_score > 100:
        issues.append(f"darwin_pass_score {cfg.darwin_pass_score} out of range [0,100]")
    if cfg.darwin_max_rounds < 1 or cfg.darwin_max_rounds > 10:
        issues.append(f"darwin_max_rounds {cfg.darwin_max_rounds} out of range [1,10]")

    # Validate ASR config
    if cfg.asr_backend == "siliconflow" and not cfg.siliconflow_api_key:
        issues.append("ASR backend is siliconflow but SILICONFLOW_API_KEY is not set")

    # Check content limits
    if cfg.max_video_duration_seconds <= 0:
        issues.append("max_video_duration_seconds must be positive")
    if cfg.session_retention_hours <= 0:
        issues.append("session_retention_hours must be positive")
    if cfg.max_reproducible_artifact_bytes <= 0:
        issues.append("max_reproducible_artifact_bytes must be positive")
    if cfg.strategy_library_warning_bytes <= 0:
        issues.append("strategy_library_warning_bytes must be positive")

    status = "fail" if issues else "pass"
    return CheckResult("config", status,
                       "Configuration valid" if not issues else f"{len(issues)} config issues",
                       detail, "; ".join(issues) if issues else "")


# ═══════════════════════════════════════════
# 3. Permissions & Directory Check
# ═══════════════════════════════════════════


def check_permissions(cfg: TutorConfig) -> CheckResult:
    """Verify read/write permissions for all required directories."""
    detail = {}
    issues = []

    dirs_to_check = [
        ("sessions_root", cfg.sessions_root),
        ("current_working_dir", Path.cwd()),
    ]

    for name, path in dirs_to_check:
        try:
            path.mkdir(parents=True, exist_ok=True)
            read_ok = os.access(str(path), os.R_OK)
            write_ok = os.access(str(path), os.W_OK)
            detail[name] = {"readable": read_ok, "writable": write_ok}
            if not write_ok:
                issues.append(f"{name} is not writable")
        except (OSError, PermissionError) as exc:
            detail[name] = {"error": type(exc).__name__}
            issues.append(_safe_failure(name, exc))

    # Check temp directory
    try:
        with tempfile.NamedTemporaryFile(delete=True) as f:
            f.write(b"test")
        detail["temp_dir"] = "writable"
    except OSError as exc:
        detail["temp_dir"] = type(exc).__name__
        issues.append(_safe_failure("temp directory is not writable", exc))

    status = "fail" if issues else "pass"
    return CheckResult("permissions", status,
                       "All directories accessible" if not issues else f"{len(issues)} permission issues",
                       detail, "; ".join(issues) if issues else "")


# ═══════════════════════════════════════════
# 4. Port/Resource Check (CLI tool — mostly N/A)
# ═══════════════════════════════════════════


def check_ports() -> CheckResult:
    """Check for port/resource conflicts. N/A for CLI tool, but checks disk space."""
    detail = {}
    issues = []

    # Disk space check
    try:
        stat = shutil.disk_usage(str(Path.cwd()))
        free_gb = stat.free / (1024 ** 3)
        detail["disk_free_gb"] = round(free_gb, 1)
        detail["disk_total_gb"] = round(stat.total / (1024 ** 3), 1)
        if free_gb < 1.0:
            issues.append(f"Low disk space: {free_gb:.1f} GB free")
    except OSError as exc:
        detail["disk_check"] = type(exc).__name__

    # Memory check
    try:
        import psutil
        mem = psutil.virtual_memory()
        detail["memory_free_gb"] = round(mem.available / (1024 ** 3), 1)
        if mem.available < 512 * 1024 * 1024:  # < 512 MB
            issues.append("Low memory available")
    except ImportError:
        detail["memory_check"] = "psutil not installed (pip install psutil for memory check)"

    status = "warn" if issues else "pass"
    return CheckResult("ports_and_disk", status,
                       f"Disk: {detail.get('disk_free_gb', '?')} GB free" if "disk_free_gb" in detail else "Disk check ok",
                       detail, "; ".join(issues) if issues else "")


# ═══════════════════════════════════════════
# 5. Pre-run Quick Check
# ═══════════════════════════════════════════


def check_prerun(cfg: TutorConfig) -> CheckResult:
    """Fast sanity check before any distillation run."""
    detail = {}
    issues = []

    # Python imports work
    try:
        from .extractors.text import TextExtractor
        from .validators.format_checker import FormatChecker
        from .optimizers.ratchet import StrategyRatchet
        _ = FormatChecker, StrategyRatchet
        detail["core_imports"] = "ok"
    except ImportError as exc:
        issues.append(_safe_failure("Core import failed", exc))
        detail["core_imports"] = type(exc).__name__

    # at least one extractor is operational
    try:
        extractor = TextExtractor()
        deps = extractor.check_dependencies()
        if deps:
            detail["text_extractor_deps_missing"] = deps
        else:
            detail["text_extractor"] = "ready"
    except Exception as exc:
        issues.append(_safe_failure("TextExtractor init failed", exc))

    # sessions_root is usable
    try:
        test_session = cfg.sessions_root / "_pretest_" / "test"
        test_session.mkdir(parents=True, exist_ok=True)
        (test_session / "test.txt").write_text("ok")
        import shutil as _shutil
        _shutil.rmtree(str(cfg.sessions_root / "_pretest_"), ignore_errors=True)
        detail["session_init"] = "ok"
    except OSError as exc:
        issues.append(_safe_failure("Session init failed", exc))

    status = "fail" if issues else "pass"
    return CheckResult("prerun", status,
                       "Ready for distillation" if not issues else f"{len(issues)} pre-run issues",
                       detail, "; ".join(issues) if issues else "")


# ═══════════════════════════════════════════
# 6. Dry-run / Trial Run
# ═══════════════════════════════════════════


def check_dry_run(cfg: TutorConfig, library_path: str | None = None) -> CheckResult:
    """Perform a trial run with a minimal test strategy."""
    detail = {}
    errors = []

    try:
        import tempfile
        from .extractors.text import TextExtractor
        from .validators.format_checker import FormatChecker
        from .validators.darwin_structure import DarwinStructureScorer
        from .optimizers.ratchet import StrategyRatchet

        # 1. Test extraction
        detail["last_step"] = "extraction"
        tmpdir = Path(tempfile.mkdtemp())
        test_file = tmpdir / "test_strategy.md"
        test_file.write_text("# Test Strategy\n\nA test strategy for dry run.\n\n1. Step one\n2. Step two\n", encoding="utf-8")
        extractor = TextExtractor()
        result = extractor.extract(str(test_file), tmpdir / "artifacts")
        detail["extraction"] = "ok"
        detail["extraction_warnings"] = result.warnings

        # 2. Test validation
        detail["last_step"] = "validation"
        test_strategy = {
            "strategy_id": "dry-run-test-001",
            "title": "Dry Run Test Strategy",
            "content": "A test strategy for verification. It has enough content. More words here.",
            "steps": ["1. First step with detail", "2. Second step with detail"],
            "source_file": "test_strategy.md",
            "exam_types": ["CET4", "CET6"],
            "modules": ["reading"],
            "added_at": datetime.now(timezone.utc).strftime("%Y-%m-%d"),
        }
        checker = FormatChecker()
        fmt_report = checker.validate(test_strategy)
        detail["format_check"] = "pass" if fmt_report.passed else f"fail: {len(fmt_report.errors)} errors"

        detail["last_step"] = "scoring"
        scorer = DarwinStructureScorer()
        structure = scorer.score(test_strategy)
        detail["darwin_structure_score"] = round(structure.total, 1)

        # 3. Test ratchet + save (if library path provided)
        if library_path:
            detail["last_step"] = "library_write"
            lib_path = Path(library_path)
            trial_path = tmpdir / "strategy-library.json"
            if lib_path.exists():
                shutil.copy2(lib_path, trial_path)
            ratchet = StrategyRatchet()
            test_strategy["distillation_method"] = "direct"
            test_strategy["source_type"] = "text"
            scored = ratchet.baseline(test_strategy, structure.total)
            lib = load_data(trial_path) if trial_path.exists() else {"strategies": []}
            ratchet.apply(scored, lib, None, structure.total)
            StrategyRatchet.atomic_save(lib, trial_path)
            detail["library_write"] = "ok (temporary copy)"

        import shutil as _shutil
        _shutil.rmtree(str(tmpdir), ignore_errors=True)

    except (ImportError, OSError, json.JSONDecodeError, RuntimeError, ValueError) as exc:
        errors.append(
            _safe_failure(
                f"Dry run failed at {detail.get('last_step', 'start')}",
                exc,
            )
        )

    status = "fail" if errors else "pass"
    return CheckResult("dry_run", status,
                       "All subsystems operational" if not errors else f"Dry run failed: {errors[0][:80]}",
                       detail, "; ".join(errors) if errors else "")


# ═══════════════════════════════════════════
# 7-8. Scheduled Task Support
# ═══════════════════════════════════════════


def check_scheduler(cfg: TutorConfig) -> CheckResult:
    """Check cron/scheduler availability for automated tasks."""
    detail = {}
    detail["platform"] = platform.system()

    if platform.system() == "Windows":
        detail["scheduler"] = "Task Scheduler (taskschd.msc)"
        detail["recommendation"] = (
            "Use Task Scheduler to run the required examlex command "
            "for recurring distillations"
        )
    else:
        cron_available = shutil.which("crontab") is not None
        detail["cron_available"] = cron_available
        detail["scheduler"] = "crontab" if cron_available else "not found"
        detail["recommendation"] = (
            "Use crontab to run the required examlex command "
            "for recurring distillations"
            if cron_available
            else "Install cron, then use crontab to run the required examlex command"
        )

    return CheckResult("scheduler", "pass",
                       f"Scheduler: {detail['scheduler']}",
                       detail)


# ═══════════════════════════════════════════
# 9. Resource Monitoring
# ═══════════════════════════════════════════


def check_resources() -> CheckResult:
    """Monitor CPU, memory, disk usage."""
    detail = {}
    issues = []

    # CPU
    detail["cpu_count"] = os.cpu_count() or 0

    # Disk
    try:
        stat = shutil.disk_usage(str(Path.cwd()))
        detail["disk"] = {
            "total_gb": round(stat.total / (1024 ** 3), 1),
            "used_gb": round(stat.used / (1024 ** 3), 1),
            "free_gb": round(stat.free / (1024 ** 3), 1),
            "percent_used": round(stat.used / stat.total * 100, 1),
        }
        if stat.free < 500 * 1024 * 1024:
            issues.append(f"Critical: only {detail['disk']['free_gb']} GB free")
    except OSError as exc:
        detail["disk"] = {"error": type(exc).__name__}

    # Memory (optional)
    try:
        import psutil
        mem = psutil.virtual_memory()
        detail["memory"] = {
            "total_gb": round(mem.total / (1024 ** 3), 1),
            "available_gb": round(mem.available / (1024 ** 3), 1),
            "percent_used": mem.percent,
        }
    except ImportError:
        detail["memory"] = "psutil not installed"

    status = "warn" if issues else "pass"
    return CheckResult("resources", status,
                       f"CPU: {detail['cpu_count']} cores, Disk: {detail.get('disk', {}).get('free_gb', '?')} GB free",
                       detail, "; ".join(issues) if issues else "")


# ═══════════════════════════════════════════
# 10. Log Inspection
# ═══════════════════════════════════════════


def check_logs(cfg: TutorConfig) -> CheckResult:
    """Check log directory and recent session logs."""
    detail = {"sessions_root": "configured"}
    issues = []

    if cfg.sessions_root.exists():
        sessions = sorted(cfg.sessions_root.rglob("pipeline_state.json"))
        detail["total_sessions"] = len(sessions)

        # Check for stuck/failed sessions
        failed = []
        stuck = []
        for s in sessions[-20:]:  # last 20
            try:
                state = json.loads(s.read_text(encoding="utf-8"))
                stage = state.get("stage", "unknown")
                if stage == "failed":
                    failed.append(str(s.parent.name))
                updated = state.get("updated_at", "")
                if updated:
                    try:
                        parsed = datetime.fromisoformat(updated)
                        if parsed.tzinfo is None:
                            parsed = parsed.replace(tzinfo=timezone.utc)
                        age_h = (datetime.now(timezone.utc) - parsed).total_seconds() / 3600
                        if age_h > 24 and stage not in ("committed", "failed"):
                            stuck.append(f"{s.parent.name} ({stage}, {age_h:.0f}h old)")
                    except (ValueError, TypeError):
                        pass
            except (json.JSONDecodeError, OSError):
                pass

        detail["failed_sessions"] = failed
        detail["stuck_sessions"] = stuck
        if failed:
            issues.append(f"{len(failed)} failed sessions need cleanup")
        if stuck:
            issues.append(f"{len(stuck)} stuck sessions (>24h)")
    else:
        detail["total_sessions"] = 0

    status = "warn" if issues else "pass"
    return CheckResult("logs", status,
                       f"{detail['total_sessions']} sessions, {len(detail.get('failed_sessions', []))} failed, {len(detail.get('stuck_sessions', []))} stuck",
                       detail, "; ".join(issues) if issues else "")


# ═══════════════════════════════════════════
# 11. Business Result Verification
# ═══════════════════════════════════════════


def check_business_results(library_path: str | None = None) -> CheckResult:
    """Verify strategy library integrity and recent results."""
    detail = {}
    issues = []

    if library_path and Path(library_path).exists():
        try:
            lib = load_data(library_path)
            strategies = lib.get("strategies", [])
            detail["total_strategies"] = len(strategies)

            # Check for strategies without scores
            unscored = [s.get("strategy_id") for s in strategies
                       if isinstance(s, dict) and "darwin_score" not in s]
            if unscored:
                issues.append(f"{len(unscored)} strategies have no Darwin score")

            # Check for strategies with low scores needing optimization
            low_score = [s.get("strategy_id") for s in strategies
                        if isinstance(s, dict) and s.get("darwin_score", 0) < 50]
            if low_score:
                detail["low_score_count"] = len(low_score)

            # Check score_history integrity
            broken_history = []
            for s in strategies:
                if not isinstance(s, dict):
                    continue
                hist = s.get("score_history", [])
                if hist and isinstance(hist[-1], dict) and s.get("darwin_score", 0) != hist[-1].get("score", 0):
                    broken_history.append(s.get("strategy_id"))
            if broken_history:
                issues.append(f"{len(broken_history)} strategies have mismatched score_history")

            detail["strategy_exam_distribution"] = _count_by_exam(strategies)
            detail["strategy_module_distribution"] = _count_by_module(strategies)

        except (json.JSONDecodeError, OSError) as exc:
            issues.append(_safe_failure("Library read failed", exc))
    else:
        detail["total_strategies"] = 0
        detail["note"] = "No strategy library found; run examlex commit to create one"

    status = "warn" if issues else "pass"
    return CheckResult("business_results", status,
                       f"{detail.get('total_strategies', 0)} strategies in library",
                       detail, "; ".join(issues) if issues else "")


def _count_by_exam(strategies: list) -> dict:
    counts: dict[str, int] = {}
    for s in strategies:
        if isinstance(s, dict):
            for exam in s.get("exam_types", []):
                counts[exam] = counts.get(exam, 0) + 1
    return dict(sorted(counts.items()))


def _count_by_module(strategies: list) -> dict:
    counts: dict[str, int] = {}
    for s in strategies:
        if isinstance(s, dict):
            for mod in s.get("modules", []):
                counts[mod] = counts.get(mod, 0) + 1
    return dict(sorted(counts.items()))


# ═══════════════════════════════════════════
# 12. Network & External Dependency Check
# ═══════════════════════════════════════════


def check_network() -> CheckResult:
    """Check network connectivity for video download and cloud ASR."""
    detail = {}
    issues = []

    # Check basic internet connectivity
    try:
        start = time.time()
        # Fixed HTTPS probe; no user-controlled URL reaches urlopen.
        with urlopen("https://www.bilibili.com", timeout=5):  # nosec B310
            pass
        detail["bilibili_latency_ms"] = round((time.time() - start) * 1000)
        detail["internet"] = "reachable"
    except Exception:
        detail["bilibili"] = "unreachable"

    try:
        start = time.time()
        # Fixed HTTPS probe; no user-controlled URL reaches urlopen.
        with urlopen("https://www.youtube.com", timeout=5):  # nosec B310
            pass
        detail["youtube_latency_ms"] = round((time.time() - start) * 1000)
    except Exception:
        detail["youtube"] = "unreachable"

    # Check SiliconFlow API (if key is set)
    api_key = os.environ.get("SILICONFLOW_API_KEY")
    if api_key:
        try:
            req = Request(
                "https://api.siliconflow.cn/v1/models",
                headers={"Authorization": f"Bearer {api_key}"},
            )
            opener = build_opener(_RejectCredentialRedirectHandler())
            with opener.open(req, timeout=5):
                pass
            detail["siliconflow_api"] = "reachable"
        except HTTPError as exc:
            detail["siliconflow_api"] = f"unreachable (HTTP {exc.code})"
            issues.append("SiliconFlow API key is set but API is unreachable")
        except Exception:
            detail["siliconflow_api"] = "unreachable"
            issues.append("SiliconFlow API key is set but API is unreachable")
    else:
        detail["siliconflow_api"] = "no API key set (video ASR uses local whisper)"

    status = "warn" if issues else "pass"
    return CheckResult("network", status,
                       f"Internet: {detail.get('internet', 'unknown')}",
                       detail, "; ".join(issues) if issues else "")


# ═══════════════════════════════════════════
# 13. Safety Limits
# ═══════════════════════════════════════════


def check_safety_limits(cfg: TutorConfig) -> CheckResult:
    """Verify safety limits are configured to prevent resource exhaustion."""
    detail = {}
    issues = []

    defaults = {
        "max_video_duration_seconds": (14400, "4 hours"),        # 4h hard limit
        "max_video_warning_seconds": (7200, "2 hours"),           # 2h warning
        "darwin_max_rounds": (3, ""),                             # optimization rounds
        "darwin_touch_top_delta": (2.0, ""),                      # stop threshold
        "min_text_length_chars": (500, ""),                       # transcript minimum
        "session_retention_hours": (168.0, "7 days"),
        "max_reproducible_artifact_bytes": (4 * 1024 ** 3, "4 GiB hard limit"),
        "strategy_library_warning_bytes": (100 * 1024 ** 2, "100 MiB warning"),
    }

    for attr, (default_val, desc) in defaults.items():
        val = getattr(cfg, attr, default_val)
        detail[attr] = {"value": val, "default": default_val}
        if desc:
            detail[attr]["description"] = desc

    # Check that limits are reasonable
    if cfg.max_video_duration_seconds > 86400:
        issues.append("max_video_duration_seconds > 24h — videos this long may exhaust disk space")
    if cfg.darwin_max_rounds > 10:
        issues.append("darwin_max_rounds > 10 — optimization may run indefinitely")
    if cfg.warn_video_duration_seconds > cfg.max_video_duration_seconds:
        issues.append("warn_video_duration > max_video_duration — warnings will never trigger")

    # Concurrent/distillation limit
    detail["concurrent_sessions_warning"] = (
        "Multiple simultaneous distillations may exhaust CPU/memory. "
        "Run one at a time unless on a server with sufficient resources."
    )

    status = "warn" if issues else "pass"
    return CheckResult("safety_limits", status,
                       f"Max video: {cfg.max_video_duration_seconds}s, Max optimization rounds: {cfg.darwin_max_rounds}",
                       detail, "; ".join(issues) if issues else "")


# ═══════════════════════════════════════════
# Orchestrator — run all checks
# ═══════════════════════════════════════════


def run_all_checks(
    cfg: TutorConfig | None = None,
    library_path: str | None = None,
    *,
    include_network: bool = True,
) -> OpsReport:
    """Execute all 13 operational readiness checks."""
    if cfg is None:
        cfg = TutorConfig()

    checks: list[CheckResult] = []

    # 1-3: Environment, Config, Permissions
    checks.append(check_environment(cfg))
    checks.append(check_config(cfg))
    checks.append(check_permissions(cfg))

    # 4: Ports/Resources (adapted for CLI)
    checks.append(check_ports())

    # 5-6: Pre-run + Dry-run
    checks.append(check_prerun(cfg))
    checks.append(check_dry_run(cfg, library_path))

    # 7-8: Scheduler support
    checks.append(check_scheduler(cfg))

    # 9: Resource monitoring
    checks.append(check_resources())

    # 10: Log inspection
    checks.append(check_logs(cfg))

    # 11: Business results
    checks.append(check_business_results(library_path))

    # 12: Network
    if include_network:
        checks.append(check_network())
    else:
        checks.append(
            CheckResult(
                "network",
                "skip",
                "Network checks skipped by request",
                {"offline": True},
                "Run without --offline when live connectivity diagnostics are needed.",
            )
        )

    # 13: Safety limits
    checks.append(check_safety_limits(cfg))

    summary = {
        "pass": sum(1 for c in checks if c.status == "pass"),
        "warn": sum(1 for c in checks if c.status == "warn"),
        "fail": sum(1 for c in checks if c.status == "fail"),
        "skip": sum(1 for c in checks if c.status == "skip"),
    }

    return OpsReport(
        timestamp=datetime.now(timezone.utc).isoformat(),
        hostname="<redacted>",
        platform=platform.platform(),
        python_version=sys.version.split()[0],
        checks=checks,
        summary=summary,
    )
