"""CLI: examlex ops-check — run all 13 operational readiness checks."""

from __future__ import annotations

import argparse
import json
import sys

from .ops import run_all_checks
from .config import TutorConfig


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Run operational readiness checks for deployment safety."
    )
    parser.add_argument("--library", help="Path to strategy-library.json (for business result check)")
    parser.add_argument("--json", action="store_true", help="JSON output")
    parser.add_argument(
        "--offline",
        action="store_true",
        help="Skip live Bilibili, YouTube, and SiliconFlow connectivity checks",
    )
    args = parser.parse_args(argv)

    cfg = TutorConfig()
    try:
        report = run_all_checks(
            cfg,
            args.library,
            include_network=not args.offline,
        )
    except Exception as exc:
        if args.json:
            print(json.dumps({"error": str(exc)}, ensure_ascii=True))
        else:
            print(f"[FAIL] Check execution failed: {exc}", file=sys.stderr)
        return 2

    if args.json:
        output = {
            "timestamp": report.timestamp,
            "hostname": report.hostname,
            "platform": report.platform,
            "python": report.python_version,
            "summary": report.summary,
            "checks": [
                {
                    "name": c.name,
                    "status": c.status,
                    "message": c.message,
                    "detail": {k: v for k, v in c.detail.items() if k != "config"},
                    "remedy": c.remedy,
                }
                for c in report.checks
            ],
        }
        print(json.dumps(output, ensure_ascii=True, indent=2))
        return 0 if report.all_pass() else 1

    # Human-readable output
    status_icon = {"pass": "[OK]", "warn": "[WARN]", "fail": "[FAIL]", "skip": "[SKIP]"}

    print("Operational Readiness Report")
    print(f"Host: {report.hostname} | Platform: {report.platform}")
    print(f"Python: {report.python_version} | Time: {report.timestamp}")
    print(f"Summary: {report.summary.get('pass', 0)} pass, {report.summary.get('warn', 0)} warn, "
          f"{report.summary.get('fail', 0)} fail, {report.summary.get('skip', 0)} skip")
    print()

    for check in report.checks:
        icon = status_icon.get(check.status, "[??]")
        print(f"  {icon} {check.name}: {check.message}")
        if check.remedy:
            print(f"       Fix: {check.remedy}")

    print()
    if report.all_pass():
        print("All critical checks passed. System is ready.")
    else:
        print(f"WARNING: {report.summary.get('fail', 0)} checks failed. Review and fix before deployment.")

    return 0 if report.all_pass() else 1
