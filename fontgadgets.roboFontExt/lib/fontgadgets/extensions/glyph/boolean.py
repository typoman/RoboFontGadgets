import booleanOperations
from fontgadgets.decorators import *


@font_cached_method(
    "Glyph.ContoursChanged", "Glyph.ComponentsChanged", "Component.BaseGlyphChanged"
)
def _flatten(glyph, returnNewGlyph=True, decompose=True) -> defcon.Glyph:
    """
    Removes overlap on the glyph. If 'returnNewGlyph' is True, the glyph will
    remain intact. If decompose is True, the glyph components will be decomposed
    before removing overlap.
    """
    if glyph.font is None:
        raise AttributeError("Can't flatten an indiviual glyph without a parent font.")
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


# choosing flatten to avoid conflict with RF
@font_method
def flatten(glyph) -> defcon.Glyph:
    """
    Removes overlap on the glyph.
    """
    return glyph._flatten(returnNewGlyph=False, decompose=True)

@font_method
def flattenedCopy(glyph) -> defcon.Glyph:
    """
    Removes overlap on a copy of the glyph and returns a new glyph, keeping
    the original glyph intact.
    """
    # we still need to duplicate the result using `copy` otherwise modifying
    # the result of cache would propogate on other places where the copy is 
    # requested.
    return glyph._flatten(returnNewGlyph=True, decompose=True).copy()
