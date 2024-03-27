import uharfbuzz as hb
"""
Based on the code in fontgoggles written by Just van Rossum.
"""

class GlyphRunInfo:
    __slots__ = ["name", "path", "dx", "dy", "ax", "ay", "advance"]

    def __init__(self, name, dx, dy, ax, ay, advance):
        self.name = name
        self.dx = dx
        self.dy = dy
        self.ax = ax
        self.ay = ay
        self.advance = advance

    def __repr__(self):
        return self.name

class HBShaper:

    def __init__(self, f):
        compiler = f.compiler
        self.ttFont = compiler.font
        self.ufo = f
        self.face = hb.Face(self._fontData, 0)
        self.font = hb.Font(self.face)
        self.glyphOrder = self.ttFont.getGlyphOrder()

    def shape(self, text, features=None,
              direction=None, language=None, script=None):
        if features is None:
            features = {}
        self.font.scale = (self.face.upem, self.face.upem)
        hb.ot_font_set_funcs(self.font)
        buf = hb.Buffer.create()
        buf.add_str(str(text))  # add_str() does not accept str subclasses
        buf.guess_segment_properties()

        buf.cluster_level = hb.BufferClusterLevel.MONOTONE_CHARACTERS

        if direction is not None:
            buf.direction = direction
        if language is not None:
            buf.set_language_from_ot_tag(language)
        if script is not None:
            buf.set_script_from_ot_tag(script)

        hb.shape(self.font, buf, features)

        glyphOrder = self.glyphOrder
        self.glyphRun = []
        adv = 0
        if buf.glyph_positions:
            for info, pos in zip(buf.glyph_infos, buf.glyph_positions):
                name = glyphOrder[info.codepoint]
                dx, dy, ax, ay = pos.position
                info = GlyphRunInfo(
                name,
                dx, dy, ax, ay,
                adv,
                )
                self.glyphRun.append(info)
                adv += ax
        return self.glyphRun
