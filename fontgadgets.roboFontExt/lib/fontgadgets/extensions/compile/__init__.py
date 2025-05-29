from fontgadgets.decorators import *
from fontTools.pens.t2CharStringPen import T2CharStringPen
from defcon import Glyph
from fontTools.fontBuilder import FontBuilder
from warnings import warn
import fontgadgets.extensions.glyph.boolean
import fontgadgets.extensions.features.compile
import io
"""
This module contains functions for compiling fonts which are taiken for caching and making
the font to be compiled faster.
"""

@font_cached_property(
    "Glyph.ContoursChanged", "Glyph.ComponentsChanged", "Component.BaseGlyphChanged"
)
def t2CharString(glyph):
    pen = T2CharStringPen(0, glyph.font)
    glyph.removeOverlapCopy().draw(pen)
    return pen.getCharString()


REQUIRED_GLYPHS = [".notdef", "space"]
_EMPTY_CHAR_STRING = T2CharStringPen(100, None).getCharString()

class Compiler:

    """
    An OTF Compiler for fast previewing ufo file.
    """

    def __init__(self, font):
        self.font = font
        self._glyphSet = {g.name: g for g in font}
        for glyph_name in REQUIRED_GLYPHS:
            if glyph_name not in self._glyphSet:
                g = Glyph()
                g.width = 0
                self._glyphSet[glyph_name] = g
        self._otf = None

    def setupOTF(self):
        font = self.font
        self.upm = font.info.unitsPerEm
        self._charstrings = {name: _EMPTY_CHAR_STRING for name in REQUIRED_GLYPHS}
        self._charstrings.update({name: _EMPTY_CHAR_STRING for name in font.keys()})
        self._metrics = {name: (self.upm, 0) for name in self._charstrings}
        fb = self.builder = FontBuilder(self.font.info.unitsPerEm, isTTF=False)
        fb.setupGlyphOrder(sorted(set(self._charstrings.keys())))
        fb.setupCharacterMap(
            {uni: names[0] for uni, names in self.font.unicodeData.items()}
        )
        familyName = str(self.font.info.familyName)
        styleName = str(self.font.info.styleName)
        version = "0.1"
        self.fontName = familyName + "-" + styleName
        self.fontName = self.fontName.replace(" ", "")
        nameStrings = dict(
            familyName=dict(en=familyName),
            styleName=dict(en=styleName),
            uniqueFontIdentifier=familyName + "." + styleName,
            fullName=self.fontName,
            psName=self.fontName,
            version="Version " + version,
        )
        fb.setupHorizontalHeader(
            ascent=round(self.font.info.ascender), descent=round(self.font.info.descender)
        )
        fb.setupNameTable(nameStrings)
        fb.setupPost()

    def _getCharstrings(self):
        return {name: glyph.t2CharString for name, glyph in self._glyphSet.items()}

    def _getMetrics(self):
        return {name: (glyph.width, 0) for name, glyph in self._glyphSet.items()}

    def getOTF(self):
        fb = self.builder
        metricsMap = self._metrics
        fb.setupHorizontalMetrics(metricsMap)
        charstrings = self._charstrings
        fb.setupCFF(self.fontName, {"FullName": self.fontName}, charstrings, {})
        self._otf = fb.font
        return self._otf

    def getOTFData(self):
        """
        Binary data of the font. This can be used for text layout without having to
        saving it to disk.
        """
        data = io.BytesIO()
        self._otf.save(data)
        return data.getvalue()

    def saveOTF(self, path):
        self._otf.save(path)

    @property
    def OTF(self):
        return self._otf

@font_cached_property(
    "UnicodeData.Changed", "Layer.GlyphAdded", "Layer.GlyphDeleted", "Info.Changed"
)
def compiler(font):
    return Compiler(font)

@font_cached_property(
    "UnicodeData.Changed", "Layer.GlyphAdded", "Layer.GlyphDeleted", "Info.Changed"
)
def _emptyOTF(font):
    compiler = font.compiler
    compiler.setupOTF()
    return font.compiler.getOTF()

@font_cached_property(
    "UnicodeData.Changed", "Layer.GlyphAdded", "Layer.GlyphDeleted", "Info.Changed", "Glyph.WidthChanged",
)
def _otfWithMetrics(font):
    # otf cache for metrics without outlines
    otf = font._emptyOTF
    fb = font.compiler.builder
    compiler = font.compiler
    metricsMap = compiler._getMetrics()
    fb.setupHorizontalMetrics(metricsMap)
    compiler._otf = fb.font
    return compiler._otf

@font_cached_property(
    "UnicodeData.Changed", "Layer.GlyphAdded", "Layer.GlyphDeleted", "Info.Changed", "Glyph.ContoursChanged", "Glyph.ComponentsChanged",
)
def _otfWithOutlines(font):
    """
    OTF cache for outlines and metrics without features.
    """
    otf = font._otfWithMetrics
    fb = font.compiler.builder
    compiler = font.compiler
    charstrings = compiler._getCharstrings()
    fb.setupCFF(compiler.fontName, {"FullName": compiler.fontName}, charstrings, {})
    compiler._otf = fb.font
    return compiler._otf

@font_cached_property(
    "UnicodeData.Changed", "Layer.GlyphAdded", "Layer.GlyphDeleted", "Info.Changed", "Features.TextChanged", "Glyph.WidthChanged", "Glyph.ContoursChanged", "Glyph.ComponentsChanged", "Anchor.Changed", "Groups.Changed", "Kerning.Changed",
)
def otf(font):
    """
    OTF file with outlines and features for proofing and previewing.
    """
    otf = font._otfWithOutlines
    compiler = font.compiler
    compiler._otf = compiler.font.features.getCompiler(ttFont=compiler._otf, glyphSet=compiler._glyphSet).ttFont
    return compiler._otf

@font_cached_property(
    "UnicodeData.Changed", "Layer.GlyphAdded", "Layer.GlyphDeleted", "Info.Changed", "Features.TextChanged", "Glyph.WidthChanged", "Anchor.Changed", "Groups.Changed", "Kerning.Changed",
)
def _emptyOTFWithFeatures(font):
    """
    OTF file without outlines for shaping text in harfbuzz.
    """
    otf = font._otfWithMetrics
    fb = font.compiler.builder
    compiler = font.compiler
    compiler._otf = compiler.font.features.getCompiler(ttFont=compiler._otf, glyphSet=compiler._glyphSet).ttFont
    return compiler._otf

class GlyphProductionNames:
    """
    An object to produce production names which will be cached until changes has
    been made to the font.
    """

    def __init__(self, font):
        self.glyphName2ProductionNameMap = {}
        postscriptNames = font.lib.get("public.postscriptNames", {})
        allProdutionNames = set()
        for g in sorted(font, key=lambda g: g.unicodes, reverse=True):
            exist = postscriptNames.get(g.name, None)
            if exist:
                self.glyphName2ProductionNameMap[g.name] = exist
            else:
                baseName = self.getProductionNameForGlyph(g)
                i = 0
                produtionName = baseName
                while produtionName in allProdutionNames:
                    i += 1
                    produtionName = f"{baseName}.{i}"
                self.glyphName2ProductionNameMap[g.name] = produtionName
                allProdutionNames.add(produtionName)

    def getProductionNameForGlyph(self, glyph):
        unicodes = glyph.unicodes
        font = glyph.font
        if len(unicodes) == 1:
            uv = unicodes[0]
            return "{}{:04X}".format("u" if uv > 0xFFFF else "uni", uv)
        else:
            seperated = glyph.name.split(".")
            if len(seperated) > 1:
                base = ".".join(seperated[:-1])
                if base in self.glyphName2ProductionNameMap:
                    return self.glyphName2ProductionNameMap[base] + "." + seperated[-1]
            unicodes = []
            for gl, sub in glyph.features.sourceGlyphs.items():
                for gn in gl:
                    unicodes.extend(font[gn].unicodes)
            if unicodes:
                if all(v and v <= 0xFFFF for v in unicodes):
                    return "uni" + "".join("%04X" % v for v in unicodes)

        warningMessage = f"Can't produce a production name for glyph '{glyph.name}'."
        warn(warningMessage)
        return glyph.name

@font_cached_property(
    "UnicodeData.Changed",
    "Layer.GlyphAdded",
    "Layer.GlyphDeleted",
    "Features.TextChanged",
)
def glyphsProductionNames(font):
    """
    Returns {glyph.name: glyph.productionName} dictionary.
    """
    return GlyphProductionNames(font).glyphName2ProductionNameMap


@font_method
def saveGlyphsProdutionNames(font):
    font.lib["public.postscriptNames"] = font.glyphsProductionNames


@font_property
def productionName(glyph):
    """
    Returns the final production (unixxxx) name for the glyph which is going to be
    saved in the final shipped binary.
    """
    return glyph.font.glyphsProductionNames[glyph.name]
