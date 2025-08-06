from utils import *
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
    target_glyph.copyContentsFromGlyph(source_glyph)
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

def test_copyContentsFromGlyph(sample_empty_glyph, sample_source_glyph, COPY_GLYPH_KWARGS):
    tmp_layer = defcon.Layer()
    for k, v in COPY_GLYPH_KWARGS.items():
        test_kwargs = dict(COPY_GLYPH_KWARGS)
        test_kwargs[k] = not v
        tmp_g = tmp_layer.instantiateGlyphObject()
        tmp_g.copyContentsFromGlyph(sample_source_glyph, **test_kwargs)
        assert_compared_glyphs_are_same(tmp_g, sample_source_glyph,
            **test_kwargs)

@pytest.fixture(scope='function')
def sample_other_glyph():
    # sample is based on a defcon glyph test
    yield sample_random_glyph(2)

def test_swapGlyphData(sample_source_glyph, sample_other_glyph, COPY_GLYPH_KWARGS):
    base_test_kwargs = dict(COPY_GLYPH_KWARGS.items())
    base_test_kwargs.pop('unicodes') # swap unicodes is not the default behaviour in glyph.swapGlyphData and is discouraged.
    tmp_layer = defcon.Layer()
    for k, v in base_test_kwargs.items():
        test_kwargs = dict(base_test_kwargs)
        test_kwargs[k] = not v
        sample_source_glyph_tmp = tmp_layer.instantiateGlyphObject()
        sample_source_glyph_tmp.copyContentsFromGlyph(sample_source_glyph)
        sample_other_glyph_tmp = tmp_layer.instantiateGlyphObject()
        sample_other_glyph_tmp.copyContentsFromGlyph(sample_other_glyph)
        sample_source_glyph_tmp.swapGlyphData(sample_other_glyph_tmp, **test_kwargs)

        assert_compared_glyphs_are_same(sample_source_glyph, sample_other_glyph_tmp,
            **test_kwargs)
        assert_compared_glyphs_are_same(sample_other_glyph, sample_source_glyph_tmp,
            **test_kwargs)

def test_clearData(sample_source_glyph, sample_empty_glyph, COPY_GLYPH_KWARGS):
    base_test_kwargs = dict(note=True, image=True, contours=True, components=True,
    anchors=True, guidelines=True, lib=True)

    for k, v in base_test_kwargs.items():
        test_kwargs = dict(base_test_kwargs)
        test_kwargs[k] = not v
        test_g = defcon.Glyph()
        test_g.copyContentsFromGlyph(sample_source_glyph, **COPY_GLYPH_KWARGS) # overrding unicodes=False
        test_g.clearData(**test_kwargs)
        assert_compared_glyphs_are_same(test_g, sample_empty_glyph, **test_kwargs)

def test_font_swapGlyphNames(sample_font_with_random_glyph_contents, COPY_GLYPH_KWARGS):
    base_test_kwargs = dict(COPY_GLYPH_KWARGS.items())
    base_test_kwargs.pop('unicodes') # swap unicodes is not the default behaviour in font.swapGlyphNames and is discouraged.

    swap_map = {'random glyph 6': 'random glyph 9', 'random glyph 0': 'random glyph 8'}
    tmp_defcon_font_1 = defcon.Font()
    tmp_defcon_font_1.setDataFromSerialization(sample_font_with_random_glyph_contents.getDataForSerialization())
    sample_font_with_random_glyph_contents.swapGlyphNames(swap_map, **base_test_kwargs)

    for gn1, gn2 in swap_map.items():
        ref_glyph = sample_font_with_random_glyph_contents[gn1]
        other_glyph = tmp_defcon_font_1[gn2]
        assert_compared_glyphs_are_same(ref_glyph, other_glyph, **base_test_kwargs)

MASK_LAYER = 'public.background'
COPY_BACKGROUND_KWARGS = dict(width=True, height=True, image=True, contours=True, components=True,
    anchors=True, guidelines=True, lib=True, note=True)

def test_copyToBackground(sample_font_with_random_glyph_contents):
    font = sample_font_with_random_glyph_contents
    glyph_name = 'random glyph 6'
    glyph = font[glyph_name]

    assert MASK_LAYER not in font.layers
    glyph.copyToBackground(decompose=False)
    # Check if the background layer was created
    assert MASK_LAYER in font.layers
    assert glyph_name in font.layers[MASK_LAYER]
    background_glyph = font.layers[MASK_LAYER][glyph_name]
    assert_compared_glyphs_are_same(background_glyph, glyph, **COPY_BACKGROUND_KWARGS)
    del font.layers[MASK_LAYER]

    # Test copying to background with different args
    for attr, value in COPY_BACKGROUND_KWARGS.items():
        test_kwargs = dict(COPY_BACKGROUND_KWARGS) # testing each arg individually
        test_kwargs[attr] = not value
        glyph.copyToBackground(decompose=False, **test_kwargs)
        background_glyph = font.layers[MASK_LAYER][glyph_name]
        assert_compared_glyphs_are_same(background_glyph, glyph, **test_kwargs)
        # Clear the background layer for the next iteration
        if MASK_LAYER in font.layers:
            del font.layers[MASK_LAYER]
