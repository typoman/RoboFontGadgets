from fontgadgets.decorators import *
import fontgadgets.extensions.component
import fontgadgets.extensions.font
from copy import deepcopy

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

@font_method
def copyFromGlyph(glyph, sourceGlyph, width=True, height=True, unicodes=True,
             note=True, image=True, contours=True, components=True, anchors=True,
             guidelines=True, lib=True):
    """
    Copy data from another **sourceGlyph**. This copies all the data by
    defualt unless on of these argument is set to False:

    width, height, unicodes, note, image, contours, components, anchors,
    guidelines, lib
    """
    if width:
        glyph.width = sourceGlyph.width
    if height:
        glyph.height = sourceGlyph.height
    if unicodes:
        glyph.unicodes = list(sourceGlyph.unicodes)
    if note:
        glyph.note = sourceGlyph.note
    if image:
        glyph.image = sourceGlyph.image
    if contours:
        for sourceContour in sourceGlyph:
            c = glyph.instantiateContour()
            c.setDataFromSerialization(sourceContour.getDataForSerialization())
            glyph.appendContour(c)
    if components:
        for sourceComponent in sourceGlyph.components:
            c = glyph.instantiateComponent()
            c.setDataFromSerialization(sourceComponent.getDataForSerialization())
            glyph.appendComponent(c)
    if anchors:
        glyph.anchors = [glyph.instantiateAnchor(a) for a in sourceGlyph.anchors]
    if guidelines:
        glyph.guidelines = [glyph.instantiateGuideline(g) for g in sourceGlyph.guidelines]
    if lib:
        glyph.lib = deepcopy(sourceGlyph.lib)
