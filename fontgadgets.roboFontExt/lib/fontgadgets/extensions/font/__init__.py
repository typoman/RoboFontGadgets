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

@font_method
def renameGlyphs(font, rename_map):
    """
    Rename glyphs using dict of {old_name: new_name}.
    """
    old_glyphOrder = font.glyphOrder
    for old_name, new_name in rename_map.items():
        if old_name not in font:
            raise FontGadgetsError(
            f"Glyph `{old_name}` not found in font."
            )
        if new_name in font:
            raise FontGadgetsError(
            f"Renaming from `{old_name}` to `{new_name}`:\n The new name already exists in font."
            )
        if old_name == new_name:
            raise FontGadgetsError(
            f"Renaming glyph to the same name:\n`{old_name}`"
            )

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

    font.glyphOrder = [rename_map.get(g, g) for g in old_glyphOrder]

    for old_name in rename_map.keys():
        del font[old_name]

    font.features.renameGlyphs(rename_map)

@font_method
def copy(font: defcon.Font):
    copyFont = defcon.Font()
    data = font.getDataForSerialization()
    copyFont.setDataFromSerialization(data)
    return copyFont

@font_method
def swapGlyphNames(font, swapMap, component_references=True, kerning_references=True,
                   groups_references=True, glyphorder_references=False, features_references=False,
                   *args, **kwargs):
    """
    Swap glyph data inside the font using a dict of {'glyphName': 'otherGlyphName'}.
    This method swaps the data of the `glyphName` with the given `otherGlyphName`.
    You can choose to swap references to these glyphs as well.

    Args:
        swapMap (dict): contains glyph names that should be swapped in the format
        of {old_name: new_name}

        Font related optional bool args:
            `component_references`: Whether to swap the component references
            inside other glyphs. Defaults to True.
            `kerning_references`: Whether to swap the glyph name references inside
            the kerning. Defaults to True.
            `groups_references`: Whether to swap the glyph name references inside
            the groups. Defaults to True.
            `glyphorder_references`: Whether to swap the glyph name references inside
            the glyphOrder. Defaults to False.

        Glyph related optional bool args:
            `width`: Whether to swap the `Glyph.width` Defaults to True.
            `height`: Whether to swap the `Glyph.height` Defaults to True.
            `unicodes`: Whether to swap the `Glyph.unicodes` Defaults to False.
            `note`: Whether to swap the `Glyph.note` Defaults to True.
            `image`: Whether to swap the `Glyph.image` Defaults to True.
            `contours`: Whether to swap the `Glyph.contours` Defaults to True.
            `components`: Whether to swap the `Glyph.components` Defaults to True.
            `anchors`: Whether to swap the `Glyph.anchors` Defaults to True.
            `guidelines`: Whether to swap the `Glyph.guidelines` Defaults to True.
            `lib`: Whether to swap the `Glyph.lib` Defaults to True.
    """
    interesctionInKeyVaules = set(swapMap.keys()) & set(swapMap.values())
    if interesctionInKeyVaules:
        raise FontGadgetsError(
            f"`swapMap` contains glyph name(s) glyph names both in keys and values:"
            f"{' '.join(interesctionInKeyVaules)}"
            )
    glyphNames = set(font.keys())
    glyphNamesToSwap = swapMap.keys() | swapMap.values()
    diff = glyphNamesToSwap - glyphNames
    if diff != set():
        missing = " ".join(diff)
        raise FontGadgetsError(
            f"`swapMap` contains glyph name(s) that don't exist in font:\n{missing}")

    for name1, name2 in swapMap.items():
        glyph1 = font[name1]
        glyph1.swapGlyphData(font[name2], *args, **kwargs)

    reverseSwapMap = {v: k for k, v in swapMap.items()}
    swapMap.update(reverseSwapMap)

    if component_references:
        affectedComposites = set()
        componentReferenceMap = font.componentReferences
        for name in glyphNamesToSwap:
            references = componentReferenceMap.get(name, set())
            affectedComposites.update(references)

        for compositeGlyphName in affectedComposites:
            compositeGlyph = font[compositeGlyphName]
            for c in compositeGlyph.components:
                c.baseGlyph = swapMap.get(c.baseGlyph, c.baseGlyph)

    if kerning_references:
        newKerning = {}
        for pair, value in font.kerning.items():
            newPair = tuple([swapMap.get(g, g) for g in pair])
            newKerning[newPair] = value
        font.kerning.clear()
        font.kerning.update(newKerning)

    if groups_references:
        newGroups = {}
        for groupName, members in font.groups.items():
            newGroups[groupName] = [swapMap.get(g, g) for g in members]
        font.groups.clear()
        font.groups.update(newGroups)

    if glyphorder_references:
        font.glyphOrder = [swapMap.get(g, g) for g in font.glyphOrder]

    if features_references:
        import fontgadgets.extensions.features.rename
        font.features.renameGlyphs(swapMap)
