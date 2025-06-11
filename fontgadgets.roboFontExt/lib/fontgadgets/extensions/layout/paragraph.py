from fontgadgets.extensions.layout.segmenting import reorderedSegments, Segment
from fontgadgets.extensions.layout.shaper import (
    Paragraph,
    GlyphRun,
    GlyphRecord,
    GlyphLine,
)
import unicodedata2


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


def _reorderGlyphRuns(glyphRuns, paragraphIsRTL):
    originalGlyphRuns = [gr.segment for gr in glyphRuns]
    isRTL = lambda s: s.bidi_level % 2 == 1
    visuallyOrderedOriginalGlyphRuns = reorderedSegments(originalGlyphRuns, paragraphIsRTL, isRTL)
    grMap = {id(gr.segment): gr for gr in glyphRuns}
    visuallyOrderedGlyphRuns = [grMap[id(orig_seg)] for orig_seg in visuallyOrderedOriginalGlyphRuns]
    return visuallyOrderedGlyphRuns


def _getGlyphLineFromGlyphRuns(glyphRuns, isRTL):
    glyphRunsForThisLine = _reorderGlyphRuns(glyphRuns, isRTL)
    grecords = []
    currentX = 0
    currentY = 0
    for glyphRun in glyphRunsForThisLine:
        for glyph, (dx, dy), (ax, ay) in zip(
            glyphRun.glyphs, glyphRun.positions, glyphRun.advances
        ):
            absX = currentX + dx
            absY = currentY + dy
            gr = GlyphRecord(glyph, (absX, absY))
            grecords.append(gr)
            currentX += ax
            currentY += ay
    return GlyphLine(grecords, glyphRuns)


def _breakGlyphRunAtIndex(glyphRun, index):
    if index == 0 or index >= len(glyphRun):
        raise Exception(f"Internal logic error, can't break the glyph run at index: {index}")
    first = glyphRun.slice(0, index)
    second = glyphRun.slice(index, len(glyphRun))
    return first, second


def breakParagraphsUsingLineWidth(paragraphs, lineWidth):
    """
    The primary goal of this function is to take a list of paragraphs and a
    target line width, and from them, produce a final list of laid-out glyph
    lines ready for rendering.

    For each paragraph, the process begins by identifying its base direction
    (left-to-right or right-to-left) and then iterates through its 
    glyph runs to arrange them into lines. All state related to the current
    line being built, such as its accumulated width and the glyph runs it
    contains, is reset for each new paragraph. All the glyphs are in
    visual order which is left to right. This makes the operation of line
    break more complex, as I need to find glyph to char mapping when I break
    the segmemt.

    Inside the main loop that processes a single paragraph, the logic builds
    one line at a time:

    - It iterates over the paragraph's glyph runs. If a glyph run fits
      completely within the remaining available width of the current line, it
      is added to a list of glyph runs for that line, and its width is
      subtracted from the available space.
    - When the next glyph run is too wide to fit, a decision must be made on
      where to break the glyph run.
        - The logic first attempts to find a suitable break point within the
          oversized glyph run by looking for space characters. It identifies
          the last space that allows the preceding text to fit on the current
          line. For right-to-left glyph runs, this search is performed in
          reverse.
        - If no space character provides a valid break point, and the current
          line is still empty, the logic falls back to a different strategy.
          It breaks the glyph run by fitting as many individual glyphs as
          possible, one by one, until their combined advance widths exceed the
          available line width. This process is also reversed for
          right-to-left glyph runs.
        - If, however, no space break point is found and the line *already
          contains other glyph runs*, the oversized glyph run is not split.
          Instead, the current line is considered complete, and the entire
          oversized glyph run is moved to the next line.
    - When a glyph run is broken, it is split into two new, smaller 
      glyph runs.
        - This split involves slicing all the internal data lists: the glyphs,
          their positions, their advance widths, and their cluster mapping.
        - The text for the new, smaller glyph runs is also recalculated by
          using the cluster information to slice the original text correctly.
          The cluster values themselves are then adjusted to be relative to
          the start of their new, smaller text snippet.
        - For right-to-left glyph runs, the two new sub-glyph runs is swapped.
          This ensures that the latter part of the original text (which
          appears first visually) is placed on the current line, while the
          beginning part is carried over to the next.
    - The part of the glyph run that fits is added to the current line, and
      the remaining part is kept to be the first glyph run processed for the
      subsequent line.

    To finalize a line, all the collected glyph runs are processed.

    - First, they undergo a bidirectional reordering to place them in their
      correct visual sequence based on the paragraph's base direction.
    - Then, the logic iterates through the visually-ordered glyph runs. It
      calculates the final, absolute X position for each glyph by starting at
      0 and accumulating the advance width of each preceding glyph on the
      line. The absolute Y position is taken directly from the glyph's
      existing position data.
    - These final coordinates are used to create glyph records, which are then
      grouped into a single glyph line.

    After the loop over a paragraph's glyph runs is complete, any glyph runs
    that were collected for the last line are also finalized in the same
    manner. The final output is the complete list of all the generated glyph
    lines.
    """
    glyphLines = []
    for paragraph in paragraphs:
        baseLevel = paragraph.baseLevel
        isRTL = baseLevel % 2 == 1
        remainingGlyphRuns = list(reversed(paragraph.glyphRuns))
        while remainingGlyphRuns:
            currentGlyphRuns = []
            addedGlyphRunsWidth = 0
            while remainingGlyphRuns:
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
                        return glyphLines
            if currentGlyphRuns:
                gline = _getGlyphLineFromGlyphRuns(currentGlyphRuns, isRTL)
                glyphLines.append(gline)
    return glyphLines

