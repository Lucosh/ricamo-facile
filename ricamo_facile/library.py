"""The design catalogue: Windows colour emoji + procedurally drawn designs."""
import json
import os
import unicodedata

from PIL import Image, ImageDraw, ImageFont

from . import shapes

DATA_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data")

# (id, italian, english, icon)
CATEGORIES = [
    ("fiori", "Fiori e piante", "Flowers & plants", "\U0001F338"),
    ("cuori", "Cuori e amore", "Hearts & love", "❤️"),
    ("animali", "Animali", "Animals", "\U0001F431"),
    ("lettere", "Lettere e numeri", "Letters & numbers", "\U0001F524"),
    ("forme", "Stelle e forme", "Stars & shapes", "⭐"),
    ("mandala", "Mandala e cornici", "Mandalas & frames", "\U0001F3F5️"),
    ("feste", "Feste e giochi", "Parties & games", "\U0001F388"),
    ("cielo", "Cielo e stagioni", "Sky & seasons", "\U0001F308"),
    ("cibo", "Cibo e dolci", "Food & sweets", "\U0001F370"),
    ("faccine", "Faccine", "Smileys", "\U0001F60A"),
    ("persone", "Persone e mani", "People & hands", "\U0001F44B"),
    ("oggetti", "Casa e oggetti", "Home & objects", "\U0001F3E0"),
    ("viaggi", "Viaggi e luoghi", "Travel & places", "\U0001F697"),
    ("simboli", "Simboli", "Symbols", "☮️"),
]
CATEGORY_NAMES = {c[0]: (c[1], c[2]) for c in CATEGORIES}


def normalize(text):
    text = unicodedata.normalize("NFKD", text.lower())
    return "".join(ch for ch in text if not unicodedata.combining(ch))


class Item:
    __slots__ = ("id", "cat", "it", "en", "search", "kind", "fn", "char", "n_colors")

    def __init__(self, id, cat, it, en, kind, fn=None, char=None, keys="", n_colors=8):
        self.id, self.cat, self.it, self.en = id, cat, it, en
        self.kind, self.fn, self.char, self.n_colors = kind, fn, char, n_colors
        cat_it, cat_en = CATEGORY_NAMES[cat]
        self.search = normalize(" ".join((it, en, keys, cat_it, cat_en)))

    def name(self, lang):
        return self.it if lang == "it" else self.en

    def render(self, size, aa=False):
        if self.kind == "emoji":
            return render_emoji(self.char, size)
        return shapes.render(self.fn, size, aa)


_emoji_fonts = {}


def render_emoji(ch, size):
    """Draws a Windows colour emoji, cropped and centred on a square canvas."""
    fs = max(16, int(size * 0.9))
    font = _emoji_fonts.get(fs)
    if font is None:
        font = _emoji_fonts[fs] = ImageFont.truetype(shapes.EMOJI_FONT, fs)
    canvas = Image.new("RGBA", (int(fs * 1.6), int(fs * 1.6)), (0, 0, 0, 0))
    ImageDraw.Draw(canvas).text((fs * 0.2, fs * 0.2), ch, font=font, embedded_color=True)
    bbox = canvas.getchannel("A").getbbox()
    out = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    if bbox is None:
        return out
    glyph = canvas.crop(bbox)
    k = size * 0.96 / max(glyph.size)
    glyph = glyph.resize((max(1, round(glyph.width * k)), max(1, round(glyph.height * k))), Image.LANCZOS)
    out.alpha_composite(glyph, ((size - glyph.width) // 2, (size - glyph.height) // 2))
    return out


def _bind(fn, pal):
    return lambda d, S: fn(d, S, pal)


def _build():
    items = []
    P = shapes.PALETTES

    # ---- Windows colour emoji ------------------------------------------------
    if os.path.exists(shapes.EMOJI_FONT):
        with open(os.path.join(DATA_DIR, "emoji.json"), encoding="utf-8") as f:
            for e in json.load(f):
                items.append(Item("e%x" % ord(e["c"][0]), e["cat"], e["it"], e["en"], "emoji",
                                  char=e["c"], keys=e["k"], n_colors=8))

    # ---- hearts ------------------------------------------------------------------
    for key, it, en in shapes.HEARTS:
        fn = getattr(shapes, key)
        for p in P:
            items.append(Item("%s_%s" % (key, p.en), "cuori", "%s · %s" % (it, p.it), "%s · %s" % (en, p.en),
                              "shape", _bind(fn, p), keys="cuore amore heart love", n_colors=5))

    # ---- stars -------------------------------------------------------------------
    for n in (5, 6, 8):
        for style, s_it, s_en in shapes.STAR_STYLES:
            fn = shapes.make_star(n, style)
            for p in P:
                it = ("Stella a %d punte %s" % (n, s_it)).strip()
                en = ("%d-point star %s" % (n, s_en)).strip()
                items.append(Item("star%d%s_%s" % (n, style, p.en), "forme", "%s · %s" % (it, p.it),
                                  "%s · %s" % (en, p.en), "shape", _bind(fn, p), keys="stella star", n_colors=4))

    # ---- geometric shapes ---------------------------------------------------------
    for kind, it, en in shapes.GEOS:
        fn = shapes.make_geo(kind)
        for p in P:
            items.append(Item("geo%s_%s" % (kind, p.en), "forme", "%s · %s" % (it, p.it), "%s · %s" % (en, p.en),
                              "shape", _bind(fn, p), keys="forma geometria shape", n_colors=5))

    # ---- flowers -----------------------------------------------------------------
    combos = [(n, s, l) for s in ("round", "pointed") for n in (5, 6, 8, 12) for l in (1, 2)]
    combos += [(n, "heart", 1) for n in (4, 5, 6)]
    shape_names = {k: (a, b) for k, a, b in shapes.FLOWER_SHAPES}
    for n, s, l in combos:
        fn = shapes.make_flower(n, s, l)
        s_it, s_en = shape_names[s]
        for p in P:
            it = "Fiore %s%s, %d petali · %s" % ("doppio " if l == 2 else "", s_it, n, p.it)
            en = "%sFlower, %d %s · %s" % ("Double " if l == 2 else "", n, s_en, p.en)
            items.append(Item("flower%d%s%d_%s" % (n, s, l, p.en), "fiori", it, en, "shape", _bind(fn, p),
                              keys="fiore margherita flower daisy", n_colors=4))

    # ---- leaves ------------------------------------------------------------------
    leaf_pals = [P[5], P[6], P[3], P[4], P[11]]
    for style in range(3):
        fn = shapes.make_leaf(style)
        for p in leaf_pals:
            it = ("Foglia" if style == 0 else "Ramo di foglie") + " · " + p.it
            en = ("Leaf" if style == 0 else "Leafy branch") + " · " + p.en
            items.append(Item("leaf%d_%s" % (style, p.en), "fiori", it, en, "shape", _bind(fn, p),
                              keys="foglia autunno leaf autumn", n_colors=3))

    # ---- mandalas ----------------------------------------------------------------
    i = 0
    for n1 in (8, 12, 16):
        for n2 in (6, 8, 12):
            for variant in range(4):
                fn = shapes.make_mandala(n1, n2, n1, variant)
                for j in range(6):
                    p = P[(i + j * 2) % len(P)]
                    items.append(Item("mandala%d_%d_%d_%s" % (n1, n2, variant, p.en), "mandala",
                                      "Mandala n. %d · %s" % (i + 1, p.it), "Mandala no. %d · %s" % (i + 1, p.en),
                                      "shape", _bind(fn, p), keys="mandala rosone decoro", n_colors=5))
                i += 1

    # ---- frames ------------------------------------------------------------------
    for kind, it, en in shapes.FRAMES:
        fn = shapes.make_frame(kind)
        for p in P:
            items.append(Item("frame%s_%s" % (kind, p.en), "mandala", "%s · %s" % (it, p.it), "%s · %s" % (en, p.en),
                              "shape", _bind(fn, p), keys="cornice bordo frame border", n_colors=4))

    # ---- snowflakes --------------------------------------------------------------
    snow_pals = [P[7], P[8], P[6], P[10], P[9]]
    k = 0
    for branches in (1, 2, 3):
        for tips in range(4):
            fn = shapes.make_snowflake(branches, tips)
            k += 1
            for p in snow_pals:
                items.append(Item("snow%d%d_%s" % (branches, tips, p.en), "cielo",
                                  "Fiocco di neve n. %d · %s" % (k, p.it), "Snowflake no. %d · %s" % (k, p.en),
                                  "shape", _bind(fn, p), keys="neve inverno natale snow winter christmas", n_colors=2))

    # ---- butterflies -------------------------------------------------------------
    for style in range(2):
        fn = shapes.make_butterfly(style)
        for p in P:
            items.append(Item("butterfly%d_%s" % (style, p.en), "animali",
                              "Farfalla %s · %s" % ("classica" if style == 0 else "a pois", p.it),
                              "%s butterfly · %s" % ("Classic" if style == 0 else "Polka dot", p.en),
                              "shape", _bind(fn, p), keys="farfalla butterfly", n_colors=5))

    # ---- letters and numbers -----------------------------------------------------
    fonts = shapes.available_fonts()
    letters = [chr(c) for c in range(ord("A"), ord("Z") + 1)]
    for li, ch in enumerate(letters):
        for fi, (ffile, f_it, f_en) in enumerate(fonts):
            for frame, fr_it, fr_en in shapes.LETTER_FRAMES:
                p = P[(li + fi) % len(P)]
                fn = shapes.make_letter(ch, ffile, frame)
                it = ("Lettera %s %s · %s" % (ch, fr_it, f_it)).replace("  ", " ")
                en = ("Letter %s %s · %s" % (ch, fr_en, f_en)).replace("  ", " ")
                items.append(Item("letter%s_%d_%s" % (ch, fi, frame), "lettere", it, en, "shape", _bind(fn, p),
                                  keys="lettera iniziale monogramma letter initial monogram " + ch.lower(), n_colors=3))
    for d in "0123456789":
        for fi, (ffile, f_it, f_en) in enumerate(fonts):
            p = P[(int(d) + fi) % len(P)]
            fn = shapes.make_letter(d, ffile, "none")
            items.append(Item("number%s_%d" % (d, fi), "lettere", "Numero %s · %s" % (d, f_it),
                              "Number %s · %s" % (d, f_en), "shape", _bind(fn, p),
                              keys="numero cifra number digit " + d, n_colors=2))
    return items


class Library:
    def __init__(self):
        self.items = _build()
        self.by_cat = {}
        for it in self.items:
            self.by_cat.setdefault(it.cat, []).append(it)

    def __len__(self):
        return len(self.items)

    def category(self, cat):
        return self.by_cat.get(cat, [])

    def search(self, query):
        words = normalize(query).split()
        if not words:
            return []
        return [it for it in self.items if all(w in it.search for w in words)]
