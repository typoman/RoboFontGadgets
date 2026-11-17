import vanilla
from mojo.subscriber import (
    registerGlyphEditorSubscriber,
    unregisterGlyphEditorSubscriber,
)
from RFGadgets.observers.startup import EXTENSION_ID
from base import BaseSubscriber
import RFGadgets.UI
from mojo.UI import (
    getDefaultColor,
)
from fontgadgets.extensions.point.geometry import distance


info = """
Shows a line between the counter points.
"""


class DrawDistancesSubscriber(BaseSubscriber):
    """
    Subscriber class to draw distance measurements on the Glyph Editor using Merz.
    """

    debug = False
    checkbox = "Display Twin Points"
    description = info

    def build(self):
        """
        Set up the Merz container and layers for drawing.
        """
        editor = self.getGlyphEditor()
        if editor is None:
            return
        self.container = editor.extensionContainer(
            identifier=f"{EXTENSION_ID}.counterPoints",
            location="foreground",
            clear=True,
        )
        self.baseLayer = self.container.appendBaseSublayer()
        self.linesLayer = self.baseLayer.appendPathSublayer()
        self.textLayer = self.baseLayer.appendTextLineSublayer()
        self.lineColor = getDefaultColor("glyphViewMeasurementsForegroundColor")
        self.textColor = getDefaultColor("glyphViewPointIndexColor")
        self.textBackgroundColor = getDefaultColor("glyphViewPointIndexBackgroundColor")
        self.textSize = 10
        self.lineSize = 1
        if self.debug:
            self.w = vanilla.Window((400, 10), "Debug Window")
            self.w.open()
            self.w.bind("close", self.close)
        self._lines = []
        self.isInteracting = False

    def close(self, _):
        self.terminate()
        self.destroy()

    def destroy(self):
        if not hasattr(self, "container"):
            return
        if self.container:
            self.container.clearSublayers()

    def glyphEditorDidSetGlyph(self, info):
        glyph = info["glyph"]
        self.updateLines(glyph)
        self.drawMeasurementLines()

    glyphEditorGlyphDidChangeSelectionDelay = 0.001

    def glyphEditorGlyphDidChangeSelection(self, info):
        glyph = info["glyph"]
        self.updateLines(glyph)
        self.drawMeasurementLines()

    glyphEditorGlyphDidChangeOutlineDelay = 0.0001

    def glyphEditorGlyphDidChangeOutline(self, _):
        self.drawMeasurementLines()

    glyphEditorDidMouseDownDelay = 0.001

    def glyphEditorDidMouseDown(self, _):
        self.isInteracting = True
        self.drawMeasurementLines()

    glyphEditorDidMouseUpDelay = 0.001

    def glyphEditorDidMouseUp(self, info):
        self.isInteracting = False
        self.updateLines(info["glyph"])
        self.drawMeasurementLines()

    glyphEditorDidKeyDownDelay = 0.001

    def glyphEditorDidKeyDown(self, _):
        self.isInteracting = True
        self.drawMeasurementLines()

    glyphEditorDidKeyUpDelay = 0.001

    def glyphEditorDidKeyUp(self, info):
        self.isInteracting = False
        self.updateLines(info["glyph"])
        self.drawMeasurementLines()

    def updateLines(self, glyph):
        """
        Update the visualization
        """
        if self.isInteracting:
            return
        self._lines = []
        if glyph is None:
            return
        selected_points = glyph.selectedPoints
        glyph = glyph.naked()
        if not selected_points:
            return
        pairs = set()
        for p1 in selected_points:
            p1 = p1.naked()
            p1_id = id(p1)
            p1_pairs = glyph.getTwinPointForPoint(p1)
            for p2 in p1_pairs:
                p2_id = id(p2)
                pair_set = frozenset((p1_id, p2_id))
                if pair_set in pairs:
                    continue
                self._lines.append((p1, p2))
                pairs.add(pair_set)

    def drawMeasurementLines(self):
        """
        Draw a single measurement line and its distance label.

        Args:
            lineObj (line2d): The line object containing start/end points and distance.
        """
        self.container.clearSublayers()
        self.baseLayer = self.container.appendBaseSublayer()

        singleLine = len(self._lines) == 1

        for line in self._lines:
            p1, p2 = line
            startPoint = (p1.x, p1.y)
            endPoint = (p2.x, p2.y)
            midX = startPoint[0] + (endPoint[0] - startPoint[0]) * 0.5
            midY = startPoint[1] + (endPoint[1] - startPoint[1]) * 0.5
            centerPoint = (midX, midY)

            dist = distance(p1, p2)
            displayText = str(int(dist))

            if singleLine:
                dx = abs(endPoint[0] - startPoint[0])
                dy = abs(endPoint[1] - startPoint[1])
                displayText = f"{int(dist)}\n→{int(dx)}  ↑{int(dy)}"

            lineLayer = self.baseLayer.appendLineSublayer()
            textLayer = self.baseLayer.appendTextLineSublayer()
            lineAttributes = dict(strokeColor=self.lineColor, strokeWidth=self.lineSize)
            textAttributes = dict(
                backgroundColor=self.textBackgroundColor,
                fillColor=self.textColor,
                padding=(6, 2),
                cornerRadius=self.textSize * 0.4,
                horizontalAlignment="center",
                verticalAlignment="center",
                pointSize=self.textSize,
                weight="bold",
                figureStyle="tabular",
            )
            lineLayer.setPropertiesByName(lineAttributes)
            lineLayer.setStartPoint(startPoint)
            lineLayer.setEndPoint(endPoint)
            textLayer.setPropertiesByName(textAttributes)
            textLayer.setText(displayText)
            textLayer.setPosition(centerPoint)

    @classmethod
    def activate(cls):
        registerGlyphEditorSubscriber(cls)

    @classmethod
    def deactivate(cls):
        unregisterGlyphEditorSubscriber(cls)


if __name__ == "__main__":
    DrawDistancesSubscriber.debug = True
    registerGlyphEditorSubscriber(DrawDistancesSubscriber)
