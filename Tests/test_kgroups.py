from fontgadgets.extensions.groups import kgroups
from utils import *

"""
todo:
- setKerningGroups: where there is a glyph with two groups for the same side.
- groupNamePrefixes test for:
    getRightSideKerningGroupNamesForGlyphs(font, glyphNames, groupNamePrefixes=False)
    getLeftSideKerningGroupNamesForGlyphs(font, glyphNames, groupNamePrefixes=False)
"""


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


def test_constants():
    assert kgroups.GROUP_SIDE_TAG == ("public.kern1.", "public.kern2.")
    assert kgroups.ORDER_2_SIDE == {0: "left", 1: "right"}
    assert kgroups.SIDE_2_ORDER == {"left": 0, "right": 1}


def test_getGroupSideNameFromGroupOrder():
    assert kgroups.getGroupSideNameFromGroupOrder(0, False) == "right"
    assert kgroups.getGroupSideNameFromGroupOrder(1, False) == "left"
    assert kgroups.getGroupSideNameFromGroupOrder(0, True) == "left"
    assert kgroups.getGroupSideNameFromGroupOrder(1, True) == "right"
    with pytest.raises(AssertionError):
        kgroups.getGroupSideNameFromGroupOrder(0, "not_a_bool")


def test_glyphToKerningGroupMapping(defcon_font_1):
    result = {
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
    assert defcon_font_1.kerningGroups._glyphToKerningGroupMapping == result


def test_getGroupOrderFromGroupSideName():
    assert kgroups.getGroupOrderFromGroupSideName("left", False) == 1
    assert kgroups.getGroupOrderFromGroupSideName("right", False) == 0
    assert kgroups.getGroupOrderFromGroupSideName("left", True) == 0
    assert kgroups.getGroupOrderFromGroupSideName("right", True) == 1

    with pytest.raises(AssertionError):
        kgroups.getGroupOrderFromGroupSideName("left", "not_a_bool")

    with pytest.raises(AssertionError):
        kgroups.getGroupOrderFromGroupSideName("invalid_side", True)


def test_kerningGroups(defcon_font_1):
    result = {
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
    assert defcon_font_1.kerningGroups.items() == result


@pytest.mark.parametrize(
    "kernGroups, expected",
    [
        ({}, ({"control": ("seen",)})),
        (
            {"left": {"H": ["D", "E"]}},
            {"control": ("seen",), "public.kern2.H": ["D", "E"]},
        ),  # left side
        (
            {"left": {"sin": ["seen", "sad"]}, "right": {"sin": ["seen", "seen.init"]}},
            {
                "control": ("seen",),
                "public.kern1.sin": ["seen", "sad"],
                "public.kern2.sin": ["seen", "seen.init"],
            },
        ),
    ],
)
def test_setAllKerningGroups(defcon_font_1, kernGroups, expected):
    defcon_font_1.kerningGroups.set(kernGroups)
    assert defcon_font_1.groups == expected


def test_clearKerningGroups(defcon_font_1):
    expected = {"control": ("seen",)}
    defcon_font_1.kerningGroups.clear()
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
    assert defcon_font_1[glyphName].kerningGroups.getLeftSide() == expected


@pytest.mark.parametrize(
    "glyphName, expected",
    [
        ("seen", "public.kern1.sin.fina"),
        ("D", "public.kern2.H"),
        ("C", "public.kern2.O"),
    ],
)
def test_leftSideKerningGroup_groupNamePrefixes(defcon_font_1, glyphName, expected):
    assert (
        defcon_font_1[glyphName].kerningGroups.getLeftSide(groupNamePrefixes=True)
        == expected
    )


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
    assert defcon_font_1[glyphName].kerningGroups.getRightSide() == expected


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
def test_rightSideKerningGroup_groupNamePrefixes(defcon_font_1, glyphName, expected):
    assert (
        defcon_font_1[glyphName].kerningGroups.getRightSide(groupNamePrefixes=True)
        == expected
    )


@pytest.mark.parametrize(
    "glyphName, expected",
    [
        ("seen.init", "test1"),  # rtl
        ("D", "test2"),  # ltr
        ("sad", None),
    ],
)
def test_setLeftSideKerningGroup(defcon_font_1, glyphName, expected):
    g = defcon_font_1[glyphName]
    g.kerningGroups.setLeftSide(expected)
    assert g.kerningGroups.getLeftSide() == expected


@pytest.mark.parametrize(
    "glyphName, expected",
    [
        ("seen", "test2"),  # rtl
        ("Ccedilla", "C2"),  # ltr
        ("E", None),
    ],
)
def test_setRightSideKerningGroup(defcon_font_1, glyphName, expected):
    g = defcon_font_1[glyphName]
    g.kerningGroups.setRightSide(expected)
    assert g.kerningGroups.getRightSide() == expected


@pytest.mark.parametrize(
    "glyphNames, expected",
    [
        (
            ("seen", "tah"),
            {"left": {"sin.fina"}, "right": {"sad.init", "sin.init"}},
        ),  # rtl
        (("C", "D", "O"), {"left": {"O", "H"}, "right": {"O", "C"}}),  # ltr
        (("C", "seen.init"), {"left": {"O"}, "right": {"C", "sin.init"}}),  # ltr
        (("ain.medi"), {"left": set(), "right": set()}),
    ],
)
def test_getKerningGroupNamesForGlyphs(defcon_font_1, glyphNames, expected):
    assert defcon_font_1.getKerningGroupNamesForGlyphs(glyphNames) == expected


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
        (("ain.medi"), {"left": set(), "right": set()}),
    ],
)
def test_getKerningGroupNamesForGlyphs_groupNamePrefixes(
    defcon_font_1, glyphNames, expected
):
    assert (
        defcon_font_1.getKerningGroupNamesForGlyphs(glyphNames, groupNamePrefixes=True)
        == expected
    )


def test_groups_cleanup(kerning_with_missing_glyphs):
    f = kerning_with_missing_glyphs
    f.groups.cleanup()
    assert f.groups == {
        "group1": ["A", "B", "C"],
        "group2": ["D", "E"],
        "group_with_missing_glyph": ["A"],
    }


def test_setKerningGroups_mixed_direction_error(defcon_font_1):
    """Test that setting a group with mixed-direction glyphs raises an error."""
    font = defcon_font_1
    mixed_group = {"left": {"mixed": ["C", "seen"]}}
    with pytest.raises(
        FontGadgetsError,
        match="All the given glyphs should be either 'right to left' or 'left to right!'",
    ):
        font.kerningGroups.set(mixed_group)


def test_convertToPrefixedGroupName_with_warning(defcon_font_1):
    """Test that a warning is issued if the group name already has a prefix."""
    with pytest.warns(
        UserWarning, match="Kerning group name already starts with a prefix"
    ):
        result = defcon_font_1.kerningGroups.convertToPrefixedGroupName(
            "public.kern1.test", "left", False
        )
    assert result == "public.kern2.test"


@pytest.mark.parametrize(
    "glyphNames, groupNamePrefixes, expected",
    [
        (("C", "D"), False, {"O", "H"}),
        (("C", "D"), True, {"public.kern2.O", "public.kern2.H"}),
        (("E", "seen.init"), False, {"H"}),
        (("seen", "sad"), True, {"public.kern1.sin.fina"}),
    ],
)
def test_getLeftSideKerningGroupNamesForGlyphs(
    defcon_font_1, glyphNames, groupNamePrefixes, expected
):
    assert (
        defcon_font_1.getLeftSideKerningGroupNamesForGlyphs(
            glyphNames, groupNamePrefixes=groupNamePrefixes
        )
        == expected
    )


def test_getSide_prefixed_but_none(defcon_font_1):
    """Test getSide with groupNamePrefixes=True when the glyph has no group."""
    glyph = defcon_font_1["E"]  # 'E' has a left group but no right group
    assert glyph.kerningGroups.getSide("right", groupNamePrefixes=True) is None


def test_remove_kerning_groups(defcon_font_1):
    """Test removeLeftSide and removeRightSide methods."""
    glyph = defcon_font_1["C"]  # Has left 'O' and right 'C'
    assert glyph.kerningGroups.left is not None
    assert glyph.kerningGroups.right is not None

    glyph.kerningGroups.removeLeftSide()
    assert glyph.kerningGroups.left is None
    assert glyph.kerningGroups.right is not None  # Right side should be unaffected

    glyph.kerningGroups.removeRightSide()
    assert glyph.kerningGroups.left is None
    assert glyph.kerningGroups.right is None  # Right side should now be gone


@pytest.mark.parametrize(
    "glyphName, groupNamePrefixes, expected",
    [
        ("C", False, {"left": {"O"}, "right": {"C"}}),
        ("C", True, {"left": {"public.kern2.O"}, "right": {"public.kern1.C"}}),
        ("E", False, {"left": {"H"}, "right": set()}),
        ("E", True, {"left": {"public.kern2.H"}, "right": set()}),
        ("ain.medi", False, {"left": set(), "right": set()}),
    ],
)
def test_getKerningGroupsForGlyph(
    defcon_font_1, glyphName, groupNamePrefixes, expected
):
    """Tests the get() method on a glyph's kerningGroups."""
    glyph = defcon_font_1[glyphName]
    assert glyph.kerningGroups.get(groupNamePrefixes=groupNamePrefixes) == expected


def test_delete_left_kerning_group(defcon_font_1):
    """Test `del glyph.kerningGroups.left`."""
    glyph = defcon_font_1["D"]  # Left: H, Right: O
    assert glyph.kerningGroups.left == "H"
    del glyph.kerningGroups.left
    assert glyph.kerningGroups.left is None
    assert glyph.kerningGroups.right == "O"  # Right side unaffected


def test_delete_right_kerning_group_bug(defcon_font_1):
    """Test `del glyph.kerningGroups.right` which has a bug in the original code."""
    glyph = defcon_font_1["D"]  # Left: H, Right: O
    assert glyph.kerningGroups.left == "H"
    assert glyph.kerningGroups.right == "O"
    del glyph.kerningGroups.right
    assert glyph.kerningGroups.right is None
    assert glyph.kerningGroups.left == "H"  # Left side should be unaffected


def test_setKerningGroups_remove_last_member(defcon_font_1):
    """Test that a group is deleted when its last member is removed."""
    font = defcon_font_1
    group_name_prefixed = "public.kern2.H"
    group_name_raw = "H"
    glyph1_name = "D"
    glyph2_name = "E"
    assert group_name_prefixed in font.groups
    assert font[glyph1_name].kerningGroups.left == group_name_raw
    assert font[glyph2_name].kerningGroups.left == group_name_raw
    font[glyph1_name].kerningGroups.setLeftSide(None)
    assert group_name_prefixed in font.groups
    assert font.groups[group_name_prefixed] == [glyph2_name]
    assert font[glyph1_name].kerningGroups.left is None
    font[glyph2_name].kerningGroups.setLeftSide(None)
    assert group_name_prefixed not in font.groups
    assert font[glyph2_name].kerningGroups.left is None


@pytest.mark.parametrize(
    "glyphNames, groupNamePrefixes, expected",
    [
        (("C", "D"), False, {"O", "C"}),
        (("C", "D"), True, {"public.kern1.O", "public.kern1.C"}),
        (("E", "tah"), False, {"sad.init"}),
        (("E", "tah"), True, {"public.kern2.sad.init"}),
        (("seen", "sad"), False, {"sin.init", "sad.init"}),
        (("seen", "sad"), True, {"public.kern2.sin.init", "public.kern2.sad.init"}),
        (("ain.medi",), False, set()),
        (("ain.medi",), True, set()),
    ],
)
def test_getRightSideKerningGroupNamesForGlyphs(
    defcon_font_1, glyphNames, groupNamePrefixes, expected
):
    assert (
        defcon_font_1.getRightSideKerningGroupNamesForGlyphs(
            glyphNames, groupNamePrefixes=groupNamePrefixes
        )
        == expected
    )


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
    members = glyph.kerningGroups.getSideMembers(side)
    assert sorted(members) == sorted(expected)


def test_setSide_with_warning(defcon_font_1):
    """Test setSide with a prefixed group name issues a warning."""
    glyph = defcon_font_1["E"]
    assert glyph.kerningGroups.left == "H"
    with pytest.warns(
        UserWarning, match="Kerning group name already starts with a prefix"
    ):
        glyph.kerningGroups.setSide("public.kern1.newGroup", "left")
    assert glyph.kerningGroups.left == "newGroup"
    assert "public.kern2.newGroup" in glyph.font.groups
    assert "E" in glyph.font.groups["public.kern2.newGroup"]
    assert "E" not in glyph.font.groups["public.kern2.H"]
