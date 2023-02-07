from fontGadgets.tools import fontCachedMethod, fontMethod
from fontTools.pens.t2CharStringPen import T2CharStringPen
from defcon import Glyph
from fontTools.fontBuilder import FontBuilder

@fontCachedMethod("Glyph.ContoursChanged", "Glyph.ComponentsChanged", "Component.BaseGlyphChanged")
def t2CharString(glyph):
    pen = T2CharStringPen(0, glyph.font)
    glyph.removedOverlapsCopy().draw(pen)
    return pen.getCharString()

REQUIRED_GLYPHS = [".notdef", "space"]
EMPTY_GLYPH = Glyph()

class DummyOTFCompiler():

    """
    An OTF Compiler for previewing ufo file. This complier uses caching to 
    make it faster to compile the fonts while it's being changed.
    """

    def __init__(self, font):
        self.font = font
        self.upm = font.info.unitsPerEm
        self._glyphSet = {name:EMPTY_GLYPH for name in REQUIRED_GLYPHS}
        self._glyphSet.update({name:EMPTY_GLYPH for name in font.keys()})
        self._metrics = {name: (self.upm, 0) for name in self._glyphSet}
        self._otf = None
        fb = self.fb = FontBuilder(self.font.info.unitsPerEm, isTTF=False)
        fb.setupGlyphOrder(sorted(set(self._glyphSet.keys())))
        fb.setupCharacterMap({uni: names[0] for uni, names in self.font.unicodeData.items()})
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
        fb.setupHorizontalHeader(ascent=self.font.info.ascender, descent=self.font.info.descender)
        fb.setupNameTable(nameStrings)
        fb.setupPost()

    @property
    def glyphSet(self):
        return self._glyphSet

    @property
    def metrics(self):
        return {name: (glyph.width, 0) for name, glyph in self._glyphSet.items()}

    @property
    def charStrings(self):
        return {name: glyph.t2CharString for name, glyph in self._glyphSet.items()}

    @property
    def otf(self):
        fb = self.fb
        fb.setupHorizontalMetrics(self.metrics)
        fb.setupCFF(self.fontName, {"FullName": self.fontName}, self.charStrings, {})
        self._otf = fb.font
        return self._otf

@fontCachedMethod("UnicodeData.Changed", "Layer.GlyphAdded", "Layer.GlyphDeleted", "Info.Changed")
def dummyOTFCompiler(font):
    return DummyOTFCompiler(font)

@fontCachedMethod("UnicodeData.Changed", "Layer.GlyphAdded", "Layer.GlyphDeleted", "Info.Changed")
def _dummyOTF(font):
    return font.dummyOTFCompiler.otf

@fontCachedMethod("UnicodeData.Changed", "Layer.GlyphAdded", "Layer.GlyphDeleted", "Info.Changed", "Glyph.AnchorsChanged", "Glyph.KerningChanged", "Features.Changed")
def dummyOTF(font):
    """
    OTF file without outlines and metrics for shaping text.
    """
    return font.features.getCompiler(ttFont=font._dummyOTF, glyphSet=font.dummyOTFCompiler.glyphSet).ttFont

@fontCachedMethod("UnicodeData.Changed", "Layer.GlyphAdded", "Layer.GlyphDeleted", "Info.Changed", "Glyph.ContoursChanged", "Glyph.ComponentsChanged", "Component.BaseGlyphChanged", "Glyph.WidthChanged")
def previewOTF(font):
    """
    OTF file with outlines for previewing.
    """
    d = font.dummyOTFCompiler
    d.glyphSet.update({name:font[name] for name in font.keys()})
    return d.otf

@fontCachedMethod("UnicodeData.Changed", "Layer.GlyphAdded", "Layer.GlyphDeleted", "Info.Changed", "Glyph.ContoursChanged", "Glyph.ComponentsChanged", "Component.BaseGlyphChanged", "Glyph.WidthChanged", "Glyph.AnchorsChanged", "Glyph.KerningChanged", "Features.Changed")
def previewOTFWithFeatures(font):
    """
    OTF file with outlines and features for previewing.
    """
    return font.features.getCompiler(ttFont=font.previewOTF, glyphSet=font.dummyOTFCompiler.glyphSet).ttFont

@fontMethod
def savePreviewOTFWithFeatures(font, path):
    """
    OTF file with outlines and features for previewing.
    """
    otf = font.previewOTFWithFeatures
    otf.save(path)

@fontCachedMethod("UnicodeData.Changed", "Layer.GlyphAdded", "Layer.GlyphDeleted")
def glyphsProdutionNames(font):
    result = {}
    postscriptNames = font.lib.get("public.postscriptNames")
    for g in self.font:
        exist = postscriptNames.get(g.name, None)
        if exist:
            result[g.name] = exist
        else:
            baseName = glyph.produtionName
            i = 0
            produtionName = baseName
            while produtionName in result.values():
                result[g.name] = baseName + i
    return result

@fontMethod
def saveGlyphsProdutionNames(font):
    font.lib["public.postscriptNames"] = font.glyphsProdutionNames

@fontCachedMethod("UnicodeData.Changed", "Layer.GlyphAdded", "Layer.GlyphDeleted", "Features.Changed")
def produtionName(glyph):
    """Return the final production name for the glyph which is going to be saved in the final binary"""
    unicodes = glyph.unicodes
    if len(unicodes) == 1:
        uv = unicodes[0]
        return "{}{:04X}".format(
            "u" if uv > 0xFFFF else "uni", uv
        )
    else:
        unicodes = []
        for gl, sub in glyph.features.sourceGlyphs.items():
            for gn in gl:
                unicodes.extend(font[gn].unicodes)
        if all(v and v <= 0xFFFF for v in unicodes):
            return "uni" + "".join("%04X" % v for v in unicodes)
    return glyph.name
