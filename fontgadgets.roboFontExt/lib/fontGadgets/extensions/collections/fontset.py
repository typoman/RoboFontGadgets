from fontgadgets.log import logger
from .error import FontCollectionsError
import defcon
from fontTools.designspaceLib import DesignSpaceDocument

def indentLines(text, indent):
    return "\n".join([f"{indent}{line}" for line in text.split("\n")])

class FontSet:
    """
    Each character set contains a set of fonts or a multiple set of fonts which
    are structurally similar and can be interpolated. Fontsets should have
    compatible groups and glyphs (e.g. Latin, Greek, Cyrillic, etc).
    """

    def __init__(self, name, characterSet=None, fonts=None, designspace=None):
        self._fonts = fonts or {}
        self._name = name # Italic, Roman, Upright, etc
        self._designspace = None
        self._characterSet = None
        self._baseFont = None
        for font in self._fonts.values():
            self.addFont(font)

    def _set_baseFont(self, baseFont):
        self._baseFont = baseFont

    def _get_baseFont(self):
        return self._baseFont

    baseFont = property(_get_baseFont, _set_baseFont, doc="The base font is the reference for the shared data between the fonts inside the fontset.")

    def _set_characterSet(self, characterSet):
        self._characterSet = characterSet

    def _get_characterSet(self):
        return self._characterSet

    characterSet = property(_get_characterSet, _set_characterSet, doc="The character set that this fontset belongs to.")

    def addFont(self, font):
        if font.path in self._fonts:
            raise FontCollectionsError(f"Duplicate font path: `{font.path}`")
        self._fonts[font.path] = font
        font.fontSet = self
        if self._baseFont is None:
            self._baseFont = font
            logger.debug(f"Setting font `{font.path}` as the base font for font set `{self.name}`.")

    def removeFont(self, font):
        if font is self.getFontByPath(font.path):
            del self._fonts[font.path]
            font.fontSet = None
            if self.baseFont is font:
                if len(self._fonts) > 0:
                    self._baseFont = self.fonts[0]
                    logger.warning(f"Setting font `{self._baseFont.path}` as the base font for font set `{self.name}`.")
                else:
                    self._baseFont = None
            return
        raise FontCollectionsError(f"Font `{font}` doesn't belong to this font set.")

    def _set_name(self, name):
        if self._characterSet is not None:
            self._characterSet._fontSets.pop(self._name)
            self._characterSet._fontSets[name] = self
        self._name = name

    def _get_name(self):
        return self._name

    name = property(_get_name, _set_name, doc="The name of this FontSet.")

    def _set_designspace(self, designspace):
        self._designspace = designspace

    def _get_designspace(self):
        return self._designspace

    designspace = property(_get_designspace, _set_designspace, doc="Path to the designspace for this FontSet.")

    def getFontByPath(self, path):
        if path not in self._fonts:
            raise KeyError(f"No font with path `{path}` in fontset `{self.name}`.")
        return self._fonts[path]

    @property
    def fonts(self):
        return list(self._fonts.values())

    def to_dict(self):
        return {
            'name': self.name,
            'fontPaths': [font.path for font in self.fonts],
            'baseFont': self.baseFont.path if self.fonts else None,
            'designspacePath': self.designspace.path
        }

    @classmethod
    def from_dict(cls, data):
        fonts = {font_path: defcon.Font(font_path) for font_path in data['fontPaths']}
        fontset = cls(data['name'])
        designspace = DesignSpaceDocument(data['designspacePath'])
        try:
            fontset.addFont(fonts.pop(data['baseFont']))
        except KeyError:
            existing_fonts = "\n".join(fonts.values())
            logger.error(f"Font set `{data['name']}` base font not found: `{data['baseFont']}`. Existing fonts:\n{existing_fonts}")
            return
        fontset.designspace = designspace
        for font in fonts.values():
            fontset.addFont(font)
        return fontset
