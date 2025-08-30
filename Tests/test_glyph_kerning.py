from utils import defcon
import fontgadgets.extensions.glyph.kerning
import unittest
from collections import namedtuple

KernTestData = namedtuple(
    "KernTestData",
    [
        "ref_name",  # name of the glyph to start from (e.g., 'A')
        "side",  # is it a 'left' or 'right' side kerning?
        "other_name",  # name of the 'other' glyph/group in the pair
        "expected_logical_pair",  # the expected (first, second) tuple in font.kerning
        "value",  # the kerning value to set and check
        "string",  # string of the pair (e.g. 'ر.')
    ],
)

TESTS = {
    "Group": {
        # ==================================
        # Group to Group Kerning
        # ==================================
        "Group": [
            # RTL Group / RTL Group
            KernTestData(
                "reh",
                "left",
                "waw",
                ("public.kern1.reh_LEFT", "public.kern2.waw_RIGHT"),
                -10,
                "رو",
            ),
            # RTL Group / NEU Group
            KernTestData(
                "reh",
                "left",
                "braceleft",
                # the NEU group in (RTL, NEU) pairs uses the opposite kern side name
                ("public.kern1.reh_LEFT", "public.kern1.braceleft_RIGHT"),
                -15,
                "ر{",
            ),
            # LTR Group / LTR Group
            KernTestData(
                "A",
                "right",
                "V",
                ("public.kern1.A_RIGHT", "public.kern2.V_LEFT"),
                -20,
                "AV",
            ),
            # LTR Group / NEU Group
            KernTestData(
                "A",
                "right",
                "braceleft",
                ("public.kern1.A_RIGHT", "public.kern2.braceleft_LEFT"),
                -25,
                "A{",
            ),
            # NEU Group / RTL Group
            KernTestData(
                "braceright",
                "left",
                "reh",
                # the NEU group in (RTL, NEU) pairs uses the opposite kern side name
                ("public.kern2.braceright_LEFT", "public.kern2.reh_RIGHT"),
                -30,
                "}ر",
            ),
            # NEU Group / LTR Group
            KernTestData(
                "braceleft",
                "right",
                "A",
                ("public.kern1.braceleft_RIGHT", "public.kern2.A_LEFT"),
                -35,
                "{A",
            ),
            # NEU Group / NEU Group
            KernTestData(
                "braceleft",
                "right",
                "braceright",
                ("public.kern1.braceleft_RIGHT", "public.kern2.braceright_LEFT"),
                -40,
                "{}",
            ),
        ],
        # ======================================
        # Group to Glyph Exception Kerning
        # ======================================
        "Glyph": [
            # RTL Group / RTL Glyph
            KernTestData(
                "reh", "left", "waw", ("public.kern1.reh_LEFT", "waw"), -50, "رو"
            ),
            # RTL Group / NEU Glyph
            KernTestData(
                "reh",
                "left",
                "braceleft",
                ("public.kern1.reh_LEFT", "braceleft"),
                -55,
                "ر{",
            ),
            # LTR Group / LTR Glyph
            KernTestData("A", "right", "V", ("public.kern1.A_RIGHT", "V"), -60, "AV"),
            # LTR Group / NEU Glyph
            KernTestData(
                "A",
                "right",
                "braceleft",
                ("public.kern1.A_RIGHT", "braceleft"),
                -65,
                "A{",
            ),
            # NEU Group / RTL Glyph
            KernTestData(
                "braceright",
                "left",
                "reh",
                ("public.kern2.braceright_LEFT", "reh"),
                -70,
                "}ر",
            ),
            # NEU Group / LTR Glyph
            KernTestData(
                "braceleft",
                "right",
                "A",
                ("public.kern1.braceleft_RIGHT", "A"),
                -75,
                "{A",
            ),
            # NEU Group / NEU Glyph
            KernTestData(
                "braceleft",
                "right",
                "braceright",
                ("public.kern1.braceleft_RIGHT", "braceright"),
                -80,
                "{}",
            ),
        ],
    },
    "Glyph": {
        # ======================================
        # Glyph to Group Exception Kerning
        # ======================================
        "Group": [
            # RTL Glyph / RTL Group
            KernTestData(
                "reh", "left", "waw", ("reh", "public.kern2.waw_RIGHT"), -90, "رو"
            ),
            # RTL Glyph / NEU Group
            KernTestData(
                "reh",
                "left",
                "braceleft",
                ("reh", "public.kern1.braceleft_RIGHT"),
                -95,
                "ر{",
            ),
            # LTR Glyph / LTR Group
            KernTestData("A", "right", "V", ("A", "public.kern2.V_LEFT"), -100, "AV"),
            # LTR Glyph / NEU Group
            KernTestData(
                "A",
                "right",
                "braceleft",
                ("A", "public.kern2.braceleft_LEFT"),
                -105,
                "A{",
            ),
            # NEU Glyph / RTL Group
            KernTestData(
                "braceright",
                "left",
                "reh",
                ("braceright", "public.kern2.reh_RIGHT"),
                -110,
                "}ر",
            ),
            # NEU Glyph / LTR Group
            KernTestData(
                "braceleft",
                "right",
                "A",
                ("braceleft", "public.kern2.A_LEFT"),
                -115,
                "{A",
            ),
            # NEU Glyph / NEU Group
            KernTestData(
                "braceleft",
                "right",
                "braceright",
                ("braceleft", "public.kern2.braceright_LEFT"),
                -120,
                "{}",
            ),
        ],
        # ======================================
        # Glyph to Glyph Exception Kerning
        # ======================================
        "Glyph": [
            # RTL Glyph / RTL Glyph
            KernTestData("reh", "left", "waw", ("reh", "waw"), -130, "رو"),
            # RTL Glyph / NEU Glyph
            KernTestData("reh", "left", "braceleft", ("reh", "braceleft"), -135, "ر{"),
            # LTR Glyph / LTR Glyph
            KernTestData("A", "right", "V", ("A", "V"), -140, "AV"),
            # LTR Glyph / NEU Glyph
            KernTestData("A", "right", "braceleft", ("A", "braceleft"), -145, "A{"),
            # NEU Glyph / RTL Glyph
            KernTestData(
                "braceright", "left", "reh", ("braceright", "reh"), -150, "}ر"
            ),
            # LTR Glyph / LTR Glyph
            KernTestData("braceleft", "right", "A", ("braceleft", "A"), -155, "{A"),
            # NEU Glyph / NEU Glyph
            KernTestData(
                "braceleft",
                "right",
                "braceright",
                ("braceleft", "braceright"),
                -160,
                "{}",
            ),
        ],
    },
}


class TestGlyphKerning(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        """Set up a base font with all necessary glyphs and unicodes."""
        font = defcon.Font()
        glyph_map = {
            "7": "seven",
            "ر": "reh",
            "و": "waw",
            "V": "V",
            "{": "braceleft",
            "}": "braceright",
            "A": "A",
        }
        for char, name in glyph_map.items():
            glyph = font.newGlyph(name)
            glyph.unicode = ord(char)
        cls.base_font = font

        groups = {
            "A": {"left": "A_LEFT", "right": "A_RIGHT"},
            "V": {"left": "V_LEFT", "right": "V_RIGHT"},
            "seven": {"left": "seven_LEFT", "right": "seven_RIGHT"},
            "reh": {"left": "reh_LEFT", "right": "reh_RIGHT"},
            "waw": {"left": "waw_LEFT", "right": "waw_RIGHT"},
            "braceleft": {"left": "braceleft_LEFT", "right": "braceleft_RIGHT"},
            "braceright": {"left": "braceright_LEFT", "right": "braceright_RIGHT"},
        }

        for glyph_name, side_groups in groups.items():
            glyph = font[glyph_name]
            glyph.kerningGroups.left = side_groups["left"]
            glyph.kerningGroups.right = side_groups["right"]

    def setUp(self):
        self.font = self.base_font

    def _get_kerning_context(self, glyph_name, side, is_group):
        glyph = self.font[glyph_name]
        if is_group:
            return glyph.kerningGroups.getKerningGroupForSide(side)
        return glyph

    def _get_kerning_dict(self, context, side):
        if isinstance(context, defcon.Glyph):
            return getattr(context.kerning, side)
        # for kerningGroup objects, .kerning is the dictionary itself
        return context.kerning

    def _test_kerning_pair(
        self, ref_context, other_context, side, value, expected_pair
    ):
        # 1. set kerning value
        ref_kerning_dict = self._get_kerning_dict(ref_context, side)
        ref_kerning_dict[other_context] = value

        # 2. assert logical pair in font.kerning
        self.assertIn(
            expected_pair,
            self.font.kerning,
            f"Logical pair {expected_pair} not created in font.kerning",
        )
        self.assertEqual(
            self.font.kerning[expected_pair],
            value,
            f"Incorrect value for {expected_pair} in font.kerning",
        )

        # 3. assert retrieval from reference context
        retrieved_value = self._get_kerning_dict(ref_context, side)[other_context]
        self.assertEqual(
            retrieved_value,
            value,
            "Could not retrieve correct value from reference context",
        )

        # 4. assert retrieval from other (reverse) context
        opposite_side = "left" if side == "right" else "right"
        reverse_retrieved_value = self._get_kerning_dict(other_context, opposite_side)[
            ref_context
        ]
        self.assertEqual(
            reverse_retrieved_value,
            value,
            "Could not retrieve correct value from reverse context",
        )

        # 5. test deletion
        del self._get_kerning_dict(ref_context, side)[other_context]
        self.assertNotIn(
            expected_pair,
            self.font.kerning,
            f"Logical pair {expected_pair} was not deleted from font.kerning",
        )

    def _run_single_kerning_test(self, test_data, ref_type, other_type):
        self.font.kerning.clear()

        side = test_data.side
        other_side = "left" if side == "right" else "right"

        # if this is an exception test (i.e., involves a glyph), first
        # set a group-to-group kerning value that the exception will
        # exist alongside.
        is_exception_test = ref_type == "Glyph" or other_type == "Glyph"
        if is_exception_test:
            GROUP_KERN_VALUE = -999  # a distinct, non-conflicting value

            # get the group contexts for both sides of the pair
            ref_group_context = self._get_kerning_context(
                test_data.ref_name, side, is_group=True
            )
            other_group_context = self._get_kerning_context(
                test_data.other_name, other_side, is_group=True
            )

            # set the base group-to-group kerning
            ref_group_kerning_dict = self._get_kerning_dict(ref_group_context, side)
            ref_group_kerning_dict[other_group_context] = GROUP_KERN_VALUE

            # verify the group kerning was added before proceeding
            self.assertEqual(
                len(self.font.kerning),
                1,
                "Base group kerning pair was not set up correctly.",
            )

        # get the actual contexts for this specific test case, which may
        # be a mix of groups and glyphs.
        ref_context = self._get_kerning_context(
            test_data.ref_name, side, ref_type == "Group"
        )
        other_context = self._get_kerning_context(
            test_data.other_name, other_side, other_type == "Group"
        )

        # if it's an exception, this will test its creation
        # alongside the existing group pair.
        self._test_kerning_pair(
            ref_context,
            other_context,
            test_data.side,
            test_data.value,
            test_data.expected_logical_pair,
        )

    def test_all_kerning_samples(self):
        for ref_type, other_types in TESTS.items():
            for other_type, test_cases in other_types.items():
                for test_data in test_cases:
                    with self.subTest(
                        ref_type=ref_type,
                        other_type=other_type,
                        ref=test_data.ref_name,
                        side=test_data.side,
                        other=test_data.other_name,
                    ):
                        self._run_single_kerning_test(test_data, ref_type, other_type)


if __name__ == "__main__":
    unittest.main()
