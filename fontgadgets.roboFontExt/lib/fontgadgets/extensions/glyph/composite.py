from fontgadgets.decorators import *
from defcon.objects.component import _defaultTransformation
from fontPens.transformPointPen import TransformPointPen
import fontgadgets.extensions.font

class DecomposePointPen(object):
    def __init__(self, glyphSet, outPointPen):
        self._glyphSet = glyphSet
        self._outPointPen = outPointPen
        self.beginPath = outPointPen.beginPath
        self.endPath = outPointPen.endPath
        self.addPoint = outPointPen.addPoint

    def addComponent(self, baseGlyphName, transformation, identifier):
        if baseGlyphName in self._glyphSet:
            baseGlyph = self._glyphSet[baseGlyphName]
            if transformation == _defaultTransformation:
                baseGlyph.drawPoints(self)
            else:
                transformPointPen = TransformPointPen(self, transformation)
                baseGlyph.drawPoints(transformPointPen)

@font_cached_method(
    "Glyph.ContoursChanged", "Glyph.ComponentsChanged", "Component.BaseGlyphChanged"
)
def decomposeCopy(glyph, layerName=None) -> defcon.Glyph:
    """
    Decomposes the glyph and returns a new copy.
    """
    if layerName is not None:
        try:
            f = glyph.font.layers[layerName]
        except KeyError:
            raise FontGadgetsError(f"Layer: `{layerName}` doesn't eixst!")
    else:
        f = glyph.font.layers.defaultLayer
    result = f.instantiateGlyphObject()
    result.name = glyph.name
    dstPen = result.getPointPen()
    decomposePen = DecomposePointPen(f, dstPen)
    glyph.drawPoints(decomposePen)
    result.copyAttributesFromGlyph(glyph, width=True, height=True, unicodes=True, note=True, image=True, contours=False,
        components=False, anchors=True, guidelines=True, lib=True)
    return result

@font_method
def decompose(glyph: defcon.Glyph):
    glyph.decomposeAllComponents()

@font_property
def relatedComposites(glyph):
    """
    Returns a set of glyph names which is related composites that are using the
    glyph in their components.
    """
    return glyph.font.componentReferences.get(glyph.name, set())
