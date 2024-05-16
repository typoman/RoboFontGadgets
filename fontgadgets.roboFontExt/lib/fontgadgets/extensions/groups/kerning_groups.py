from fontgadgets.decorators import *
import fontgadgets.extensions.unicode.properties
import re
from warnings import warn

RE_GROUP_TAG = re.compile(r"public.kern[12]\.")
GROUP_SIDE_TAG = ("public.kern1.", "public.kern2.")
ORDER_2_SIDE = {0: "left", 1: "right"}
SIDE_2_ORDER = {"left": 0, "right": 1}


def isKerningGroup(entry):
    """
    Return True if the given entry is a kerning group name starting either with
    `public.kern1.` or `public.kern2.`
    """
    if entry is None:
        return False
    if re.match(RE_GROUP_TAG, entry) is None:
        return False
    return True


def getGroupSideNameFromGroupOrder(order, RTL):
    """
    Returns `right` or `left` depending on what order the group is defined in
    UFO 3 format.
    RTl argument should be True or False.
    """
    assert isinstance(RTL, bool)
    if RTL is False:
        order = abs(order - 1)
    return ORDER_2_SIDE[order]


def getGroupOrderFromGroupSideName(side, RTL):
    """
    Returns `0` or `1` depending on which side the group is going to be defined.
    RTl argument should be True or False.
    """
    assert side in ("left", "right")
    assert isinstance(RTL, bool)
    order = SIDE_2_ORDER[side]
    if RTL is False:
        order = abs(order - 1)
    return order


class KerningGroups:
    """
    Kerning group names don't contain the `public.kern1.` or `public.kern2.`
    prefix tags. They're defined based on which visual side of the glyph
    they're grouped, `left` or `right` side.
    """

    # An object that gets destroyed every time font.groups change. This is used
    # for changing kerning groups of the font.

    def __init__(self, groups):
        self.groups = groups
        self.font = self.groups.font
        self._glyphToKerningGroupMapping = {} # {"glyphName": {"left": kerningGroupName, "right": kerningGroupName}, ...}
        self._items = None # {"left": {kerningGroupsName: [glyphName1, glyphName2]}, "right": {kerningGroupsName: [glyphName1, glyphName2]}}
        self._kerningGroupName2PrefixedGroupName = {"right": {}, "left": {}} # {"right": {"kerningGroupName1": "public.kern1.kerningGroupName1", ...}
        self.convertPrefixedGroupsToKerningGroups()

    def convertPrefixedGroupsToKerningGroups(self):
        """
        GlyphName to raw group name mapping. The groups are filtered so only
        kerning groups are returned.
        """
        self._glyphToKerningGroupMapping = {}
        self._items = {"left": {}, "right": {}}
        for group, members in self.groups.items():
            if isKerningGroup(group):
                for glyphName in members:
                    sideAndName = self._getSideAndRawGroupName(group)
                    if sideAndName is not None:
                        side, name = sideAndName
                        self._glyphToKerningGroupMapping.setdefault(glyphName, {})[side] = name
                        self._kerningGroupName2PrefixedGroupName[side][name] = group
                        self._items[side].setdefault(name, []).append(glyphName)

    @property
    def glyphToKerningGroupMapping(self):
        """
        Returns a dict that has glyph names as keys and values are kerning group
        names in the follwing format. Kerning groups does contain the
        `public.kern1.` or `public.kern2.` prefix tags.

        format:
        {
            'glyphName1': {
                'left': 'kerningGroupName1',
                'right': 'kerningGroupName2'
            }
            'glyphName2': {
                'left': 'kerningGroupName2',
                'right': None
            }
            ...
        }
        """
        if self._items is None:
            self.convertPrefixedGroupsToKerningGroups()
        return self._glyphToKerningGroupMapping

    def items(self):
        """
        Returns a dict that has only two keys, `left` and `right`. Values
        are kerning groups for that side. Kerning groups does contain the
        `public.kern1.` or `public.kern2.` prefix tags.

        format:
        {
        "left": {
            'kerningGroupName1':
                    ['glyphName1', 'glyphName2']
                },
        "right": {
            'kerningGroupName2':
                    ['glyphName1']
                }
        }
        """
        if self._items is None:
            self.convertPrefixedGroupsToKerningGroups()
        return self._items

    def set(self, kerningGroups, update=False):
        """
        Sets the kerning groups to the given one. If update is set to True, the
        old groups will be extended instead of getting removed or reset.
        Returns True if groups have been changed.
        """
        changed = False
        self.groups.holdNotifications(
            note="Requested by fontgadgets.objects.groups.KerningGroups.set."
        )
        if not update:
            self.clear()
        if self._glyphToKerningGroupMapping == {}:
            self.convertPrefixedGroupsToKerningGroups()
        fontGroups = dict(self.groups)
        for side, sideKernGroups in kerningGroups.items():
            for kernGroupName, newMembers in sideKernGroups.items():
                for glyphName in newMembers:
                    # remove old memberships
                    prevKernGroupName = self.glyphToKerningGroupMapping.get(
                        glyphName, {}
                    ).get(side, None)
                    if prevKernGroupName is not None:
                        prevGroupName = self.convertToPrefixedGroupName(prevKernGroupName, side, self.font[glyphName].unicodeDirection == "rtl",)
                        prevMembers = list(fontGroups.get(prevGroupName, []))
                        if prevMembers:
                            prevMembers.remove(glyphName)
                            if len(prevMembers) > 0:
                                fontGroups[prevGroupName] = prevMembers
                            else:
                                del fontGroups[prevGroupName]
                            changed = True
                if kernGroupName is None:
                    continue
                uniDirection = self.font.unicodeDirectionForGlyphNames(newMembers)
                if uniDirection is None:
                    raise FontGadgetsError(
                        "All the given glyphs should be either 'right to left' or 'left to right!'"
                    )
                isRtl = uniDirection == "rtl"
                newGroupName = self.convertToPrefixedGroupName(kernGroupName, side, isRtl)

                changed = True
                if update:
                    # add new members to old groups if it exist
                    members = list(fontGroups.get(newGroupName, []))
                    members.extend([g for g in newMembers if g not in members])
                    fontGroups[newGroupName] = members
                else:
                    # reset the group
                    fontGroups[newGroupName] = newMembers
        if changed:
            self.groups.clear()
            self.groups.update(fontGroups)
        self.groups.releaseHeldNotifications()
        return changed

    def getGroupNamesForGlyphs(self, glyphNames, groupNamePrefixes=False):
        """
        Returns a dictionary with two keys `right` and `left`, each indicating the
        group kerning name for that side. The values of the keys is set of names
        indicating the kerning groups for the given `glyphNames`.

        groupNamePrefixes: If set to True, the `public.kern1.` or `public.kern2.`
        prefixes will be added to the group name.
        """
        result = {"left": set(), "right": set()}

        mapping = self._glyphToKerningGroupMapping
        for sideName in result:
            for glyphName in glyphNames:
                if glyphName not in mapping:
                    continue
                groupName = mapping[glyphName].get(sideName, None)
                if groupName is not None:
                    if groupNamePrefixes:
                        groupName = self._kerningGroupName2PrefixedGroupName[sideName][groupName]
                    result[sideName].add(groupName)
        return result

    def getRightSideGroupNamesForGlyphs(self, glyphNames, groupNamePrefixes=False):
        return self.getGroupNamesForGlyphs(glyphNames, groupNamePrefixes=groupNamePrefixes)["right"]

    def getLeftSideGroupNamesForGlyphs(self, glyphNames, groupNamePrefixes=False):
        return self.getGroupNamesForGlyphs(glyphNames, groupNamePrefixes=groupNamePrefixes)["left"]

    def update(self, kerningGroups):
        """
        Any new glyph for a kerning group will be added to the old kerning
        groups.
        """
        return self.set(kerningGroups, update=True)

    def clear(self):
        """
        Clears only kerning groups.
        """
        for group in list(self.groups):
            if isKerningGroup(group):
                del self.groups[group]

    def _getSideAndRawGroupName(self, groupName):
        match = re.match(RE_GROUP_TAG, groupName)
        members = self.font.groups[groupName]
        uniDirection = self.font.unicodeDirectionForGlyphNames(members)
        if match is not None:
            order = GROUP_SIDE_TAG.index(match.group(0))
            return (
                getGroupSideNameFromGroupOrder(order, uniDirection == "rtl"),
                re.split(RE_GROUP_TAG, groupName)[-1],
            )

    def convertToPrefixedGroupName(self, name, side, rtl):
        """
        Adds the kerning group name the prefix `public.kern1.` or
        `public.kern2.` prefixes to convert it to the standard ufo kerning
        group name.

        - name: name of the group without any prefix
        - side: `left` or `right`
        - rtl: True or False depending on wether the group is defined for a
        right to left glyph or not.
        """
        if isKerningGroup(name):
            warn(
                f"Kerning group name already starts with a prefix, it will be removed:\n{name}"
            )
            name = name[13:]
        order = getGroupOrderFromGroupSideName(side, rtl)
        prefix = GROUP_SIDE_TAG[order]
        return f"{prefix}{name}"


@font_cached_property("Groups.Changed")
def kerningGroups(font):
    return KerningGroups(font.groups)


@font_method
def kerningGroupSide(glyph, side, groupNamePrefixes=False):
    """
    Returns kerning group name for the given side.

    if groupNamePrefixes is set to True, the `public.kern1.` or `public.kern2.`
    prefixes will be added to the group name.

    side: `left` or `right`
    """
    kerningGroups = glyph.font.kerningGroups
    groupName = kerningGroups.glyphToKerningGroupMapping.get(glyph.name, {}).get(side, None)
    if groupNamePrefixes and groupName is not None:
        groupName = kerningGroups._kerningGroupName2PrefixedGroupName[side][groupName]
    return groupName

@font_method
def kerningGroupSideMembers(glyph, side):
    """
    Returns all the glyph names that are also members of the kerning group for
    the given side of this glyph.

    side: `left` or `right`
    """
    font = glyph.font
    group = glyph.kerningGroupSide(side)
    members = font.kerningGroups.items().get(group, [])
    return members


@font_method
def setKerningGroupSide(glyph, kernGroupName, side):
    """
    Set the kerning group name for the given side of the glyph.

    side: `left` or `right`
    """
    if isKerningGroup(kernGroupName):
        warn(f"Kerning group name already starts with a prefix, it will be removed:\n{kernGroupName}")
        kernGroupName = kernGroupName[13:]
    glyph.font.kerningGroups.update({side: {kernGroupName: [glyph.name, ]}})


@font_property
def getLeftSideKerningGroupMembers(glyph):
    """
    Returns the kerning group members for the left side of the glyph.
    """
    return glyph.kerningGroupSideMembers("left")


@font_property
def getRightSideKerningGroupMembers(glyph):
    """
    Returns the kerning group members for the right side of the glyph.
    """
    return glyph.kerningGroupSideMembers("right")


@font_method
def setLeftSideKerningGroup(glyph, kernGroupName):
    """
    Sets the kerning group name for the left side of the glyph.
    """
    glyph.setKerningGroupSide(kernGroupName, "left")


@font_method
def setRightSideKerningGroup(glyph, kernGroupName):
    """
    Sets the kerning group name for the right side of the glyph.
    """
    glyph.setKerningGroupSide(kernGroupName, "right")


@font_method
def getLeftSideKerningGroup(glyph, groupNamePrefixes=False):
    """
    Returns the kerning group name for the left side of the glyph.

    groupNamePrefixes: If set to True, the `public.kern1.` or `public.kern2.`
    prefixes will be added to the group name.
    """
    return glyph.kerningGroupSide("left", groupNamePrefixes)


@font_method
def getRightSideKerningGroup(glyph, groupNamePrefixes=False):
    """
    Returns the kerning group name for the right side of the glyph.

    groupNamePrefixes: If set to True, the `public.kern1.` or `public.kern2.`
    prefixes will be added to the group name.
    """
    return glyph.kerningGroupSide("right", groupNamePrefixes)


@font_method
def getKerningGroups(glyph, groupNamePrefixes=False):
    """
    Returns a dictionary with two keys `right` and `left`, each indicating the
    group kerning name for that side. The values of the keys is set of names
    indicating the kerning groups for the glyph.

    groupNamePrefixes: If set to True, the `public.kern1.` or `public.kern2.`
    prefixes will be added to the group name.
    """
    return glyph.font.kerningGroups.getGroupNamesForGlyphs((glyph.name,), groupNamePrefixes=groupNamePrefixes)


@font_property
def isGrouped(glyph):
    """
    Returns True if glyph has any kerning group.
    """
    return (
        glyph.kerningGroupSide("left") is not None or glyph.kerningGroupSide("right") is not None
    )


@font_cached_method("Groups.Changed", "Layer.GlyphAdded", "Layer.GlyphDeleted")
def getKerningGroupNamesForGlyphs(font, glyphNames, groupNamePrefixes=False):
    """
    Returns a dictionary with two keys `right` and `left`, each indicating the
    group kerning name for that side. The values of the keys is set of names
    indicating the kerning groups for the given `glyphNames`.

    groupNamePrefixes: If set to True, the `public.kern1.` or `public.kern2.`
    prefixes will be added to the group name.
    """
    return font.kerningGroups.getGroupNamesForGlyphs(glyphNames, groupNamePrefixes=groupNamePrefixes)


@font_cached_method("Groups.Changed", "Layer.GlyphAdded", "Layer.GlyphDeleted")
def getRightSideKerningGroupNamesForGlyphs(font, glyphNames, groupNamePrefixes=False):
    """
    Returns a set of names indicating the kerning groups for the right side of
    the glyph.

    groupNamePrefixes: If set to True, the `public.kern1.` or `public.kern2.`
    prefixes will be added to the group name.
    """
    return font.kerningGroups.getRightSideGroupNamesForGlyphs(glyphNames, groupNamePrefixes=groupNamePrefixes)


@font_cached_method("Groups.Changed", "Layer.GlyphAdded", "Layer.GlyphDeleted")
def getLeftSideKerningGroupNamesForGlyphs(font, glyphNames, groupNamePrefixes=False):
    """
    Returns a set of names indicating the kerning groups for the right side of
    the glyph.

    groupNamePrefixes: If set to True, the `public.kern1.` or `public.kern2.`
    prefixes will be added to the group name.
    """
    return font.kerningGroups.getLeftSideGroupNamesForGlyphs(glyphNames, groupNamePrefixes=groupNamePrefixes)
