"""
Generate GumaSpending PWA icons to match GumaStockReport/GumaPhoto style.
Dark background (#050505) with emerald (#10b981) wallet/won glyph.

Usage (one-shot, commit resulting PNGs):
    python scripts/generate_icons.py
"""

from __future__ import annotations

from pathlib import Path

from PIL import Image, ImageDraw

BG = (5, 5, 5, 255)            # #050505
FG = (16, 185, 129, 255)       # #10b981 emerald

OUT_DIR = Path(__file__).resolve().parent.parent / "static" / "icons"
OUT_DIR.mkdir(parents=True, exist_ok=True)


def draw_won(size: int) -> Image.Image:
    img = Image.new("RGBA", (size, size), BG)
    d = ImageDraw.Draw(img)

    # Scale reference: 512px canvas, glyph centered in middle 60%.
    s = size / 512
    cx = size / 2

    stroke = int(44 * s)
    top = int(150 * s)
    bottom = int(362 * s)

    # Two diagonals forming "W"
    peaks = [
        (int(128 * s), top),
        (int(200 * s), bottom),
        (int(cx), int(235 * s)),
        (int(324 * s), bottom),
        (int(384 * s), top),
    ]
    d.line(peaks, fill=FG, width=stroke, joint="curve")

    # Two horizontal bars (Korean won 원 signature)
    bar_y1 = int(225 * s)
    bar_y2 = int(270 * s)
    bar_x1 = int(100 * s)
    bar_x2 = int(412 * s)
    bar_stroke = int(28 * s)
    d.line([(bar_x1, bar_y1), (bar_x2, bar_y1)], fill=FG, width=bar_stroke)
    d.line([(bar_x1, bar_y2), (bar_x2, bar_y2)], fill=FG, width=bar_stroke)

    return img


def main() -> None:
    for size in (192, 512):
        img = draw_won(size)
        out = OUT_DIR / f"icon-{size}x{size}.png"
        img.save(out, format="PNG")
        print(f"wrote {out}")

    apple = draw_won(180)
    out = OUT_DIR / "apple-touch-icon.png"
    apple.save(out, format="PNG")
    print(f"wrote {out}")


if __name__ == "__main__":
    main()
