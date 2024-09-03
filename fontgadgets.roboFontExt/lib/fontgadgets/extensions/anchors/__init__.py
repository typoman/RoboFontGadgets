from fontgadgets.log import logger
import defcon
from fontgadgets.decorators import font_cached_property
from fontgadgets.extensions.point.__int__ import distance
import fontgadgets.extensions.glyph.type
from fontTools.misc.transform import Transform
from fontgadgets import FontGadgetsError
from functools import lru_cache
import re


"""
todo:
- propogateAnchors method:
    - write the propogated anchros position inside the glyph.lib or anchor.lib
      and if the positions, has changed don't update the anchor position. This is
      used to check if an anchor has been moved manualy *after* the propogation
      the new position should not be overriden. Otherwise update their positions.
"""

MARK_ANCHOR_PREFIX = "_"
MARK_ANCHOR_PREFIXES = MARK_ANCHOR_PREFIX, # mark anchors commonly have these prefixes
MAX_DISTANCE = float('inf')


class AnchorsDict(dict):
    """
    A dictionary that keeps the anchors data for a glyph and takes care of
    tranforming or dropping the data in form of {anchor.name: ((x, y), ...)}.
    This is more efficent and easier to maintain than modify the defcon.Anchor
    class.
    """

    @staticmethod
    def fromGlyph(glyph):
        """
        Creates an AnchorsDict instance from the anchors in the given glyph.
        """
        assert isinstance(glyph, defcon.Glyph), f"`fromGlyph` method takes a `defcon.Glyph` instance, got {type(glyph)}"
        result = AnchorsDict()
        result._glyph = glyph
        result.importFromGlyph()
        return result

    def _set_glyph(self, glyph):
        if getattr(self, '_glyph', None) is glyph:
            return
        if hasattr(self, '_glyph') and self.items():
            logger.warning(f"Clearing anchors before setting new glyph in {glyph.name}.")
            self._clear()
        self._glyph = glyph
        self._glyph

    def _get_glyph(self):
        return self._glyph

    glyph = property(_get_glyph, _set_glyph)

    def accumulate(self, other):
        """
        Adds all the anchors in from the given dictionary.
        """
        for name, poses in other.items():
            existing = set(self.get(name, ()))
            existing.update(poses)
            self[name] = tuple(existing)

    def overridePositions(self, other):
        """
        If a name in `other` exists in `self`, it will be overridden.
        """
        for name, poses in other.items():
            if name in self:
                self[name] = poses

    def keys(self):
        # we using a tuple instead of generators, because tuples are hashable
        return tuple(super().keys())

    def values(self):
        return tuple(super().values())

    def items(self):
        return tuple(super().items())

    def copy(self):
        result = AnchorsDict(super().copy())
        result._glyph = self._glyph
        return result

    def removeByNames(self, names):
        """
        Remove all the anchors with the given names.
        """
        oldItems = self.items()
        self.clear()
        for name, poses in oldItems:
            if name not in names:
                self[name] = poses

    def dropPrefixes(self, prefixes):
        """
        Drop all the anchors which their names start with any of the given prefixes.
        """
        oldItems = self.items()
        self.clear()
        for name, poses in oldItems:
            if any([name.startswith(prefix) for prefix in prefixes]):
                continue
            self[name] = poses

    def transform(self, transformation: tuple):
        """
        Transforms all the anchors positions with the given transformation affine matrix.
        """
        oldItems = self.items()
        self.clear()
        transformPointFunct = Transform(*transformation).transformPoint
        for name, poses in oldItems:
            self[name] = tuple([transformPointFunct(p) for p in poses])

    def addToGlyph(self):
        """
        Add the anchors from the dict to the glyph.
        """
        for name, positions in self.items():
            if len(positions) > 1:
                logger.warning(f"Anchor {name} in {self.glyph.name} has more than one position, taking only the first.")
            x, y = positions[0]
            an = dict(name=name, x=x, y=y)
            self._glyph.instantiateAnchor(an)
            self._glyph.appendAnchor(an)

    def importFromGlyph(self):
        """
        Import the anchors from the glyph.
        """
        for a in self._glyph.anchors:
            existing = set(self.get(a.name, set()))
            pos = (a.x, a.y)
            if pos in existing:
                logger.warning(f"Anchor {a.name} in {self.glyph.name} has a duplicate with same position, skipping.")
                continue
            existing.add((a.x, a.y))
            self[a.name] = tuple(existing)

    def overridePositionsByClosestAnchorFromAnotherDict(self, another: dict):
        """
        Overrides positions of anchors in the current dict from the given
        another dict by getting the closest anchor that has the same base name.
        For example if current dict has `top_1` and `top_2` anchors with
        different positions, and `another` dict has `top` and `_top` anchros;
        this method will override the position of `top_1` or `top_2` depending on
        which one is closer to the given `top` anchor from the 'another' dict.

        Args:
        another (dict): A dictionary of anchor names and their
        positions.
        """

        # This function is used when a ligature has a diacritic anchor, and its
        # position should come from the diacritic glyph rather than the base
        # glyph. During anchor propagation, first, the base anchors are
        # propagated, and then the diacritic anchors are propagated. This
        # method overrides the positions of the base anchors by finding the
        # closest anchor from the 'another' dictionary, which usually contains
        # new mark anchors. For example, if the base anchor is 'top_1' and
        # the 'another' dictionary has '_top' and 'top', the position
        # of 'top_1' will be overridden from the closest position of 'top' from
        # the given 'another' dictionary.

        overlappingNames = set([name for name in self if name.split("_")[0] in another])

        anotherMarkItems = another.items()

        for anotherMarkName, anotherMarkPoses in anotherMarkItems:
            # skip diacritic anchors
            if anotherMarkName.startswith(MARK_ANCHOR_PREFIX):
                continue

            for anotherpos in anotherMarkPoses:
                closestName, _ = self.getClosestAnchorToPoint(anotherpos, overlappingNames)
                self[closestName] = anotherpos,

    def getClosestAnchorToPoint(self, point: tuple, filterToNames: list | set | tuple = None):
        """
        Returns the name and positions of the closest anchor to the given point.
        `filterToNames` can be a list of anchor names or a set of names that will
        be ckecked and other anchor names will be ignored.
        """
        items = self.items()
        if filterToNames is not None:
            items = [(n, p) for n, p in items if n in filterToNames]
        lastMinDistance = MAX_DISTANCE
        nameAndPose = None, None
        for name, poses in items:
            allDistances = {distance(p, point): p for p in poses}
            minDistance = min(allDistances)
            if minDistance < lastMinDistance:
                nameAndPose = name, allDistances[minDistance]
                lastMinDistance = minDistance
        return nameAndPose

    def removeDuplicatePositionsInFavourOfFarthestFromAGivenPoint(self, point: tuple):
        """
        If an anchor name has mutliple positions, typically the anchros we want
        to keep are the ones that are farhter from the center a of glyph
        shape.
        """
        oldItems = self.items()
        self.clear()
        for name, poses in oldItems:
            if len(poses) == 1:
                self[name] = poses
                continue
            distances = {distance(p, point): p for p in poses}
            farthest = distances[max(distances.keys())]
            self[name] = farthest,

    def ligatureAnchors(self):
        """
        Returns a new anchor dict that contains only the anchors that are
        ligature anchors.
        """
        result = AnchorsDict()
        for name, pos in self.items():
            if name[-1].isdigit():
                result[name] = pos
        result._glyph = self.glyph
        return result


@font_cached_property("Glyph.AnchorsChanged")
def anchorsDict(glyph):
    """
    Returns a dictionary of {anchorName: (pos1, pos2, ...)}
    """
    return AnchorsDict.fromGlyph(glyph)

def getAnchorClassFromName(name: str):
    """
    >>> getAnchorClassFromName('ogonek')
    'ogonek'
    >>> getAnchorClassFromName('_center')
    'center'
    >>> getAnchorClassFromName('*exit')
    'exit'
    >>> getAnchorClassFromName('#exit')
    'exit'
    >>> getAnchorClassFromName('_sindot')
    'sindot'
    >>> getAnchorClassFromName('top_4')
    'top'
    >>> getAnchorClassFromName('bottom-y')
    'bottom'
    >>> getAnchorClassFromName('_kafbar_')
    'kafbar'
    >>> getAnchorClassFromName('***')
    Traceback (most recent call last):
    ...
    fontgadgets.tools.FontGadgetsError: Anchor name *** has no alphabetic characters
    >>> getAnchorClassFromName('123')
    Traceback (most recent call last):
    ...
    fontgadgets.tools.FontGadgetsError: Anchor name 123 has no alphabetic characters
    """
    for substring in re.split(r'[^a-zA-Z]+', name):
        if substring != '':
            return substring
    raise FontGadgetsError(f"Anchor name {name} has no alphabetic characters")

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

def _filterLigatureAnchors(anchros):
    result = {}
    for name, pos in anchros.items():
        if name[-1].isdigit():
            result[name] = pos
    return result

if __name__ == "__main__":
    import doctest
    doctest.testmod()

