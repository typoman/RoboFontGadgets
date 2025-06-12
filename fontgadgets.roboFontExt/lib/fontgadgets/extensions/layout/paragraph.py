from fontgadgets.extensions.layout.shaper import HBShaper
import unicodedata2

"""
The primary goal of the break line function is to take a list of baseLevel,
glyphRun tuples and a target line width, and from them, produce a final list of
laid-out glyph lines ready for rendering.

For each paragraph, the process begins by identifying its base direction
(left-to-right or right-to-left) and then iterates through its glyph runs to
arrange them into lines. All state related to the current line being built,
such as its accumulated width and the glyph runs it contains, is reset for each
new paragraph. All the glyphs are in visual order which is left to right. This
makes the operation of line break more complex, as I need to find glyph to char
mapping when I break the glyph run.

Inside the main loop that processes a single paragraph, the logic builds one
line at a time:

- It iterates over the paragraph's glyph runs. If a glyph run fits completely
  within the remaining available width of the current line, it is added to a
  list of glyph runs for that line, and its width is subtracted from the
  available space.
- When the next glyph run is too wide to fit, a decision must be made on where
  to break the glyph run.
    - The logic first attempts to find a suitable break point within the
      oversized glyph run by looking for space characters. It identifies the
      last space that allows the preceding text to fit on the current line. For
      right-to-left glyph runs, this search is performed in reverse.
    - If no space character provides a valid break point, and the current line
      is still empty, the logic falls back to a different strategy. It breaks
      the glyph run by fitting as many individual glyphs as possible, one by
      one, until their combined advance widths exceed the available line width.
      This process is also reversed for right-to-left glyph runs.
    - If, however, no space break point is found and the line *already contains
      other glyph runs*, the oversized glyph run is not split. Instead, the
      current line is considered complete, and the entire oversized glyph run
      is moved to the next line.
- When a glyph run is broken, it is split into two new, smaller glyph runs.
    - This split involves slicing all the internal data lists: the glyphs,
      their positions, their advance widths, and their cluster mapping.
    - The text for the new, smaller glyph runs is also recalculated by using
      the cluster information to slice the original text correctly. The cluster
      values themselves are then adjusted to be relative to the start of their
      new, smaller text snippet.
    - For right-to-left glyph runs, the two new sub-glyph runs is swapped. This
      ensures that the latter part of the original text (which appears first
      visually) is placed on the current line, while the beginning part is
      carried over to the next.
- The part of the glyph run that fits is added to the current line, and the
  remaining part is kept to be the first glyph run processed for the subsequent
  line.

To finalize a line, all the collected glyph runs are processed.

- First, they undergo a bidirectional reordering to place them in their correct
  visual sequence based on the paragraph's base direction.
- Then, the logic iterates through the visually-ordered glyph runs. It
  calculates the final, absolute X position for each glyph by starting at
    0 and accumulating the advance width of each preceding glyph on the line.
    The absolute Y position is taken directly from the glyph's existing
    position data.
- These final coordinates are used to create glyph records, which are then
  grouped into a single glyph line.

After the loop over a paragraph's glyph runs is complete, any glyph runs that
were collected for the last line are also finalized in the same manner. The
final output is the complete list of all the generated glyph lines.

todo:

- Introduce a Paragraph class with a `addTextFromFont` method and a `lineWidth`
  and `lineHeight` attribute. The paragraph should cache the shaping per each
  call for `addTextFromFont` depending on the font cache for the shaper, and if
  the line width changes, it can calucalte the absolute glyph postions again on
  demand.
    - Make the glyph positions relative all the time, add a method for getting
      the absolute postions on demand.
    - glyph postions don't change based on the lineHeight, the lines should
      have a x, y offset attribute for the alignment and lineHeight.
    - Also contatins glyphLines instances.
    - each glyphLine should hava a reference to the glyphRun class too
    - final glyph records inside the glyphLine, should have also refrences to
      the actual glyph objects, making it possible to obtain the outline.
"""


class GlyphRecord:
    """
    Represents a single glyph with its absolute position.

    Attributes:
        glyph: The glyph object
        position (tuple[float, float]): The absolute (x, y) coordinate of the glyph's origin.
    """
    __slots__ = ('glyph', 'position', 'glyphRun')

    def __init__(self, glyph, position, glyphRun):
        object.__setattr__(self, 'glyph', glyph)
        object.__setattr__(self, 'position', tuple(position))
        object.__setattr__(self, 'glyphRun', tuple(glyphRun))

    def __setattr__(self, name, value):
        raise AttributeError(f"Cannot modify attribute '{name}'. GlyphRecord objects are immutable.")

    def __repr__(self):
        return f"GlyphRecord(glyph={self.glyph!r}, position={self.position!r}, glyphRun={self.glyphRun!r})"


class GlyphLine:
    """
    Represents a single line of laid-out glyphs.

    Attributes:
        records (tuple[GlyphRecord]): A tuple of GlyphRecord objects, each
            representing a glyph with its absolute position on the line.
        glyphRuns (tuple[GlyphRun]): The tuple of GlyphRun objects that
            make up this line.
        x (float): The horizontal offset of the line's starting point.
        y (float): The vertical offset of the line's starting point.
    """
    __slots__ = ('records', '_x', '_y')

    def __init__(self, records, x=0, y=0):
        object.__setattr__(self, 'records', tuple(records))
        object.__setattr__(self, '_x', x)
        object.__setattr__(self, '_y', y)

    def _x_get(self):
        return self._x

    def _x_set(self, value):
        object.__setattr__(self, '_x', value)

    def _y_get(self):
        return self._y

    def _y_set(self, value):
        object.__setattr__(self, '_y', value)

    x = property(_x_get, _x_set, None, "The horizontal offset of the line's starting point.")
    y = property(_y_get, _y_set, None, "The vertical offset of the line's starting point.")

    def __setattr__(self, name, value):
        # This will only be called for attributes not handled by properties,
        # i.e., 'records' and 'glyphRuns'.
        raise AttributeError("Only 'x' and 'y' attributes of GlyphLine can be changed.")

    def __repr__(self):
        return (f"GlyphLine(x={self.x}, y={self.y}, records={len(self.records)} records)")

class Paragraph:
    """
    A paragraph class that manages text layout with configurable line width and height.
    """

    def __init__(self, baseLevel, lineWidth=None, lineHeight=None):
        self._baseLevel = baseLevel
        self._lineWidth = lineWidth
        self._lineHeight = lineHeight
        self._font_glyphRuns = []
        self._availableWidth = lineWidth # remained width after applying line braaks

    def _lineWidth_get(self):
        return self._lineWidth

    def _lineWidth_set(self, value):
        self._lineWidth = value

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

    def _glyphRuns_get(self):
        return self._font_glyphRuns

    def _glyphRuns_set(self, glyphRuns):
        self._font_glyphRuns = glyphRuns
    
    glyphRuns = property(
        _glyphRuns_get, _glyphRuns_set, None, "List of GlyphRun objects in the paragraph"
    )

    def addTextFromFont(self, text, font, features=None, language=None, script=None, variations=None):
        shaper = HBShaper(font)
        glyphRunsForThisFont = shaper.shapeTextToGlyphRuns(text, self._baseLevel, features, language, script, variations)
        self._font_glyphRuns.append((font, glyphRunsForThisFont))

    def _breakGlyphRuns(self):
        self._lines = breakGlyphRunsUsingLineWidth(self._font_glyphRuns, self._lineWidth, self._availableWidth)
        return self._lines

    def _makeGlyphLineWithAbsolutePositionsFromGlyphRuns(self):
        # this will take the glyph runs and make glyph records with abs postions
        result = []
        for l in self._lines:
            grecords = []
            currentX = 0
            currentY = 0
            for font, glyphRun in l:
                for glyphName, (dx, dy), (ax, ay) in zip(glyphRun.glyphs,
                                                         glyphRun.positions,
                                                         glyphRun.advances):
                    glyph = font[glyphName]
                    absY = currentY + dy
                    absX = currentX + dx
                    gr = GlyphRecord(glyph, (absX, absY))
                    grecords.append(gr)
                    currentX += ax
                    currentY += ay
            result.append(GlyphLine(grecords))
        return result

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
    lines = []
    remainingGlyphRuns = list(reversed(glyphRuns))
    availableWidth = lineWidth

    while remainingGlyphRuns:
        # line loop
        currentLineGlyphRuns = []
        while remainingGlyphRuns:
            # glyph run break loop
            currentGlyphRun = remainingGlyphRuns.pop()
            if currentGlyphRun.width <= availableWidth:
                availableWidth -= currentGlyphRun.width
                currentLineGlyphRuns.append(currentGlyphRun)
            else:
                # break glyph run and finish the line, add remainder of glyph
                # run for next line
                breakIndex = _getBreakIndexInGlyphRunUsingSpaces(currentGlyphRun, availableWidth)
                if breakIndex is None:
                    if not currentLineGlyphRuns:
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
                    currentLineGlyphRuns.append(currentSubGR)
                    break
                else:
                    # can't fit the first glyph, return what we have
                    return lines
        if currentLineGlyphRuns:
            lines.append(currentLineGlyphRuns)
        availableWidth = lineWidth
    return lines

