from fontGadgets.tools import fontMethod

@fontMethod
def _autoOrder(component):
    return component.baseGlyph, component.transformation
