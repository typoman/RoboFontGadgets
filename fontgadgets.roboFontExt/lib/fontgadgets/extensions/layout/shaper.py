import uharfbuzz as hb
import fontgadgets.extensions.compile
from fontgadgets.extensions.layout.segmenting import textSegments, reorderedSegments, UNKNOWN_SCRIPT, Segment
from types import SimpleNamespace
# based on drawbot-skia
from collections import namedtuple, deque
import itertools
from itertools import islice
from functools import cached_property

Paragraph = namedtuple(
    "Paragraph",
    [
        "baseLevel",  # Paragraph's base bidi level
        "glyphRuns",  # List of GlyphRun objects
    ],
)

GlyphRecord = namedtuple("GlyphRecord", ["glyph", "position"])
GlyphLine = namedtuple("GlyphLine", ["records", "glyphRuns"])


class GlyphRun:
    """
    A `GlyphRun` represents a list of glyphs produced by the HarfBuzz shaping
    engine for a specific `Segment` of text. It contains the shaped glyphs,
    their positions, advances (calculated width after kerning), and cluster
    mapping, which links glyphs back to the original characters in the text.

    GlyphRun direction is always visual order as in left to right. This means
    glyphs are supposed to be rendered from left to right on the screen no
    matter if their direction is RTL or LTR. The inital postions in GlyphRun
    is relative postion to the glyph on the left. So in order to draw glyphs,
    layout engine should each time advance the next glyph position to get its
    final position in the layout.

    This class uses a mechanism for slicing. When a `GlyphRun` is sliced, it
    creates a new `GlyphRun` instance that acts as a lightweight "view" into
    the original, full `GlyphRun`'s data. This avoids data duplication and is
    efficient for operations like line breaking, which involves frequent
    slicing.

    Attributes:
        segment (Segment): The original text segment associated with this run.
            For a sliced run, this segment is updated to reflect the sliced text
            and its new start index.
        width (float): The total advance width of all glyphs in the run.
        glyphs (iterator): An iterator for the glyph names in the run.
        positions (iterator): An iterator for the (x_offset, y_offset) tuples for
            each glyph.
        advances (iterator): An iterator for the (x_advance, y_advance) tuples for
            each glyph.
        clusters (iterator): An iterator for the cluster indices, mapping each
            glyph back to its corresponding character index in the `segment.text`.
            For a sliced run, these clusters are relative to the start of the
            slice's `segment.text`.

    Example of creating a `GlyphRun` from scratch:
    >>> from types import SimpleNamespace
    >>> text = "Hello"
    >>> segment = Segment(text=text, bidi_level=0, start_index=0)
    >>> glyphs = ['H', 'e', 'l', 'l', 'o']
    >>> positions = [(0, 0), (0, 0), (0, 0), (0, 0), (0, 0)]
    >>> advances = [(50, 0), (40, 0), (30, 0), (30, 0), (50, 0)]
    >>> clusters = [0, 1, 2, 3, 4]
    >>> full_run = GlyphRun(
    ...     segment=segment,
    ...     glyphs=glyphs,
    ...     positions=positions,
    ...     advances=advances,
    ...     clusters=clusters
    ... )
    >>> print(full_run.width)
    200
    >>> print(list(full_run.glyphs))
    ['H', 'e', 'l', 'l', 'o']

    Example of creating a `GlyphRun` by slicing:
    >>> # Continuing from the previous example
    >>> sliced_run = full_run.slice(1, 4)  # Slice "ell"
    >>> print(sliced_run.segment.text)
    ell
    >>> print(sliced_run.segment.start_index)
    1
    >>> print(list(sliced_run.glyphs))
    ['e', 'l', 'l']
    >>> print(list(sliced_run.clusters)) # Clusters are relative to the new segment
    [0, 1, 2]
    >>> print(sliced_run.width)
    100.0
    """

    __slots__ = (
        "_segment",
        "_source",
        "_start",
        "_end",
        "_relative_clusters",
        "_glyphs",
        "_positions",
        "_advances",
        "_clusters",
        "_width",
    )

    def __init__(
        self,
        segment,
        glyphs=None,
        positions=None,
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
        else:
            object.__setattr__(self, "_source", self)
            object.__setattr__(self, "_glyphs", tuple(glyphs))
            object.__setattr__(self, "_positions", tuple(positions))
            object.__setattr__(self, "_advances", tuple(advances))
            object.__setattr__(self, "_clusters", tuple(clusters))
            object.__setattr__(self, "_relative_clusters", tuple(clusters))
            object.__setattr__(self, "_start", 0)
            object.__setattr__(self, "_end", len(glyphs))
        object.__setattr__(self, "_width", None)

    def __setattr__(self, name, value):
        raise AttributeError("GlyphRun is immutable")

    @property
    def width(self):
        if self._width is None:
            adv_iter = islice(self._source._advances, self._start, self._end)
            calculated_width = sum(abs(adv[0]) for adv in adv_iter)
            object.__setattr__(self, '_width', calculated_width)
        return self._width

    @property
    def segment(self):
        return self._segment

    @property
    def glyphs(self):
        return islice(self._source._glyphs, self._start, self._end)

    @property
    def positions(self):
        return islice(self._source._positions, self._start, self._end)

    @property
    def advances(self):
        return islice(self._source._advances, self._start, self._end)

    @property
    def clusters(self):
        return iter(self._relative_clusters)

    def __len__(self):
        return self._end - self._start

    def __eq__(self, other):
        if not isinstance(other, GlyphRun):
            return NotImplemented
        return (
            self.segment == other.segment
            and list(self.glyphs) == list(other.glyphs)
            and list(self.positions) == list(other.positions)
            and list(self.advances) == list(other.advances)
            and list(self.clusters) == list(other.clusters)
        )

    def __repr__(self):
        return (f"GlyphRun(segment={self.segment!r}, glyphs={list(self.glyphs)!r}, "
                f"positions={list(self.positions)!r}, advances={list(self.advances)!r}, "
                f"clusters={list(self.clusters)!r})")
    
    def slice(self, start, end):
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
            source=self,
            start=self._start + start,
            end=self._start + end,
            relative_clusters=new_clusters_relative,
        )


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
            list: list of Paragraph instances.
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
            result.append(Paragraph(baseLevel, shapedSegmentList))
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
        positions = [(pos.x_offset, pos.y_offset) for pos in buf.glyph_positions]
        advances = [(pos.x_advance, pos.y_advance) for pos in buf.glyph_positions]

        return GlyphRun(
            segment=segment,
            glyphs=glyphs,
            positions=positions,
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