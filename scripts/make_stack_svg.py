#!/usr/bin/env python3
"""writes stack.svg — glassmorphism pill badges for the tech stack.

Usage: python scripts/make_stack_svg.py
Brand glyphs are fetched from the simple-icons CDN (jsdelivr) at generation
time; terms with no official icon (RAG, NLP, Computer Vision, REST APIs,
Monad, MetaMask) fall back to a tinted monogram chip.
Env: STATIC=1 skips the on-load shimmer sweep (frozen frame for Quick Look).
"""
import os
import re
from pathlib import Path
from xml.sax.saxutils import escape

import requests

OUT_PATH = Path("stack.svg")
WIDTH = 860
BG = "#0d1117"
TEXT = "#e6edf3"

# (category label, tint color, [(display name, simple-icons slug or None)])
CATEGORIES = [
    ("AI / ML & LLMs", "#6AD3FF", [
        ("Python", "python"), ("PyTorch", "pytorch"), ("TensorFlow", "tensorflow"),
        ("Hugging Face", "huggingface"), ("LangChain", "langchain"), ("OpenAI", "openai"),
        ("RAG", None), ("NLP", None), ("Computer Vision", None),
        ("Scikit-learn", "scikitlearn"), ("Pandas", "pandas"), ("NumPy", "numpy"),
    ]),
    ("Web / Backend", "#39d353", [
        ("TypeScript", "typescript"), ("JavaScript", "javascript"), ("Next.js", "nextdotjs"),
        ("React", "react"), ("Node.js", "nodedotjs"), ("Flask", "flask"), ("FastAPI", "fastapi"),
        ("Tailwind CSS", "tailwindcss"), ("REST APIs", None), ("HTML5", "html5"), ("CSS3", "css3"),
    ]),
    ("Web3 / Blockchain", "#DC0000", [
        ("Solidity", "solidity"), ("Ethereum", "ethereum"), ("Web3.js", "web3dotjs"),
        ("Ethers.js", "ethers"), ("IPFS", "ipfs"), ("MetaMask", None), ("Monad", None),
    ]),
    ("Data / Infra", "#a371f7", [
        ("Supabase", "supabase"), ("MongoDB", "mongodb"), ("PostgreSQL", "postgresql"),
        ("Firebase", "firebase"), ("Redis", "redis"), ("Stripe", "stripe"),
    ]),
    ("Cloud / DevOps / Tools", "#f0a020", [
        ("Docker", "docker"), ("Linux", "linux"), ("Git", "git"),
        ("GitHub Actions", "githubactions"), ("Azure", "microsoftazure"),
        ("Vercel", "vercel"), ("Postman", "postman"),
    ]),
]

ICON_CDN = "https://cdn.jsdelivr.net/npm/simple-icons@latest/icons/{slug}.svg"
PATH_RE = re.compile(r'<path\s+d="([^"]+)"')

MARGIN = 24
CAT_HEADER_H = 26
CHIP_H = 30
ICON_SIZE = 14
PAD_X = 14
GAP_ICON_TEXT = 7
GAP_CHIPS = 10
GAP_ROWS = 12
CAT_GAP = 22
FONT_SIZE = 13
CHAR_W = FONT_SIZE * 0.6

SHIMMER_DUR = 0.6
SHIMMER_BASE = 0.2
SHIMMER_SPAN = 1.0


def fetch_icon_paths(slug: str) -> list[str] | None:
    try:
        resp = requests.get(ICON_CDN.format(slug=slug), timeout=8)
        resp.raise_for_status()
        paths = PATH_RE.findall(resp.text)
        return paths or None
    except Exception:
        return None


def chip_width(label: str) -> float:
    return PAD_X + ICON_SIZE + GAP_ICON_TEXT + len(label) * CHAR_W + PAD_X


def render_icon(slug: str | None, cx: float, cy: float, tint: str, initials: str) -> str:
    paths = fetch_icon_paths(slug) if slug else None
    if paths:
        scale = ICON_SIZE / 24
        d = "".join(f'<path d="{p}" fill="{TEXT}"/>' for p in paths)
        return f'<g transform="translate({cx - ICON_SIZE / 2:.1f},{cy - ICON_SIZE / 2:.1f}) scale({scale:.4f})">{d}</g>'
    return (
        f'<circle cx="{cx:.1f}" cy="{cy:.1f}" r="{ICON_SIZE / 2:.1f}" fill="{tint}" fill-opacity="0.22" '
        f'stroke="{tint}" stroke-opacity="0.6"/>'
        f'<text x="{cx:.1f}" y="{cy + 2.5:.1f}" font-size="7" font-weight="700" fill="{tint}" '
        f'text-anchor="middle">{initials}</text>'
    )


def render_chip(idx: int, x: float, y: float, label: str, slug: str | None, tint: str, static: bool) -> tuple[str, float]:
    w = chip_width(label)
    clip_id = f"clip{idx}"
    glow_id_suffix = tint.lstrip("#")
    icon_cx = x + PAD_X + ICON_SIZE / 2
    icon_cy = y + CHIP_H / 2
    initials = "".join(w0[0] for w0 in label.replace("-", " ").split()[:2]).upper()

    parts = [f'<clipPath id="{clip_id}"><rect x="{x:.1f}" y="{y:.1f}" width="{w:.1f}" height="{CHIP_H}" rx="{CHIP_H / 2}"/></clipPath>']

    # base glass pill
    parts.append(f'<rect x="{x:.1f}" y="{y:.1f}" width="{w:.1f}" height="{CHIP_H}" rx="{CHIP_H / 2}" '
                 f'fill="#ffffff" fill-opacity="0.06" stroke="{tint}" stroke-opacity="0.35" '
                 f'filter="url(#chipShadow)"/>')

    # low-opacity category-tint glow behind the label
    parts.append(f'<ellipse cx="{x + w / 2:.1f}" cy="{y + CHIP_H / 2:.1f}" rx="{w / 2:.1f}" ry="{CHIP_H / 2:.1f}" '
                 f'fill="url(#glow-{glow_id_suffix})" clip-path="url(#{clip_id})"/>')

    # gloss: top-half white sheen, clipped to the pill outline
    parts.append(f'<rect x="{x:.1f}" y="{y:.1f}" width="{w:.1f}" height="{CHIP_H * 0.55:.1f}" '
                 f'fill="url(#glossGrad)" clip-path="url(#{clip_id})"/>')

    # subtle bright top edge (light-from-above cue)
    parts.append(f'<line x1="{x + CHIP_H / 2:.1f}" y1="{y + 1.5:.1f}" x2="{x + w - CHIP_H / 2:.1f}" y2="{y + 1.5:.1f}" '
                 f'stroke="#ffffff" stroke-opacity="0.22" stroke-width="1" stroke-linecap="round"/>')

    parts.append(render_icon(slug, icon_cx, icon_cy, tint, initials))

    text_x = x + PAD_X + ICON_SIZE + GAP_ICON_TEXT
    parts.append(f'<text x="{text_x:.1f}" y="{y + CHIP_H / 2 + 4.5:.1f}" font-size="{FONT_SIZE}" '
                 f'fill="{TEXT}">{escape(label)}</text>')

    if not static:
        begin = SHIMMER_BASE + (x / WIDTH) * SHIMMER_SPAN
        parts.append(
            f'<g clip-path="url(#{clip_id})">'
            f'<rect y="{y:.1f}" width="10" height="{CHIP_H}" fill="#ffffff" opacity="0">'
            f'<animate attributeName="x" from="{x - 24:.1f}" to="{x + w + 24:.1f}" dur="{SHIMMER_DUR}s" '
            f'begin="{begin:.2f}s" fill="freeze"/>'
            f'<animate attributeName="opacity" values="0;0.45;0" keyTimes="0;0.5;1" dur="{SHIMMER_DUR}s" '
            f'begin="{begin:.2f}s" fill="freeze"/>'
            f'</rect></g>'
        )

    return "".join(parts), w


def render_svg(static: bool) -> str:
    body = []
    defs = [
        '<filter id="chipShadow" x="-20%" y="-60%" width="140%" height="240%">'
        '<feDropShadow dx="0" dy="2" stdDeviation="3" flood-color="#000000" flood-opacity="0.35"/></filter>',
        '<linearGradient id="glossGrad" x1="0" y1="0" x2="0" y2="1">'
        '<stop offset="0%" stop-color="#ffffff" stop-opacity="0.22"/>'
        '<stop offset="100%" stop-color="#ffffff" stop-opacity="0"/></linearGradient>',
    ]
    for _, tint, _ in CATEGORIES:
        defs.append(
            f'<radialGradient id="glow-{tint.lstrip("#")}" cx="50%" cy="50%" r="65%">'
            f'<stop offset="0%" stop-color="{tint}" stop-opacity="0.30"/>'
            f'<stop offset="100%" stop-color="{tint}" stop-opacity="0"/></radialGradient>'
        )

    y = MARGIN
    chip_idx = 0
    for cat_label, tint, items in CATEGORIES:
        body.append(f'<text x="{MARGIN}" y="{y + 14:.1f}" font-size="14" font-weight="700" '
                    f'fill="{tint}">{escape(cat_label)}</text>')
        y += CAT_HEADER_H

        x = MARGIN
        row_start_y = y
        for label, slug in items:
            w = chip_width(label)
            if x + w > WIDTH - MARGIN and x > MARGIN:
                x = MARGIN
                y += CHIP_H + GAP_ROWS
            chip_svg, w = render_chip(chip_idx, x, y, label, slug, tint, static)
            body.append(chip_svg)
            chip_idx += 1
            x += w + GAP_CHIPS
        y += CHIP_H + CAT_GAP

    height = round(y - CAT_GAP + MARGIN)

    svg = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{WIDTH}" height="{height}" '
        f'viewBox="0 0 {WIDTH} {height}" font-family="SFMono-Regular, Consolas, Menlo, monospace">',
        f'<defs>{"".join(defs)}</defs>',
        f'<rect width="{WIDTH}" height="{height}" fill="{BG}"/>',
        *body,
        '</svg>',
    ]
    return "\n".join(svg)


def main() -> None:
    static = os.environ.get("STATIC") == "1"
    svg = render_svg(static)
    OUT_PATH.write_text(svg)
    print(f"wrote {OUT_PATH} ({'static' if static else 'animated'})")


if __name__ == "__main__":
    main()
