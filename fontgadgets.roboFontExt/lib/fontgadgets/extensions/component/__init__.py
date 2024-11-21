from fontgadgets.decorators import *

# component.transformation should be replaced with a relative position (to the
# bounds) and relative size to the bounds ratio
@font_property
def _autoOrderIndex(component):
    return component.baseGlyph, component.transformation
