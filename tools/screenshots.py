"""Opens every screen of the app and saves screenshots (used for the README).

Usage: python tools/screenshots.py OUTPUT_DIR [it|en]
"""
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))

from PIL import ImageGrab  # noqa: E402

from ricamo_facile import app as A  # noqa: E402

out = sys.argv[1]
lang = sys.argv[2] if len(sys.argv) > 2 else "it"
os.makedirs(out, exist_ok=True)
app = A.App()
app.t.lang = lang
app.root.state("normal")
app.root.geometry("%dx%d+0+0" % (app.px(1200), app.px(740)))
steps = []


def shot(name):
    def f():
        app.root.update()
        r = app.root
        x, y = r.winfo_rootx(), r.winfo_rooty()
        ImageGrab.grab((x, y - 0, x + r.winfo_width(), y + r.winfo_height()), all_screens=True).save(
            os.path.join(out, "%s_%s.png" % (name, lang)))
    return f


def wait_design(next_step):
    def f():
        s = app.screen
        if getattr(s, "design", None) is None:
            app.root.after(200, f)
        else:
            app.root.after(300, next_step)
    return f


def run(i=0):
    if i >= len(steps):
        app.root.destroy()
        return
    delay, fn = steps[i]
    res = fn()
    if res == "wait":
        app.root.after(200, wait_design(lambda: run(i + 1)))
    else:
        app.root.after(delay, lambda: run(i + 1))


emoji_item = next(it for it in app.library.items if it.char == "\U0001F431")
flower = next(it for it in app.library.items if it.id.startswith("flower5round2_red"))
steps = [
    (800, lambda: app.show(A.HomeScreen)),
    (300, shot("01_home")),
    (600, lambda: app.show(A.CategoriesScreen)),
    (300, shot("02_categories")),
    (900, lambda: app.show(A.GridScreen, cat="fiori")),
    (300, shot("03_catalog")),
    (100, lambda: app.screen.open(emoji_item) or "wait"),
    (300, shot("04_editor_emoji")),
    (100, lambda: app.show(A.EditorScreen, job=A.Job("Fiore", flower.render(1000), False, A.HomeScreen, n_colors=4)) or "wait"),
    (300, shot("05_editor_flower")),
    (600, lambda: app.show(A.TextScreen)),
    (300, shot("06_text")),
    (100, lambda: app.screen.next() or "wait"),
    (300, shot("07_editor_text")),
    (600, lambda: app.show(A.PhotoScreen)),
    (300, shot("08_photo")),
    (300, lambda: app.show_help()),
    (300, shot("09_help")),
]
app.root.after(500, run)
app.run()
