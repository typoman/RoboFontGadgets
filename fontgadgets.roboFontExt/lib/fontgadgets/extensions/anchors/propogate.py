from fontgadgets.decorators import font_cached_method
from fontgadgets.extensions.anchors import getAnchorClassFromName, MARK_ANCHOR_PREFIXES
from fontgadgets.log import logger
from functools import lru_cache


"""
todo:
- If a glyph is made from kashida and beh-init, the propogate script should decide which
  base glyph to use for propogate. This means we should at order the base letters
  and decide which one is more likely the base glyph (canela ar had this issue).
- If a base glyph for a composite is not a ligature but you see a numbered
  anchor, throw warning
- throw warning for glyphs that have duplicate anchors
"""

SKIP_PREFIXES = '*', # skip these prefixes in propogating

@lru_cache
def ـoneNameInIterableStartsWithPrefixesBasedOnCondition(anchorNames: tuple, prefixes: tuple, reverseCondition: bool = False):
    """
    If any anchor name starts with one of the given prefixes, return True

    # Example 1: Anchor name starts with one of the prefixes
    >>> anchorNames = ("top_1", "_top")
    >>> anchorNames2 = ("top", "top_1")

    # at least one anchor should start with given prefixes
    >>> ـoneNameInIterableStartsWithPrefixesBasedOnCondition(anchorNames, MARK_ANCHOR_PREFIXES)
    True

    >>> ـoneNameInIterableStartsWithPrefixesBasedOnCondition(anchorNames2, MARK_ANCHOR_PREFIXES)
    False

    # no anchor should't start with given prefixes
    >>> ـoneNameInIterableStartsWithPrefixesBasedOnCondition(anchorNames, MARK_ANCHOR_PREFIXES, True)
    True

    >>> ـoneNameInIterableStartsWithPrefixesBasedOnCondition(anchorNames2, MARK_ANCHOR_PREFIXES, True)
    True
    """
    for p in prefixes:
        for a in anchorNames:
            if a.startswith(p) is not reverseCondition:
                # By default if any name has a prefix that matches any of the
                # prefixes, returns True. If reverseCondition is True, and any
                # name doesn't start with any of the prefixes, returns True.
                return True
    return False

def oneNameInIterableStartsWithPrefixes(anchorNames: tuple, prefixes: tuple):
    """
    If any anchor name starts with one of the given prefixes, return True
    """
    return ـoneNameInIterableStartsWithPrefixesBasedOnCondition(anchorNames, prefixes)

def oneNameInIterableDoesntStartWithPrefixes(anchorNames: tuple, prefixes: tuple):
    """
    If any anchor name doesn't start with one of the given prefixes, return True
    """
    return ـoneNameInIterableStartsWithPrefixesBasedOnCondition(anchorNames, prefixes, True)

def _shouldMarkAnchorsPropogateFromComponent(compositeMarkAnchorNames: tuple, componentGlyphAnchorNames: tuple):
    """
    Should this *diacritic* composite anchors propogate from this given componentGlyph?
    `glyph`: composite glyph we want to add anchors by propogating which is a diacritic
    `componentGlyph`: base defcon.Glyph obj of the component inside the `glyph`
    """
    markClass1 = set([getAnchorClassFromName(n) for n in compositeMarkAnchorNames]) # inside the composite
    markClass2 = set([getAnchorClassFromName(n) for n in componentGlyphAnchorNames]) # inside the mark baseGlyph
    if markClass1 and markClass1 & markClass2 == set():
        # no overlap in mark anchor classes (e.g. top vs bottom or dot vs top)
        return False

    if all((oneNameInIterableStartsWithPrefixes(compositeMarkAnchorNames, MARK_ANCHOR_PREFIXES),
            oneNameInIterableDoesntStartWithPrefixes(compositeMarkAnchorNames, MARK_ANCHOR_PREFIXES))):
        # this is a diacritic which already has all the anchors is needed for a
        # mark glyph. Which is at least one prefixed with '_' and also at least
        # one **not** prefixed with '_'.(e.i. don't propogate top anchors from a
        # bottom mark)
        return False

    if oneNameInIterableDoesntStartWithPrefixes(componentGlyphAnchorNames, MARK_ANCHOR_PREFIXES):
        # there is an anchor name inside this component that doesn't start with '_'
        return True
    return False

@lru_cache
def _isLigaComponent(compositeAnchorNames: tuple, componentGlyphAnchorNames: tuple):
    """
    compositeAnchorNames is from the glyph receiving the anchors
    componentGlyphAnchorNames is from the glyph sending the anchors
    """
    ligaAnchorNamePrefixesInsideTheComponent = (f"{name}_" for name in componentGlyphAnchorNames)
    if oneNameInIterableStartsWithPrefixes(compositeAnchorNames, ligaAnchorNamePrefixesInsideTheComponent):
        # this avoids a situation where a ligature is made of a component glyph
        # which has anchors and we don't want the anchors that don't have
        # numbers to come to the ligature (e.g. a ligature has an anchor
        # `top_1`, but should not receive `top`.)
        return True
    return False

@font_cached_method("Glyph.AnchorsChanged", "Glyph.ComponentsChanged", "Component.BaseGlyphChanged")
def getAnchorsToPropagate(glyph, skipPrefixes: tuple = (), skipGlyphNames: tuple = ()):
    """
    skipPrefixes: a list of str. if anchor names start with one of these prefixes don't propogate
    skipGlyphNames: a list of str. if a glyph name is in this list don't propogate
    """
    newMarkAnchors = AnchorsDict()
    newMarkAnchors.glyph = glyph
    newBaseAnchors = AnchorsDict()
    newBaseAnchors.glyph = glyph
    if skipPrefixes == ():
        skipPrefixes = SKIP_PREFIXES
    if glyph.name in skipGlyphNames or not glyph.components:
        return newMarkAnchors
    skipGlyphNames = set(skipGlyphNames)
    skipGlyphNames.add(glyph.name)
    compositeExistingAnchors = AnchorsDict.fromGlyph(glyph)
    font = glyph.font

    # skip existing anchors that are already propogated
    propogatedBefore = AnchorsDict(glyph.lib.get("fontgadgets.anchor.propogate", {}))
    overlap = set(compositeExistingAnchors.keys()) & set(propogatedBefore.keys())
    for name in overlap:
        if compositeExistingAnchors[name] == propogatedBefore[name]:
            # if their position is the same, it means user didn't adjust them we can
            # update them as if they didn't exist
            del compositeExistingAnchors[name]

    # sort components
    for component in glyph.components:
        try:
            baseGlyphOfThisComponent = font[component.baseGlyph]
        except KeyError:
            logger.warning(f"Base glyph {component.baseGlyph} not found in font.")
            continue
        propogatedAnchorsInComponent = AnchorsDict()
        propogatedAnchorsInComponent = getAnchorsToPropagate(baseGlyphOfThisComponent, skipPrefixes=skipPrefixes, skipGlyphNames=tuple(skipGlyphNames))
        propogatedAnchorsInComponent.accumulate(AnchorsDict.fromGlyph(baseGlyphOfThisComponent))

        if _isLigaComponent(compositeExistingAnchors.keys(), propogatedAnchorsInComponent.keys()):
            continue

        transfomedAnchors = propogatedAnchorsInComponent
        transfomedAnchors.transform(component.transformation)
        if baseGlyphOfThisComponent.isMark:
            if _shouldMarkAnchorsPropogateFromComponent(compositeExistingAnchors.keys(), transfomedAnchors.keys()):
                newMarkAnchors.accumulate(transfomedAnchors)
        else:
            newBaseAnchors.accumulate(transfomedAnchors)

    for anchorDict in (newBaseAnchors, newMarkAnchors):
        # remove existing anchors inside the composite from the result
        anchorDict.removeByNames(compositeExistingAnchors)

    if glyph.isMark:
        # for duplicates poses for the same name keep the farthest ones from the
        # center
        newMarkAnchors.removeDuplicatePositionsInFavourOfFarthestFromAGivenPoint(glyph.centerOfBounds)
        return newMarkAnchors
    else:
        if glyph.isLigature:
            newBaseAnchors.overridePositionsByClosestAnchorFromAnotherDict(newMarkAnchors)
        else:
            newBaseAnchors.overridePositions(newMarkAnchors)
            newBaseAnchors.removeDuplicatePositionsInFavourOfFarthestFromAGivenPoint(glyph.centerOfBounds)
        newBaseAnchors.dropPrefixes(skipPrefixes)
        return newBaseAnchors

if __name__ == "__main__":
    import doctest
    doctest.testmod()
