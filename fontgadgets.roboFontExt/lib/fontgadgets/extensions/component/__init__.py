from fontgadgets.decorators import *

@font_property
def _autoOrderIndex(component):
    return component.baseGlyph, component.transformation
