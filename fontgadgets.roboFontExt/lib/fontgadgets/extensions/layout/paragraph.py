from fontgadgets.extensions.layout.shaper import HBShaper
import unicodedata2


class GlyphRecord:
    """
    Represents a single glyph's position and spacing information after text shaping.

    Attributes:
        glyph: The glyph object, typically a `defcon.Glyph`.
        offset tuple[float, float]: The (x, y) offset of the glyph's origin
        relative to its initial position, often is non zero after mark positioning.
        advance tuple[float, float]: Indicates how farther the next glyph should be placed, often
        equals to glyph.width, if no kerning is applied.
    """
    __slots__ = ('glyph', 'offset', 'advance')

    def __init__(self, glyph, offset, advance):
        object.__setattr__(self, 'glyph', glyph)
        object.__setattr__(self, 'offset', tuple(offset))
        object.__setattr__(self, 'advance', tuple(advance))

    def __setattr__(self, name, value):
        raise AttributeError(f"Cannot modify attribute '{name}'. GlyphRecord objects are immutable.")

    def __repr__(self):
        return f"GlyphRecord(glyph={self.glyph!r}, offset={self.offset!r}, advance={self.advance!r})"


class GlyphLine:
    """
    Represents a single line of laid-out glyphs.

    Attributes:
        glyphRuns (tuple[GlyphRun]): The tuple of GlyphRun objects that
            make up this line.
        x (float): The horizontal offset of the line's starting point.
        y (float): The vertical offset of the line's starting point.
        width (float): The total width of all glyph runs in the line.
    """
    __slots__ = ('glyphRuns', '_x', '_y', '_glyphRecords', '_width')

    def __init__(self, glyphRuns, x=0, y=0):
        object.__setattr__(self, 'glyphRuns', tuple(glyphRuns))
        object.__setattr__(self, '_x', x)
        object.__setattr__(self, '_y', y)
        object.__setattr__(self, '_glyphRecords', None)
        object.__setattr__(self, '_width', None) # Initialize _width to None

    def _x_get(self):
        return self._x

    def _x_set(self, value):
        object.__setattr__(self, '_x', value)

    def _y_get(self):
        return self._y

    def _y_set(self, value):
        object.__setattr__(self, '_y', value)

    def _width_get(self):
        if self._width is None:
            object.__setattr__(self, '_width', sum(gr.width for gr in self.glyphRuns))
        return self._width

    x = property(_x_get, _x_set, None, "The horizontal offset of the line's starting point.")
    y = property(_y_get, _y_set, None, "The vertical offset of the line's starting point.")
    width = property(_width_get, None, None, "The total width of all glyph runs in the line.")

    def __setattr__(self, name, value):
       raise AttributeError("Only 'x' and 'y' attributes of GlyphLine can be changed.")

    def __repr__(self):
        # Access self.width to ensure it's calculated if not already
        return (f"GlyphLine(x={self.x}, y={self.y}, width={self.width}, glyphRuns={len(self.glyphRuns)} runs)")

    def _get_glyphRecords(self):
        if self._glyphRecords is None:
            records = []
            for glyphRun in self.glyphRuns:
                for glyphName, offset, advance in zip(glyphRun.glyphs,
                                                      glyphRun.offsets,
                                                      glyphRun.advances):
                    try:
                        glyph = glyphRun.font[glyphName]
                    except KeyError:
                        glyph = glyphRun.font._fallbackNotDef
                    records.append(GlyphRecord(glyph, offset, advance))
            object.__setattr__(self, '_glyphRecords', records)
        return self._glyphRecords

    glyphRecords = property(_get_glyphRecords, None, None, "A list of GlyphRecord objects for all glyphs in the line.")

class Paragraph:
    """Manages basic line break in text layout within a paragraph.

    Attributes:
        width (int, optional): Width of each line in the paragraph.
        lineHeight (int, optional): Height of each line in the paragraph.
        baseLevel (int): Paragraph's base bidi level (0=LTR, 1=RTL).
        glyphLines (list): List of GlyphLine objects representing the laid-out text.
    """

    def __init__(self, baseLevel, width=None, lineHeight=None):
        self._baseLevel = baseLevel
        self._width = width
        self._lineHeight = lineHeight
        self._glyphRuns = []
        self._glyphLines = []
        self._needs_layout = True

    def _lineWidth_get(self):
        return self._width

    def _lineWidth_set(self, value):
        self._needs_layout = True
        self._width = value

    lineWidth = property(
        _lineWidth_get, _lineWidth_set, None, "Width of each line in the paragraph"
    )

    def _lineHeight_get(self):
        return self._lineHeight

    def _lineHeight_set(self, value):
        self._lineHeight = value

    lineHeight = property(
        _lineHeight_get, _lineHeight_set, None, "Height of each line in the paragraph"
    )

    def _baseLevel_get(self):
        return self._baseLevel

    def _baseLevel_set(self, value):
        self._baseLevel = value

    baseLevel = property(
        _baseLevel_get, _baseLevel_set, None, "Paragraph's base bidi level (0=LTR, 1=RTL)"
    )

    def addTextFromFont(self, text, font, features=None, language=None, script=None, variations=None):
        """Adds text to the paragraph from a given font.

        Args:
            text (str): The text to add.
            font (defcon.Glyph): The font object to use for shaping.
            features (dict, optional): The font features. {feat_tag: False/True, ...}
            language (str, optional): The language.
            script (str, optional): The script.
            variations (dict, optional): The font variations. {axis_tag: value, ...}
        """
        self._needs_layout = True
        shaper = font._HBShaper
        glyphRunsForThisFont = shaper.shapeTextToGlyphRuns(text, self._baseLevel, features, language, script, variations)
        self._glyphRuns.extend(glyphRunsForThisFont)

    def calculateGlyphLines(self):
        """Calculates and updates the glyph lines based on current settings."""
        if not self._needs_layout and self._glyphLines:
            return
        self._glyphLines = []
        lines_of_glyph_runs = breakGlyphRunsUsingLineWidth(self._glyphRuns,
                                                           self._width)
        for line_glyph_runs in lines_of_glyph_runs:
            glyph_line = GlyphLine(line_glyph_runs, x=0, y=0)
            self._glyphLines.append(glyph_line)
        self._needs_layout = False

    @property
    def glyphLines(self):
        """Returns the list of GlyphLine objects, calculating them if needed."""
        self.calculateGlyphLines()
        return self._glyphLines

def _getBreakIndexInGlyphRunUsingSpaces(glyphRun, availableWidth):
    if len(glyphRun) == 1:
        return
    space_char_indices = {
        i
        for i, char in enumerate(glyphRun.segment.text)
        if unicodedata2.category(char) == "Zs"
    }
    if not space_char_indices:
        return
    advances = list(glyphRun.advances)
    clusters = list(glyphRun.clusters)
    currentWidth = 0
    i_adv_cluster = list(enumerate(zip(advances, clusters)))
    isRTL = glyphRun.segment.bidi_level == 1
    if isRTL:
        i_adv_cluster = reversed(i_adv_cluster)
    prev_i = None
    for i, (adv, cluster) in i_adv_cluster:
        currentWidth += abs(adv[0])
        if currentWidth > availableWidth:
            if not prev_i:
                return
            if isRTL:
                return prev_i
            return prev_i + 1
        if cluster in space_char_indices:
            prev_i = i


def _getBreakIndexInGlyphRunByGlyphAdvance(glyphRun, availableWidth):
    if len(glyphRun) == 1:
        return
    currentWidth = 0
    isRTL = glyphRun.segment.bidi_level == 1
    i_adv = list(enumerate(glyphRun.advances))
    if isRTL:
        i_adv = reversed(i_adv)
    prev_i = None
    for i, adv in i_adv:
        gWidth = abs(adv[0])
        currentWidth += gWidth
        if currentWidth > availableWidth:
            if not prev_i:
                return
            if isRTL:
                return prev_i
            return prev_i + 1
        prev_i = i


def _breakGlyphRunAtIndex(glyphRun, index):
    if index == 0 or index >= len(glyphRun):
        raise Exception(f"Internal logic error, can't break the glyph run at index: {index}")
    first = glyphRun.slice(0, index)
    second = glyphRun.slice(index, len(glyphRun))
    return first, second


def breakGlyphRunsUsingLineWidth(glyphRuns, lineWidth):
    # The primary goal of this function is to take a list of glyphRun tuples
    # and a target line width, and from them, produce a final list of laid-out
    # glyph lines ready for rendering.
    #
    # The process iterates through the provided glyph runs to arrange them into
    # lines. All state related to the current line being built, such as its
    # accumulated width and the glyph runs it contains, is reset for each new line.
    # All the glyphs are in visual order (left-to-right). This makes the operation
    # of line breaking more complex, as it requires finding glyph-to-character
    # mapping when a glyph run is broken.
    #
    # Inside the main loop, the logic builds one line at a time:
    #
    # - It iterates over the remaining glyph runs. If a glyph run fits
    #   completely within the remaining available width of the current line, it
    #   is added to a list of glyph runs for that line, and its width is
    #   subtracted from the available space.
    # - When the next glyph run is too wide to fit, a decision must be made on
    #   where to break the glyph run.
    #     - The logic first attempts to find a suitable break point within the
    #       oversized glyph run by looking for space characters. It identifies
    #       the last space that allows the preceding text to fit on the current
    #       line.
    #     - If no space character provides a valid break point, and the current
    #       line is still empty (meaning the oversized glyph run is the first
    #       item being considered for this line), the logic falls back to a
    #       different strategy. It breaks the glyph run by fitting as many
    #       individual glyphs as possible, one by one, until their combined
    #       advance widths exceed the available line width.
    #     - If, however, no space break point is found and the line *already
    #       contains other glyph runs*, the oversized glyph run is not split.
    #       Instead, the current line is considered complete, and the entire
    #       oversized glyph run is moved to the next line.
    # - When a glyph run is broken, it is split into two new, smaller
    #   glyph runs.
    #     - This split involves slicing all the internal data lists: the glyphs,
    #       their positions, their advance widths, and their cluster mapping.
    #     - The text for the new, smaller glyph runs is also recalculated by
    #       using the cluster information to slice the original text correctly.
    #       The cluster values themselves are then adjusted to be relative to
    #       the start of their new, smaller text snippet.
    #     - For right-to-left glyph runs (bidi_level == 1), the two new
    #       sub-glyph runs are swapped. This ensures that the part of the
    #       original text that appears visually first (which is the latter part
    #       of the original logical text) is placed on the current line, while
    #       the beginning part is carried over to the next.
    # - The part of the glyph run that fits is added to the current line, and
    #   the remaining part is kept to be the first glyph run processed for the
    #   subsequent line.
    #
    # After the loop over all glyph runs is complete, any glyph runs
    # that were collected for the last line are also finalized. The final output
    # is the complete list of all the generated glyph lines.


    glyphLines = []
    remainingGlyphRuns = list(reversed(glyphRuns))
 
    availableWidth = lineWidth

    while remainingGlyphRuns:
        # line loop
        currentGlyphRuns = []
        addedGlyphRunsWidth = 0
        while remainingGlyphRuns:
            # glyph run break loop
            currentGlyphRun = remainingGlyphRuns.pop()
            if addedGlyphRunsWidth + currentGlyphRun.width <= lineWidth:
                addedGlyphRunsWidth += currentGlyphRun.width
                currentGlyphRuns.append(currentGlyphRun)
            else:
                availableWidth = lineWidth - addedGlyphRunsWidth
                breakIndex = _getBreakIndexInGlyphRunUsingSpaces(currentGlyphRun, availableWidth)
                if breakIndex is None:
                    if not currentGlyphRuns:
                        breakIndex = _getBreakIndexInGlyphRunByGlyphAdvance(currentGlyphRun, availableWidth)
                    else:
                        remainingGlyphRuns.append(currentGlyphRun)
                        break
                if breakIndex is not None:
                    if breakIndex == 0:
                        breakIndex = 1
                    currentSubGR, nextLineSubGR = _breakGlyphRunAtIndex(currentGlyphRun, breakIndex)
                    if currentGlyphRun.segment.bidi_level == 1:
                        currentSubGR, nextLineSubGR = (nextLineSubGR, currentSubGR)
                    if nextLineSubGR.glyphs:
                        remainingGlyphRuns.append(nextLineSubGR)
                    currentGlyphRuns.append(currentSubGR)
                    break
                else:
                    # last glyph ia wider than line width
                    return glyphLines
        if currentGlyphRuns:
            glyphLines.append(currentGlyphRuns)
    return glyphLines

