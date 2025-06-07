"""
Text segmentation for bidirectional text layout.

This module provides functionality to:
1. Segment text by script (Latin, Arabic, Hebrew, etc.)
2. Determine bidirectional embedding levels (for RTL/LTR text)
3. Reorder segments for proper display

The main use case is preparing text for rendering in mixed-script,
bidirectional contexts (e.g. Arabic/Latin combinations).

Key functions:
- textSegments(): Split text into script/bidi segments
- reorderedSegments(): Reorder segments for display
- detectScript(): Identify Unicode script for each character
- getBiDiInfo(): Get bidirectional algorithm metadata

"""
import itertools
from fontTools.unicodedata import script
from unicodedata2 import category

# Monkeypatch bidi to use unicodedata2
import unicodedata2
import bidi.algorithm


# based on drawbot-skia written by Just Van Rossum

bidi.algorithm.bidirectional = unicodedata2.bidirectional
bidi.algorithm.category = unicodedata2.category
bidi.algorithm.mirrored = unicodedata2.mirrored
from bidi.algorithm import (
    get_empty_storage,
    get_base_level,
    get_embedding_levels,
    explicit_embed_and_overrides,
    resolve_weak_types,
    resolve_neutral_types,
    resolve_implicit_levels,
    reorder_resolved_levels,
    PARAGRAPH_LEVELS,
)
from bidi.mirror import MIRRORED


UNKNOWN_SCRIPT = {"Zinh", "Zyyy", "Zxxx"}


def textSegments(txt):
    """
    Split text into segments with consistent script and bidirectional level.

    Args:
        txt: The input text string to segment.

    Returns:
        A tuple of:
        - List of segments, where each segment is a tuple of:
          (text, script_code, bidi_level, start_index)
        - The base bidi level (0 for LTR, 1 for RTL)

    >>> segments, base_level = textSegments("Hello العالم")
    >>> base_level
    0
    >>> segments
    [('Hello ', 'Latn', 0, 0), ('العالم', 'Arab', 1, 6)]
    """
    scripts = detectScript(txt)
    storage = getBiDiInfo(txt)

    levels = [None] * len(txt)
    for ch in storage["chars"]:
        levels[ch["index"]] = ch["level"]

    prevLevel = storage["base_level"]
    for i, level in enumerate(levels):
        if level is None:
            levels[i] = prevLevel
        else:
            prevLevel = level

    charInfo = list(zip(scripts, levels))

    runLenghts = []
    for value, sub in itertools.groupby(charInfo):
        runLenghts.append(len(list(sub)))

    segments = []
    index = 0
    for rl in runLenghts:
        nextIndex = index + rl
        segment = charInfo[index:nextIndex]
        runChars = txt[index:nextIndex]
        script, bidiLevel = segment[0]
        segments.append((runChars, script, bidiLevel, index))
        index = nextIndex
    return segments, storage["base_level"]


def reorderedSegments(segments, isRTL, isSegmentRTLFunc):
    """
    Reorder text segments for proper bidirectional display.

    Args:
        segments: List of text segments from textSegments(), where each segment is:
            (text, script_code, bidi_level, start_index)
        isRTL: Base paragraph direction (True for RTL, False for LTR)
        isSegmentRTLFunc: Function that takes a segment tuple and returns True if
                         the segment should be treated as RTL (typically checks if
                         bidi_level % 2 == 1)

    Returns:
        List of segments in visual order (left-to-right display order), with RTL
        segments in reverse order when needed.

    >>> # LTR base paragraph with mixed LTR/RTL segments.
    >>> # Based on test_reorderedSegments()
    >>> # Input text: " hello  أحدث  מוסיקה  hello "
    >>> segments = [
    ...     (' hello  ', 'Latn', 0, 0),
    ...     ('أحدث  ', 'Arab', 1, 8),
    ...     ('מוסיקה ', 'Hebr', 1, 14),
    ...     (' h', 'Hebr', 0, 20),
    ...     ('ello  ', 'Latn', 0, 22)
    ... ]
    >>> is_rtl_base = False
    >>> reordered = reorderedSegments(segments, is_rtl_base, lambda s: s[2] % 2 == 1)
    >>> # The two consecutive RTL segments ('Arab' and 'Hebr') are reordered.
    >>> reordered
    [(' hello  ', 'Latn', 0, 0), ('מוסיקה ', 'Hebr', 1, 14), ('أحدث  ', 'Arab', 1, 8), (' h', 'Hebr', 0, 20), ('ello  ', 'Latn', 0, 22)]

    >>> # RTL base paragraph with mixed RTL/LTR segments.
    >>> # Based on a case in test_textSegments()
    >>> # Input text: " أحدث  hello  أحدث "
    >>> segments = [
    ...     (' أحدث ', 'Arab', 1, 0),
    ...     (' hello', 'Latn', 2, 7),
    ...     ('  ', 'Latn', 1, 12),
    ...     ('أحدث ', 'Arab', 1, 14)
    ... ]
    >>> is_rtl_base = True
    >>> reordered = reorderedSegments(segments, is_rtl_base, lambda s: s[2] % 2 == 1)
    >>> # The entire sequence of segment groups is reversed for RTL display.
    >>> reordered
    [('أحدث ', 'Arab', 1, 14), ('  ', 'Latn', 1, 12), (' hello', 'Latn', 2, 7), (' أحدث ', 'Arab', 1, 0)]
    """
    reorderedSegments = []
    for value, sub in itertools.groupby(segments, key=isSegmentRTLFunc):
        if isRTL == value:
            reorderedSegments.extend(sub)
        else:
            reorderedSegments.extend(reversed(list(sub)))
    if isRTL:
        reorderedSegments.reverse()
    assert len(reorderedSegments) == len(segments)
    return reorderedSegments


def detectScript(txt):
    """Identify the Unicode script for each character in a string.

    Handles unknown/ambiguous characters by inheriting script from adjacent characters.
    Special cases:
    - Inherits script from previous character for unknown script codes (Zyyy, Zinh, Zxxx)
    - Treats mirrored closing punctuation (like ')') as having no script

    Args:
        txt: Input text string to analyze

    Returns:
        A list where each element is the script code (e.g. 'Latn', 'Arab', 'Hebr')
        for the corresponding character in the input string.

    >>> detectScript("Aل")
    ['Latn', 'Arab']
    """
    charScript = [script(c) for c in txt]

    for i, ch in enumerate(txt):
        scr = charScript[i]
        if scr in UNKNOWN_SCRIPT:
            if i:
                scr = charScript[i - 1]
            else:
                scr = None
            cat = category(ch)
            if ch in MIRRORED and cat == "Pe":
                scr = None
        charScript[i] = scr

    prev = None
    for i in range(len(txt) - 1, -1, -1):
        if charScript[i] is None:
            charScript[i] = prev
        else:
            prev = charScript[i]

    prev = "Zxxx"
    for i in range(len(txt)):
        if charScript[i] is None:
            charScript[i] = prev
        else:
            prev = charScript[i]

    assert None not in charScript

    return charScript


# JVR: copied from bidi/algorthm.py and modified to be more useful for us.


def getBiDiInfo(text, *, upper_is_rtl=False, base_dir=None, debug=False):
    """
    Analyze text using the Unicode Bidirectional Algorithm (UBA).

    Args:
        text: Input string to analyze
        upper_is_rtl: Treat uppercase as strong RTL (for debugging)
        base_dir: Override base direction ('L' or 'R')
        debug: Print algorithm steps to stderr

    Returns:
        Dict containing:
        - base_level: Paragraph embedding level (0=LTR, 1=RTL)
        - base_dir: Base direction ('L' or 'R')
        - chars: List of character dicts with:
            * ch: The character
            * level: Resolved bidi level
            * index: Original position

    >>> info = getBiDiInfo("Hello, العالم!")
    >>> info["base_level"]  # Returns 0 (LTR base direction)
    0
    """
    storage = get_empty_storage()

    if base_dir is None:
        base_level = get_base_level(text, upper_is_rtl)
    else:
        base_level = PARAGRAPH_LEVELS[base_dir]

    storage["base_level"] = base_level
    storage["base_dir"] = ("L", "R")[base_level]

    get_embedding_levels(text, storage, upper_is_rtl, debug)
    assert len(text) == len(storage["chars"])
    for index, (ch, chInfo) in enumerate(zip(text, storage["chars"])):
        assert ch == chInfo["ch"]
        chInfo["index"] = index

    explicit_embed_and_overrides(storage, debug)
    resolve_weak_types(storage, debug)
    resolve_neutral_types(storage, debug)
    resolve_implicit_levels(storage, debug)
    reorder_resolved_levels(storage, debug)

    return storage


if __name__ == "__main__":
    import doctest

    doctest.testmod()
