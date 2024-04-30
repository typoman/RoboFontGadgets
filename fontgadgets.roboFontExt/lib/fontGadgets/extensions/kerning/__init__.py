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

@font_method
def removeGlyphs(kerning, glyphNamesToRemove, pruneGroups=False, cleanup=True):
    """
    Remove all kerning pairs which reference the given glyphNamesToRemove.
    pruneGroups: If True, remove the given glyphNamesToRemove from groups. This will automatically remove them from kerning.
    cleanup: If True, remove empty groups and invalid kerning pairs at the end.
    """
    f = kerning.font
    if pruneGroups:
        f.groups.removeGlyphs(glyphNamesToRemove, cleanup=False)
    groups = dict(f.groups)
    originalKerning = dict(f.kerning.items())
    finalKerning = {}
    glyphNamesToRemove = set(glyphNamesToRemove) # glyph names to remove them from groups or kerning

    for originalPair, value in originalKerning.items():
        newPair = [e for e in originalPair if e in glyphNamesToRemove]
        if len(newPair) == 2:
            logger.info(f"The kerning pair '{newPair}' has been removed.")
        elif len(newPair) == 1:
            glyphs = groups.get(newPair[0], [newPair[0]])
            logger.info(f"These glyphs are kerned next to a glyph that are being removed from kerning:\n{' '.join(glyphs)}")
        else:
            finalKerning[originalPair] = value

    f.kerning.clear()
    f.kerning.update(finalKerning)
    if cleanup:
        f.kerning.cleanup()
