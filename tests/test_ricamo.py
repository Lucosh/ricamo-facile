"""Basic checks for the converter and the catalogue (run with: python -m pytest)."""
import os
import sys

import pyembroidery
import pytest
from PIL import Image, ImageDraw

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))

from ricamo_facile import shapes  # noqa: E402
from ricamo_facile.converter import convert  # noqa: E402
from ricamo_facile.library import Library  # noqa: E402


def red_circle_photo():
    img = Image.new("RGB", (800, 600), (250, 250, 248))
    ImageDraw.Draw(img).ellipse((250, 150, 550, 450), fill=(200, 30, 40))
    return img


def test_pes_round_trip(tmp_path):
    design = convert(red_circle_photo(), "medium", 4, remove_bg=True, photo=True)
    assert len(design.blocks) == 1
    assert 95 <= design.width_mm <= 101 and 95 <= design.height_mm <= 101
    path = str(tmp_path / "circle.pes")
    design.save_pes(path)
    pattern = pyembroidery.read(path)
    assert pattern.count_stitches() > 1000
    left, top, right, bottom = pattern.bounds()
    assert 950 <= right - left <= 1010


def test_background_kept_when_asked():
    design = convert(red_circle_photo(), "medium", 4, remove_bg=False, photo=True)
    assert len(design.blocks) == 2
    assert design.width_mm > design.height_mm


@pytest.mark.parametrize("size,limit", [("small", 50), ("medium", 100), ("large", 180)])
def test_fits_in_hoop(size, limit):
    design = convert(red_circle_photo(), size, 4, remove_bg=False, photo=True)
    assert max(design.width_mm, design.height_mm) <= limit + 1


def test_flat_colours_are_kept():
    flower = shapes.render(lambda d, S: shapes.make_flower(5, "round", 2)(d, S, shapes.PALETTES[0]), 800)
    design = convert(flower, "medium", 4, photo=False)
    assert len(design.blocks) == 3  # red, pink and the yellow centre


def test_library_is_big_and_searchable():
    lib = Library()
    assert len(lib) > 2500
    assert lib.search("gatto")
    assert lib.search("cat")
    assert lib.search("cuore")
    for item in lib.items[::300]:
        assert item.render(64, aa=True).getbbox() is not None
