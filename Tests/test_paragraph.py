from utils import *
from fontgadgets.extensions.layout.paragraph import *
import unittest
"""
todo
more tests for edge cases, and maybe same phrases with different widths.
"""


class ParagraphTest(unittest.TestCase):

    def setUp(self):
        ufo_path = Path(__file__).parent.joinpath("data/ar-font-test-1.ufo")
        self.font = defcon.Font(ufo_path)
        self.maxDiff = None

    def shapeTextToGlyphLines(self, text, line_width, base_level=0):
        paragraph = Paragraph(baseLevel=base_level, width=line_width)
        paragraph.addTextFromFont(text, self.font)
        paragraph.calculateGlyphLines()
        return paragraph.glyphLines

    def assertGlyphLinesTextEqual(self, glyphLines, expected):
        result = []
        for gl in glyphLines:
            lineText = []
            for gr in gl.glyphRuns:
                lineText.append(gr.segment.text)
            result.append("".join(lineText))
        self.assertEqual(expected, result)

    def test_long_arabic_word(self):
        glyphLines = self.shapeTextToGlyphLines("این نوشـــته بلنده.", 2000)
        self.assertGlyphLinesTextEqual(glyphLines, ['این ', 'نوشـــت', 'ه ', 'بلنده', '.'])

    def test_tiny_line(self):
        glyphLines = self.shapeTextToGlyphLines("چی", 1000)
        self.assertGlyphLinesTextEqual(glyphLines, [])

    def test_long_eng_word(self):
        glyphLines = self.shapeTextToGlyphLines("this loooong word", 2000)
        self.assertGlyphLinesTextEqual(glyphLines, ['this', ' lo', 'ooo', 'ng ', 'wor', 'd'])

    def test_long_bidi_phrase(self):
        glyphLines = self.shapeTextToGlyphLines("/en/خط/fa", 2200)
        self.assertGlyphLinesTextEqual(glyphLines, ["/en/", "خط/", "fa"])

if __name__ == '__main__':
    unittest.main()
