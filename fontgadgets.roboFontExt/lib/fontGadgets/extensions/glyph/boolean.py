import booleanOperations
from fontgadgets.decorators import *

# caching helps to compile preview fonts faster
@font_cached_method(
    "Glyph.ContoursChanged", "Glyph.ComponentsChanged", "Component.BaseGlyphChanged"
)
def removeOverlapCopy(glyph, returnNewGlyph=True, decompose=True) -> defcon.Glyph:
    """
    Removes overlap on the glyph. If 'returnNewGlyph' is True, the glyph will
    remain intact. If decompose is True, the glyph components will be decomposed
    before removing overlap.
    """
    result = glyph.font.layers.defaultLayer.instantiateGlyphObject()
    result.name = glyph.name
    result.width = glyph.width
    if decompose:
        contours = list(glyph.decomposeCopy())
    else:
        contours = list(glyph)
    if len(contours):
        for contour in contours:
            for point in contour:
                if point.segmentType == "qcurve":
                    raise TypeError("Can't removeOverlap for quadratics")
        booleanOperations.union(contours, result.getPointPen())
    if returnNewGlyph:
        return result
    else:
        glyph.clearContours()
        if decompose:
            glyph.clearComponents()
        for c in result:
            glyph.appendContour(c)
    return glyph
