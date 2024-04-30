from fontgadgets.decorators import *

def _scaleRound(v, factor):
    return int(round(v * factor))


_scaleAttribues = [
    "descender",
    "xHeight",
    "capHeight",
    "ascender",
    # "unitsPerEm",
]

def _scaleGlyph(glyph: fontParts.fontshell.RGlyph, factor):
    # scale the glyph for font.scale function
    if len(glyph.contours) > 0:
        for contour in glyph.contours:
            contour.scaleBy(factor)
    for anchor in glyph.anchors:
        anchor.scaleBy(factor)
    for guideline in glyph.guidelines:
        guideline.scaleBy(factor)
    for c in glyph.components:
        xScale, xyScale, yxScale, yScale, xOffset, yOffset = c.transformation
        xOffset *= factor
        yOffset *= factor
        c.transformation = xScale, xyScale, yxScale, yScale, xOffset, yOffset
    glyph.width *= factor

@font_method
def scale(font: fontParts.fontshell.RFont, factor=1, layerNames=None, roundValues=True):
    """
    Smalller values than 1 makes the font smaller.
    layerNames: list of name of layers you want to scale, if not provided then
    the default layer will be scaled.
    """
    layersToScale = []
    if layerNames is not None:
        layersToScale = [font.getLayer(l) for l in layerNames]
    if layersToScale == []:
        layersToScale = [
            font,
        ]
    scaleFunct = _scaleGlyph

    for layer in layersToScale:
        for g in layer:
            scaleFunct(g, factor)
    kerning = font.kerning
    if kerning:
        kerning.scaleBy(factor)

    for a in _scaleAttribues:
        v = getattr(font.info, a)
        setattr(font.info, a, _scaleRound(v, factor))
    if roundValues:
        font.round()
    font.changed()
