from main import *
import fontgadgets.extensions.font.scale as _scale

def test_swapGlyphNames_normal(kerning_with_missing_glyphs):
    swap_map = {'A': 'B', 'C': 'D'}
    old_kerning = dict(kerning_with_missing_glyphs.kerning)
    kerning_with_missing_glyphs.swapGlyphNames(swap_map)

    # Assert that kerning pairs have been swapped:
    assert kerning_with_missing_glyphs.kerning.get(("D", "C")) == old_kerning.get(("C", "D"))
    assert kerning_with_missing_glyphs.kerning.get(("E", "missing_glyph")) == old_kerning.get(("E", "missing_glyph"))
    assert kerning_with_missing_glyphs.kerning.get(("missing_glyph", "B")) == old_kerning.get(("missing_glyph", "A"))

    # # Assert that groups have been swapped:
    assert set(kerning_with_missing_glyphs.groups["group1"]) == {'B', 'A', 'D'}
    assert set(kerning_with_missing_glyphs.groups["group2"]) == {'C', 'E'}
    assert set(kerning_with_missing_glyphs.groups["empty_group"]) == set()
    assert set(kerning_with_missing_glyphs.groups["group_with_missing_glyph"]) == {'B', 'missing_glyph'}

def test_swapGlyphNames_mssingName(kerning_with_missing_glyphs):
    swap_map = {'A': 'X'}
    kerning_with_missing_glyphs.kerning.clear()

    with pytest.raises(FontGadgetsError):
        kerning_with_missing_glyphs.swapGlyphNames(swap_map)
