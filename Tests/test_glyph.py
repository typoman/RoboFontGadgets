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
    target_glyph.copyAttributesFromGlyph(source_glyph)
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

@pytest.fixture(scope='function')
def sample_source_glyph():
    # sample is taken from defcon glyph test
    yield sample_random_glyph(1)

@pytest.fixture(scope='function')
def sample_empty_glyph():
    layer = defcon.Layer()
    target = layer.instantiateGlyphObject()
    yield target

def test_copyAttributesFromGlyph(sample_empty_glyph, sample_source_glyph, COPY_GLYPH_KWARGS):
    tmp_layer = defcon.Layer()
    for k, v in COPY_GLYPH_KWARGS.items():
        test_kwargs = dict(COPY_GLYPH_KWARGS)
        test_kwargs[k] = not v
        tmp_g = tmp_layer.instantiateGlyphObject()
        tmp_g.copyAttributesFromGlyph(sample_source_glyph, **test_kwargs)
        assert_compared_glyphs_are_same(tmp_g, sample_source_glyph,
            **test_kwargs)

@pytest.fixture(scope='function')
def sample_other_glyph():
    # sample is based on a defcon glyph test
    yield sample_random_glyph(2)

def test_swapGlyphData(sample_source_glyph, sample_other_glyph, COPY_GLYPH_KWARGS):
    tmp_layer = defcon.Layer()
    for k, v in COPY_GLYPH_KWARGS.items():
        test_kwargs = dict(COPY_GLYPH_KWARGS)
        test_kwargs[k] = not v
        sample_source_glyph_tmp = tmp_layer.instantiateGlyphObject()
        sample_source_glyph_tmp.copyAttributesFromGlyph(sample_source_glyph)
        sample_other_glyph_tmp = tmp_layer.instantiateGlyphObject()
        sample_other_glyph_tmp.copyAttributesFromGlyph(sample_other_glyph)
        sample_source_glyph_tmp.swapGlyphData(sample_other_glyph_tmp, **test_kwargs)

        assert_compared_glyphs_are_same(sample_source_glyph, sample_other_glyph_tmp,
            **test_kwargs)
        assert_compared_glyphs_are_same(sample_other_glyph, sample_source_glyph_tmp,
            **test_kwargs)

def test_clearData(sample_source_glyph, sample_empty_glyph):
    kwargs = dict(unicodes=True, note=True, image=True, contours=True, components=True,
            anchors=True, guidelines=True, lib=True)
    for k, v in kwargs.items():
        test_kwargs = dict(kwargs)
        test_kwargs[k] = not v
        test_g = defcon.Glyph()
        test_g.copyAttributesFromGlyph(sample_source_glyph)
        test_g.clearData(**test_kwargs)
        assert_compared_glyphs_are_same(test_g, sample_empty_glyph, **test_kwargs)

def test_font_swapGlyphNames(sample_font_with_random_glyph_contents, COPY_GLYPH_KWARGS):
    swap_map = {'random glyph 6': 'random glyph 9', 'random glyph 0': 'random glyph 8'}
    tmp_defcon_font_1 = defcon.Font()
    tmp_defcon_font_1.setDataFromSerialization(sample_font_with_random_glyph_contents.getDataForSerialization())
    sample_font_with_random_glyph_contents.swapGlyphNames(swap_map)

    # revserse_sawp_map
    swap_map.update({v: k for k, v in swap_map.items()})
    for gn1, gn2 in swap_map.items():
        ref_glyph = sample_font_with_random_glyph_contents[gn1]
        other_glyph = tmp_defcon_font_1[gn2]
        assert_compared_glyphs_are_same(ref_glyph, other_glyph, **COPY_GLYPH_KWARGS)
