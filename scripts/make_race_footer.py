#!/usr/bin/env python3
"""standalone footer: three F1 cars racing left -> right, looping forever.

Usage: python scripts/make_race_footer.py
Output: race-footer.svg (~860x140). Static asset — not part of the daily
contribution-graph refresh, commit it once and forget it.
Env: STATIC=1 emits a frozen frame (no SMIL) for Quick Look previews.
"""
import os
from pathlib import Path

WIDTH, HEIGHT = 860, 140
BG = "#0d1117"
LANE_LINE = "#30363d"
FG_DIM = "#8b949e"
ACCENT = "#6AD3FF"
CARS = [
    {"color": "#DC0000", "lane": 0, "dur": 4.2, "begin": 0.0},   # Ferrari red
    {"color": "#6AD3FF", "lane": 1, "dur": 3.6, "begin": 0.6},   # cyan accent
    {"color": "#39d353", "lane": 2, "dur": 5.0, "begin": 1.2},   # green
]

TRACK_TOP = 8
LANE_H = 32
CAR_W, CAR_H = 62, 20
OUT_PATH = Path("race-footer.svg")


def car_shape(color: str, static: bool) -> str:
    def spin(cx: int, cy: int) -> str:
        if static:
            return ""
        return (f'<animateTransform attributeName="transform" type="rotate" '
                f'from="0 {cx} {cy}" to="360 {cx} {cy}" dur="0.3s" repeatCount="indefinite"/>')

    w1, w2 = spin(14, 15), spin(46, 15)
    return (
        '<rect x="0" y="1" width="5" height="2" fill="#e6edf3"/>'
        '<rect x="0" y="11" width="5" height="2" fill="#e6edf3"/>'
        '<rect x="0" y="2" width="3" height="10" fill="#111"/>'
        f'<path d="M5,11 L9,11 L14,6 L30,4 L39,5 L46,8 L55,9 L58,10 L58,12 '
        f'L51,13 L44,13 L39,14 L18,14 L11,13 L5,13 Z" fill="{color}"/>'
        '<path d="M25,6 Q30,-1 35,6" fill="none" stroke="#c9d1d9" stroke-width="1.3"/>'
        '<rect x="58" y="8" width="3" height="7" fill="#111"/>'
        '<rect x="56" y="7" width="5" height="2" fill="#e6edf3"/>'
        '<rect x="56" y="14" width="5" height="2" fill="#e6edf3"/>'
        f'<g>{w1}<circle cx="14" cy="15" r="4.5" fill="#111"/>'
        '<circle cx="14" cy="15" r="1.6" fill="#666"/>'
        '<line x1="14" y1="15" x2="14" y2="11" stroke="#888" stroke-width="1"/></g>'
        f'<g>{w2}<circle cx="46" cy="15" r="4.5" fill="#111"/>'
        '<circle cx="46" cy="15" r="1.6" fill="#666"/>'
        '<line x1="46" y1="15" x2="46" y2="11" stroke="#888" stroke-width="1"/></g>'
    )


def render_car(car: dict, static: bool) -> str:
    lane_center = TRACK_TOP + car["lane"] * LANE_H + LANE_H / 2
    y = lane_center - CAR_H / 2
    start_x, end_x = -CAR_W - 10, WIDTH + 10
    shape = car_shape(car["color"], static)

    if static:
        x = start_x + (0.2 + car["lane"] * 0.3) * (end_x - start_x)
        return f'<g transform="translate({x:.1f},{y:.1f})">{shape}</g>'

    return (
        f'<g transform="translate({start_x},{y:.1f})">'
        f'<animateTransform attributeName="transform" type="translate" '
        f'from="{start_x},{y:.1f}" to="{end_x},{y:.1f}" dur="{car["dur"]}s" '
        f'begin="{car["begin"]}s" repeatCount="indefinite"/>'
        f'{shape}</g>'
    )


def render_svg(static: bool) -> str:
    track_h = LANE_H * len(CARS)
    parts = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{WIDTH}" height="{HEIGHT}" '
        f'viewBox="0 0 {WIDTH} {HEIGHT}" font-family="SFMono-Regular, Consolas, Menlo, monospace">',
        '<defs><pattern id="checker" width="8" height="8" patternUnits="userSpaceOnUse">'
        '<rect width="8" height="8" fill="#e6edf3"/><rect width="4" height="4" fill="#111"/>'
        '<rect x="4" y="4" width="4" height="4" fill="#111"/></pattern></defs>',
        f'<rect width="{WIDTH}" height="{HEIGHT}" fill="{BG}"/>',
    ]

    for i in range(1, len(CARS)):
        y = TRACK_TOP + i * LANE_H
        parts.append(f'<line x1="0" y1="{y}" x2="{WIDTH - 24}" y2="{y}" stroke="{LANE_LINE}" '
                     f'stroke-width="2" stroke-dasharray="8 6"/>')

    parts.append(f'<rect x="{WIDTH - 22}" y="{TRACK_TOP}" width="18" height="{track_h}" '
                 f'fill="url(#checker)" stroke="#e6edf3" stroke-width="1"/>')

    for car in CARS:
        parts.append(render_car(car, static))

    caption = "mantej@github ~ $ ./race.sh  &#8212;  always building, always racing &#127954;"
    parts.append(f'<text x="{WIDTH / 2}" y="{HEIGHT - 12}" font-size="12" fill="{ACCENT}" '
                 f'text-anchor="middle">{caption}</text>')

    parts.append('</svg>')
    return "\n".join(parts)


def main() -> None:
    static = os.environ.get("STATIC") == "1"
    svg = render_svg(static)
    OUT_PATH.write_text(svg)
    print(f"wrote {OUT_PATH} ({'static' if static else 'looping'}, {WIDTH}x{HEIGHT})")


if __name__ == "__main__":
    main()
