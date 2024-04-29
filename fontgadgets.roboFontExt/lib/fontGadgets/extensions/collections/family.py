from .characterset import *
from .error import FontCollectionsError
import json

class Family:
    """
    This class holds the information about a set of fonts which are related.
    Families are made from one or multiple character sets.

    FontSets can perform operations such as: compiling, merging, hinting,
    subsetting.
    """
    _default_characterSet_name = 'default.characterSet'

    def __init__(self, name, path=None):
        self._name = name
        self._characterSets = {}
        self._defaultCharacterSet = None
        self._path = path

    def _set_name(self, name):
        self._name = name

    def _get_name(self):
        return self._name

    name = property(_get_name, _set_name, doc="The name of this Family.")

    def _get_default_characterSet(self):
        if self._defaultCharacterSet is None:
            self._makeDefaultCharacterSet()
        return self._defaultCharacterSet

    def _set_default_characterSet(self, default_characterSet):
        self._defaultCharacterSet = default_characterSet

    defaultCharacterSet = property(_get_default_characterSet, _set_default_characterSet, doc="The default character set of this family.")

    @property
    def characterSets(self):
        return list(self._characterSets.values())

    def _makeDefaultCharacterSet(self):
        default_characterSet = CharacterSet(self._default_characterSet_name, self)
        self._defaultCharacterSet = default_characterSet
        self.addCharacterSet(default_characterSet)
        return default_characterSet

    def addCharacterSet(self, characterSet):
        """
        Adds the given characterSet object to the family.
        """
        if characterSet.name in self._characterSets:
            raise FontCollectionsError(f"Duplicate character set name: {characterSet.name}")
        self._characterSets[characterSet.name] = characterSet
        characterSet.family = self
        if self._defaultCharacterSet is None:
            self.defaultCharacterSet = characterSet
            logger.debug(f"For the family `{self.name}` default character set is set to `{characterSet.name}`.")

    def removeCharacterSet(self, characterSet):
        """
        Removes the givne characterSet object from the family.
        """
        if characterSet.name in self._characterSets and characterSet is self.getCharacterSetByName(characterSet.name):
            del self._characterSets[characterSet.name]
            characterSet.family = None
            if self._defaultCharacterSet.name == characterSet.name:
                if len(self._characterSets) > 0:
                    self._defaultCharacterSet = self.characterSets[0]
                    logger.warning(f"Default character set changed to `{self.defaultCharacterSet.name}`.")
                else:
                    self._defaultCharacterSet = None
            return
        raise FontCollectionsError(f"characterSet `{characterSet.name}` doesn't belong to this family.")

    def getCharacterSetByName(self, characterSetName):
        """
        Returns the characterSet using the given name.
        """
        if characterSetName not in self._characterSets:
            if self._defaultCharacterSet is None and characterSetName == self._default_characterSet_name:
                return self._makeDefaultCharacterSet()
            raise KeyError(f"Family `{self.name}` doesn't have a character set named `{characterSetName}`.")
        return self._characterSets[characterSetName]

    def addFontSet(self, fontSet, characterSetName=None):
        """
        Adds the fontSet to the family. If characterSetName is given, the
        fontSet will be added to the given characterSet in this family. If no
        characterSetName is given, the fontSet will be added to the default
        characterSet.
        """
        if characterSetName is None:
            characterSet = self.defaultCharacterSet
            logger.warning(f"Adding fontSet `{fontSet.name}` to the default character set `{characterSet.name}`.")
        elif characterSetName not in self._characterSets:
            raise FontCollectionsError(f"Family `{self}` doesn't have a character set named `{characterSetName}`.")
        else:
            characterSet = self.getCharacterSetByName(characterSetName)
        if fontSet.characterSet is not None:
            logger.warning(f"FontSet `{fontSet.name}` already belongs to a character set, it will be overridden to `{characterSet}`.")
        characterSet.addFontSet(fontSet)

    def removeFontSet(self, fontSet):
        if fontSet.characterSet is not None:
            if fontSet.characterSet is self.getCharacterSetByName(fontSet.characterSet.name):
                fontSet.characterSet.removeFontSet(fontSet)
                return
        raise FontCollectionsError(f"Fontset `{fontSet.name}` doesn't belong to this family.")

    def addFont(self, font, fontSetName=None, characterSetName=None):
        """
        Adds the font to the family. If the font is doesn't belong to a
        characterSet, it will be added to the default characterSet of the
        family.
        """
        if font.fontSet is None:
            self.defaultCharacterSet.addFont(font)
            logger.warning(f"Adding font `{font.path}` to the default fontSet `{self.defaultCharacterSet.name}`.")
        else:
            characterSet_name = font.fontSet.characterSet.name
            if characterSet_name is None:
                self.defaultCharacterSet.addFont(font)
                logger.warning(f"Adding font `{font.path}` to the default character set `{self.defaultCharacterSet.name}`.")
            elif characterSet_name not in self._characterSets:
                raise FontCollectionsError(f"Font `{font.path}` doesn't belong to this family.")
            else:
                font.fontSet.addFont(font)

    def removeFont(self, font):
        """
        Removes the font from the family.
        """
        if font.fontSet is not None:
            characterSet = font.fontSet.characterSet
            if characterSet is self.getCharacterSetByName(characterSet.name):
                font.fontSet.removeFont(font)
                return
        raise FontCollectionsError(f"Font `{font.path}` doesn't belong to this family.")

    def to_dict(self):
        return {
            'name': self.name,
            'characterSets': {characterset.name: characterset.to_dict() for characterset in self.characterSets},
            'defaultCharacterSet': self.defaultCharacterSet.to_dict() if self.characterSets else None
        }

    @classmethod
    def from_dict(cls, data):
        character_sets = {characterset_name: CharacterSet.from_dict(characterset_data) for characterset_name, characterset_data in data['characterSets'].items()}
        family = cls(data['name'])
        try:
            family.addCharacterSet(character_sets.pop(data['defaultCharacterSet']))
        except KeyError:
            existing_character_sets = "\n".join(character_sets.values())
            logger.error(f"Family `{data['name']}` default character set not found: `{data['defaultCharacterSet']}`. Existing character sets:\n{existing_character_sets}")
            return
        for characterset in character_sets.values():
            family.addCharacterSet(characterset)
        return family

    def save(self, file_path):
        with open(file_path, 'w') as file:
            json.dump(self.to_dict(), file)

    @classmethod
    def load(cls, file_path):
        with open(file_path, 'r') as file:
            data = json.load(file)
        return cls.from_dict(data)

    def __repr__(self):
        charset_representation = "\n".join(f"\t{charset}" for characterset in self.fontSets)
        return f"Family({self.name}):\n{fontsets_representation}"
