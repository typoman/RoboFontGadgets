from utils import *
import fontgadgets.extensions.features

@pytest.mark.parametrize(
    "glyphName, expectedNumberOfSourceGlyphs",
    [
    ("shadda-ar", 0),
    ("dot-ar", 0),
    ("_part.connectionFlat-ar", 0),
    ("alef-ar.fina.short", 0),
    ("yehbarree-ar.fina", 1),
    ("alefMaksura-ar.fina", 1),
    ("shaddaFathatan-ar", 2),
    ("_alefMaksura_meem-ar", 0),
    ],
)
def test_numberOfSourceGlyphs(defcon_ar_font_1, glyphName, expectedNumberOfSourceGlyphs):
    glyph = defcon_ar_font_1[glyphName]
    assert glyph.features.numberOfSourceGlyphs == expectedNumberOfSourceGlyphs
