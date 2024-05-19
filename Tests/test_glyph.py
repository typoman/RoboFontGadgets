from main import *
import fontgadgets.extensions.glyph
import operator

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

@pytest.fixture(scope='function')
def copy_source_glyph():
    # sample is taken from defcon glyph test
    source = defcon.Glyph()
    source.name = "a"
    source.width = 1
    source.height = 2
    source.unicodes = [3, 4]
    source.note = "test image"
    source.image = dict(fileName="test image", xScale=1, xyScale=1,
                        yxScale=1, yScale=1, xOffset=0, yOffset=0,
                        color=None)
    source.anchors = [dict(x=100, y=200, name="test anchor")]
    source.guidelines = [dict(x=10, y=20, name="test guideline")]
    source.lib = {"foo": "bar"}
    pen = source.getPointPen()
    pen.beginPath()
    pen.addPoint((100, 200), segmentType="line")
    pen.addPoint((300, 400), segmentType="line")
    pen.endPath()
    component = defcon.Component()
    component.base = "b"
    source.appendComponent(component)
    yield source


@pytest.fixture(scope='function')
def copy_target_glyph():
    target = defcon.Glyph()
    yield target

def _contour_points_as_list(glyph):
    result = []
    for contour in glyph:
        result.append([])
        for point in contour:
            result[-1].append((point.x, point.x,
                point.segmentType, point.name))
    return result

def _get_operator(condition):
    # Returns the equality operator (==) if condition is True, and the
    # inequality operator (!=) if condition is False. This allows for dynamic
    # switching between equality and inequality checks.
    _operator = operator.eq if condition else operator.ne
    return _operator

def assert_changed_only(copy_target_glyph, copy_source_glyph, width=False,
                     height=False, unicodes=False, note=False, image=False, contours=False,
                     components=False, anchors=False, guidelines=False, lib=False):
    # Assert that the attributes of copy_target_glyph are not changed
    # from copy_source_glyph, except for the specified attributes.
    assert _get_operator(width)(copy_target_glyph.width, copy_source_glyph.width)
    assert _get_operator(height)(copy_target_glyph.height, copy_source_glyph.height)
    assert _get_operator(unicodes)(copy_target_glyph.unicodes, copy_source_glyph.unicodes)
    assert _get_operator(note)(copy_target_glyph.note, copy_source_glyph.note)
    assert _get_operator(image)(copy_target_glyph.image, copy_source_glyph.image)
    sourceContours = _contour_points_as_list(copy_source_glyph)
    targetContours = _contour_points_as_list(copy_target_glyph)
    assert _get_operator(contours)(sourceContours, targetContours)
    assert _get_operator(components)(len(copy_target_glyph.components), len(copy_source_glyph.components))
    assert _get_operator(anchors)([g.items() for g in copy_target_glyph.anchors], [g.items() for g in copy_source_glyph.anchors])
    assert _get_operator(guidelines)([g.items() for g in copy_target_glyph.guidelines], [g.items() for g in copy_source_glyph.guidelines])
    assert _get_operator(lib)(copy_target_glyph.lib, copy_source_glyph.lib)

def test_copy_width(copy_target_glyph, copy_source_glyph):
    copy_target_glyph.copyFromGlyph(
        copy_source_glyph, width=True, height=False, unicodes=False, note=False,
        image=False, contours=False, components=False, anchors=False,
        guidelines=False, lib=False)
    assert_changed_only(copy_target_glyph, copy_source_glyph, width=True)

def test_copy_height(copy_target_glyph, copy_source_glyph):
    copy_target_glyph.copyFromGlyph(
        copy_source_glyph, width=False, height=True, unicodes=False, note=False,
        image=False, contours=False, components=False, anchors=False,
        guidelines=False, lib=False)
    assert_changed_only(copy_target_glyph, copy_source_glyph, height=True)

def test_copy_unicodes(copy_target_glyph, copy_source_glyph):
    copy_target_glyph.copyFromGlyph(
        copy_source_glyph, width=False, height=False, unicodes=True, note=False,
        image=False, contours=False, components=False, anchors=False,
        guidelines=False, lib=False)
    assert_changed_only(copy_target_glyph, copy_source_glyph, unicodes=True)

def test_copy_note(copy_target_glyph, copy_source_glyph):
    copy_target_glyph.copyFromGlyph(
        copy_source_glyph, width=False, height=False, unicodes=False, note=True,
        image=False, contours=False, components=False, anchors=False,
        guidelines=False, lib=False)
    assert_changed_only(copy_target_glyph, copy_source_glyph, note=True)

def test_copy_image(copy_target_glyph, copy_source_glyph):
    copy_target_glyph.copyFromGlyph(
        copy_source_glyph, width=False, height=False, unicodes=False, note=False,
        image=True, contours=False, components=False, anchors=False,
        guidelines=False, lib=False)
    assert_changed_only(copy_target_glyph, copy_source_glyph, image=True)

def test_copy_contours(copy_target_glyph, copy_source_glyph):
    copy_target_glyph.copyFromGlyph(
        copy_source_glyph, width=False, height=False, unicodes=False, note=False,
        image=False, contours=True, components=False, anchors=False,
        guidelines=False, lib=False)
    assert_changed_only(copy_target_glyph, copy_source_glyph, contours=True)

def test_copy_components(copy_target_glyph, copy_source_glyph):
    copy_target_glyph.copyFromGlyph(
        copy_source_glyph, width=False, height=False, unicodes=False, note=False,
        image=False, contours=False, components=True, anchors=False,
        guidelines=False, lib=False)
    assert_changed_only(copy_target_glyph, copy_source_glyph, components=True)

def test_copy_anchors(copy_target_glyph, copy_source_glyph):
    copy_target_glyph.copyFromGlyph(
        copy_source_glyph, width=False, height=False, unicodes=False, note=False,
        image=False, contours=False, components=False, anchors=True,
        guidelines=False, lib=False)
    assert_changed_only(copy_target_glyph, copy_source_glyph, anchors=True)

def test_copy_guidelines(copy_target_glyph, copy_source_glyph):
    copy_target_glyph.copyFromGlyph(
        copy_source_glyph, width=False, height=False, unicodes=False, note=False,
        image=False, contours=False, components=False, anchors=False,
        guidelines=True, lib=False)
    assert_changed_only(copy_target_glyph, copy_source_glyph, guidelines=True)

def test_copy_lib(copy_target_glyph, copy_source_glyph):
    copy_target_glyph.copyFromGlyph(
        copy_source_glyph, width=False, height=False, unicodes=False, note=False,
        image=False, contours=False, components=False, anchors=False,
        guidelines=False, lib=True)
    assert_changed_only(copy_target_glyph, copy_source_glyph, lib=True)
