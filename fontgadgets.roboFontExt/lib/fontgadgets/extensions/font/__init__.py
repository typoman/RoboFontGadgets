from fontgadgets.decorators import *
import os
from fontTools.designspaceLib import DesignSpaceDocument
from ufonormalizer import normalizeUFO
from fontgadgets.tools import FontGadgetsError
import fontgadgets.extensions.glyph

@font_property
def fontFileName(font):
    """
    Returns the file name of the font file.
    """
    return os.path.basename(font.path)


@font_property
def folderPath(font):
    """
    Returns the root path of the font file.
    """
    return os.path.dirname(font.path)


@font_property
def designSpaces(font):
    """
    Return the design space files on the root of the font file if it contain
    the font as a source in form of a dictionary: {path: DesignSpaceDocument}
    """

    designSpaceFiles = {}
    for fontFileName in os.listdir(font.folderPath):
        if fontFileName.endswith(".designspace"):
            designSpaceFile = DesignSpaceDocument.fromfile(
                os.path.join(font.folderPath, fontFileName)
            )
            for so in designSpaceFile.sources:
                if so.path == font.path:
                    designSpaceFiles[designSpaceFile.path] = designSpaceFile
    return designSpaceFiles


@font_method
def normalize(font, includedFeatures=True):
    font.features.normalize(includedFeatures)
    font.save()
    normalizeUFO(font.path, onlyModified=False, writeModTimes=False)


@font_cached_property("Layer.GlyphAdded", "Layer.GlyphDeleted")
def cachedGlyphOrder(font):
    """
    Returns cached glyph order.
    """
    return font.glyphOrder

@font_cached_property("UnicodeData.Changed")
def cmap(font):
    """
    Returns cached unicode to glyph name(s) character mapping.
    """
    return font.unicodeData


def renameGlyphs(font, rename_map):
    """
    Rename glyphs using dict of {old_name: new_name}.
    """

    for old_name, new_name in rename_map.items():
        glyph = font[old_name]
        font.insertGlyph(glyph, new_name)

    new_groups = {}
    old_groups = dict(font.groups)
    font.groups.clear()
    for group_name, group_glyphs in old_groups.items():
        new_groups[group_name] = [rename_map.get(g, g) for g in group_glyphs]
    font.groups.update(new_groups)

    new_kerning = {}
    old_kerning = dict(font.kerning)
    for pair, kern_value in old_kerning.items():
        del font.kerning[pair]
        new_pair = tuple([rename_map.get(g, g) for g in pair])
        new_kerning[new_pair] = kern_value
    font.kerning.update(new_kerning)

    for glyph in font:
        for component in glyph.components:
            base_glyph = component.baseGlyph
            component.baseGlyph = rename_map.get(base_glyph, base_glyph)

    font.glyphOrder = [rename_map.get(g, g) for g in font.glyphOrder]

    for old_name in rename_map.keys():
        del font[old_name]


@font_method
def swapGlyphNames(font, swapMap):
    """
    Swap glyph data inside the font using a dict.

    swapMap contains glyph names that should be swapped. {old_name: new_name}
    """
    glyphNames = set(font.keys())
    glyphNamesToSwap = set([g for pair in swapMap.items() for g in pair])
    diff = glyphNamesToSwap - glyphNames
    if diff != set():
        missing = " ".join(diff)
        raise FontGadgetsError(
            f"`swapMap` contains glyph name(s) that don't exist in font:\n{missing}")

    for name1, name2 in swapMap.items():
        glyph1 = font[name1]
        glyph1.swapGlyphData(font[name2])

    reverseSwapMap = {v: k for k, v in swapMap.items()}

    def _swapNames(name):
        return swapMap.get(name, reverseSwapMap.get(name, name))

    # based on ufoProcessor: changes the names in groups the shapes will swap,
    # that will invalidate the kerning so the names need to swap in the kerning
    # as well.
    newKerning = {}
    for pair, value in font.kerning.items():
        newPair = map(_swapNames, pair)
        newKerning[tuple(newPair)] = value
    font.kerning.clear()
    font.kerning.update(newKerning)

    newGroups = {}
    for groupName, members in font.groups.items():
        newGroups[groupName] = list(map(_swapNames, members))
    font.groups.clear()
    font.groups.update(newGroups)
