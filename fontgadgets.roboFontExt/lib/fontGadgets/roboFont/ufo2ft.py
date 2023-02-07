import ufo2ft
from fontGadgets.tools import fontCachedMethod, fontMethod
from fontTools.pens.t2CharStringPen import T2CharStringPen
from defcon import Glyph
"""
Tools to make ufo2ft more accessible in RF
"""

@fontCachedMethod("Glyph.ContoursChanged", "Glyph.ComponentsChanged", "Component.BaseGlyphChanged")
def t2CharString(glyph):
    pen = T2CharStringPen(0, glyph.font)
    glyph.removedOverlapsCopy().draw(pen)
    return pen.getCharString()

ufo2ft.outlineCompiler.StubGlyph.t2CharString = property(lambda glyph: t2CharString(glyph))

class CachedOutlineOTFCompiler(ufo2ft.outlineCompiler.OutlineOTFCompiler):

    def compileGlyphs(self):
        compiledGlyphs = {}
        for glyphName in self.glyphOrder:
            glyph = self.allGlyphs[glyphName]
            compiledGlyphs[glyphName] = glyph.t2CharString
        return compiledGlyphs

    @staticmethod
    def makeMissingRequiredGlyphs(font, glyphSet, sfntVersion, notdefGlyph=None):
        glyphSet[".notdef"] = Glyph()

    @property
    def fontBoundingBox(self):
        return EMPTY_BOUNDING_BOX

    def setupTable_hmtx(self):
        self.otf["hmtx"] = hmtx = newTable("hmtx")
        hmtx.metrics = {}
        for glyphName, glyph in self.allGlyphs.items():
            width = otRound(glyph.width)
            if width < 0:
                width = 0
            hmtx[glyphName] = (width, 0)

@fontMethod
def previewOTF(font, path=None, compileGPOS=True):
    glyphSet = font
    otf = CachedOutlineOTFCompiler(font).compile()
    if compileGPOS:
        featureCompiler = ufo2ft.featureCompiler.FeatureCompiler(font, otf)
        otFont = featureCompiler.compile()
    if path is not None:
        otFont.save(path)
    return otFont


