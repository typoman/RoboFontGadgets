# Copyright 2025 Bahman Eslami All Rights Reserved.
import fontgadgets.extensions.features
from fontgadgets.decorators import cached_method, font_cached_property, font_property
from fontTools import unicodedata
from fontTools import agl
from ufo2ft.util import unicodeScriptDirection
from ufo2ft.featureWriters.kernFeatureWriter import unicodeBidiType

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


def unicodeCategoryCode(uv):
    return unicodedata.category(chr(uv))

def unicodeCategoryName(uv):
    return UNICODE_GENERAL_CATEGORIES[unicodeCategoryCode(uv)]

def unicodeScriptCode(uv):
    return unicodedata.script(chr(uv))

def unicodeScriptName(uv):
    code = unicodeScriptCode(uv)
    return unicodedata.script_name(code, default=None)

def getUnicodesFromSuffixed(name, glyph_name_2_unicodes_map):
    """
    Get unicode values for a glyph name with a suffix (e.g., 'a.alt').

    This function strips the suffix from the glyph name and looks up the
    unicodes associated with the base name.

    Args:
        name (str): The suffixed glyph name.
        glyph_name_2_unicodes_map (dict): A map from glyph names to unicode tuples.

    Returns:
        tuple: A sorted tuple of integer unicode values.

    >>> getUnicodesFromSuffixed('a.alt', {'a': (97,)})
    (97,)
    >>> getUnicodesFromSuffixed('a.sc.pcap', {'a': (97,)})
    (97,)
    >>> getUnicodesFromSuffixed('uni0041.alt', {})
    (65,)
    >>> getUnicodesFromSuffixed('.notdef', {})
    ()
    >>> getUnicodesFromSuffixed('foo.alt', {})
    ()
    >>> getUnicodesFromSuffixed('f_i.liga', {})
    (102, 105)
    """
    unicodes = set()
    base_name = name.rsplit(".", 1)[0]
    if base_name != name:  # check if a suffix was actually removed
        base_unicodes = glyph_name_2_unicodes_map.get(base_name, ())
        if base_unicodes:
            unicodes.update(base_unicodes)
        else:
            unicodes.update(getUnicodesFromAGLName(base_name))
    return tuple(sorted(unicodes))


def getUnicodesFromLigaName(name, glyph_name_2_unicodes_map):
    """
    Get unicode values for a ligature glyph name (e.g., 'f_i').

    This function splits the name by underscores and aggregates the unicodes
    from each part.

    Args:
        name (str): The ligature glyph name.
        glyph_name_2_unicodes_map (dict): A map from glyph names to unicode tuples.

    Returns:
        tuple: A sorted tuple of integer unicode values.

    >>> getUnicodesFromLigaName('a.alt_b.sc', {'a': (97,), 'b': (98,)})
    (97, 98)
    >>> getUnicodesFromLigaName('f_i', {'f': (102,), 'i': (105,)})
    (102, 105)
    >>> getUnicodesFromLigaName('a.alt_b.sc', {'a': (97,), 'b': (98,)})
    (97, 98)
    >>> getUnicodesFromLigaName('a__b', {'a': (97,), 'b': (98,)})
    (97, 98)
    >>> getUnicodesFromLigaName('uni0041_a', {})
    (65, 97)
    >>> getUnicodesFromLigaName('a_uni0041', {'a': (97,), })
    (65, 97)
    >>> getUnicodesFromLigaName('uni0041_uni0042', {})
    (65, 66)
    >>> getUnicodesFromLigaName('a.alt_uni0042', {'a': (97,)})
    (66, 97)
    >>> getUnicodesFromLigaName('uni0041.alt_a', {'a': (97,)})
    (65, 97)
    """
    unicodes = set()
    liga_parts = name.split("_")
    if len(liga_parts) > 1:
        for part in liga_parts:
            part_unicodes = glyph_name_2_unicodes_map.get(part, ())
            if not part_unicodes:
                part_unicodes = getUnicodesFromSuffixed(part, glyph_name_2_unicodes_map)
            if not part_unicodes:
                part_unicodes = getUnicodesFromAGLName(part)
            unicodes.update(part_unicodes)
    return tuple(sorted(unicodes))

def getUnicodesFromAGLName(name):
    """
    Get unicode values from an Adobe Glyph List (AGL) compliant name.

    Args:
        name (str): The AGL-compliant glyph name.

    Returns:
        A tuple of integer unicode values.
    """
    return tuple(ord(c) for c in agl.toUnicode(name))


class FontUnicodeProperties:
    """
    Analyze and provide unicode properties for glyphs in a font.

    This class provides methods to retrieve various unicode properties such as
    bidirectional type, script direction, script names, and general categories.
    It attempts to infer unicode values for glyphs that don't have explicit
    unicode assignments by analyzing GSUB substitutions, glyph names, and
    composite structures. Interpreted unicodes are only to get the properties
    so they're by themselves not the most concrete answer for the glyph
    unicodes. We need them mostly to get their category, direction or script
    of a glyph.

    Args:
        font: A font object containing glyphs with potential unicode assignments.
    """

    def __init__(self, font):
        self._font = font
        self._updateUnicodes()

    def _updateUnicodes(self):
        """
        Build and populate the map of glyph names to unicode values.

        This method initializes the map with directly encoded glyphs and then
        iteratively tries to resolve un-encoded glyphs using various inference
        methods (GSUB, name, components) until no more glyphs can be resolved.
        """
        self._glyph_name_2_unicodes_map = {}
        font = self._font
        for g in font:
            valid_unicodes = [u for u in g.unicodes if unicodedata.category(chr(u)) != 'Co']
            if valid_unicodes:
                self._glyph_name_2_unicodes_map[g.name] = tuple(valid_unicodes)
        unresolved_glyphs = self._nonUnicodeGlyphs()
        while True:
            processed_this_pass = set()
            for glyph_name in sorted(unresolved_glyphs):
                glyph = font[glyph_name]
                for _getUnicodes in (
                    self._unicodesFromGSUB,
                    self._unicodesFromName,
                    self._unicodesFromComposites,
                ):
                    unicodes = _getUnicodes(glyph)
                    if unicodes:
                        self._glyph_name_2_unicodes_map[glyph_name] = tuple(sorted(unicodes))
                        processed_this_pass.add(glyph_name)
                        break
            if not processed_this_pass:
                return
            unresolved_glyphs -= processed_this_pass

    def _nonUnicodeGlyphs(self):
        """
        Get a set of glyph names that do not have direct unicode assignments.
        """
        return {g.name for g in self._font if g.name not in self._glyph_name_2_unicodes_map}

    def _unicodesFromGSUB(self, glyph):
        """
        Infer unicodes for a glyph from its GSUB substitutions.

        This method checks if the glyph is a target in any substitution and
        infers its unicodes from the source glyphs of that substitution.

        Args:
            glyph: The glyph object.

        Returns:
            set: A set of inferred integer unicode values.
        """
        unicodes = set()
        for gl, _ in glyph.features.sourceGlyphs.items():
            for gn in gl:
                unicodes.update(self._glyph_name_2_unicodes_map.get(gn, ()))
        return unicodes

    def _unicodesFromName(self, glyph):
        """
        Infer unicodes for a glyph from its name.

        This method attempts to parse the glyph name to find unicodes, trying
        suffixed names (e.g., 'a.alt'), ligature names (e.g., 'f_i'), and
        'uniXXXX' style names.

        Args:
            glyph: The glyph object.

        Returns:
            tuple: A tuple of inferred integer unicode values.
        """
        name = glyph.name
        g_map = self._glyph_name_2_unicodes_map
        unicodes = getUnicodesFromSuffixed(name, g_map)
        if not unicodes:
            unicodes = getUnicodesFromLigaName(name, g_map)
        if not unicodes:
            unicodes = getUnicodesFromAGLName(name)
        return unicodes

    def _unicodesFromComposites(self, glyph):
        """
        Infer unicodes for a glyph from its components.

        This method aggregates the unicodes of the base glyphs of all
        components within a composite glyph. This is the last resort
        and can be the least reliable way.

        Args:
            glyph: The glyph object.

        Returns:
            set: A set of inferred integer unicode values from its components.
        """
        unicodes = set()
        for component in glyph.components:
            unicodes.update(self._glyph_name_2_unicodes_map.get(component.baseGlyph, ()))
        return unicodes

    def _getProperty(self, glyph_name, callback, default=None):
        """
        Finds the main unicode for a glyph, applies a given callback function
        to it, and returns the result.

        Args:
            glyph_name (str): The name of the glyph.
            callback (callable): A function that takes an integer unicode value
                and returns a unicode property.
            default: The value to return if the glyph has no main unicode.

        Returns:
            The result of the callback, or the default value.
        """
        main_unicode = self.getMainUnicodeForGlyphName(glyph_name)
        if main_unicode is not None:
            return callback(main_unicode)
        return default

    @cached_method
    def getMainUnicodeForGlyphName(self, glyph_name):
        """
        Determine the primary unicode for a glyph.

        For glyphs with multiple associated unicodes, this method selects the
        most representative one based on a priority order of general categories:
        Letter > Number > Symbol > Punctuation > Mark. If multiple unicodes
        share the highest priority, the one with the lowest code point value
        is chosen for deterministic results.

        Args:
            glyph_name (str): The name of the glyph.

        Returns:
            int | None: The main integer unicode value, or None if the glyph has
            no associated unicodes.
        """
        # priority: Letter > Number > Symbol > Punctuation > Mark
        unicodes = self._glyph_name_2_unicodes_map.get(glyph_name, [])
        if not unicodes:
            return None
        if len(unicodes) == 1:
            return unicodes[0]
        # L=Letter, N=Number, S=Symbol, P=Punctuation, M=Mark, Z=Separator, C=Other
        priority_order = {"L": 1, "N": 2, "S": 3, "P": 4, "M": 5}
        default_priority = 99
        def get_priority(u):
            # the first letter of the category string (e.g., 'L' from 'Lu')
            # is sufficient to determine the main category group.
            main_category = unicodedata.category(chr(u))[0]
            return priority_order.get(main_category, default_priority)
        # find the unicode with the minimum (best) priority value and the
        # lowest unicode value among them for deterministic result
        return min(unicodes, key=lambda u: (get_priority(u), u))

    @cached_method
    def getInterpretedUnicodesForGlyphName(self, glyph_name):
        """
        Get all assigned or inferred unicodes for a glyph.

        Args:
            glyph_name (str): The name of the glyph.

        Returns:
            list: A list of integer unicode values associated with the glyph.
                Returns an empty list if no unicodes could be determined.
        """
        return self._glyph_name_2_unicodes_map.get(glyph_name, [])

    @cached_method
    def getBidiTypeForGlyphName(self, glyph_name):
        """Determine the bidirectional type for a given Unicode value.

        Args:
            glyph_name (str): The name of the glyph.

        Returns:
            Return "R" for glyphs with RTL direction, or "L" for LTR (whether
            'strong' or 'weak'), or None for neutral direction.
        """
        return self._getProperty(glyph_name, unicodeBidiType)

    @cached_method
    def getScriptDirectionForGlyphName(self, glyph_name):
        """
        Determine the horizontal script direction for a Unicode codepoint.

        Args:
            glyph_name (str): The name of the glyph.

        Returns:
            str: "LTR" or "RTL" if a direction is defined for the script.
            None: For "Zyyy" (Common) or "Zinh" (Inherited) scripts. This
            is used for determining the kerning pairs and groups direction.
        """
        return self._getProperty(glyph_name, unicodeScriptDirection)

    @cached_method
    def getScriptCodeForGlyphName(self, glyph_name):
        """
        Return the four-letter script code assigned to the glyph uniocde.

        Args:
            glyph_name (str): The name of the glyph.
        """
        return self._getProperty(glyph_name, unicodeScriptCode)

    @cached_method
    def getScriptNameForGlyphName(self, glyph_name):
        """
        Return the four-letter script code assigned to the glyph uniocde.

        Args:
            glyph_name (str): The name of the glyph.
        """
        return self._getProperty(glyph_name, unicodeScriptName)

    @cached_method
    def getCategoryCodeForGlyphName(self, glyph_name):
        """
        Get the two-letter unicode general category code for the glyph.

        Args:
            glyph_name (str): The name of the glyph.

        Returns:
            str | None: The two-letter unicde category code (e.g., 'Lu', 'Po'), or None
            if no main unicode is found.
        """
        return self._getProperty(glyph_name, unicodeCategoryCode)

    @cached_method
    def getCategoryNameForGlyphName(self, glyph_name):
        return self._getProperty(glyph_name, unicodeCategoryName)

@font_cached_property(
    "UnicodeData.Changed",
    "Features.TextChanged",
    "Component.BaseGlyphChanged",
    "Glyph.ComponentWillBeAdded",
    "Glyph.ComponentWillBeDeleted",
    "Glyph.NameChanged",
    "Glyph.UnicodesChanged"
    )
def unicodeProperties(font):
    """
    Returns an object for retrieving unicode properties of glyphs.

    This function returns an instance of `FontUnicodeProperties`, which provides
    methods to query unicode-related information for glyphs in a font. It
    infers unicode values for glyphs that do not have explicit unicode
    assignments. This inference is performed by analyzing GSUB feature
    substitutions (inferring from source glyphs), glyph names (e.g., 'a.alt'
    might get 'a's unicode), and component relationships (inferring from base
    components or composite glyphs).

    Returns:
        FontUnicodeProperties: An object providing methods to access glyph
            unicode properties.
    """
    return FontUnicodeProperties(font)


class GlyphUnicodeProperties:
    """
    Provides access to unicode properties for a specific glyph.

    Args:
        glyph: A glyph object from a font.
    """

    def __init__(self, glyph):
        self._glyph = glyph
        self._font = glyph.font

    @property
    def _properties(self):
        return self._font.unicodeProperties

    @property
    def categoryCode(self):
        """
        Returns the unicode general category two letter code for the glyph.
        """
        return self._properties.getCategoryCodeForGlyphName(self._glyph.name)

    @property
    def category(self):
        """
        Returns the full name of unicode general category for the glyph.
        (e.g., 'Uppercase Letter', 'Punctuation Mark').
        """
        return self._properties.getCategoryNameForGlyphName(self._glyph.name)

    @property
    def bidiType(self):
        return self._properties.getBidiTypeForGlyphName(self._glyph.name)

    @property
    def scriptDirection(self):
        return self._properties.getScriptDirectionForGlyphName(self._glyph.name)

    @property
    def interpretedUnicodes(self):
        """
        Returns the interpreted Unicodes for the glyph.
        """
        return self._properties.getInterpretedUnicodesForGlyphName(self._glyph.name)

    @property
    def script(self):
        """
        Returns the unicode script associated with the glyph
        (e.g., 'Latin', 'Arabic').
        """
        return self._properties.getScriptNameForGlyphName(self._glyph.name)

    @property
    def scriptCode(self):
        return self._properties.getScriptCodeForGlyphName(self._glyph.name)


@font_property
def unicodeProperties(glyph):
    """
    Returns an object for retrieving unicode properties of glyphs.

    This function returns an instance of `GlyphUnicodeProperties`, which provides
    methods to query unicode-related information for glyphs in a font. It
    infers unicode values for glyphs that do not have explicit unicode
    assignments. This inference is performed by analyzing GSUB feature
    substitutions (inferring from source glyphs), glyph names (e.g., 'a.alt'
    might get 'a's unicode), and component relationships (inferring from base
    components or composite glyphs).

    Returns:
        GlyphUnicodeProperties: An object providing methods to access glyph
            unicode properties.
    """
    return GlyphUnicodeProperties(glyph)

if __name__ == "__main__":
    import doctest
    doctest.testmod()
