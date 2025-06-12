from utils import *
from fontgadgets.extensions.layout import Layout

"""
todo:
- more test that includes line width and alignment.
"""
def test_layout_postions(defcon_ar_font_1):
    l = Layout(defcon_ar_font_1)
    assert l.getGlyphNamesAndPositionsFromText('la فا') == [('l', (0, 0)), ('a', (307, 0)), ('.notdef', (860, 0)), ('alef-ar.fina', (1360, 0)), ('feh-ar.init', (1614, 0))]
    assert l.getGlyphNamesAndPositionsFromText('وِ') == [('kasra-ar', (100, -454)), ('waw-ar', (0, 0))]
