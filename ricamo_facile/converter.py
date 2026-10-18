"""Turns a picture into embroidery stitches and writes Brother .PES files.

Pipeline:
  1. low-resolution pass: pick the thread colours (median cut), find the
     background (transparent pixels, or the colour touching the border) and
     the bounding box of the subject;
  2. full-resolution pass on a 0.2 mm grid: quantise with the same colours,
     remove speckles with a mode filter, merge tiny colours;
  3. for every colour, fill the area with tatami rows (0.4 mm apart, 3 mm
     stitches, staggered), chaining overlapping rows to avoid jumps.
"""
import math

import numpy as np
import pyembroidery
from PIL import Image, ImageDraw, ImageEnhance, ImageFilter, ImageOps

from .threads import color_distance, make_thread

PX_MM = 0.2           # size of one grid pixel, in mm
ROW_PX = 2            # distance between fill rows, in grid pixels (0.4 mm)
MIN_RUN_PX = 3        # shorter runs are not sewn (0.6 mm)
STITCH_MM = 3.0       # fill stitch length
TRAVEL_MM = 3.0       # max length of a connecting stitch
MIN_STITCH_MM = 0.3   # shorter stitches are skipped
TRIM_MM = 2.5         # moves longer than this become trim + jump
PULL_MM = 0.15        # pull compensation added at both ends of each row
BG = 255              # label used for "no stitches here"
BG_TOLERANCE = 42     # RGB distance from the border colour still counted as background

# Hoop presets: (width, height) in mm. The design is rotated if it fits better.
SIZES = {
    "small": (50, 50),
    "medium": (100, 100),
    "large": (130, 180),
}


class ColorBlock:
    def __init__(self, thread, area):
        self.thread = thread
        self.rgb = (thread.get_red(), thread.get_green(), thread.get_blue())
        self.area = area
        self.lines = []          # list of polylines, each a list of (x, y) in mm

    @property
    def stitch_count(self):
        return sum(len(line) for line in self.lines)


class Design:
    def __init__(self, blocks, width_mm, height_mm):
        self.blocks = blocks
        self.width_mm = width_mm
        self.height_mm = height_mm

    @property
    def stitch_count(self):
        return sum(b.stitch_count for b in self.blocks)

    @property
    def trim_count(self):
        return sum(max(0, len(b.lines) - 1) for b in self.blocks)

    def minutes(self):
        """Rough sewing time: 600 stitches per minute plus thread changes."""
        return max(1, round(self.stitch_count / 600 + len(self.blocks) * 0.7 + self.trim_count * 0.05))

    def to_pattern(self):
        p = pyembroidery.EmbPattern()
        for i, block in enumerate(self.blocks):
            p.add_thread(block.thread)
            if i > 0:
                p.add_command(pyembroidery.COLOR_CHANGE)
            for j, line in enumerate(block.lines):
                if j > 0:
                    p.add_command(pyembroidery.TRIM)
                x0, y0 = line[0]
                p.add_stitch_absolute(pyembroidery.JUMP, x0 * 10, y0 * 10)
                for x, y in line:
                    p.add_stitch_absolute(pyembroidery.STITCH, x * 10, y * 10)
        p.add_command(pyembroidery.END)
        return p

    def save_pes(self, path):
        pyembroidery.write_pes(self.to_pattern(), path, {
            "version": 6,
            "tie_on": True,
            "tie_off": True,
            "max_stitch": 121,
            "max_jump": 121,
        })

    def preview(self, size=600, fabric=(246, 241, 232)):
        """Draws the stitches as they will look on the fabric."""
        ss = 2  # supersampling
        big = size * ss
        img = Image.new("RGB", (big, big), fabric)
        if not self.blocks:
            return img.resize((size, size))
        scale = big * 0.92 / max(self.width_mm, self.height_mm)
        cx, cy = big / 2, big / 2
        d = ImageDraw.Draw(img)
        w = max(1, round(0.42 * scale))
        for block in self.blocks:
            dark = tuple(int(c * 0.72) for c in block.rgb)
            for line in block.lines:
                pts = [(cx + x * scale, cy + y * scale) for x, y in line]
                if len(pts) > 1:
                    d.line(pts, fill=dark, width=w + max(1, w // 3))
            for line in block.lines:
                pts = [(cx + x * scale, cy + y * scale) for x, y in line]
                if len(pts) > 1:
                    d.line(pts, fill=block.rgb, width=w)
        return img.resize((size, size), Image.LANCZOS)


# --------------------------------------------------------------------------
# image -> labels
# --------------------------------------------------------------------------

def _flatten(img):
    bg = Image.new("RGB", img.size, (255, 255, 255))
    bg.paste(img, mask=img.getchannel("A"))
    return bg


def _resize_max(img, side):
    s = side / max(img.size)
    return img.resize((max(1, round(img.width * s)), max(1, round(img.height * s))), Image.LANCZOS)


def _prepare_rgb(img, photo):
    rgb = _flatten(img)
    if photo:
        rgb = rgb.filter(ImageFilter.MedianFilter(3))
        rgb = ImageEnhance.Color(rgb).enhance(1.15)
    return rgb


def _border_flood(mask):
    """Pixels of `mask` connected to the image border."""
    h, w = mask.shape
    m = Image.fromarray((mask * 255).astype(np.uint8), "L").copy()  # copy: fromarray memory is read-only
    px = m.load()
    seeds = [(x, 0) for x in range(w)] + [(x, h - 1) for x in range(w)]
    seeds += [(0, y) for y in range(h)] + [(w - 1, y) for y in range(h)]
    for xy in seeds:
        if px[xy] == 255:
            ImageDraw.floodfill(m, xy, 128)
    return np.array(m) == 128


def _palette_image(colors):
    """A 'P' image usable with Image.quantize(palette=...) holding exactly `colors`."""
    flat = []
    for i in range(256):
        flat.extend(colors[min(i, len(colors) - 1)])
    img = Image.new("P", (1, 1))
    img.putpalette(flat)
    return img


def _graphic_palette(pixels, max_colors):
    """The real flat colours of a drawing, ignoring anti-aliasing pixels.

    Returns None when the picture has no clear flat colours (e.g. gradients)."""
    codes = (pixels[:, 0].astype(np.uint32) << 16) | (pixels[:, 1].astype(np.uint32) << 8) | pixels[:, 2]
    uniq, counts = np.unique(codes, return_counts=True)
    order = np.argsort(-counts)
    total = len(codes)
    chosen, covered = [], 0
    for i in order:
        if counts[i] < total * 0.002 or len(chosen) >= max_colors:
            break
        c = int(uniq[i])
        rgb = (c >> 16, (c >> 8) & 255, c & 255)
        covered += counts[i]
        if all(color_distance(rgb, o) > 1500 for o in chosen):
            chosen.append(rgb)
    if not chosen or covered < total * 0.8:
        return None
    return chosen


def _fit_scale(w, h, box):
    """mm per source pixel so that (w, h) fits in box, rotating the box if better."""
    bw, bh = box
    return max(min(bw / w, bh / h), min(bh / w, bw / h))


def _labels(img, box, n_colors, remove_bg, photo):
    img = ImageOps.exif_transpose(img).convert("RGBA")
    alpha_full = img.getchannel("A")
    has_alpha = alpha_full.getextrema()[0] < 128
    if has_alpha:
        bbox = alpha_full.point(lambda a: 255 if a >= 128 else 0).getbbox()
        if bbox is None:
            raise ValueError("empty image")
        img = img.crop(bbox)

    # ---- pass 1: colours, background, bounding box --------------------------
    small = _resize_max(img, 320)
    small_rgb = _prepare_rgb(small, photo)
    small_alpha = np.array(small.getchannel("A")) >= 128
    arr = np.array(small_rgb)
    bg_small = ~small_alpha
    if remove_bg and not has_alpha:
        # background = pixels close to the typical border colour, connected to the border
        border = np.concatenate([arr[0], arr[-1], arr[:, 0], arr[:, -1]]).astype(np.int32)
        ref = np.median(border, axis=0)
        near = np.sqrt(((arr.astype(np.int32) - ref) ** 2).sum(axis=2)) < BG_TOLERANCE
        if near[0].mean() + near[-1].mean() + near[:, 0].mean() + near[:, -1].mean() >= 4 * 0.4:
            flood = _border_flood(near)
            if 0.02 < flood.mean() < 0.97:
                bg_small = flood
    pixels = arr[~bg_small]
    if len(pixels) == 0:
        raise ValueError("empty image")
    colors = None if photo else _graphic_palette(pixels, max(n_colors, 12))
    if colors is None:
        strip = Image.fromarray(pixels.reshape(1, -1, 3).astype(np.uint8), "RGB")
        q = strip.quantize(colors=n_colors, method=Image.Quantize.MEDIANCUT,
                           kmeans=2, dither=Image.Dither.NONE)
        used = sorted(set(np.array(q).ravel().tolist()))
        palette = q.getpalette()
        colors = [tuple(palette[3 * i:3 * i + 3]) for i in used]
    pal = _palette_image(colors)
    ys, xs = np.nonzero(~bg_small)
    if len(xs) == 0:
        raise ValueError("empty image")
    sx = img.width / small.width
    sy = img.height / small.height
    left = max(0, int(xs.min() * sx) - 1)
    top = max(0, int(ys.min() * sy) - 1)
    right = min(img.width, int(math.ceil((xs.max() + 1) * sx)) + 1)
    bottom = min(img.height, int(math.ceil((ys.max() + 1) * sy)) + 1)
    crop = img.crop((left, top, right, bottom))

    # ---- pass 2: full resolution on the stitch grid ------------------------
    mm_per_px = _fit_scale(crop.width, crop.height, box)
    gw = max(4, round(crop.width * mm_per_px / PX_MM))
    gh = max(4, round(crop.height * mm_per_px / PX_MM))
    big = crop.resize((gw, gh), Image.LANCZOS)
    big_rgb = _prepare_rgb(big, photo)
    labels = np.array(big_rgb.quantize(palette=pal, dither=Image.Dither.NONE))
    bg_mask = np.array(big.getchannel("A")) < 128
    if remove_bg and not has_alpha and bg_small.any():
        # scale the background mask (in small-image coordinates) onto the grid
        bx0, by0 = left / sx, top / sy
        bx1, by1 = right / sx, bottom / sy
        m = Image.fromarray((bg_small * 255).astype(np.uint8), "L")
        m = m.transform((gw, gh), Image.EXTENT, (bx0, by0, bx1, by1), Image.BILINEAR)
        bg_mask |= np.array(m) > 127
    labels[bg_mask] = BG
    size = 7 if photo else 3
    labels = np.array(Image.fromarray(labels.astype(np.uint8), "L").filter(ImageFilter.ModeFilter(size)))

    return labels, colors, gw * PX_MM, gh * PX_MM, photo


def _merge_colors(labels, colors, photo):
    """Merges colours too small to be sewn into the closest bigger colour."""
    ids, counts = np.unique(labels[labels != BG], return_counts=True)
    if len(ids) == 0:
        return labels, {}
    total = counts.sum()
    min_area = total * (0.006 if photo else 0.0012)
    big = [int(i) for i, c in zip(ids, counts) if c >= min_area] or [int(ids[counts.argmax()])]
    lut = np.full(256, BG, dtype=np.uint8)
    for i in ids:
        i = int(i)
        lut[i] = i if i in big else min(big, key=lambda b: color_distance(colors[i], colors[b]))
    return lut[labels], {b: make_thread(colors[b]) for b in big}


# --------------------------------------------------------------------------
# labels -> stitches
# --------------------------------------------------------------------------

def _runs(mask):
    starts, ends, rows = [], [], []
    h = mask.shape[0]
    for ri, y in enumerate(range(ROW_PX // 2, h, ROW_PX)):
        padded = np.concatenate(([0], mask[y].astype(np.int8), [0]))
        d = np.diff(padded)
        s = np.flatnonzero(d == 1)
        e = np.flatnonzero(d == -1)
        keep = (e - s) >= MIN_RUN_PX
        starts.extend(s[keep].tolist())
        ends.extend(e[keep].tolist())
        rows.extend([ri] * int(keep.sum()))
    return np.array(starts, dtype=np.int32), np.array(ends, dtype=np.int32), np.array(rows, dtype=np.int32)


def _row_points(xa, xb, ri):
    """Stitch x positions (mm) along a row from xa to xb, with tatami stagger."""
    off = (ri % 3) * STITCH_MM / 3
    lo, hi = (xa, xb) if xa < xb else (xb, xa)
    n0 = math.ceil((lo + MIN_STITCH_MM * 2 - off) / STITCH_MM)
    n1 = math.floor((hi - MIN_STITCH_MM * 2 - off) / STITCH_MM)
    inner = [off + n * STITCH_MM for n in range(n0, n1 + 1)]
    if xa > xb:
        inner.reverse()
    return [xa] + inner + [xb]


def _append(line, x, y):
    """Appends a point, splitting long moves and skipping tiny stitches."""
    if line:
        px, py = line[-1]
        dist = math.hypot(x - px, y - py)
        if dist < MIN_STITCH_MM:
            return
        if dist > TRAVEL_MM:
            n = int(dist // TRAVEL_MM)
            for k in range(1, n + 1):
                t = k / (n + 1)
                line.append((px + (x - px) * t, py + (y - py) * t))
    line.append((x, y))


def _fill(mask, block, pos, ox, oy):
    rs, re_, rr = _runs(mask)
    n = len(rs)
    if n == 0:
        return pos
    alive = np.ones(n, dtype=bool)
    by_row = {}
    for i, r in enumerate(rr.tolist()):
        by_row.setdefault(r, []).append(i)
    ry = (rr * ROW_PX + ROW_PX // 2).astype(np.float64)
    line = None
    px, py = pos
    while True:
        idx = np.flatnonzero(alive)
        if len(idx) == 0:
            break
        dy = (ry[idx] - py) ** 2
        d0 = (rs[idx] - px) ** 2 + dy
        d1 = (re_[idx] - px) ** 2 + dy
        k0, k1 = d0.argmin(), d1.argmin()
        if d0[k0] <= d1[k1]:
            cur, forward, dist2 = idx[k0], True, d0[k0]
        else:
            cur, forward, dist2 = idx[k1], False, d1[k1]
        if line is None or math.sqrt(dist2) * PX_MM > TRIM_MM:
            line = []
            block.lines.append(line)
        while True:
            alive[cur] = False
            a = rs[cur] * PX_MM - PULL_MM
            b = re_[cur] * PX_MM + PULL_MM
            y = ry[cur] * PX_MM
            xs = _row_points(a, b, rr[cur]) if forward else _row_points(b, a, rr[cur])
            for x in xs:
                _append(line, x + ox, y + oy)
            end_px = re_[cur] if forward else rs[cur]
            best, best_d = None, None
            for c in by_row.get(rr[cur] + 1, ()):
                if alive[c] and rs[c] < re_[cur] and re_[c] > rs[cur]:
                    start_px = re_[c] if forward else rs[c]
                    dd = abs(start_px - end_px)
                    if best is None or dd < best_d:
                        best, best_d = c, dd
            px, py = end_px, ry[cur]
            if best is None:
                break
            cur, forward = best, not forward
    block.lines[:] = [l for l in block.lines if len(l) > 1]
    return px, py


def convert(img, size="medium", n_colors=6, remove_bg=True, photo=True):
    """Converts a PIL image into a Design."""
    box = SIZES.get(size, size)
    labels, colors, w_mm, h_mm, photo = _labels(img, box, n_colors, remove_bg, photo)
    labels, threads = _merge_colors(labels, colors, photo)
    order = sorted(threads, key=lambda b: -(labels == b).sum())
    ox, oy = -w_mm / 2, -h_mm / 2
    blocks = []
    pos = (0.0, 0.0)
    for b in order:
        mask = labels == b
        block = ColorBlock(threads[b], int(mask.sum()))
        pos = _fill(mask, block, pos, ox, oy)
        if block.lines:
            blocks.append(block)
    # trim the real extent of the stitches
    if blocks:
        xs = [x for bl in blocks for line in bl.lines for x, _ in line]
        ys = [y for bl in blocks for line in bl.lines for _, y in line]
        w_mm = max(xs) - min(xs)
        h_mm = max(ys) - min(ys)
        cx, cy = (max(xs) + min(xs)) / 2, (max(ys) + min(ys)) / 2
        for bl in blocks:
            bl.lines = [[(x - cx, y - cy) for x, y in line] for line in bl.lines]
    return Design(blocks, w_mm, h_mm)
