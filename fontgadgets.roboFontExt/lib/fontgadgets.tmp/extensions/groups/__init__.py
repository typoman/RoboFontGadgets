from fontgadgets.decorators import *
from fontgadgets.log import logger

@font_method
def cleanup(groups):
    """
    Cleanup groups by removing empty groups or missing glyph references from groups.
    """
    f = groups.font
    currentGroups = dict(f.groups.items())
    finalGroups = {}
    empty = set()
    missing = set()

    for groupName, groupMembers in currentGroups.items():
        members = [g for g in groupMembers if g in f]
        if members:
            finalGroups[groupName] = members
        else:
            empty.add(groupName)
        missingGlyphs = set(groupMembers) - set(members)
        if missingGlyphs:
            missing.update(missingGlyphs)

    if finalGroups == currentGroups:
        logger.info('No groups has been changed!')
        return

    if empty:
        logger.info('Removed empty groups:\n%s' %(' '.join(sorted(empty))))

    if missing:
        logger.info('Missing glyphs:\n%s' %(' '.join(sorted(missing))))

    f.groups.clear()
    f.groups.update(finalGroups)
    logger.info('Number of dropped groups: %i' %(len(currentGroups) - len(finalGroups)))

@font_method
def removeGlyphs(groups, glyphNamesToRemove, cleanup=True):
    """
    Remove all the given glyphNamesToRemove from the groups.
    cleanup: cleanup empty groups after removing glyphs
    """
    f = groups.font
    originalGroups = dict(groups.items())
    finalGroups = {}
    glyphNamesToRemove = set(glyphNamesToRemove)  # glyph names to remove them from groups

    for groupName in originalGroups:
        members = originalGroups[groupName]
        newMembers = set(members) - glyphNamesToRemove
        finalGroups[groupName] = tuple(sorted(newMembers, key=lambda g: members.index(g)))
    f.groups.clear()
    f.groups.update(finalGroups)
    if cleanup:
        groups.cleanup(groups)
