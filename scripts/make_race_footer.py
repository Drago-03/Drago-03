#!/usr/bin/env python3
"""standalone footer: three F1 cars racing away from a 3/4 overhead camera,
up a perspective track toward a horizon finish line, looping forever with
a different leader each lap.

Usage: python scripts/make_race_footer.py
Output: race-footer.svg (~860x200). Static asset — not part of the daily
contribution-graph refresh, commit it once and forget it.
Env: STATIC=1 emits a frozen frame (no SMIL) for Quick Look previews.
"""
import math
import os
from pathlib import Path

WIDTH, HEIGHT = 860, 200
BG = "#0d1117"
ACCENT = "#6AD3FF"

# perspective: trapezoid track, narrow at the horizon (top), wide at camera (bottom)
CENTER_X = WIDTH / 2
TOP_HW, BOTTOM_HW = 70, 410      # track half-width at horizon vs. at camera
HORIZON_Y, BOTTOM_Y = 24, 176
SCALE_MIN, SCALE_MAX = 0.42, 1.05  # car scale far (horizon) vs. near (camera)

SAMPLES = 28
OUT_PATH = Path("race-footer.svg")

CARS = [
    {
        "name": "red", "color": "#DC0000", "light": "#ff5c5c", "lane_r": -0.55,
        "dur": 4.6, "begin": 0.0,
        "p_kt": (0, 0.22, 0.5, 0.78, 1), "p_v": (1, 0.78, 0.5, 0.2, 0),
        "weave_period": 1.7, "weave_amp": 0.10, "phase": 0.0,
    },
    {
        "name": "cyan", "color": "#6AD3FF", "light": "#bdeeff", "lane_r": 0.0,
        "dur": 4.1, "begin": 0.5,
        "p_kt": (0, 0.15, 0.45, 0.7, 1), "p_v": (1, 0.82, 0.55, 0.22, 0),
        "weave_period": 1.4, "weave_amp": 0.09, "phase": 1.0,
    },
    {
        "name": "green", "color": "#39d353", "light": "#95f7b6", "lane_r": 0.55,
        "dur": 5.0, "begin": 1.0,
        "p_kt": (0, 0.3, 0.6, 0.85, 1), "p_v": (1, 0.7, 0.5, 0.18, 0),
        "weave_period": 2.0, "weave_amp": 0.11, "phase": 2.0,
    },
]


def project(t: float, r: float) -> tuple[float, float, float]:
    """t: 0 at horizon (far) -> 1 at camera (near). r: -1..1 across track width."""
    half_w = TOP_HW + t * (BOTTOM_HW - TOP_HW)
    y = HORIZON_Y + t * (BOTTOM_Y - HORIZON_Y)
    x = CENTER_X + r * half_w
    return x, y, half_w


def lerp_piecewise(frac: float, keytimes: tuple, values: tuple) -> float:
    for i in range(len(keytimes) - 1):
        k0, k1 = keytimes[i], keytimes[i + 1]
        if k0 <= frac <= k1:
            span = (k1 - k0) or 1e-9
            local = (frac - k0) / span
            return values[i] + local * (values[i + 1] - values[i])
    return values[-1]


def edge_fade(frac: float, margin: float = 0.06) -> float:
    if frac < margin:
        return frac / margin
    if frac > 1 - margin:
        return (1 - frac) / margin
    return 1.0


def car_template(color: str, light: str, static: bool) -> str:
    spin = "" if static else (
        '<animateTransform attributeName="transform" type="rotate" '
        'from="0 {cx} {cy}" to="360 {cx} {cy}" dur="0.22s" repeatCount="indefinite"/>'
    )

    def wheel(cx: float, cy: float) -> str:
        s = spin.format(cx=cx, cy=cy) if not static else ""
        return (f'<g>{s}<ellipse cx="{cx}" cy="{cy}" rx="3.2" ry="2.4" fill="#111"/>'
                f'<circle cx="{cx}" cy="{cy}" r="1.1" fill="#666"/>'
                f'<line x1="{cx}" y1="{cy}" x2="{cx}" y2="{cy - 2}" stroke="#999" stroke-width="0.8"/></g>')

    return (
        # soft blurred contact shadow on the track — sells the overhead 3D read
        '<ellipse cx="2" cy="6" rx="13" ry="5" fill="#000000" opacity="0.4" filter="url(#carBlur)"/>'
        # trailing speed smear behind the car (toward camera, i.e. +y)
        f'<ellipse cx="0" cy="24" rx="6" ry="11" fill="{color}" opacity="0.16" filter="url(#carBlur)"/>'
        # front + rear wheels
        + wheel(-9, -11) + wheel(9, -11) + wheel(-9, 11) + wheel(9, 11)
        # rear wing (near/camera end) with endplates
        + f'<rect x="-10" y="17" width="20" height="4" fill="#111"/>'
        f'<rect x="-11" y="13" width="2" height="8" fill="{light}"/>'
        f'<rect x="9" y="13" width="2" height="8" fill="{light}"/>'
        # body: darker base polygon + lighter inset top-face for fake volume
        f'<polygon points="0,-23 7,-14 9,0 8,14 0,20 -8,14 -9,0 -7,-14" fill="{color}"/>'
        f'<polygon points="0,-19 4,-11 5,0 4,10 0,16 -4,10 -5,0 -4,-11" fill="{light}"/>'
        # halo + cockpit
        '<ellipse cx="0" cy="-3" rx="5" ry="7" fill="none" stroke="#c9d1d9" stroke-width="1.2"/>'
        '<ellipse cx="0" cy="-3" rx="3" ry="4" fill="#111"/>'
        # front wing (far/horizon end)
        '<rect x="-9" y="-24" width="18" height="3" fill="#111"/>'
    )


def render_car(car: dict, static: bool) -> str:
    dur, begin = car["dur"], car["begin"]

    if static:
        t = 0.5
        r = car["lane_r"]
        x, y, _ = project(t, r)
        scale = SCALE_MIN + t * (SCALE_MAX - SCALE_MIN)
        shape = car_template(car["color"], car["light"], static=True)
        return f'<g transform="translate({x:.1f},{y:.1f}) scale({scale:.3f})">{shape}</g>'

    xs, ys, scales, opacities = [], [], [], []
    for i in range(SAMPLES):
        frac = i / (SAMPLES - 1)
        t = lerp_piecewise(frac, car["p_kt"], car["p_v"])
        elapsed = frac * dur
        weave = car["weave_amp"] * math.sin(2 * math.pi * elapsed / car["weave_period"] + car["phase"])
        r = max(-0.92, min(0.92, car["lane_r"] + weave))
        x, y, _ = project(t, r)
        xs.append(x)
        ys.append(y)
        scales.append(SCALE_MIN + t * (SCALE_MAX - SCALE_MIN))
        opacities.append(edge_fade(frac))

    key_times = ";".join(f"{i / (SAMPLES - 1):.4f}" for i in range(SAMPLES))
    translate_vals = ";".join(f"{x:.1f},{y:.1f}" for x, y in zip(xs, ys))
    scale_vals = ";".join(f"{s:.3f}" for s in scales)
    opacity_vals = ";".join(f"{o:.3f}" for o in opacities)

    shape = car_template(car["color"], car["light"], static=False)
    return (
        f'<g opacity="0">'
        f'<animate attributeName="opacity" values="{opacity_vals}" keyTimes="{key_times}" '
        f'dur="{dur}s" begin="{begin}s" repeatCount="indefinite"/>'
        f'<animateTransform attributeName="transform" type="translate" values="{translate_vals}" '
        f'keyTimes="{key_times}" dur="{dur}s" begin="{begin}s" repeatCount="indefinite"/>'
        f'<g><animateTransform attributeName="transform" type="scale" values="{scale_vals}" '
        f'keyTimes="{key_times}" dur="{dur}s" begin="{begin}s" repeatCount="indefinite"/>'
        f'{shape}</g></g>'
    )


def render_track(static: bool) -> str:
    parts = []

    top_l, _, _ = project(0, -1)
    top_r, _, _ = project(0, 1)
    bot_l, bot_ly, _ = project(1, -1)
    bot_r, _, _ = project(1, 1)
    parts.append(f'<polygon points="{top_l:.1f},{HORIZON_Y} {top_r:.1f},{HORIZON_Y} '
                 f'{bot_r:.1f},{bot_ly:.1f} {bot_l:.1f},{bot_ly:.1f}" fill="url(#trackGrad)"/>')

    # side barriers (red/white curb stripes), converging with the track edges
    for side in (-1, 1):
        i_l_x, _, _ = project(0, side * 1.0)
        i_r_x, _, _ = project(0, side * 1.07)
        o_l_x, o_ly, _ = project(1, side * 1.0)
        o_r_x, _, _ = project(1, side * 1.08)
        parts.append(f'<polygon points="{i_l_x:.1f},{HORIZON_Y} {i_r_x:.1f},{HORIZON_Y} '
                     f'{o_r_x:.1f},{o_ly:.1f} {o_l_x:.1f},{o_ly:.1f}" fill="url(#barrier)"/>')

    # checkered start/finish band near the horizon
    band_tl, _, _ = project(0, -1)
    band_tr, _, _ = project(0, 1)
    band_bl, band_by, _ = project(0.07, -1)
    band_br, _, _ = project(0.07, 1)
    parts.append(f'<polygon points="{band_tl:.1f},{HORIZON_Y} {band_tr:.1f},{HORIZON_Y} '
                 f'{band_br:.1f},{band_by:.1f} {band_bl:.1f},{band_by:.1f}" fill="url(#checker)"/>')

    # lane dividers, converging, tapering thinner near the horizon, dashes scrolling toward camera
    dash_anim = "" if static else (
        '<animate attributeName="stroke-dashoffset" values="0;-40" dur="0.7s" repeatCount="indefinite"/>'
    )
    for r in (-1 / 3, 1 / 3):
        mid_x, mid_y, _ = project(0.5, r)
        top_x, _, _ = project(0.07, r)
        bot_x, bot_y, _ = project(1, r)
        parts.append(f'<line x1="{top_x:.1f}" y1="{band_by:.1f}" x2="{mid_x:.1f}" y2="{mid_y:.1f}" '
                     f'stroke="#e6edf3" stroke-opacity="0.55" stroke-width="1" stroke-dasharray="6 6">'
                     f'{dash_anim}</line>')
        parts.append(f'<line x1="{mid_x:.1f}" y1="{mid_y:.1f}" x2="{bot_x:.1f}" y2="{bot_y:.1f}" '
                     f'stroke="#e6edf3" stroke-opacity="0.55" stroke-width="2.5" stroke-dasharray="10 8">'
                     f'{dash_anim}</line>')

    return "".join(parts)


def render_svg(static: bool) -> str:
    defs = (
        '<linearGradient id="trackGrad" x1="0" y1="0" x2="0" y2="1">'
        '<stop offset="0%" stop-color="#262c36"/><stop offset="100%" stop-color="#1a1f27"/></linearGradient>'
        '<pattern id="checker" width="10" height="10" patternUnits="userSpaceOnUse">'
        '<rect width="10" height="10" fill="#e6edf3"/><rect width="5" height="5" fill="#111"/>'
        '<rect x="5" y="5" width="5" height="5" fill="#111"/></pattern>'
        '<pattern id="barrier" width="10" height="10" patternTransform="rotate(45)" patternUnits="userSpaceOnUse">'
        '<rect width="10" height="10" fill="#e6edf3"/><rect width="5" height="10" fill="#DC0000"/></pattern>'
        '<filter id="carBlur" x="-60%" y="-60%" width="220%" height="220%">'
        '<feGaussianBlur stdDeviation="1.6"/></filter>'
    )

    caption = "mantej@github ~ $ ./race.sh  &#8212;  always building, always racing &#127954;"

    svg = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{WIDTH}" height="{HEIGHT}" '
        f'viewBox="0 0 {WIDTH} {HEIGHT}" font-family="SFMono-Regular, Consolas, Menlo, monospace">',
        f'<defs>{defs}</defs>',
        f'<rect width="{WIDTH}" height="{HEIGHT}" fill="{BG}"/>',
        render_track(static),
        *[render_car(car, static) for car in CARS],
        f'<text x="{WIDTH / 2}" y="{HEIGHT - 10}" font-size="12" fill="{ACCENT}" '
        f'text-anchor="middle">{caption}</text>',
        '</svg>',
    ]
    return "\n".join(svg)


def main() -> None:
    static = os.environ.get("STATIC") == "1"
    svg = render_svg(static)
    OUT_PATH.write_text(svg)
    print(f"wrote {OUT_PATH} ({'static' if static else 'looping'}, {WIDTH}x{HEIGHT})")


if __name__ == "__main__":
    main()
