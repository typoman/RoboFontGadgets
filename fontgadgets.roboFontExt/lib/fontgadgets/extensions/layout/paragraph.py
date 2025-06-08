from fontgadgets.extensions.layout.segmenting import reorderedSegments, Segment
from fontgadgets.extensions.layout.shaper import (
    ShapedParagraph,
    ShapedSegment,
    GlyphRecord,
    GlyphLine,
)
import unicodedata2

"""
# Soft line break logic
- breakParagraphsUsingLineWidth takes the list of `ShapedParagraph` objects
  from `HBShaper.shape` and another argument, `lineWidth`. Its goal is to
  produce a final list of laid-out `GlyphLine` instances.
- In shaped segment RTL glyphs are reversed (visual order) as glyphs will be
  later rendered from left to right, no matter their direction.
- In each `GlyphLine`, the start `y=0`, assuming line spacing is done later in
  rendering.
- It will process one `ShapedParagraph` at a time in an outer loop. All state
  related to the current line (its width, its segments) is reset for each new
  paragraph.
- Inside the paragraph loop:
    - Iterate over segments and if its width is not exceeding the lineWidth
      add it to the `currentLineSegment`.
    - When adding a segment's `width` would exceed the `lineWidth`, break the
      exceeding segment into another segment, first part kept for this line,
      rest for next line (the first part and sceond part are reversed for RTL
      segment.)
    - This logic defines the break point:
        - If the segment is the only segment in the line: by breaking before
          the exceeding glyph. Glyph iterations should be reversed for RTL
          segment.
        - else: finding first break point from the "breakPoints" parameter of
          the segment. Iterate backward from the end of the segment to find
          the last valid break point that fits on the line. Break point
          iterations should be reversed for RTL segment.
    - This split will create two new, smaller `ShapedSegment` objects by
      slicing all the lists (`glyphs`, `positions`, `advances`, `clusters`).
      After slicing there is no changes to the x and y of positions, only the
      list is sliced.
    - Add the first part of the broken segment to the `currentLineSegment`  and keep
      the rest for the the next line `currentLineSegment`.
- To finalize a line, you take all the segments from `currentLineSegment` and
  perform the BiDi reordering on them using `reorderedSegments` and the
  paragraph's `baseLevel`. After reordering, you can iterate through the
  visually ordered segments, calculate the final absolute positions for each
  glyph, and create the `GlyphRecord`s for a new `GlyphLine`.
- After the loop over a paragraph's segments is finished, any segments
  remaining on the current line must also be finalized into a `GlyphLine`.
- The function returns a final list of `GlyphLine` instances, each containing
  a list of `GlyphRecord`s ready for rendering.
"""

def debug_decorator(func):
    def wrapper(*args, **kwargs):
        print(f">>> {func.__name__}({', '.join(map(repr, args))})")
        result = func(*args, **kwargs)
        print(repr(result))
        print()
        return result
    return wrapper


def _sliceShapedSegment(shapedSegment, startIndex, endIndex):
    segment = shapedSegment.segment
    segment = Segment(segment.text[startIndex:endIndex], segment.bidi_level, segment.start_index + startIndex)
    return ShapedSegment(
        segment=segment,
        glyphs=shapedSegment.glyphs[startIndex:endIndex],
        positions=shapedSegment.positions[startIndex:endIndex],
        advances=shapedSegment.advances[startIndex:endIndex],
        clusters=shapedSegment.clusters[startIndex:endIndex],
        width=sum(abs(adv[0]) for adv in shapedSegment.advances[startIndex:endIndex]),
    )


def _getBreakIndexInSegmentUsingSpaces(shapedSegment, availableWidth):
    space_char_indices = {
        i
        for i, char in enumerate(shapedSegment.segment.text)
        if unicodedata2.category(char) == "Zs"
    }
    if not space_char_indices:
        return None
    advances = shapedSegment.advances
    clusters = shapedSegment.clusters
    current_width = 0
    i_adv_cluster = list(enumerate(zip(advances, clusters)))
    isRTL = shapedSegment.segment.bidi_level == 1
    if isRTL:
        i_adv_cluster = reversed(i_adv_cluster)
    prev_i = None
    for i, (adv, cluster) in i_adv_cluster:
        if cluster in space_char_indices:
            if isRTL:
                prev_i = i
            else:
                prev_i = i + 1

        current_width += abs(adv[0])
        if current_width > availableWidth:
            return prev_i
    return None


def _getBreakIndexInSegmentByGlyphAdvance(shapedSegment, availableWidth):
    current_width = 0
    isRTL = shapedSegment.segment.bidi_level == 1
    i_adv = list(enumerate(shapedSegment.advances))
    if shapedSegment.segment.bidi_level == 1:
        i_adv = reversed(i_adv)
    for i, adv in i_adv:
        width_of_this_glyph = abs(adv[0])
        if current_width + width_of_this_glyph > availableWidth:
            return i + 1 if isRTL else i
        current_width += width_of_this_glyph
    return None


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
    return GlyphLine(grecords)


def _breakSegmentAtIndex(segment, index):
    if index >= len(segment.glyphs):
        # break at last glyph or more
        raise Exception("Internal logic error!")
    first = _sliceShapedSegment(segment, 0, index)
    second = _sliceShapedSegment(segment, index, len(segment.glyphs))
    return first, second


def breakParagraphsUsingLineWidth(paragraphs, lineWidth):
    glyphLines = []
    for paragraph in paragraphs:
        baseLevel = paragraph.baseLevel
        isRTL = baseLevel % 2 == 1
        remainingSegments = list(paragraph.segments)
        while remainingSegments:
            currentLineSegments = []
            addedSegmentsWidth = 0
            while remainingSegments:
                currentSegment = remainingSegments[0]
                if addedSegmentsWidth + currentSegment.width <= lineWidth:
                    addedSegmentsWidth += currentSegment.width
                    currentLineSegments.append(currentSegment)
                    remainingSegments.pop(0)
                else:
                    availableWidth = lineWidth - addedSegmentsWidth
                    breakIndex = _getBreakIndexInSegmentUsingSpaces(currentSegment, availableWidth)
                    if breakIndex is None:
                        if not currentLineSegments:
                            breakIndex = _getBreakIndexInSegmentByGlyphAdvance(currentSegment, availableWidth)
                        else:
                            break
                    if breakIndex:
                        currentSubSeg, nextLineSubSeg = _breakSegmentAtIndex(currentSegment, breakIndex)
                        if currentSegment.segment.bidi_level == 1:
                            currentSubSeg, nextLineSubSeg = (nextLineSubSeg, currentSubSeg)
                        if nextLineSubSeg:
                            remainingSegments[0] = nextLineSubSeg
                        else:
                            remainingSegments.pop(0)
                        currentLineSegments.append(currentSubSeg)
                    break
            if currentLineSegments:
                gline = _getGlyphLineFromSegmments(currentLineSegments, isRTL)
                glyphLines.append(gline)
    return glyphLines
