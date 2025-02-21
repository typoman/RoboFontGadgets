from utils import *

def test_random_glyph(COPY_GLYPH_KWARGS):
    g1 = sample_random_glyph(10)
    g2 = sample_random_glyph(10)
    assert_compared_glyphs_are_same(g1, g2, **COPY_GLYPH_KWARGS)
    g3 = sample_random_glyph(12)
    assert_compared_glyphs_are_same(g1, g3)
