from fontgadgets.decorators import *
import fontgadgets.extensions.glyph.scale
from fontTools.misc.roundTools import otRound

_scaleAttribues = [
    "descender",
    "xHeight",
    "capHeight",
    "ascender",
]

@font_method
def scale(font: defcon.Font, factor=1, layer_Names=None, round_values=True):
    """
    Scales the font by a given factor.

    Smaller values than 1 make the font smaller. This method scales
    glyphs, kerning and font info attributes like descender, xHeight,
    capHeight, and ascender.

    Args:
        font (defcon.Font): The font object to be scaled.
        factor (float): The scaling factor. Defaults to 1 (no scaling).
            Values smaller than 1 reduce the size, values larger than 1
            increase the size.
        layer_Names (list, optional): List of layer names to scale. If
            not provided, the default layer will be scaled. Defaults to
            None.
        round_values (bool, optional): Whether to round the scaled values
            to integers. Defaults to True.

    Returns:
        None
    """
    layersToScale = []
    if layer_Names is not None:
        layersToScale = [l for l in font.layers if l.name in layer_Names]
    if layersToScale == []:
        layersToScale = [
            font,
        ]

    for layer in layersToScale:
        for g in layer:
            g.scale(factor, round_values=round_values)
    kerning = dict(font.kerning)
    
    if kerning:
        for k, v in kerning.items():
            v *= factor
            if round_values:
                v = otRound(v)
            kerning[k] = v
    font.kerning.clear()
    font.kerning.update(kerning)

    for a in _scaleAttribues:
        v = getattr(font.info, a) * factor
        if round_values:
            v = otRound(v)
        setattr(font.info, a, v)

    for guideline in font.guidelines:
        for attr in ('x', 'y'):
            v = getattr(guideline, attr) * factor
            if round_values:
                v = otRound(v)
            setattr(guideline, attr, v)
