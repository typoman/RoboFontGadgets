import uharfbuzz as hb
import fontgadgets.extensions.compile
from fontgadgets.extensions.layout.segmenting import textSegments, reorderedSegments, UNKNOWN_SCRIPT, Segment
from types import SimpleNamespace
# based on drawbot-skia
from collections import namedtuple, deque
import itertools

ShapedSegment = namedtuple(
    "ShapedSegment",
    [
        "segment",  # Original Segment object
        "glyphs",  # List of glyph names
        "positions",  # List of (dx, dy) glyph offsets
        "advances",  # List of (ax, ay) glyph advances
        "clusters",  # List of character clusters
        "width",  # Total advance width of the segment glyphs
    ],
)

ShapedParagraph = namedtuple(
    "ShapedParagraph",
    [
        "baseLevel",  # Paragraph's base bidi level
        "segments",  # List of ShapedSegment objects
    ],
)

GlyphRecord = namedtuple("GlyphRecord", ["glyph", "position"])
GlyphLine = namedtuple("GlyphLine", ["records"])

class HBShaper:

    def __init__(self, font):
        """
        Initializes the HBShaper with the given font and.

        Args:
            font: The font to use.
        """

        self._font = font
        self.ttFont = font._emptyOTFWithFeatures
        self._fontData = font.compiler.getOTFData()
        self.face = hb.Face(self._fontData, 0)
        self.hbFont = hb.Font(self.face) # Separate hb.Font instance for shapeShape
        self.hbFont.scale = (self.face.upem, self.face.upem)
        self.glyphOrder = self.ttFont.getGlyphOrder()
        hb.ot_font_set_funcs(self.hbFont)

    def shapeTextToParagraphs(self, txt, features=None, language=None, script=None, variations=None):
        """
        Shapes the given text using the provided font and features.

        Args:
            txt (str): The unicode string to apply open type features shaping.
            features (dict, optional): The font features. {feat_tag: False/True, ...}
            language (str, optional): The language.
            script (str, optional): The script.
            variations (dict, optional): The font variations. {axis_tag: value, ...}

        Returns:
            list: list of ShapedParagraph instances.
        """
        result = []
        for parTxt in txt.split("\n"):
            segments, baseLevel = textSegments(parTxt)
            shapedSegmentList = []
            for segment in segments:
                runInfo = self._shapeTextSegment(
                    segment=segment,
                    features=features,
                    language=language,
                    variations=variations,
                )
                shapedSegmentList.append(runInfo)
            result.append(ShapedParagraph(baseLevel, shapedSegmentList))
        return result

    def _shapeTextSegment(self, segment, features=None, variations=None, language=None, script=None):
        if features is None:
            features = {}
        if variations is None:
            variations = {}

        hbFont = self.hbFont
        hbFont.set_variations(variations)
        buf = hb.Buffer.create()
        buf.add_str(segment.text)
        buf.guess_segment_properties()
        buf.cluster_level = hb.BufferClusterLevel.MONOTONE_CHARACTERS
        if language is not None:
            buf.language = language
        if script is not None:
            buf.script = script

        hb.shape(hbFont, buf, features)
        gids = [info.codepoint for info in buf.glyph_infos]
        go = self.glyphOrder
        glyphs = [go[i] for i in gids]
        clusters = [info.cluster for info in buf.glyph_infos]
        positions = []
        advances = []
        width = 0
        for pos in buf.glyph_positions:
            dx, dy, ax, ay = pos.position
            positions.append((dx, dy))
            advances.append((ax, ay))
            width += abs(ax)

        return ShapedSegment(
            segment=segment,
            glyphs=glyphs,
            positions=positions,
            advances=advances,
            clusters=clusters,
            width=width,
        )

    def getFeatures(self, otTableTag):
        features = set()
        for scriptIndex, script in enumerate(hb.ot_layout_table_get_script_tags(self.face, otTableTag)):
            langIdices = list(range(len(hb.ot_layout_script_get_language_tags(self.face, otTableTag, scriptIndex))))
            langIdices.append(0xFFFF)
            for langIndex in langIdices:
                features.update(hb.ot_layout_language_get_feature_tags(self.face, otTableTag, scriptIndex, langIndex))
        return features

    def getStylisticSetNames(self):
        tags = _stylisticSets & set(self.getFeatures("GSUB"))
        if not tags:
            return {}
        gsubTable = self.ttFont.get("GSUB")
        nameTable = self.ttFont.get("name")
        if gsubTable is None or nameTable is None:
            return {}
        gsubTable = gsubTable.table
        names = {}
        for feature in gsubTable.FeatureList.FeatureRecord:
            tag = feature.FeatureTag
            if tag in tags and tag not in names:
                feaParams = feature.Feature.FeatureParams
                if feaParams is not None:
                    nameRecord = nameTable.getName(feaParams.UINameID, 3, 1)
                    if nameRecord is not None:
                        names[tag] = nameRecord.toUnicode()
        return names

    def getScriptsAndLanguages(self, otTableTag):
        scriptsAndLanguages = {}
        for scriptIndex, script in enumerate(hb.ot_layout_table_get_script_tags(self.face, otTableTag)):
            scriptsAndLanguages[script] = set(hb.ot_layout_script_get_language_tags(self.face, otTableTag, scriptIndex))
        return scriptsAndLanguages