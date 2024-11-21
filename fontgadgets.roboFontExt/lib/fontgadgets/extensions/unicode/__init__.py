from fontgadgets.decorators import *
from fontTools.unicodedata import script_extension
import fontgadgets.extensions.features
import re
PUA_CATEGORY = "Zzzz"


class FontPseudoUnicodes:
    def __init__(self, font):
        self.font = font
        self.glyph2UnicodesMap = {}
        for g in font:
            if len(g.unicodes) != 0 and PUA_CATEGORY not in script_extension(
                chr(g.unicodes[0])
            ):
                self.glyph2UnicodesMap[g.name] = g.unicodes
        for _getUnicodes in (
            self.unicodesFromGSUB,
            self.unicodesFromName,
            self.unicodesFromComposites,
        ):
            numTargetGlyphs = -1
            while numTargetGlyphs != len(self.nonUnicodeGlyphs):
                numTargetGlyphs = len(self.nonUnicodeGlyphs)
                for g in self.nonUnicodeGlyphs:
                    unicodes = _getUnicodes(g)
                    if unicodes:
                        self.glyph2UnicodesMap[g.name] = list(unicodes)

    @property
    def nonUnicodeGlyphs(self):
        return [g for g in self.font if g.name not in self.glyph2UnicodesMap]

    def unicodesFromGSUB(self, glyph):
        unicodes = set()
        for gl, sub in glyph.features.sourceGlyphs.items():
            for gn in gl:
                unicodes.update(self.glyph2UnicodesMap.get(gn, set()))
        return unicodes

    def unicodesFromName(self, glyph):
        seperated = re.split(r"[_.]", glyph.name)
        unicodes = set()
        for part in seperated:
            unicodes.update(self.glyph2UnicodesMap.get(part, set()))
        return unicodes

    def unicodesFromComposites(self, glyph):
        unicodes = set()
        for component in glyph.components:
            unicodes.update(self.glyph2UnicodesMap.get(component.baseGlyph, set()))
        if not unicodes:
            for composite in self.font.componentReferences.get(glyph.name, set()):
                unicodes.update(self.glyph2UnicodesMap.get(composite, set()))
        return unicodes


@font_cached_property("UnicodeData.Changed", "Features.Changed")
def pseudoUnicodesMapping(font):
    return FontPseudoUnicodes(font).glyph2UnicodesMap


@font_property
def pseudoUnicodes(glyph):
    """
    If a glyph doesn't have unicode, it will be intrepreted from the
    other data inside the font.
    """
    return glyph.font.pseudoUnicodesMapping.get(glyph.name, [])

@font_cached_property("UnicodeData.Changed")
def glyphName2UnicodesMap(font):
    result = {}
    for glyph in font:
        name = glyph.name
        unis = glyph.unicodes
        if unis:
            existing = set(result.get(name, set()))
            existing.update(unis)
            result[name] = frozenset(existing)
    return result
