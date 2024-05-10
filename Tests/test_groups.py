import fontgadgets.extensions.groups.kerning_groups as kgroups
from main import *
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
    assert defcon_font_1[glyphName].isGrouped is expected


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
    assert defcon_font_1[glyphName].getLeftSideKerningGroup() == expected


@pytest.mark.parametrize(
    "glyphName, expected",
    [
        ("seen", "public.kern1.sin.fina"),
        ("D", "public.kern2.H"),
        ("C", "public.kern2.O"),
    ],
)
def test_leftSideKerningGroup_groupNamePrefixes(defcon_font_1, glyphName, expected):
    assert defcon_font_1[glyphName].getLeftSideKerningGroup(groupNamePrefixes=True) == expected

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
    assert defcon_font_1[glyphName].getRightSideKerningGroup() == expected

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
    assert defcon_font_1[glyphName].getRightSideKerningGroup(groupNamePrefixes=True) == expected

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
    g.setLeftSideKerningGroup(expected)
    assert g.getLeftSideKerningGroup() == expected


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
    g.setRightSideKerningGroup(expected)
    assert g.getRightSideKerningGroup() == expected


@pytest.mark.parametrize(
    "glyphNames, expected",
    [
        (("seen", "tah"), {"left": {"sin.fina"}, "right": {"sad.init", "sin.init"}}),  # rtl
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
        (("seen", "tah"), {"left": {"public.kern1.sin.fina"}, "right": {"public.kern2.sad.init", "public.kern2.sin.init"}}),  # rtl
        (("C", "D", "O"), {"left": {"public.kern2.O", "public.kern2.H"}, "right": {"public.kern1.O", "public.kern1.C"}}),  # ltr
        (("C", "seen.init"), {"left": {"public.kern2.O"}, "right": {"public.kern1.C", "public.kern2.sin.init"}}),  # ltr
        (("ain.medi"), {"left": set(), "right": set()}),
    ],
)
def test_getKerningGroupNamesForGlyphs_groupNamePrefixes(defcon_font_1, glyphNames, expected):
    assert defcon_font_1.getKerningGroupNamesForGlyphs(glyphNames, groupNamePrefixes=True) == expected

def test_groups_cleanup(kerning_with_missing_glyphs):
    f = kerning_with_missing_glyphs
    f.groups.cleanup()
    assert f.groups == {
        'group1': ['A', 'B', 'C'],
        'group2': ['D', 'E'],
        'group_with_missing_glyph': ['A'],
    }

@pytest.mark.parametrize(
    "glyph_names, expected_groups", [
    (
        ['B', 'C', 'not_a_glyph'],
        {
            'empty_group': (),
            'group1': ('A',),
            'group2': ('D', 'E'),
            'group_with_missing_glyph': ('A', 'missing_glyph'),
            'group_that_going_to_be_deleted': ('missing_glyph_2',),
        }
    ),
    (
        ['A', 'D', 'missing_glyph', 'missing_glyph_2'],
        {
            'empty_group': (),
            'group1': ('B', 'C'),
            'group2': ('E',),
            'group_with_missing_glyph': (),
            'group_that_going_to_be_deleted': (),
        }
    ),
    (
        ['B', 'C', 'D', 'E'],
        {
            'empty_group': (),
            'group1': ('A',),
            'group2': (),
            'group_with_missing_glyph': ('A', 'missing_glyph',),
            'group_that_going_to_be_deleted': ('missing_glyph_2',),
        }
    ),
]
)
def test_removeGlyphsFromGroups(kerning_with_missing_glyphs, glyph_names, expected_groups):
    font = kerning_with_missing_glyphs
    font.groups.removeGlyphs(glyph_names, cleanup=False)
    assert dict(font.groups) == expected_groups
