from fontgadgets import getEnvironment

def loadExtensions():
	from . import unicode as _unicode
	from . import component as _component
	from . import contour as _contour
	from . import features as _features
	from . import font as _font
	from . import glyph as _glyph
	from . import groups as _groups
	from . import kerning as _kerning
	from . import layout as _layout
	from . import point as _point
	from . import segment as _segment
	from . import compile as _compile

	if getEnvironment() == "robofont":
		from . import robofont as _robofont
