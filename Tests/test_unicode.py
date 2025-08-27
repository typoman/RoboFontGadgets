import unittest
import defcon
import fontgadgets.extensions.unicode.properties

def _add_component(glyph, base_glyph_name):
    component = glyph.instantiateComponent()
    component.baseGlyph = base_glyph_name
    glyph.appendComponent(component)


class TestGlyphUnicodeProperties(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        font = defcon.Font()
        font.newGlyph("a").unicode = ord("a") # LTR direction
        font.newGlyph("b").unicode = ord("b")
        font.newGlyph("f").unicode = ord("f")
        font.newGlyph("i").unicode = ord("i")
        font.newGlyph("rial").unicode = ord("﷼")
        font.newGlyph("space").unicode = ord(" ")
        font.newGlyph("one").unicode = ord("1")
        font.newGlyph("period").unicode = ord(".") # neutral direction
        font.newGlyph("peh").unicode = ord("پ") # RTL direction
        font.newGlyph("dollar").unicode = ord("$") # Symbol
        font.newGlyph("acutecomb").unicode = ord("́") # Mark (U+0301 COMBINING ACUTE ACCENT)

        # a composite glyph made from components with different unicode categories
        # to test inference and main unicode selection priority (Letter > Number > Punctuation).
        multi_cat_comp = font.newGlyph("multi_category_comp")
        _add_component(multi_cat_comp, "a")
        _add_component(multi_cat_comp, "one")
        _add_component(multi_cat_comp, "period")

        # a composite glyph to test the full main unicode priority order:
        # Letter > Number > Symbol > Punctuation > Mark
        full_priority_comp = font.newGlyph("full_priority_comp")
        _add_component(full_priority_comp, "period") # Punctuation
        _add_component(full_priority_comp, "one") # Number
        _add_component(full_priority_comp, "acutecomb") # Mark
        _add_component(full_priority_comp, "a") # Letter
        _add_component(full_priority_comp, "dollar") # Symbol

        font.newGlyph("a.alt")          # suffix inference
        font.newGlyph("f_i")            # ligature inference
        font.newGlyph("a_b.alt")        # ligature with suffixed part
        font.newGlyph("uni0042")        # AGL/uniXXXX inference (uni0042 -> B)
        font.newGlyph("uni0043.alt")    # AGL/uniXXXX inference with suffix (uni0043 -> C)
        font.newGlyph("f_uni0069")      # ligature with AGL name part

        # composite glyph to be inferred from components
        acutecomp = font.newGlyph("acutecomp")
        _add_component(acutecomp, "a")
        _add_component(acutecomp, "acutecomb")

        # glyph to be inferred from GSUB substitution
        font.newGlyph("a01") # alternate to 'a' in ss01, but with a non AGL name
        font.newGlyph(".notdef")
        font.newGlyph("unrelated_glyph") # no unicode, no inferable name/comp/sub

        # case for a glyph mapped to a Private Use Area (PUA) unicode.
        # this should be filtered out and not considered during inference
        font.newGlyph("onepersian.pnum").unicodes = [0xE000]

        # a composite glyph whose components' unicodes are also inferred.
        # 'ficomp' should be inferred from 'f_i', which is inferred from 'f' and 'i'.
        fi_comp = font.newGlyph("ficomp")
        _add_component(fi_comp, "f_i")

        # nested inference chain:
        # a.alt.ss02 is inferred from a.alt (via GSUB)
        # a.alt is inferred from a (via name)
        # a.alt.ss02.comp is inferred from a.alt.ss02 (via components)
        font.newGlyph("a.alt.ss02")
        a_alt_ss02_comp = font.newGlyph("a.alt.ss02.comp")
        _add_component(a_alt_ss02_comp, "a.alt.ss02")

        feature_text = """
        feature ss01 {
            sub a by a01;
        } ss01;

        feature ss02 {
            sub a.alt by a.alt.ss02;
        } ss02;
        """
        font.features.text = feature_text
        cls.base_font = font

    def setUp(self):
        """Create a fresh copy of the font for each test to ensure isolation."""
        self.font = self.base_font.copy()

    def test_glyph_unicode_properties_ligature_inference(self):
        glyph = self.font["f_i"]
        # unicodes are inferred from 'f' (102) and 'i' (105)
        self.assertEqual(glyph.unicodeProperties.interpretedUnicodes, (102, 105))
        self.assertEqual(glyph.unicodeProperties.category, "Lowercase Letter")
        self.assertEqual(glyph.unicodeProperties.categoryCode, 'Ll')
        self.assertEqual(glyph.unicodeProperties.script, 'Latin')
        self.assertEqual(glyph.unicodeProperties.scriptCode, 'Latn')
        self.assertEqual(glyph.unicodeProperties.bidiType, 'L')
        self.assertEqual(glyph.unicodeProperties.scriptDirection, 'LTR')

    def test_direct_encoding_properties(self):
        # test LTR glyph
        glyph_a = self.font["a"]
        self.assertEqual(glyph_a.unicodeProperties.interpretedUnicodes, (97,))
        self.assertEqual(glyph_a.unicodeProperties.category, "Lowercase Letter")
        self.assertEqual(glyph_a.unicodeProperties.categoryCode, "Ll")
        self.assertEqual(glyph_a.unicodeProperties.script, "Latin")
        self.assertEqual(glyph_a.unicodeProperties.scriptCode, "Latn")
        self.assertEqual(glyph_a.unicodeProperties.bidiType, 'L')
        self.assertEqual(glyph_a.unicodeProperties.scriptDirection, 'LTR')

        # test RTL glyph
        glyph_peh = self.font["peh"]
        self.assertEqual(glyph_peh.unicodeProperties.interpretedUnicodes, (1662,))
        self.assertEqual(glyph_peh.unicodeProperties.category, "Letter/Syllable/Ideograph")
        self.assertEqual(glyph_peh.unicodeProperties.categoryCode, "Lo")
        self.assertEqual(glyph_peh.unicodeProperties.script, "Arabic")
        self.assertEqual(glyph_peh.unicodeProperties.scriptCode, "Arab")
        self.assertEqual(glyph_peh.unicodeProperties.bidiType, 'R')
        self.assertEqual(glyph_peh.unicodeProperties.scriptDirection, 'RTL')

        # test neutral direction glyph
        glyph_period = self.font["period"]
        self.assertEqual(glyph_period.unicodeProperties.interpretedUnicodes, (46,))
        self.assertEqual(glyph_period.unicodeProperties.category, "Punctuation Mark")
        self.assertEqual(glyph_period.unicodeProperties.categoryCode, "Po")
        self.assertEqual(glyph_period.unicodeProperties.script, "Common")
        self.assertIsNone(glyph_period.unicodeProperties.bidiType)
        self.assertIsNone(glyph_period.unicodeProperties.scriptDirection)

    def test_suffix_name_inference(self):
        glyph = self.font["a.alt"]
        self.assertEqual(glyph.unicodeProperties.interpretedUnicodes, (97,))
        self.assertEqual(glyph.unicodeProperties.category, "Lowercase Letter")
        self.assertEqual(glyph.unicodeProperties.categoryCode, "Ll")
        self.assertEqual(glyph.unicodeProperties.script, "Latin")
        self.assertEqual(glyph.unicodeProperties.scriptCode, "Latn")
        self.assertEqual(glyph.unicodeProperties.bidiType, 'L')

    def test_ligature_with_suffixed_part_inference(self):
        glyph = self.font["a_b.alt"]
        self.assertEqual(glyph.unicodeProperties.interpretedUnicodes, (97, 98))
        self.assertEqual(glyph.unicodeProperties.category, "Lowercase Letter") # main is 'a'
        self.assertEqual(glyph.unicodeProperties.scriptCode, "Latn")

    def test_agl_name_inference(self):
        glyph = self.font["uni0042"]
        self.assertEqual(glyph.unicodeProperties.interpretedUnicodes, (66,)) # 'B'
        self.assertEqual(glyph.unicodeProperties.category, "Uppercase Letter")
        self.assertEqual(glyph.unicodeProperties.scriptCode, "Latn")

    def test_agl_with_suffix_name_inference(self):
        glyph = self.font["uni0043.alt"]
        self.assertEqual(glyph.unicodeProperties.interpretedUnicodes, (67,)) # 'C'
        self.assertEqual(glyph.unicodeProperties.category, "Uppercase Letter")

    def test_ligature_with_agl_name_inference(self):
        glyph = self.font["f_uni0069"]
        self.assertEqual(glyph.unicodeProperties.interpretedUnicodes, (102, 105)) # f, i
        self.assertEqual(glyph.unicodeProperties.category, "Lowercase Letter") # main is 'f'

    def test_component_inference(self):
        glyph = self.font["acutecomp"]
        # Inferred from 'a' (97, Ll, Latn) and component unicode 769
        self.assertEqual(set(glyph.unicodeProperties.interpretedUnicodes), {97, 769})
        # Main unicode should be from 'a' (Letter) over 'acutecomb' (Mark)
        self.assertEqual(glyph.unicodeProperties.category, "Lowercase Letter")
        self.assertEqual(glyph.unicodeProperties.categoryCode, "Ll")
        self.assertEqual(glyph.unicodeProperties.script, "Latin")
        self.assertEqual(glyph.unicodeProperties.scriptCode, "Latn")

    def test_composite_main_unicode_priority(self):
        glyph = self.font["multi_category_comp"]
        # unicodes are from 'a' (97), 'one' (49), 'period' (46)
        self.assertEqual(set(glyph.unicodeProperties.interpretedUnicodes), {97, 49, 46})
        # main unicode should be 'a' due to priority: Letter > Number > Punctuation
        self.assertEqual(glyph.unicodeProperties.category, "Lowercase Letter")
        self.assertEqual(glyph.unicodeProperties.scriptCode, "Latn")

    def test_main_unicode_full_priority_order(self):
        glyph = self.font["full_priority_comp"]
        # Unicodes from 'a'(97), 'one'(49), 'dollar'(36), 'period'(46), 'acutecomb'(769)
        expected_unicodes = {97, 49, 36, 46, 769}
        self.assertEqual(set(glyph.unicodeProperties.interpretedUnicodes), expected_unicodes)
        # Main unicode should be from 'a' due to priority:
        # Letter > Number > Symbol > Punctuation > Mark
        self.assertEqual(glyph.unicodeProperties.category, "Lowercase Letter")
        self.assertEqual(glyph.unicodeProperties.script, "Latin")
        self.assertEqual(glyph.unicodeProperties.categoryCode, "Ll")

    def test_gsub_inference(self):
        glyph = self.font["a01"]
        self.assertEqual(glyph.unicodeProperties.interpretedUnicodes, (97,))
        self.assertEqual(glyph.unicodeProperties.category, "Lowercase Letter")
        self.assertEqual(glyph.unicodeProperties.scriptCode, "Latn")

    def test_nested_inference_component_of_ligature(self):
        glyph = self.font["ficomp"]
        # inferred from component 'f_i', which is inferred from 'f' and 'i'
        self.assertEqual(glyph.unicodeProperties.interpretedUnicodes, (102, 105))
        self.assertEqual(glyph.unicodeProperties.category, "Lowercase Letter")

    def test_nested_inference_gsub_of_suffixed(self):
        glyph = self.font["a.alt.ss02"]
        # inferred from 'a.alt' via GSUB, which is inferred from 'a' via name
        self.assertEqual(glyph.unicodeProperties.interpretedUnicodes, (97,))
        self.assertEqual(glyph.unicodeProperties.category, "Lowercase Letter")

    def test_deeply_nested_inference_from_component(self):
        glyph = self.font["a.alt.ss02.comp"]
        # inferred from component 'a.alt.ss02' -> GSUB 'a.alt' -> name 'a'
        self.assertEqual(glyph.unicodeProperties.interpretedUnicodes, (97,))
        self.assertEqual(glyph.unicodeProperties.category, "Lowercase Letter")

    def test_no_unicode_properties(self):
        for name in [".notdef", "unrelated_glyph"]:
            glyph = self.font[name]
            self.assertEqual(glyph.unicodeProperties.interpretedUnicodes, [])
            self.assertIsNone(glyph.unicodeProperties.category)
            self.assertIsNone(glyph.unicodeProperties.scriptCode)
            self.assertIsNone(glyph.unicodeProperties.bidiType)

    def test_pua_unicode_is_ignored(self):
        glyph = self.font["onepersian.pnum"]
        # private use area unicodes should be filtered out and instead other methods
        # used to find its properties, here the unicode comes from AGL naming
        self.assertEqual(glyph.unicodeProperties.interpretedUnicodes, (1777,))
        self.assertEqual(glyph.unicodeProperties.category, "Decimal Digit")
        self.assertEqual(glyph.unicodeProperties.scriptCode, "Arab")

    def test_cache_invalidation_on_unicode_change(self):
        glyph = self.font.newGlyph("test_glyph_unicode_changes")
        glyph.unicode = ord("B")

        # Initial check
        self.assertEqual(glyph.unicodeProperties.interpretedUnicodes, (66,))
        self.assertEqual(glyph.unicodeProperties.category, "Uppercase Letter")

        # Modify unicodes
        glyph.unicode = ord("z")

        # Check if properties are updated
        self.assertEqual(glyph.unicodeProperties.interpretedUnicodes, (122,))
        self.assertEqual(glyph.unicodeProperties.category, "Lowercase Letter")

    def test_cache_invalidation_on_component_change(self):
        # Create a new glyph for this test to avoid side effects
        comp_glyph = self.font.newGlyph("comp_glyph")

        # Initial check (no components, no unicode)
        self.assertEqual(comp_glyph.unicodeProperties.interpretedUnicodes, [])
        self.assertIsNone(comp_glyph.unicodeProperties.category)

        # Add a component
        _add_component(comp_glyph, "a")

        # Check if properties are updated based on the new component
        self.assertEqual(comp_glyph.unicodeProperties.interpretedUnicodes, (97,))
        self.assertEqual(comp_glyph.unicodeProperties.category, "Lowercase Letter")

        # Remove the component
        comp_glyph.clearComponents()

        # Check if properties are reset
        self.assertEqual(comp_glyph.unicodeProperties.interpretedUnicodes, [])
        self.assertIsNone(comp_glyph.unicodeProperties.category)

    def test_cache_invalidation_on_glyph_name_change(self):
         glyph = self.font.newGlyph("foo")
         self.assertEqual(glyph.unicodeProperties.interpretedUnicodes, [])
         self.assertIsNone(glyph.unicodeProperties.category)

         # Rename to another inferable name
         glyph.name = "o.alt"

         # Check if properties are inferred from the new name
         self.assertEqual(glyph.unicodeProperties.interpretedUnicodes, (111,))
         self.assertEqual(glyph.unicodeProperties.category, "Lowercase Letter")

    def test_cache_invalidation_on_features_change(self):
         glyph_ss01 = self.font["a01"]
         # Initial check (inferred from GSUB)
         self.assertEqual(glyph_ss01.unicodeProperties.interpretedUnicodes, (97,))

         # Remove the feature definition
         self.font.features.text = ""

         # Check if properties are now empty (as GSUB inference is gone)
         self.assertEqual(glyph_ss01.unicodeProperties.interpretedUnicodes, [])
         self.assertIsNone(glyph_ss01.unicodeProperties.category)

         # Add the feature back
         self.font.features.text = "feature ss01 { sub a by a01; } ss01;"

         # Check if properties are re-inferred
         self.assertEqual(glyph_ss01.unicodeProperties.interpretedUnicodes, (97,))
         self.assertEqual(glyph_ss01.unicodeProperties.category, "Lowercase Letter")


if __name__ == '__main__':
    unittest.main()
