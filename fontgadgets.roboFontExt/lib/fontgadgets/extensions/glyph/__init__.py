from fontgadgets.decorators import *
from warnings import warn
import fontgadgets.extensions.component
import fontgadgets.extensions.glyph.composite
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
def copyAttributesFromGlyph(glyph: defcon.Glyph,
    sourceGlyph, width=True, height=True, unicodes=False, note=True, image=True,
    contours=True, components=True, anchors=True, guidelines=True, lib=True):
    """
    Copies all attributes from another glyph.

    Args:
        sourceGlyph: The glyph to copy attributes from.
        width (bool): Whether to copy the width. Defaults to True.
        height (bool): Whether to copy the height. Defaults to True.
        unicodes (bool): Whether to copy the unicodes. Defaults to False.
        note (bool): Whether to copy the note. Defaults to True.
        image (bool): Whether to copy the image. Defaults to True.
        contours (bool): Whether to copy the contours. Defaults to True.
        components (bool): Whether to copy the components. Defaults to True.
        anchors (bool): Whether to copy the anchors. Defaults to True.
        guidelines (bool): Whether to copy the guidelines. Defaults to True.
        lib (bool): Whether to copy the lib data. Defaults to True.

    Returns:
        None
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

@font_method
def copyAttributesFromGlyph(glyph: fontParts.fontshell.RGlyph, sourceGlyph,
    width=True, height=True, unicodes=False, note=True, image=True, contours=True,
    components=True, anchors=True, guidelines=True, lib=True):
    """
    Copies all attributes from another glyph.

    Args:
        sourceGlyph: The glyph to copy attributes from.
        width (bool): Whether to copy the width. Defaults to True.
        height (bool): Whether to copy the height. Defaults to True.
        unicodes (bool): Whether to copy the unicodes. Defaults to True.
        note (bool): Whether to copy the note. Defaults to True.
        image (bool): Whether to copy the image. Defaults to True.
        contours (bool): Whether to copy the contours. Defaults to True.
        components (bool): Whether to copy the components. Defaults to True.
        anchors (bool): Whether to copy the anchors. Defaults to True.
        guidelines (bool): Whether to copy the guidelines. Defaults to True.
        lib (bool): Whether to copy the lib data. Defaults to True.

    Returns:
        None
    """
    kwargs = dict(list(locals().items())[2:])
    sourceGlyph = sourceGlyph.naked()
    glyph.naked().copyAttributesFromGlyph(**kwargs)

@font_method
def clearData(glyph: defcon.Glyph,
    unicodes=False, note=True, image=True, contours=True, components=True,
    anchors=True, guidelines=True, lib=True):
    """
    Clears the data of the glyph.

    Args:
        unicodes (bool): If True, clears the unicodes. Defaults to True.
        note (bool): If True, clears the note. Defaults to True.
        image (bool): If True, clears the image. Defaults to True.
        contours (bool): If True, clears the contours. Defaults to True.
        components (bool): If True, clears the components. Defaults to True.
        anchors (bool): If True, clears the anchors. Defaults to True.
        guidelines (bool): If True, clears the guidelines. Defaults to True.
        lib (bool): If True, clears the lib. Defaults to True.

    Returns:
        None
    """
    if unicodes:
        glyph.unicodes = []
    if note:
        glyph.note = None
    if contours:
        glyph.clearContours()
    if components:
        glyph.clearComponents()
    if anchors:
        glyph.clearAnchors()
    if guidelines:
        glyph.clearGuidelines()
    if image:
        glyph.clearImage()
    if lib:
        glyph.lib = {}

# redfined differently for fontParts
@font_method
def clearData(glyph: fontParts.fontshell.RGlyph,
    unicodes=False, note=True, image=True, contours=True, components=True,
    anchors=True, guidelines=True, lib=True):
    """
    Clears the data of the glyph.

    Args:
        unicodes (bool): If True, clears the unicodes. Defaults to False.
        note (bool): If True, clears the note. Defaults to True.
        image (bool): If True, clears the image. Defaults to True.
        contours (bool): If True, clears the contours. Defaults to True.
        components (bool): If True, clears the components. Defaults to True.
        anchors (bool): If True, clears the anchors. Defaults to True.
        guidelines (bool): If True, clears the guidelines. Defaults to True.
        lib (bool): If True, clears the lib. Defaults to True.

    Returns:
        None
    """
    kwargs = dict(list(locals().items())[1:])
    glyph.naked().clearData(**kwargs)

@font_method
def swapGlyphData(glyph: defcon.Glyph, otherGlyph,
    width=True, height=True, unicodes=False, note=True, image=True, contours=True,
    components=True, anchors=True, guidelines=True, lib=True):
    """
    Swaps the contents and all the data of the glyph with the given otherGlyph.

    Args:
        otherGlyph: The other glyph object to swap the contents with.
        width (bool, optional): Whether to swap the width. Defaults to True.
        height (bool, optional): Whether to swap the height. Defaults to True.
        unicodes (bool, optional): Whether to swap the unicodes. Defaults to False.
        note (bool, optional): Whether to swap the note. Defaults to True.
        image (bool, optional): Whether to swap the image. Defaults to True.
        contours (bool, optional): Whether to swap the contours. Defaults to True.
        components (bool, optional): Whether to swap the components. Defaults to True.
        anchors (bool, optional): Whether to swap the anchors. Defaults to True.
        guidelines (bool, optional): Whether to swap the guidelines. Defaults to True.
        lib (bool, optional): Whether to swap the lib. Defaults to True.

    Returns:
        None
    """

    copy_kwargs = dict(list(locals().items())[2:])
    clear_kwargs = dict(list(copy_kwargs.items())[2:])
    if copy_kwargs['unicodes'] is True and glyph.font == otherGlyph.font:
        warn('Swapping unicodes in a same font could create unexpected results!')
    tmp_otherGlyph = glyph.layer.instantiateGlyphObject()
    tmp_otherGlyph.copyAttributesFromGlyph(otherGlyph)
    otherGlyph.clearData(**clear_kwargs)
    otherGlyph.copyAttributesFromGlyph(glyph, **copy_kwargs)
    glyph.clearData(**clear_kwargs)
    glyph.copyAttributesFromGlyph(tmp_otherGlyph, **copy_kwargs)

# redfined differently for fontParts
@font_method
def swapGlyphData(glyph: fontParts.fontshell.RGlyph, otherGlyph,
    width=True, height=True, unicodes=False, note=True, image=True, contours=True,
    components=True, anchors=True, guidelines=True, lib=True):
    """
    Swaps the contents and all the data of the glyph with the given otherGlyph.

    Args:
        otherGlyph: The other glyph object to swap the contents with.
        width (bool, optional): Whether to swap the width. Defaults to True.
        height (bool, optional): Whether to swap the height. Defaults to True.
        unicodes (bool, optional): Whether to swap the unicodes. Defaults to True.
        note (bool, optional): Whether to swap the note. Defaults to True.
        image (bool, optional): Whether to swap the image. Defaults to True.
        contours (bool, optional): Whether to swap the contours. Defaults to True.
        components (bool, optional): Whether to swap the components. Defaults to True.
        anchors (bool, optional): Whether to swap the anchors. Defaults to True.
        guidelines (bool, optional): Whether to swap the guidelines. Defaults to True.
        lib (bool, optional): Whether to swap the lib. Defaults to True.

    Returns:
        None
    """
    kwargs = dict(list(locals().items())[2:])
    if kwargs['unicodes'] is True and glyph.font == otherGlyph.font:
        warn('Swapping unicodes in a same font could create unexpected results.')
    glyph = glyph.naked()
    otherGlyph = otherGlyph.naked()
    glyph.swapGlyphData(otherGlyph, **kwargs)

@font_method
def copy(glyph: defcon.Glyph, decompose=False):
    if decompose is True:
        result = sourceGlyph.decomposeCopy()
    else:
        result = defcon.Glyph()
        result.copyAttributesFromGlyph(glyph)
    result.name = glyph.name
    return result

@font_property
def background(glyph):
    font = glyph.font
    backgroundLayer = font.background
    if glyph.name not in backgroundLayer:
        backgroundGlyph = backgroundLayer.newGlyph(glyph.name)
    else:
        backgroundGlyph = backgroundLayer[glyph.name]
    return backgroundGlyph

@font_method
def copyToBackground(glyph, sourceGlyph=None, clearBackground=True, decompose=True,
    updateComponentReferences=False, **copy_kwargs):
    """
    Copies a glyph to the background/mask layer of the glyph.

    This function creates a copy of the glyph in the background/mask layer of
    the font, optionally clearing the existing background layer and decomposing
    the source glyph before copying.

    Args:
    sourceGlyph (Glyph, optional): The glyph to be used as the source for the copy.
        Defaults to the glyph that is running the method as the source if not specified.
    clearBackground (bool, optional): Whether to clear the existing background layer.
        Defaults to True.
    decompose (bool, optional): Whether to decompose the source glyph before copying.
        Defaults to True.
    width (bool, optional): Whether to copy the glyph's width. Defaults to True.
    height (bool, optional): Whether to copy the glyph's height. Defaults to True.
    image (bool, optional): Whether to copy the glyph's image. Defaults to True.
    contours (bool, optional): Whether to copy the glyph's contours. Defaults to True.
    components (bool, optional): Whether to copy the glyph's components. Defaults to True.
    anchors (bool, optional): Whether to copy the glyph's anchors. Defaults to True.
    guidelines (bool, optional): Whether to copy the glyph's guidelines. Defaults to True.
    lib (bool, optional): Whether to copy the glyph's lib. Defaults to True.

    Returns:
    None
    """
    font = glyph.font
    _copy_kwargs = dict(width=True, height=True, unicodes=False, note=True, image=True, contours=True,
    components=True, anchors=True, guidelines=True, lib=True)
    _copy_kwargs.update(copy_kwargs)
    _copy_kwargs['unicodes'] = False
    targetGlyph = glyph.background

    if sourceGlyph is None:
        sourceGlyph = glyph
    if decompose:
        sourceGlyph = sourceGlyph.decomposeCopy()
        _copy_kwargs['components'] = False
    else:
        shouldUpdateComps = _copy_kwargs.get('components', False)
        if shouldUpdateComps is True and updateComponentReferences is True:
            for comp in sourceGlyph.components:
                baseGlyphName = comp.baseGlyph
                if baseGlyphName in targetLayer:
                    compGlyph = font[baseGlyphName]
                else:
                    compGlyph = targetLayer.newGlyph(baseGlyphName)
                compGlyph.copyToBackground(clearBackground=clearBackground, decompose=False,
                        updateComponentReferences=True, **_copy_kwargs)
    targetGlyph.copyAttributesFromGlyph(sourceGlyph, **_copy_kwargs)

@font_cached_property("Glyph.ContoursChanged", "Glyph.ComponentsChanged")
def centerOfBounds(glyph: defcon.Glyph):
    """
    Returns the center of the glyph bounds.
    """
    xMin, yMin, xMax, yMax = glyph.bounds
    w = xMax - xMin
    h = yMax - yMin
    return xMin + w / 2, yMin + h / 2
