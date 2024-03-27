import itertools
from fontgadgets.decorators import *
"""
get/set Kerning pairs per glyph basis. Makes it easy for transfering kerning from one font to another.
"""

@font_method
def flattenPair(kerning, pair):
    """
    Flatten a kerning pair from group kerning to glyph kerning. Returns a list.
    """
    groups = kerning.font.groups
    left, right = pair
    leftGlyphs = groups.get(left, [left])
    rightGlyphs = groups.get(right, [right])
    return list(itertools.product(leftGlyphs, rightGlyphs))


@font_method
def isKerningPairValid(kerning, pair):
    """
    Returns `False` if kerning pair contains a missing glyph/group
    """
    for entry in pair:
        if entry not in kerning.font.validKerningEntries:
            return False
    return True


@font_cached_property("Groups.Changed", "Layer.GlyphAdded", "Layer.GlyphDeleted")
def validKerningEntries(font):
    return set(font.keys()) | set(font.groups.keys())
