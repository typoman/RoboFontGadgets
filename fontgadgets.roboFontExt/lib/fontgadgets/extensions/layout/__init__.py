from .shaper import HBShaper
# based on drawbot-skia

def alignGlyphPositions(glyphsInfo, align):
    """
    Aligns the glyph positions based on the given alignment.

    Args:
        glyphsInfo (SimpleNamespace): The glyph information.
        align (str, optional): The alignment. Defaults to None.
    """
    textWidth = glyphsInfo.endPos[0]
    if align is None:
        align = "left" if not glyphsInfo.baseLevel else "right"
    xOffset = 0
    if align == "right":
        xOffset = -textWidth
    elif align == "center":
        xOffset = -textWidth / 2
    glyphsInfo.positions = [(x + xOffset, y) for x, y in glyphsInfo.positions]


class Layout():

    def __init__(self, font):
        """
        Initializes the Layout with the given font.

        Args:
            font (defcon.Font) 
        """
        self.shaper = HBShaper(font=font)

    def getGlyphNamesAndPositionsFromText(self, txt, features=None,
              direction=None, language=None, script=None, variations=None, offset=None, align=None):
        """
        Gets the glyph names and positions from the given text.

        Args:
            txt (str): The text to get glyph names and positions from.
            features (dict, optional): The font features. Defaults to None.
            direction (int, optional): The text direction. Defaults to None.
            language (str, optional): The language. Defaults to None.
            script (str, optional): The script. Defaults to None.
            variations (dict, optional): The font variations. Defaults to None.
            offset (tuple, optional): The offset. Defaults to None.
            align (str, optional): The alignment. Defaults to None.

        Returns:
            list: A list of tuples containing the glyph name and position.
        """
        glyphRun = [] # [(glyphName, position)]
        if txt:
            glyphsInfo = self.shaper.shape(txt)
            alignGlyphPositions(glyphsInfo, align)
            x, y = (0, 0) if offset is None else offset
            for gid, pos in zip(glyphsInfo.gids, glyphsInfo.positions):
                glyphName = self.shaper.glyphOrder[gid]
                glyphRun.append((glyphName, (pos[0] + x, pos[1] + y)))
        return glyphRun

