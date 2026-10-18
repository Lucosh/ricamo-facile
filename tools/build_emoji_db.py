"""Builds ricamo_facile/data/emoji.json from Unicode data files.

Usage:
    python tools/build_emoji_db.py emoji-test.txt it.xml

emoji-test.txt : https://unicode.org/Public/emoji/15.1/emoji-test.txt
it.xml         : https://github.com/unicode-org/cldr/blob/release-45/common/annotations/it.xml

Only emoji made of a single code point (optionally followed by U+FE0F) are kept,
because Pillow without libraqm cannot shape ZWJ sequences. Every emoji is also
test-rendered with the Windows "Segoe UI Emoji" font and dropped if the font
has no glyph for it.
"""
import json
import os
import re
import sys
import xml.etree.ElementTree as ET

from PIL import Image, ImageDraw, ImageFont

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "..", "ricamo_facile", "data", "emoji.json")
FONT = r"C:\Windows\Fonts\seguiemj.ttf"

# (group, subgroup prefix) -> app category. First match wins.
CATEGORY_RULES = [
    ("Smileys & Emotion", "heart", "cuori"),
    ("Smileys & Emotion", "emotion", "simboli"),
    ("Smileys & Emotion", "", "faccine"),
    ("People & Body", "", "persone"),
    ("Animals & Nature", "plant", "fiori"),
    ("Animals & Nature", "animal", "animali"),
    ("Food & Drink", "", "cibo"),
    ("Travel & Places", "sky", "cielo"),
    ("Travel & Places", "", "viaggi"),
    ("Activities", "", "feste"),
    ("Objects", "", "oggetti"),
    ("Symbols", "", "simboli"),
]
SKIP_GROUPS = {"Component", "Flags"}
SKIP_CHARS = {"💮"}  # white flower: contains Japanese text
SKIP_SUBGROUPS = {"keycap", "alphanum", "av-symbol", "other-symbol", "punctuation",
                  "currency", "math", "geometric", "arrow", "warning"}


def category_for(group, subgroup):
    for g, prefix, cat in CATEGORY_RULES:
        if g == group and subgroup.startswith(prefix):
            return cat
    return None


def load_italian(path):
    names, keywords = {}, {}
    root = ET.parse(path).getroot()
    for ann in root.iter("annotation"):
        cp = ann.get("cp", "").replace("\ufe0f", "")
        text = (ann.text or "").strip()
        if ann.get("type") == "tts":
            names[cp] = text
        else:
            keywords[cp] = [k.strip() for k in text.split("|") if k.strip()]
    return names, keywords


def renders(font, ch):
    img = Image.new("RGBA", (96, 96), (0, 0, 0, 0))
    ImageDraw.Draw(img).text((8, 8), ch, font=font, embedded_color=True)
    bbox = img.getchannel("A").getbbox()
    return bbox is not None


def main(test_file, it_file):
    it_names, it_keywords = load_italian(it_file)
    font = ImageFont.truetype(FONT, 64)
    line_re = re.compile(r"^([0-9A-F ]+?)\s*;\s*fully-qualified\s*#\s*(\S+)\s+E[\d.]+\s+(.+)$")
    group = subgroup = ""
    items = []
    with open(test_file, encoding="utf-8") as f:
        for line in f:
            line = line.rstrip("\n")
            if line.startswith("# group:"):
                group = line.split(":", 1)[1].strip()
                continue
            if line.startswith("# subgroup:"):
                subgroup = line.split(":", 1)[1].strip()
                continue
            m = line_re.match(line)
            if not m or group in SKIP_GROUPS or subgroup in SKIP_SUBGROUPS:
                continue
            cps = [c for c in m.group(1).split() if c != "FE0F"]
            if len(cps) != 1:
                continue
            ch = chr(int(cps[0], 16))
            if ch in SKIP_CHARS:
                continue
            cat = category_for(group, subgroup)
            if cat is None:
                continue
            full = m.group(2)
            if not renders(font, full):
                continue
            name_en = m.group(3).strip()
            name_it = it_names.get(ch, name_en)
            items.append({
                "c": full,
                "cat": cat,
                "en": name_en[:1].upper() + name_en[1:],
                "it": name_it[:1].upper() + name_it[1:],
                "k": " ".join(it_keywords.get(ch, [])),
            })
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    with open(OUT, "w", encoding="utf-8") as f:
        json.dump(items, f, ensure_ascii=False, separators=(",", ":"))
    counts = {}
    for it in items:
        counts[it["cat"]] = counts.get(it["cat"], 0) + 1
    print(len(items), "emoji written to", os.path.normpath(OUT))
    print(counts)


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])
