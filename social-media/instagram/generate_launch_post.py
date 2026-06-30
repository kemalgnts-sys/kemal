#!/usr/bin/env python3
"""Generate GurbetDe Instagram launch post assets."""

from __future__ import annotations

import math
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

OUTPUT_DIR = Path(__file__).parent / "post-01-launch"
SIZE = 1080

# Brand palette
NAVY = (13, 27, 42)
WHITE = (255, 255, 255)
RED = (227, 10, 23)
BLACK = (10, 10, 10)
GOLD = (255, 204, 0)
BG = (247, 247, 245)
MUTED = (110, 110, 110)
LIGHT_BORDER = (225, 225, 222)

FONT_REGULAR = "/usr/share/fonts/truetype/noto/NotoSans-Regular.ttf"
FONT_BOLD = "/usr/share/fonts/truetype/noto/NotoSans-Bold.ttf"


def load_font(size: int, bold: bool = False) -> ImageFont.FreeTypeFont:
    return ImageFont.truetype(FONT_BOLD if bold else FONT_REGULAR, size)


def draw_star(draw: ImageDraw.ImageDraw, cx: float, cy: float, radius: float, fill: tuple[int, int, int]) -> None:
    points = []
    for i in range(10):
        angle = math.radians(-90 + i * 36)
        r = radius if i % 2 == 0 else radius * 0.42
        points.append((cx + r * math.cos(angle), cy + r * math.sin(angle)))
    draw.polygon(points, fill=fill)


def draw_logo(draw: ImageDraw.ImageDraw, x: int, y: int, size: int) -> None:
    radius = size // 5
    box = [x, y, x + size, y + size]
    draw.rounded_rectangle(box, radius=radius, fill=NAVY)

    stripe_h = max(4, size // 18)
    base_y = y + size - stripe_h * 3 - 6
    inset = size // 10
    for i, color in enumerate([BLACK, RED, GOLD]):
        draw.rectangle(
            [x + inset, base_y + i * stripe_h, x + size - inset, base_y + (i + 1) * stripe_h],
            fill=color,
        )

    center_x = x + size * 0.52
    center_y = y + size * 0.46
    outer_r = size * 0.28
    inner_r = size * 0.19
    bbox_outer = [center_x - outer_r, center_y - outer_r, center_x + outer_r, center_y + outer_r]
    bbox_inner = [
        center_x - inner_r + size * 0.06,
        center_y - inner_r,
        center_x + inner_r + size * 0.06,
        center_y + inner_r,
    ]
    draw.pieslice(bbox_outer, start=40, end=320, fill=WHITE)
    draw.pieslice(bbox_inner, start=40, end=320, fill=NAVY)
    bar_y = center_y
    draw.rectangle(
        [center_x - size * 0.02, bar_y - size * 0.045, center_x + outer_r * 0.95, bar_y + size * 0.045],
        fill=WHITE,
    )
    draw_star(draw, center_x - size * 0.08, center_y - size * 0.02, size * 0.055, RED)


def draw_gradient_line(draw: ImageDraw.ImageDraw, x1: int, y: int, x2: int, height: int = 3) -> None:
    width = x2 - x1
    for i in range(width):
        t = i / max(width - 1, 1)
        color = (
            int(55 + (255 - 55) * t),
            int(55 + (204 - 55) * t),
            int(55 + (0 - 55) * t),
        )
        draw.line([(x1 + i, y), (x1 + i, y + height)], fill=color)


def text_width(text: str, font: ImageFont.FreeTypeFont) -> int:
    bbox = font.getbbox(text)
    return bbox[2] - bbox[0]


def text_height(font: ImageFont.FreeTypeFont) -> int:
    bbox = font.getbbox("Ag")
    return bbox[3] - bbox[1]


def draw_centered_text(
    draw: ImageDraw.ImageDraw,
    text: str,
    y: int,
    font: ImageFont.FreeTypeFont,
    fill: tuple[int, int, int],
    width: int = SIZE,
) -> int:
    tw = text_width(text, font)
    th = text_height(font)
    draw.text(((width - tw) // 2, y), text, font=font, fill=fill)
    return y + th


def create_feed_post() -> Image.Image:
    img = Image.new("RGB", (SIZE, SIZE), BG)
    draw = ImageDraw.Draw(img)

    # Logo lockup — horizontal like brand identity
    logo_size = 160
    brand_font = load_font(68, bold=True)
    brand_text = "GurbetDe"
    brand_w = text_width(brand_text, brand_font)
    lockup_w = logo_size + 28 + brand_w
    lockup_x = (SIZE - lockup_w) // 2
    lockup_y = 130

    draw_logo(draw, lockup_x, lockup_y, logo_size)
    brand_x = lockup_x + logo_size + 28
    brand_y = lockup_y + 28
    draw.text((brand_x, brand_y), brand_text, font=brand_font, fill=BLACK)
    draw_gradient_line(draw, brand_x, brand_y + 78, brand_x + brand_w, height=3)

    # Announcement badge
    badge_font = load_font(20, bold=True)
    badge_text = "YENİ HESAP · İLK GÖNDERİ"
    badge_w = text_width(badge_text, badge_font) + 40
    badge_x = (SIZE - badge_w) // 2
    badge_y = lockup_y + logo_size + 56
    draw.rounded_rectangle([badge_x, badge_y, badge_x + badge_w, badge_y + 40], radius=20, fill=NAVY)
    draw.text(
        (badge_x + 20, badge_y + 9),
        badge_text,
        font=badge_font,
        fill=WHITE,
    )

    # Headline block
    headline_font = load_font(54, bold=True)
    sub_font = load_font(28)
    headline_y = badge_y + 72
    headline_y = draw_centered_text(draw, "Yolculuğumuz Başladı", headline_y, headline_font, NAVY)
    headline_y = draw_centered_text(
        draw,
        "Gurbetçi topluluklar için yeni buluşma noktası",
        headline_y + 20,
        sub_font,
        MUTED,
    )

    # Content card — text only
    card_margin = 80
    card_top = headline_y + 52
    card_h = 250
    card_bottom = card_top + card_h
    draw.rounded_rectangle(
        [card_margin, card_top, SIZE - card_margin, card_bottom],
        radius=28,
        fill=WHITE,
        outline=LIGHT_BORDER,
        width=2,
    )

    body_font = load_font(29)
    lines = [
        "Almanya'daki Türk topluluğu için",
        "oluşturduğumuz platformla yola çıkıyoruz.",
        "",
        "Kültürümüzü, deneyimlerimizi",
        "ve birbirimizi bir araya getiriyoruz.",
    ]
    y = card_top + 48
    for line in lines:
        if line:
            y = draw_centered_text(draw, line, y, body_font, BLACK)
            y += 12
        else:
            y += 18

    # Pills row below card
    pill_font = load_font(21, bold=True)
    pills = ["Topluluk", "Almanya", "Dayanışma"]
    icons = ["🇹🇷", "🇩🇪", "✦"]
    pill_labels = [f"{i}  {p}" for i, p in zip(icons, pills)]
    pill_ws = [text_width(l, pill_font) + 44 for l in pill_labels]
    row_w = sum(pill_ws) + 20
    px = (SIZE - row_w) // 2
    py = card_bottom + 32
    for label, pw in zip(pill_labels, pill_ws):
        draw.rounded_rectangle([px, py, px + pw, py + 50], radius=25, fill=(244, 246, 249), outline=LIGHT_BORDER)
        tw = text_width(label, pill_font)
        th = text_height(pill_font)
        draw.text((px + (pw - tw) // 2, py + (50 - th) // 2 - 1), label, font=pill_font, fill=NAVY)
        px += pw + 10

    # Footer CTA — clearly below pills
    cta_font = load_font(28, bold=True)
    draw_centered_text(draw, "Bizi takip edin · Çok yakında", 870, cta_font, NAVY)
    draw_centered_text(draw, "@gurbetde", 922, load_font(24), MUTED)

    return img


def create_story() -> Image.Image:
    width, height = 1080, 1920
    img = Image.new("RGB", (width, height), NAVY)
    draw = ImageDraw.Draw(img)

    for i in range(height):
        t = i / height
        color = (int(NAVY[0] + 18 * t), int(NAVY[1] + 14 * t), int(NAVY[2] + 22 * t))
        draw.line([(0, i), (width, i)], fill=color)

    logo_size = 220
    logo_x = (width - logo_size) // 2
    logo_y = 380
    draw_logo(draw, logo_x, logo_y, logo_size)

    brand_font = load_font(80, bold=True)
    y = draw_centered_text(draw, "GurbetDe", logo_y + logo_size + 44, brand_font, WHITE, width)
    draw_gradient_line(draw, width // 2 - 150, y + 20, width // 2 + 150, height=4)

    y = draw_centered_text(draw, "Artık Buradayız", y + 60, load_font(54, bold=True), WHITE, width)
    y = draw_centered_text(draw, "Gurbetçi topluluklar için", y + 24, load_font(30), (195, 205, 215), width)
    draw_centered_text(draw, "dijital buluşma noktası", y + 8, load_font(30), (195, 205, 215), width)

    draw.rounded_rectangle([110, 1540, 970, 1650], radius=30, fill=GOLD)
    cta = "Takip Et"
    cta_font = load_font(34, bold=True)
    draw.text(((width - text_width(cta, cta_font)) // 2, 1588), cta, font=cta_font, fill=BLACK)
    draw_centered_text(draw, "@gurbetde", 1720, load_font(28), (165, 175, 185), width)

    return img


def main() -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    create_feed_post().save(OUTPUT_DIR / "gurbetde-launch-feed-1080.png", optimize=True)
    create_story().save(OUTPUT_DIR / "gurbetde-launch-story-1080x1920.png", optimize=True)
    print(f"Saved assets to {OUTPUT_DIR}")


if __name__ == "__main__":
    main()
