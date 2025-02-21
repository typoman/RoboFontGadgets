from fontgadgets.decorators import *
from fontTools.misc.roundTools import otRound

@font_method
def scale(glyph: defcon.Glyph, factor, round_values=True):
    """
    Scale the contours, anchors, guidelines, components and width
    of the glyph by factor.

    Args:
    factor (float): The scaling factor.
    """
    def scale_and_round(value):
        v = value * factor
        return otRound(v) if round_values else v

    if len(glyph) > 0:
        for contour in glyph:
            for point in contour:
                point.x = scale_and_round(point.x)
                point.y = scale_and_round(point.y)
    for anchor in glyph.anchors:
        anchor.x = scale_and_round(anchor.x)
        anchor.y = scale_and_round(anchor.y)
    for guideline in glyph.guidelines:
        if guideline.x is not None:
            guideline.x = scale_and_round(guideline.x)
        if guideline.y is not None:
            guideline.y = scale_and_round(guideline.y)
    for c in glyph.components:
        xScale, xyScale, yxScale, yScale, xOffset, yOffset = c.transformation
        xOffset = scale_and_round(xOffset)
        yOffset = scale_and_round(yOffset)
        c.transformation = xScale, xyScale, yxScale, yScale, xOffset, yOffset
    glyph.width = scale_and_round(glyph.width)
