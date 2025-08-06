from fontgadgets.decorators import *
from warnings import warn
import fontgadgets.extensions.component
import fontgadgets.extensions.glyph.composite
import fontgadgets.extensions.groups.kgroups
import fontgadgets.extensions.font
import fontgadgets.extensions.layer
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
def copyContentsFromGlyph(
    glyph: defcon.Glyph,
    source_glyph,
    width=True,
    height=True,
    unicodes=False,
    note=True,
    image=True,
    contours=True,
    components=True,
    anchors=True,
    guidelines=True,
    lib=True,
    left_side_kerning_group=False,
    right_side_kerning_group=False,
):
    """
    Copies contents from another glyph selectively.

    Args:
        source_glyph: The glyph to copy attributes from.
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
        left_side_kerning_group (bool): Whether to copy the left side kerning group. Defaults to False.
        right_side_kerning_group (bool): Whether to copy the left side kerning group. Defaults to False.
    Returns:
        None
    """
    if width:
        glyph.width = source_glyph.width
    if height:
        glyph.height = source_glyph.height
    if unicodes:
        new = set(source_glyph.unicodes)
        if glyph.font is not None:
            cmap = set(glyph.font.unicodeData.keys())
            new -= cmap
        glyph.unicodes = list(new)
    if note:
        glyph.note = source_glyph.note
    if image:
        glyph.image = source_glyph.image
    if contours:
        pointPen = glyph.getPointPen()
        for c in source_glyph:
            c.drawPoints(pointPen)
    if components:
        pointPen = glyph.getPointPen()
        for c in source_glyph.components:
            c.drawPoints(pointPen)
    if anchors:
        glyph.anchors = [glyph.instantiateAnchor(a) for a in source_glyph.anchors]
    if guidelines:
        glyph.guidelines = [glyph.instantiateGuideline(g) for g in source_glyph.guidelines]
    if lib:
        glyph.lib = deepcopy(source_glyph.lib)
    if glyph.font is not None:
        if left_side_kerning_group:
            glyph.kerningGroups.left = source_glyph.kerningGroups.left
        if right_side_kerning_group:
            glyph.kerningGroups.right = source_glyph.kerningGroups.right

@font_method
def copyContentsFromGlyph(
    glyph: fontParts.fontshell.RGlyph,
    source_glyph,
    width=True,
    height=True,
    unicodes=False,
    note=True,
    image=True,
    contours=True,
    components=True,
    anchors=True,
    guidelines=True,
    lib=True,
    left_side_kerning_group=True,
    right_side_kerning_group=True,
):
    """
    Copies contents from another glyph selectively.

    Args:
        source_glyph: The glyph to copy attributes from.
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
        left_side_kerning_group (bool): Whether to copy the left side kerning group. Defaults to True.
        right_side_kerning_group (bool): Whether to copy the right side kerning group. Defaults to True.

    Returns:
        None
    """
    kwargs = dict(list(locals().items())[2:])
    source_glyph = source_glyph.naked()
    glyph.naked().copyContentsFromGlyph(**kwargs)

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
def swapGlyphData(glyph: defcon.Glyph, other_glyph,
    width=True, height=True, unicodes=False, note=True, image=True, contours=True,
    components=True, anchors=True, guidelines=True, lib=True):
    """
    Swaps the contents and all the data of the glyph with the given otherGlyph.

    Args:
        other_glyph: The other glyph object to swap the contents with.
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
    if copy_kwargs['unicodes'] is True and glyph.font == other_glyph.font:
        warn('Swapping unicodes in a same font could create unexpected results!')
    tmp_otherGlyph = glyph.layer.instantiateGlyphObject()
    tmp_otherGlyph.copyContentsFromGlyph(other_glyph)
    other_glyph.clearData(**clear_kwargs)
    other_glyph.copyContentsFromGlyph(glyph, **copy_kwargs)
    glyph.clearData(**clear_kwargs)
    glyph.copyContentsFromGlyph(tmp_otherGlyph, **copy_kwargs)

# redfined differently for fontParts
@font_method
def swapGlyphData(glyph: fontParts.fontshell.RGlyph, other_glyph,
    width=True, height=True, unicodes=False, note=True, image=True, contours=True,
    components=True, anchors=True, guidelines=True, lib=True):
    """
    Swaps the contents and all the data of the glyph with the given otherGlyph.

    Args:
        other_glyph: The other glyph object to swap the contents with.
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
    if kwargs['unicodes'] is True and glyph.font == other_glyph.font:
        warn('Swapping unicodes in a same font could create unexpected results.')
    glyph = glyph.naked()
    other_glyph = other_glyph.naked()
    glyph.swapGlyphData(other_glyph, **kwargs)

@font_method
def copy(glyph: defcon.Glyph, decompose=False):
    if decompose is True:
        result = glyph.decomposeCopy()
    else:
        result = defcon.Glyph()
        result.copyContentsFromGlyph(glyph)
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
def copyToBackground(glyph, source_glyph=None, clear_background=True, decompose=True,
    update_component_references=False, **copy_kwargs):
    """
    Copies a glyph to the background/mask layer of the glyph.

    This function creates a copy of the glyph in the background/mask layer of
    the font, optionally clearing the existing background layer and decomposing
    the source glyph before copying.

    Args:
    source_glyph (Glyph, optional): The glyph to be used as the source for the copy.
        Defaults to the glyph that is running the method as the source if not specified.
    clear_background (bool, optional): Whether to clear the existing background layer.
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
    targetLayer = targetGlyph.layer

    if source_glyph is None:
        source_glyph = glyph
    if decompose:
        source_glyph = source_glyph.decomposeCopy()
        _copy_kwargs['components'] = False
    else:
        shouldUpdateComps = _copy_kwargs.get('components', False)
        if shouldUpdateComps is True and update_component_references is True:
            for comp in source_glyph.components:
                baseGlyphName = comp.baseGlyph
                if baseGlyphName in targetLayer:
                    compGlyph = font[baseGlyphName]
                else:
                    compGlyph = targetLayer.newGlyph(baseGlyphName)
                compGlyph.copyToBackground(clear_background=clear_background, decompose=False,
                        update_component_references=True, **_copy_kwargs)
    targetGlyph.copyContentsFromGlyph(source_glyph, **_copy_kwargs)

@font_cached_property("Glyph.ContoursChanged", "Glyph.ComponentsChanged")
def centerOfBounds(glyph: defcon.Glyph):
    """
    Returns the center of the glyph bounds.
    """
    xMin, yMin, xMax, yMax = glyph.bounds
    w = xMax - xMin
    h = yMax - yMin
    return xMin + w / 2, yMin + h / 2
