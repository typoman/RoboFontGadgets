from .fontset import *

class CharacterSet:
    """
    Family contains CharacterSet(s) which support a specific set of languages or
    writing systems (e.g. Cyrillic, Latin, Arabic, Greek, etc). CharacterSets
    are the parent to FontSets.

    CharacterSets can be subset or merged together to create new character sets.
    """

    _default_fontSet_name = 'default.fontSet'

    def __init__(self, name, family=None):
        self._name = name
        self._family = family
        self._fontSets = {}
        self._default_fontSet = None

    def _set_name(self, name):
        if self._family is not None:
            self._family._characterSets.pop(self._name)
            self._family._characterSets[name] = self
        self._name = name

    def _get_name(self):
        return self._name

    name = property(_get_name, _set_name, doc="The name of this Character Set.")

    def _set_family(self, family):
        self._family = family

    def _get_family(self):
        return self._family

    family = property(_get_family, _set_family, doc="The parent Family.")

    def addFontSet(self, fontSet):
        """
        Add a font set to this character set.
        """
        if fontSet.name in self._fontSets:
            raise FontCollectionsError(f"Duplicate font set name: `{fontSet.name}`")
        self._fontSets[fontSet.name] = fontSet
        fontSet.characterSet = self
        if self._default_fontSet is None:
            self._default_fontSet = fontSet
            logger.debug(f"For the character set `{self.name}` default font set is set to `{fontSet.name}`.")

    def removeFontSet(self, fontSet):
        """
        Remove a font set from this character set.
        """
        if fontSet is self.getFontSetByName(fontSet.name):
            del self._fontSets[fontSet.name]
            fontSet.characterSet = None
            if self._default_fontSet.name == fontSet.name:
                if len(self._fontSets) > 0:
                    self._default_fontSet = self.fonts[0]
                    logger.warning(f"Default font set changed to `{self.defaultFontSet.name}`.")
                else:
                    self._default_fontSet = None
            return
        raise FontCollectionsError(f"FontSet `{fontSet}` doesn't belong to this character set.")

    def _makeDefaultFontSet(self):
        logger.debug(f"Making default font set for the character set `{self.name}`.")
        default_fontSet = FontSet(self._default_fontSet_name, self)
        self._default_fontSet = default_fontSet
        self.addFontSet(default_fontSet)
        return default_fontSet

    def _get_default_fontSet(self):
        if self._default_fontSet is None:
            self._makeDefaultFontSet()
        return self._default_fontSet

    def _set_default_fontSet(self, default_fontSet):
        self._default_fontSet = default_fontSet

    defaultFontSet = property(_get_default_fontSet, _set_default_fontSet, doc="The default font set of this character set.")

    def getFontSetByName(self, fontSet_name):
        """
        Get a font set by its name.
        """
        if fontSet_name not in self._fontSets:
            if fontSet_name == self._default_fontSet_name and self._default_fontSet is None:
                return self._makeDefaultFontSet()
            raise KeyError(f"Character set `{self.name}` doesn't have a font set named `{fontSet_name}`.")
        return self._fontSets[fontSet_name]

    def addFont(self, font):
        """
        Add a font to this character set.
        """
        if font.fontSet is None:
            self.defaultFontSet.addFont(font)
            logger.warning(f"Adding font `{font.path}` to character set `{self.name}`.")
        else:
            fontSet = font.fontSet
            if fontSet.name not in self._fontSets:
                self.addFontSet(fontSet)
                logger.warning(f"Adding font `{font.path}` to character set `{self.name}`.")
            fontSet.addFont(font)

    def removeFont(self, font):
        """
        Remove a font from this character set.
        """
        if font.fontSet is not None:
            if font.fontSet is self.getFontSetByName(font.fontSet.name):
                font.fontSet.removeFont(font)
                return
        raise FontCollectionsError(f"Font `{font.path}` doesn't belong to this character set.")

    @property
    def fontSets(self):
        return list(self._fontSets.values())

    def to_dict(self):
        return {
            'name': self.name,
            'fontSets': {fontset.name: fontset.to_dict() for fontset in self.fontSets},
            'defaultFontSet': self.defaultFontSet.name if self.fontSets else None
        }

    @classmethod
    def from_dict(cls, data):
        fontsets = {fontset_name: FontSet.from_dict(fontset_data) for fontset_name, fontset_data in data['fontSets'].items()}
        characterset = cls(data['name'])
        try:
            characterset.addFontSet(fontsets.pop(data['defaultFontSet']))
        except KeyError:
            existing_fontsets = "\n".join(fontsets.values())
            logger.error(f"Character set `{data['name']}` default font set not found: `{data['defaultFontSet']}`. Existing font sets:\n{existing_fontsets}")
            return

        for fontset in fontsets.values():
            characterset.addFontSet(fontset)
        return characterset

    def __repr__(self):
        fontsets_representation = "\n".join(f"\t{fontset}" for fontset in self.fontSets)
        return f"CharacterSet({self.name}):\n{fontsets_representation}"
