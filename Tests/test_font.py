from main import *
import fontgadgets.extensions.font.scale as _scale


def test_scaleGlyph(glyph_1):
    factor = 2
    _scale._scaleGlyph(glyph_1, factor)

    for contour in glyph_1.contours:
        contour.scaleBy.assert_called_with(factor)

    for anchor in glyph_1.anchors:
        anchor.scaleBy.assert_called_with(factor)
    for guideline in glyph_1.guidelines:
        guideline.scaleBy.assert_called_with(factor)

    for component in glyph_1.components:
        xScale, xyScale, yxScale, yScale, xOffset, yOffset = component.transformation
        assert xOffset == 20
        assert yOffset == 26

    assert glyph_1.width == 100 * factor

