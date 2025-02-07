import uharfbuzz as hb
import fontgadgets.extensions.compile
from fontgadgets.extensions.layout.segmenting import textSegments, reorderedSegments, UNKNOWN_SCRIPT
from types import SimpleNamespace
# based on drawbot-skia

def shapeSegment(
    hbFont,
    text,
    fontSize=None,
    startPos=(0, 0),
    startCluster=0,
    flippedCanvas=False,
    *,
    features=None,
    variations=None,
    direction=None,
    language=None,
    script=None
):
    """
    Shapes the given text using the provided HarfBuzz font.

    Args:
        hbFont (hb.Font): The HarfBuzz font to use for shaping.
        text (str): The text to shape.
        fontSize (float, optional): The font size. Defaults to None.
        startPos (tuple, optional): The starting position. Defaults to (0, 0).
        startCluster (int, optional): The starting cluster. Defaults to 0.
        flippedCanvas (bool, optional): Whether the canvas is flipped. Defaults to False.
        features (dict, optional): The font features. Defaults to None.
        variations (dict, optional): The font variations. Defaults to None.
        direction (int, optional): The text direction. Defaults to None.
        language (str, optional): The language. Defaults to None.
        script (str, optional): The script. Defaults to None.

    Returns:
        SimpleNamespace: An object containing the shaped glyph IDs, clusters, positions, and end position.
    """
    if features is None:
        features = {}
    if variations is None:
        variations = {}

    face = hbFont.face
    if fontSize is None:
        fontScaleX = fontScaleY = 1
    else:
        fontScaleX = fontScaleY = fontSize / face.upem
    if flippedCanvas:
        fontScaleY = -fontScaleY

    hbFont.scale = (face.upem, face.upem)
    hbFont.set_variations(variations)

    hb.ot_font_set_funcs(hbFont)

    buf = hb.Buffer.create()
    buf.add_str(text)  # add_str() does not accept str subclasses
    buf.guess_segment_properties()
    buf.cluster_level = hb.BufferClusterLevel.MONOTONE_CHARACTERS

    if direction is not None:
        buf.direction = direction
    if language is not None:
        buf.language = language
    if script is not None:
        buf.script = script

    hb.shape(hbFont, buf, features)

    gids = [info.codepoint for info in buf.glyph_infos]
    clusters = [info.cluster + startCluster for info in buf.glyph_infos]
    positions = []
    startPosX, startPosY = startPos
    x = y = 0
    for pos in buf.glyph_positions:
        dx, dy, ax, ay = pos.position
        positions.append(
            (
                startPosX + (x + dx) * fontScaleX,
                startPosY + (y + dy) * fontScaleY,
            )
        )
        x += ax
        y += ay
    endPos = startPosX + x * fontScaleX, startPosY + y * fontScaleY
    return SimpleNamespace(
        gids=gids,
        clusters=clusters,
        positions=positions,
        endPos=endPos,
    )

class HBShaper:

    def __init__(self, font, fontSize=None):
        """
        Initializes the HBShaper with the given font and font size.

        Args:
            font: The font to use.
            fontSize (float, optional): The font size. Defaults to None.
        """

        self._font = font
        self.fontSize = fontSize
        self.ttFont = font._emptyOTFWithFeatures
        self._fontData = font.compiler.getOTFData()
        self.face = hb.Face(self._fontData, 0)
        self.hbFont = hb.Font(self.face) # Separate hb.Font instance for shapeShape
        self.hbFont.scale = (self.face.upem, self.face.upem)
        self.glyphOrder = self.ttFont.getGlyphOrder()
        hb.ot_font_set_funcs(self.hbFont)

    def shape(self, txt, features=None,
              direction=None, language=None, script=None, variations=None):
        """
        Shapes the given text using the provided font and features.

        Args:
            txt (str): The text to shape.
            features (dict, optional): The font features. Defaults to None.
            direction (int, optional): The text direction. Defaults to None.
            language (str, optional): The language. Defaults to None.
            script (str, optional): The script. Defaults to None.
            variations (dict, optional): The font variations. Defaults to None.

        Returns:
            SimpleNamespace: An object containing the shaped glyph IDs, clusters, positions, and end position.
        """
        segments, baseLevel = textSegments(txt)
        segments = reorderedSegments(segments, baseLevel % 2, lambda item: item[2] % 2)
        startPos = (0, 0)
        glyphsInfo = None
        for runChars, segmentScript, bidiLevel, index in segments:
            runInfo = shapeSegment(
                hbFont=self.hbFont,
                fontSize=self.fontSize,
                text=runChars,
                startPos=startPos,
                startCluster=index,
                flippedCanvas=True,
                features=features,
                language=language,
            )
            if glyphsInfo is None:
                glyphsInfo = runInfo
            else:
                glyphsInfo.gids += runInfo.gids
                glyphsInfo.clusters += runInfo.clusters
                glyphsInfo.positions += runInfo.positions
                glyphsInfo.endPos = runInfo.endPos
            startPos = runInfo.endPos
        if glyphsInfo is not None:
            glyphsInfo.baseLevel = baseLevel
        return glyphsInfo

