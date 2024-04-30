from fontgadgets.decorators import font_cached_property

@font_cached_property("Glyph.AnchorsChanged")
def anchorsMap(glyph):
    """
    Returns a dictionary of {anchorName: [anchor1, anchor2], etc}
    """
    result = {}
    [result.setdefault(a.name, []).append(a) for a in glyph.anchors]
    return result
