from fontgadgets.decorators import *
from fontTools.pens.t2CharStringPen import T2CharStringPen
from defcon import Glyph
from fontTools.fontBuilder import FontBuilder
from warnings import warn
import fontgadgets.extensions.glyph.boolean
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
EMPTY_GLYPH = Glyph()


class Compiler:

    """
    An OTF Compiler for fast previewing ufo file.
    """

    def __init__(self, font):
        self.font = font

    def setupOTF(self, font):
        self.upm = font.info.unitsPerEm
        self._glyphSet = {name: EMPTY_GLYPH for name in REQUIRED_GLYPHS}
        self._glyphSet.update({name: EMPTY_GLYPH for name in font.keys()})
        self._metrics = {name: (self.upm, 0) for name in self._glyphSet}
        self._otf = None
        fb = self.builder = FontBuilder(self.font.info.unitsPerEm, isTTF=False)
        fb.setupGlyphOrder(sorted(set(self._glyphSet.keys())))
        fb.setupCharacterMap(
            {uni: names[0] for uni, names in self.font.unicodeData.items()}
        )
        familyName = self.font.info.familyName
        styleName = self.font.info.styleName
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
            ascent=self.font.info.ascender, descent=self.font.info.descender
        )
        fb.setupNameTable(nameStrings)
        fb.setupPost()

    @property
    def glyphSet(self):
        """
        By default outlines are empty. Override this method to fill the outlines with
        the shapes from the source:

        compiler.glyphSet.update({name: source_ufo[name] for name in source_ufo.keys()})
        """
        return self._glyphSet

    @property
    def metrics(self):
        return {name: (glyph.width, 0) for name, glyph in self._glyphSet.items()}

    @property
    def charStrings(self):
        return {name: glyph.t2CharString for name, glyph in self._glyphSet.items()}

    @property
    def otf(self):
        fb = self.builder
        fb.setupHorizontalMetrics(self.metrics)
        fb.setupCFF(self.fontName, {"FullName": self.fontName}, self.charStrings, {})
        self._otf = fb.font
        return self._otf

    def data(self):
        """
        Binary data of the font. This can be used for text layout without having to
        saving it to disk.
        """
        raise NotImplementedError

    def save(self):
        raise NotImplementedError


@font_cached_method(
    "UnicodeData.Changed", "Layer.GlyphAdded", "Layer.GlyphDeleted", "Info.Changed"
)
def compiler(font):
    return Compiler(font)


@font_cached_method(
    "UnicodeData.Changed", "Layer.GlyphAdded", "Layer.GlyphDeleted", "Info.Changed"
)
def _dummyOTF(font):
    return font.compiler.otf


@font_cached_method(
    "UnicodeData.Changed",
    "Layer.GlyphAdded",
    "Layer.GlyphDeleted",
    "Info.Changed",
    "Glyph.AnchorsChanged",
    "Glyph.KerningChanged",
    "Features.Changed",
)
def dummyOTF(font):
    """
    OTF file without outlines and metrics for shaping text.
    """
    return font.features.getCompiler(
        ttFont=font._dummyOTF, glyphSet=font.compiler.glyphSet
    ).ttFont


@font_cached_method(
    "UnicodeData.Changed",
    "Layer.GlyphAdded",
    "Layer.GlyphDeleted",
    "Info.Changed",
    "Glyph.ContoursChanged",
    "Glyph.ComponentsChanged",
    "Component.BaseGlyphChanged",
    "Glyph.WidthChanged",
)
def previewOTF(font):
    """
    OTF file with outlines for previewing.
    """
    compiler = font.compiler
    compiler.glyphSet.update({name: font[name] for name in font.keys()})
    return compiler.otf


@font_cached_method(
    "UnicodeData.Changed",
    "Layer.GlyphAdded",
    "Layer.GlyphDeleted",
    "Info.Changed",
    "Glyph.ContoursChanged",
    "Glyph.ComponentsChanged",
    "Component.BaseGlyphChanged",
    "Glyph.WidthChanged",
    "Glyph.AnchorsChanged",
    "Glyph.KerningChanged",
    "Features.Changed",
)
def previewOTFWithFeatures(font):
    """
    OTF file with outlines and features for previewing.
    """
    return font.features.getCompiler(ttFont=font.previewOTF).ttFont


@font_method
def savePreviewOTFWithFeatures(font, path):
    """
    OTF file with outlines and features for previewing.
    """
    otf = font.previewOTFWithFeatures
    otf.save(path)


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
