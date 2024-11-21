from fontgadgets.decorators import font_cached_method
from fontgadgets.extensions.features import *

@font_cached_property("Features.TextChanged", "Layer.GlyphAdded", " Layer.GlyphDeleted")
def getFeaturesFromGlyphs(features, glyphNameList):
    """
    Returns the fonttools ast.Feature objects that reference the given glyphs.

    Args:
    glyphNameList (list of str):
        A list of glyph names to find features for.

    Returns:
    set of fontTools.ttLib.getTableClass('feat').Feature:
        A set of features that reference the given glyphs.
    """
    result = set()
    font = features.font
    for gn in glyphNameList:
        g = font[gn]
        for gl, subs in g.features.sourceGlyphs.items():
            for s in subs:
                result.update(s.features)
    return result

@font_cached_property("Features.TextChanged", "Layer.GlyphAdded", " Layer.GlyphDeleted")
def getRelatedGlyphsForFeatures(features, featuresList):
    """
    Returns glyphs in a font that are referenced by a set of features.

    Args:
    featuresList (iterable): An iterable containing fonttools ast.Feature objects.

    Returns:
    list: A list of glyph names that are referenced inside the given features.
    """
    result = []
    font = features.font
    for g in font:
        for gl, subs in g.features.sourceGlyphs.items():
            for s in subs:
                if set(s.features) & features:
                    result.append(g.name)
    return result
