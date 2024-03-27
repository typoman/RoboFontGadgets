from fontgadgets.decorators import *

@font_property
def _autoOrderIndex(contour):
    return contour.baseGlyph, contour.transformation
