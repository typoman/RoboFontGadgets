from fontgadgets.decorators import *
from collections import OrderedDict
from ufo2ft.featureCompiler import FeatureCompiler
from ufo2ft.featureWriters import (
    GdefFeatureWriter,
    CursFeatureWriter,
    KernFeatureWriter,
    MarkFeatureWriter,
)

class IsolatedFeatureCompiler(FeatureCompiler):
    """
    overrides ufo2ft to exclude ufo existing features in the generated GPOS.
    """

    def setupFeatures(self):
        featureFile = (
            self.ufo.features.defaultScripts
        )  # ufo2ft requires default scripts to function properly
        lenExtraScripts = len(self.ufo.features.defaultScripts.asFea())
        for writerClass in self.featureWriters:
            writerClass().write(self.ufo, featureFile, compiler=self)
        self.features = featureFile.asFea()[lenExtraScripts + 1 :]


@font_method
def getCompiler(features, featureWriters=None, ttFont=None, glyphSet=None):
    """
    Returns a `ufo2ft.featureCompiler.FeatureCompiler` based on the given featurewitres.
    """
    font = features.font
    skipExport = font.lib.get("public.skipExportGlyphs", [])
    glyphOrder = (gn for gn in font.glyphOrder if gn not in skipExport)
    if featureWriters is not None:
        featuresCompiler = IsolatedFeatureCompiler(
            font, ttFont=ttFont, glyphSet=glyphSet, featureWriters=featureWriters
        )
        featuresCompiler.featureWriters = featureWriters
    else:
        featuresCompiler = FeatureCompiler(
            font, ttFont=ttFont, glyphSet=glyphSet, featureWriters=featureWriters
        )
    featuresCompiler.glyphSet = OrderedDict((gn, font[gn]) for gn in glyphOrder)
    featuresCompiler.compile()
    return featuresCompiler


@font_cached_property("Kerning.Changed", "Layer.GlyphAdded", "Layer.GlyphDeleted")
def kern(features):
    """
    Compiled kerning feature using ufo2ft.
    """
    return features.getCompiler([KernFeatureWriter, GdefFeatureWriter]).features


@font_cached_property("Glyph.AnchorsChanged", "Layer.GlyphAdded", "Layer.GlyphDeleted")
def mark(features):
    """
    Compiled mark feature using ufo2ft.
    """
    return features.getCompiler(
        [
            MarkFeatureWriter,
        ]
    ).features


@font_cached_property(
    "Glyph.AnchorsChanged",
    "Layer.GlyphAdded",
    "Layer.GlyphDeleted",
    "Features.TextChanged",
)
def gdef(features):
    """
    Compiled GDEF feature using ufo2ft.
    """
    return features.getCompiler(
        [
            GdefFeatureWriter,
        ]
    ).features


@font_cached_property("Glyph.AnchorsChanged", "Layer.GlyphAdded", "Layer.GlyphDeleted")
def curs(features):
    """
    Compiled cursive attatchment feature using ufo2ft.
    """
    return features.getCompiler(
        [
            CursFeatureWriter,
        ]
    ).features
