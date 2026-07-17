"""Run automatic artifact retention and review-only strategy capacity checks."""

from __future__ import annotations

import argparse
import base64
import html
import json
import os
import shutil
import subprocess
import sys
import tempfile
from dataclasses import asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

try:
    from .cleanup_sessions import apply_retention_policy
    from .config import TutorConfig
    from .strategy_store import format_duplicate_candidates, strategy_library_health
except ImportError:  # pragma: no cover - copied Skill execution
    from cleanup_sessions import apply_retention_policy  # type: ignore[no-redef]
    from config import TutorConfig  # type: ignore[no-redef]
    from strategy_store import (  # type: ignore[no-redef]
        format_duplicate_candidates,
        strategy_library_health,
    )


def _atomic_write_json(path: Path, value: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    descriptor, temp_name = tempfile.mkstemp(
        prefix=path.name + ".", suffix=".tmp", dir=str(path.parent)
    )
    temporary = Path(temp_name)
    try:
        with os.fdopen(descriptor, "w", encoding="utf-8", newline="\n") as stream:
            stream.write(json.dumps(value, ensure_ascii=False, indent=2) + "\n")
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary, path)
    finally:
        try:
            temporary.unlink()
        except FileNotFoundError:
            pass


def _windows_toast(title: str, message: str) -> bool:
    """Best-effort toast for an interactive Windows scheduled task."""
    if os.name != "nt":
        return False
    powershell = shutil.which("powershell.exe") or shutil.which("powershell")
    if not powershell:
        return False
    title_xml = html.escape(title, quote=True)
    message_xml = html.escape(message, quote=True)
    script = f"""
[Windows.UI.Notifications.ToastNotificationManager, Windows.UI.Notifications, ContentType = WindowsRuntime] > $null
[Windows.Data.Xml.Dom.XmlDocument, Windows.Data.Xml.Dom.XmlDocument, ContentType = WindowsRuntime] > $null
$xml = New-Object Windows.Data.Xml.Dom.XmlDocument
$xml.LoadXml('<toast><visual><binding template="ToastGeneric"><text>{title_xml}</text><text>{message_xml}</text></binding></visual></toast>')
$toast = New-Object Windows.UI.Notifications.ToastNotification $xml
[Windows.UI.Notifications.ToastNotificationManager]::CreateToastNotifier('ExamLex').Show($toast)
""".strip()
    encoded = base64.b64encode(script.encode("utf-16le")).decode("ascii")
    try:
        result = subprocess.run(
            [powershell, "-NoProfile", "-NonInteractive", "-EncodedCommand", encoded],
            check=False,
            capture_output=True,
            timeout=15,
        )
    except (OSError, subprocess.SubprocessError):
        return False
    return result.returncode == 0


def run_capacity_monitor(
    *,
    sessions_root: Path,
    strategy_library_path: Path,
    retention_hours: float,
    max_reproducible_artifact_bytes: int,
    strategy_library_warning_bytes: int,
    status_file: Path,
    notify_windows: bool = False,
) -> dict[str, Any]:
    """Apply hard limits only to reproducible artifacts and warn on strategies."""
    retention = apply_retention_policy(
        sessions_root,
        retention_hours=retention_hours,
        max_reproducible_artifact_bytes=max_reproducible_artifact_bytes,
    )
    strategy = strategy_library_health(
        strategy_library_path,
        warning_threshold_bytes=strategy_library_warning_bytes,
        duplicate_limit=10,
    )
    notification = {"requested": notify_windows, "sent": False}
    warning_file = status_file.with_name(status_file.stem + "-warning.json")
    if strategy["threshold_reached"]:
        candidate_text = format_duplicate_candidates(strategy["duplicate_candidates"])
        message = (
            f"Strategy library reached {strategy['size_bytes']} bytes. "
            "No strategies or revisions were deleted."
        )
        if candidate_text:
            message += f" Possible duplicates: {candidate_text}"
        warning = {
            "created_at": datetime.now(timezone.utc).isoformat(),
            "message": message,
            "strategy_library": strategy,
            "review_command": (
                f"examlex strategies --library {strategy_library_path} --duplicates"
            ),
        }
        _atomic_write_json(warning_file, warning)
        if notify_windows:
            notification["sent"] = _windows_toast("ExamLex capacity warning", message)
    elif warning_file.exists():
        try:
            warning_file.unlink()
        except OSError:
            pass

    result = {
        "checked_at": datetime.now(timezone.utc).isoformat(),
        "sessions_root": str(sessions_root),
        "strategy_library_path": str(strategy_library_path),
        "retention": asdict(retention),
        "strategy_library": strategy,
        "automatic_strategy_deletion": False,
        "notification": notification,
        "warning_file": str(warning_file) if strategy["threshold_reached"] else None,
    }
    _atomic_write_json(status_file, result)
    return result


def main(argv: list[str] | None = None) -> int:
    cfg = TutorConfig()
    parser = argparse.ArgumentParser(
        prog="examlex capacity-monitor",
        description=(
            "Prune regenerable session artifacts and emit review-only strategy warnings."
        ),
    )
    parser.add_argument("--sessions-root", type=Path, default=cfg.sessions_root)
    parser.add_argument(
        "--strategy-library",
        type=Path,
        default=cfg.strategy_library_path,
    )
    parser.add_argument(
        "--retention-hours",
        type=float,
        default=cfg.session_retention_hours,
    )
    parser.add_argument(
        "--max-artifact-bytes",
        type=int,
        default=cfg.max_reproducible_artifact_bytes,
    )
    parser.add_argument(
        "--strategy-warning-bytes",
        type=int,
        default=cfg.strategy_library_warning_bytes,
    )
    parser.add_argument("--status-file", type=Path)
    parser.add_argument("--notify-windows", action="store_true")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args(argv)
    if args.retention_hours <= 0:
        parser.error("--retention-hours must be positive")
    if args.max_artifact_bytes <= 0:
        parser.error("--max-artifact-bytes must be positive")
    if args.strategy_warning_bytes <= 0:
        parser.error("--strategy-warning-bytes must be positive")
    status_file = args.status_file or args.sessions_root.parent / "capacity-monitor.json"
    try:
        result = run_capacity_monitor(
            sessions_root=args.sessions_root,
            strategy_library_path=args.strategy_library,
            retention_hours=args.retention_hours,
            max_reproducible_artifact_bytes=args.max_artifact_bytes,
            strategy_library_warning_bytes=args.strategy_warning_bytes,
            status_file=status_file,
            notify_windows=args.notify_windows,
        )
    except Exception as exc:
        print(f"capacity monitor failed: {exc}", file=sys.stderr)
        return 1
    if args.json:
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        retention = result["retention"]
        strategy = result["strategy_library"]
        print(
            "capacity monitor complete: "
            f"reclaimed={retention['bytes_reclaimed']} bytes; "
            f"strategy={strategy['size_bytes']} bytes; "
            f"warning={strategy['threshold_reached']}"
        )
        if strategy["threshold_reached"]:
            print(f"Review warning: {result['warning_file']}", file=sys.stderr)
    return 1 if result["retention"]["failures"] else 0


if __name__ == "__main__":
    raise SystemExit(main())
