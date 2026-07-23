#!/usr/bin/env python3
"""prepped grayscale photo -> self-typing monochrome ASCII portrait SVG.

Usage: python scripts/make_ascii_svg.py [source-prepped.png]
Output: avi-ascii.svg — each row wipes in left-to-right with a block cursor,
staggered top-to-bottom, prints once and freezes (no loop).
Env: STATIC=1 emits a frozen final frame (no SMIL) for Quick Look previews.
"""
import os
import sys
from pathlib import Path
from xml.sax.saxutils import escape

from PIL import Image

RAMP = " .`:-=+*cs#%@"          # leading space clears the background
COLS, ROWS = 100, 53
WIDTH = 370
CELL_W = WIDTH / COLS
CELL_H = CELL_W * 1.9            # monospace glyphs are taller than wide
HEIGHT = round(ROWS * CELL_H)
FONT_SIZE = CELL_H * 0.92

BG = "#0d1117"
TEXT_COLOR = "#c9d1d9"

ROW_DUR = 0.5          # seconds to wipe one row in
ROW_STAGGER = 0.045    # seconds between row starts
BASE_DELAY = 0.15
CURSOR_FADE = 0.15

OUT_NAME = "avi-ascii.svg"


def image_to_grid(path: str) -> list[str]:
    img = Image.open(path).convert("L").resize((COLS, ROWS), Image.LANCZOS)
    pixels = list(img.getdata())
    rows = []
    for r in range(ROWS):
        row_px = pixels[r * COLS:(r + 1) * COLS]
        chars = [RAMP[round((255 - p) / 255 * (len(RAMP) - 1))] for p in row_px]
        rows.append("".join(chars))
    return rows


def render_svg(rows: list[str], static: bool) -> str:
    row_w = COLS * CELL_W
    parts = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{WIDTH}" height="{HEIGHT}" '
        f'viewBox="0 0 {WIDTH} {HEIGHT}" font-family="SFMono-Regular, Consolas, Menlo, monospace">',
        f'<rect width="{WIDTH}" height="{HEIGHT}" fill="{BG}"/>',
    ]

    for i, row in enumerate(rows):
        top = i * CELL_H
        baseline = top + CELL_H * 0.82
        text = escape(row)
        delay = BASE_DELAY + i * ROW_STAGGER

        if static:
            parts.append(
                f'<text x="0" y="{baseline:.2f}" font-size="{FONT_SIZE:.2f}" fill="{TEXT_COLOR}" '
                f'textLength="{row_w:.2f}" lengthAdjust="spacingAndGlyphs" xml:space="preserve">{text}</text>'
            )
            continue

        clip_id = f"clip{i}"
        parts.append(
            f'<clipPath id="{clip_id}"><rect x="0" y="{top:.2f}" width="0" height="{CELL_H:.2f}">'
            f'<animate attributeName="width" from="0" to="{row_w:.2f}" dur="{ROW_DUR}s" '
            f'begin="{delay:.3f}s" fill="freeze"/></rect></clipPath>'
        )
        parts.append(
            f'<g clip-path="url(#{clip_id})">'
            f'<text x="0" y="{baseline:.2f}" font-size="{FONT_SIZE:.2f}" fill="{TEXT_COLOR}" '
            f'textLength="{row_w:.2f}" lengthAdjust="spacingAndGlyphs" xml:space="preserve">{text}</text>'
            f'</g>'
        )
        parts.append(
            f'<rect y="{top:.2f}" width="{CELL_W * 0.9:.2f}" height="{CELL_H * 0.85:.2f}" '
            f'fill="{TEXT_COLOR}" opacity="0.85">'
            f'<animate attributeName="x" from="0" to="{row_w:.2f}" dur="{ROW_DUR}s" '
            f'begin="{delay:.3f}s" fill="freeze"/>'
            f'<animate attributeName="opacity" from="0.85" to="0" dur="{CURSOR_FADE}s" '
            f'begin="{delay + ROW_DUR:.3f}s" fill="freeze"/>'
            f'</rect>'
        )

    parts.append('</svg>')
    return "\n".join(parts)


def main() -> None:
    src = sys.argv[1] if len(sys.argv) > 1 else "source-prepped.png"
    if not Path(src).exists():
        raise SystemExit(f"prepped photo not found: {src} (run prep_photo.py first)")

    static = os.environ.get("STATIC") == "1"
    rows = image_to_grid(src)
    svg = render_svg(rows, static)
    Path(OUT_NAME).write_text(svg)
    print(f"wrote {OUT_NAME} ({'static' if static else 'animated'}, {WIDTH}x{HEIGHT})")


if __name__ == "__main__":
    main()
