#!/usr/bin/env python3
"""source photo -> background removed, contrast-boosted, white-composited grayscale PNG.

Usage: python scripts/prep_photo.py source-photo.jpg
Output: source-prepped.png (same directory), used by make_ascii_svg.py.
"""
import sys
from pathlib import Path

import cv2
import numpy as np
from PIL import Image
from rembg import remove

OUT_NAME = "source-prepped.png"


def prep_photo(src_path: str, out_path: str = OUT_NAME) -> None:
    src = Path(src_path)
    if not src.exists():
        raise SystemExit(f"photo not found: {src}")

    raw = Image.open(src).convert("RGBA")
    cutout = remove(raw)  # rembg: alpha-matted subject on transparent bg

    rgb = np.array(cutout.convert("RGB"))
    alpha = np.array(cutout)[:, :, 3].astype(np.float32) / 255.0

    # local contrast boost (CLAHE on the L channel only, keeps colors sane)
    lab = cv2.cvtColor(rgb, cv2.COLOR_RGB2LAB)
    l, a, b = cv2.split(lab)
    clahe = cv2.createCLAHE(clipLimit=2.5, tileGridSize=(8, 8))
    l = clahe.apply(l)
    contrasted = cv2.cvtColor(cv2.merge((l, a, b)), cv2.COLOR_LAB2RGB).astype(np.float32)

    # composite onto pure white so background maps to the blank end of the ascii ramp
    white = np.full_like(contrasted, 255.0)
    mask = alpha[:, :, None]
    composited = (contrasted * mask + white * (1 - mask)).astype(np.uint8)

    gray = cv2.cvtColor(composited, cv2.COLOR_RGB2GRAY)
    Image.fromarray(gray).save(out_path)
    print(f"wrote {out_path} ({gray.shape[1]}x{gray.shape[0]})")


if __name__ == "__main__":
    prep_photo(sys.argv[1] if len(sys.argv) > 1 else "source-photo.jpg")
