from fontgadgets.decorators import *
import fontgadgets.extensions.features.subset
import fontgadgets.extensions.kerning

@font_method
def subset(font, glyphsToKeep) -> tuple[defcon.Font, dict]:
    """
    Subsets and returns the subsetted font and included subset feature file(s).
    """

    glyphsToKeep = [g for g in glyphsToKeep if g in font]
    subsetFont = type(font)()
    data = font.getDataForSerialization()
    subsetFont.setDataFromSerialization(data)
    subsetFont.features.text = ""
    subsetFeatures = font.features.subset(tuple(glyphsToKeep))
    glyphsToKeep = set(glyphsToKeep)
    glyphsToRemove = set(subsetFont.keys()) - glyphsToKeep
    componentReferences = subsetFont.componentReferences

    for glyphToRemove in glyphsToRemove:
        decomposeList = componentReferences.get(glyphToRemove, [])
        for glyphName in decomposeList:
            if glyphName in subsetFont:
                glyphToDecompose = subsetFont[glyphName]
                for c in glyphToDecompose.components:
                    if c.baseGlyph == glyphToRemove:
                        glyphToDecompose.decomposeComponent(c)
        for layer in subsetFont.layers:
            if glyphToRemove in layer:
                del layer[glyphToRemove]

    subsetFont.lib["public.glyphOrder"] = [
        gn for gn in subsetFont.glyphOrder if gn in glyphsToKeep
    ]

    newGroups = {}
    for groupName, glyphList in subsetFont.groups.items():
        glyphList = [g for g in glyphList if g in glyphsToKeep]
        if glyphList:
            newGroups[groupName] = glyphList
    subsetFont.groups.clear()
    subsetFont.groups.update(newGroups)

    newKerning = {}
    for pair, value in subsetFont.kerning.items():
        if subsetFont.kerning.isPairValid(pair):
            newKerning[pair] = value

    subsetFont.kerning.clear()
    subsetFont.kerning.update(newKerning)
    return subsetFont, subsetFeatures
