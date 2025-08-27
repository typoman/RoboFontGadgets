from fontgadgets.extensions.groups import kgroups
from fontgadgets.decorators import FontGadgetsError
from utils import *
import copy


class GroupChangeChecker:
    """
    A context manager to verify that only specific groups in font.groups are
    changed during a test. 
    """

    def __init__(self, font, allowed_changes: list[str]):
        self.font = font
        self.allowed_changes = set(allowed_changes)
        self.initial_groups_state = None

    def __enter__(self):
        self.initial_groups_state = copy.deepcopy(self.font.groups)
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        # If an exception was raised inside the 'with' block, don't run checks.
        if exc_type is not None:
            return False  # Re-raise the exception.

        final_groups_state = self.font.groups
        all_group_names = set(self.initial_groups_state.keys()) | set(final_groups_state.keys())

        for group_name in all_group_names:
            if group_name in self.allowed_changes:
                continue  # This group was allowed to change.

            # This group was not expected to change, so its state must be identical.
            initial_members = tuple(self.initial_groups_state.get(group_name))
            final_members = tuple(final_groups_state.get(group_name))

            assert initial_members == final_members, (
                f"Unexpected change in group '{group_name}'. "
                f"Initial state: {initial_members}, Final state: {final_members}"
            )


def assertGroupsIntactExcept(font, allowed_changes: list[str]):
    """
    Helper function to create the GroupChangeChecker context manager.

    Args:
        font: The font object to monitor.
        allowed_changes (list[str]): A list of prefixed group names that are
                                     expected to be added, removed, or modified.
    """
    return GroupChangeChecker(font, allowed_changes)


def test_RE_GROUP_TAG():
    assert kgroups.RE_GROUP_TAG.match("public.kern1.sample") is not None
    assert kgroups.RE_GROUP_TAG.match("public.kern2.sample") is not None
    assert kgroups.RE_GROUP_TAG.match("public.kern3.sample") is None
    assert kgroups.RE_GROUP_TAG.match("other.tag.sample") is None


def test_isKerningGroup():
    assert kgroups.isKerningGroup("public.kern1.sample") is True
    assert kgroups.isKerningGroup("public.kern2.sample") is True
    assert kgroups.isKerningGroup("public.kern3.sample") is False
    assert kgroups.isKerningGroup("other.tag.sample") is False


def test_getGroupSideNameFromGroupOrder():
    assert kgroups.getGroupSideNameFromGroupOrder(0, False) == "right"
    assert kgroups.getGroupSideNameFromGroupOrder(1, False) == "left"
    assert kgroups.getGroupSideNameFromGroupOrder(0, True) == "left"
    assert kgroups.getGroupSideNameFromGroupOrder(1, True) == "right"
    with pytest.raises(AssertionError):
        kgroups.getGroupSideNameFromGroupOrder(0, "not_a_bool")


def test_glyphToKerningGroupMapping(defcon_font_1):
    adapter = defcon_font_1._kerningGroupsAdapter
    mapping_of_names = {
        glyph_name: {side: kg_obj.name for side, kg_obj in side_map.items()}
        for glyph_name, side_map in adapter._glyph_name_to_kerning_group_mapping.items()
    }
    expected = {
        "C": {"left": "O", "right": "C"},
        "Ccedilla": {"left": "O", "right": "C"},
        "D": {"left": "H", "right": "O"},
        "E": {"left": "H"},
        "O": {"left": "O", "right": "O"},
        "Ograve": {"left": "O", "right": "O"},
        "sad": {"left": "sin.fina", "right": "sad.init"},
        "seen": {"left": "sin.fina", "right": "sin.init"},
        "seen.init": {"right": "sin.init"},
        "tah": {"right": "sad.init"},
    }
    assert mapping_of_names == expected


def test_getGroupOrderFromGroupSideName():
    assert kgroups.getGroupLogicalOrderFromGroupSideName("left", False) == 1
    assert kgroups.getGroupLogicalOrderFromGroupSideName("right", False) == 0
    assert kgroups.getGroupLogicalOrderFromGroupSideName("left", True) == 0
    assert kgroups.getGroupLogicalOrderFromGroupSideName("right", True) == 1

    with pytest.raises(AssertionError):
        kgroups.getGroupLogicalOrderFromGroupSideName("left", "not_a_bool")

    with pytest.raises(AssertionError):
        kgroups.getGroupLogicalOrderFromGroupSideName("invalid_side", True)


def test_kerningGroups(defcon_font_1):
    # Reconstruct the expected dictionary structure for comparison
    result = {
        "left": {
            name: kg_obj.glyphSet
            for name, kg_obj in defcon_font_1.kerningGroups.left.items()
        },
        "right": {
            name: kg_obj.glyphSet
            for name, kg_obj in defcon_font_1.kerningGroups.right.items()
        },
    }
    expected = {
        "left": {
            "H": ["D", "E"],
            "O": ["C", "Ccedilla", "O", "Ograve"],
            "sin.fina": ["seen", "sad"],
        },
        "right": {
            "C": ["C", "Ccedilla"],
            "O": ["D", "O", "Ograve"],
            "sad.init": ["sad", "tah"],
            "sin.init": ["seen", "seen.init"],
        },
    }
    for side in expected:
        for group in expected[side]:
            result[side][group].sort()
            expected[side][group].sort()
    assert result == expected


def test_clearKerningGroups(defcon_font_1):
    expected = {"control": ("seen",)}
    defcon_font_1._kerningGroupsAdapter.clear()
    assert defcon_font_1.groups == expected


@pytest.mark.parametrize("glyphName, expected", [("seen", True), ("ain.medi", False)])
def test_isGrouped(defcon_font_1, glyphName, expected):
    assert defcon_font_1[glyphName].kerningGroups.isGrouped() is expected


@pytest.mark.parametrize(
    "glyphName, expected",
    [
        ("seen.init", None),
        ("ain.medi", None),
        ("sad", "sin.fina"),
        ("D", "H"),
        ("tah", None),
        ("C", "O"),
    ],
)
def test_leftSideKerningGroup(defcon_font_1, glyphName, expected):
    kg_obj = defcon_font_1[glyphName].kerningGroups.left
    if expected is None:
        assert kg_obj is None
    else:
        assert kg_obj.name == expected


@pytest.mark.parametrize(
    "glyphName, expected",
    [
        ("seen", "public.kern1.sin.fina"),
        ("D", "public.kern2.H"),
        ("C", "public.kern2.O"),
    ],
)
def test_leftSideKerningGroup_prefixedName(defcon_font_1, glyphName, expected):
    assert defcon_font_1[glyphName].kerningGroups.left.prefixedName == expected


@pytest.mark.parametrize(
    "glyphName, expected",
    [
        ("seen.init", "sin.init"),
        ("ain.medi", None),
        ("sad", "sad.init"),
        ("E", None),
        ("D", "O"),
        ("Ccedilla", "C"),
    ],
)
def test_rightSideKerningGroup(defcon_font_1, glyphName, expected):
    kg_obj = defcon_font_1[glyphName].kerningGroups.right
    if expected is None:
        assert kg_obj is None
    else:
        assert kg_obj.name == expected


@pytest.mark.parametrize(
    "glyphName, expected",
    [
        ("seen.init", "public.kern2.sin.init"),
        ("ain.medi", None),
        ("sad", "public.kern2.sad.init"),
        ("E", None),
        ("D", "public.kern1.O"),
        ("Ccedilla", "public.kern1.C"),
    ],
)
def test_rightSideKerningGroup_prefixedName(defcon_font_1, glyphName, expected):
    kg_obj = defcon_font_1[glyphName].kerningGroups.right
    if expected is None:
        assert kg_obj is None
    else:
        assert kg_obj.prefixedName == expected


@pytest.mark.parametrize(
    "glyphName, group_name_to_set",
    [
        ("seen.init", "test1"),  # rtl
        ("D", "test2"),  # ltr
        ("sad", None),
    ],
)
def test_setLeftSideKerningGroup(defcon_font_1, glyphName, group_name_to_set):
    g = defcon_font_1[glyphName]

    # Define which groups are allowed to change for each test case
    if glyphName == "seen.init":
        allowed = ["public.kern1.test1"]  # New RTL group on left side -> kern1
    elif glyphName == "D":
        allowed = ["public.kern2.H", "public.kern2.test2"]  # Change LTR group
    else:
        allowed = ["public.kern1.sin.fina"]  # Remove from RTL group

    with assertGroupsIntactExcept(defcon_font_1, allowed):
        g.kerningGroups.left = group_name_to_set

    result_group = g.kerningGroups.left
    if group_name_to_set is None:
        assert result_group is None
    else:
        assert result_group.name == group_name_to_set


@pytest.mark.parametrize(
    "glyphName, group_name_to_set",
    [
        ("seen", "test2"),  # rtl
        ("Ccedilla", "C2"),  # ltr
        ("E", None),
    ],
)
def test_setRightSideKerningGroup(defcon_font_1, glyphName, group_name_to_set):
    g = defcon_font_1[glyphName]

    if glyphName == "seen":
        allowed = ["public.kern2.sin.init", "public.kern2.test2"]  # Change RTL group
    elif glyphName == "Ccedilla":
        allowed = ["public.kern1.C", "public.kern1.C2"]  # Change LTR group
    else:  # E
        allowed = []  # E has no right side group, so nothing should change

    with assertGroupsIntactExcept(defcon_font_1, allowed):
        g.kerningGroups.right = group_name_to_set

    result_group = g.kerningGroups.right
    if group_name_to_set is None:
        assert result_group is None
    else:
        assert result_group.name == group_name_to_set


@pytest.mark.parametrize(
    "glyphNames, expected",
    [
        (
            ("seen", "tah"),
            {"left": {"sin.fina"}, "right": {"sad.init", "sin.init"}},
        ),  # rtl
        (("C", "D", "O"), {"left": {"O", "H"}, "right": {"O", "C"}}),  # ltr
        (("C", "seen.init"), {"left": {"O"}, "right": {"C", "sin.init"}}),  # ltr
        (("ain.medi",), {"left": set(), "right": set()}),
    ],
)
def test_getKerningGroupsForGlyphSet(defcon_font_1, glyphNames, expected):
    result_objs = defcon_font_1._kerningGroupsAdapter.getKerningGroupsForGlyphSet(
        glyphNames
    )
    result_names = {side: {kg.name for kg in kgs} for side, kgs in result_objs.items()}
    assert result_names == expected


@pytest.mark.parametrize(
    "glyphNames, expected",
    [
        (
            ("seen", "tah"),
            {
                "left": {"public.kern1.sin.fina"},
                "right": {"public.kern2.sad.init", "public.kern2.sin.init"},
            },
        ),  # rtl
        (
            ("C", "D", "O"),
            {
                "left": {"public.kern2.O", "public.kern2.H"},
                "right": {"public.kern1.O", "public.kern1.C"},
            },
        ),  # ltr
        (
            ("C", "seen.init"),
            {
                "left": {"public.kern2.O"},
                "right": {"public.kern1.C", "public.kern2.sin.init"},
            },
        ),  # ltr
        (("ain.medi",), {"left": set(), "right": set()}),
    ],
)
def test_getKerningGroupsForGlyphSet_prefixedName(defcon_font_1, glyphNames, expected):
    result_objs = defcon_font_1._kerningGroupsAdapter.getKerningGroupsForGlyphSet(
        glyphNames
    )
    result_prefixed_names = {
        side: {kg.prefixedName for kg in kgs} for side, kgs in result_objs.items()
    }
    assert result_prefixed_names == expected


def test_groups_cleanup(kerning_with_missing_glyphs):
    f = kerning_with_missing_glyphs
    f.groups.cleanup()
    assert f.groups == {
        "group1": ["A", "B", "C"],
        "group2": ["D", "E"],
        "group_with_missing_glyph": ["A"],
    }


def test_setKerningGroup_mixed_direction_error(defcon_font_1):
    # Test that setting a group with mixed-direction glyphs raises an error.
    font = defcon_font_1
    mixed_members = ["C", "seen"]  # LTR and RTL
    with pytest.raises(
        FontGadgetsError,
        match="Mixed direction glyphs in the set ",
    ):
        font._kerningGroupsAdapter.setKerningGroupFromNameSideAndMembers(
            "mixed", "left", mixed_members
        )


def test_convertToPrefixedGroupName_with_warning(defcon_font_1):
    # Test that a warning is issued if the group name already has a prefix."""
    with pytest.warns(
        UserWarning, match="Kerning group name already starts with a prefix"
    ):
        result = defcon_font_1._kerningGroupsAdapter._convertKerningGroupNameToPrefixedGroupName(
            "public.kern1.test", "left", False
        )
    assert result == "public.kern2.test"


@pytest.mark.parametrize(
    "glyphNames, expected_names, expected_prefixed",
    [
        (("C", "D"), {"O", "H"}, {"public.kern2.O", "public.kern2.H"}),
        (("E", "seen.init"), {"H"}, {"public.kern2.H"}),
        (("seen", "sad"), {"sin.fina"}, {"public.kern1.sin.fina"}),
    ],
)
def test_getLeftSideKerningGroupsForGlyphSet(
    defcon_font_1, glyphNames, expected_names, expected_prefixed
):
    result_objs = (
        defcon_font_1._kerningGroupsAdapter.getLeftSideKerningGroupsForGlyphSet(
            glyphNames
        )
    )
    names = {kg.name for kg in result_objs}
    prefixed_names = {kg.prefixedName for kg in result_objs}
    assert names == expected_names
    assert prefixed_names == expected_prefixed


def test_getSide_prefixed_but_none(defcon_font_1):
    # Test getSide when the glyph has no group."""
    glyph = defcon_font_1["E"]  # 'E' has a left group but no right group
    assert glyph.kerningGroups.right is None


def test_remove_kerning_groups(defcon_font_1):
    # Test removeLeftSide and removeRightSide methods."""
    glyph = defcon_font_1["C"]  # Has left 'O' and right 'C'
    assert glyph.kerningGroups.left is not None
    assert glyph.kerningGroups.right is not None

    with assertGroupsIntactExcept(defcon_font_1, ["public.kern2.O"]):
        del glyph.kerningGroups.left
    assert glyph.kerningGroups.left is None
    assert glyph.kerningGroups.right is not None  # Right side should be unaffected

    with assertGroupsIntactExcept(defcon_font_1, ["public.kern1.C"]):
        del glyph.kerningGroups.right
    assert glyph.kerningGroups.left is None
    assert glyph.kerningGroups.right is None  # Right side should now be gone


@pytest.mark.parametrize(
    "glyphName, expected_names, expected_prefixed",
    [
        (
            "C",
            {"left": "O", "right": "C"},
            {"left": "public.kern2.O", "right": "public.kern1.C"},
        ),
        ("E", {"left": "H", "right": None}, {"left": "public.kern2.H", "right": None}),
        ("ain.medi", {"left": None, "right": None}, {"left": None, "right": None}),
    ],
)
def test_getKerningGroupsForGlyph(
    defcon_font_1, glyphName, expected_names, expected_prefixed
):
    # Tests accessing a glyph's kerningGroups properties.
    glyph = defcon_font_1[glyphName]

    # Test names
    left_kg = glyph.kerningGroups.left
    right_kg = glyph.kerningGroups.right
    result_names = {
        "left": left_kg.name if left_kg else None,
        "right": right_kg.name if right_kg else None,
    }
    assert result_names == expected_names

    # Test prefixed names
    result_prefixed = {
        "left": left_kg.prefixedName if left_kg else None,
        "right": right_kg.prefixedName if right_kg else None,
    }
    assert result_prefixed == expected_prefixed


def test_delete_left_kerning_group(defcon_font_1):
    # Test `del glyph.kerningGroups.left`."""
    glyph = defcon_font_1["D"]  # Left: H, Right: O
    assert glyph.kerningGroups.left.name == "H"
    with assertGroupsIntactExcept(defcon_font_1, ["public.kern2.H"]):
        del glyph.kerningGroups.left
    assert glyph.kerningGroups.left is None
    assert glyph.kerningGroups.right.name == "O"  # Right side unaffected


def test_delete_right_kerning_group_bug(defcon_font_1):
    # Test `del glyph.kerningGroups.right`."""
    glyph = defcon_font_1["D"]  # Left: H, Right: O
    assert glyph.kerningGroups.left.name == "H"
    assert glyph.kerningGroups.right.name == "O"
    with assertGroupsIntactExcept(defcon_font_1, ["public.kern1.O"]):
        del glyph.kerningGroups.right
    assert glyph.kerningGroups.right is None
    assert glyph.kerningGroups.left.name == "H"  # Left side should be unaffected


def test_setKerningGroup_remove_last_member(defcon_font_1):
    # Test that a group is deleted when its last member is removed via the new method.
    font = defcon_font_1
    adapter = font._kerningGroupsAdapter
    group_name = "H"
    side = "left"
    prefixed_name = "public.kern2.H"

    assert prefixed_name in font.groups

    # Remove one member
    with assertGroupsIntactExcept(defcon_font_1, [prefixed_name]):
        adapter.setKerningGroupFromNameSideAndMembers(group_name, side, ["E"])
    assert prefixed_name in font.groups
    assert font.groups[prefixed_name] == ["E"]
    assert font["D"].kerningGroups.left is None

    # Remove the last member, which should delete the group
    adapter = font._kerningGroupsAdapter
    with assertGroupsIntactExcept(defcon_font_1, [prefixed_name]):
        adapter.setKerningGroupFromNameSideAndMembers(group_name, side, [])
    assert prefixed_name not in font.groups
    assert group_name not in font.kerningGroups.left


@pytest.mark.parametrize(
    "glyphNames, expected_names, expected_prefixed",
    [
        (("C", "D"), {"O", "C"}, {"public.kern1.O", "public.kern1.C"}),
        (("E", "tah"), {"sad.init"}, {"public.kern2.sad.init"}),
        (
            ("seen", "sad"),
            {"sin.init", "sad.init"},
            {"public.kern2.sin.init", "public.kern2.sad.init"},
        ),
        (("ain.medi",), set(), set()),
    ],
)
def test_getRightSideKerningGroupsForGlyphSet(
    defcon_font_1, glyphNames, expected_names, expected_prefixed
):
    result_objs = (
        defcon_font_1._kerningGroupsAdapter.getRightSideKerningGroupsForGlyphSet(
            glyphNames
        )
    )
    names = {kg.name for kg in result_objs}
    prefixed_names = {kg.prefixedName for kg in result_objs}
    assert names == expected_names
    assert prefixed_names == expected_prefixed


@pytest.mark.parametrize(
    "glyphName, side, expected",
    [
        ("O", "left", ["C", "Ccedilla", "O", "Ograve"]),
        ("O", "right", ["D", "O", "Ograve"]),
        ("E", "left", ["D", "E"]),
        ("E", "right", []),
        ("seen", "left", ["seen", "sad"]),
        ("seen", "right", ["seen", "seen.init"]),
        ("ain.medi", "left", []),
        ("ain.medi", "right", []),
    ],
)
def test_getSideMembers(defcon_font_1, glyphName, side, expected):
    glyph = defcon_font_1[glyphName]
    if side == "left":
        kg_obj = glyph.kerningGroups.left
    else:
        kg_obj = glyph.kerningGroups.right

    members = kg_obj.glyphSet if kg_obj else []
    assert sorted(members) == sorted(expected)


def test_setSide_with_warning(defcon_font_1):
    # Test setSide with a prefixed group name issues a warning
    glyph = defcon_font_1["E"]
    assert glyph.kerningGroups.left.name == "H"
    allowed_changes = ["public.kern2.H", "public.kern2.newGroup"]
    with pytest.warns(
        UserWarning, match="Kerning group name already starts with a prefix"
    ), assertGroupsIntactExcept(defcon_font_1, allowed_changes):
        glyph.kerningGroups.left = "public.kern1.newGroup"
    assert glyph.kerningGroups.left.name == "newGroup"
    assert "public.kern2.newGroup" in glyph.font.groups
    assert "E" in glyph.font.groups["public.kern2.newGroup"]
    assert "E" not in glyph.font.groups["public.kern2.H"]


def test_automatic_glyph_reassignment(defcon_font_1):
    # Tests that a glyph is automatically removed from its old group when
    # assigned to a new one on the same side.
    font = defcon_font_1
    glyph = font["D"]
    old_group_name = "H"
    new_group_name = "new_H"

    # Pre-condition: 'D' is in the left group 'H'
    assert glyph.kerningGroups.left.name == old_group_name
    assert "D" in font.kerningGroups.left[old_group_name].glyphSet
    assert new_group_name not in font.kerningGroups.left

    allowed_changes = ["public.kern2.H", "public.kern2.new_H"]
    with assertGroupsIntactExcept(defcon_font_1, allowed_changes):
        # Action: Reassign 'D' to a new left-side group
        glyph.kerningGroups.left = new_group_name

    # Post-condition: 'D' should be in 'new_H' and removed from 'H'
    assert glyph.kerningGroups.left.name == new_group_name
    assert "D" in font.kerningGroups.left[new_group_name].glyphSet
    assert "D" not in font.kerningGroups.left[old_group_name].glyphSet


def test_setKerningGroup_with_redundant_prefix_handling(defcon_font_1):
    # Tests that using a prefixed group name issues a warning and correctly strips the prefix.
    font = defcon_font_1
    prefixed_name = "public.kern1.prefixedGroup"
    expected_raw_name = "prefixedGroup"
    # LTR glyph 'D' on the left side should result in a public.kern2 group
    expected_final_prefixed_name = "public.kern2.prefixedGroup"

    allowed_changes = ["public.kern2.H", expected_final_prefixed_name]
    with pytest.warns(
        UserWarning, match="Kerning group name already starts with a prefix"
    ), assertGroupsIntactExcept(defcon_font_1, allowed_changes):
        font._kerningGroupsAdapter.setKerningGroupFromNameSideAndMembers(
            prefixed_name, "left", ["D"]
        )

    # Check that the group was created correctly
    assert expected_final_prefixed_name in font.groups
    assert font.groups[expected_final_prefixed_name] == ["D"]
    assert expected_raw_name in font.kerningGroups.left
    assert font["D"].kerningGroups.left.name == expected_raw_name


def test_kerning_group_rename(defcon_font_1):
    # Test renaming a KerningGroup via its name property
    font = defcon_font_1
    old_name = "H"
    new_name = "newH"
    old_prefixed_name = "public.kern2.H"
    new_prefixed_name = "public.kern2.newH"
    members = ["D", "E"]
    assert old_name in font.kerningGroups.left
    assert new_name not in font.kerningGroups.left
    assert old_prefixed_name in font.groups
    assert sorted(font.groups[old_prefixed_name]) == sorted(members)
    kg_obj = font.kerningGroups.left[old_name]

    with assertGroupsIntactExcept(font, [old_prefixed_name, new_prefixed_name]):
        kg_obj.name = new_name

    assert old_name not in font.kerningGroups.left
    assert new_name in font.kerningGroups.left
    assert old_prefixed_name not in font.groups
    assert new_prefixed_name in font.groups
    assert sorted(font.groups[new_prefixed_name]) == sorted(members)
    assert font["D"].kerningGroups.left.name == new_name
    assert font["E"].kerningGroups.left.name == new_name
    assert font.kerningGroups.left[new_name].name == new_name


def test_kerning_group_rename_to_existing(defcon_font_1):
    # Test that renaming a group to an existing name raises an error
    font = defcon_font_1
    side_manager = font.kerningGroups.left
    kg_obj_H = side_manager["H"]

    # 'O' already exists as a left-side group
    with pytest.raises(ValueError, match="A kerning group named 'O' already exists"):
        kg_obj_H.name = "O"


def test_kerning_group_rename_to_same_name(defcon_font_1):
    # Test that renaming a group to its current name does nothing
    font = defcon_font_1
    kg_obj = font.kerningGroups.left["H"]
    original_groups = dict(font.groups)

    kg_obj.name = "H"  # Set to the same name

    assert font.groups == original_groups


def test_kerning_group_rename_invalid_type(defcon_font_1):
    # Test that setting a non-string name raises a TypeError
    kg_obj = defcon_font_1.kerningGroups.left["H"]
    with pytest.raises(TypeError, match="Group name must be a string."):
        kg_obj.name = 123


def test_kerning_group_set_glyphset_same_direction(defcon_font_1):
    # Test setting glyphSet with members of the same direction
    font = defcon_font_1
    kg_obj = font.kerningGroups.left["H"]  # LTR group with ['D', 'E']
    prefixed_name = "public.kern2.H"
    new_members = ["D", "F"]  # 'F' is also LTR

    # Pre-conditions
    assert sorted(kg_obj.glyphSet) == ["D", "E"]
    assert font["F"].kerningGroups.left is None

    with assertGroupsIntactExcept(font, [prefixed_name]):
        # Action
        kg_obj.glyphSet = new_members

    # Post-conditions
    new_kg_obj = font.kerningGroups.left["H"]
    assert sorted(new_kg_obj.glyphSet) == sorted(new_members)
    assert sorted(font.groups[prefixed_name]) == sorted(new_members)
    assert font["E"].kerningGroups.left is None  # 'E' should be removed
    assert font["F"].kerningGroups.left.name == "H"  # 'F' should be added


def test_kerning_group_set_glyphset_change_direction(defcon_font_1):
    # Test setting glyphSet that changes the group's direction from LTR to RTL
    font = defcon_font_1
    kg_obj = font.kerningGroups.left["H"]  # LTR group
    old_prefixed_name = "public.kern2.H"
    new_prefixed_name = "public.kern1.H"  # Left side for RTL is kern1
    new_rtl_members = ["seen", "sad"]

    # Pre-conditions
    assert old_prefixed_name in font.groups
    assert new_prefixed_name not in font.groups

    allowed_changes = [old_prefixed_name, new_prefixed_name, "public.kern1.sin.fina"]
    with assertGroupsIntactExcept(font, allowed_changes):
        # Action
        kg_obj.glyphSet = new_rtl_members

    new_kg_obj = font.kerningGroups.left["H"]

    # Post-conditions
    assert old_prefixed_name not in font.groups
    assert new_prefixed_name in font.groups
    assert sorted(font.groups[new_prefixed_name]) == sorted(new_rtl_members)
    # The object's internal state should be updated
    assert new_kg_obj.prefixedName == new_prefixed_name
    assert new_kg_obj.direction == "R"
    assert sorted(new_kg_obj.glyphSet) == sorted(new_rtl_members)


def test_kerning_group_set_glyphset_to_empty(defcon_font_1):
    # Test setting glyphSet to an empty list
    font = defcon_font_1
    kg_obj = font.kerningGroups.left["H"]
    prefixed_name = kg_obj.prefixedName
    original_members = list(kg_obj.glyphSet)

    with assertGroupsIntactExcept(font, [prefixed_name]):
        # Action
        kg_obj.glyphSet = []

    # Post-conditions for the object might not be what's expected,
    # as the group might be deleted. Let's check the font state.
    assert prefixed_name not in font.groups
    assert "H" not in font.kerningGroups.left

    for glyph_name in original_members:
        assert font[glyph_name].kerningGroups.left is None


def test_kerning_group_set_glyphset_mixed_direction_error(defcon_font_1):
    # Test that setting glyphSet with mixed directions raises an error
    font = defcon_font_1
    kg_obj = font.kerningGroups.left["H"]
    mixed_members = ["D", "seen"]  # LTR and RTL

    with pytest.raises(FontGadgetsError, match="Mixed direction glyphs in the set"):
        kg_obj.glyphSet = mixed_members


def test_kerning_group_set_glyphset_invalid_type(defcon_font_1):
    # Test that setting glyphSet with a non-list/tuple raises a TypeError
    kg_obj = defcon_font_1.kerningGroups.left["H"]
    with pytest.raises(
        TypeError, match="Glyph set must be a list or tuple of glyph names."
    ):
        kg_obj.glyphSet = "not a list"


def test_set_side_with_kerning_group_object(defcon_font_1):
    # Tests setting a glyph's group using a KerningGroup object.
    font = defcon_font_1
    glyph_E = font["E"]
    glyph_D = font["D"]

    # Pre-conditions
    assert glyph_E.kerningGroups.right is None
    assert glyph_D.kerningGroups.left.name == "H"

    # Get a KerningGroup object to assign
    group_O_right = font.kerningGroups.right["O"]
    group_H_left = font.kerningGroups.left["H"]

    with assertGroupsIntactExcept(font, ["public.kern1.O"]):
        # Action 1: Assign a right-side group object to the right side
        glyph_E.kerningGroups.right = group_O_right

    # Post-condition 1
    assert glyph_E.kerningGroups.right.name == "O"
    assert "E" in font.kerningGroups.right["O"].glyphSet

    with assertGroupsIntactExcept(font, []):  # No change expected
        # Action 2: Assign a left-side group object to the left side (reassignment)
        glyph_D.kerningGroups.left = group_H_left  # This is a no-op but tests the logic
    assert glyph_D.kerningGroups.left.name == "H"

    # Action 3: Attempt to assign a group to the wrong side
    with pytest.raises(
        ValueError,
        match="Cannot assign a 'right' side KerningGroup to the 'left' side of the glyph.",
    ):
        glyph_E.kerningGroups.left = group_O_right


@pytest.mark.parametrize(
    "glyphName, expected_groups",
    [
        ("C", {("O", "left"), ("C", "right")}),  # Has both left and right groups
        ("E", {("H", "left")}),  # Has only a left group
        ("seen.init", {("sin.init", "right")}),  # Has only a right group
        ("ain.medi", set()),  # Has no groups
    ],
)
def test_glyph_kerning_groups_iterator(defcon_font_1, glyphName, expected_groups):
    # Tests iterating over the kerning groups of a glyph.
    glyph = defcon_font_1[glyphName]
    # Collect the (name, side) tuples from the iterator
    found_groups = {(kg.name, kg.side) for kg in glyph.kerningGroups}
    assert found_groups == expected_groups
