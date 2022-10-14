import itertools
from fontGadgets.tools import fontCachedMethod

@fontCachedMethod("Groups.Changed", "Layer.GlyphAdded", "Layer.GlyphDeleted")
def flattenPair(kerning, pair):
	"""
	Flatten a kerning pair from group kerning to glyph kerning. Returns a list.
	"""
	groups = kerning.font.groups
	left, right = pair
	leftGlyphs = groups.get(left, [left])
	rightGlyphs = groups.get(right, [right])
	return list(itertools.product(leftGlyphs, rightGlyphs))

@fontCachedMethod("Groups.Changed", "Layer.GlyphAdded", "Layer.GlyphDeleted")
def isKerningPairValid(kerning, pair):
	"""
	Returns `False` if kerning pair contains a missing glyph/group
	"""
	for entry in pair:
		if entry not in kerning.font.validKerningEntries:
			return False
	return True

@fontCachedMethod("Groups.Changed", "Layer.GlyphAdded", "Layer.GlyphDeleted")
def validKerningEntries(font):
	return set(font.keys()) | set(font.groups.keys())
