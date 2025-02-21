from utils import *
import fontgadgets.extensions.kerning

def test_cleanup(kerning_with_missing_glyphs):
    f = kerning_with_missing_glyphs
    f.kerning.cleanup()
    assert f.kerning == {
        ('A', 'B'): 50,
        ('C', 'D'): 30,
        ('B', 'B'): 40,
        ('group_with_missing_glyph', 'A'): 15,
    }

@pytest.mark.parametrize(
    "pair, expected",
    [
        (
            ('group1', 'group2'),
            [('A', 'D'), ('A', 'E'), ('B', 'D'), ('B', 'E'), ('C', 'D'), ('C', 'E')]
        ),
        (
            ('group_with_missing_glyph', 'group1'),
            [('A', 'A'), ('A', 'B'), ('A', 'C'), ('missing_glyph', 'A'), ('missing_glyph', 'B'), ('missing_glyph', 'C')]
        ),
        (
            ('empty_group', 'group1'),
            []
        ),
        (
            ('A', 'group1'),
            [('A', 'A'), ('A', 'B'), ('A', 'C')]
        ),
    ],
)
def test_flattenPair(kerning_with_missing_glyphs, pair, expected):
    f = kerning_with_missing_glyphs
    assert f.kerning.flattenPair(pair) == expected

@pytest.mark.parametrize(
    "pair, expected",
    [
        (
            ('A', 'B'),
            True
        ),
        (
            ('missing_glyph', 'B'),
            False
        ),
        (
            ('group_that_going_to_be_deleted', 'B'),
            True
        ),
    ],
)
def test_isKerningPairValid(kerning_with_missing_glyphs, pair, expected):
    f = kerning_with_missing_glyphs
    assert f.kerning.isKerningPairValid(pair) is expected

def test_validKerningEntries(kerning_with_missing_glyphs):
    f = kerning_with_missing_glyphs
    expected = {
                'A',
                'B',
                'C',
                'D',
                'E',
                'empty_group',
                'group1',
                'group2',
                'group_that_going_to_be_deleted',
                'group_with_missing_glyph',
                }
    assert f.validKerningEntries == expected


@pytest.mark.parametrize("glyph_names_to_remove, expected_kerning", [
    # Test 1: sample pair to remove: (missing_glyph, existing glyph)
    (
        ['A'],
        {
            ('C', 'D'): 30,
            ('E', 'missing_glyph'): 20,
            ('B', 'B'): 40,
            ('E', 'empty_group'): 10,
            ('group_that_going_to_be_deleted', 'empty_group'): 20,
            ('missing_glyph', 'group_with_missing_glyph'): 20,
            ('E', 'not_group_not_glyph'): 10,
        }
    ),
    # Test 2: sample pair to remove: (existing glyph, exisitng glyph)
    (
        ['B'],
        {
            ('C', 'D'): 30,
            ('E', 'missing_glyph'): 20,
            ('missing_glyph', 'A'): 10,
            ('E', 'empty_group'): 10,
            ('E', 'not_group_not_glyph'): 10,
            ('group_that_going_to_be_deleted', 'A'): 10,
            ('group_with_missing_glyph', 'A'): 15,
            ('group_that_going_to_be_deleted', 'empty_group'): 20,
            ('missing_glyph', 'group_with_missing_glyph'): 20,
        }
    ),
    # Test 3: sample pair to remove: (existing glyph, missing group)
    (
        ['E'],
        {
            ('A', 'B'): 50,
            ('C', 'D'): 30,
            ('missing_glyph', 'A'): 10,
            ('B', 'B'): 40,
            ('group_that_going_to_be_deleted', 'A'): 10,
            ('group_with_missing_glyph', 'A'): 15,
            ('group_that_going_to_be_deleted', 'empty_group'): 20,
            ('missing_glyph', 'group_with_missing_glyph'): 20,
        }
    ),
    # Test 4: sample pair to remove: (missing glyph, missing group)
    (
        ['missing_glyph_2', 'missing_glyph'],
        {
            ('A', 'B'): 50,
            ('C', 'D'): 30,
            ('B', 'B'): 40,
            ('E', 'empty_group'): 10,
            ('E', 'not_group_not_glyph'): 10,
            ('group_that_going_to_be_deleted', 'A'): 10,
            ('group_with_missing_glyph', 'A'): 15,
            ('group_that_going_to_be_deleted', 'empty_group'): 20,
        }
    ),
])
def test_remove_glyphs(kerning_with_missing_glyphs, glyph_names_to_remove, expected_kerning):
    f = kerning_with_missing_glyphs
    f.kerning.removeGlyphs(glyph_names_to_remove, pruneGroups=False, cleanup=False)
    assert f.kerning.items() == expected_kerning.items()
