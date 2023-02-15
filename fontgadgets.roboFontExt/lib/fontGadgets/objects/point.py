from fontGadgets.tools import fontMethod

@fontMethod
def interpolate(point, otherPoint, interpolationFactor):
	"""
	Returns the x, y point coordinates of linear interpolation between
	the current point and the otherPoint.
	"""

	x = point.x + interpolationFactor * (otherPoint.x - point.x)
	y = point.y + interpolationFactor * (otherPoint.y - point.y)
	return (x, y)
