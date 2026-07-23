#!/usr/bin/env python3
"""data/contributions.json -> animated GitHub-style contribution heatmap SVG.

Usage: python scripts/render_heatmap_svg.py
Output: contrib-heatmap.svg — cells pop in diagonally (top-left to
bottom-right) once on load via CSS keyframes, then freeze. No loop.
"""
import json
from datetime import date, datetime, timedelta
from pathlib import Path

DATA_PATH = Path("data/contributions.json")
OUT_PATH = Path("contrib-heatmap.svg")

PALETTE = ["#161b22", "#0e4429", "#006d32", "#26a641", "#39d353", "#69f0a0"]
BG = "#0d1117"
ACCENT = "#6AD3FF"
FG_DIM = "#8b949e"

WIDTH = 860
MARGIN_LEFT = 30
MARGIN_RIGHT = 14
MARGIN_TOP = 20
GAP = 3
WEEKDAY_LABELS = {1: "Mon", 3: "Wed", 5: "Fri"}
MONTH_NAMES = ["Jan", "Feb", "Mar", "Apr", "May", "Jun",
               "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]

POP_DUR = 0.3
POP_STAGGER = 0.018
POP_BASE_DELAY = 0.1


def build_weeks(days: list[dict]) -> list[list[dict | None]]:
    first = datetime.strptime(days[0]["date"], "%Y-%m-%d").date()
    grid_start = first - timedelta(days=(first.weekday() + 1) % 7)  # back up to Sunday

    by_date = {d["date"]: d for d in days}
    last = datetime.strptime(days[-1]["date"], "%Y-%m-%d").date()

    weeks: list[list[dict | None]] = []
    cur_week: list[dict | None] = []
    d = grid_start
    while d <= last:
        entry = by_date.get(d.isoformat())
        cur_week.append(entry)
        if len(cur_week) == 7:
            weeks.append(cur_week)
            cur_week = []
        d += timedelta(days=1)
    if cur_week:
        while len(cur_week) < 7:
            cur_week.append(None)
        weeks.append(cur_week)
    return weeks


def render_svg(payload: dict) -> str:
    days = payload["days"]
    weeks = build_weeks(days)
    cols = len(weeks)

    grid_w = WIDTH - MARGIN_LEFT - MARGIN_RIGHT
    unit = grid_w / cols
    cell = unit - GAP
    grid_h = 7 * unit - GAP

    legend_y = MARGIN_TOP + grid_h + 26
    footer_y1 = legend_y + 26
    footer_y2 = footer_y1 + 20
    height = round(footer_y2 + 14)

    best = payload["best_day"]["date"]

    parts = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{WIDTH}" height="{height}" '
        f'viewBox="0 0 {WIDTH} {height}" font-family="SFMono-Regular, Consolas, Menlo, monospace">',
        '<style>'
        '.cell{opacity:0;transform:scale(0.35);transform-box:fill-box;transform-origin:center;'
        'animation:popIn ' f'{POP_DUR}s ease-out forwards;}}'
        '@keyframes popIn{to{opacity:1;transform:scale(1);}}'
        '</style>',
        f'<rect width="{WIDTH}" height="{height}" fill="{BG}"/>',
    ]

    # month labels
    prev_month = None
    for w, week in enumerate(weeks):
        first_day = next((c for c in week if c), None)
        if not first_day:
            continue
        month = int(first_day["date"][5:7])
        if month != prev_month:
            x = MARGIN_LEFT + w * unit
            parts.append(
                f'<text x="{x:.1f}" y="{MARGIN_TOP - 7:.1f}" font-size="10" fill="{FG_DIM}">'
                f'{MONTH_NAMES[month - 1]}</text>'
            )
            prev_month = month

    # weekday labels
    for wd, label in WEEKDAY_LABELS.items():
        y = MARGIN_TOP + wd * unit + cell * 0.75
        parts.append(f'<text x="0" y="{y:.1f}" font-size="10" fill="{FG_DIM}">{label}</text>')

    # cells, diagonal stagger by (week + weekday)
    for w, week in enumerate(weeks):
        for wd, entry in enumerate(week):
            x = MARGIN_LEFT + w * unit
            y = MARGIN_TOP + wd * unit
            if entry is None:
                color = PALETTE[0]
                title = ""
            else:
                color = PALETTE[5] if entry["date"] == best and entry["count"] > 0 else PALETTE[entry["level"]]
                title = f'{entry["count"]} contributions on {entry["date"]}'
            delay = POP_BASE_DELAY + (w + wd) * POP_STAGGER
            parts.append(
                f'<rect class="cell" x="{x:.1f}" y="{y:.1f}" width="{cell:.1f}" height="{cell:.1f}" '
                f'rx="2" fill="{color}" style="animation-delay:{delay:.3f}s">'
                + (f'<title>{title}</title>' if title else '') + '</rect>'
            )

    # legend
    lx = MARGIN_LEFT
    parts.append(f'<text x="{lx}" y="{legend_y + cell * 0.75:.1f}" font-size="11" fill="{FG_DIM}">Less</text>')
    lx += 32
    for i in range(5):
        parts.append(f'<rect x="{lx:.1f}" y="{legend_y:.1f}" width="{cell:.1f}" height="{cell:.1f}" '
                      f'rx="2" fill="{PALETTE[i]}"/>')
        lx += cell + GAP
    parts.append(f'<text x="{lx + 6:.1f}" y="{legend_y + cell * 0.75:.1f}" font-size="11" fill="{FG_DIM}">More</text>')

    # stats footer
    total_line = f'{payload["total"]:,} contributions in the last year'
    streak_line = (f'current streak {payload["current_streak"]}d · '
                    f'longest streak {payload["longest_streak"]}d · '
                    f'best day {payload["best_day"]["count"]} on {payload["best_day"]["date"]}')
    parts.append(f'<text x="{MARGIN_LEFT}" y="{footer_y1:.1f}" font-size="13" font-weight="600" '
                 f'fill="{ACCENT}">{total_line}</text>')
    parts.append(f'<text x="{MARGIN_LEFT}" y="{footer_y2:.1f}" font-size="11" fill="{FG_DIM}">{streak_line}</text>')

    parts.append('</svg>')
    return "\n".join(parts)


def main() -> None:
    if not DATA_PATH.exists():
        raise SystemExit(f"{DATA_PATH} not found — run fetch_contributions.py first")
    payload = json.loads(DATA_PATH.read_text())
    svg = render_svg(payload)
    OUT_PATH.write_text(svg)
    print(f"wrote {OUT_PATH} ({payload['total']} contributions)")


if __name__ == "__main__":
    main()
