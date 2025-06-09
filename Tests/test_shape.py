from utils import *
from fontgadgets.extensions.layout.shaper import *
import unittest

class ShaperTest(unittest.TestCase):

    def setUp(self):
        ufo_path = Path(__file__).parent.joinpath("data/ar-font-test-1.ufo")
        font = defcon.Font(ufo_path)
        self._shaper = HBShaper(font)

    def test_letter_postions(self):
        pars = self._shaper.shapeTextToParagraphs('la فا')
        expected = [
            ShapedParagraph(
                baseLevel=0,
                segments=[
                    ShapedSegment(
                        segment=Segment(text="la ", bidi_level=0, start_index=0),
                        glyphs=["l", "a", ".notdef"],
                        positions=[(0, 0), (0, 0), (0, 0)],
                        advances=[(307, 0), (553, 0), (500, 0)],
                        clusters=[0, 1, 2],
                        width=1360,
                    ),
                    ShapedSegment(
                        segment=Segment(text="فا", bidi_level=1, start_index=3),
                        glyphs=["alef-ar.fina", "feh-ar.init"],
                        positions=[(0, 0), (0, 0)],
                        advances=[(254, 0), (416, 0)],
                        clusters=[1, 0],
                        width=670,
                    ),
                ],
            )
        ]
        self.assertEqual(pars, expected)

    def test_diacritcs_postions(self):
        pars = self._shaper.shapeTextToParagraphs('وِ')
        expected = [
            ShapedParagraph(
                baseLevel=1,
                segments=[
                    ShapedSegment(
                        segment=Segment(text="وِ", bidi_level=1, start_index=0),
                        glyphs=["kasra-ar", "waw-ar"],
                        positions=[(100, -454), (0, 0)],
                        advances=[(0, 0), (426, 0)],
                        clusters=[1, 0],
                        width=426,
                    )
                ],
            )
        ]
        self.assertEqual(pars, expected)

if __name__ == '__main__':
    unittest.main()