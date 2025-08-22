from fontgadgets.decorators import *
import fontgadgets.extensions.unicode.properties
from ufo2ft.featureWriters.kernFeatureWriter2 import Direction
from fontgadgets.extensions.groups.kgroups import KerningGroup
import defcon
from typing import Dict, Any, Union, Tuple, Iterator, ItemsView, KeysView, ValuesView
import weakref

class KerningEntry:
    """
    Represents a single entry in a kerning pair (a glyph or a group).

    This is an internal helper class that wraps a glyph or kerning group
    to provide a consistent interface for referencing the glyph or kerning
    group object inside a dictionary. Since the object is immutable it's
    hashable and can be used as dictionary keys.

    Args:
        font (defcon.Font): The font object that contains the entry.
        entry (Union[str, defcon.Glyph, KerningGroup]): The kerning entry
            which can be a glyph name string, a glyph object, or a
            kerning group object.

    Raises:
        TypeError: If the entry type is not supported (not str, Glyph, or
            KerningGroup).
        FontGadgetsError: If the referenced font or kerning entry object
            has been deleted or cannot be found.

    Examples:
        # Create from glyph name
        entry = KerningEntry(font, 'A')
 
        # Create from glyph object
        glyph = font['A']
        entry = KerningEntry(font, glyph)

        # Create from kerning group
        kgroup = glyph.kerningGroups.left
        entry = KerningEntry(font, kgroup)

        # Access properties
        name = entry.name  # Returns the name/prefixed name
        obj = entry.object  # Returns the actual glyph or group object
        direction = entry.direction  # Returns the writing direction
    """

    def __init__(self, font: defcon.Font, entry: Union[str, defcon.Glyph, KerningGroup]) -> None:
        self._font_ref = weakref.ref(font)
        self._object_ref = None
        if isinstance(entry, str):
            name = entry
        elif isinstance(entry, defcon.Glyph):
            name = entry.name
            self._object_ref = weakref.ref(entry)
        elif isinstance(entry, KerningGroup):
            name = entry.prefixedName
            self._object_ref = weakref.ref(entry)
        else:
            raise TypeError(f"Unsupported type for kerning entry: '{type(entry).__name__}'")
        self._name = name
        self._direction = None

    @property
    def name(self) -> str:
        return self._name

    @property
    def object(self) -> Union[defcon.Glyph, KerningGroup]:
        obj = self._object_ref() if self._object_ref is not None else None
        if obj is None:
            font = self.font
            if self._name in font:
                obj = font[self._name]
            elif self._name in font.groups:
                obj = font.kerningGroups.getKerningGroupFromPrefixedGroupName(self._name)
            if obj is not None:
                self._object_ref = weakref.ref(obj)
        if obj is None:
            raise FontGadgetsError(f"Kerning entry object is not found or has been deleted: '{self._name}'")
        return obj

    @property
    def font(self) -> defcon.Font:
        font = self._font_ref()
        if font is None:
            raise FontGadgetsError("The font object for this KerningEntry has been deleted.")
        return font

    def __eq__(self, other: Any) -> bool:
        if not isinstance(other, KerningEntry):
            return NotImplemented
        return self._name == other._name and self.font == other.font

    @property
    def direction(self) -> Direction:
        if self._direction is None:
            font = self.font 
            entry_obj = self.object
            if isinstance(entry_obj, defcon.Glyph):
                getDir = font.glyphsUnicodeProperties.getBidiTypeDirectionForGlyphName
                self._direction = getDir(self._name)
            elif isinstance(entry_obj, KerningGroup):
                self._direction = entry_obj.direction
        if self._direction is None:
            raise FontGadgetsError(f"Can't determine direction for '{self._name}'")
        return self._direction

    def __hash__(self) -> int:
        return hash(self._name)


class KerningAdapater:
    """
    Manages glyph kerning by visual (left/right) or logical sides.

    This class provides an interface to work with kerning on a per-glyph
    or per-group basis, rather than treating kerning as a global font
    object. It handles both LTR and RTL writing directions, converting
    logical kerning pairs to visual left/right sides. The class
    abstracts away font kerning complexities and provides methods to get
    and set kerning by glyph name and visual side.

    Args:
        font (defcon.Font): The font object containing kerning data.

    Examples:
        # Create a kerning adapter for a font
        adapter = KerningAdapater(font)
        
        # Get all kerning pairs where other glyphs are to the left of 'A'
        left_kerning = adapter.getKerningForKerningEntryForSide('A', 'left')
        
        # Set kerning values for 'A' when 'T' is on its left
        adapter.setKerningForKerningEntryForSide('A', 'left', {'T': -60})
        
        # Remove specific kerning pairs
        adapter.removeForKerningEntryForSideByKerningEntryList(
            'A', 'left', ['T']
        )
    """

    def __init__(self, font: defcon.Font) -> None:
        self._font = font
        self._logical_order_kerning = font.kerning
        self._kerning_entry_2_visual_side_kerning: Dict[KerningEntry, Dict[str, Dict[KerningEntry, int]]] = {}
        self._kerning_entry_2_logical_side_kerning: Dict[KerningEntry, Any] = {}
        self._left_side_kerning: Dict[KerningEntry, Dict[KerningEntry, int]] = {}
        self._right_side_kerning: Dict[KerningEntry, Dict[KerningEntry, int]] = {}
        self._kg_adapter = font._kerningGroupsAdapter
        self._font_kern_groups = font.kerningGroups
        self._pending_changes: Dict[Any, Any] = {}
        self._getGlyphSetDirection = self._kg_adapter._getGlyphSetDirection
        for pair, value in self._logical_order_kerning.items():
            left, right = self._logicalToVisual(pair)
            self._left_side_kerning.setdefault(left, {})[right] = value
            self._right_side_kerning.setdefault(right, {})[left] = value

    def _getPairDirection(self, pair: Tuple[str, str]) -> Direction:
        """
        Determines the writing direction (LTR or RTL) for a kerning pair.

        This method analyzes the glyphs within the pair to establish their
        collective writing direction, which is essential for correctly
        converting between logical and visual kerning orders.

        Args:
            pair (Tuple[str, str]): A tuple of two kerning entry names
                (glyph names or prefixed group names).

        Returns:
            Direction: The writing direction of the pair (e.g.,
            `Direction.RightToLeft`).
        """
        glyphs = self._font.kerning.getPairGlyphs(pair)
        return self._kg_adapter._getGlyphSetDirection(glyphs)

    def _visualToLogical(self, visual_pair: Tuple[KerningEntry, KerningEntry], direction: Union[Direction, None] = None) -> Tuple[str, str]:
        """
        Converts a visual kerning pair (left, right) to a logical one.

        The conversion depends on the writing direction of the pair. For
        LTR, (left, right) -> (second, first). For RTL, (left, right) ->
        (first, second).

        Args:
            visual_pair (Tuple[KerningEntry, KerningEntry]): A tuple of
                two `KerningEntry` objects in visual order.
            direction (Optional[Direction]): The writing direction. If
                None, it is determined automatically.

        Returns:
            Tuple[str, str]: A tuple of two names in logical order.
        """
        left, right = [e.name for e in visual_pair]
        if direction is None:
            direction = self._getPairDirection((left, right))
        if direction == Direction.RightToLeft:
            return left, right
        else:
            # This may seem confusing because the visual order is left to
            # right, but here we are considering what is on the left or
            # right of the reference glyph, in opposed to what is sitting
            # on left or right. Here the side depends on what is the
            # reference glyph.
            return right, left

    def _logicalToVisual(self, logical_pair: Tuple[str, str], direction: Union[Direction, None] = None) -> Tuple[KerningEntry, KerningEntry]:
        """
        Converts a logical kerning pair (first, second) to a visual one.

        This is the inverse of `_visualToLogical`. The conversion depends
        on the writing direction of the pair. For LTR, (first, second) ->
        (second, first). For RTL, (first, second) -> (first, second).

        Args:
            logical_pair (Tuple[str, str]): A tuple of two names (glyph
                or group) in logical order.
            direction (Optional[Direction]): The writing direction. If
                None, it will be determined automatically.

        Returns:
            A tuple of two `KerningEntry` objects in visual order (left,
            right).
        """
        first, second = [KerningEntry(self._font , e) for e in logical_pair]
        if direction is None:
            direction = self._getPairDirection(logical_pair)
        if direction == Direction.RightToLeft:
            return first, second
        else:
            return second, first

    def getKerningForKerningEntryForSide(
        self,
        kerning_entry: Union[str, defcon.Glyph, KerningGroup],
        side: str,
    ) -> Dict[KerningEntry, int]:
        """
        Gets all kerning pairs on a specified visual side of an entry.

        This method returns kerning values for all glyphs or groups that
        are positioned on the specified visual side (left or right) of
        the reference kerning entry.

        Args:
            kerning_entry: The reference glyph or group to query.
            side (str): The visual side to query ('left' or 'right').

        Returns:
            A dictionary mapping `KerningEntry` objects to their kerning
            values.

        Raises:
            ValueError: If side is not 'left' or 'right'.

        Examples:
            # Get all kerning pairs where other glyphs are to the left
            # of 'A'.
            left_kerning = adapter.getKerningForKerningEntryForSide(
                'A', 'left'
            )
            # left_kerning might be: {<KerningEntry 'T'>: -60}

            # Get kerning for a group on a right side of a glyph
            kgroup = font['B'].kerningGroups.right
            right_kerning = adapter.getKerningForKerningEntryForSide(
                kgroup, 'right'
            )
        """
        entry = KerningEntry(self._font, kerning_entry)
        if side not in {"left", "right"}:
            raise ValueError("Side must be 'left' or 'right'")
        if entry in self._kerning_entry_2_visual_side_kerning and side in self._kerning_entry_2_visual_side_kerning[entry]:
            # use the cache
            return self._kerning_entry_2_visual_side_kerning[entry][side]
 
        result: Dict[KerningEntry, int] = {}
        side_map = (self._left_side_kerning if side == "left" else self._right_side_kerning)
        result.update(side_map.get(entry, {}))
        self._kerning_entry_2_visual_side_kerning.setdefault(entry, {})[side] = result
        return result

    def setKerningForKerningEntryForSide(
        self,
        kerning_entry: Union[str, defcon.Glyph, KerningGroup],
        side: str,
        kerning_dict: Dict[Union[str, defcon.Glyph, KerningGroup], int],
        prefer_group_kerning: bool = False,
    ) -> None:
        """
        Sets or updates kerning values on a specified visual side of a glyph/group.

        This method applies new kerning values from a given dictionary.

        Args:
            kerning_entry: The reference glyph or group to set kerning for.
            side (str): The visual side to modify ('left' or 'right').
            kerning_dict (dict): A dictionary where keys are other kerning
                entries and values are the integer kerning amounts.
            prefer_group_kerning (bool): If True and `kerning_entry` is a
                glyph in a kerning group on the specified side, kerning
                will be applied to the group instead of the glyph.
                Defaults to False.

        Raises:
            ValueError: If side is not 'left' or 'right'.

        Examples:
            # Set kerning for 'A' when 'T' is on its left.
            adapter.setKerningForKerningEntryForSide(
                'A', 'left', {'T': -60}
            )

            # Set kerning for the left group of 'A' instead of 'A'.
            adapter.setKerningForKerningEntryForSide(
                'A', 'left', {'T': -60}, prefer_group_kerning=True
            )
        """
        if side not in {"left", "right"}:
            raise ValueError("Side must be 'left' or 'right'")

        kerning_entry_obj = KerningEntry(self._font, kerning_entry)
        if prefer_group_kerning and isinstance(kerning_entry_obj.object, defcon.Glyph):
            kerning_group = kerning_entry_obj.object.kerningGroups.getKerningGroupForVisualSide(side)
            if kerning_group is not None:
                kerning_entry_obj = KerningEntry(self._font, kerning_group)

        other_entries_dict = {KerningEntry(self._font, e): value for e, value in kerning_dict.items()}
        # default case is if side='left' and RTL or side='right' and LTR
        pairs = [(kerning_entry_obj.name, e.name) for e in other_entries_dict.keys()]
        direction = kerning_entry_obj.direction
        if (
            side == "right"
            and direction == Direction.RightToLeft
            or side == "left"
            and direction != Direction.RightToLeft
        ):
            pairs = [(l, r) for r, l in pairs]
        new_kerning = {p: v for p, v in zip(pairs, other_entries_dict.values())}
        self._logical_order_kerning.holdNotifications()
        self._font.kerning.update(new_kerning)
        self._logical_order_kerning.releaseHeldNotifications()

    def removeForKerningEntryForSideByKerningEntryList(
        self,
        kerning_entry: Union[str, defcon.Glyph, KerningGroup],
        side: str,
        other_entries: Iterator[Union[str, defcon.Glyph, KerningGroup]],
        remove_group_kerning: bool = False,
    ) -> None:
        """
        Removes specified kerning pairs on a visual side of glyph/group.

        This method deletes kerning between the `kerning_entry` and a
        list of `other_entries` on the given visual side.

        Args:
            kerning_entry: The reference glyph or group.
            side (str): The visual side where `other_entries` are located
                ('left' or 'right').
            other_entries: An iterator of other kerning entries to remove
                kerning with.
            remove_group_kerning (bool): If True and `kerning_entry` is a
                glyph belonging to a kerning group on the specified side,
                the method will also attempt to remove kerning involving
                that group. Defaults to False.

        Raises:
            ValueError: If side is not 'left' or 'right'.

        Examples:
            # Remove kerning where 'T' is to the left of 'A'.
            adapter.removeForKerningEntryForSideByKerningEntryList(
                'A', 'left', ['T']
            )
        """
        if side not in {"left", "right"}:
            raise ValueError("Side must be 'left' or 'right'")

        kerning_entry_obj = KerningEntry(self._font, kerning_entry)
        entries_to_process = [kerning_entry_obj]
        if remove_group_kerning and isinstance(kerning_entry_obj.object, defcon.Glyph):
            kerning_group = kerning_entry_obj.object.kerningGroups.getKerningGroupForVisualSide(side)
            if kerning_group is not None:
                entries_to_process.append(KerningEntry(self._font, kerning_group))

        other_entries_list = [KerningEntry(self._font, e) for e in other_entries]
        pairs_to_delete = [(kerning_entry_obj.name, other.name) for other in other_entries_list]
        direction = kerning_entry_obj.direction
        if (
                side == "right"
                and direction == Direction.RightToLeft
                or side == "left"
                and direction != Direction.RightToLeft
            ):
            pairs_to_delete = [(l, r) for r, l in pairs_to_delete]

        self._logical_order_kerning.holdNotifications()
        for pair in pairs_to_delete:
            if pair in self._logical_order_kerning:
                del self._logical_order_kerning[pair]
        self._logical_order_kerning.releaseHeldNotifications()


@font_cached_property(
    "Kerning.Changed", "Groups.Changed", "UnicodeData.Changed", "Features.Changed"
)
def _kerningAdaptor(font):
    return KerningAdapater(font)


class VisualSideKerning:
    """
    A dict-like object for kerning on one side of a glyph or group.

    This class provides an interface for accessing and modifying kerning
    on either the left or right visual side of a kerning entry. It
    supports standard dictionary operations like getting, setting,
    deleting, and iterating over kerning pairs.
    """

    def __init__(self, reference_entry: Union[defcon.Glyph, KerningGroup], side: str) -> None:
        self._reference_entry = reference_entry
        self._side = side
        self._font = reference_entry.font
        self._kerning_adaptor = self._font._kerningAdaptor

    def _get_kerning_dict(self) -> Dict[KerningEntry, int]:
        return self._kerning_adaptor.getKerningForKerningEntryForSide(self._reference_entry, self._side)

    def __getitem__(self, other_entry: Union[str, defcon.Glyph, KerningGroup]) -> int:
        key = KerningEntry(self._font, other_entry)
        return self._get_kerning_dict()[key]

    def __setitem__(self, other_entry: Union[str, defcon.Glyph, KerningGroup], value: int) -> None:
        self._kerning_adaptor.setKerningForKerningEntryForSide(self._reference_entry, self._side, {other_entry: value})

    def __delitem__(self, other_entry: Union[str, defcon.Glyph, KerningGroup]) -> None:
        self._kerning_adaptor.removeForKerningEntryForSideByKerningEntryList(self._reference_entry, self._side, [other_entry])

    def __repr__(self) -> str:
        return repr(self._get_kerning_dict())

    def __iter__(self) -> Iterator[KerningEntry]:
        return iter(self._get_kerning_dict())

    def __len__(self) -> int:
        return len(self._get_kerning_dict())

    def items(self) -> ItemsView[KerningEntry, int]:
        return self._get_kerning_dict().items()

    def keys(self) -> KeysView[KerningEntry]:
        return self._get_kerning_dict().keys()

    def values(self) -> ValuesView[int]:
        return self._get_kerning_dict().values()

    def get(self, kerning_entry: Union[str, defcon.Glyph, KerningGroup], default: Any = None) -> Union[int, None]:
        query_entry = KerningEntry(self._font, kerning_entry)
        return self._get_kerning_dict().get(query_entry, default)

    def update(self, kerning_dict: Dict[Union[str, defcon.Glyph, KerningGroup], int], **kwargs: int) -> None:
        """
        Updates the side kerning from a dictionary or keyword arguments.

        Examples:
            # Using a dictionary
            glyph.kerning.left.update({'T': -60, 'Y': -40})

            # Using keyword arguments
            glyph.kerning.right.update(A=-50, V=-80)
        """
        d = dict(kerning_dict, **kwargs)
        self._kerning_adaptor.setKerningForKerningEntryForSide(self._reference_entry, self._side, d)

    def clear(self, remove_group_kerning: bool = False) -> None:
        """
        Removes all kerning pairs for this glyph/group on this side.

        Args:
            remove_group_kerning (bool): If True, also removes kerning
                pairs involving the kerning group that the glyph belongs
                to on this side. Defaults to False.
        """
        keys_to_remove = list(self.keys())
        if keys_to_remove:
            self._kerning_adaptor.removeForKerningEntryForSideByKerningEntryList(
                self._reference_entry,
                self._side,
                keys_to_remove,
                remove_group_kerning=remove_group_kerning,
            )


class GlyphKerning:
    """
    Provides a glyph-centric API for working with kerning.

    This class offers interface for working with kerning data from a glyph's
    perspective, organizing pairs by visual sides (left and right). It provides
    dictionary-like access to kerning values via `.left` and `.right`
    properties.

    Examples:
        glyph = font['T']

        # Get all left-side kerning values.
        left_pairs = dict(glyph.kerning.left.items())

        # --- Working on glyph kerning using glyph names (string) ---
        glyph_A = font['A']
 
        # Set right kerning with glyph 'V'
        glyph_A.kerning.right['V] = -40
 
        # Get left kerning with glyph 'T'
        value = glyph_A.kerning.left['T']
 
        # Check if kerning exists with a glyph name
        if 'W' in glyph_A.kerning.left:
            print(f"Kerning with `W` exists.")

        # Delete kerning using a glyph nam
        del glyph_A.kerning.left['W']

        # Update left kerning with multiple glyphs by name
        glyph_A.kerning.left.update({'T': -55, 'Y': -65})

        # --- Using Glyph objects ---
        glyph_W = font['W']

        # Set left kerning with the Glyph object for 'W'
        glyph_A.kerning.left[glyph_W] = -50

        # --- Using prefixed group names (string) ---
        # Assume 'public.kern1.O' is a right-side kerning group
        right_group_name = 'public.kern1.O'
 
        # Set left kerning with the kerning group of 'O'
        glyph_A.kerning.left[right_group_name] = -25

        # Get the value
        kerning_value = glyph_A.kerning.left[right_group_name]

        # --- Using KerningGroup objects ---
        V_left_group = font['V'].kerningGroups.left
 
        if V_left_group:
            # Set right kerning with the KerningGroup object
            glyph_A.kerning.right[V_left_group] = -35

            # Get all kerning pairs on the right side
            right_pairs = dict(glyph_A.kerning.right.items())
            # right_pairs might look like:
            # {<KerningEntry 'V'>: -40, <KerningEntry 'public.kern1.V'>: -35}

        # Replace all left-side kerning with a new dictionary
        # that includes a KerningGroup object
        left_group_for_T = font['T'].kerningGroups.left
        if left_group_for_T:
            glyph_A.kerning.left = {
                'T': -50,
                left_group_for_T: -55, 
                font['Y']: -60
            }
        # Update multiple pairs at once.
        glyph_A.kerning.left.update({'Y': -60, 'W': -45})

        # Remove a kerning pair.
        del glyph_A.kerning.right['A']

        # Clear all kerning on one side.
        glyph_A.kerning.left.clear()
    """

    def __init__(self, reference_object) -> None:
        self._left = VisualSideKerning(reference_object, "left")
        self._right = VisualSideKerning(reference_object, "right")

    @property
    def left(self) -> VisualSideKerning:
        """
        Accesses the left-side kerning pairs for this glyph.

        Returns:
            A dictionary-like object that can be used to get, set, and
            delete kerning pairs where other glyphs/groups are on the
            left side of this glyph.

        Examples:
            # Get kerning with a specific glyph 'T'.
            value = glyph.kerning.left['T']

            # Set kerning with 'T'.
            glyph.kerning.left['T'] = -50

            # Remove kerning with 'T'.
            del glyph.kerning.left['T']

            # Update multiple pairs.
            glyph.kerning.left.update({'T': -55, 'Y': -60})
        """
        return self._left

    @left.setter
    def left(self, kerning_dict: Dict[Union[str, defcon.Glyph, KerningGroup], int]) -> None:
        """
        Sets the left-side kerning, replacing any existing pairs.

        Args:
            kerning_dict: A dictionary of kerning pairs where keys are
                other glyphs or groups, and values are kerning amounts.
        """
        self._left.clear()
        self._left.update(kerning_dict)

    @property
    def right(self) -> VisualSideKerning:
        """
        Accesses the right-side kerning pairs for this glyph.

        Returns:
            A dictionary-like object that can be used to get, set, and
            delete kerning pairs where other glyphs/groups are on the
            right side of this glyph.

        Examples:
            # Get kerning with a specific glyph 'A'.
            value = glyph.kerning.right['A']

            # Set kerning with 'A'.
            glyph.kerning.right['A'] = -60

            # Remove kerning with 'A'.
            del glyph.kerning.right['A']

            # Update multiple pairs.
            glyph.kerning.right.update({'V': -70, 'W': -45})
        """
        return self._right

    @right.setter
    def right(self, kerning_dict: Dict[Union[str, defcon.Glyph, KerningGroup], int]) -> None:
        """
        Sets the right-side kerning, replacing any existing pairs.

        Args:
            kerning_dict: A dictionary of kerning pairs where keys are
                other glyphs or groups, and values are kerning amounts.
        """
        self._right.clear()
        self._right.update(kerning_dict)


@font_property
def kerning(glyph):
    """
    Provides access to the visual kerning API for a glyph.

    This property returns a `GlyphKerning` object, which allows for
    intuitive, glyph-centric manipulation of kerning pairs via its `.left`
    and `.right` attributes. Each side behaves like a dictionary where
    keys are other glyphs or groups, and values are kerning amounts.

    Returns:
        GlyphKerning: An object to manage the glyph's kerning.

    Examples:
        # Basic kerning access
        glyph = font['T']

        # Get kerning value when 'A' is on the right side of 'T'
        kern_value = glyph.kerning.right['A']  # e.g., -60

        # Set kerning value
        glyph.kerning.right['A'] = -50

        # Set all right-side kerning, replacing existing pairs
        glyph.kerning.right = {'A': -55, 'V': -75}

        # Get kerning value when 'Y' is on the left side of 'A'
        left_kern = font['A'].kerning.left['Y']

        # Check if kerning exists with default fallback
        value = glyph.kerning.left.get('T')  # Returns None if no kerning

        # Iterate over all left-side kerning pairs
        for other_glyph, kern_value in glyph.kerning.left.items():
            print(f"Kerning with {other_glyph.name}: {kern_value}")

        # Get all kerning entries on the right side
        right_entries = list(glyph.kerning.right.keys())

        # Get all kerning values on the left side
        left_values = list(glyph.kerning.left.values())

        # Update multiple kerning pairs at once
        glyph.kerning.right.update({'A': -60, 'V': -80, 'W': -45})

        # Update using keyword arguments
        glyph.kerning.left.update(T=-55, Y=-70)

        # Remove a specific kerning pair
        del glyph.kerning.right['A']

        # Check number of kerning pairs on each side
        left_count = len(glyph.kerning.left)
        right_count = len(glyph.kerning.right)

        # Clear all kerning on the left side
        glyph.kerning.left.clear()

        # Clear all kerning on the right side, including group kerning
        glyph.kerning.right.clear(remove_group_kerning=True)

        # Working with kerning groups
        group = font.kerningGroups['public.kern1.O']
        glyph.kerning.left[group] = -30

        # Check if glyph has any kerning
        has_left_kerning = len(glyph.kerning.left) > 0
        has_right_kerning = len(glyph.kerning.right) > 0

        # Convert kerning to regular dictionary for processing
        left_kerning_dict = dict(glyph.kerning.left.items())
        right_kerning_dict = dict(glyph.kerning.right.items())
    """
    return GlyphKerning(glyph)


@font_property_setter
def kerning(glyph, glyph_kerning: GlyphKerning):
    glyph.kerning.left = glyph_kerning.left
    glyph.kerning.right = glyph_kerning.right
