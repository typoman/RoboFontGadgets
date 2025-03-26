from fontgadgets.decorators import *

MASK_LAYER = 'public.background'

@font_property
def dirPath(layer):
    """
    Returns the abs directory of the layer.
    """
    return layer._glyphSet.fs.getsyspath('/')

@font_property
def background(font):
    try:
        backgroundLayer = font.layers[MASK_LAYER]
    except KeyError:
        backgroundLayer = font.newLayer(MASK_LAYER)
    return backgroundLayer

