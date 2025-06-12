from utils import *
from fontgadgets.extensions.layout.shaper import *
import unittest
from pathlib import Path
import defcon

class TestGlyphRunClass(unittest.TestCase):

    def setUp(self):
        # Set up a common original glyph run for all tests.
        self.original_text = "Hello world example"
        self.original_glyphRun = Segment(self.original_text, bidi_level=0, start_index=0)

        # One-to-one mapping for simplicity
        self.glyphs = [f"g{i}" for i in range(len(self.original_text))]
        self.offsets = [(0, 0)] * len(self.original_text) # Changed from positions to offsets
        # Let each glyph have a width of 10
        self.advances = [(10, 0)] * len(self.original_text)
        self.clusters = list(range(len(self.original_text)))  # [0, 1, 2, ..., 18]

        # Dummy font for GlyphRun constructor
        class DummyFont:
            pass
        self.dummy_font = DummyFont()

        self.full_glyphRun = GlyphRun(
            segment=self.original_glyphRun,
            font=self.dummy_font,
            glyphs=self.glyphs,
            offsets=self.offsets,
            advances=self.advances,
            clusters=self.clusters,
        )

    def test_initialization_original(self):
        # Test that an original glyph run is created correctly.
        self.assertEqual(len(self.full_glyphRun), 19)
        self.assertEqual(self.full_glyphRun.width, 190)
        self.assertIs(self.full_glyphRun._source, self.full_glyphRun)
        self.assertEqual(list(self.full_glyphRun.clusters), self.clusters)
        self.assertEqual(list(self.full_glyphRun.glyphs), self.glyphs)

    def test_slice_basic(self):
        # Test a simple slice and verify its properties.
        # Slice the word "world" (indices 6 through 10)
        sliced_view = self.full_glyphRun.slice(6, 11)

        self.assertEqual(len(sliced_view), 5)
        self.assertEqual(sliced_view.width, 50)
        self.assertEqual(sliced_view.segment.text, "world")
        # The bidi level should be inherited
        self.assertEqual(sliced_view.segment.bidi_level, 0)
        # The start index of the text segment should be absolute
        self.assertEqual(sliced_view.segment.start_index, 6)

        # Clusters must be relative to "world", not "Hello world example"
        self.assertEqual(list(sliced_view.clusters), [0, 1, 2, 3, 4])

        # Check that the glyphs are the correct slice from the source
        self.assertEqual(list(sliced_view.glyphs), ["g6", "g7", "g8", "g9", "g10"])

        # Check that the source is correct
        self.assertIs(sliced_view._source, self.full_glyphRun)

    def test_slice_nested(self):
        # Test slicing a glyph run that is already a slice.
        # First, slice "world example" (from index 6 to end)
        first_slice = self.full_glyphRun.slice(6, 19)
        self.assertEqual(first_slice.segment.text, "world example")
        self.assertEqual(list(first_slice.clusters), list(range(13)))  # 0..12

        # Now, slice "example" from the first slice
        # "example" is at index 6 of "world example"
        second_slice = first_slice.slice(6, 13)

        self.assertEqual(len(second_slice), 7)
        self.assertEqual(second_slice.width, 70)
        self.assertEqual(second_slice.segment.text, "example")
        # The start index is relative to the original text
        self.assertEqual(second_slice.segment.start_index, 12)

        # check a nested slice
        self.assertEqual(list(second_slice.clusters), [0, 1, 2, 3, 4, 5, 6])

        # Check that glyphs are correct
        self.assertEqual(list(second_slice.glyphs), [f"g{i}" for i in range(12, 19)])

        # The source should point to the ultimate original glyph run
        self.assertIs(second_slice._source, self.full_glyphRun)


class ShaperTest(unittest.TestCase):
    def setUp(self):
        ufo_path = Path(__file__).parent.joinpath("data/ar-font-test-1.ufo")
        self.font = defcon.Font(ufo_path)
        self.maxDiff = None
        self._shaper = HBShaper(self.font)
 
    def test_letter_postions(self): 
        actual = self._shaper.shapeTextToGlyphRuns("la فا")
        expected = [GlyphRun(
                        font=self.font,
                        segment=Segment(text="la ", bidi_level=0, start_index=0),
                        glyphs=["l", "a", ".notdef"],
                        offsets=[(0, 0), (0, 0), (0, 0)],
                        advances=[(307, 0), (553, 0), (500, 0)],
                        clusters=[0, 1, 2],
                    ),
                    GlyphRun(
                        font=self.font,
                        segment=Segment(text="فا", bidi_level=1, start_index=3),
                        glyphs=["alef-ar.fina", "feh-ar.init"],
                        offsets=[(0, 0), (0, 0)],
                        advances=[(254, 0), (416, 0)],
                        clusters=[1, 0],
                    ),
                ]
        self.assertListEqual(actual, expected) # Corrected indentation
 
    def test_diacritcs_postions(self): 
        actual = self._shaper.shapeTextToGlyphRuns("وِ")
        expected = [GlyphRun(
                        font=self.font,
                        segment=Segment(text="وِ", bidi_level=1, start_index=0),
                        glyphs=["kasra-ar", "waw-ar"],
                        offsets=[(100, -454), (0, 0)],
                        advances=[(0, 0), (426, 0)],
                        clusters=[1, 0],
                    )
        ]
        self.assertListEqual(actual, expected)

if __name__ == "__main__":
    unittest.main()
