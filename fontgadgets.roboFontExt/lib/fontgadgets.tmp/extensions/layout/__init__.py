from fontgadgets.decorators import font_cached_method
from . import shaper

@font_cached_method("UnicodeData.Changed")
def getGlyphsFromText(font, text, shaper='harfbuzz'):
    """
    Returns list of glyph names from the given 'text' string.
    """
    glyphs = []
    if shaper is None:
        cmap = font.cmap
        for c in text:
            glyphs.append(cmap.get(ord(c), ['.notdef'])[0])
        return glyphs
