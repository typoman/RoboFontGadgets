from main import *
import fontgadgets.extensions.unicode.properties

def test_unicodeDirectionForGlyphNames(defcon_font_1):
    # Define some example input data
    glyph_names_rtl = ["seen", "sad", "tah", "seen.init"]
    glyph_names_ltr = ["C", "Ccedilla", "D", "O", "Ograve"]

    # Test case 1: All glyph names are LTR
    assert defcon_font_1.unicodeDirectionForGlyphNames(glyph_names_ltr) == "ltr"

    # Test case 2: All glyph names are RTL
    assert defcon_font_1.unicodeDirectionForGlyphNames(glyph_names_rtl) == "rtl"

    # Test case 3: Glyph names have mixed direction
    glyph_names_mixed = glyph_names_ltr + glyph_names_rtl
    assert defcon_font_1.unicodeDirectionForGlyphNames(glyph_names_mixed) is None

def test_isGlyphSetRTL(defcon_font_1):
    assert defcon_font_1.unicodeDirectionForGlyphNames(["seen", "seen.init"]) == "rtl"
    assert defcon_font_1.unicodeDirectionForGlyphNames(["C", "O"]) == "ltr"
    assert defcon_font_1.unicodeDirectionForGlyphNames(["C", "O", "seen"]) is None


def test_isGlyphRTL(defcon_font_1):
    assert defcon_font_1["seen"].unicodeDirection == "rtl"
    assert defcon_font_1["C"].unicodeDirection == "ltr"
    defcon_font_1.newGlyph("abc")
    assert defcon_font_1["abc"].unicodeDirection is None
