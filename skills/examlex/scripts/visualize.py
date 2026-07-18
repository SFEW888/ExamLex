#!/usr/bin/env python3
"""Generate a standalone HTML progress report with inline SVG charts.

Usage:
  python visualize.py --ability-history <path> --ledger <path> [--output report.html]
"""

from __future__ import annotations

import argparse
import datetime
import html
import json
import math
import sys
from pathlib import Path

try:
    from . import common
except ImportError:
    import common  # type: ignore[no-redef]


# ── SVG chart generators ───────────────────────────────────────────────────

def _svg_radar(modules_data: dict[str, float], width=400, height=400) -> str:
    """Generate an inline SVG radar chart for ability levels."""
    labels = list(modules_data.keys())
    values = [modules_data[k] for k in labels]
    n = len(labels)
    if n < 3:
        return '<svg width="400" height="100"><text x="10" y="30">Not enough data for radar chart</text></svg>'

    cx, cy, r = width / 2, height / 2, 140
    parts = []
    # Background rings
    for level in [0.25, 0.5, 0.75, 1.0]:
        lr = r * level
        parts.append(f'<circle cx="{cx}" cy="{cy}" r="{lr:.0f}" '
                     f'fill="none" stroke="#e0e0e0" stroke-width="1" stroke-dasharray="4,4"/>')

    # Axes
    for i in range(n):
        angle = -90 + i * (360 / n)
        ex_real = cx + r * math.cos(math.radians(angle))
        ey_real = cy + r * math.sin(math.radians(angle))
        parts.append(f'<line x1="{cx:.1f}" y1="{cy:.1f}" x2="{ex_real:.1f}" y2="{ey_real:.1f}" '
                     f'stroke="#ddd" stroke-width="1"/>')
        # Label
        lx = cx + (r + 30) * math.cos(math.radians(angle))
        ly = cy + (r + 30) * math.sin(math.radians(angle))
        anchor = "middle"
        if lx < cx - 20:
            anchor = "end"
        elif lx > cx + 20:
            anchor = "start"
        parts.append(f'<text x="{lx:.1f}" y="{ly:.1f}" text-anchor="{anchor}" '
                     f'font-size="12" fill="#333">{html.escape(str(labels[i]))}</text>')

    # Data polygon
    points = []
    for i, v in enumerate(values[:n]):
        angle = -90 + i * (360 / n)
        vx = cx + r * v * math.cos(math.radians(angle))
        vy = cy + r * v * math.sin(math.radians(angle))
        points.append(f"{vx:.1f},{vy:.1f}")
    poly = " ".join(points)
    parts.append(f'<polygon points="{poly}" fill="rgba(74,144,217,0.3)" '
                 f'stroke="#4A90D9" stroke-width="2"/>')

    # Data dots
    for i, v in enumerate(values[:n]):
        angle = -90 + i * (360 / n)
        vx = cx + r * v * math.cos(math.radians(angle))
        vy = cy + r * v * math.sin(math.radians(angle))
        parts.append(f'<circle cx="{vx:.1f}" cy="{vy:.1f}" r="4" fill="#4A90D9"/>')
        parts.append(f'<text x="{vx:.1f}" y="{vy-8:.1f}" text-anchor="middle" '
                     f'font-size="10" fill="#555">{int(v*100)}</text>')

    return f'<svg id="radar" viewBox="0 0 {width} {height}" width="{width}" height="{height}">\n' + \
           "\n".join(f"  {p}" for p in parts) + '\n</svg>'


def _svg_trends(dates: list[str], accuracy_by_module: dict[str, list[float]],
                width=700, height=300) -> str:
    """Generate inline SVG line chart for practice accuracy trends."""
    if not dates or len(dates) < 2:
        return '<svg width="700" height="100"><text x="10" y="30">Not enough data for trend chart</text></svg>'

    colors = ["#4A90D9", "#E67E22", "#2ECC71", "#E74C3C", "#9B59B6", "#1ABC9C"]
    margin = {"top": 30, "right": 30, "bottom": 50, "left": 60}
    plot_w = width - margin["left"] - margin["right"]
    plot_h = height - margin["top"] - margin["bottom"]

    parts = [f'<rect x="0" y="0" width="{width}" height="{height}" fill="white"/>']

    # Grid lines
    for pct in [0, 25, 50, 75, 100]:
        y = margin["top"] + plot_h * (1 - pct / 100)
        parts.append(f'<line x1="{margin["left"]}" y1="{y:.1f}" x2="{width - margin["right"]}" '
                     f'y2="{y:.1f}" stroke="#eee" stroke-width="1"/>')
        parts.append(f'<text x="{margin["left"] - 5}" y="{y+4:.1f}" text-anchor="end" '
                     f'font-size="10" fill="#999">{pct}%</text>')

    # X-axis labels
    n_dates = len(dates)
    for i, d in enumerate(dates):
        if n_dates <= 10 or i % max(1, n_dates // 8) == 0:
            x = margin["left"] + plot_w * i / max(1, n_dates - 1)
            parts.append(f'<text x="{x:.1f}" y="{height - 10:.1f}" text-anchor="middle" '
                         f'font-size="9" fill="#999">{html.escape(str(d)[5:])}</text>')

    # Lines
    mods = list(accuracy_by_module.keys())
    for mi, mod in enumerate(mods[:len(colors)]):
        vals = accuracy_by_module[mod]
        path_parts = []
        for i, v in enumerate(vals):
            x = margin["left"] + plot_w * i / max(1, len(vals) - 1)
            y = margin["top"] + plot_h * (1 - v / 100)
            path_parts.append(f"{'M' if i == 0 else 'L'} {x:.1f} {y:.1f}")
        color = colors[mi]
        parts.append(f'<path d="{" ".join(path_parts)}" fill="none" '
                     f'stroke="{color}" stroke-width="2"/>')
        # Label at end
        last_x = margin["left"] + plot_w
        last_y = margin["top"] + plot_h * (1 - vals[-1] / 100)
        parts.append(f'<text x="{last_x + 5:.1f}" y="{last_y:.1f}" font-size="10" fill="{color}">{html.escape(str(mod))}</text>')

    # Y-axis label
    parts.append(f'<text x="15" y="{height/2:.1f}" text-anchor="middle" '
                 f'font-size="11" fill="#666" transform="rotate(-90 15 {height/2:.0f})">Accuracy (%)</text>')

    return f'<svg id="trends" viewBox="0 0 {width} {height}" width="{width}" height="{height}">\n' + \
           "\n".join(f"  {p}" for p in parts) + '\n</svg>'


def _as_number(value: object) -> float:
    """Return a number for display math; a non-number (or bool) degrades to 0."""
    if isinstance(value, bool):
        return 0
    return value if isinstance(value, (int, float)) else 0


def _as_nonnegative_count(value: object) -> int:
    """Return a safe display count for HTML; malformed values degrade to 0."""
    if isinstance(value, int) and not isinstance(value, bool) and value >= 0:
        return value
    return 0


def _compute_ability_levels(ability_history: list[dict]) -> dict[str, float]:
    """Compute average ability level (0-1) per module from ability history."""
    if not ability_history:
        return {}
    latest = ability_history[-1]
    levels: dict[str, float] = {}
    # A malformed history whose last element is not an object must not crash the
    # report; a non-numeric per-node level degrades to 0 rather than raising.
    if not isinstance(latest, dict):
        return levels
    modules = latest.get("modules", {})
    if isinstance(modules, dict):
        for mod_name, nodes in modules.items():
            if isinstance(nodes, list) and nodes:
                avg = sum(
                    _as_number(n.get("level", 0)) / 10.0
                    for n in nodes if isinstance(n, dict)
                ) / len(nodes)
                levels[mod_name] = min(1.0, avg)
    return levels


def _compute_trend_data(ledger: list[dict]) -> tuple[list[str], dict[str, list[float]]]:
    """Compute daily accuracy by module from practice ledger."""
    if not ledger:
        return [], {}
    by_date: dict[str, dict[str, list[float]]] = {}
    for rec in ledger:
        if not isinstance(rec, dict):
            continue
        date = str(rec.get("date", ""))
        mod = str(rec.get("module", ""))
        total = rec.get("total_items", 0)
        correct = rec.get("correct_items", 0)
        if date and mod and isinstance(total, int) and isinstance(correct, int) and total > 0:
            if date not in by_date:
                by_date[date] = {}
            if mod not in by_date[date]:
                by_date[date][mod] = []
            by_date[date][mod].append(correct / total * 100)

    dates = sorted(by_date.keys())
    modules_set: set[str] = set()
    for d in dates:
        modules_set.update(by_date[d].keys())

    accuracy_by_module: dict[str, list[float]] = {m: [] for m in sorted(modules_set)}
    for d in dates:
        for m in accuracy_by_module:
            vals = by_date[d].get(m, [])
            accuracy_by_module[m].append(sum(vals) / len(vals) if vals else None)

    # Interpolate None values
    for mod, vals in accuracy_by_module.items():
        for i in range(len(vals)):
            if vals[i] is None:
                prev = next((v for v in reversed(vals[:i]) if v is not None), None)
                nxt = next((v for v in vals[i+1:] if v is not None), None)
                if prev is not None and nxt is not None:
                    vals[i] = (prev + nxt) / 2
                elif prev is not None:
                    vals[i] = prev
                else:
                    vals[i] = 0.0

    return dates, accuracy_by_module


# ── Main CLI ────────────────────────────────────────────────────────────────

def generate_report(
    ability_history: list[dict],
    ledger: list[dict],
    error_summary: dict | None = None,
    title: str = "英语备考进度报告",
    days: int = 30,
) -> str:
    today = datetime.date.today()
    cutoff = today - datetime.timedelta(days=days)

    # Filter ledger to recent days (skip records with invalid/missing dates)
    recent_ledger: list[dict] = []
    for r in ledger:
        if not isinstance(r, dict):
            continue
        try:
            rec_date = datetime.date.fromisoformat(str(r.get("date", today.isoformat())))
        except (ValueError, TypeError):
            continue
        if rec_date >= cutoff:
            recent_ledger.append(r)

    levels = _compute_ability_levels(ability_history)
    dates, trends = _compute_trend_data(recent_ledger)

    radar_html = _svg_radar(levels) if levels else '<p>No ability data available.</p>'
    trends_html = _svg_trends(dates, trends) if dates else '<p>No trend data available.</p>'

    total_records = len(ledger)
    total_recent = len(recent_ledger)
    total_errors = sum(
        sum(1 for tag in tags if isinstance(tag, str))
        for record in ledger
        if isinstance(record, dict)
        and isinstance((tags := record.get("error_tags", [])), list)
    )

    # Speed from error_summary
    speed_info = ""
    sa = error_summary.get("speed_analysis") if isinstance(error_summary, dict) else None
    if isinstance(sa, dict):
        timed_sessions = _as_nonnegative_count(sa.get("timed_sessions", 0))
        speed_info = f"""
    <div class="stat">
      <div class="stat-value">{timed_sessions}</div>
      <div class="stat-label">计时训练次数</div>
    </div>
    <div class="stat">
      <div class="stat-value">{html.escape(str(sa.get('verdict', 'N/A')))}</div>
      <div class="stat-label">速度诊断</div>
    </div>"""

    title_esc = html.escape(str(title))
    return f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="utf-8">
<title>{title_esc}</title>
<style>
* {{ margin: 0; padding: 0; box-sizing: border-box; }}
body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif; background: #f5f7fa; color: #333; padding: 20px; }}
.container {{ max-width: 900px; margin: 0 auto; }}
h1 {{ font-size: 24px; margin-bottom: 8px; }}
.date {{ color: #999; font-size: 14px; margin-bottom: 24px; }}
.stats {{ display: flex; gap: 16px; flex-wrap: wrap; margin-bottom: 24px; }}
.stat {{ background: white; border-radius: 8px; padding: 16px 20px; flex: 1; min-width: 140px; box-shadow: 0 1px 3px rgba(0,0,0,0.1); }}
.stat-value {{ font-size: 28px; font-weight: 700; color: #4A90D9; }}
.stat-label {{ font-size: 12px; color: #999; margin-top: 4px; }}
.chart-section {{ background: white; border-radius: 8px; padding: 20px; margin-bottom: 16px; box-shadow: 0 1px 3px rgba(0,0,0,0.1); }}
.chart-section h2 {{ font-size: 18px; margin-bottom: 12px; }}
.chart-section svg {{ display: block; margin: 0 auto; }}
table {{ width: 100%; border-collapse: collapse; }}
th, td {{ text-align: left; padding: 8px 12px; border-bottom: 1px solid #eee; font-size: 14px; }}
th {{ background: #f9fafb; font-weight: 600; }}
</style>
</head>
<body>
<div class="container">
<h1>{title_esc}</h1>
<p class="date">生成日期: {today} &nbsp;|&nbsp; 统计范围: 最近 {days} 天</p>

<div class="stats">
  <div class="stat">
    <div class="stat-value">{total_records}</div>
    <div class="stat-label">总练习次数</div>
  </div>
  <div class="stat">
    <div class="stat-value">{total_recent}</div>
    <div class="stat-label">最近 {days} 天</div>
  </div>
  <div class="stat">
    <div class="stat-value">{total_errors}</div>
    <div class="stat-label">总错误标签数</div>
  </div>
  {speed_info}
</div>

<div class="chart-section">
  <h2>能力雷达图</h2>
  {radar_html}
</div>

<div class="chart-section">
  <h2>学习正确率趋势</h2>
  {trends_html}
</div>

<div class="chart-section">
  <h2>错题统计摘要</h2>
  {_error_table(error_summary)}
</div>

</div>
</body>
</html>"""


def _error_table(error_summary: dict | None) -> str:
    # A malformed --error-summary (non-dict, or a non-dict by_tag / string
    # numeric fields) must not crash the report; degrade to the empty-state
    # message or coerce non-numbers to 0 for the format specifiers below.
    if not isinstance(error_summary, dict):
        return "<p>No error data available.</p>"
    by_tag = error_summary.get("by_tag", {})
    if not isinstance(by_tag, dict) or not by_tag:
        return "<p>No error data available.</p>"
    rows = []
    for tag, data in sorted(
        by_tag.items(),
        key=lambda x: -_as_number(x[1].get("count", 0) if isinstance(x[1], dict) else 0),
    ):
        if not isinstance(data, dict):
            continue
        count = _as_number(data.get("count", 0))
        pct = _as_number(data.get("percentage", 0))
        urgency = _as_number(data.get("review_urgency", 0))
        rows.append(f"<tr><td>{html.escape(str(tag))}</td><td>{count}</td><td>{pct:.0%}</td>"
                    f"<td>{urgency:.2f}</td></tr>")
    header = "<tr><th>Error Tag</th><th>Count</th><th>%</th><th>Urgency</th></tr>"
    return f'<table>{header}{"".join(rows)}</table>'


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Generate HTML progress report.")
    parser.add_argument("--ability-history", required=True, help="Path to ability-history JSON array.")
    parser.add_argument("--ledger", required=True, help="Path to practice ledger JSON array.")
    parser.add_argument("--error-summary", help="Optional error summary JSON.")
    parser.add_argument("--output", default="progress-report.html", help="Output HTML path.")
    parser.add_argument("--days", type=int, default=30, help="Recent days for trend chart (default: 30).")
    parser.add_argument("--title", default="英语备考进度报告", help="Report title.")
    args = parser.parse_args(argv)

    try:
        ability_history = common.load_data(args.ability_history)
        ledger = common.load_data(args.ledger)
        error_summary = common.load_data(args.error_summary) if args.error_summary else None
    except (FileNotFoundError, json.JSONDecodeError, OSError) as exc:
        print(f"Error loading data: {exc}", file=sys.stderr)
        return 1

    if not isinstance(ability_history, list):
        ability_history = [ability_history]
    if not isinstance(ledger, list):
        print("Error: ledger must be a JSON array.", file=sys.stderr)
        return 1

    html = generate_report(ability_history, ledger, error_summary, args.title, args.days)
    Path(args.output).write_text(html, encoding="utf-8")
    print(f"Report written to {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
