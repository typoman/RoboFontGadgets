from fontgadgets.decorators import *

@font_property
def dirPath(layer):
    """
    Returns the abs directory of the layer.
    """
    return layer._glyphSet.fs.getsyspath('/')
