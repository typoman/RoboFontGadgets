from fontgadgets.decorators import *
import uharfbuzz as hb
import fontgadgets.extensions.compile
from fontgadgets.extensions.layout.segmenting import textSegments, Segment, reorderedSegments
# based on drawbot-skia
from itertools import islice


class GlyphRun:
    """
    A `GlyphRun` represents a list of glyphs produced by the HarfBuzz shaping
    engine from a segment of a text with a single bidi level for a specific
    `Segment` of text. It contains the glyph names, their offsets, advances
    (calculated width after kerning), and cluster mapping, which links glyphs
    back to the original characters in the text.

    GlyphRun direction is always visual order as in left to right. This means
    glyphs are supposed to be rendered from left to right on the screen no
    matter if their direction is RTL or LTR. The inital postions in GlyphRun
    is relative postion to the glyph on the left. So in order to draw glyphs,
    layout engine should each time advance the next glyph position to get its
    final position in the layout.


    Attributes:
        segment (Segment): The original text segment associated with this run.
            For a sliced run, this segment is updated to reflect the sliced text
            and its new start index.
        width (float): The total advance width of all glyphs in the run.
        glyphs (iterator): An iterator for the glyph names in the run.
        offsets (iterator): An iterator for the (x_offset, y_offset) tuples for
            each glyph.
        advances (iterator): An iterator for the (x_advance, y_advance) tuples for
            each glyph.
        clusters (iterator): An iterator for the cluster indices, mapping each
            glyph back to its corresponding character index in the `segment.text`.
            For a sliced run, these clusters are relative to the start of the
            slice's `segment.text`.

    """

    __slots__ = (
        "_segment",
        "_source",
        "_start",
        "_end",
        "_relative_clusters",
        "_glyphs",
        "_offsets",
        "_advances",
        "_clusters",
        "_width",
        "_font",
    )

    def __init__(
        self,
        segment,
        font,
        glyphs=None,
        offsets=None,
        advances=None,
        clusters=None,
        source=None,
        start=None,
        end=None,
        relative_clusters=None,
    ):
        object.__setattr__(self, "_segment", segment)
        if source:
            object.__setattr__(self, "_source", source._source)
            object.__setattr__(self, "_start", start)
            object.__setattr__(self, "_end", end)
            object.__setattr__(self, "_relative_clusters", relative_clusters)
            object.__setattr__(self, "_font", source._font)
        else:
            object.__setattr__(self, "_source", self)
            object.__setattr__(self, "_glyphs", tuple(glyphs))
            object.__setattr__(self, "_offsets", tuple(offsets))
            object.__setattr__(self, "_advances", tuple(advances))
            object.__setattr__(self, "_clusters", tuple(clusters))
            object.__setattr__(self, "_relative_clusters", tuple(clusters))
            object.__setattr__(self, "_start", 0)
            object.__setattr__(self, "_end", len(glyphs))
            object.__setattr__(self, "_font", font)
        object.__setattr__(self, "_width", None)

    def __setattr__(self, name, value):
        raise AttributeError("GlyphRun is immutable")

    @property
    def width(self):
        """The total advance width of all glyphs in the run."""
        if self._width is None:
            adv_iter = islice(self._source._advances, self._start, self._end)
            calculated_width = sum(abs(adv[0]) for adv in adv_iter)
            object.__setattr__(self, '_width', calculated_width)
        return self._width

    @property
    def segment(self):
        """The original text segment associated with this run."""
        return self._segment

    @property
    def glyphs(self):
        """An iterator for the glyph names in the run."""
        return islice(self._source._glyphs, self._start, self._end)

    @property
    def font(self):
        """The font used for this glyph run."""
        return self._font

    @property
    def offsets(self):
        """An iterator for the (x_offset, y_offset) tuples for each glyph."""
        return islice(self._source._offsets, self._start, self._end)

    @property
    def advances(self):
        """An iterator for the (x_advance, y_advance) tuples for each glyph."""
        return islice(self._source._advances, self._start, self._end)

    @property
    def clusters(self):
        """An iterator for the cluster indices, mapping each
        glyph back to its corresponding character index in the `segment.text`.
        """
        return iter(self._relative_clusters)

    def __len__(self):
        return self._end - self._start

    def __eq__(self, other):
        if not isinstance(other, GlyphRun):
            return NotImplemented
        return (
            self.segment == other.segment
            and list(self.glyphs) == list(other.glyphs)
            and list(self.offsets) == list(other.offsets)
            and list(self.advances) == list(other.advances)
            and list(self.clusters) == list(other.clusters)
        )

    def __repr__(self):
        return (f"GlyphRun(segment={self.segment!r}, glyphs={list(self.glyphs)!r}, "
                f"offsets={list(self.offsets)!r}, advances={list(self.advances)!r}, "
                f"clusters={list(self.clusters)!r})")
    
    def slice(self, start, end):
        # This class uses a special mechanism for slicing. When a `GlyphRun` is
        # sliced, it creates a new `GlyphRun` instance that acts as a
        # lightweight "view" into the original, full `GlyphRun`'s data. This
        # avoids data duplication and is efficient for operations like line
        # breaking, which involves frequent slicing.
        if start < 0 or end > len(self) or start > end:
            raise IndexError('Slice indices are out of bounds')
        abs_clusters_for_slice = list(islice(self._source._clusters, self._start + start, self._start + end))
        if not abs_clusters_for_slice:
            new_text = ''
            new_segment_start_index = self.segment.start_index
            new_clusters_relative = []
        else:
            min_char_index = min(abs_clusters_for_slice)
            max_char_index = max(abs_clusters_for_slice)
            new_text = self._source.segment.text[min_char_index:max_char_index + 1]
            new_segment_start_index = self._source.segment.start_index + min_char_index
            new_clusters_relative = [c - min_char_index for c in abs_clusters_for_slice]
        new_text_segment = Segment(new_text, self.segment.bidi_level, new_segment_start_index)
        return GlyphRun(
            segment=new_text_segment,
            font=self.font,
            source=self,
            start=self._start + start,
            end=self._start + end,
            relative_clusters=new_clusters_relative,
        )

_stylisticSets = {f"ss{i:02}" for i in range(1, 21)}

class HBShaper:

    def __init__(self, font):
        """
        Initializes a harfbuzz shaper for the given font.

        Args:
            font: The font to use.
        """

        self._font = font
        self.ttFont = font._otfForHBShaper
        self._fontData = font.compiler.getOTFData()
        self.face = hb.Face(self._fontData, 0)
        self.hbFont = hb.Font(self.face)
        self.hbFont.scale = (self.face.upem, self.face.upem)
        self.glyphOrder = self.ttFont.getGlyphOrder()
        hb.ot_font_set_funcs(self.hbFont)

    def setFontScale(self, scale):
            """
            Sets the font scale for the HarfBuzz font object.

            Args:
                scale (int): The scale value to set for both x and y dimensions.
            """
            self.hbFont.scale = (scale, scale)

    def shapeTextToGlyphRuns(self, txt, base_level=None, features=None, language=None, script=None, variations=None, scale=None):
        """
        Shapes the given text using the provided font and features.

        Args:
            txt (str): The unicode string to apply open type features shaping.
            baseLevel (int): Base level for direction of the text.
            features (dict, optional): The font features. {feat_tag: False/True, ...}
            language (str, optional): The language.
            script (str, optional): The script.
            variations (dict, optional): The font variations. {axis_tag: value, ...}
            scale (int, optional): If provided, sets the font scale before shaping.

        Returns:
            list: GlyphRun
        """
        if scale is not None:
            self.hbFont.scale = (scale, scale)
        glyphRunList = []
        segments, _baseLevel = textSegments(txt)
        if base_level is None:
            base_level = _baseLevel
        isSegmentRTL = lambda s: s.bidi_level % 2 == 1
        segments = reorderedSegments(segments, base_level, isSegmentRTL)
        for segment in segments:
            runInfo = self._shapeTextSegment(
                segment=segment,
                features=features,
                language=language,
                variations=variations,
                script=script,
            )
            glyphRunList.append(runInfo)
        return glyphRunList

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
        offsets = [(pos.x_offset, pos.y_offset) for pos in buf.glyph_positions]
        advances = [(pos.x_advance, pos.y_advance) for pos in buf.glyph_positions]

        return GlyphRun(
            segment=segment,
            font=self._font,
            glyphs=glyphs,
            offsets=offsets,
            advances=advances,
            clusters=clusters,
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


@font_cached_property( "UnicodeData.Changed", "Layer.GlyphAdded",
                      "Layer.GlyphDeleted", "Info.Changed",
                      "Features.TextChanged", "Glyph.WidthChanged",
                      "Anchor.Changed", "Groups.Changed", "Kerning.Changed",)
def _otfForHBShaper(font):
    """
    OTF file without outlines for shaping text in harfbuzz.
    """
    otf = font._otfWithMetrics
    fb = font.compiler.builder
    compiler = font.compiler
    compiler._otf = compiler.font.features.getCompiler(ttFont=compiler._otf, glyphSet=compiler._glyphSet).ttFont
    return compiler._otf


@font_cached_property( "UnicodeData.Changed", "Layer.GlyphAdded",
                      "Layer.GlyphDeleted", "Info.Changed",
                      "Features.TextChanged", "Glyph.WidthChanged",
                      "Anchor.Changed", "Groups.Changed", "Kerning.Changed",)
def _HBShaper(font):
    hbshaper = HBShaper(font)
    return hbshaper
