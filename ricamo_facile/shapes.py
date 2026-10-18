"""Procedurally drawn designs: hearts, stars, flowers, mandalas, snowflakes...

Every design is a function f(draw, S, pal) that draws on a transparent S x S
canvas. `pal` is a Palette (main, light, dark, accent colours).
"""
import math
import os
from collections import namedtuple

from PIL import Image, ImageDraw, ImageFont

Palette = namedtuple("Palette", "it en main light dark accent")

PALETTES = [
    Palette("rosso", "red", (210, 30, 45), (245, 125, 135), (125, 10, 25), (250, 200, 40)),
    Palette("rosa", "pink", (240, 120, 170), (252, 195, 218), (185, 45, 105), (250, 200, 40)),
    Palette("fucsia", "fuchsia", (210, 30, 135), (240, 140, 200), (130, 10, 80), (250, 200, 40)),
    Palette("arancione", "orange", (245, 130, 30), (252, 195, 120), (180, 75, 10), (120, 60, 20)),
    Palette("giallo", "yellow", (250, 205, 30), (253, 235, 150), (200, 140, 0), (130, 75, 25)),
    Palette("verde", "green", (50, 150, 60), (150, 210, 110), (20, 90, 35), (250, 200, 40)),
    Palette("turchese", "turquoise", (20, 170, 170), (135, 215, 210), (5, 105, 110), (250, 200, 40)),
    Palette("azzurro", "light blue", (90, 170, 235), (175, 218, 250), (30, 95, 180), (250, 200, 40)),
    Palette("blu", "blue", (35, 70, 180), (115, 150, 228), (15, 30, 100), (250, 200, 40)),
    Palette("viola", "purple", (125, 55, 170), (192, 148, 226), (72, 20, 108), (250, 200, 40)),
    Palette("lilla", "lilac", (185, 150, 220), (228, 210, 246), (115, 75, 160), (250, 200, 40)),
    Palette("bordeaux", "burgundy", (125, 20, 45), (195, 85, 105), (65, 5, 20), (250, 200, 40)),
]
WHITE = (250, 250, 250)
GREEN = (60, 145, 60)
DARK_GREEN = (25, 95, 40)

FONT_DIR = os.path.join(os.environ.get("WINDIR", r"C:\Windows"), "Fonts")
EMOJI_FONT = os.path.join(FONT_DIR, "seguiemj.ttf")

# (file, italian, english)
LETTER_FONTS = [
    ("segoescb.ttf", "Corsivo", "Script"),
    ("MTCORSVA.TTF", "Calligrafico", "Calligraphy"),
    ("georgiab.ttf", "Classico", "Classic"),
    ("ariblk.ttf", "Stampatello", "Block letters"),
    ("Gabriola.ttf", "Elegante", "Elegant"),
    ("comicbd.ttf", "Allegro", "Playful"),
]


def available_fonts():
    return [f for f in LETTER_FONTS if os.path.exists(os.path.join(FONT_DIR, f[0]))]


# --------------------------------------------------------------------------
# geometry helpers
# --------------------------------------------------------------------------

def rot(x, y, a):
    c, s = math.cos(a), math.sin(a)
    return x * c - y * s, x * s + y * c


def heart_pts(cx, cy, r, a=0.0, n=160):
    pts = []
    for i in range(n):
        t = 2 * math.pi * i / n
        x = 16 * math.sin(t) ** 3
        y = -(13 * math.cos(t) - 5 * math.cos(2 * t) - 2 * math.cos(3 * t) - math.cos(4 * t)) + 2.5
        x, y = rot(x * r / 16.5, y * r / 16.5, a)
        pts.append((cx + x, cy + y))
    return pts


def star_pts(cx, cy, R, r, n, a=-math.pi / 2):
    pts = []
    for i in range(2 * n):
        rr = R if i % 2 == 0 else r
        t = a + math.pi * i / n
        pts.append((cx + rr * math.cos(t), cy + rr * math.sin(t)))
    return pts


def poly_pts(cx, cy, R, n, a=-math.pi / 2):
    return [(cx + R * math.cos(a + 2 * math.pi * i / n), cy + R * math.sin(a + 2 * math.pi * i / n)) for i in range(n)]


def ellipse_pts(cx, cy, a, b, angle, n=90):
    pts = []
    for i in range(n):
        t = 2 * math.pi * i / n
        x, y = rot(a * math.cos(t), b * math.sin(t), angle)
        pts.append((cx + x, cy + y))
    return pts


def petal_pts(cx, cy, r0, r1, width, a, pointed=False, n=40):
    """A petal from radius r0 to r1 along angle a."""
    pts = []
    L = r1 - r0
    for side in (1, -1):
        rng = range(n + 1) if side == 1 else range(n, -1, -1)
        for i in rng:
            t = i / n
            w = math.sin(math.pi * t) ** (1.0 if pointed else 0.5) * width / 2
            if pointed:
                w *= (1 - 0.35 * t)
            x, y = rot(r0 + L * t, side * w, a)
            pts.append((cx + x, cy + y))
    return pts


def ring(d, cx, cy, R, w, fill):
    d.ellipse((cx - R, cy - R, cx + R, cy + R), outline=fill, width=int(w))


def circle(d, cx, cy, R, fill):
    d.ellipse((cx - R, cy - R, cx + R, cy + R), fill=fill)


# --------------------------------------------------------------------------
# designs
# --------------------------------------------------------------------------

def heart_full(d, S, p):
    d.polygon(heart_pts(S / 2, S / 2, S * 0.45), fill=p.main)


def heart_double(d, S, p):
    d.polygon(heart_pts(S / 2, S / 2, S * 0.45), fill=p.main)
    d.polygon(heart_pts(S / 2, S / 2, S * 0.27), fill=p.light)


def heart_outline(d, S, p):
    d.polygon(heart_pts(S / 2, S / 2, S * 0.45), fill=p.main)
    d.polygon(heart_pts(S / 2, S / 2, S * 0.36), fill=(0, 0, 0, 0))


def heart_three(d, S, p):
    d.polygon(heart_pts(S * 0.30, S * 0.36, S * 0.22, -0.3), fill=p.light)
    d.polygon(heart_pts(S * 0.70, S * 0.36, S * 0.22, 0.3), fill=p.dark)
    d.polygon(heart_pts(S * 0.50, S * 0.62, S * 0.30), fill=p.main)


def heart_clover(d, S, p):
    for k in range(4):
        a = k * math.pi / 2
        x, y = rot(0, -S * 0.2, a)
        d.polygon(heart_pts(S / 2 + x, S / 2 + y, S * 0.2, a + math.pi), fill=p.main)
    d.line((S * 0.5, S * 0.55, S * 0.62, S * 0.95), fill=DARK_GREEN, width=int(S * 0.04))


def heart_flower(d, S, p):
    d.polygon(heart_pts(S / 2, S / 2, S * 0.45), fill=p.main)
    cx, cy = S / 2, S * 0.47
    for k in range(5):
        d.polygon(petal_pts(cx, cy, S * 0.02, S * 0.17, S * 0.12, k * 2 * math.pi / 5 - math.pi / 2), fill=WHITE)
    circle(d, cx, cy, S * 0.05, p.accent)


HEARTS = [
    ("heart_full", "Cuore", "Heart"),
    ("heart_double", "Cuore doppio", "Double heart"),
    ("heart_outline", "Cuore vuoto", "Open heart"),
    ("heart_three", "Tre cuori", "Three hearts"),
    ("heart_clover", "Quadrifoglio di cuori", "Heart clover"),
    ("heart_flower", "Cuore con fiore", "Heart with flower"),
]


def make_star(points, style):
    def f(d, S, p):
        R, r = S * 0.48, S * 0.48 * (0.42 if points <= 6 else 0.55)
        d.polygon(star_pts(S / 2, S / 2, R, r, points), fill=p.main)
        if style == "two":
            d.polygon(star_pts(S / 2, S / 2, R * 0.55, r * 0.55, points), fill=p.light)
        elif style == "open":
            d.polygon(star_pts(S / 2, S / 2, R * 0.62, r * 0.62, points), fill=(0, 0, 0, 0))
        elif style == "dot":
            circle(d, S / 2, S / 2, r * 0.5, p.accent)
    return f


STAR_STYLES = [("full", "", ""), ("two", "bicolore", "two-tone"), ("open", "vuota", "open"), ("dot", "con punto", "with dot")]


def make_flower(petals, shape, layers):
    def f(d, S, p):
        cx = cy = S / 2
        R = S * 0.48
        width = 2 * math.pi * R / petals * (0.9 if shape != "pointed" else 0.75)
        width = min(width, R * 0.9)
        cols = [p.main, p.light] if layers == 2 else [p.main]
        for li, col in enumerate(cols):
            rr = R * (1 - 0.32 * li)
            ww = width * (1 - 0.3 * li)
            off = (math.pi / petals) * li
            for k in range(petals):
                a = off + 2 * math.pi * k / petals - math.pi / 2
                if shape == "round":
                    d.polygon(petal_pts(cx, cy, R * 0.05, rr, ww, a), fill=col)
                elif shape == "pointed":
                    d.polygon(petal_pts(cx, cy, R * 0.05, rr, ww, a, pointed=True), fill=col)
                else:  # heart shaped petals
                    x, y = rot(rr * 0.55, 0, a)
                    d.polygon(heart_pts(cx + x, cy + y, rr * 0.45, a + math.pi / 2), fill=col)
        circle(d, cx, cy, R * 0.2, p.accent)
    return f


FLOWER_SHAPES = [("round", "petali tondi", "round petals"), ("pointed", "petali a punta", "pointed petals"),
                 ("heart", "petali a cuore", "heart petals")]


def make_mandala(n1, n2, n3, variant):
    def f(d, S, p):
        cx = cy = S / 2
        R = S * 0.48
        # outer petals
        for k in range(n1):
            a = 2 * math.pi * k / n1
            d.polygon(petal_pts(cx, cy, R * 0.45, R, 2 * math.pi * R * 0.75 / n1 * 0.9, a, pointed=variant % 2 == 0), fill=p.dark)
        circle(d, cx, cy, R * 0.66, p.light)
        for k in range(n2):
            a = 2 * math.pi * k / n2 + math.pi / n2
            d.polygon(petal_pts(cx, cy, R * 0.2, R * 0.64, 2 * math.pi * R * 0.45 / n2, a, pointed=variant % 3 == 0), fill=p.main)
        circle(d, cx, cy, R * 0.26, p.accent if variant % 2 else p.dark)
        if variant >= 2:
            for k in range(n3):
                a = 2 * math.pi * k / n3
                x, y = rot(R * 0.82, 0, a)
                circle(d, cx + x, cy + y, R * 0.05, p.light)
        circle(d, cx, cy, R * 0.12, p.light if variant % 2 else p.accent)
    return f


def make_snowflake(branches, tips):
    def f(d, S, p):
        cx = cy = S / 2
        R = S * 0.48
        w = int(S * 0.045)
        col = p.main
        for k in range(6):
            a = k * math.pi / 3 - math.pi / 2
            x, y = rot(R * 0.95, 0, a)
            d.line((cx, cy, cx + x, cy + y), fill=col, width=w)
            for b in range(branches):
                t = 0.35 + 0.5 * b / max(1, branches)
                bl = R * (0.32 - 0.08 * b)
                for side in (1, -1):
                    bx, by = rot(R * t, 0, a)
                    ex, ey = rot(R * t + bl * 0.7, side * bl * 0.7, a)
                    d.line((cx + bx, cy + by, cx + ex, cy + ey), fill=col, width=w)
            ex, ey = rot(R * 0.92, 0, a)
            if tips == 1:
                circle(d, cx + ex, cy + ey, R * 0.07, col)
            elif tips == 2:
                d.polygon(star_pts(cx + ex, cy + ey, R * 0.1, R * 0.05, 4, a), fill=col)
        d.polygon(poly_pts(cx, cy, R * 0.18, 6), fill=col)
        if tips == 3:
            d.polygon(poly_pts(cx, cy, R * 0.09, 6), fill=(0, 0, 0, 0))
    return f


def make_butterfly(style):
    def f(d, S, p):
        cx, cy = S / 2, S / 2
        for side in (1, -1):
            d.polygon(ellipse_pts(cx + side * S * 0.23, cy - S * 0.15, S * 0.25, S * 0.18, side * -0.55), fill=p.main)
            d.polygon(ellipse_pts(cx + side * S * 0.17, cy + S * 0.17, S * 0.17, S * 0.13, side * 0.6),
                      fill=p.dark if style == 0 else p.light)
            circle(d, cx + side * S * 0.27, cy - S * 0.18, S * 0.08, p.light if style == 0 else p.accent)
            if style == 1:
                circle(d, cx + side * S * 0.18, cy + S * 0.19, S * 0.05, p.dark)
        d.ellipse((cx - S * 0.035, cy - S * 0.25, cx + S * 0.035, cy + S * 0.3), fill=(70, 45, 30))
        for side in (1, -1):
            d.line((cx, cy - S * 0.24, cx + side * S * 0.12, cy - S * 0.42), fill=(70, 45, 30), width=int(S * 0.018))
    return f


def make_leaf(style):
    def f(d, S, p):
        cx = S / 2
        col, vein = (p.main, p.dark) if style != 2 else (p.light, p.main)
        if style == 0:
            d.polygon(petal_pts(S * 0.08, S * 0.92, 0, S * 1.15, S * 0.5, -math.pi / 4, pointed=True), fill=col)
            d.line((S * 0.08, S * 0.92, S * 0.75, S * 0.25), fill=vein, width=int(S * 0.025))
        else:
            for k in range(-2, 3):
                a = -math.pi / 2 + k * 0.42
                d.polygon(petal_pts(cx, S * 0.9, S * 0.1, S * (0.85 - 0.08 * abs(k)), S * 0.2, a, pointed=True), fill=col)
            d.line((cx, S * 0.98, cx, S * 0.5), fill=vein, width=int(S * 0.03))
    return f


def make_frame(kind):
    def f(d, S, p):
        cx = cy = S / 2
        R = S * 0.47
        w = S * 0.06
        if kind == "circle":
            ring(d, cx, cy, R, w, p.main)
            ring(d, cx, cy, R * 0.82, w * 0.4, p.light)
        elif kind == "square":
            d.rounded_rectangle((S * 0.04, S * 0.04, S * 0.96, S * 0.96), radius=S * 0.08, outline=p.main, width=int(w))
            d.rounded_rectangle((S * 0.13, S * 0.13, S * 0.87, S * 0.87), radius=S * 0.05, outline=p.light, width=int(w * 0.4))
        elif kind == "scallop":
            n = 16
            for k in range(n):
                x, y = rot(R * 0.88, 0, 2 * math.pi * k / n)
                circle(d, cx + x, cy + y, R * 0.13, p.main)
            circle(d, cx, cy, R * 0.8, (0, 0, 0, 0))
            ring(d, cx, cy, R * 0.72, w * 0.4, p.light)
        elif kind == "wreath":
            n = 18
            for k in range(n):
                a = 2 * math.pi * k / n
                x, y = rot(R * 0.85, 0, a)
                d.polygon(petal_pts(cx + x, cy + y, 0, R * 0.25, R * 0.12, a + math.pi / 2 + 0.6, pointed=True), fill=GREEN)
            for k in range(6):
                x, y = rot(R * 0.85, 0, 2 * math.pi * k / 6 + 0.2)
                circle(d, cx + x, cy + y, R * 0.09, p.main)
    return f


FRAMES = [("circle", "Cornice rotonda", "Round frame"), ("square", "Cornice quadrata", "Square frame"),
          ("scallop", "Cornice smerlata", "Scalloped frame"), ("wreath", "Ghirlanda", "Wreath")]


def make_geo(kind):
    def f(d, S, p):
        cx = cy = S / 2
        R = S * 0.48
        if kind == "hexagon":
            d.polygon(poly_pts(cx, cy, R, 6, 0), fill=p.main)
            d.polygon(poly_pts(cx, cy, R * 0.6, 6, 0), fill=p.light)
            d.polygon(poly_pts(cx, cy, R * 0.25, 6, 0), fill=p.dark)
        elif kind == "circles":
            circle(d, cx, cy, R, p.dark)
            circle(d, cx, cy, R * 0.72, p.main)
            circle(d, cx, cy, R * 0.44, p.light)
            circle(d, cx, cy, R * 0.18, p.accent)
        elif kind == "diamond":
            d.polygon(poly_pts(cx, cy, R, 4), fill=p.main)
            d.polygon(poly_pts(cx, cy, R * 0.55, 4), fill=p.light)
        elif kind == "moon":
            circle(d, cx, cy, R, p.main)
            circle(d, cx + R * 0.45, cy - R * 0.2, R * 0.85, (0, 0, 0, 0))
        elif kind == "drop":
            pts = []
            for i in range(120):
                t = 2 * math.pi * i / 120
                pts.append((cx + R * 0.62 * math.sin(t) * math.sin(t / 2), cy - R * math.cos(t)))
            d.polygon(pts, fill=p.main)
        elif kind == "sun":
            for k in range(12):
                a = 2 * math.pi * k / 12
                d.polygon(petal_pts(cx, cy, R * 0.45, R, R * 0.3, a, pointed=True), fill=p.dark)
            circle(d, cx, cy, R * 0.55, p.main)
        elif kind == "cloud":
            for x, y, r in ((0.32, 0.58, 0.18), (0.5, 0.45, 0.24), (0.7, 0.56, 0.18), (0.5, 0.62, 0.17)):
                circle(d, S * x, S * y, S * r, p.main)
        elif kind == "dots":
            for k in range(8):
                x, y = rot(R * 0.75, 0, 2 * math.pi * k / 8)
                circle(d, cx + x, cy + y, R * 0.2, p.main if k % 2 else p.light)
            circle(d, cx, cy, R * 0.3, p.dark)
    return f


GEOS = [("hexagon", "Esagono", "Hexagon"), ("circles", "Cerchi", "Circles"), ("diamond", "Rombo", "Diamond"),
        ("moon", "Luna", "Moon"), ("drop", "Goccia", "Drop"), ("sun", "Sole", "Sun"),
        ("cloud", "Nuvola", "Cloud"), ("dots", "Pallini", "Dots")]


# --------------------------------------------------------------------------
# letters
# --------------------------------------------------------------------------

_font_cache = {}


def _font(file, size):
    key = (file, size)
    if key not in _font_cache:
        _font_cache[key] = ImageFont.truetype(os.path.join(FONT_DIR, file), size)
    return _font_cache[key]


def draw_text_centered(img, text, font_file, color, box):
    """Draws `text` as large as possible inside box=(x0, y0, x1, y1)."""
    x0, y0, x1, y1 = box
    bw, bh = x1 - x0, y1 - y0
    size = int(bh)
    for _ in range(3):
        font = _font(font_file, max(8, size))
        l, t, r, b = font.getbbox(text)
        tw, th = r - l, b - t
        if tw <= 0 or th <= 0:
            return
        k = min(bw / tw, bh / th)
        size = int(size * k * 0.98)
    font = _font(font_file, max(8, size))
    l, t, r, b = font.getbbox(text)
    ImageDraw.Draw(img).text((x0 + (bw - (r - l)) / 2 - l, y0 + (bh - (b - t)) / 2 - t), text, font=font, fill=color)


def make_letter(ch, font_file, frame):
    def f(d, S, p):
        img = d._image
        if frame == "none":
            draw_text_centered(img, ch, font_file, p.main, (S * 0.06, S * 0.06, S * 0.94, S * 0.94))
        elif frame == "circle":
            ring(d, S / 2, S / 2, S * 0.47, S * 0.05, p.main)
            draw_text_centered(img, ch, font_file, p.dark, (S * 0.25, S * 0.22, S * 0.75, S * 0.78))
        elif frame == "heart":
            d.polygon(heart_pts(S / 2, S / 2, S * 0.47), fill=p.light)
            draw_text_centered(img, ch, font_file, p.dark, (S * 0.3, S * 0.25, S * 0.7, S * 0.68))
    return f


LETTER_FRAMES = [("none", "", ""), ("circle", "nel cerchio", "in a circle"), ("heart", "nel cuore", "in a heart")]


def render_text(text, font_file, color, height=400):
    """Renders a name/word on a transparent image."""
    font = _font(font_file, height)
    l, t, r, b = font.getbbox(text)
    img = Image.new("RGBA", (r - l + 40, b - t + 40), (0, 0, 0, 0))
    ImageDraw.Draw(img).text((20 - l, 20 - t), text, font=font, fill=color)
    return img


def render(fn, size, aa=False):
    """Draws a design function on a transparent square image."""
    ss = 3 if aa else 1
    S = size * ss
    img = Image.new("RGBA", (S, S), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    fn(d, S)
    if ss > 1:
        img = img.resize((size, size), Image.LANCZOS)
    return img
