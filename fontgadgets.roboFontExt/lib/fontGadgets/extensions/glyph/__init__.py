from fontgadgets.decorators import *
import fontgadgets.extensions.component
import fontgadgets.extensions.font

@font_property
def isComposite(glyph):
    """
    Returns true if glyph contains any components and no contours.
    """
    return len(glyph) == 0 and len(glyph.components) > 0


@font_method
def autoComponentOrder(glyph):
    """
    Orders the components based on their baseGlyph and transformaiton.
    """
    newComps = sorted(glyph.components, key=lambda c: c._autoOrderIndex)
    glyph.clearComponents()
    for c in newComps:
        glyph.appendComponent(c)


@font_property
def orderIndex(glyph):
    """
    Returns the glyph order index from the glyphOrder of the font.
    """
    return glyph.font.cachedGlyphOrder.index(glyph.name)

@font_property
def hasShape(glyph):
    font = glyph.font
    if len(glyph) > 0:
        return True
    if glyph.components:
        for c in glyph.components:
            if c.baseGlyph in font and font[c.baseGlyph].hasShape:
                return True
    return False
