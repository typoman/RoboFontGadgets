from fontgadgets.decorators import font_method

@font_method
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
