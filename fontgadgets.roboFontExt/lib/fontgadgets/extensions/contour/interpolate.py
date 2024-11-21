from fontgadgets.decorators import *
from fontPens.digestPointPen import DigestPointStructurePen
from fontTools.pens.basePen import BasePen

class ContourStrucutrePen(DigestPointStructurePen):
    """
    A pen same as DigestPointStructurePen but without identifiers and components.
    """

    def beginPath(self, identifier=None):
        self._data.append(('beginPath'))

    def addComponent(self, baseGlyphName, transformation, identifier=None):
        return

@font_method
def interpolate(contour, otherContour, interpolationFactor, appendToGlyph=True) -> defcon.Contour:
    """
    Interpolates the `contour` with `otherContour` using `interpolationFactor` and adds
    the result to the glyph. If `appendToGlyph` is false, the result is returned.
    """
    glyph = contour.glyph
    assert isinstance(otherContour, glyph.contourClass), 'Provided contour should be an instance of `defcon.Contour` or `glyph.contourClass` object.'
    if contour.isPointStructureCompatible(otherContour):
        result = glyph.contourClass(pointClass=glyph.pointClass)
        for i in range(len(contour)):
            point = contour[i]
            result.addPoint(point.interpolate(otherContour[i], interpolationFactor),
                segmentType=point.segmentType,
                smooth=point.smooth,
                name=point.name)
        if appendToGlyph:
            glyph.appendContour(result)
        else:
            return result

@font_method
def isPointStructureCompatible(contour: defcon.Contour, otherContour):
    thisContourPen = ContourStrucutrePen(ignoreSmoothAndName=True)
    contour.drawPoints(thisContourPen)
    thisContourData = thisContourPen.getDigest()

    otherContourPen = ContourStrucutrePen(ignoreSmoothAndName=True)
    otherContour.drawPoints(otherContourPen)
    otherContourData = otherContourPen.getDigest()

    if thisContourData == otherContourData:
        return
    raise FontGadgetsError("Contours structures not compatible for interpolaiton!")

