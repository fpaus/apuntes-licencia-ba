# /// script
# dependencies = ["pillow"]
# ///
"""Draw the PWA icons into app/. Run: uv run scripts/make_icons.py"""
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

APP = Path(__file__).resolve().parent.parent / "app"
GREEN, WHITE = (47, 138, 79), (255, 255, 255)
FONT = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"


def icon(size, safe):
    """Steering wheel over 'B1'. safe < 1 shrinks the drawing into the maskable safe zone."""
    img = Image.new("RGB", (size, size), GREEN)
    d = ImageDraw.Draw(img)
    c, r = size / 2, size * 0.30 * safe
    w = max(2, int(size * 0.045 * safe))
    cy = c - size * 0.08 * safe
    d.ellipse([c - r, cy - r, c + r, cy + r], outline=WHITE, width=w)
    d.ellipse([c - r * 0.22, cy - r * 0.22, c + r * 0.22, cy + r * 0.22], fill=WHITE)
    for dx, dy in ((-1, 0), (1, 0), (0, 1)):  # three spokes
        d.line([c, cy, c + dx * r, cy + dy * r], fill=WHITE, width=w)
    font = ImageFont.truetype(FONT, int(size * 0.17 * safe))
    d.text((c, cy + r + size * 0.11 * safe), "B1", font=font, fill=WHITE, anchor="mm")
    return img


for name, size, safe in [("icon-192.png", 192, 1), ("icon-512.png", 512, 1),
                         ("icon-maskable-512.png", 512, 0.78), ("apple-touch-icon.png", 180, 0.9)]:
    icon(size, safe).save(APP / name, optimize=True)
print("ok")
