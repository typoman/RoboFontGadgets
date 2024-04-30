from fontgadgets.decorators import *
from fontTools.unicodedata import category as getUniCategory
from fontTools import unicodedata
from fontTools.unicodedata import script_name

RTL_BIDI_TYPES = {"R", "AL"}
LTR_BIDI_TYPES = {"L", "AN", "EN"}

@font_property
def unicodeDirection(glyph):
    """
    Returns 'rtl' or 'ltr' based on the unicode values. Returns None if the
    directions cannot be determined.
    """
    if glyph.unicodes:
        uv = glyph.unicodes[0]
    elif glyph.pseudoUnicodes:
        uv = glyph.pseudoUnicodes[0]
    else:
        return
    char = chr(uv)
    bidiType = unicodedata.bidirectional(char)
    if bidiType in RTL_BIDI_TYPES:
        return "rtl"
    elif bidiType in LTR_BIDI_TYPES:
        return "ltr"


@font_method
def glyphsUnicodeDirection(font, glyphSet):
    """
    glyphSet: a list of glyph names
    Returns 'rtl' or 'ltr' based on the unicode values.
    """
    direction = set([font[g].unicodeDirection for g in glyphSet])
    if len(direction) == 1:
        return direction.pop()


@font_property
def scripts(glyph):
    """
    Returns the name of scripts (writing systems) this glyph is associated with.
    This is interpreted from the unicodes or pseudoUnicodes.
    """
    return tuple(script_name(tag) for tag in glyph.scriptTags)


@font_property
def scriptTags(glyph):
    result = set()
    for uv in glyph.pseudoUnicodes:
        result.update(script_extension(uv))
    return tuple(sorted(result))


# Based on: http://www.unicode.org/Public/UCD/latest/ucd/PropertyValueAliases.txt
UNICODE_GENERAL_CATEGORIES = {
    "Lu": "Uppercase Letter",
    "Ll": "Lowercase Letter",
    "Lt": "Digraphic Character",
    "Lm": "Modifier Letter",
    "Lo": "Letter/Syllable/Ideograph",
    "Mn": "Nonspacing Combining Mark",  # zero advance width
    "Mc": "Spacing Combining Mark",  # positive advance width
    "Me": "Enclosing Combining Mark",
    "Nd": "Decimal Digit",
    "Nl": "Letterlike Numeric Character",
    "No": "Numeric Character",
    "Pc": "Connecting Punctuation Mark",
    "Pd": "Dash/Hyphen Punctuation",
    "Ps": "Opening Punctuation Mark",  # of a pair
    "Pe": "Closing Punctuation Mark",  # of a pair
    "Pi": "Initial Quotation Mark",
    "Pf": "Final Quotation Mark",
    "Po": "Punctuation Mark",  # of other type
    "Sm": "Math Symbol",
    "Sc": "Currency Sign",
    "Sk": "Non-Letter Modifier Symbol",
    "So": "Symbol",  # of other type
    "Zs": "Space Character",  # of various non-zero widths
    "Zl": "Line Separator",  # of various non-zero widths
    "Zp": "Paragraph Separator",
    "Cc": "Control Code",
    "Cf": "Format Control Character",
    "Cs": "Surrogate Code Point",
    "Co": "Private-Use Character",
    "Cn": "Reserved Unassigned Code Point/Non-Character",
}


@font_property
def unicodeCategory(glyph):
    """
    Returns the unicode category of the glyph. If a glyph doesn't have unicode
    (s) it will be intrepreted from the substituions in the features or the
    composites.
    """
    if glyph.pseudoUnicodes:
        return UNICODE_GENERAL_CATEGORIES[getUniCategory(chr(glyph.pseudoUnicodes[0]))]

@font_method
def unicodeDirectionForGlyphNames(font, glyphNames):
    """
    Reutrns the direction of given glyph names. The glyphset should be an iterable
    sequence of glyph names. Returns either "ltr" or "rtl". If the directioon of glyphs
    is both, then None is returned.
    """
    direction = set([font[g].unicodeDirection for g in glyphNames])
    if len(direction) == 1:
        return direction.pop()
