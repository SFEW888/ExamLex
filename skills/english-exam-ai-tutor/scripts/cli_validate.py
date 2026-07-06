"""CLI entry point: tutor validate — format check + Darwin structure scoring."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from .validators.format_checker import FormatChecker
from .validators.darwin_structure import DarwinStructureScorer


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Validate distilled strategies and compute Darwin structure scores."
    )
    parser.add_argument("--artifacts-dir", required=True,
                        help="Session artifacts directory containing distilled.json")
    parser.add_argument("--json", action="store_true", help="JSON output")
    args = parser.parse_args(argv)

    artifacts = Path(args.artifacts_dir)
    distilled = artifacts / "distilled.json"
    if not distilled.exists():
        output = {
            "status": "error",
            "message": f"distilled.json not found in {artifacts}. Run distillation first.",
        }
        if args.json:
            print(json.dumps(output, ensure_ascii=False, indent=2))
        else:
            print(f"ERROR: {output['message']}")
        return 2

    data = json.loads(distilled.read_text(encoding="utf-8"))
    strategies = data.get("strategies", [])

    if not strategies:
        output = {
            "status": "warning",
            "message": "No strategies produced by distillation (empty array).",
            "total_strategies": 0,
            "results": [],
        }
        if args.json:
            print(json.dumps(output, ensure_ascii=False, indent=2))
        else:
            print("WARNING: No strategies to validate.")
        return 0

    checker = FormatChecker()
    scorer = DarwinStructureScorer()

    results = []
    total_structure_score = 0.0
    all_passed = True

    for strategy in strategies:
        format_report = checker.validate(strategy)
        structure_score = scorer.score(strategy)

        entry = {
            "strategy_id": strategy.get("strategy_id", "unknown"),
            "title": strategy.get("title", ""),
            "format_passed": format_report.passed,
            "format_errors": len(format_report.errors),
            "format_warnings": len(format_report.warnings),
            "structure_score": structure_score.total,
            "structure_passed": structure_score.passed,
            "dimensions": [
                {"name": d.name, "label": d.label, "raw": d.raw,
                 "weighted": d.weighted, "issues": d.issues}
                for d in structure_score.dimensions
            ],
            "format_issues": [
                {"field": i.field, "severity": i.severity, "message": i.message}
                for i in format_report.errors + format_report.warnings
            ],
        }
        results.append(entry)
        total_structure_score += structure_score.total
        if not format_report.passed:
            all_passed = False

    avg_structure = total_structure_score / len(strategies) if strategies else 0.0

    output = {
        "status": "ok",
        "total_strategies": len(strategies),
        "all_format_passed": all_passed,
        "average_structure_score": round(avg_structure, 1),
        "results": results,
    }

    # Write report
    report_path = artifacts / "validation_report.json"
    report_path.write_text(json.dumps(output, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    if args.json:
        print(json.dumps(output, ensure_ascii=False, indent=2))
    else:
        print(f"Strategies validated: {len(strategies)}")
        print(f"Average structure score: {avg_structure:.1f}/59")
        for r in results:
            status = "PASS" if r["format_passed"] else "FAIL"
            print(f"  {status} {r['strategy_id']}: structure {r['structure_score']:.1f}/59 "
                  f"({r['format_errors']} errors, {r['format_warnings']} warnings)")
        print(f"Report: {report_path}")

    return 0 if all_passed else 1
