from fontGadgets.tools import fontCachedMethod, fontMethod
import re
from warnings import warn

RE_GROUP_TAG = re.compile(r'public.kern\d\.')
GROUP_SIDE_TAG = ("public.kern1.", "public.kern2.")

class KerningGroups():
	"""
	An object that gets destroyed every time font.groups change. This is
	used for changing kerning groups of the font.
	"""

	def __init__(self, groups):
		self.groups = groups
		self._glyphToKerningGroupMapping = None
		self._items = None

	def _isKerningGroup(self, entry):
		"""
		Return True if the given entry is a kerning group name starting either with
		`public.kern1.` or `public.kern2.`
		"""
		if re.match(RE_GROUP_TAG, entry) is None:
			return False
		return True

	@property
	def glyphToKerningGroupMapping(self):
		"""
		GlyphName to raw kerning group name mapping.
		"""
		if self._glyphToKerningGroupMapping is None:
			result = [{}, {}]
			for group, members in self.groups.items():
				if self._isKerningGroup(group):
					for glyphName in members:
						side, name = self._getSideAndRawGroupName(group)
						result[side][glyphName] = name
			self._glyphToKerningGroupMapping = tuple(result)
		return self._glyphToKerningGroupMapping

	def items(self):
		"""
		Kerning groups is a tuple with two members. First member is an group dict that
		only appears in the first item of a kerning pair and also same for the second
		member.
		"""
		if self._items is None:
			result = [{}, {}]
			for group, members in self.groups.items():
				if self._isKerningGroup(group):
					side, name = self._getSideAndRawGroupName(group)
					result[side][name] = members
			self._items = tuple(result)
		return self._items

	def set(self, kerningGroups, update=False):
		"""
		Sets the kerning groups to the given one. If update is set to True,
		the old groups will be extended instead of getting removed or reset.
		Returns True if groups have been changed.
		"""
		changed = False
		self.groups.holdNotifications(note="Requested by fontGadgets.objects.groups.KerningGroups.set.")
		if not update:
			self.clear()
		fontGroups = dict(self.groups)
		for side, kernGroups in enumerate(kerningGroups):
			for kernGroupName, newMembers in kernGroups.items():
				for glyphName in newMembers:
					# remove old memberships
					prevKernGroupName = self.glyphToKerningGroupMapping[side].get(glyphName, None)
					if prevKernGroupName is not None:
						prevGroupName = self.convertToKerningGroupName(prevKernGroupName, side)
						prevMembers = list(fontGroups.get(prevGroupName, []))
						if prevMembers:
							prevMembers.remove(glyphName)
							if len(prevMembers) > 0:
								fontGroups[prevGroupName] = prevMembers
							else:
								del fontGroups[prevGroupName]
							changed = True
				if kernGroupName is None:
					continue
				newGroupName = self.convertToKerningGroupName(kernGroupName, side)
				changed = True
				if update:
					# add new members to old groups if it exist
					members = list(fontGroups.get(newGroupName, []))
					members.extend([g for g in newMembers if g not in members])
					fontGroups[newGroupName] = members
				else:
					# reset the group
					fontGroups[newGroupName] = newMembers
		if changed:
			self.groups.clear()
			self.groups.update(fontGroups)
		self.groups.releaseHeldNotifications()
		return changed

	def getGroupNamesForGlyphs(self, glyphNames):
		"""
		Returns two set of names which represent (in respective order) leftGroups and rightGroups
		of the given glyphNames.
		"""
		sides = (1, 0)
		f = self.groups.font 
		if f.isGlyphSetRTL(glyphNames):
			sides = (0, 1)
		mapping = f.kerningGroups.glyphToKerningGroupMapping
		result = []
		for i in range(2):
			groupNames = []
			thisMap = mapping[sides[i]]
			for g in glyphNames:
				if g in thisMap:
					groupNames.append(thisMap[g])
			result.append(set(groupNames))
		return tuple(result)

	def update(self, kerningGroups):
		"""
		Any new glyph for a kerning group will be added to the old kerning
		groups.
		"""
		return self.set(kerningGroups, update=True)

	def clear(self):
		"""
		Clears only kerning groups.
		"""
		for group in list(self.groups):
			if self._isKerningGroup(group):
				del self.groups[group]

	def _getSideAndRawGroupName(self, group_name):
		match = re.match(RE_GROUP_TAG, group_name)
		if match is not None:
			side = match.group(0)
			return GROUP_SIDE_TAG.index(side), re.split(RE_GROUP_TAG, group_name)[-1]

	def convertToKerningGroupName(self, name, side):
		"""
		Adds the kerning group the prefix to the group name.
		"""
		assert side in (0, 1)
		prefix = GROUP_SIDE_TAG[side]
		if self._isKerningGroup(name):
			warn(f"Kerning group name already starts with a prefix, it will be removed:\n{name}")
			name = name[13:]
		return f"{prefix}{name}"

@fontCachedMethod("Groups.Changed")
def kerningGroups(font):
	return KerningGroups(font.groups)

@fontMethod
def _kerningGroupSide(glyph, side):
	# `0` is left side, `1` is right side.
	if not glyph.isRTL:
		side = abs(side - 1)
	return glyph.font.kerningGroups.glyphToKerningGroupMapping[side].get(glyph.name, None)

@fontMethod
def _kerningGroupSideMembers(glyph, side):
	# `0` is left side, `1` is right side.
	if not glyph.isRTL:
		side = abs(side - 1)
	kg = glyph.font.kerningGroups
	groupName = kg.glyphToKerningGroupMapping[side].get(glyph.name, None)
	group = kg.convertToKerningGroupName(groupName)
	return glyph.font.groups.get(group, [])

@fontMethod
def _setKerningGroupSide(glyph, kernGroupName, side):
	result = [{}, {}]
	if not glyph.isRTL:
		side = abs(side - 1)
	result[side] = {kernGroupName: [glyph.name, ]}
	glyph.font.kerningGroups.update(result)

@fontMethod
def getLeftSideKerningGroupMembers(glyph):
	"""
	Get the kerning group members for the left side of the glyph.
	"""
	return glyph._kerningGroupSideMembers(0)

@fontMethod
def getRightSideKerningGroupMembers(glyph):
	"""
	Get the kerning group members for the right side of the glyph.
	"""
	return glyph._kerningGroupSideMembers(1)

@fontMethod
def setLeftSideKerningGroup(glyph, kernGroupName):
	"""
	Set the kerning group name for the left side of the glyph.
	"""
	glyph._setKerningGroupSide(kernGroupName, 0)

@fontMethod
def setRightSideKerningGroup(glyph, kernGroupName):
	"""
	Set the kerning group name for the right side of the glyph.
	"""
	glyph._setKerningGroupSide(kernGroupName, 1)

@fontMethod
def getLeftSideKerningGroup(glyph):
	return glyph._kerningGroupSide(0)

@fontMethod
def getRightSideKerningGroup(glyph):
	return glyph._kerningGroupSide(1)

@fontMethod
def isGrouped(glyph):
	"""
	Returns True if glyph has any kerning group.
	"""
	return glyph._kerningGroupSide(0) is not None or glyph._kerningGroupSide(1) is not None

@fontMethod
def getGroupNamesForGlyphs(font, glyphNames):
	"""
	Returns two set of names which represent (in respective order) leftGroups, rightGroups.
	"""
	return font.kerningGroups.getGroupNamesForGlyphs(glyphNames)
