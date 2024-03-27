from main import *
import fontgadgets.extensions.glyph.type

@pytest.mark.parametrize(
    "glyph_name, expected_result",
    [
    ("lam_alef-ar.fina", True),
    ("teh_heh-ar.init", True),
    ("yehVabove_yehVabove-ar.fina.rlig", True),
    ("alefMaksura_heh-ar.medi", True),
    ("_fehDotless_alefMaksura-ar", True),
    ("beh-ar", False),
    ("kasratan-ar", False),
    ("_part.connection-ar", False),
    ],
)
def test_is_ligature(defcon_ar_font_1, glyph_name, expected_result):
    glyph = defcon_ar_font_1[glyph_name]
    assert glyph.isLigature is expected_result

@pytest.mark.parametrize(
    "glyph_name, expected_result",
    [
    ("sheen-ar.init", False),
    ("yehFarsi_noon-ar.fina.rlig", False),
    ("five", False),
    ("parenright", False),
    ("twodotshorizontalabove-ar", True),
    ("threedotsupabove-ar", True),
    ("fatha-ar", True),
    ("shaddaFathatan-ar", True),
    ],
)
def test_isMark(defcon_ar_font_1, glyph_name, expected_result):
    glyph = defcon_ar_font_1[glyph_name]
    assert glyph.isMark is expected_result

@pytest.mark.parametrize(
    "glyph_name, expected_result",
    [
    ("sheen-ar.init", True),
    ("five", True),
    ("parenright", True),
    ("shaddaFathatan-ar", False),
    ("yehVabove_yehVabove-ar.fina.rlig", False),
    ("_fehDotless_alefMaksura-ar", False),
    ("kasratan-ar", False),
    ("_part.connection-ar", True),
    ("hamza-ar", True),
    ("beh-ar.medi.calt", True),
    ("behDotless-ar.medi.calt", True),
    ("shadda-ar", False),
    ("commabelow-ar", True),
    ("_part.connectionHahInit-ar", True),
    ],
)
def test_is_base(defcon_ar_font_1, glyph_name, expected_result):
    glyph = defcon_ar_font_1[glyph_name]
    assert glyph.isBase is expected_result

@pytest.mark.parametrize(
    "glyph_name, expected_result",
    [
    ("teh-ar.medi", "base"),
    ("hah-ar.isol", "base"),
    ("sheen-ar", "base"),
    ("ain-ar.isol", "base"),
    ("kaf-ar.init", "base"),
    ("hehgoal-ar.medi", "base"),
    ("beh_tcheh-ar", "ligature"),
    ("teh_tcheh-ar", "ligature"),
    ("tteh_khah-ar", "ligature"),
    ("dad_reh-ar.fina.rlig", "ligature"),
    ("alefMaksura_heh-ar.medi.ss01", "ligature"),
    ("one", "base"),
    ("percent-ar", "base"),
    ("hamzaabove-ar", "mark"),
    ("shaddaKasratan-ar", "mark"),
    ("_alefMaksura_meem-ar.medi", "ligature"),
    ("_alefMaksura_meem-ar.calt1", "ligature"),
    ],
)
def test_get_type(defcon_ar_font_1, glyph_name, expected_result):
    glyph = defcon_ar_font_1[glyph_name]
    assert glyph.getType() is expected_result
