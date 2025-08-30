from defcon import Glyph
import fontgadgets.extensions.unicode.properties
from fontgadgets.extensions.groups.kgroups import KerningGroup, GROUP_TERMINOLOGY_DOC
import weakref
from fontgadgets.decorators import (
    cached_method,
    font_cached_property,
    font_property_setter,
    font_property,
    defcon,
    FontGadgetsError,
)
from typing import (
    Dict,
    Any,
    Optional,
    Union,
    Tuple,
    Iterator,
    ItemsView,
    KeysView,
    ValuesView,
)
from fontgadgets import patch
from warnings import warn

MODULE_INFO = """
Glyph-Centric Kerning Management with Visual Side-Based Access.

This module introduces a glyph-centric API for manipulating UFO kerning data.
Instead of working with the font's global kerning dictionary, which is based
on logical pairs (first, second), this extension allows users to access and
modify kerning from the perspective of an individual glyph or kerning group,
using visual sides (left/right) to align with how designers think about
spacing visually.

While kerning data is ultimately stored in the font as `(glyph1, glyph2)`
pairs, this API doesn't provide kerning pairs. You are not manipulating pairs
directly. Instead, you are working with a dictionary for each visual side of a
**single reference glyph** where each key is a group or a glyph.

In this model:
    - The **reference glyph** is the one you are calling `.kerning` on.
    - The **key** in the `.left` or `.right` dictionary is the *other* glyph/group
    involved.
    - The **value** is the kerning amount that applies in that context.

The complete logical kerning pair is formed in the `font.kerning` without you
having to worry about the underlying mechanism, while correctly handling both
Left-to-Right and Right-to-Left writing directions.
""" + GROUP_TERMINOLOGY_DOC + """
The core of the module is the `glyph.kerning` property, which provides `.left`
and `.right` attributes. Crucially, these sides are defined from the perspective
of the glyph being acted upon, which may differ from the UFO specification's
logical `(first, second)` pair order. The `.left` and `.right` attributes
behave like dictionaries, mapping the other group/glyph to the kerning value.

- `glyph.kerning.left`:  Manages kerning where another glyph/group is visually
  on the **left side** of the reference glyph.
  (e.g., `font['T'].kerning.left['A']` refers to the pair `AT`).
- `glyph.kerning.right`: Manages kerning where another glyph/group is visually
  on the **right side** of the reference glyph.
  (e.g., `font['T'].kerning.right['A']` refers to the pair `TA`).

Usage:
"""
EXAMPLES_DOC = """
# --- Accessing Individual Kerning Values ---

# Import this module to add the kering group extensions
import fontgadgets.extensions.glyph.kerning

# Access the glyph in the usual way
glyph = font['T']

# Get kerning value when 'A' is on the right side of 'T'
kern_value = glyph.kerning.right['A']  # e.g., -60

# Get kerning value when 'Y' is on the left side of 'A'
left_kern = font['A'].kerning.left['Y']


# --- Setting & Updating Kerning Values ---

# Set kerning value
glyph.kerning.right['A'] = -50

# Set all right-side kerning, replacing existing values using glyph names
glyph.kerning.right = {'A': -55, 'V': -75}

# Update multiple kerning values at once for glyphs (doesn't affect group kerning)
glyph.kerning.right.update({'A': -60, 'V': -80, 'W': -45})

# Update using keyword arguments
glyph.kerning.left.update(T=-55, Y=-70)


# --- Deleting Kerning Values ---

# Delete kerning using a glyph name
del glyph.kerning.left['W']

# Clear all kerning on the left side
glyph.kerning.left.clear()

# Clear all kerning on the right side, including group kerning
glyph.kerning.right.clear(remove_group_kerning=True)

# --- Checking for Kerning Values ---

# Check if kerning exists with a glyph name
if 'W' in glyph.kerning.left:
    print(f"Kerning with `W` exists.")

# Check if kerning exists with default fallback
value = glyph.kerning.left.get('T')  # Returns None if no kerning


# --- Iterating Over Kerning Values ---

# Iterate over all left-side kerning values
# Note: While you can use glyph or group names (strings) to access, set,
# and delete individual kerning values, iterating over the kerning dictionary
# (e.g., via `.keys()` or `.items()`) yields `Context` objects as keys.
# These rich objects allow you to access the name via `.name` or the
# underlying Glyph/KerningGroup object via `.object`.
for other_glyph_or_group, kern_value in glyph.kerning.left.items():
    print(f"Kerning with {other_glyph_or_group.name}: {kern_value}")


# --- Retrieving All Kerning Values ---

# Get all kerning values on the right side
right_contexts = list(glyph.kerning.right.keys())

# Get all kerning values on the left side
left_values = list(glyph.kerning.left.values())


# --- Counting Kerning Values ---

# Check number of kerning values on each side
left_count = len(glyph.kerning.left)
right_count = len(glyph.kerning.right)


# --- Working with Kerning Groups ---

# Working with KerningGroup objects is similar to working with glyphs. However,
# since a kerning group is defined as either a left-side group or a right-side
# group, its .kerning property is a VisualSideKerning object, which behaves
# like a dictionary.

# For example, a left-side group can only be kerned against glyphs or groups
# that appear on its left. Its `.kerning` property manages kerning only for
# that side. In other words, `KerningGroup.kerning` doesn't have a 'left' or
# 'right' attributes, since the object only represents either left or right
# side.

V_left_group = font['V'].kerningGroups.left

if V_left_group:
    # group/glyph kerning
    V_left_group.kerning['o'] = -30

    # group/group kerning
    A_right_group = font['A'].kerningGroups.right
    if A_right_group:
        # left side group can only be kerned against a right side group and vice-versa
        A_right_group.kerning[V_left_group] = -35

# --- Retrieve All Kerning Values as a Dictionary ---

# Convert kerning to regular dictionary for processing
left_kerning_dict = dict(glyph.kerning.left.items())

# --- Copying Kerning Between Glyphs/Groups ---

# Copying kerning from one glyph to another
font["A"].kerning.left = font["Triangle"].kerning.left

# Copying kerning from one kerning group to another
leftGroup_1 = font["A"].kerningGroups.left
leftGroup_2 = font["Triangle"].kerningGroups.left
leftGroup_1.kerning = leftGroup_2.kerning
"""

__doc__ = MODULE_INFO + EXAMPLES_DOC

class Context:
    """
    Represents either a glyph or a kerning group within a kerning context. This
    provides a unified interface for handling both types of objects in kerning
    operations.
    """

    def __new__(cls, font: defcon.Font, context: Union[str, defcon.Glyph, KerningGroup]) -> "Context":
        # this class ensures that for a given font, only one instance exists per
        # glyph or group name. It achieves this by keeping instances on the font
        # object itself.
        if isinstance(context, str):
            name = context
        elif isinstance(context, defcon.Glyph):
            name = context.name
        elif isinstance(context, KerningGroup):
            name = context.prefixedName
        else:
            raise FontGadgetsError(f"Unsupported type for kerning context: '{type(context).__name__}'")
        if not hasattr(font.kerning, '_visualOrderKerningContexts'):
            font.kerning._visualOrderKerningContexts = {}
        cache = font.kerning._visualOrderKerningContexts
        instance = cache.get(name)
        if instance is not None:
            return instance
        instance = super().__new__(cls)
        cache[name] = instance
        return instance

    def __init__(self, font: defcon.Font, context: Union[str, KerningGroup]) -> None:
        # Prevent re-initialization if the instance already exists
        if hasattr(self, '_name'):
            return
        self._font = font
        self._object_ref = None
        if isinstance(context, str):
            name = context
        elif isinstance(context, defcon.Glyph):
            name = context.name
            self._object_ref = weakref.ref(context)
        elif isinstance(context, KerningGroup):
            name = context.prefixedName
            self._object_ref = weakref.ref(context)
        else:
            raise TypeError(f"Unsupported type for kerning context: '{type(context).__name__}'")
        self._name = name

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
            else:
                raise FontGadgetsError(f"Context `{self._name}` object not found in font or groups.")
        return obj

    @property
    def font(self) -> defcon.Font:
        return self._font

    @property
    def direction(self) -> Optional[str]:
        obj = self.object
        direction = None
        if isinstance(obj, defcon.Glyph):
            direction = obj.unicodeProperties.bidiType
        else:
            direction = obj.direction
        return direction

    def __eq__(self, other: Any) -> bool:
        if not isinstance(other, Context):
            return NotImplemented
        # Since instances are unique per font, we only need to check for identity.
        return self is other


    def __hash__(self) -> int:
        return hash(self._name)

    def __repr__(self):
        object_class = self.object.__class__.__name__
        if isinstance(self.object, KerningGroup):
            object_class += f" Side:'{self.object.side}'"
        return f"{object_class} Name: '{self.object.name}'"


class KerningAdaptor:
    """
    Manages glyph kerning by visual (left/right).

    This class provides an interface to work with kerning on a per-glyph or
    per-group basis, rather than treating kerning as a global font object.
    It's made for setting the kerning on a small scale per operation, as it
    can become slow for large changes. It handles both LTR and RTL writing
    directions, converting logical kerning values to visual left/right sides.
    First the adapter builds a mapping of visual side kerning for efficient
    lookups. This mapping is built once and reused for subsequent operations.
    This class is not built to be accessed directly by the user, but rather
    through the glyph's 'kerning' property. Storing this class in a variable is
    not recommended as it will not be updated when the font's kerning is
    changed.
    """

    def __init__(self, font: defcon.Font) -> None:
        self._font = font
        self._logical_order_kerning = font.kerning
        self._kerning_context_2_visual_side_kerning: Dict[Context, Dict[str, Dict[Context, int]]] = {}
        self._kerning_context_2_logical_side_kerning: Dict[Context, Any] = {}
        self._left_side_kerning: Dict[Context, Dict[Context, int]] = {}
        self._right_side_kerning: Dict[Context, Dict[Context, int]] = {}
        self._getGlyphDirection = lambda glyphName: self._font[glyphName].unicodeProperties.bidiType
        self._kg_adapter = font._kerningGroupsAdapter
        self._font_kern_groups = font.kerningGroups
        self._pending_changes: Dict[Any, Any] = {}
        self._getGlyphSetDirection = self._kg_adapter._getGlyphSetDirection
        for pair, value in self._logical_order_kerning.items():
            left, right = self._logicalToVisual(pair)
            self._left_side_kerning.setdefault(right, {})[left] = value
            self._right_side_kerning.setdefault(left, {})[right] = value

    @cached_method
    def _kerningEntryDirection(self, kerning_context: Union[str, Context]) -> Optional[str]:
        if isinstance(kerning_context, Context):
            return kerning_context.direction
        groups = self._font.groups
        glyphs = groups.get(kerning_context, [kerning_context, ])
        directions = {self._font[g].unicodeProperties.bidiType for g in glyphs}
        if len(directions) > 1:
            directions.discard(None)
            if len(directions) > 1:
                warn(
                    f"Ambiguous direction in group {kerning_context}, this group may will be dropped in "
                    "the exported fonts! For now let's consider the direction to be RTL, as"
                    "this situation is more likely to be the case."
                )
                return "R"
        return directions.pop()

    @cached_method
    def _getPairDirection(self, pair: Tuple[str, str]) -> Optional[str]:
        """
        Determines the writing direction (LTR or RTL) for a kerning pair.

        This method analyzes the glyphs within the pair to establish their
        collective writing direction, which is essential for correctly
        converting between logical and visual kerning orders.

        Args:
            pair (Tuple[str, str]): A tuple of two kerning context names
                (glyph names or prefixed group names).

        Returns:
            str: The writing direction of the pair ('L' for LTR, 'R' for RTL).
        """
        directions = set(map(self._kerningEntryDirection, pair))
        if len(directions) > 1:
            directions.discard(None)
            if len(directions) > 1:
                warn(
                    f"Ambiguous direction in pair {pair}, this pair may will be dropped in "
                    "the exported fonts! For now let's consider the direction to be RTL, as"
                    "this situation is more likely to be the case."
                )
                return "R"
        return directions.pop()

    @cached_method
    def _visualToLogical(self, visual_pair: Tuple[Context, Context]) -> Tuple[str, str]:
        """
        Converts a visual kerning pair (left, right) to a logical one.

        The conversion depends on the writing direction of the pair.

        Args:
            visual_pair (Tuple[Context, Context]): A tuple of
                two `Context` objects in visual order.

        Returns:
            Tuple[str, str]: A tuple of two names in logical order.
        """
        left, right = [e.name for e in visual_pair]
        direction = self._getPairDirection((left, right))
        if direction == "R":
            return right, left
        else:
            return left, right

    @cached_method
    def _logicalToVisual(self, logical_pair: Tuple[str, str]) -> Tuple[Context, Context]:
        """
        Converts a logical kerning pair (first, second) to a visual one.

        This is the inverse of `_visualToLogical`. The conversion depends
        on the writing direction of the pair.

        Args:
            logical_pair (Tuple[str, str]): A tuple of two names (glyph
                or group) in logical order.

        Returns:
            A tuple of two `Context` objects in visual order (left,
            right).
        """
        first, second = [Context(self._font , e) for e in logical_pair]
        direction = self._getPairDirection(logical_pair)
        if direction == "R":
            return second, first
        else:
            return first, second

    @cached_method
    def getKerningForSide(
        self,
        kerning_context: Union[str, Context],
        side: str,
    ) -> Dict[Context, int]:
        """
        Gets all kerning values on a specified visual side of a kerning_context
        (glyph/group).

        This method returns kerning values for all glyphs or groups that
        are positioned on the specified visual side (left or right) of
        the reference kerning context.

        Args:
            kerning_context: The reference glyph or group to query.
            side (str): The visual side to query ('left' or 'right').

        Returns:
            A dictionary mapping `Context` objects to their kerning
            values.

        Raises:
            ValueError: If side is not 'left' or 'right'.
        """
        if not isinstance(kerning_context, Context):
            kerning_context = Context(self._font, kerning_context)
        if side not in {"left", "right"}:
            raise ValueError("Side must be 'left' or 'right'")
        side_map = self._left_side_kerning if side == "left" else self._right_side_kerning
        return side_map.get(kerning_context, {})

    def updateKerningForSide(
        self,
        kerning_context: Union[str, Context],
        side: str,
        kerning_dict: Dict[Union[str, Context], int],
        prefer_group_kerning: bool = False,
    ) -> None:
        """
        Updates kerning values on a specified visual side of a glyph/group.

        This method applies new kerning values from a given dictionary.

        Args:
            kerning_context: The reference glyph or group to set kerning for.
            side (str): The visual side to modify ('left' or 'right').
            kerning_dict (dict): A dictionary where keys are other kerning
                contexts and values are the integer kerning amounts.
            prefer_group_kerning (bool): If True and `kerning_context` is a
                glyph in a kerning group on the specified side, kerning
                will be applied to the group instead of the glyph.
                Defaults to False.

        Raises:
            ValueError: If side is not 'left' or 'right'.
        """
        if side not in {"left", "right"}:
            raise ValueError("Side must be 'left' or 'right'")

        if not isinstance(kerning_context, Context):
            kerning_context = Context(self._font, kerning_context)
        if prefer_group_kerning and isinstance(kerning_context.object, defcon.Glyph):
            kerning_group = kerning_context.object.kerningGroups.getKerningGroupForVisualSide(side)
            if kerning_group is not None:
                kerning_context = Context(self._font, kerning_group)

        other_contexts_dict = {
            (e if isinstance(e, Context) else Context(self._font, e)): value
            for e, value in kerning_dict.items()
        }
        if side == 'left':
            # other contexts are on the left of the reference kerning_context
            visual_pairs = {(l, kerning_context): v for l, v in other_contexts_dict.items()}
        else:
            visual_pairs = {(kerning_context, r): v for r, v in other_contexts_dict.items()}
        self._logical_order_kerning.holdNotifications()
        for v_pair, value in visual_pairs.items():
            logical_pair = self._visualToLogical(v_pair)
            self._font.kerning[logical_pair] = value
        self._logical_order_kerning.releaseHeldNotifications()

    def removeKerningForSide(
        self,
        kerning_context: Union[str, Context],
        side: str,
        side_contexts_to_remove: Iterator[Union[str, Context]],
        remove_group_kerning: bool = False,
    ) -> None:
        """
        Removes specified kerning contexts on a visual side of glyph/group.

        This method deletes kerning between the `kerning_context` and a
        list of `side_contexts_to_remove` on the given visual side.

        Args:
            kerning_context: The reference glyph or group.
            side (str): The visual side where `side_contexts_to_remove` are located
                ('left' or 'right') in reference to the kerning_context.
            side_contexts_to_remove: An iterator of other kerning contexts to remove
                kerning with.
            remove_group_kerning (bool): If True and `kerning_context` is a
                glyph belonging to a kerning group on the specified side,
                the method will also attempt to remove kerning involving
                that group. Defaults to False.

        Raises:
            ValueError: If side is not 'left' or 'right'.

        Examples:
            # Remove kerning where 'T' is to the left of 'A'.
            adapter.removeKerningForSide('A', 'left', ['T'])
        """
        if side not in {"left", "right"}:
            raise ValueError("Side must be 'left' or 'right'")
        if not isinstance(kerning_context, Context):
            kerning_context = Context(self._font, kerning_context)
        reference_contexts = [kerning_context, ]

        if remove_group_kerning and isinstance(kerning_context.object, defcon.Glyph):
            kerning_group = kerning_context.object.kerningGroups.getKerningGroupForVisualSide(side)
            if kerning_group is not None:
                reference_contexts.append(Context(self._font, kerning_group))

        side_contexts_to_remove = {Context(self._font, e) if not isinstance(e, Context) else e
                                for e in side_contexts_to_remove}
        visual_kerning_to_remove = set()
        for e in reference_contexts:
            other_contexts = [o for o in self.getKerningForSide(e, side) if o in side_contexts_to_remove]
            if side == 'left':
                visual_pairs =[(l, e) for l in other_contexts]
            else:
                visual_pairs = [(e, r) for r in other_contexts]
            visual_kerning_to_remove.update(visual_pairs)

        self._logical_order_kerning.holdNotifications()
        for v_pair in visual_kerning_to_remove:
            logical_pair = self._visualToLogical(v_pair)
            del self._logical_order_kerning[logical_pair]
        self._logical_order_kerning.releaseHeldNotifications()


@font_cached_property(
    "Kerning.Changed",
    "Groups.Changed",
    "UnicodeData.Changed",
    "Glyph.UnicodesChanged",
    "Features.TextChanged",
    "Component.BaseGlyphChanged",
    "Glyph.ComponentWillBeAdded",
    "Glyph.ComponentWillBeDeleted",
    "Glyph.NameChanged",
    "Glyph.UnicodesChanged"
)
def _kerningAdaptor(font):
    # should not be accessed by any API or sroted in a varibale directly as its
    # data can become stale.
    return KerningAdaptor(font)


class VisualSideKerning:
    """
    A dict-like object for kerning on one side (left/right) of a glyph or group.

    This class provides an interface for accessing and modifying kerning
    on either the left or right visual side of a kerning context. It
    supports standard dictionary operations like getting, setting,
    deleting, and iterating over kerning values.
    """

    def __init__(self, reference_context: Union[Glyph, KerningGroup], side: str) -> None:
        self._reference_context = Context(reference_context.font, reference_context)
        self._side = side
        self._font = reference_context.font

    @property
    def _adaptor(self):
        return self._font._kerningAdaptor

    def _get_kerning_dict(self) -> Dict[Context, int]:
        return self._adaptor.getKerningForSide(self._reference_context, self._side)

    def __getitem__(self, other_context: Union[str, KerningGroup, Context, Glyph]) -> int:
        if isinstance(other_context, (KerningGroup, Glyph)):
            other_context = Context(self._font, other_context)
        return self._get_kerning_dict()[other_context]

    def __setitem__(self, other_context: Union[str, KerningGroup, Context, Glyph], value: int) -> None:
        if isinstance(other_context, (KerningGroup, Glyph)):
            other_context = Context(self._font, other_context)
        self._adaptor.updateKerningForSide(self._reference_context, self._side, {other_context: value})

    def __delitem__(self, other_context: Union[str, KerningGroup, Context, Glyph]) -> None:
        if isinstance(other_context, (KerningGroup, Glyph)):
            other_context = Context(self._font, other_context)
        self._adaptor.removeKerningForSide(self._reference_context, self._side, [other_context, ])

    def __repr__(self) -> str:
        return repr(self._get_kerning_dict())

    def __iter__(self) -> Iterator[Context]:
        return iter(self._get_kerning_dict())

    def __len__(self) -> int:
        return len(self._get_kerning_dict())

    def items(self) -> ItemsView[Context, int]:
        return self._get_kerning_dict().items()

    def keys(self) -> KeysView[Context]:
        return self._get_kerning_dict().keys()

    def values(self) -> ValuesView[int]:
        return self._get_kerning_dict().values()

    def get(self, other_context: Union[str, KerningGroup, Context], default: Any = None) -> Union[int, None]:
        if isinstance(other_context, KerningGroup):
            other_context = Context(self._font, other_context)
        return self._get_kerning_dict().get(other_context, default)

    def update(self, kerning_dict: Dict[Union[str, Context], int], **kwargs: int) -> None:
        """
        Updates the side kerning from a dictionary or keyword arguments.

        Examples:
            # Using a dictionary for a glyph
            glyph.kerning.left.update({'T': -60, 'Y': -40})

            # Using keyword arguments for group
            group.kerning.update(A=-50, V=-80)
        """
        d = dict(kerning_dict, **kwargs)
        self._adaptor.updateKerningForSide(self._reference_context, self._side, d)

    def clear(self, remove_group_kerning: bool = False) -> None:
        """
        Removes all kerning values for this glyph/group on this side.

        Args:
            remove_group_kerning (bool): If True, also removes kerning
                values involving the kerning group that the glyph belongs
                to on this side. Defaults to False.
        """
        keys_to_remove = list(self.keys())
        if keys_to_remove:
            self._adaptor.removeKerningForSide(
                self._reference_context,
                self._side,
                keys_to_remove,
                remove_group_kerning=remove_group_kerning,
            )


@patch.doc(examples=EXAMPLES_DOC)
class GlyphKerning:
    """
    Provides a glyph-centric API for working with kerning.

    This object provides `.left` and `.right` attributes to manage kerning from
    the glyph's perspective.

    - `.left`: Manages kerning pairs where other glyphs/groups are on the
      **left side** of this glyph.
    - `.right`: Manages kerning pairs where other glyphs/groups are on the
      **right side** of this glyph.

    Examples:
        {examples}
    """ 

    def __init__(self, reference_object) -> None:
        self._left = VisualSideKerning(reference_object, "left")
        self._right = VisualSideKerning(reference_object, "right")

    @property
    def left(self) -> VisualSideKerning:
        """
        Accesses the left-side kerning values for this glyph.

        Returns:
            A dictionary-like object that can be used to get, set, and
            delete kerning values where other glyphs/groups are on the
            left side of this glyph.

        Examples:
            # Get kerning with a specific glyph 'T'.
            value = glyph.kerning.left['T']

            # Set kerning with 'T'.
            glyph.kerning.left['T'] = -50

            # Remove kerning with 'T'.
            del glyph.kerning.left['T']

            # Update multiple values.
            glyph.kerning.left.update({'T': -55, 'Y': -60})
        """
        return self._left

    @left.setter
    def left(self, kerning_dict: Dict[Union[str, Context], int]) -> None:
        """
        Sets all left-side kerning values for this glyph, replacing any
        existing left-side kerning. This will not affect right-side kerning.

        Args:
            kerning_dict: A dictionary of kerning values where keys are
                other glyphs or groups, and values are kerning amounts.
        """
        self._left.clear()
        self._left.update(kerning_dict)

    @property
    def right(self) -> VisualSideKerning:
        """
        Accesses the right-side kerning values for this glyph.

        Returns:
            A dictionary-like object that can be used to get, set, and
            delete kerning values where other glyphs/groups are on the
            right side of this glyph.

        Examples:
            # Get kerning with a specific glyph 'A'.
            value = glyph.kerning.right['A']

            # Set kerning with 'A'.
            glyph.kerning.right['A'] = -60

            # Remove kerning with 'A'.
            del glyph.kerning.right['A']

            # Update multiple values.
            glyph.kerning.right.update({'V': -70, 'W': -45})
        """
        return self._right

    @right.setter
    def right(self, kerning_dict: Dict[Union[str, Context], int]) -> None:
        """
        Sets all right-side kerning values for this glyph, replacing any
        existing right-side kerning. This will not affect left-side kerning.

        Args:
            kerning_dict: A dictionary of kerning values where keys are
                other glyphs or groups, and values are kerning amounts.
        """
        self._right.clear()
        self._right.update(kerning_dict)

@font_property
@patch.doc(examples=EXAMPLES_DOC)
def kerning(glyph):
    """
    Provides a glyph-centric interface for managing kerning.

    This property returns a `GlyphKerning` object, which allows you to
    manipulate kerning values from the perspective of the current glyph.
    It provides two dictionary-like attributes: `.left` and `.right`.

    - `.left`: Manages kerning values where other glyphs/groups appear
    on the **left** of this glyph.

    - `.right`: Manages kerning values where other glyphs/groups appear
    on the **right** of this glyph.

    Returns:
        GlyphKerning: An object to manage the glyph's kerning.

    Examples:
        {examples}
    """
    return GlyphKerning(glyph)


@font_property_setter
def kerning(glyph, glyph_kerning: GlyphKerning):
    glyph.kerning.left = glyph_kerning.left
    glyph.kerning.right = glyph_kerning.right
