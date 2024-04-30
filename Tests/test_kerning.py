from main import *
import fontgadgets.extensions.kerning

def test_cleanup(kerning_with_missing_glyphs):
    f = kerning_with_missing_glyphs
    f.kerning.cleanup()
    assert f.kerning == {
        ('A', 'B'): 50,
        ('C', 'D'): 30,
        ('B', 'B'): 40,
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
