from utils import *
import fontgadgets.extensions.glyph.scale
from fontTools.misc.roundTools import otRound

def test_scale_glyph():
    glyph = sample_random_glyph(42)
    factor = 0.5
    glyph.scale(factor)
    assert glyph.width == 41
    contour0_values = [(-30, -22), (-37, -38), (-38, -4), (27, -16), (43, 9), (-2, -40), (30, 29)]
    for i, contour in enumerate(glyph):
        if i == 0:
            for j, point in enumerate(contour):
                assert (point.x, point.y) == contour0_values[j]
    anchors_values = [(-47, 22), (-25, 42), (33, 40), (20, 4), (-22, 7)]
    for i, anchor in enumerate(glyph.anchors):
        assert (anchor.x, anchor.y) == anchors_values[i]
    guidelines_values = [-14 , -49 , 47 , -30 , 39]
    for i, guideline in enumerate(glyph.guidelines):
        assert guideline.x == guidelines_values[i]
    components_values = [(-40, -20), (-5, -23), (-28, 18)]
    for i, c in enumerate(glyph.components):
        assert (c.transformation[4], c.transformation[5]) == components_values[i]

def test_scale_glyph_no_round():
    glyph = sample_random_glyph(43)
    factor = 0.5
    glyph.scale(factor, round_values=False)
    assert glyph.width == 2.5
    contours_values = [(23.5, -27.0), (-42.0, -44.0), (-26.5, -42.5), (-12.5,-15.0),
                      (16.5, 29.5), (24.5, 33.5), (-38.0, 29.5), (32.5, 42.5)]
    k = 0
    for i, contour in enumerate(glyph):
        for j, point in enumerate(contour):
            if k < len(contours_values):
                assert (point.x, point.y) == contours_values[k]
                k+=1
    anchors_values = [(0, -27.5), (-43.0, -36.5), (-34.5, -2.0), (-30.5, -38.0)]
    for i, anchor in enumerate(glyph.anchors):
        assert (anchor.x, anchor.y) == anchors_values[i]
    guidelines_values = [15.5, 13.0]
    for i, guideline in enumerate(glyph.guidelines):
        assert guideline.x == guidelines_values[i]
    components_values = [(49.5, -9.5), (-41.0, 20.5), (41.5, 5.5)]
    for i, c in enumerate(glyph.components):
        assert (c.transformation[4], c.transformation[5]) == components_values[i]
