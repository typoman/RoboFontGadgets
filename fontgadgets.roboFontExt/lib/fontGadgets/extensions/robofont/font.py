from fontgadgets.decorators import *

@font_method
def serializedDataForCompile(font):
	keep = [
	'features',
	'groups',
	'kerning',
	'layers',
	]

	defLayers = [
	'public.default',
	'foreground'
	]

	def _getDefLayer(layers):
		for l in layers:
			if l[0] in defLayers:
				return l

	data = font.getDataForSerialization()
	result = {}
	for k, v in data.items():
		if k in keep:
			if k == 'layers':
				defLayer = _getDefLayer(v['layers'])
				assert defLayer is not None
				v['layers'] = [defLayer]
			result[k] = v
	return result

def getSortedFonts(fonts=None):
	"""
	Returns all the fonts based on their `glyph.width`. In most cases this will
	result in fonts being sorted by weight. If the argument is not provided then
	the all the open fonts will be returned.
	"""
	if fonts is None:
		fonts = AllFonts()
	numFonts = len(fonts)
	for gname in fonts[0].glyphOrder:
		try:
			widths = {f[gname].width: f for f in fonts}
		except KeyError:
			continue
		if len(widths) == numFonts:
			return [widths[w] for w in sorted(widths)]
