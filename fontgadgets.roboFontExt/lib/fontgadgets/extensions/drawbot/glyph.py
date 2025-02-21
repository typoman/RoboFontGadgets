try:
    from drawBot import *
except ImportError:
    print("Install drawbot!")
from fontTools.pens.cocoaPen import CocoaPen

def drawGlyph(glyph):
	pen = CocoaPen(glyph.font)
	glyph.draw(pen)
	drawPath(pen.path)

