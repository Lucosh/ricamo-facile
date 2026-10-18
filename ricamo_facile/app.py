"""Ricamo Facile - the window, screens and widgets (tkinter)."""
import ctypes
import json
import os
import queue
import string
import sys
import threading
import traceback
import unicodedata
from collections import OrderedDict

import tkinter as tk
from tkinter import filedialog

from PIL import Image, ImageOps, ImageTk

from . import shapes
from .converter import convert
from .i18n import Translator
from .library import CATEGORIES, CATEGORY_NAMES, Library, render_emoji
from .threads import simple_name, to_hex

C = {
    "bg": "#FFF7EF",
    "card": "#FFFFFF",
    "primary": "#B4245D",
    "primary_dark": "#8A1546",
    "primary_light": "#FBE3EC",
    "green": "#2E7D32",
    "green_dark": "#1B5E20",
    "text": "#2A2A2A",
    "muted": "#5F5F5F",
    "border": "#E6D5C6",
    "fabric": "#F6F1E8",
    "top": "#FFFFFF",
}
FONT = "Segoe UI"
APP_DIR = os.path.join(os.environ.get("APPDATA", os.path.expanduser("~")), "RicamoFacile")
SETTINGS_FILE = os.path.join(APP_DIR, "settings.json")
LOG_FILE = os.path.join(APP_DIR, "errori.log")
IMAGE_TYPES = "*.jpg *.jpeg *.png *.bmp *.gif *.webp *.tif *.tiff"


# --------------------------------------------------------------------------
# helpers
# --------------------------------------------------------------------------

def load_settings():
    try:
        with open(SETTINGS_FILE, encoding="utf-8") as f:
            return json.load(f)
    except (OSError, ValueError):
        return {}


def save_settings(data):
    try:
        os.makedirs(APP_DIR, exist_ok=True)
        with open(SETTINGS_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f)
    except OSError:
        pass


def log_error(text):
    try:
        os.makedirs(APP_DIR, exist_ok=True)
        with open(LOG_FILE, "a", encoding="utf-8") as f:
            f.write(text + "\n")
    except OSError:
        pass


def usb_drives():
    """Letters of the removable drives currently plugged in, e.g. ['E:\\']."""
    if sys.platform != "win32":
        return []
    k32 = ctypes.windll.kernel32
    old = k32.SetErrorMode(1)  # no "insert a disk" pop-ups
    try:
        mask = k32.GetLogicalDrives()
        drives = []
        for i, letter in enumerate(string.ascii_uppercase):
            if mask >> i & 1 and letter not in "AB":
                root = letter + ":\\"
                if k32.GetDriveTypeW(root) == 2 and os.path.isdir(root):
                    drives.append(root)
        return drives
    finally:
        k32.SetErrorMode(old)


def safe_filename(name):
    name = unicodedata.normalize("NFKD", name)
    name = "".join(ch for ch in name if ch.isascii() and (ch.isalnum() or ch in " -_"))
    name = "_".join(name.split())[:24].strip("_-")
    return name or "ricamo"


def unique_path(folder, base):
    path = os.path.join(folder, base + ".pes")
    n = 2
    while os.path.exists(path):
        path = os.path.join(folder, "%s_%d.pes" % (base, n))
        n += 1
    return path


def known_folder(name):
    home = os.path.expanduser("~")
    for cand in (os.path.join(home, name), os.path.join(home, "OneDrive", name)):
        if os.path.isdir(cand):
            return cand
    return home


def short(text, n=44):
    return text if len(text) <= n else text[:n - 1].rstrip() + "…"


# --------------------------------------------------------------------------
# widgets
# --------------------------------------------------------------------------

BUTTON_KINDS = {
    "primary": ("primary", "primary_dark", "#FFFFFF"),
    "green": ("green", "green_dark", "#FFFFFF"),
    "light": ("card", "primary_light", "primary"),
}


def make_button(parent, text, command, kind="primary", size=16, image=None, padx=22, pady=10, **kw):
    bg_key, act_key, fg_key = BUTTON_KINDS[kind]
    bg, act = C[bg_key], C[act_key]
    fg = C.get(fg_key, fg_key)
    wrap = tk.Frame(parent, bg=C["primary"] if kind == "light" else bg, padx=2, pady=2)
    b = tk.Button(wrap, text=text, command=command, bg=bg, fg=fg, activebackground=act, activeforeground=fg,
                  font=(FONT, size, "bold"), relief="flat", bd=0, cursor="hand2", padx=padx, pady=pady,
                  image=image, compound="left" if image else None, **kw)
    b.pack(fill="both", expand=True)
    b.bind("<Enter>", lambda e: b.config(bg=act))
    b.bind("<Leave>", lambda e: b.config(bg=bg))
    wrap.button = b
    return wrap


class ToggleGroup(tk.Frame):
    """A row of big buttons where exactly one is selected."""

    def __init__(self, parent, options, value, on_change, size=14):
        super().__init__(parent, bg=parent["bg"])
        self.on_change = on_change
        self.value = value
        self.buttons = {}
        for i, (v, text) in enumerate(options):
            wrap = tk.Frame(self, padx=3, pady=3)
            btn = tk.Button(wrap, text=text, font=(FONT, size, "bold"), relief="flat", bd=0, cursor="hand2",
                            pady=8, command=lambda v=v: self.select(v))
            btn.pack(fill="both", expand=True)
            wrap.grid(row=0, column=i, sticky="nsew", padx=(0, 8))
            self.columnconfigure(i, weight=1, uniform="t")
            self.buttons[v] = (wrap, btn)
        self._paint()

    def select(self, v):
        if v != self.value:
            self.value = v
            self._paint()
            self.on_change(v)

    def _paint(self):
        for v, (wrap, btn) in self.buttons.items():
            if v == self.value:
                wrap.config(bg=C["primary"])
                btn.config(bg=C["primary"], fg="white", activebackground=C["primary_dark"], activeforeground="white")
            else:
                wrap.config(bg=C["border"])
                btn.config(bg=C["card"], fg=C["text"], activebackground=C["primary_light"], activeforeground=C["text"])


class Scrollable(tk.Frame):
    """A vertically scrollable frame (mouse wheel works when the pointer is over it)."""

    def __init__(self, parent, bg):
        super().__init__(parent, bg=bg)
        self.canvas = tk.Canvas(self, bg=bg, highlightthickness=0, bd=0)
        self.bar = tk.Scrollbar(self, orient="vertical", command=self.canvas.yview, width=18)
        self.inner = tk.Frame(self.canvas, bg=bg)
        self._win = self.canvas.create_window(0, 0, window=self.inner, anchor="nw")
        self.canvas.configure(yscrollcommand=self.bar.set)
        self.canvas.pack(side="left", fill="both", expand=True)
        self.bar.pack(side="right", fill="y")
        self.inner.bind("<Configure>", lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all")))
        self.canvas.bind("<Configure>", lambda e: self.canvas.itemconfigure(self._win, width=e.width))

    def wheel(self, event):
        if self.inner.winfo_height() > self.canvas.winfo_height():
            self.canvas.yview_scroll(int(-event.delta / 120) * 3, "units")


def on_mouse_wheel(event):
    w = event.widget
    while w is not None and not isinstance(w, str):
        if isinstance(w, Scrollable):
            w.wheel(event)
            return
        w = getattr(w, "master", None)


def clickable(widget, command, hover_target=None, normal=None, hover=None):
    """Makes a frame and all its children react to clicks (and hover)."""
    def bind(w):
        w.bind("<Button-1>", lambda e: command())
        w.configure(cursor="hand2")
        if hover_target is not None:
            w.bind("<Enter>", lambda e: hover_target.config(bg=hover), add="+")
            w.bind("<Leave>", lambda e: hover_target.config(bg=normal), add="+")
        for child in w.winfo_children():
            bind(child)
    bind(widget)


# --------------------------------------------------------------------------
# application
# --------------------------------------------------------------------------

class Job:
    """What is being turned into embroidery, plus the user's choices."""

    def __init__(self, name, image, photo, back, back_kwargs=None, n_colors=8, size="medium"):
        self.name = name
        self.image = image
        self.photo = photo
        self.back = back
        self.back_kwargs = back_kwargs or {}
        self.n_colors = n_colors
        self.size = size
        self.remove_bg = True
        self.cache = {}

    def key(self):
        return (self.size, self.n_colors, self.remove_bg)


class App:
    def __init__(self):
        if sys.platform == "win32":
            try:
                ctypes.windll.shcore.SetProcessDpiAwareness(1)
            except (AttributeError, OSError):
                pass
        self.root = tk.Tk()
        self.root.withdraw()
        self.scale = max(1.0, self.root.winfo_fpixels("1i") / 96)
        self.settings = load_settings()
        self.t = Translator(self.settings.get("lang", "it"))
        self.library = Library()
        self._emoji_cache = {}
        self._thumb_cache = OrderedDict()
        self.root.report_callback_exception = self._on_error
        self.root.bind_all("<MouseWheel>", on_mouse_wheel)

        self.root.title(self.t("app_title"))
        self.root.configure(bg=C["bg"])
        sw, sh = self.root.winfo_screenwidth(), self.root.winfo_screenheight()
        self.root.geometry("%dx%d+%d+%d" % (min(sw, self.px(1280)), min(sh - 80, self.px(820)), 20, 20))
        self.root.minsize(min(sw, self.px(1000)), min(sh - 80, self.px(640)))
        icon = self.emoji("\U0001F9F5", 64, raw=True)
        self.root.iconphoto(True, icon)
        try:
            self.root.state("zoomed")
        except tk.TclError:
            pass

        self.topbar = tk.Frame(self.root, bg=C["top"], height=self.px(70))
        self.topbar.pack(fill="x")
        tk.Frame(self.root, bg=C["border"], height=2).pack(fill="x")
        self.body = tk.Frame(self.root, bg=C["bg"])
        self.body.pack(fill="both", expand=True)
        self.screen = None
        self.show(HomeScreen)
        self.root.deiconify()

    # ---- utilities ---------------------------------------------------------
    def px(self, v):
        return int(v * self.scale)

    def emoji(self, ch, size, raw=False):
        key = (ch, size)
        if key not in self._emoji_cache:
            self._emoji_cache[key] = ImageTk.PhotoImage(render_emoji(ch, size if raw else self.px(size)))
        return self._emoji_cache[key]

    def thumb(self, item, size):
        key = (item.id, size)
        img = self._thumb_cache.get(key)
        if img is None:
            img = ImageTk.PhotoImage(item.render(self.px(size), aa=True))
            self._thumb_cache[key] = img
            if len(self._thumb_cache) > 500:
                self._thumb_cache.popitem(last=False)
        return img

    def _on_error(self, exc, val, tb):
        log_error("".join(traceback.format_exception(exc, val, tb)))
        self.message(self.t("oops"), self.t("error_convert"), "\U0001F615")

    # ---- navigation ---------------------------------------------------------
    def show(self, cls, **kwargs):
        if self.screen is not None:
            self.screen.close()
        for w in self.body.winfo_children():
            w.destroy()
        self._build_topbar(cls is not HomeScreen)
        self.screen = cls(self, self.body, **kwargs)
        self.screen.pack(fill="both", expand=True)

    def toggle_language(self):
        self.t.lang = "en" if self.t.lang == "it" else "it"
        self.settings["lang"] = self.t.lang
        save_settings(self.settings)
        self.root.title(self.t("app_title"))
        self.show(type(self.screen), **self.screen.state())

    def _build_topbar(self, show_home):
        for w in self.topbar.winfo_children():
            w.destroy()
        bar = tk.Frame(self.topbar, bg=C["top"], padx=self.px(16), pady=self.px(10))
        bar.pack(fill="x")
        if show_home:
            make_button(bar, "  " + self.t("home"), lambda: self.show(HomeScreen), kind="light", size=15,
                        image=self.emoji("\U0001F3E0", 30), padx=14, pady=4).pack(side="left")
        title = tk.Frame(bar, bg=C["top"])
        title.place(relx=0.5, rely=0.5, anchor="center")
        tk.Label(title, image=self.emoji("\U0001F9F5", 36), bg=C["top"]).pack(side="left", padx=(0, 10))
        tk.Label(title, text=self.t("app_title"), font=(FONT, 22, "bold"), fg=C["primary"], bg=C["top"]).pack(side="left")
        make_button(bar, self.t("other_lang"), self.toggle_language, kind="light", size=13, padx=14, pady=6).pack(side="right")
        make_button(bar, "  " + self.t("help"), self.show_help, kind="light", size=15,
                    image=self.emoji("\u2753", 26), padx=14, pady=4).pack(side="right", padx=(0, 12))
        if not show_home:
            tk.Frame(bar, bg=C["top"], height=self.px(46)).pack(side="left")

    # ---- dialogs ----------------------------------------------------------------
    def message(self, title, text, icon="\u2705", width=620):
        top = tk.Toplevel(self.root)
        top.title(title)
        top.configure(bg=C["bg"])
        top.transient(self.root)
        top.resizable(False, False)
        box = tk.Frame(top, bg=C["bg"], padx=self.px(36), pady=self.px(28))
        box.pack()
        head = tk.Frame(box, bg=C["bg"])
        head.pack(anchor="w")
        tk.Label(head, image=self.emoji(icon, 56), bg=C["bg"]).pack(side="left", padx=(0, 16))
        tk.Label(head, text=title, font=(FONT, 24, "bold"), fg=C["primary"], bg=C["bg"]).pack(side="left")
        tk.Label(box, text=text, font=(FONT, 15), fg=C["text"], bg=C["bg"], justify="left",
                 wraplength=self.px(width)).pack(anchor="w", pady=(self.px(18), self.px(24)))
        ok = make_button(box, self.t("ok"), top.destroy, kind="green", size=18, padx=40, pady=10)
        ok.pack()
        top.bind("<Return>", lambda e: top.destroy())
        top.bind("<Escape>", lambda e: top.destroy())
        top.update_idletasks()
        x = self.root.winfo_rootx() + (self.root.winfo_width() - top.winfo_width()) // 2
        y = self.root.winfo_rooty() + (self.root.winfo_height() - top.winfo_height()) // 3
        top.geometry("+%d+%d" % (max(0, x), max(0, y)))
        top.grab_set()
        ok.button.focus_set()

    def show_help(self):
        self.message(self.t("help_title"), self.t("help_text"), "\U0001F4A1", width=760)

    def run(self):
        self.root.mainloop()


class Screen(tk.Frame):
    def __init__(self, app, parent, **kwargs):
        super().__init__(parent, bg=C["bg"])
        self.app = app
        self.t = app.t
        self.kwargs = kwargs

    def state(self):
        return self.kwargs

    def close(self):
        pass

    def title(self, parent, text, size=26):
        return tk.Label(parent, text=text, font=(FONT, size, "bold"), fg=C["text"], bg=C["bg"])


# --------------------------------------------------------------------------
# home
# --------------------------------------------------------------------------

class HomeScreen(Screen):
    def __init__(self, app, parent):
        super().__init__(app, parent)
        px = app.px
        center = tk.Frame(self, bg=C["bg"])
        center.place(relx=0.5, rely=0.46, anchor="center")
        self.title(center, self.t("home_hello"), 30).pack(pady=(0, px(36)))
        row = tk.Frame(center, bg=C["bg"])
        row.pack()
        n = len(app.library) // 100 * 100
        n = "{:,}".format(n).replace(",", "." if self.t.lang == "it" else ",")
        cards = [
            ("\U0001F4F7", self.t("home_photo"), self.t("home_photo_sub"), lambda: app.show(PhotoScreen)),
            ("\U0001F338", self.t("home_catalog"),
             self.t("home_catalog_sub", n=n),
             lambda: app.show(CategoriesScreen)),
            ("\u270F\ufe0f", self.t("home_text"), self.t("home_text_sub"), lambda: app.show(TextScreen)),
        ]
        for icon, title, sub, cmd in cards:
            wrap = tk.Frame(row, bg=C["border"], padx=3, pady=3)
            wrap.pack(side="left", padx=px(14))
            card = tk.Frame(wrap, bg=C["card"], width=px(320), height=px(330))
            card.pack()
            card.pack_propagate(False)
            tk.Label(card, image=app.emoji(icon, 110), bg=C["card"]).pack(pady=(px(34), px(16)))
            tk.Label(card, text=title, font=(FONT, 22, "bold"), fg=C["primary"], bg=C["card"]).pack()
            tk.Label(card, text=sub, font=(FONT, 14), fg=C["muted"], bg=C["card"], justify="center").pack(pady=px(8))
            clickable(wrap, cmd, wrap, C["border"], C["primary"])
        tk.Label(center, text=self.t("home_note"), font=(FONT, 13), fg=C["muted"], bg=C["bg"],
                 wraplength=px(1000)).pack(pady=(px(36), 0))


# --------------------------------------------------------------------------
# catalogue
# --------------------------------------------------------------------------

def search_bar(screen, parent, initial=""):
    app = screen.app
    box = tk.Frame(parent, bg=C["bg"])
    tk.Label(box, image=app.emoji("\U0001F50D", 30), bg=C["bg"]).pack(side="left", padx=(0, 8))
    var = tk.StringVar(value=initial)
    wrap = tk.Frame(box, bg=C["border"], padx=2, pady=2)
    wrap.pack(side="left")
    entry = tk.Entry(wrap, textvariable=var, font=(FONT, 17), width=22, relief="flat", bd=6, fg=C["text"])
    entry.pack()

    def go():
        q = var.get().strip()
        if q:
            app.show(GridScreen, query=q)
    entry.bind("<Return>", lambda e: go())
    make_button(box, app.t("search"), go, size=15, padx=18, pady=6).pack(side="left", padx=(8, 0))
    return box


class CategoriesScreen(Screen):
    def __init__(self, app, parent):
        super().__init__(app, parent)
        px = app.px
        head = tk.Frame(self, bg=C["bg"], padx=px(30), pady=px(18))
        head.pack(fill="x")
        self.title(head, self.t("choose_topic")).pack(side="left")
        search_bar(self, head).pack(side="right")
        tk.Label(self, text=self.t("search_hint"), font=(FONT, 12), fg=C["muted"], bg=C["bg"]).pack(anchor="e", padx=px(30))
        self.grid_area = tk.Frame(self, bg=C["bg"])
        self.grid_area.pack(fill="both", expand=True, padx=px(24), pady=px(10))
        self.inner = tk.Frame(self.grid_area, bg=C["bg"])
        self.inner.place(relx=0.5, y=0, anchor="n")
        self.tiles = []
        for cat, it, en, icon in CATEGORIES:
            items = app.library.category(cat)
            if not items:
                continue
            wrap = tk.Frame(self.inner, bg=C["border"], padx=3, pady=3)
            tile = tk.Frame(wrap, bg=C["card"], width=px(200), height=px(170))
            tile.pack()
            tile.pack_propagate(False)
            tk.Label(tile, image=app.emoji(icon, 70), bg=C["card"]).pack(pady=(px(16), px(6)))
            tk.Label(tile, text=it if self.t.lang == "it" else en, font=(FONT, 15, "bold"), fg=C["text"],
                     bg=C["card"]).pack()
            tk.Label(tile, text=self.t("designs_count", n=len(items)), font=(FONT, 12), fg=C["muted"],
                     bg=C["card"]).pack()
            clickable(wrap, lambda c=cat: app.show(GridScreen, cat=c), wrap, C["border"], C["primary"])
            self.tiles.append(wrap)
        self._cols = None
        self.grid_area.bind("<Configure>", self._layout)

    def _layout(self, event):
        cols = max(1, event.width // self.app.px(222))
        if cols == self._cols:
            return
        self._cols = cols
        for i, w in enumerate(self.tiles):
            w.grid(row=i // cols, column=i % cols, padx=self.app.px(8), pady=self.app.px(8))


class GridScreen(Screen):
    TILE_W, TILE_H = 178, 206

    def __init__(self, app, parent, cat=None, query=None, start=0):
        super().__init__(app, parent, cat=cat, query=query, start=start)
        px = app.px
        self.items = app.library.category(cat) if cat else app.library.search(query or "")
        self.start = start
        head = tk.Frame(self, bg=C["bg"], padx=px(24), pady=px(14))
        head.pack(fill="x")
        make_button(head, "◀  " + self.t("topics"), lambda: app.show(CategoriesScreen), kind="light",
                    size=15, padx=14, pady=6).pack(side="left", padx=(0, px(20)))
        if cat:
            it, en = CATEGORY_NAMES[cat]
            title = it if self.t.lang == "it" else en
        else:
            title = self.t("results_for", q=query)
        self.title(head, short(title, 34), 24).pack(side="left")
        tk.Label(head, text="  " + self.t("designs_count", n=len(self.items)), font=(FONT, 14), fg=C["muted"],
                 bg=C["bg"]).pack(side="left", pady=(px(8), 0))
        search_bar(self, head, query or "").pack(side="right")

        foot = tk.Frame(self, bg=C["bg"], pady=px(12))
        foot.pack(side="bottom", fill="x")
        self.prev_btn = make_button(foot, self.t("prev"), self.prev_page, kind="light", size=16, padx=24, pady=8)
        self.prev_btn.pack(side="left", padx=px(30))
        self.next_btn = make_button(foot, self.t("next"), self.next_page, kind="primary", size=16, padx=24, pady=8)
        self.next_btn.pack(side="right", padx=px(30))
        self.page_label = tk.Label(foot, font=(FONT, 16), fg=C["text"], bg=C["bg"])
        self.page_label.pack()

        self.grid_area = tk.Frame(self, bg=C["bg"])
        self.grid_area.pack(fill="both", expand=True, padx=px(20))
        self.per_page = None
        self._pending = None
        if not self.items:
            tk.Label(self.grid_area, text=self.t("no_results"), font=(FONT, 20), fg=C["muted"],
                     bg=C["bg"]).place(relx=0.5, rely=0.4, anchor="center")
            foot.pack_forget()
        else:
            self.grid_area.bind("<Configure>", self._on_resize)

    def state(self):
        return dict(self.kwargs, start=self.start)

    def _on_resize(self, event):
        if self._pending:
            self.after_cancel(self._pending)
        self._pending = self.after(120, lambda: self._layout(event.width, event.height))

    def _layout(self, width, height):
        px = self.app.px
        cols = max(2, width // px(self.TILE_W + 16))
        rows = max(1, height // px(self.TILE_H + 16))
        if cols * rows == self.per_page and getattr(self, "_cols", None) == cols:
            return
        self._cols = cols
        self.per_page = cols * rows
        self.start = (self.start // self.per_page) * self.per_page
        self.render_page()

    def render_page(self):
        px = self.app.px
        for w in self.grid_area.winfo_children():
            w.destroy()
        inner = tk.Frame(self.grid_area, bg=C["bg"])
        inner.place(relx=0.5, y=0, anchor="n")
        page_items = self.items[self.start:self.start + self.per_page]
        for i, item in enumerate(page_items):
            wrap = tk.Frame(inner, bg=C["border"], padx=3, pady=3)
            tile = tk.Frame(wrap, bg=C["card"], width=px(self.TILE_W), height=px(self.TILE_H))
            tile.pack()
            tile.pack_propagate(False)
            tk.Label(tile, image=self.app.thumb(item, 128), bg=C["card"]).pack(pady=(px(10), px(4)))
            tk.Label(tile, text=short(item.name(self.t.lang)), font=(FONT, 11), fg=C["text"], bg=C["card"],
                     wraplength=px(self.TILE_W - 16), justify="center").pack()
            clickable(wrap, lambda it=item: self.open(it), wrap, C["border"], C["primary"])
            wrap.grid(row=i // self._cols, column=i % self._cols, padx=px(6), pady=px(6))
        pages = max(1, -(-len(self.items) // self.per_page))
        page = self.start // self.per_page + 1
        self.page_label.config(text=self.t("page", a=page, b=pages))
        self._enable(self.prev_btn, page > 1)
        self._enable(self.next_btn, page < pages)

    def _enable(self, wrap, on):
        wrap.button.config(state="normal" if on else "disabled")

    def prev_page(self):
        if self.start > 0:
            self.start = max(0, self.start - self.per_page)
            self.render_page()

    def next_page(self):
        if self.start + self.per_page < len(self.items):
            self.start += self.per_page
            self.render_page()

    def open(self, item):
        image = item.render(1000)
        job = Job(item.name(self.t.lang).split(" · ")[0], image, photo=False, back=GridScreen,
                  back_kwargs=self.state(), n_colors=item.n_colors)
        self.app.show(EditorScreen, job=job)


# --------------------------------------------------------------------------
# photo
# --------------------------------------------------------------------------

def choose_photo(app, back_kwargs=None):
    path = filedialog.askopenfilename(
        parent=app.root, title=app.t("choose_photo"),
        initialdir=app.settings.get("last_dir") or known_folder("Pictures"),
        filetypes=[(app.t("pictures"), IMAGE_TYPES), ("*", "*.*")])
    if not path:
        return
    try:
        img = Image.open(path)
        img = ImageOps.exif_transpose(img)
        img.thumbnail((2000, 2000))
        img = img.convert("RGBA")
    except Exception:  # any unreadable file
        app.message(app.t("oops"), app.t("error_open"), "\U0001F615")
        return
    app.settings["last_dir"] = os.path.dirname(path)
    save_settings(app.settings)
    name = os.path.splitext(os.path.basename(path))[0]
    job = Job(name, img, photo=True, back=PhotoScreen, n_colors=6)
    app.show(EditorScreen, job=job)


class PhotoScreen(Screen):
    def __init__(self, app, parent):
        super().__init__(app, parent)
        px = app.px
        center = tk.Frame(self, bg=C["bg"])
        center.place(relx=0.5, rely=0.45, anchor="center")
        tk.Label(center, image=app.emoji("\U0001F5BC\ufe0f", 120), bg=C["bg"]).pack(pady=(0, px(16)))
        self.title(center, self.t("photo_title"), 28).pack()
        tk.Label(center, text=self.t("photo_intro"), font=(FONT, 16), fg=C["text"], bg=C["bg"],
                 wraplength=px(760), justify="center").pack(pady=px(24))
        make_button(center, "   " + self.t("choose_photo"), lambda: choose_photo(app), kind="green", size=22,
                    image=app.emoji("\U0001F4C2", 44), padx=40, pady=14).pack()


# --------------------------------------------------------------------------
# text
# --------------------------------------------------------------------------

TEXT_COLORS = [p.main for p in shapes.PALETTES] + [(20, 20, 20), (205, 160, 40), (110, 110, 110)]


class TextScreen(Screen):
    def __init__(self, app, parent, text=None, font=0, color=0):
        super().__init__(app, parent)
        px = app.px
        self.fonts = shapes.available_fonts()
        self.font_idx = min(font, len(self.fonts) - 1)
        self.color_idx = color
        self.var = tk.StringVar(value=text if text is not None else self.t("text_default"))
        box = tk.Frame(self, bg=C["bg"], padx=px(40), pady=px(20))
        box.pack(fill="both", expand=True)
        self.title(box, self.t("text_title"), 28).pack(anchor="w")

        tk.Label(box, text=self.t("text_label"), font=(FONT, 17, "bold"), fg=C["text"], bg=C["bg"]).pack(anchor="w", pady=(px(18), px(6)))
        wrap = tk.Frame(box, bg=C["primary"], padx=2, pady=2)
        wrap.pack(anchor="w")
        self.entry = tk.Entry(wrap, textvariable=self.var, font=(FONT, 28), width=20, relief="flat", bd=8, fg=C["text"])
        self.entry.pack()
        self.entry.focus_set()
        self.entry.icursor("end")
        self.entry.bind("<Return>", lambda e: self.next())
        self.var.trace_add("write", lambda *a: self._schedule())

        tk.Label(box, text=self.t("text_font"), font=(FONT, 17, "bold"), fg=C["text"], bg=C["bg"]).pack(anchor="w", pady=(px(20), px(6)))
        self.font_row = tk.Frame(box, bg=C["bg"])
        self.font_row.pack(anchor="w")
        self.font_btns = []
        for i, (ffile, f_it, f_en) in enumerate(self.fonts):
            w = tk.Frame(self.font_row, bg=C["border"], padx=3, pady=3)
            inner = tk.Frame(w, bg=C["card"], width=px(230), height=px(110))
            inner.pack()
            inner.pack_propagate(False)
            img_lbl = tk.Label(inner, bg=C["card"])
            img_lbl.pack(expand=True)
            tk.Label(inner, text=f_it if self.t.lang == "it" else f_en, font=(FONT, 11), fg=C["muted"],
                     bg=C["card"]).pack(pady=(0, px(4)))
            clickable(w, lambda i=i: self.set_font(i))
            w.grid(row=i // 3, column=i % 3, padx=(0, px(12)), pady=(0, px(12)))
            self.font_btns.append((w, img_lbl))

        tk.Label(box, text=self.t("text_color"), font=(FONT, 17, "bold"), fg=C["text"], bg=C["bg"]).pack(anchor="w", pady=(px(8), px(6)))
        self.color_row = tk.Frame(box, bg=C["bg"])
        self.color_row.pack(anchor="w")
        self.color_btns = []
        for i, rgb in enumerate(TEXT_COLORS):
            w = tk.Frame(self.color_row, bg=C["bg"], padx=4, pady=4)
            sw = tk.Frame(w, bg=to_hex(rgb), width=px(46), height=px(46))
            sw.pack()
            clickable(w, lambda i=i: self.set_color(i))
            w.pack(side="left", padx=(0, px(4)))
            self.color_btns.append(w)

        make_button(box, self.t("text_next"), self.next, kind="green", size=20, padx=36, pady=12).pack(anchor="w", pady=(px(24), 0))
        self._pending = None
        self._paint()

    def state(self):
        return dict(text=self.var.get(), font=self.font_idx, color=self.color_idx)

    def _schedule(self):
        if self._pending:
            self.after_cancel(self._pending)
        self._pending = self.after(250, self._paint)

    def set_font(self, i):
        self.font_idx = i
        self._paint()

    def set_color(self, i):
        self.color_idx = i
        self._paint()

    def _paint(self):
        px = self.app.px
        text = self.var.get().strip()[:30] or "Abc"
        color = TEXT_COLORS[self.color_idx]
        self._imgs = []
        for i, (w, lbl) in enumerate(self.font_btns):
            img = shapes.render_text(text, self.fonts[i][0], color, height=px(60))
            img.thumbnail((px(210), px(70)), Image.LANCZOS)
            photo = ImageTk.PhotoImage(img)
            self._imgs.append(photo)
            lbl.config(image=photo)
            w.config(bg=C["primary"] if i == self.font_idx else C["border"])
        for i, w in enumerate(self.color_btns):
            w.config(bg=C["primary"] if i == self.color_idx else C["bg"])

    def next(self):
        text = " ".join(self.var.get().split())[:30]
        if not text:
            self.app.message(self.t("oops"), self.t("text_empty"), "\u270F\ufe0f")
            return
        img = shapes.render_text(text, self.fonts[self.font_idx][0], TEXT_COLORS[self.color_idx], height=400)
        job = Job(text, img, photo=False, back=TextScreen, back_kwargs=self.state(), n_colors=2)
        self.app.show(EditorScreen, job=job)


# --------------------------------------------------------------------------
# editor: preview + options + save
# --------------------------------------------------------------------------

class EditorScreen(Screen):
    def __init__(self, app, parent, job):
        super().__init__(app, parent, job=job)
        px = app.px
        self.job = job
        self.design = None
        self.queue = queue.Queue()
        self.running = set()
        self._usb = None
        self._poll_id = None
        self._usb_id = None
        sw, sh = app.root.winfo_screenwidth(), app.root.winfo_screenheight()
        self.preview_px = max(px(320), min(sh - px(250), sw - px(640), px(760)))

        # ---- left: title and preview -----------------------------------------
        left = tk.Frame(self, bg=C["bg"], padx=px(24), pady=px(14))
        left.pack(side="left", fill="both", expand=True)
        head = tk.Frame(left, bg=C["bg"])
        head.pack(fill="x")
        make_button(head, "◀  " + self.t("back"), self.go_back, kind="light", size=15, padx=14, pady=6).pack(side="left")
        self.title(head, "  " + short(job.name, 30), 22).pack(side="left")
        frame = tk.Frame(left, bg=C["border"], padx=3, pady=3)
        frame.pack(pady=(px(12), 0))
        self._preview = ImageTk.PhotoImage(Image.new("RGB", (self.preview_px, self.preview_px), (246, 241, 232)))
        self.preview = tk.Label(frame, bg=C["fabric"], image=self._preview, bd=0)
        self.preview.pack()
        self.busy = tk.Label(frame, text="\u23F3  " + self.t("working"), font=(FONT, 18, "bold"),
                             fg=C["primary"], bg=C["card"], padx=20, pady=12)

        # ---- right: options --------------------------------------------------------
        right = tk.Frame(self, bg=C["bg"], width=px(500))
        right.pack(side="right", fill="y", padx=(0, px(20)), pady=px(14))
        right.pack_propagate(False)
        self.save_area = tk.Frame(right, bg=C["bg"])
        self.save_area.pack(side="bottom", fill="x", pady=(px(10), 0))
        scroll = Scrollable(right, C["bg"])
        scroll.pack(fill="both", expand=True)
        opts = scroll.inner

        top = tk.Frame(opts, bg=C["bg"])
        top.pack(fill="x", pady=(0, px(10)))
        thumb = job.image.copy()
        thumb.thumbnail((px(90), px(90)))
        bg = Image.new("RGBA", thumb.size, (255, 255, 255, 255))
        bg.alpha_composite(thumb)
        self._orig = ImageTk.PhotoImage(bg)
        tk.Label(top, image=self._orig, bg=C["card"], relief="solid", bd=1).pack(side="left")
        info = tk.Frame(top, bg=C["bg"])
        info.pack(side="left", padx=px(12), fill="x")
        tk.Label(info, text=self.t("original"), font=(FONT, 12), fg=C["muted"], bg=C["bg"]).pack(anchor="w")
        if job.photo:
            make_button(info, self.t("change_photo"), lambda: choose_photo(app), kind="light", size=13,
                        padx=12, pady=4).pack(anchor="w", pady=(px(4), 0))

        self._label(opts, self.t("step_size"))
        ToggleGroup(opts, [("small", self.t("size_small")), ("medium", self.t("size_medium")),
                           ("large", self.t("size_large"))], job.size, self._set_size).pack(fill="x")
        if job.photo:
            self._label(opts, self.t("step_colors"))
            ToggleGroup(opts, [(4, self.t("colors_few")), (6, self.t("colors_normal")), (10, self.t("colors_many"))],
                        job.n_colors, self._set_colors).pack(fill="x")
            self._label(opts, self.t("step_background"))
            ToggleGroup(opts, [(True, self.t("yes")), (False, self.t("no"))], job.remove_bg,
                        self._set_bg, size=15).pack(fill="x")

        self.info = tk.Label(opts, font=(FONT, 15), fg=C["text"], bg=C["card"], justify="left", anchor="w",
                             padx=px(14), pady=px(10), relief="flat")
        self.info.pack(fill="x", pady=(px(18), 0))
        self.warning = tk.Label(opts, text=self.t("large_warning"), font=(FONT, 12, "bold"), fg="#A15C00",
                                bg=C["bg"], wraplength=px(440), justify="left")
        self._label(opts, self.t("threads_title"))
        self.threads = tk.Frame(opts, bg=C["bg"])
        self.threads.pack(fill="x")

        self._refresh_usb()
        self.request()

    def state(self):
        return dict(job=self.job)

    def close(self):
        for aid in (self._poll_id, self._usb_id):
            if aid:
                self.after_cancel(aid)

    def _label(self, parent, text):
        tk.Label(parent, text=text, font=(FONT, 16, "bold"), fg=C["text"], bg=C["bg"]).pack(anchor="w", pady=(self.app.px(16), self.app.px(6)))

    def go_back(self):
        self.app.show(self.job.back, **self.job.back_kwargs)

    # ---- options -----------------------------------------------------------------
    def _set_size(self, v):
        self.job.size = v
        self.request()

    def _set_colors(self, v):
        self.job.n_colors = v
        self.request()

    def _set_bg(self, v):
        self.job.remove_bg = v
        self.request()

    # ---- conversion in the background -------------------------------------------
    def request(self):
        key = self.job.key()
        if self.job.size == "large":
            self.warning.pack(after=self.info, anchor="w", pady=(self.app.px(6), 0))
        else:
            self.warning.pack_forget()
        if key in self.job.cache:
            self.show_design(*self.job.cache[key])
            return
        self.design = None
        self._update_save_buttons()
        self.busy.place(relx=0.5, rely=0.5, anchor="center")
        self.busy.lift()
        if key in self.running:
            return
        self.running.add(key)
        job, size, out = self.job, self.preview_px, self.queue
        size_, n, bg = key

        def work():
            try:
                design = convert(job.image, size_, n, bg, photo=job.photo)
                result = (design, design.preview(size))
            except Exception:
                log_error(traceback.format_exc())
                result = None
            out.put((key, result))
        threading.Thread(target=work, daemon=True).start()
        if self._poll_id is None:
            self._poll()

    def _poll(self):
        self._poll_id = self.after(80, self._poll)
        try:
            key, result = self.queue.get_nowait()
        except queue.Empty:
            return
        self.running.discard(key)
        if result is not None:
            self.job.cache[key] = result
        if key != self.job.key():
            return
        self.busy.place_forget()
        if result is None:
            self.app.message(self.t("oops"), self.t("error_convert"), "\U0001F615")
            return
        self.show_design(*result)

    def show_design(self, design, preview):
        px = self.app.px
        self.busy.place_forget()
        self.design = design
        self._preview = ImageTk.PhotoImage(preview)
        self.preview.config(image=self._preview, width=self.preview_px, height=self.preview_px)
        fmt = lambda v: ("%.1f" % (v / 10)).replace(".", "," if self.t.lang == "it" else ".")
        count = "{:,}".format(design.stitch_count)
        if self.t.lang == "it":
            count = count.replace(",", ".")
        self.info.config(text=self.t("info", w=fmt(design.width_mm), h=fmt(design.height_mm), s=count,
                                     m=design.minutes()))
        for w in self.threads.winfo_children():
            w.destroy()
        for i, block in enumerate(design.blocks):
            row = tk.Frame(self.threads, bg=C["bg"])
            row.pack(fill="x", pady=px(3))
            sw = tk.Canvas(row, width=px(36), height=px(36), bg=C["bg"], highlightthickness=0)
            sw.create_oval(2, 2, px(34), px(34), fill=to_hex(block.rgb), outline="#777777", width=1)
            sw.pack(side="left")
            tk.Label(row, text="%d.  %s" % (i + 1, simple_name(block.rgb, self.t.lang)), font=(FONT, 15, "bold"),
                     fg=C["text"], bg=C["bg"]).pack(side="left", padx=(px(10), px(6)))
            tk.Label(row, text="(%s: %s)" % (self.t("brother"), block.thread.description), font=(FONT, 12),
                     fg=C["muted"], bg=C["bg"]).pack(side="left")
        self._update_save_buttons()

    # ---- saving ------------------------------------------------------------------
    def _refresh_usb(self):
        drives = usb_drives()
        if drives != self._usb:
            self._usb = drives
            self._build_save_area()
        self._usb_id = self.after(2000, self._refresh_usb)

    def _build_save_area(self):
        for w in self.save_area.winfo_children():
            w.destroy()
        app = self.app
        self.save_buttons = []
        if self._usb:
            for d in self._usb[:2]:
                b = make_button(self.save_area, "  " + self.t("save_usb", d=d.rstrip("\\")), lambda d=d: self.save_usb(d),
                                kind="green", size=17, image=app.emoji("\U0001F4BE", 34), padx=10, pady=10)
                b.pack(fill="x", pady=(0, app.px(8)))
                self.save_buttons.append(b)
            b = make_button(self.save_area, self.t("save_pc"), self.save_pc, kind="light", size=15, pady=8)
            b.pack(fill="x")
            self.save_buttons.append(b)
        else:
            tk.Label(self.save_area, text=self.t("no_usb"), font=(FONT, 12), fg=C["muted"], bg=C["bg"],
                     justify="left").pack(anchor="w", pady=(0, app.px(6)))
            b = make_button(self.save_area, "  " + self.t("save_pc"), self.save_pc, kind="green", size=17,
                            image=app.emoji("\U0001F4BE", 34), padx=10, pady=10)
            b.pack(fill="x")
            self.save_buttons.append(b)
        self._update_save_buttons()

    def _update_save_buttons(self):
        for b in getattr(self, "save_buttons", []):
            b.button.config(state="normal" if self.design is not None else "disabled")

    def _write(self, path):
        try:
            self.design.save_pes(path)
            return True
        except Exception:
            log_error(traceback.format_exc())
            self.app.message(self.t("oops"), self.t("error_save"), "\U0001F615")
            return False

    def save_usb(self, drive):
        if self.design is None:
            return
        path = unique_path(drive, safe_filename(self.job.name))
        if self._write(path):
            self.app.message(self.t("saved_title"), self.t("saved_usb", name=os.path.basename(path)))

    def save_pc(self):
        if self.design is None:
            return
        folder = self.app.settings.get("save_dir") or known_folder("Documents")
        path = filedialog.asksaveasfilename(parent=self.app.root, title=self.t("save_pc"), initialdir=folder,
                                            initialfile=safe_filename(self.job.name) + ".pes",
                                            defaultextension=".pes", filetypes=[("PES", "*.pes")])
        if not path:
            return
        if self._write(path):
            self.app.settings["save_dir"] = os.path.dirname(path)
            save_settings(self.app.settings)
            self.app.message(self.t("saved_title"), self.t("saved_pc", path=os.path.normpath(path)))


def main():
    App().run()
