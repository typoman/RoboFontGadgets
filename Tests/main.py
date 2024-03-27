import defcon
import fontParts.fontshell
from unittest.mock import MagicMock
import pytest

@pytest.fixture
def defcon_font_1():
    groups = {
        "public.kern1.C": ("C", "Ccedilla"),
        "public.kern1.O": ("D", "O", "Ograve"),
        "public.kern1.sin": ("seen", "sad"),
        "public.kern2.H": ("D", "E"),
        "public.kern2.O": ("C", "Ccedilla", "O", "Ograve"),
        "public.kern2.sad": ("sad", "tah"),
        "public.kern2.sin": ("seen", "seen.init"),
        "control": ("seen",),
    }

    cmap = {
        67: "C",
        199: "Ccedilla",
        68: "D",
        69: "E",
        79: "O",
        210: "Ograve",
        1587: "seen",
        1589: "sad",
        1591: "tah",
        65203: "seen.init",
        65228: "ain.medi",
    }

    font = defcon.Font()
    font.groups.update(groups)
    for un, gn in cmap.items():
        font.newGlyph(gn).unicodes = [un]
    return font


@pytest.fixture
def fontParts_font_1(defcon_font_1):
    return fontParts.fontshell.RFont(defcon_font_1)


@pytest.fixture
def glyph_1():
    glyph = MagicMock()
    glyph.contours = [MagicMock() for _ in range(3)]
    glyph.anchors = [MagicMock() for _ in range(3)]
    glyph.guidelines = [MagicMock() for _ in range(3)]
    glyph.components = [
        MagicMock(transformation=(1, 0, 0, 1, 10, 13)) for _ in range(3)
    ]  # Mock transformation
    glyph.width = 100
    return glyph

@pytest.fixture
def defcon_ar_font_1():
    """
    arabic test font inc. features, unicodes, kerning, groups, components
    """
    font = defcon.Font("data/ar-font-test-1.ufo")
    return font
