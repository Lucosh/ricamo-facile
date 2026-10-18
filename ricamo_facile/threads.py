"""Thread colours: the Brother PEC palette and friendly colour names."""
from pyembroidery import EmbThread
from pyembroidery.EmbThreadPec import get_thread_set

# Brother PEC palette (index 0 is "unknown" and is skipped).
PEC_THREADS = [t for t in get_thread_set() if t is not None]

# Simple names shown to the user: (italian, english, rgb)
SIMPLE_COLORS = [
    ("Nero", "Black", (20, 20, 20)),
    ("Bianco", "White", (250, 250, 250)),
    ("Crema", "Cream", (245, 235, 205)),
    ("Grigio chiaro", "Light grey", (195, 195, 195)),
    ("Grigio", "Grey", (128, 128, 128)),
    ("Grigio scuro", "Dark grey", (70, 70, 70)),
    ("Rosso", "Red", (215, 35, 35)),
    ("Bordeaux", "Burgundy", (120, 15, 35)),
    ("Rosa", "Pink", (250, 160, 190)),
    ("Rosa antico", "Dusty pink", (200, 120, 130)),
    ("Fucsia", "Fuchsia", (215, 30, 135)),
    ("Arancione", "Orange", (250, 135, 20)),
    ("Pesca", "Peach", (250, 185, 140)),
    ("Giallo", "Yellow", (250, 220, 30)),
    ("Giallo chiaro", "Light yellow", (250, 240, 140)),
    ("Oro", "Gold", (205, 160, 40)),
    ("Beige", "Beige", (215, 190, 150)),
    ("Marrone chiaro", "Light brown", (175, 115, 60)),
    ("Marrone", "Brown", (115, 65, 30)),
    ("Marrone scuro", "Dark brown", (65, 35, 20)),
    ("Verde chiaro", "Light green", (150, 215, 95)),
    ("Verde", "Green", (40, 155, 50)),
    ("Verde scuro", "Dark green", (15, 85, 35)),
    ("Verde oliva", "Olive green", (120, 125, 40)),
    ("Turchese", "Turquoise", (20, 180, 175)),
    ("Azzurro", "Light blue", (110, 185, 240)),
    ("Blu", "Blue", (30, 75, 200)),
    ("Blu scuro", "Navy blue", (15, 25, 95)),
    ("Lilla", "Lilac", (200, 165, 230)),
    ("Viola", "Purple", (125, 50, 165)),
]


def _dist(a, b):
    # "redmean" perceptual approximation of colour distance
    rm = (a[0] + b[0]) / 2
    dr, dg, db = a[0] - b[0], a[1] - b[1], a[2] - b[2]
    return (2 + rm / 256) * dr * dr + 4 * dg * dg + (2 + (255 - rm) / 256) * db * db


def color_distance(a, b):
    return _dist(a, b)


def nearest_thread(rgb):
    """Returns the closest Brother thread (pyembroidery EmbThread)."""
    return min(PEC_THREADS, key=lambda t: _dist(rgb, (t.get_red(), t.get_green(), t.get_blue())))


def make_thread(rgb):
    """A thread with the exact colour, named after the closest Brother thread."""
    pec = nearest_thread(rgb)
    t = EmbThread()
    t.set_color(*[int(v) for v in rgb])
    t.description = pec.description
    t.catalog_number = pec.catalog_number
    t.brand = "Brother"
    return t


def thread_rgb(thread):
    return (thread.get_red(), thread.get_green(), thread.get_blue())


def simple_name(rgb, lang="it"):
    it, en, _ = min(SIMPLE_COLORS, key=lambda c: _dist(rgb, c[2]))
    return it if lang == "it" else en


def to_hex(rgb):
    return "#%02x%02x%02x" % tuple(int(v) for v in rgb)
