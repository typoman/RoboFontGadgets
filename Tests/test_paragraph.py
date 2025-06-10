from utils import *
from fontgadgets.extensions.layout.paragraph import *
from fontgadgets.extensions.layout.shaper import HBShaper
import unittest

class ParagraphTest(unittest.TestCase):

    def setUp(self):
        ufo_path = Path(__file__).parent.joinpath("data/ar-font-test-1.ufo")
        font = defcon.Font(ufo_path)
        self.maxDiff = None
        self._shaper = HBShaper(font)

    def shapeTextTooParagraphs(self, txt):
        return self._shaper.shapeTextToParagraphs(txt)

    def assertGlyphLinesTextEqual(self, glyphLines, expected):
        result = []
        for gl in glyphLines:
            lineText = []
            for gr in gl.glyphRuns:
                lineText.append(gr.segment.text)
            result.append("".join(lineText))
        actual = "\n".join(result)
        self.assertEqual(expected, actual)

    def test_long_arabic_word(self):
        pars = self.shapeTextTooParagraphs("این نوشـــته بلنده.")
        glyphLines = breakParagraphsUsingLineWidth(pars, 2000)
        self.assertGlyphLinesTextEqual(glyphLines, 'این \nنوشـــت\nه \nبلنده\n.')

    def test_tiny_line(self):
        pars = self.shapeTextTooParagraphs("چی")
        glyphLines = breakParagraphsUsingLineWidth(pars, 1000)
        self.assertGlyphLinesTextEqual(glyphLines, "")

    def test_long_eng_word(self):
        pars = self.shapeTextTooParagraphs("this loooong word")
        glyphLines = breakParagraphsUsingLineWidth(pars, 2000)
        self.assertGlyphLinesTextEqual(glyphLines, 'this\n lo\nooo\nng \nwor\nd')

    def test_long_bidi_phrase(self):
        pars = self.shapeTextTooParagraphs("/en/خط/fa")
        glyphLines = breakParagraphsUsingLineWidth(pars, 2200)
        self.assertGlyphLinesTextEqual(glyphLines, "/en/\nخط/\nfa")

if __name__ == '__main__':
    unittest.main()