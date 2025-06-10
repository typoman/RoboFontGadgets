from fontgadgets.extensions.layout.segmenting import reorderedSegments, Segment
from fontgadgets.extensions.layout.shaper import (
    ShapedParagraph,
    ShapedSegment,
    GlyphRecord,
    GlyphLine,
)
import unicodedata2

def _sliceShapedSegment(shapedSegment, startIndex, endIndex):
    newGlyphs = shapedSegment.glyphs[startIndex:endIndex]
    newClustersForSlice = shapedSegment.clusters[startIndex:endIndex]
    newAdvances = shapedSegment.advances[startIndex:endIndex]
    newPositions = shapedSegment.positions[startIndex:endIndex]
    if not newClustersForSlice:
        newText = ""
        newSegmentStartIndex = shapedSegment.segment.start_index
        newClustersRelative = []
    else:
        originalSegmentText = shapedSegment.segment.text
        minCharIndex = min(newClustersForSlice)
        maxCharIndex = max(newClustersForSlice)
        newText = originalSegmentText[minCharIndex : maxCharIndex + 1]
        newClustersRelative = [c - minCharIndex for c in newClustersForSlice]
        newSegmentStartIndex = shapedSegment.segment.start_index + minCharIndex
    segment = Segment(newText, shapedSegment.segment.bidi_level, newSegmentStartIndex)

    return ShapedSegment(
        segment=segment,
        glyphs=newGlyphs,
        positions=newPositions,
        advances=newAdvances,
        clusters=newClustersRelative,
        width=sum(abs(adv[0]) for adv in newAdvances),
    )


def _getBreakIndexInSegmentUsingSpaces(shapedSegment, availableWidth):
    if len(shapedSegment.advances) == 1:
        return
    space_char_indices = {
        i
        for i, char in enumerate(shapedSegment.segment.text)
        if unicodedata2.category(char) == "Zs"
    }
    if not space_char_indices:
        return
    advances = shapedSegment.advances
    clusters = shapedSegment.clusters
    current_width = 0
    i_adv_cluster = list(enumerate(zip(advances, clusters)))
    isRTL = shapedSegment.segment.bidi_level == 1
    if isRTL:
        i_adv_cluster = reversed(i_adv_cluster)
    prev_i = None
    for i, (adv, cluster) in i_adv_cluster:
        current_width += abs(adv[0])
        if current_width > availableWidth:
            if not prev_i:
                return
            if isRTL:
                return prev_i
            return prev_i + 1
        if cluster in space_char_indices:
            prev_i = i


def _getBreakIndexInSegmentByGlyphAdvance(shapedSegment, availableWidth):
    if len(shapedSegment.advances) == 1:
        return
    currentWidth = 0
    isRTL = shapedSegment.segment.bidi_level == 1
    i_adv = list(enumerate(shapedSegment.advances))
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


def _reorderShapedSegments(glyphRuns, paragraphIsRTL):
    originalSegments = [shaped_seg.segment for shaped_seg in glyphRuns]
    isSegmentRTL = lambda s: s.bidi_level % 2 == 1
    visuallyOrderedOriginalSegments = reorderedSegments(originalSegments, paragraphIsRTL, isSegmentRTL)
    segmentMap = {id(shaped_seg.segment): shaped_seg for shaped_seg in glyphRuns}
    visuallyOrderedSegments = [segmentMap[id(orig_seg)] for orig_seg in visuallyOrderedOriginalSegments]
    return visuallyOrderedSegments


def _getGlyphLineFromSegmments(glyphRuns, isRTL):
    segmentsForThisLine = _reorderShapedSegments(glyphRuns, isRTL)
    grecords = []
    currentX = 0
    for segment in segmentsForThisLine:
        for glyph, (dx, dy), (ax, ay) in zip(
            segment.glyphs, segment.positions, segment.advances
        ):
            absX = currentX + dx
            absY = dy
            grecords.append(GlyphRecord(glyph, (absX, absY)))
            currentX += ax
    return GlyphLine(grecords, glyphRuns)


def _breakSegmentAtIndex(segment, index):
    if index == 0 or index >= len(segment.glyphs):
        # break at first/last glyph or more, this is here to prevent infinite loop
        raise Exception(f"Internal logic error, can't break the glyph run at index: {index}")
    first = _sliceShapedSegment(segment, 0, index)
    second = _sliceShapedSegment(segment, index, len(segment.glyphs))
    return first, second


def breakParagraphsUsingLineWidth(paragraphs, lineWidth):
    """
    The primary goal of this function is to take a list of shaped paragraphs
    and a target line width, and from them, produce a final list of laid-out
    glyph lines ready for rendering.

    For each paragraph, the process begins by identifying its base direction
    (left-to-right or right-to-left) and then iterates through its shaped segments
    to arrange them into lines. All state related to the current line being built,
    such as its accumulated width and the segments it contains, is reset for each
    new paragraph. All the shaped glyphs are in visual order which is left to
    right. This makes the operation of line break more complex, as I need to find
    glyph to char mapping when I break the segmemt.

    Inside the main loop that processes a single paragraph, the logic builds one
    line at a time:

    - It iterates over the paragraph's segments. If a segment fits completely
      within the remaining available width of the current line, it is added to a
      list of segments for that line, and its width is subtracted from the
      available space.
    - When the next segment is too wide to fit, a decision must be made on where
      to break the segment.
        - The logic first attempts to find a suitable break point within the
          oversized segment by looking for space characters. It identifies the
          last space that allows the preceding text to fit on the current line.
          For right-to-left segments, this search is performed in reverse.
        - If no space character provides a valid break point, and the current line
          is still empty, the logic falls back to a different strategy. It breaks
          the segment by fitting as many individual glyphs as possible, one by
          one, until their combined advance widths exceed the available line
          width. This process is also reversed for right-to-left segments.
        - If, however, no space break point is found and the line *already
          contains other segments*, the oversized segment is not split. Instead,
          the current line is considered complete, and the entire oversized
          segment is moved to the next line.
    - When a segment is broken, it is split into two new, smaller shaped segments.
        - This split involves slicing all the internal data lists: the glyphs,
          their positions, their advance widths, and their cluster mapping.
        - The text for the new, smaller segments is also recalculated by using the
          cluster information to slice the original text correctly. The cluster
          values themselves are then adjusted to be relative to the start of their
          new, smaller text snippet.
        - For right-to-left segments, the two new sub-segments is swapped. This
          ensures that the latter part of the original text (which appears first
          visually) is placed on the current line, while the beginning part is
          carried over to the next.
    - The part of the segment that fits is added to the current line, and the
      remaining part is kept to be the first segment processed for the subsequent
      line.

    To finalize a line, all the collected segments are processed.

    - First, they undergo a bidirectional reordering to place them in their
      correct visual sequence based on the paragraph's base direction.
    - Then, the logic iterates through the visually-ordered segments. It
      calculates the final, absolute X position for each glyph by starting at 0
      and accumulating the advance width of each preceding glyph on the line. The
      absolute Y position is taken directly from the glyph's existing position
      data.
    - These final coordinates are used to create glyph records, which are then
      grouped into a single glyph line.

    After the loop over a paragraph's segments is complete, any segments that were
    collected for the last line are also finalized in the same manner. The final
    output is the complete list of all the generated glyph lines.
    """
    glyphLines = []
    for paragraph in paragraphs:
        baseLevel = paragraph.baseLevel
        isRTL = baseLevel % 2 == 1
        remainingSegments = list(reversed(paragraph.segments))
        while remainingSegments:
            currentLineSegments = []
            addedSegmentsWidth = 0
            while remainingSegments:
                currentSegment = remainingSegments.pop()
                if addedSegmentsWidth + currentSegment.width <= lineWidth:
                    addedSegmentsWidth += currentSegment.width
                    currentLineSegments.append(currentSegment)
                else:
                    availableWidth = lineWidth - addedSegmentsWidth
                    breakIndex = _getBreakIndexInSegmentUsingSpaces(currentSegment, availableWidth)
                    if breakIndex is None:
                        if not currentLineSegments:
                            breakIndex = _getBreakIndexInSegmentByGlyphAdvance(currentSegment, availableWidth)
                        else:
                            # line has content, so the entire segment moves to the next line.
                            # add it back to the list to be processed next.
                            remainingSegments.append(currentSegment)
                            break  # finalize the current line
                    if breakIndex is not None:
                        # the segment needs to be split.
                        if breakIndex == 0:
                            breakIndex = 1  # at least one glyph is taken for this line
                        currentSubSeg, nextLineSubSeg = _breakSegmentAtIndex(currentSegment, breakIndex)
                        if currentSegment.segment.bidi_level == 1:
                            currentSubSeg, nextLineSubSeg = (nextLineSubSeg, currentSubSeg)
                        if nextLineSubSeg.glyphs:
                            remainingSegments.append(nextLineSubSeg)
                        currentLineSegments.append(currentSubSeg)
                        break
                    else:
                        # the first glyph too wide fit in the line
                        return glyphLines
            if currentLineSegments:
                gline = _getGlyphLineFromSegmments(currentLineSegments, isRTL)
                glyphLines.append(gline)
    return glyphLines