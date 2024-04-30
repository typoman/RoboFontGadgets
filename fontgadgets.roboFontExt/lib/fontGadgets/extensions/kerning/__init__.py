import itertools
from fontgadgets.decorators import *
from fontgadgets.log import logger
import fontgadgets.extensions.groups

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


@font_method
def cleanup(kerning, cleanupGroups=True):
    """
    Cleanup kerning by removing kerning pairs with missing references from glyphs/groups.
    """
    f = kerning.font
    currentKern = dict(f.kerning.items())
    finalKerning = {}
    if cleanupGroups:
        f.groups.cleanup()
    validKerningEntries = f.validKerningEntries  # glyphs or groups that are valid and exist
    missing = set()  # Missing glyphs/groups
    removed = set()  # Kerning pairs to remove

    for pair, value in currentKern.items():
        valid_pair = [g if g in validKerningEntries else None for g in pair]
        missing_entries = set(pair) - set(valid_pair)
        if missing_entries:
            missing.update(missing_entries)
            removed.update([str(pair)])
            continue
        finalKerning[tuple(valid_pair)] = value

    if not removed:
        logger.info('Kerning is not changed!')
        return

    logger.info('Missing glyphs/groups:\n%s' %(' '.join(sorted(missing))))
    logger.info('Removed pairs:\n%s' %(' '.join(sorted(removed))))
    logger.info('Number of dropped kern pairs: %i' %(len(currentKern) - len(finalKerning)))
    f.kerning.clear()
    f.kerning.update(finalKerning)
