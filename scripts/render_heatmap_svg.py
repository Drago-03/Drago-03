#!/usr/bin/env python3
"""data/contributions.json -> animated GitHub-style contribution heatmap SVG.

Usage: python scripts/render_heatmap_svg.py
Output: contrib-heatmap.svg — a two-phase intro that plays once then
freezes (no loop): an F1 car drifts across the top (phase A), then the
contribution grid pop-in reveals diagonally, delayed so it looks like
the car kicked it up (phase B).
"""
import json
from datetime import date, datetime, timedelta
from pathlib import Path

DATA_PATH = Path("data/contributions.json")
OUT_PATH = Path("contrib-heatmap.svg")

PALETTE = ["#161b22", "#0e4429", "#006d32", "#26a641", "#39d353", "#69f0a0"]
BG = "#0d1117"
ACCENT = "#6AD3FF"
RED = "#DC0000"
GREEN_PULSE = PALETTE[4]
FG_DIM = "#8b949e"

WIDTH = 860
CAR_LANE_H = 32   # top strip reserved for the F1 car flyby
MARGIN_LEFT = 30
MARGIN_RIGHT = 14
MARGIN_TOP = 20 + CAR_LANE_H
GAP = 3
WEEKDAY_LABELS = {1: "Mon", 3: "Wed", 5: "Fri"}
MONTH_NAMES = ["Jan", "Feb", "Mar", "Apr", "May", "Jun",
               "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]

CAR_DUR = 1.2          # phase A: car sweeps left -> right across the top
POP_DUR = 0.3
POP_STAGGER = 0.018
POP_BASE_DELAY = 1.1   # phase B starts as the car exits (overlaps its tail)


def render_car() -> str:
    """stylized F1 car (pure SVG shapes) drifting across the top, once."""
    car_w = 70
    start_x, end_x = -car_w - 10, WIDTH + 10
    end_y = 6  # slight downward drift toward the grid

    trail = []
    for frac in (0.05, 0.2, 0.35, 0.5, 0.65, 0.8):
        cx = start_x + frac * (end_x - start_x) + car_w / 2
        begin = frac * CAR_DUR + 0.04
        trail.append(
            f'<ellipse cx="{cx:.1f}" cy="18" rx="11" ry="4" fill="{FG_DIM}" opacity="0">'
            f'<animate attributeName="opacity" values="0;0.32;0" keyTimes="0;0.3;1" '
            f'dur="0.45s" begin="{begin:.2f}s" fill="freeze"/></ellipse>'
        )

    car = (
        f'<g transform="translate({start_x},0)">'
        f'<animateTransform attributeName="transform" type="translate" '
        f'from="{start_x},0" to="{end_x},{end_y}" dur="{CAR_DUR}s" begin="0s" fill="freeze"/>'
        '<g><animateTransform attributeName="transform" type="rotate" '
        'values="0 35 13;-6 35 13;4 35 13;-2 35 13;0 35 13" keyTimes="0;0.25;0.55;0.8;1" '
        f'dur="{CAR_DUR}s" begin="0s" fill="freeze"/>'
        f'<rect x="0" y="1" width="6" height="2" fill="{ACCENT}"/>'
        f'<rect x="0" y="13" width="6" height="2" fill="{ACCENT}"/>'
        '<rect x="0" y="2" width="4" height="12" fill="#111"/>'
        f'<path d="M6,13 L10,13 L16,7 L34,5 L44,6 L52,9 L62,10 L66,11 L66,14 L58,15 L50,15 '
        f'L44,16 L20,16 L12,15 L6,15 Z" fill="{RED}"/>'
        '<path d="M28,7 Q34,-1 40,7" fill="none" stroke="#c9d1d9" stroke-width="1.5"/>'
        '<rect x="66" y="9" width="4" height="8" fill="#111"/>'
        f'<rect x="64" y="8" width="6" height="2" fill="{ACCENT}"/>'
        f'<rect x="64" y="16" width="6" height="2" fill="{ACCENT}"/>'
        '<circle cx="16" cy="18" r="5" fill="#111"/><circle cx="16" cy="18" r="2" fill="#444"/>'
        '<circle cx="52" cy="18" r="5" fill="#111"/><circle cx="52" cy="18" r="2" fill="#444"/>'
        '</g></g>'
    )
    return "".join(trail) + car


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
        render_car(),
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
    last_cell_delay = POP_BASE_DELAY + ((cols - 1) + 6) * POP_STAGGER
    pulse_begin = last_cell_delay + POP_DUR + 0.15
    parts.append(f'<text x="{MARGIN_LEFT}" y="{footer_y1:.1f}" font-size="13" font-weight="600" '
                 f'fill="{ACCENT}">{total_line}'
                 f'<animate attributeName="fill" values="{ACCENT};{GREEN_PULSE};{ACCENT}" '
                 f'keyTimes="0;0.5;1" dur="0.6s" begin="{pulse_begin:.2f}s" fill="freeze"/>'
                 f'</text>')
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
