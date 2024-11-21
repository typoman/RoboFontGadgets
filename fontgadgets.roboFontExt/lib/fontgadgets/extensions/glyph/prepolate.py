from fontTools.pens.basePen import BasePen
from fontTools.misc.arrayTools import updateBounds
import numpy as np
import math

def cornerAngle(p0, p1, p2):
    """
    Compute rotation angle (in radians) for the corner defined by points p0, p1,
    p2.

    The result represents the angle between the vectors (p0 to p1) and (p1 to p2).
    The rotation is considered clockwise if the result is positive, and
    counterclockwise if it's negative. To put it another way, if the first vector
    is pointing upwards, the rotation angle will be negative if the second vector
    is rotating to the left of the first vector, and positive if it's rotating to
    the right.

    Args:
    p0 (list of float): The first point in the form of [x, y].
    p1 (list of float): The second point in the form of [x, y].
    p2 (list of float): The third point in the form of [x, y].

    Returns:
    float: The angle (in radians) for the corner defined by points p0, p1, p2.
    """
    # The only real challenge for comparing corners happens when the angle of
    # the corner is close to 180. It's hard to see the similarity between 179
    # and -179 on the number line; altough they look very similar visually.
    # This can be solved to encode the result by removing the positve and
    # negative aspect of the value and keep it as another attribute which
    # denotes the clock or counter clockwise rotation of the angle in form of
    # True or False.

    v0 = np.array(p0) - np.array(p1)
    v1 = np.array(p2) - np.array(p1)
    angle = math.atan2(np.linalg.det([v0, v1]), np.dot(v0, v1))
    return angle

def vectorAngle(p0, p1):
    """
    Returns the angle of the line formed by points p0 and p1 in radians
    """
    dx, dy = np.array(p1) - np.array(p0)
    return np.arctan2(dy, dx)

class CornerAnglePen(BasePen):

    def __init__(self, glyphSet, ignoreSinglePoints=False):
        BasePen.__init__(self, glyphSet)
        self.corners = [] # nested list that resets with start of each contour
        self.segments = []

    def _moveTo(self, p1):
        self.segments = []
        self._preP = p1
        self._startP = p1

    def _lineTo(self, p1):
        # print(p1)
        self.segments.append((self._preP, p1))
        self._preP = p1

    def _curveToOne(self, p1, p2, p3):
        self.segments.append((self._preP, p1, p2, p3))
        self._preP = p3

    def _closePath(self):
        if self._preP != self._startP:
            self._lineTo(self._startP)
        self.calculateCorners()

    def _endPath(self):
        if self.preP != self._startP:
            self._lineTo(self._startP)
        self.calculateCorners()

    def calculateCorners(self):
        corners = [] # tuples of (vectorAngle, cornerAngle)
        # todo, maybe add the size of the first vector (vectorAngle) relatve to
        # the size of the previous vector or the whole glyph. although the ratio
        # to the hole glyph is more useful but how to get the bounds?
        for i, currentSegment in enumerate(self.segments):
            previousSegment = self.segments[i-1]
            nexSegmentIndex = (i+1) % len(self.segments)
            nextSegment = self.segments[nexSegmentIndex]
            middleP = currentSegment[0]
            previousPForCorner = previousSegment[0]
            if len(previousSegment) == 4:
                previousPForCorner = previousSegment[-2]
            nextPForCorner = nextSegment[0]
            if len(currentSegment) == 4:
                nextPForCorner = currentSegment[1]
            cornerA = cornerAngle(previousPForCorner, middleP, nextPForCorner) / math.pi
            nextOnCurveP = currentSegment[-1]
            vectorA = vectorAngle(middleP, nextOnCurveP) / math.pi
            corners.append((vectorA, cornerA))
        self.corners.append(corners)

def cornerAngles(glyph):
    pen = CornerAnglePen(glyph.layer)
    glyph.draw(pen)
    return pen.corners

f = CurrentFont()
corners = {}
# for g in f.naked():
#     corners[g.name] = getCornerAngles(g)

g = CurrentGlyph().naked()
print(getCornerAngles(g))