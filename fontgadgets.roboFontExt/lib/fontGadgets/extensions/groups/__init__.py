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
