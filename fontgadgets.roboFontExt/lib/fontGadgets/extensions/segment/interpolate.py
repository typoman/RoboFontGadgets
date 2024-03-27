from fontgadgets.decorators import *

@font_method
def interpolate(
    segment: fontParts.fontshell.RSegment,
    otherSegment,
    interpolationFactor,
    appendToGlyph=True,
) -> defcon.Contour:
    """
    Interpolates the `segment` with `otherSegment` using `interpolationFactor` and adds
    the result to the glyph. If `appendToGlyph` is false, the result is returned
    as a defcon.Contour object.
    """
    contour = segment.asContour()
    return contour.interpolate(
        otherSegment.asContour(), interpolationFactor, appendToGlyph
    )


@font_method
def asContour(segment: fontParts.fontshell.RSegment) -> defcon.Contour:
    """
    Returns a full isolated segment as a contour.
    """
    g = segment.contour.glyph
    result = g.contourClass(pointClass=g.pointClass)
    start = segment.contour.segments[segment.index - 1][-1]
    result.addPoint((start.x, start.y), type="move")
    for point in segment.points:
        result.addPoint(
            (point.x, point.y),
            segmentType=point.segmentType,
            smooth=point.smooth,
            name=point.name,
        )
    return result
