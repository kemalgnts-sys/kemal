#!/usr/bin/env python3
"""Generate GurbetDe Faz-0 assets into content-group folders."""

from __future__ import annotations

from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).parent
SIZE = 1080

NAVY = (13, 27, 42)
WHITE = (255, 255, 255)
RED = (227, 10, 23)
GOLD = (255, 204, 0)
MUTED = (180, 190, 200)

FONT_REG = "/usr/share/fonts/truetype/noto/NotoSans-Regular.ttf"
FONT_BOLD = "/usr/share/fonts/truetype/noto/NotoSans-Bold.ttf"


def font(size: int, bold: bool = False) -> ImageFont.FreeTypeFont:
    return ImageFont.truetype(FONT_BOLD if bold else FONT_REG, size)


def tw(text: str, f: ImageFont.FreeTypeFont) -> int:
    return f.getbbox(text)[2] - f.getbbox(text)[0]


def wrap(draw: ImageDraw.ImageDraw, text: str, f: ImageFont.FreeTypeFont, max_w: int) -> list[str]:
    words = text.split()
    lines: list[str] = []
    cur = ""
    for w in words:
        trial = f"{cur} {w}".strip()
        if tw(trial, f) <= max_w:
            cur = trial
        else:
            if cur:
                lines.append(cur)
            cur = w
    if cur:
        lines.append(cur)
    return lines or [text]


def wordmark(draw: ImageDraw.ImageDraw, x: int = 56, y: int = 48) -> None:
    f = font(42, bold=True)
    draw.text((x, y), "Gurbet", font=f, fill=WHITE)
    w = tw("Gurbet", f)
    draw.text((x + w, y), "De", font=f, fill=RED)


def footer(draw: ImageDraw.ImageDraw, swipe: bool = True) -> None:
    if swipe:
        f = font(28, bold=True)
        t = "Kaydır →"
        draw.text(((SIZE - tw(t, f)) // 2, 960), t, font=f, fill=GOLD)
    f2 = font(24, bold=False)
    u = "gurbetde.com"
    draw.text(((SIZE - tw(u, f2)) // 2, 1005), u, font=f2, fill=MUTED)


def slide_no(draw: ImageDraw.ImageDraw, n: int, total: int) -> None:
    f = font(26, bold=True)
    t = f"{n}/{total}"
    draw.text((SIZE - 56 - tw(t, f), 56), t, font=f, fill=GOLD)


def base() -> tuple[Image.Image, ImageDraw.ImageDraw]:
    img = Image.new("RGB", (SIZE, SIZE), NAVY)
    draw = ImageDraw.Draw(img)
    draw.rectangle([24, 24, SIZE - 24, SIZE - 24], outline=(30, 48, 70), width=2)
    return img, draw


def draw_lines(draw: ImageDraw.ImageDraw, lines: list[str], y: int, f: ImageFont.FreeTypeFont, fill, gap: int = 12) -> int:
    for line in lines:
        draw.text(((SIZE - tw(line, f)) // 2, y), line, font=f, fill=fill)
        y += (f.getbbox("Ag")[3] - f.getbbox("Ag")[1]) + gap
    return y


def make_text_slide(
    out: Path,
    n: int,
    total: int,
    title: str,
    body: str | list[str],
    *,
    swipe: bool = True,
    title_size: int = 56,
) -> None:
    img, draw = base()
    wordmark(draw)
    slide_no(draw, n, total)
    tf = font(title_size, bold=True)
    title_lines = wrap(draw, title, tf, SIZE - 120)
    y = 280
    y = draw_lines(draw, title_lines, y, tf, WHITE, gap=10)
    y += 28
    bf = font(30, bold=False)
    if isinstance(body, list):
        for item in body:
            line = f"· {item}" if not item.startswith("·") else item
            for wl in wrap(draw, line, bf, SIZE - 160):
                draw.text((90, y), wl, font=bf, fill=MUTED)
                y += 44
            y += 8
    else:
        for wl in wrap(draw, body, bf, SIZE - 140):
            draw.text(((SIZE - tw(wl, bf)) // 2, y), wl, font=bf, fill=MUTED)
            y += 42
    footer(draw, swipe=swipe)
    out.parent.mkdir(parents=True, exist_ok=True)
    img.save(out, "PNG")
    print("wrote", out)


def make_hook_slide(out: Path, n: int, total: int, h1: str, sub: str) -> None:
    img, draw = base()
    wordmark(draw)
    slide_no(draw, n, total)
    tf = font(64, bold=True)
    y = 360
    y = draw_lines(draw, wrap(draw, h1, tf, SIZE - 120), y, tf, WHITE, gap=8)
    y += 24
    sf = font(32, bold=False)
    draw_lines(draw, wrap(draw, sub, sf, SIZE - 140), y, sf, GOLD, gap=8)
    footer(draw, swipe=True)
    out.parent.mkdir(parents=True, exist_ok=True)
    img.save(out, "PNG")
    print("wrote", out)


def make_cta_slide(out: Path, n: int, total: int, h1: str, url: str) -> None:
    img, draw = base()
    wordmark(draw)
    slide_no(draw, n, total)
    tf = font(52, bold=True)
    y = 380
    y = draw_lines(draw, wrap(draw, h1, tf, SIZE - 120), y, tf, WHITE, gap=8)
    y += 36
    uf = font(34, bold=True)
    draw_lines(draw, wrap(draw, url, uf, SIZE - 120), y, uf, GOLD, gap=8)
    y += 80
    cf = font(28, bold=True)
    draw_lines(draw, ["Kaydet · Paylaş"], y, cf, MUTED, gap=8)
    footer(draw, swipe=False)
    out.parent.mkdir(parents=True, exist_ok=True)
    img.save(out, "PNG")
    print("wrote", out)


def make_single(out: Path, lines: list[tuple[str, int, tuple, bool]]) -> None:
    img, draw = base()
    wordmark(draw)
    y = 300
    for text, size, color, bold in lines:
        f = font(size, bold=bold)
        for wl in wrap(draw, text, f, SIZE - 120):
            draw.text(((SIZE - tw(wl, f)) // 2, y), wl, font=f, fill=color)
            y += (f.getbbox("Ag")[3] - f.getbbox("Ag")[1]) + 14
        y += 10
    footer(draw, swipe=False)
    out.parent.mkdir(parents=True, exist_ok=True)
    img.save(out, "PNG")
    print("wrote", out)


def make_highlight(out: Path, label: str) -> None:
    img = Image.new("RGB", (SIZE, SIZE), NAVY)
    draw = ImageDraw.Draw(img)
    draw.ellipse([240, 200, 840, 800], outline=GOLD, width=8)
    f = font(56, bold=True)
    draw.text(((SIZE - tw(label, f)) // 2, 470), label, font=f, fill=WHITE)
    wordmark(draw)
    out.parent.mkdir(parents=True, exist_ok=True)
    img.save(out, "PNG")
    print("wrote", out)


def make_reel_cover(out: Path, lines: list[tuple[str, int, tuple, bool]]) -> None:
    w, h = 1080, 1920
    img = Image.new("RGB", (w, h), NAVY)
    draw = ImageDraw.Draw(img)
    draw.rectangle([24, 24, w - 24, h - 24], outline=(30, 48, 70), width=2)
    f = font(42, bold=True)
    draw.text((56, 64), "Gurbet", font=f, fill=WHITE)
    draw.text((56 + tw("Gurbet", f), 64), "De", font=f, fill=RED)
    y = 720
    for text, size, color, bold in lines:
        ff = font(size, bold=bold)
        for wl in wrap(draw, text, ff, w - 120):
            draw.text(((w - tw(wl, ff)) // 2, y), wl, font=ff, fill=color)
            y += (ff.getbbox("Ag")[3] - ff.getbbox("Ag")[1]) + 16
        y += 12
    uf = font(28, bold=False)
    u = "gurbetde.com"
    draw.text(((w - tw(u, uf)) // 2, 1780), u, font=uf, fill=MUTED)
    out.parent.mkdir(parents=True, exist_ok=True)
    img.save(out, "PNG")
    print("wrote", out)


def gen_highlights() -> None:
    d = ROOT / "00-profil" / "kapaklar"
    for slug, label in [
        ("rehber", "REHBER"),
        ("forum", "FORUM"),
        ("ilanlar", "İLANLAR"),
        ("konsolosluk", "KONSOLOSLUK"),
        ("sehirler", "ŞEHİRLER"),
        ("basla", "BAŞLA"),
    ]:
        make_highlight(d / f"{slug}.png", label)


def gen_p03() -> None:
    d = ROOT / "A-rehber-burokrasi" / "gun-01-anmeldung-carousel" / "slides"
    make_hook_slide(d / "01.png", 1, 6, "Anmeldung'u erteleme", "14 gün kuralı + belge listesi — Türkçe")
    make_text_slide(d / "02.png", 2, 6, "Anmeldung nedir?", "Adresini Bürgeramt'a resmi bildirmek. Anmeldebestätigung olmadan banka, sigorta ve birçok işlem kilitlenir.")
    make_text_slide(d / "03.png", 3, 6, "Yanına al", ["Pasaport/Kimlik", "Wohnungsgeberbestätigung", "Mietvertrag", "Anmeldung formu", "(varsa) aile belgeleri"])
    make_text_slide(d / "04.png", 4, 6, "Termin gerçeği", "Büyük şehirde randevusuz gitme. Sabah erken slot açılır; iptalleri takip et. Berlin → service.berlin.de")
    make_text_slide(d / "05.png", 5, 6, "Belgeyi sakla", "Anmeldebestätigung fotokopisi: banka ve işveren ister. Taşınınca yeniden Anmeldung.")
    make_cta_slide(d / "06.png", 6, 6, "Adım adım rehber", "gurbetde.com/guide/anmeldung")


def gen_p05() -> None:
    d = ROOT / "B-topluluk-forum" / "gun-03-forum-kanit" / "slides"
    make_hook_slide(d / "01.png", 1, 5, "Forumda bugün", "Wohnungsgeberbestätigung imzalanmıyor — ne olur?")
    make_text_slide(d / "02.png", 2, 5, "Sorun", "Ev sahibi formu imzalamıyor. Anmeldung bekliyor.")
    make_text_slide(d / "03.png", 3, 5, "Neden kritik", "Bu belge olmadan Bürgeramt kaydı çoğu yerde yürümüyor.")
    make_text_slide(d / "04.png", 4, 5, "Ne yapılır", "Aynı yolu geçmişlerin deneyimini oku. Sorunu foruma yaz.")
    make_cta_slide(d / "05.png", 5, 5, "Şehrini seç · Konu aç", "gurbetde.com/forum")


def gen_p07() -> None:
    make_single(
        ROOT / "B-topluluk-forum" / "gun-05-berlin" / "01.png",
        [
            ("BERLİN", 72, WHITE, True),
            ("Bu hafta sorulanlar", 34, GOLD, True),
            ("· Anmeldung / Bürgeramt termin", 30, MUTED, False),
            ("· WG & Schufa", 30, MUTED, False),
            ("· Dil kursu ilanları", 30, MUTED, False),
            ("Şehrini seç → gurbetde.com", 28, WHITE, True),
        ],
    )


def gen_p08() -> None:
    d = ROOT / "A-rehber-burokrasi" / "gun-06-schufa-konut" / "slides"
    make_hook_slide(d / "01.png", 1, 5, 'Schufa "keine Information"', "Ev sahibi yine dosya istiyor")
    make_text_slide(d / "02.png", 2, 5, "Bu ne demek", 'Yeni gelende kayıt boş olabilir — "skor yok" ≠ "kötü skor".')
    make_text_slide(d / "03.png", 3, 5, "Dosyaya ne eklenir", ["İş sözleşmesi", "Banka ekstre", "Kefil/garanti", "Mieterselbstauskunft"])
    make_text_slide(d / "04.png", 4, 5, "Soru foruma", "Senin şehirde ne işe yaradı?")
    make_cta_slide(d / "05.png", 5, 5, "Forum + kira rehberi", "gurbetde.com/forum")


def gen_p10() -> None:
    d = ROOT / "A-rehber-burokrasi" / "gun-08-kira-wg" / "slides"
    make_hook_slide(d / "01.png", 1, 6, "WG / kira dosyası", "Başvurudan önce checklist")
    make_text_slide(d / "02.png", 2, 6, "Mietvertrag", "Sözleşmeyi okumadan imzalama.")
    make_text_slide(d / "03.png", 3, 6, "Kaution + Nebenkosten", "Net aylık maliyeti hesapla.")
    make_text_slide(d / "04.png", 4, 6, "Untermiete vs Zwischenmiete", "Türü netleştir — hakların değişir.")
    make_text_slide(d / "05.png", 5, 6, "İlanlarda şehir seç", "Berlin'den Münih'e — filtrele, gör.")
    make_cta_slide(d / "06.png", 6, 6, "İlanlara git", "gurbetde.com/ilanlar")


def gen_reel_covers() -> None:
    make_reel_cover(
        ROOT / "A-rehber-burokrasi" / "gun-02-anmeldung-banka-reel" / "kapak.png",
        [("Anmeldung'suz", 64, WHITE, True), ("banka açtın.", 64, WHITE, True), ("Sonra ne olur?", 40, GOLD, True)],
    )
    make_reel_cover(
        ROOT / "D-marka-usp" / "gun-04-eski-forum-vs" / "kapak.png",
        [("Eski forum", 64, WHITE, True), ("yetmiyor.", 64, WHITE, True), ("3 fark — GurbetDe", 36, GOLD, True)],
    )
    make_reel_cover(
        ROOT / "C-yasam-altyapisi" / "gun-07-konsolosluk" / "kapak.png",
        [("Randevu duyurusu", 56, WHITE, True), ("kaçtı mı?", 56, WHITE, True), ("Konsolosluk kanalı", 36, GOLD, True)],
    )
    make_reel_cover(
        ROOT / "C-yasam-altyapisi" / "gun-09-cta" / "kapak.png",
        [("Sorununu", 64, WHITE, True), ("Story'ye yazma.", 64, WHITE, True), ("gurbetde.com'a gel", 36, GOLD, True)],
    )


def main() -> None:
    gen_highlights()
    gen_p03()
    gen_p05()
    gen_p07()
    gen_p08()
    gen_p10()
    gen_reel_covers()
    print("done → content-group folders under", ROOT)


if __name__ == "__main__":
    main()
