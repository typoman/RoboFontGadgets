from fontTools.misc.transform import Transform
from base import SAVE_EVENTS, LazyGlyphSubscriber, GLYPH_EVENTS, APPLICATION_EVENTS
from RFGadgets.observers.startup import EXTENSION_ID
from mojo.roboFont import AllFonts
import fontgadgets.extensions.glyph.composite

info = """If you move outlines of a glyph that is used in other composites,
their positions in the composites will also move. In most of the time I don't
want this to happen. This script keeps the position of the component fixated
in same place if you move the outline of the base glyph, but if you change the
outlines in any other way (scaling, modifying curves) it will not do any
thing.
"""

BOUNDS_KEY = f"{EXTENSION_ID}.previousBounds"
CHANGES_KEY = f"{EXTENSION_ID}.changed"


class AutoOffsetComponents(LazyGlyphSubscriber):
    debug = False
    checkbox = "Revert Component on Base Glyph Shift"
    description = info

    def build(self):
        for f in AllFonts():
            self.addFont(f)

    def addFont(self, font):
        font.tempLib[CHANGES_KEY] = set()
        # previous bounds doesn't stick in glyph.tempLib after undo, instead using
        # font.tempLib
        if BOUNDS_KEY not in font.tempLib:
            font.tempLib[BOUNDS_KEY] = {}
        for g in font.naked().componentReferences:
            self.addPrevBounds(font[g])

    def fontDocumentDidOpen(self, info):
        super().fontDocumentDidOpen(info)
        f = info["font"]
        self.addFont(f)

    def addPrevBounds(self, glyph):
        if glyph.font is None:
            return
        boundsDict = glyph.font.tempLib.get(BOUNDS_KEY)
        if boundsDict is None:
            boundsDict = {}
            glyph.font.tempLib[BOUNDS_KEY] = boundsDict
        boundsDict[glyph.name] = glyph.bounds

    def _checkIfBaseGlyphMoved(self, base_glyph):
        # check if base_glyph outline has been moved and not scaled or
        # modified in any other way
        font = base_glyph.font
        if font is None:
            return
        boundsDict = font.tempLib.get(BOUNDS_KEY)
        if boundsDict is None:
            boundsDict = {}
            font.tempLib[BOUNDS_KEY] = boundsDict
        currentBounds = base_glyph.bounds
        previousBounds = boundsDict.get(base_glyph.name)
        if previousBounds is None:
            boundsDict[base_glyph.name] = currentBounds
            return
        if currentBounds is None:
            boundsDict[base_glyph.name] = None
            return
        prev_xMin, prev_yMin, prev_xMax, prev_yMax = previousBounds
        curr_xMin, curr_yMin, curr_xMax, curr_yMax = currentBounds
        prev_width = prev_xMax - prev_xMin
        prev_height = prev_yMax - prev_yMin
        curr_width = curr_xMax - curr_xMin
        curr_height = curr_yMax - curr_yMin
        epsilon = 0.001
        if (
            abs(prev_width - curr_width) > epsilon
            or abs(prev_height - curr_height) > epsilon
        ):
            boundsDict[base_glyph.name] = currentBounds
            return
        epsilon = 0.1  # offset needs higher tolerance
        offsetX = curr_xMin - prev_xMin
        offsetY = curr_yMin - prev_yMin
        if abs(offsetX) > epsilon or abs(offsetY) > epsilon:
            offset = (-offsetX, -offsetY)
            self._fixRelatedCompositeComponentPositions(base_glyph, offset)
        boundsDict[base_glyph.name] = currentBounds

    def _fixRelatedCompositeComponentPositions(self, glyph, offset):
        font = glyph.font
        if not font:
            return
        relatedComps = glyph.relatedComposites
        fixed_glyphs = set()
        for compGn in relatedComps:
            if compGn not in font:
                continue
            compG = font[compGn]
            if compG == glyph:
                continue
            compG.prepareUndo("Compensate position of component.")
            didMove = False
            for comp in compG.components:
                if comp.baseGlyph == glyph.name:
                    scaletransformation = list(comp.transformation[:4])
                    newP = offset
                    if scaletransformation != [1.0, 0.0, 0.0, 1.0]:
                        scaletransformation.extend([0, 0])
                        transformPoint = Transform(*scaletransformation).transformPoint
                        newP = transformPoint(offset)
                    comp.moveBy(newP)
                    didMove = True
            if didMove:
                compG.changed()
                compG.performUndo()
                fixed_glyphs.add(compG.name)
        if fixed_glyphs and self.debug:
            print(f"Updated components in: {', '.join(fixed_glyphs)}")

    adjunctGlyphDidChangeOutlineDelay = 0.01

    def adjunctGlyphDidChangeOutline(self, info):
        # collect changes
        glyph = info["glyph"]
        if glyph.relatedComposites:
            glyph.font.tempLib[CHANGES_KEY].add(glyph.name)
            font = glyph.font
            if font is None:
                return
            boundsDict = font.tempLib.get(BOUNDS_KEY)
            if boundsDict is None:
                boundsDict = {}
                font.tempLib[BOUNDS_KEY] = boundsDict
            previousBounds = boundsDict.get(glyph.name)
            if previousBounds is None:
                boundsDict[glyph.name] = glyph.bounds

    def updateChanges(self, info):
        # apply changes on low feedback UI events
        eventName = info.get("subscriberEventName")
        currentGlyph = None
        if eventName in GLYPH_EVENTS:
            currentGlyph = info.get("glyph")
        if currentGlyph is None or eventName in APPLICATION_EVENTS | SAVE_EVENTS:
            # apply changes on everything, user can wait longer
            for f in AllFonts():
                for gn in f.tempLib[CHANGES_KEY]:
                    self._checkIfBaseGlyphMoved(f[gn])
                f.tempLib[CHANGES_KEY] = set()
        else:
            # only update the currentglyph if it's inside one of the
            # relatedComposites of the glyphs from the changes
            cgn = currentGlyph.name
            for f in AllFonts():
                newChanges = set()
                for gn in f.tempLib[CHANGES_KEY]:
                    related = f[gn].relatedComposites
                    if cgn in related:
                        self._checkIfBaseGlyphMoved(f[gn])
                    else:
                        newChanges.add(gn)
                f.tempLib[CHANGES_KEY] = newChanges

