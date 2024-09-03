import pytest
from main import *
from fontgadgets.extensions.anchors import AnchorsDict
from fontTools.misc.transform import Transform

@pytest.fixture
def empty_anchors_dict():
    return AnchorsDict()

@pytest.fixture(scope="module", autouse=True)
def anchors_dict_font_test():
    ufo_path = Path(__file__).parent.joinpath("data/anchors-propogate-test.ufo")
    font = defcon.Font(ufo_path)
    yield font

def test_glyphAnchorsDictInit(anchors_dict_font_test):
    glyph = anchors_dict_font_test['sad-ar']
    test_anchors_dict = glyph.anchorsDict
    assert test_anchors_dict._glyph == glyph
    assert test_anchors_dict == {'bottom': ((259, -201),), 'dotTop': ((876, 467),), 'top': ((887, 467),)}

def test_accumulate(empty_anchors_dict):
    other = {"a": ((1, 2),), "b": ((3, 4),)}
    empty_anchors_dict.accumulate(other)
    assert empty_anchors_dict == {"a": ((1, 2),), "b": ((3, 4),)}

def test_overridePositions(anchors_dict_font_test):
    glyph = anchors_dict_font_test['sad-ar']
    other = {'bottom': ((345, 234),), }
    glyph.anchorsDict.overridePositions(other)
    assert glyph.anchorsDict == {'bottom': ((345, 234),), 'dotTop': ((876, 467),), 'top': ((887, 467),)}

def test_keys(empty_anchors_dict):
    empty_anchors_dict["a"] = ((1, 2),)
    empty_anchors_dict["b"] = ((3, 4),)
    assert empty_anchors_dict.keys() == ("a", "b")

def test_values(empty_anchors_dict):
    empty_anchors_dict["a"] = ((1, 2),)
    empty_anchors_dict["b"] = ((3, 4),)
    assert empty_anchors_dict.values() == (((1, 2),), ((3, 4),))

def test_items(empty_anchors_dict):
    empty_anchors_dict["a"] = ((1, 2),)
    empty_anchors_dict["b"] = ((3, 4),)
    assert empty_anchors_dict.items() == (("a", ((1, 2),)), ("b", ((3, 4),)))

def test_copy(anchors_dict_font_test):
    glyph = anchors_dict_font_test['sad-ar']
    copy = glyph.anchorsDict.copy()
    assert copy == glyph.anchorsDict

def test_removeByName(empty_anchors_dict):
    empty_anchors_dict["a"] = ((1, 2),)
    empty_anchors_dict["ab"] = ((3, 4),)
    empty_anchors_dict.removeByNames(["a"])
    assert empty_anchors_dict == {"ab": ((3, 4),)}

def test_dropPrefixes(empty_anchors_dict):
    empty_anchors_dict["*a"] = ((1, 2),)
    empty_anchors_dict["_b"] = ((3, 4),)
    empty_anchors_dict.dropPrefixes(["*"])
    assert empty_anchors_dict == {"_b": ((3, 4),)}

def test_transform(empty_anchors_dict):
    empty_anchors_dict["a"] = ((1, 2),)
    transform = Transform(2, 0, 0, 2, 0, 0)
    empty_anchors_dict.transform(transform)
    assert empty_anchors_dict == {"a": ((2, 4),)}

def test_addToGlyph():
    test_glyph = defcon.Glyph()
    empty_anchors_dict = AnchorsDict()
    empty_anchors_dict.glyph = test_glyph
    empty_anchors_dict["a"] = ((1, 2),)
    empty_anchors_dict.addToGlyph()
    assert len(test_glyph.anchors) == 1
    assert test_glyph.anchors[0].name == "a"
    assert test_glyph.anchors[0].x == 1
    assert test_glyph.anchors[0].y == 2

def test_GetClosestAnchorToPoint(empty_anchors_dict):
    # Create some sample anchors
    empty_anchors_dict["anchor1"] = (10, 20), (30, 40),
    empty_anchors_dict["anchor2"] = (50, 60),
    empty_anchors_dict["anchor3"] = (90, 100),

    # Test without filtering names
    closestName, closestPose = empty_anchors_dict.getClosestAnchorToPoint((25, 35))
    assert closestName == "anchor1"
    assert closestPose == (30, 40)

    # # Test with filtering names
    closestName, closestPose = empty_anchors_dict.getClosestAnchorToPoint((65, 82), filterToNames=["anchor2", "anchor3"])
    assert closestName == "anchor2"
    assert closestPose == (50, 60)

def test_overridePositionsByClosestAnchorFromAnotherDict(empty_anchors_dict):
    another = AnchorsDict()
    another["top"] = ((10, 20), )

    assert empty_anchors_dict == {}

    empty_anchors_dict["top_1"] = ((0, 0), )
    empty_anchors_dict["top_2"] = ((100, 0), )
    empty_anchors_dict["bottom_1"] = ((0, 100), )
    empty_anchors_dict["bottom_2"] = ((100, 100), )

    empty_anchors_dict.overridePositionsByClosestAnchorFromAnotherDict(another)
    assert empty_anchors_dict["top_1"] == ((10, 20), ) # only this has changed, since it (0, 0) is closer to (10, 20) comapred to (100, 0)
    assert empty_anchors_dict["top_2"] == ((100, 0), )

def test_ligatureAnchors(anchors_dict_font_test):
    # test case when anchors dict contains ligature anchors and glyph
    glyph1 = anchors_dict_font_test['_lam.medi.1']
    glyph2 = anchors_dict_font_test['_NoonComp']
    assert glyph1.anchorsDict.ligatureAnchors().items() == (('bottom_1', ((157, 35),)), ('bottom_2', ((-116, 14),)), ('top_1', ((115, 655),)))
    assert glyph2.anchorsDict.ligatureAnchors().items() == ()
