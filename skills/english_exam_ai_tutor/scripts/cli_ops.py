"""CLI: tutor ops-check — run all 13 operational readiness checks."""

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
    parser.add_argument("--quick", action="store_true", help="Quick mode: skip network + dry-run")
    args = parser.parse_args(argv)

    cfg = TutorConfig()
    report = run_all_checks(cfg, args.library)

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
        print(json.dumps(output, ensure_ascii=False, indent=2))
        return 0 if report.all_pass() else 1

    # Human-readable output
    status_icon = {"pass": "[OK]", "warn": "[WARN]", "fail": "[FAIL]", "skip": "[SKIP]"}

    print(f"Operational Readiness Report")
    print(f"Host: {report.hostname} | Platform: {report.platform}")
    print(f"Python: {report.python_version} | Time: {report.timestamp}")
    print(f"Summary: {report.summary['pass']} pass, {report.summary['warn']} warn, "
          f"{report.summary['fail']} fail, {report.summary['skip']} skip")
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
        print(f"WARNING: {report.summary['fail']} checks failed. Review and fix before deployment.")

    return 0 if report.all_pass() else 1
