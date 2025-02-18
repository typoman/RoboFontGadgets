from main import *
import fontgadgets.extensions.glyph.scale
from fontTools.misc.roundTools import otRound

def test_scale_glyph():
    glyph = sample_random_glyph(42)
    factor = 0.5
    glyph.scale(factor)
    assert glyph.width == 41
    for i, contour in enumerate(glyph):
        for j, point in enumerate(contour):
            expected = ((-1, -38), (-6, 27), (-44, 43))[j]
            assert (point.x, point.y) == expected
    anchors_values = [(-47, 22), (-25, 42), (33, 40), (20, 4), (-22, 7)]
    for i, anchor in enumerate(glyph.anchors):
        assert (anchor.x, anchor.y) == anchors_values[i]
    guidelines_values = [(-14, -49), (47, -30), (39, 4), (-6, -14), (-30, -22)]
    for i, guideline in enumerate(glyph.guidelines):
        assert (guideline.x, guideline.y) == guidelines_values[i]
    components_values = [(30, 29), (-13, -40), (-29, -3), (28, 31)]
    for i, c in enumerate(glyph.components):
        assert (c.transformation[4], c.transformation[5]) == components_values[i]


def test_scale_glyph_no_round():
    glyph = sample_random_glyph(43)
    factor = 0.5
    glyph.scale(factor, round_values=False)
    assert glyph.width == 2.5
    contours_values = [(23.5, -27.0), (-42.0, -44.0), (-42.5, -26.5), (-29.0, -12.5), (-40.5, 16.5), (-37.0, 24.5),
                       (33.0, 36.5), (-38.0, 29.5), (32.5, 42.5), (-8.0, 17.5)]
    for i, contour in enumerate(glyph):
        for j, point in enumerate(contour):
            if j < len(contours_values):
                assert (point.x, point.y) == contours_values[j]
    anchors_values = [(0, -27.5), (-43.0, -36.5), (-34.5, -2.0), (-30.5, -38.0)]
    for i, anchor in enumerate(glyph.anchors):
        assert (anchor.x, anchor.y) == anchors_values[i]
    guidelines_values = [(15.5, 13.0), (-34.0, 48.5)]
    for i, guideline in enumerate(glyph.guidelines):
        assert (guideline.x, guideline.y) == guidelines_values[i]
    components_values = [(-16.0, -3.0), (-35.5, -12.0), (10.5, 3.0), (43.5, -30.5)]
    for i, c in enumerate(glyph.components):
        assert (c.transformation[4], c.transformation[5]) == components_values[i]
