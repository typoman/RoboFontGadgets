from fontgadgets.decorators import *
import fontgadgets.extensions.features
from fontTools import unicodedata
from ufo2ft.featureWriters.kernFeatureWriter2 import (
    unicodeBidiType,
    unicodeScriptDirection,
)
import re

PUA_CATEGORY = "Zzzz"
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


class GlyphUnicodeProperties:
    """
    Analyze and provide Unicode properties for glyphs in a font.

    This class provides methods to retrieve various Unicode properties such as
    bidirectional type, script direction, script names, and general categories.
    It attempts to infer Unicode values for glyphs that don't have explicit
    Unicode assignments by analyzing GSUB substitutions, glyph names, and
    composite structures.

    Args:
        font: A font object containing glyphs with potential Unicode assignments.
    """

    def __init__(self, font):
        self._font = font
        self._glyph2UnicodesMap = {}
        for g in font:
            if len(
                g.unicodes
            ) != 0 and PUA_CATEGORY not in unicodedata.script_extension(
                chr(g.unicodes[0])
            ):
                self._glyph2UnicodesMap[g.name] = g.unicodes
        for _getUnicodes in (
            self._unicodesFromGSUB,
            self._unicodesFromName,
            self._unicodesFromComposites,
        ):
            numTargetGlyphs = -1
            while numTargetGlyphs != len(self._nonUnicodeGlyphs()):
                numTargetGlyphs = len(self._nonUnicodeGlyphs())
                for g in self._nonUnicodeGlyphs():
                    unicodes = _getUnicodes(g)
                    if unicodes:
                        self._glyph2UnicodesMap[g.name] = list(unicodes)

    def _nonUnicodeGlyphs(self):
        return [g for g in self._font if g.name not in self._glyph2UnicodesMap]

    def _unicodesFromGSUB(self, glyph):
        unicodes = set()
        for gl, _ in glyph.features.sourceGlyphs.items():
            for gn in gl:
                unicodes.update(self._glyph2UnicodesMap.get(gn, set()))
        if not unicodes:
            for gl, _ in glyph.featreus.targetGlyphs.items():
                for gn in gl:
                    unicodes.update(self._glyph2UnicodesMap.get(gn, set()))
        return unicodes

    def _unicodesFromName(self, glyph):
        seperated = re.split(r"[_.]", glyph.name)
        unicodes = set()
        for part in seperated:
            unicodes.update(self._glyph2UnicodesMap.get(part, set()))
        return unicodes

    def _unicodesFromComposites(self, glyph):
        unicodes = set()
        for component in glyph.components:
            unicodes.update(self._glyph2UnicodesMap.get(component.baseGlyph, set()))
        if not unicodes:
            for composite in self._font.componentReferences.get(glyph.name, set()):
                unicodes.update(self._glyph2UnicodesMap.get(composite, set()))
        return unicodes

    def getInterpretedUnicodeForGlyphName(self, glyph_name):
        """
        Get the interpreted Unicode values for a given glyph name.

        Returns the Unicode codepoints associated with the specified glyph name.
        If the glyph has explicit Unicode assignments, those are returned. For
        glyphs without explicit Unicode values, this method attempts to infer
        them from GSUB substitutions, glyph name parsing, or composite glyph
        analysis.

        Args:
            glyph_name (str): The name of the glyph to look up.

        Returns:
            list: A list of Unicode codepoint integers associated with the glyph.
                Returns an empty list if no Unicode values can be determined.
        """
        return self._glyph2UnicodesMap.get(glyph_name, [])

    def getBidiTypeDirectionForGlyphName(self, glyph_name):
        """
        Get the bidirectional type direction for a given glyph name.

        Returns the Unicode bidirectional type direction for the specified
        glyph based on its interpreted Unicode values. This determines how the
        character behaves in bidirectional text layout.

        Args:
            glyph_name (str): The name of the glyph to analyze.

        Returns:
            Direction | None: Direction.RightToLeft for characters with strong RTL
                direction, Direction.LeftToRight for strong LTR, European and
                Arabic numbers, or None for neutral direction or glyphs without
                Unicode values.
        """
        uvs = self.getInterpretedUnicodeForGlyphName(glyph_name)
        if uvs == []:
            return
        return unicodeBidiType(uvs[0])

    def getScriptDirectionForGlyphName(self, glyph_name):
        """
        Get the script direction for a given glyph name.

        Returns the writing direction of the script associated with the specified
        glyph based on its interpreted Unicode values. This indicates whether
        the script is written left-to-right or right-to-left.

        Args:
            glyph_name (str): The name of the glyph to analyze.

        Returns:
            Direction | None: The script direction (Direction.LeftToRight or 
                Direction.RightToLeft), or None if the script is considered 
                default or the glyph has no Unicode values.
        """
        uvs = self.getInterpretedUnicodeForGlyphName(glyph_name)
        if uvs == []:
            return
        return unicodeScriptDirection(glyph_name)

    def getScriptNamesForGlyphName(self, glyph_name):
        """
        Get the script names for a given glyph name.

        Returns the Unicode script names associated with the specified glyph
        based on its interpreted Unicode values. Scripts represent writing
        systems like Latin, Arabic, Cyrillic, etc.

        Args:
            glyph_name (str): The name of the glyph to analyze.

        Returns:
            set: A set of script name strings (e.g., 'Latin', 'Arabic', 'Cyrillic')
                associated with the glyph's Unicode values. Returns an empty set
                if no Unicode values can be determined.
        """
        return tuple(
            unicodedata.script_name(tag)
            for tag in self.getScriptTagsForGlyphName(glyph_name)
        )

    def getScriptTagsForGlyphName(self, glyph_name):
        """
        Get the OpenType script tags for a given glyph name.

        Returns the OpenType script tags associated with the specified glyph
        based on its interpreted Unicode values. Script tags are 4-character
        identifiers used in OpenType features.

        Args:
            glyph_name (str): The name of the glyph to analyze.

        Returns:
            set: A set of 4-character OpenType script tag strings (e.g., 'latn',
                'arab', 'cyrl') associated with the glyph's Unicode values.
                Returns an empty set if no Unicode values can be determined.
        """
        result = set()
        uvs = self.getInterpretedUnicodeForGlyphName(glyph_name)
        for uv in uvs:
            result.update(unicodedata.script_extension(uv))
        return tuple(sorted(result))

    def getCategoryForGlyphName(self, glyph_name):
        """
        Get the Unicode category for a given glyph name.

        Returns the Unicode general category of the specified glyph based on its
        interpreted Unicode values. Categories classify characters by their
        general type (e.g., letter, number, punctuation).

        Args:
            glyph_name (str): The name of the glyph to analyze.

        Returns:
            str | None: The Unicode general category string or None if no
            Unicode values can be determined.
        """
        uvs = self.getInterpretedUnicodeForGlyphName(glyph_name)
        if uvs:
            return UNICODE_GENERAL_CATEGORIES[unicodedata.category(chr(uvs[0]))]


@font_cached_property("UnicodeData.Changed", "Features.Changed")
def glyphsUnicodeProperties(font):
    """
    Returns a cached object for retrieving Unicode properties of glyphs.

    This function returns an instance of `GlyphUnicodeProperties`, which provides
    methods to query Unicode-related information for glyphs in a font. It
    intelligently infers Unicode values for glyphs that do not have explicit
    Unicode assignments. This inference is performed by analyzing GSUB feature
    substitutions (inferring from source glyphs), glyph names (e.g., 'a.alt'
    might get 'a's Unicode), and component relationships (inferring from base
    components or composite glyphs). The resulting object is cached for
    performance.

    Args:
        font (defcon.Font): The font object to analyze.

    Returns:
        GlyphUnicodeProperties: An object providing methods to access glyph
            Unicode properties.
    """
    return GlyphUnicodeProperties(font)
