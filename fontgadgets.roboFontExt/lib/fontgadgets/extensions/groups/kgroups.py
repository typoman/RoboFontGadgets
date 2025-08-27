# Copyright 2025 Bahman Eslami All Rights Reserved.
from fontgadgets.decorators import *
import fontgadgets.extensions.unicode.properties
import re
from warnings import warn
from typing import (
    Union,
    Dict,
    List,
    Tuple,
    Optional,
    Iterator,
    Any,
    KeysView,
    ValuesView,
    ItemsView,
)
__doc__ = """
UFO Kerning Groups Management with Visual Side-Based Access.

This module provides a comprehensive API for managing UFO kerning groups using
visual side terminology (left/right) rather than the UFO specification's
logical order prefixes (public.kern1./public.kern2.). It abstracts away the
complexities of bidirectional text handling and provides both font-level and
glyph-level interfaces for kerning group manipulation. 

The module enables GUI tool development by offering a glyph-centered data model
that simplifies kerning group operations. Users can copy/paste kerning groups
between glyphs, modify group memberships, and manage groups without needing to
understand the underlying UFO technical details or handle LTR/RTL direction
considerations manually. Left or right in this context mean the glyphs which
their left side or right side look visually similar.

Usage:
    # Import this module to add the kering group extensions
    import fontgadgets.extensions.groups.kgroups

    # Font-level modification of kerning groups based on which side they look
    # similar (left/right)
    font.kerningGroups.left["A"] = ["A", "Agrave", "Aacute"]
    font.kerningGroups.right["O"] = ["O", "Oacute", "Odieresis"]
 
    # Glyph-level modification of kerning groups based on which side they look
    # similar (left/right)
    glyph.kerningGroups.left = "A"
    glyph.kerningGroups.right = "O"
 
    # Copy kerning groups between glyphs
    target_glyph.kerningGroups.left = source_glyph.kerningGroups.left
"""


RE_GROUP_TAG = re.compile(r"public.kern[12]\.")
GROUP_SIDE_TAG = ("public.kern1.", "public.kern2.")
ORDER_2_SIDE = {0: "left", 1: "right"}
SIDE_2_ORDER = {"left": 0, "right": 1}


def isKerningGroup(entry: Optional[str]) -> bool:
    """
    Return True if the given entry is a kerning group name starting either with
    `public.kern1.` or `public.kern2.`

    Args:
        entry (Optional[str]): The string to check.

    Returns:
        bool: True if the string is a valid prefixed kerning group name,
        False otherwise.
    """
    if entry is None:
        return False
    if re.match(RE_GROUP_TAG, entry) is None:
        return False
    return True


def getGroupSideNameFromGroupOrder(order: int, RTL: bool) -> str:
    """
    Returns `right` or `left` depending on what order the group is defined in
    UFO 3 format.

    In LTR context, kern1 (order 0) is the left side, and kern2 (order 1) is
    the right side. In RTL context, this is reversed.

    Args:
        order (int): The logical order, 0 for kern1, 1 for kern2.
        RTL (bool): True if the context is Right-To-Left, False for Left-To-Right.

    Returns:
        str: The visual side name, "left" or "right".
    """
    assert isinstance(RTL, bool)
    if RTL is False:
        order = abs(order - 1)
    return ORDER_2_SIDE[order]


def getGroupLogicalOrderFromGroupSideName(side: str, RTL: bool) -> int:
    """
    Returns `0` or `1` depending on which side the group is going to be defined.
    This is the reverse of `getGroupSideNameFromGroupOrder`.

    Args:
        side (str): The visual side, "left" or "right".
        RTL (bool): True if the context is Right-To-Left, False for Left-To-Right.

    Returns:
        int: The logical order, 0 for kern1, 1 for kern2.
    """
    assert side in ("left", "right")
    assert isinstance(RTL, bool)
    order = SIDE_2_ORDER[side]
    if RTL is False:
        order = abs(order - 1)
    return order


class KerningGroup:
    """
    Represents a single kerning group with visual side (left/right) information
    and members.

    Holds a kerning group name (without UFO prefixes), visual side, member
    glyphs, direction, and associated font.

    Args:
        group_prefixed_name (str): The UFO-standard prefixed name
            (e.g., "public.kern1.groupName").
        name (str): The raw name of the group (without public.kern1/2 prefix).
        side (str): The visual side of the group ("left" or "right").
        glyph_set (list): A list of glyph names belonging to this group.
        direction (Optional[str]): The primary direction of the group members
            ("L" for LTR, "R" for RTL, or None for neutral).
        font (defcon.Font): The font object this group belongs to.
    """

    def __init__(
        self,
        group_prefixed_name: str,
        name: str,
        side: str,
        glyph_set: List[str],
        direction: Optional[str],
        font: "defcon.Font",
    ) -> None:
        """
        Initializes a KerningGroup instance.

        Args:
            group_prefixed_name (str): The UFO-standard prefixed name (e.g., "public.kern1.groupName").
            name (str): The raw name of the kerning group (without public.kern1/2 prefix).
            side (str): The visual side of the group ("left" or "right").
            glyph_set (list): A list of glyph names belonging to this group.
            direction (Optional[str]): The primary direction of the group members
                                   ("L" for LTR, "R" for RTL, or None for neutral).
            font (defcon.Font): The font object this group belongs to.
        """
        self._prefixed_name = group_prefixed_name
        self._name = name
        self._side = side
        self._glyph_set = glyph_set
        self._direction = direction
        self._font = font
        self._kerning = None

    @property
    def name(self) -> str:
        """The raw name of the group (without public.kern1/2 prefix)."""
        return self._name

    @name.setter
    def name(self, new_name: str) -> None:
        """
        Set the kerning group name (without public.kern1/2 prefix).

        This renames the group in the font, moving all members to the new name.

        Args:
            new_name (str): The new name for the group.
        """
        if not isinstance(new_name, str):
            raise TypeError("Group name must be a string.")
        if self._name == new_name:
            return
        adapter = self._font._kerningGroupsAdapter
        adapter.renameKerningGroupForSide(self._name, new_name, self._side)
        self._name = new_name
        return self._update()

    def _update(self):
        new_self = self._font._kerningGroupsAdapter.getKerningGroupFromNameAndSide(self._name, self._side)
        if new_self is None:
            return
        if self._direction != new_self.direction:
            self._direction = new_self.direction
            self._prefixed_name = new_self.prefixedName
        return new_self

    @property
    def side(self) -> str:
        """The visual side of the group ("left" or "right")."""
        return self._side

    @property
    def glyphSet(self) -> List[str]:
        """A list of glyph names belonging to this group."""
        return self._glyph_set

    @glyphSet.setter
    def glyphSet(self, new_members: Union[List[str], Tuple[str, ...]]) -> None:
        """
        Sets the group members, replacing the existing list.

        Args:
            new_members (Union[List[str], Tuple[str, ...]]): A list or tuple
                of glyph names.
        """
        if not isinstance(new_members, (list, tuple)):
            raise TypeError("Glyph set must be a list or tuple of glyph names.")
        new_members = list(new_members)
        self._glyph_set = new_members
        self._font._kerningGroupsAdapter.setKerningGroupFromNameSideAndMembers(self._name, self._side, new_members)
        return self._update()

    @property
    def direction(self) -> Optional[str]:
        """The primary direction of the group members."""
        return self._direction

    @property
    def font(self) -> 'defcon.Font':
        """The font object this group belongs to."""
        return self._font

    @property
    def prefixedName(self) -> str:
        """
        Returns the UFO-standard prefixed name for this kerning group
        (e.g., "public.kern1.groupName").
        """
        return self._prefixed_name

    @property
    def kerning(self) -> 'VisualSideKerning':
        """
        Accesses the kerning dictionary associated with this group.

        Returns:
            VisualSideKerning: An object to query and modify kerning values
            involving this group.
        """
        if self._kerning is None:
            from fontgadgets.extensions.glyph.kerning import VisualSideKerning
            self._kerning = VisualSideKerning(self, self._side)
        return self._kerning

    def __repr__(self) -> str:
        return (
            f"<KerningGroup name='{self._name}' side='{self._side}' "
            f"members={len(self.glyphSet)}>"
        )

    def __eq__(self, other: Any) -> bool:
        if not isinstance(other, KerningGroup):
            return NotImplemented
        return self._prefixed_name == other._prefixed_name and self._font == other._font


class KerningGroupsAdapter:
    """
    Adapter class for managing UFO kerning groups with visual side-based access.

    Converts UFO standard groups (with public.kern1./public.kern2. prefixes) to
    KerningGroup objects organized by visual side (left/right) rather than
    logical order, which is the encoding method in the UFO 3 format.

    The adapter automatically handles bidirectional text considerations,
    converting between logical order (kern1/kern2) and visual sides based on
    the script direction of the group members.

    Args:
        groups (defcon.Groups): The font's groups object containing UFO
            standard kerning groups.
    """

    # An object that gets destroyed every time font.groups change. This is used
    # for changing kerning groups of the font from the glyph centered perspective.

    def __init__(self, groups: 'defcon.Groups') -> None:
        self._logical_order_groups = groups
        self._font = self._logical_order_groups.font
        self._logical_to_visual_naming_map: Dict[str, KerningGroup] = {} # get KerningGroup object from its prefixed name

        # {"glyph_name": {"left": KerningGroup, "right": KerningGroup}, ...}
        self._glyph_name_to_kerning_group_mapping: Dict[str, Dict[str, KerningGroup]] = {}
        # {"left": {rawKerningGroupName: KerningGroup}, "right": {rawKerningGroupName: KerningGroup}}
        self._visual_side_groups: Dict[str, Dict[str, KerningGroup]] = {"left": {}, "right": {}}

        self._getGlyphDirection = lambda glyphName: self._font[glyphName].unicodeProperties.bidiType
        self._changed = True
        self._updateInternalState()

    @property
    def font(self) -> 'defcon.Font':
        """The font object this adapter belongs to."""
        return self._font

    def _updateInternalState(self) -> None:
        if not self._changed:
            return
        self._glyph_name_to_kerning_group_mapping = {}
        self._visual_side_groups = {"left": {}, "right": {}}
        for prefixed_group_name, members in self._logical_order_groups.items():
            if isKerningGroup(prefixed_group_name):
                side_and_name = self._getSideAndRawGroupName(prefixed_group_name)
                if side_and_name is not None:
                    side, kerning_group_name = side_and_name
                    direction = None
                    if members:
                        direction = self._getGlyphSetDirection(members)
                    kg_object = KerningGroup(
                        group_prefixed_name=prefixed_group_name,
                        name=kerning_group_name,
                        side=side,
                        glyph_set=list(members),
                        direction=direction,
                        font=self._font
                    )
                    self._visual_side_groups.setdefault(side, {})[kerning_group_name] = kg_object
                    self._logical_to_visual_naming_map[prefixed_group_name] = kg_object
                    for glyph_name in members:
                        self._glyph_name_to_kerning_group_mapping.setdefault(glyph_name, {})[side] = kg_object
        self._changed = False

    def getKerningGroupFromPrefixedGroupName(self, prefixed_group_name: str) -> KerningGroup:
        """
        Retrieve a KerningGroup object using its UFO-standard prefixed name.

        Args:
            prefixed_group_name (str): The UFO-standard prefixed group name
                (e.g., "public.kern1.groupName" or "public.kern2.groupName").

        Returns:
            KerningGroup: The KerningGroup object corresponding to the prefixed
                name.

        Raises:
            KeyError: If no kerning group exists with the given prefixed name.
        """
        return self._logical_to_visual_naming_map[prefixed_group_name]

    def getKerningGroupFromNameAndSide(self, kerning_group_name: str, side: str) -> Optional[KerningGroup]:
        """
        Retrieve a KerningGroup object by its name and visual side.

        Args:
            kerning_group_name (str): The name of the kerning group (without
                public.kern1/2 prefix).
            side (str): The visual side of the group, either "left" or "right".

        Returns:
            Optional[KerningGroup]: The KerningGroup object if found, None if no
                group exists with the given name and side combination.
        """
        kerning_group = self._visual_side_groups[side].get(kerning_group_name, None)
        return kerning_group

    def setKerningGroupFromNameSideAndMembers(self, kerning_group_name: str, side: str, members: List[str]) -> bool:
        """
        Sets or updates a single kerning group, ensuring glyphs are not in
        multiple groups on the same side.

        This method defines the complete membership for a given kerning group.
        - If a glyph in `members` is already in another group on the same `side`,
          it is removed from the old group.
        - If a glyph that was previously in this group is not in the new `members`
          list, it is effectively ungrouped.
        - If the `members` list is empty, the group is deleted.

        Args:
            kerning_group_name (str): The raw name of the group.
            side (str): The visual side, "left" or "right".
            members (list): A list of glyph names for the group.

        Returns:
            bool: True if the font's groups were modified, False otherwise.
        """
        self._logical_order_groups.holdNotifications(note='Requested by fontgadgets.extensions.groups.kgroups')
        self._updateInternalState()

        initial_groups_state = dict(self._logical_order_groups)
        members = list(members)

        # 1. Remove provided glyphs from any other group on the same side.
        for glyph_name in members:
            prev_kern_group = self._glyph_name_to_kerning_group_mapping.get(glyph_name, {}).get(side)
            if prev_kern_group and prev_kern_group.name != kerning_group_name:
                # This glyph is moving from another group.
                old_prefixed_name = prev_kern_group.prefixedName
                if old_prefixed_name in self._logical_order_groups:
                    old_members = list(self._logical_order_groups[old_prefixed_name])
                    if glyph_name in old_members:
                        old_members.remove(glyph_name)
                        if not old_members:
                            del self._logical_order_groups[old_prefixed_name]
                        else:
                            self._logical_order_groups[old_prefixed_name] = old_members

        # 2. Handle the target group.
        # Find the existing object for this group, if any, to get its old prefixed name.
        existing_group_obj = self._visual_side_groups.get(side, {}).get(kerning_group_name)
        old_prefixed_name = existing_group_obj.prefixedName if existing_group_obj else None

        if not members:
            # If the new member list is empty, the group should be deleted.
            if old_prefixed_name and old_prefixed_name in self._logical_order_groups:
                del self._logical_order_groups[old_prefixed_name]
        else:
            # Determine the correct new prefixed name based on the members' direction.
            isRTL = self._getGlyphSetDirection(members) == "R"
            new_prefixed_name = self._convertKerningGroupNameToPrefixedGroupName(kerning_group_name, side, isRTL)

            # If the prefixed name has changed (due to direction change), remove the old one.
            if old_prefixed_name and old_prefixed_name != new_prefixed_name:
                if old_prefixed_name in self._logical_order_groups:
                    del self._logical_order_groups[old_prefixed_name]

            # Set the group with its new members.
            self._logical_order_groups[new_prefixed_name] = members

        self._changed = initial_groups_state != dict(self._logical_order_groups)
        self._logical_order_groups.releaseHeldNotifications()

    def renameKerningGroupForSide(self, old_name: str, new_name: str, side: str) -> None:
        """
        Rename a kerning group on a specific visual side.

        This method changes the name of an existing kerning group while preserving
        all its members. The group's members are moved to the new group name,
        and the old group is deleted.

        Args:
            old_name (str): The current name of the kerning group (without
                public.kern1/2 prefix).
            new_name (str): The new name for the kerning group (without
                public.kern1/2 prefix).
            side (str): The visual side of the group, either "left" or "right".

        Raises:
            KeyError: If no kerning group with the old_name exists on the
                specified side.
            ValueError: If a kerning group with the new_name already exists on
                the specified side.
        """
        if old_name == new_name:
            return
        self._updateInternalState()
        side_groups = self._visual_side_groups.get(side, {})
        if old_name not in side_groups:
            raise KeyError(f"No '{side}' kerning group named '{old_name}' found.")
        if new_name in side_groups:
            raise ValueError(f"A kerning group named '{new_name}' already exists for the '{side}' side.")
        old_group_obj = side_groups[old_name]
        old_prefixed_name = old_group_obj.prefixedName
        isRTL = old_group_obj.direction == "R"
        new_prefixed_name = self._convertKerningGroupNameToPrefixedGroupName(new_name, side, isRTL)
        self._logical_order_groups[new_prefixed_name] = self._logical_order_groups.pop(old_prefixed_name)
        self._changed = True

    def removeMembersFromKerningGroupOnSide(self, kerning_group_name: str, side: str, members_to_remove: List[str]) -> None:
        """
        Remove members from a kerning group on a visual side.

        Args:
            kerning_group_name (str): The name of the kerning group (without
                public.kern1/2 prefix).
            side (str): The visual side of the group, either "left" or "right".
            members_to_remove (List[str]): List of glyph names to remove from the group.

        Raises:
            FontGadgetsError: If no kerning group with the given name exists on the
                specified side.
        """
        if not members_to_remove:
            return
        self._updateInternalState()
        kerning_group = self.getKerningGroupFromNameAndSide(kerning_group_name, side)
        if kerning_group is None:
            raise FontGadgetsError(f"Kerning group with name `{kerning_group_name}` on the `{side}` doesn't exist!")
        new_members = [g for g in kerning_group.glyphSet if g not in members_to_remove]
        self.setKerningGroupFromNameSideAndMembers(kerning_group_name, side, new_members)

    def addMembersToKerningGroupOnSide(self, kerning_group_name: str, side: str, new_members: List[str]) -> None:
        """
        Add members to a kerning group on a visual side.

        Args:
            kerning_group_name (str): The name of the kerning group (without
                public.kern1/2 prefix).
            side (str): The visual side of the group, either "left" or "right".
            new_members (List[str]): List of glyph names to add to the group.

        Raises:
            FontGadgetsError: If no kerning group with the given name exists on the
                specified side.
        """
        if not new_members:
            return
        self._updateInternalState()
        kerning_group = self.getKerningGroupFromNameAndSide(kerning_group_name, side)
        if kerning_group is None:
            raise FontGadgetsError(f"Kerning group with name `{kerning_group_name}` on the `{side}` doesn't exist!")
        members = kerning_group.glyphSet
        if set(members) == set(new_members):
            return
        members.extend([g for g in new_members if g not in members])
        self.setKerningGroupFromNameSideAndMembers(kerning_group_name, side, members)

    def _getGlyphSetDirection(self, glyph_set: List[str]) -> Optional[str]:
        """
        Determines the dominant writing direction for a set of glyphs.
        """
        directions = {self._getGlyphDirection(gn) for gn in glyph_set}
        directions.discard(None)
        if len(directions) > 1:
            raise FontGadgetsError(f'Mixed direction glyphs in the set `{glyph_set}`.')
        if not directions:
            return None
        return directions.pop()

    def getKerningGroupsForGlyphSet(self, glyph_set: List[str]) -> Dict[str, List[KerningGroup]]:
        """
        Get all kerning groups that contain any glyphs from the specified set.

        This method searches through all the font kerning groups to find those
        that contain at least one glyph from the provided glyph set. The
        results are organized by visual side (left/right) and return the actual
        KerningGroup objects.

        Args:
            glyph_set (List[str]): List of glyph names to search for in kerning groups.

        Returns:
            Dict[str, List[KerningGroup]]: A dictionary mapping visual sides to
            lists of KerningGroup objects:
            {"left": [KerningGroup, ...], "right": [KerningGroup, ...]}
            Each KerningGroup in the lists contains at least one glyph from the
            input glyph_set.

        Example:
            # Find all groups containing glyphs A, B, or C
            groups = adapter.getKerningGroupsForGlyphSet(["A", "B", "C"])
            # Returns: {"left": [KerningGroup("left_group_1")],
            #           "right": [KerningGroup("right_group_2")]}
        """
        self._updateInternalState()
        result = {}
        mapping = self._glyph_name_to_kerning_group_mapping
        for side_name, kerning_groups in self._visual_side_groups.items():
            kgroup_names = set()
            for glyph_name in glyph_set:
                if glyph_name not in mapping:
                    continue
                kerning_group = mapping[glyph_name].get(side_name, None)
                if kerning_group is not None:
                    kgroup_names.add(kerning_group.name)
            result[side_name] = [kerning_groups[kg] for kg in kgroup_names]
        return result

    def getRightSideKerningGroupsForGlyphSet(self, glyph_set: List[str]) -> List[KerningGroup]:
        """
        Get all right-side kerning groups that contain any glyphs from the set.

        This method searches through the font right-side kerning groups to find
        those that contain at least one glyph from the provided glyph set.

        Args:
            glyph_set (List[str]): List of glyph names to search for in right-side
                kerning groups.

        Returns:
            List[KerningGroup]: A list of KerningGroup objects from the right side
            that contain at least one glyph from the input glyph_set.

        Example:
            # Find all right-side groups containing glyphs O, Q, or C
            right_groups = adapter.getRightSideKerningGroupsForGlyphSet(
                ["O", "Q", "C"]
            )
            # Returns: [KerningGroup("round_letters"), KerningGroup("O")]
        """
        return self.getKerningGroupsForGlyphSet(glyph_set)["right"]

    def getLeftSideKerningGroupsForGlyphSet(self, glyph_set: List[str]) -> List[KerningGroup]:
        """
        Get all left-side kerning groups that contain any glyphs from the set.

        This method searches through the font left-side kerning groups to find
        those that contain at least one glyph from the provided glyph set.

        Args:
            glyph_set (List[str]): List of glyph names to search for in left-side
                kerning groups.

        Returns:
            List[KerningGroup]: A list of KerningGroup objects from the left side
            that contain at least one glyph from the input glyph_set.

        Example:
            # Find all left-side groups containing glyphs A, V, or T
            left_groups = adapter.getLeftSideKerningGroupsForGlyphSet(
                ["A", "V", "T"]
            )
            # Returns: [KerningGroup("triangular"), KerningGroup("A")]
        """
        return self.getKerningGroupsForGlyphSet(glyph_set)["left"]

    def updateKerningGroupsUsingDict(self, kerning_groups_dict: Dict[str, Dict[Optional[Union[str, KerningGroup]], List[str]]]) -> bool:
        """
        Update kerning groups by adding new members to existing groups.

        This method processes a nested dictionary structure to add glyphs to
        kerning groups. New glyphs are added to existing groups without removing
        current members. If a group doesn't exist, it will be created. Glyphs
        can also be removed from groups by specifying None as the group key.

        Args:
            kerning_groups_dict: A nested dictionary with the structure:
                {
                    "side": {
                        kerning_group: [glyph_names],
                        ...
                    },
                    ...
                }
                Where:
                - "side" is either "left" or "right"
                - kerning_group can be:
                    * str: kerning group name
                    * KerningGroup: existing kerning group object
                    * None: removes glyphs from their current groups
                - [glyph_names] is a list of glyph names to add/remove

        Returns:
            bool: True if any changes were made to the font's groups, False
            otherwise.

        Example:
            # Add glyphs to groups
            groups_dict = {
                "left": {
                    "A": ["A", "Agrave", "Aacute"],
                    "V": ["V", "W"]
                },
                "right": {
                    "O": ["O", "Q"]
                }
            }
            changed = adapter.updateKerningGroupsUsingDict(groups_dict)

            # Remove glyphs from groups
            remove_dict = {
                "left": {
                    None: ["unwanted_glyph"]
                }
            }
            adapter.updateKerningGroupsUsingDict(remove_dict)
        """
        self._updateInternalState()
        self._logical_order_groups.holdNotifications(note='Requested by fontgadgets.extensions.groups.kgroups')
        for side, side_groups in kerning_groups_dict.items():
            for group_key, new_members_to_add in side_groups.items():
                if isinstance(group_key, KerningGroup):
                    group_name: Optional[str] = group_key.name
                else:
                    group_name = group_key
                if group_name is None:
                    for glyph_name in new_members_to_add:
                        prev_kern_group = self._glyph_name_to_kerning_group_mapping.get(glyph_name, {}).get(side)
                        if prev_kern_group:
                            current_members = list(prev_kern_group.glyphSet)
                            current_members.remove(glyph_name)
                            self.setKerningGroupFromNameSideAndMembers(prev_kern_group.name, side, current_members)
                    continue
                existing_group = self._visual_side_groups.get(side, {}).get(group_name)
                if existing_group:
                    current_members = set(existing_group.glyphSet)
                else:
                    current_members = set()
                updated_members = list(current_members.union(set(new_members_to_add)))
                self.setKerningGroupFromNameSideAndMembers(group_name, side, updated_members)
        self._logical_order_groups.releaseHeldNotifications()

    def clear(self) -> None:
        """
        Clears all kerning groups from the font, leaving other groups intact.
        """
        to_delete = [k for k in self._logical_order_groups if isKerningGroup(k)]
        if to_delete:
            for k in to_delete:
                del self._logical_order_groups[k]
        self._changed = True

    def clearSide(self, side: str) -> None:
        """
        Clears all kerning groups on the given visual side (left/right).

        Args:
            side (str): The visual side to clear, "left" or "right".
        """
        side_map = self._visual_side_groups[side]
        to_delete = set()
        for kg_object in side_map.values():
            to_delete.add(kg_object.prefixedName)
        for group_prefixed_name in to_delete:
            del self._logical_order_groups[group_prefixed_name]
        self._changed = True

    def _getSideAndRawGroupName(self, prefixed_group_name: str) -> Optional[Tuple[str, str]]:
        """
        Helper to extract the visual side and non-prefixed kerning group name.

        Assumes groupName is a valid prefixed kerning group.
        """
        match = re.match(RE_GROUP_TAG, prefixed_group_name)
        if match is None:
            return None
        members = self._logical_order_groups.get(prefixed_group_name, [])
        uniDirection = self._getGlyphSetDirection(members)
        order = GROUP_SIDE_TAG.index(match.group(0))
        is_rtl_direction = (uniDirection == "R")
        return (getGroupSideNameFromGroupOrder(order, is_rtl_direction),
                re.split(RE_GROUP_TAG, prefixed_group_name)[-1],)

    def _convertKerningGroupNameToPrefixedGroupName(self, kerning_group_name: str, side: str, rtl: bool) -> str:
        """
        Adds the `public.kern1.` or `public.kern2.` prefix to a kerning group name.

        Args:
            kerning_group_name (str): name of the kerning group without any prefix.
            side (str): `left` or `right`.
            rtl (bool): True if the group contains right-to-left glyphs.

        Returns:
            str: The fully prefixed UFO kerning group name.
        """
        if isKerningGroup(kerning_group_name):
            warn(f"Kerning group name already starts with a prefix, it will be removed:\n{kerning_group_name}")
            kerning_group_name = kerning_group_name[13:] # Remove "public.kernX."
        order = getGroupLogicalOrderFromGroupSideName(side, rtl)
        prefix = GROUP_SIDE_TAG[order]
        return f"{prefix}{kerning_group_name}"


@font_cached_property("Groups.Changed", "Layer.GlyphAdded", "Layer.GlyphDeleted", "UnicodeData.Changed", "Features.Changed")
def _kerningGroupsAdapter(font):
    """
    A cached property that attaches a KerningGroupsAdapter to a font object.

    This ensures that the adapter is created only once and is invalidated and
    recreated whenever the font's groups or relevant glyph data changes.
    """
    return KerningGroupsAdapter(font.groups)


class FontKerningGroupSide:
    """
    A dictionary-like object that holds kerning groups of a font on one visual
    side (left/right).

    This class provides access to kerning groups using their raw names (without
    UFO prefixes like 'public.kern1.' or 'public.kern2.'). The UFO specification
    uses logical order prefixes where 'public.kern1.' represents the first
    position and 'public.kern2.' the second position in a kerning pair. However,
    this class abstracts that complexity by organizing groups by their visual
    side appearance in text flow.

    For example:
    - UFO standard kerning group prefixed name: "public.kern1.A"
    - Raw kerning group name: "A"
    - Visual side: "left"

    Accessing items returns KerningGroup objects.
    Setting items expects a list of glyph names.
    Deleting items removes the group from the font.

    Args:
        font (defcon.Font): The font object containing the kerning groups.
        side (str): The visual side ("left" or "right") this object manages.
    """

    def __init__(self, font: 'defcon.Font', side: str) -> None:
        self._font = font
        self._side = side

    @property
    def _adapter(self) -> KerningGroupsAdapter:
        """Dynamically get the adapter to ensure it's always fresh."""
        return self._font._kerningGroupsAdapter

    def __getitem__(self, kerning_group_name: str) -> KerningGroup:
        """
        Returns the KerningGroup object for the given group name.

        Raises:
            KeyError: If the group is not found.
        """
        try:
            return self._adapter._visual_side_groups[self._side][kerning_group_name]
        except KeyError:
            raise KeyError(f"No '{self._side}' kerning group named '{kerning_group_name}' found.")

    def __setitem__(self, kerning_group_name: str, members: List[str]) -> None:
        """
        Sets or updates a kerning group with a list of members.

        If the group exists, its members are replaced. If it doesn't exist, it
        is created.

        Args:
            kerning_group_name (str): The name of the group.
            members (List[str]): A list of glyph names.
        """
        if not isinstance(members, list):
            raise TypeError("Members must be a list of glyph names.")
        self._adapter.setKerningGroupFromNameSideAndMembers(kerning_group_name, self._side, members)

    def __delitem__(self, kerning_group_name: str) -> None:
        """
        Deletes a kerning group.

        Raises:
            KeyError: If the group is not found.
        """
        try:
            kerning_group_obj = self[kerning_group_name]
            prefixed_name = kerning_group_obj.prefixedName
            if prefixed_name in self._font.groups:
                del self._font.groups[prefixed_name]
            else:
                # This can happen if the adapter's state is stale, which
                # notifications should prevent.
                raise KeyError
        except KeyError:
            raise KeyError(f"No '{self._side}' kerning group named '{kerning_group_name}' found.")

    def __iter__(self) -> Iterator[str]:
        """Iterates over the names of the kerning groups on this side."""
        return iter(self._adapter._visual_side_groups[self._side])

    def __len__(self) -> int:
        """Returns the number of kerning groups on this side."""
        return len(self._adapter._visual_side_groups[self._side])

    def __contains__(self, kerning_group_name: str) -> bool:
        """Checks if a kerning group with the given name exists on this side."""
        return kerning_group_name in self._adapter._visual_side_groups[self._side]

    def __repr__(self) -> str:
        return (
            f"<FontKerningGroupSide side='{self._side}' "
            f"groups={list(self.keys())}>"
        )

    def keys(self) -> KeysView[str]:
        """Returns a view of the group names on this side."""
        return self._adapter._visual_side_groups[self._side].keys()

    def values(self) -> ValuesView[KerningGroup]:
        """Returns a view of the KerningGroup objects on this side."""
        return self._adapter._visual_side_groups[self._side].values()

    def items(self) -> ItemsView[str, KerningGroup]:
        """Returns a view of the (name, KerningGroup) pairs on this side."""
        return self._adapter._visual_side_groups[self._side].items()

    def get(self, kerning_group_name: str, default: Any = None) -> Any:
        """
        Gets a kerning group by name, returning a default value if not found.

        Args:
            kerning_group_name (str): The name of the group.
            default (Any): The value to return if the group is not found.

        Returns:
            Union[KerningGroup, Any]: The KerningGroup object or the default value.
        """
        return self._adapter._visual_side_groups[self._side].get(kerning_group_name, default)

    def clear(self) -> None:
        """Removes all kerning groups from this visual side."""
        self._adapter.clearSide(self._side)

    def renameKerningGroup(self, old_name: str, new_name: str) -> None:
        """
        Renames a kerning group on this side.

        Args:
            old_name (str): The current name of the group.
            new_name (str): The new name for the group.

        Raises:
            KeyError: If the old_name is not found.
            ValueError: If the new_name already exists.
        """
        if old_name not in self:
            raise KeyError(f"No '{self._side}' kerning group named '{old_name}' found.")
        if old_name == new_name:
            return
        if new_name in self:
            raise ValueError(f"A kerning group named '{new_name}' already exists for the '{self._side}' side.")
        return self._adapter.renameKerningGroupForSide(old_name, new_name, self._side)

class FontKerningGroups():
    """
    A container for kerning groups inside a font with two properties: `left` and `right`.
    Each property provides a dictionary-like interface to the kerning groups
    on that visual side.

    Examples:
        # Access the left-side groups
        left_groups = font.kerningGroups.left

        # Get a specific left-side kerning group's KerningGroup object
        group_A_left = left_groups["A"]

        # Set the members of a right-side kerning group
        font.kerningGroups.right["O"] = ["O", "Oacute", "Odieresis"]

        # Check if a kerning group exists
        if "V" in font.kerningGroups.left:
            print("V left group exists.")

        # Delete a kerning group
        del font.kerningGroups.left["V"]
    """
    def __init__(self, font: 'defcon.Font') -> None:
        self._font = font
        self._left = FontKerningGroupSide(font, 'left')
        self._right = FontKerningGroupSide(font, 'right')

    @property
    def _adapter(self) -> KerningGroupsAdapter:
        """Dynamically get the adapter to ensure it's always fresh."""
        return self._font._kerningGroupsAdapter

    @property
    def left(self) -> FontKerningGroupSide:
        """
        Provides dictionary-like access to all left-side kerning groups.
        """
        return self._left

    @property
    def right(self) -> FontKerningGroupSide:
        """
        Provides dictionary-like access to all right-side kerning groups.
        """
        return self._right

    def getSide(self, side: str) -> FontKerningGroupSide:
        """
        Get the FontKerningGroupSide object for a given side name.

        Args:
            side (str): "left" or "right".

        Returns:
            FontKerningGroupSide: The corresponding side object.

        Raises:
            FontGadgetsError: If side is not "left" or "right".
        """
        match side:
            case 'right':
                return self._right
            case 'left':
                return self._left
        raise FontGadgetsError(f"Kerning group side can either be 'left' or 'right', not {side}!")

    def getKerningGroupFromPrefixedGroupName(self, prefixed_group_name: str) -> KerningGroup:
        """
        Retrieve a KerningGroup object using its full UFO-standard prefixed name.

        Args:
            prefixed_group_name (str): The full group name (e.g., "public.kern1.A").

        Returns:
            KerningGroup: The corresponding KerningGroup object.
        """
        return self._adapter.getKerningGroupFromPrefixedGroupName(prefixed_group_name)

    def __repr__(self) -> str:
        return (
            f"<FontKerningGroups "
            f"left={len(self.left)} groups, right={len(self.right)} groups>"
        )

@font_cached_property("Groups.Changed", "Layer.GlyphAdded", "Layer.GlyphDeleted", "UnicodeData.Changed", "Features.Changed")
def kerningGroups(font):
    """
    A cached property that attaches a FontKerningGroups manager to the font object.

    This provides a high-level API for interacting with the font's kerning
    groups, organized by visual side.
    """
    return FontKerningGroups(font)

class GlyphKerningGroups:
    """
    Provides kerning group access and manipulation for a single glyph.

    Manages kerning group assignments for both left and right sides of a glyph,
    using visual side names rather than UFO's logical order prefixes. Supports
    getting, setting, and removing kerning group memberships.

    Args:
        glyph (defcon.Glyph): The glyph object to manage kerning groups for.

    Properties:
        left (Optional[KerningGroup]): The left-side kerning group.
        right (Optional[KerningGroup]): The right-side kerning group.
    """

    def __init__(self, glyph: 'defcon.Glyph') -> None:
        self._glyph = glyph

    @property
    def _adapter(self):
        return self._glyph.font._kerningGroupsAdapter

    def getKerningGroupForSide(self, side: str) -> Optional[KerningGroup]:
        """
        Returns the kerning group for the given side of the glyph.

        Args:
            side (str): `left` or `right`.

        Returns:
            Optional[KerningGroup]: The KerningGroup object if the glyph is in
            a group on that side, otherwise None.
        """
        glyph = self._glyph
        return self._adapter._glyph_name_to_kerning_group_mapping.get(glyph.name, {}).get(side, None)

    def setKerningGroupForSide(self, kerning_group: Optional[Union[str, KerningGroup]], side: str) -> Optional[KerningGroup]:
        """
        Sets, changes, or removes the kerning group for a specific visual side of the glyph.

        This method is the core logic for managing a glyph's group membership. It handles
        three main scenarios based on the `kerning_group` argument:

        1.  **Assigning/Changing a group:** If a group name (`str`) or a `KerningGroup`
            object is provided, the glyph is added to that group's members for the
            specified `side`. If the glyph was previously in another group on the same
            side, it is automatically moved. If the target group doesn't exist, it is
            created with this glyph as its first member.

        2.  **Removing from a group:** If `None` is provided, the glyph is removed from
            its current kerning group on the specified `side`.

        Args:
            kerning_group (Optional[Union[str, KerningGroup]]):
                The target kerning group or action to take.
                - `str`: The name of the kerning group (e.g., "A"). The glyph will
                  be added to this group.
                - `KerningGroup`: A `KerningGroup` object. The glyph will be added to
                  this group. The object's `side` must match the `side` argument.
                - `None`: The glyph will be removed from any kerning group it belongs
                  to on the specified `side`.
            side (str): The visual side to modify, either "left" or "right".

        Returns:
            Optional[KerningGroup]: The `KerningGroup` object the glyph now belongs to,
            or `None` if the glyph was removed from its group or was not in a group
            to begin with.

        Raises:
            TypeError: If `kerning_group` is not a `str`, `KerningGroup`, or `None`.
            ValueError: If a `KerningGroup` object is passed whose `side` does not
                match the `side` argument.
        """
        kerning_group_name = kerning_group
        if isinstance(kerning_group, KerningGroup):
            if kerning_group.side != side:
                raise ValueError(
                    f"Cannot assign a '{kerning_group.side}' side KerningGroup "
                    f"to the '{side}' side of the glyph."
                )
            kerning_group_name = kerning_group.name

        adapter = self._adapter
        if kerning_group_name is None:
            current_group = self.getKerningGroupForSide(side)
            if current_group is not None:
                adapter.removeMembersFromKerningGroupOnSide(current_group.name, side, [self._glyph.name])
            return None

        if not isinstance(kerning_group_name, str):
             raise TypeError(f"Expected a string or KerningGroup, but got {type(kerning_group_name).__name__}")
        if isKerningGroup(kerning_group_name):
            warn(f"Kerning group name already starts with a prefix, it will be removed:\n{kerning_group_name}")
            kerning_group_name = kerning_group_name[13:]

        existing_group = adapter.getKerningGroupFromNameAndSide(kerning_group_name, side)
        if existing_group is None:
            # Create a new group
            adapter.setKerningGroupFromNameSideAndMembers(kerning_group_name, side, [self._glyph.name])
        else:
            # Add to an existing group
            adapter.addMembersToKerningGroupOnSide(kerning_group_name, side, [self._glyph.name])
        return self.getKerningGroupForSide(side)

    def setLeftSide(self, kerning_group: Union[str, KerningGroup, None]) -> Optional[KerningGroup]:
        """
        Sets the kerning group for the left side of the glyph.

        Args:
            kerning_group: The kerning group to assign. Can be a string
                (kerning group name without prefix), a KerningGroup object, or None
                to remove the current assignment.

        Returns:
            Optional[KerningGroup]: The updated KerningGroup object, or None.
        """
        return self.setKerningGroupForSide(kerning_group, "left")

    def setRightSide(self, kerning_group: Union[str, KerningGroup, None]) -> Optional[KerningGroup]:
        """
        Sets the kerning group for the right side of the glyph.

        Args:
            kerning_group: The kerning group to assign. Can be a string
                (kerning group name without prefix), a KerningGroup object, or None
                to remove the current assignment.
        Returns:
            Optional[KerningGroup]: The updated KerningGroup object, or None.
        """
        return self.setKerningGroupForSide(kerning_group, "right")

    def removeLeftSide(self) -> None:
        """
        Removes the kerning group for the left side of the glyph.
        """
        self.setKerningGroupForSide(None, "left")

    def removeRightSide(self) -> None:
        """
        Removes the kerning group for the right side of the glyph.
        """
        self.setKerningGroupForSide(None, "right")

    def getLeftSide(self) -> Optional[KerningGroup]:
        """
        Returns the kerning group for the left side of the glyph.
        """
        return self.getKerningGroupForSide("left")

    def getRightSide(self) -> Optional[KerningGroup]:
        """
        Returns the kerning group for the right side of the glyph.
        """
        return self.getKerningGroupForSide("right")

    def __iter__(self) -> Iterator[KerningGroup]:
        """
        Iterates over the KerningGroup objects this glyph belongs to.
        (A glyph can be in at most one left-side and one right-side group).
        """
        glyph = self._glyph
        kerningGroupsDict = self._adapter._glyph_name_to_kerning_group_mapping.get(glyph.name, {})
        for kg_object in kerningGroupsDict.values():
            yield kg_object

    def isGrouped(self) -> bool:
        """
        Returns True if the glyph belongs to any kerning group (left or right).
        """
        for kg_object in iter(self):
            if kg_object is not None:
                return True
        return False

    @property
    def left(self) -> Optional[KerningGroup]:
        """
        The left-side kerning group for this glyph.

        Can be set with a kerning group name (str), a KerningGroup object, or None.
        Can be deleted to remove the glyph from its left-side group.
        """
        return self.getLeftSide()

    @left.setter
    def left(self, value: Optional[Union[str, KerningGroup]]) -> None:
        self.setLeftSide(value)

    @left.deleter
    def left(self) -> None:
        self.removeLeftSide()

    @property
    def right(self) -> Optional[KerningGroup]:
        """
        The right-side kerning group for this glyph.

        Can be set with a kerning group name (str), a KerningGroup object, or None.
        Can be deleted to remove the glyph from its right-side group.
        """
        return self.getRightSide()

    @right.setter
    def right(self, value: Optional[Union[str, KerningGroup]]) -> None:
        self.setRightSide(value)

    @right.deleter
    def right(self) -> None:
        self.removeRightSide()


@font_property
def kerningGroups(glyph):
    """
    Provides kerning group access and manipulation for a single glyph.

    Manages kerning group assignments for both left and right sides of a glyph,
    using visual side names rather than UFO's logical order prefixes. Supports
    getting, setting, and removing kerning group memberships. Left or right
    in this object mean the glyphs which their left side or right side look
    visually similar.

    Properties:
        left (Optional[KerningGroup]): The left-side kerning group.
        right (Optional[KerningGroup]): The right-side kerning group.

    Examples:
        # Set kerning groups for left and right sides
        glyph.kerningGroups.left = "D"    # Returns KerningGroup("D")
        glyph.kerningGroups.right = "O"   # Returns KerningGroup("O")

        # Iterating kerning groups of a glyph
        for kerning_group in glyph.kerningGroups:
            print(f"Group: {kerning_group.name}, Side: {kerning_group.side}")
            print(f"Members: {kerning_group.glyphSet}")

        # Check if glyph has any kerning groups
        is_grouped = glyph.kerningGroups.isGrouped()  # Returns True

        # Remove kerning groups
        del glyph.kerningGroups.left   # Removes left side kerning group
        del glyph.kerningGroups.right  # Removes right side kerning group

        # Changing members of a kerning group which belongs to this glyph
        left_group = glyph.kerningGroups.left
        if left_group:
            left_group.glyphSet = ["A", "Aring", "Atilde"]  # Updates group members

        # Change the kerning group name on a visual side
        right_group = glyph.kerningGroups.right
        if right_group:
            right_group.name = "New_Group"
    """
    return GlyphKerningGroups(glyph)
