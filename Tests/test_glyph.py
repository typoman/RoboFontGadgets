from main import *
import fontgadgets.extensions.glyph

def test_isComposite(defcon_ar_font_1):
    composite_names = "beh-ar.init khah-ar.init.calt hehgoalHamzaabove-ar.fina hah_alefMaksura-ar.fina.rlig gaf_yehHamzaabove-ar.rlig yehHamzaabove_meem-ar.init yehVabove_heh-ar.init".split()
    for glyph_name in composite_names:
        glyph = defcon_ar_font_1[glyph_name]
        assert glyph.isComposite is True

    contour_glyphs = "alef-ar.fina.short ain-ar.fina heh-ar.medi.ss02 allah-ar dateseparator-ar".split()
    for glyph_name in contour_glyphs:
        glyph = defcon_ar_font_1[glyph_name]
        assert glyph.isComposite is False

    # add a contour to a composite
    source_glyph = defcon_ar_font_1[contour_glyphs[1]]
    target_glyph = defcon_ar_font_1[composite_names[0]]
    target_glyph.copyDataFromGlyph(source_glyph)
    assert target_glyph.isComposite is False

@pytest.mark.parametrize(
    "glyphName, expectedOrder",
    [
    ('jeem-ar.init.calt', ['dotbelow-ar', 'hah-ar.init.calt']),
    ('khah-ar.init.calt', ['dotabove-ar', 'hah-ar.init.calt']),
    ('meem-ar.isol', ['meem-ar']),
    ('beh_yehHamzaabove-ar.rlig', ['_behdotless_alefMaksura-ar', 'dotbelow-ar', 'hamzaabove-ar']),
    ('teh_meem-ar', ['_alefMaksura_meem-ar', 'twodotshorizontalabove-ar']),
    ('theh_reh-ar.fina.rlig', ['_alefMaksura_reh-ar.fina.rlig', 'threedotsupabove-ar']),
    ('theh_yeh-ar.rlig', ['_behdotless_alefMaksura-ar', 'threedotsupabove-ar', 'twodotshorizontalbelow-ar']),
    ('hah_yehVabove-ar.rlig', ['hah_alefMaksura-ar.rlig', 'vabove-ar']),
    ('sheen_rehVbelow-ar.rlig', ['seen_reh-ar.rlig', 'threedotsupabove-ar', 'vbelow-ar']),
    ('dad_jeh-ar.rlig', ['dotabove-ar', 'sad_reh-ar.rlig', 'threedotsupabove-ar']),
    ],
)
def test_autoComponentOrder(defcon_ar_font_1, glyphName, expectedOrder):
    # create a glyph with multiple components
    glyph = defcon_ar_font_1[glyphName]
    glyph.autoComponentOrder()
    assert [c.baseGlyph for c in glyph.components] == expectedOrder

@pytest.mark.parametrize(
    "glyphName, expectedOrder",
    [
    ("S", 18),
    ("peh-ar", 76),
    ("rreh-ar.fina", 146),
    ("lam-ar.medi", 236),
    ("yehFarsi-ar.init", 321),
    ("teh_hah-ar.init", 413),
    ("khah_yehHamzaabove-ar.fina.rlig", 530),
    ],
)
def test_orderIndex(defcon_ar_font_1, glyphName, expectedOrder):
    # create a font with a glyph order
    glyph = defcon_ar_font_1[glyphName]
    assert glyph.orderIndex == expectedOrder

@pytest.mark.parametrize(
    "glyphName, expected",
    [
    ("r", True),
    ("jeem-ar.init.calt", True),
    ("miniKeheh-ar", False),
    ],
)
def test_hasShape(defcon_ar_font_1, glyphName, expected):
    glyph = defcon_ar_font_1[glyphName]
    assert glyph.hasShape is expected
