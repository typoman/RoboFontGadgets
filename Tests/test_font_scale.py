from utils import *
from fontTools.misc.roundTools import otRound
import fontgadgets.extensions.font.scale

@pytest.fixture
def sample_font_for_scaling():
    font = defcon.Font()

    # Add some glyphs
    font.newGlyph("A")
    font.newGlyph("B")

    # Add kerning
    font.kerning[("A", "B")] = 10
    font.kerning[("B", "A")] = 20

    # Add font info attributes
    font.info.descender = -100
    font.info.xHeight = 500
    font.info.capHeight = 700
    font.info.ascender = 800

    # Add guidelines
    font.appendGuideline({"x": 50, "y": 0, "angle": 90})
    font.appendGuideline({"x": 0, "y": 100, "angle": 0})
    return font

def test_scale_font(sample_font_for_scaling):
    font = sample_font_for_scaling
    font.scale(factor=0.5)

    assert font.kerning[("A", "B")] == 5
    assert font.kerning[("B", "A")] == 10
    assert font.info.descender == -50
    assert font.info.xHeight == 250
    assert font.info.capHeight == 350
    assert font.info.ascender == 400
    assert font.guidelines[0].x == 25
    assert font.guidelines[1].y == 50

def test_scale_font_no_rounding(sample_font_for_scaling):
    font = sample_font_for_scaling
    font.scale(factor=0.333, round_values=False)

    assert font.kerning[("A", "B")] == 10 * 0.333
    assert font.kerning[("B", "A")] == 20 * 0.333
    assert font.info.descender == -100 * 0.333
    assert font.info.xHeight == 500 * 0.333
    assert font.info.capHeight == 700 * 0.333
    assert font.info.ascender == 800 * 0.333
    assert font.guidelines[0].x == 50 * 0.333
    assert font.guidelines[1].y == 100 * 0.333
