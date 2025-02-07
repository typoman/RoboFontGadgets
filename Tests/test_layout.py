from main import *
from fontgadgets.extensions.layout import Layout

def test_layout_postions(defcon_ar_font_1):
    l = Layout(defcon_ar_font_1)
    assert l.getGlyphNamesAndPositionsFromText('la فا') == [('l', (0, 0)), ('a', (307, 0)), ('.notdef', (860, 0)), ('alef-ar.fina', (860, 0)), ('feh-ar.init', (1114, 0))]
    assert l.getGlyphNamesAndPositionsFromText('وِ') == [('kasra-ar', (-326, -454)), ('waw-ar', (-426, 0))]
