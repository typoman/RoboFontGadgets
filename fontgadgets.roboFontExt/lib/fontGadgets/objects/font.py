from fontGadgets.tools import fontMethod
from defcon import Font
from collections import Counter
import os
import shutil
from fontTools.designspaceLib import DesignSpaceDocument
from ufonormalizer import normalizeUFO

def _scaleGlyph(glyph, factor):
    with glyph.undo():
        if glyph.contours:
            for contour in glyph:
                contour.scaleBy(factor)
        for anchor in glyph.anchors:
            anchor.scaleBy(factor)
        for guideline in glyph.guidelines:
            guideline.scaleBy(factor)
        for c in glyph.components:
            xScale, xyScale, yxScale, yScale, xOffset, yOffset = c.transformation
            xOffset *= factor
            yOffset *= factor
            c.transformation = xScale, xyScale, yxScale, yScale, xOffset, yOffset
        glyph.width *= factor

def _scaleRound(v, factor):
    return int(round(v * factor))

_scaleAttribues = [
    "descender",
    "xHeight",
    "capHeight",
    "ascender",
    # "unitsPerEm",
]

@fontMethod
def scale(font, factor=1, layerNames=None, roundValues=True):
    """
    Smalller values than 1 makes the font smaller.
    layerNames: list of name of layers you want to scale, if not provided then
    the default layer will be scaled.
    """
    layersToScale = []
    if layerNames is not None:
        layersToScale = [font.getLayer(l) for l in layerNames]
    if layersToScale == []:
        layersToScale = [font, ]
    for layer in layersToScale:
        for g in layersToScale:
            _scaleGlyph(g, factor)
    if font.kerning:
        font.kerning.scaleBy(factor)
    for a in _scaleAttribues:
        v = getattr(font.info, a)
        setattr(font.info, a, _scaleRound(v, factor))
    if roundValues:
        font.round()
    font.changed()

# Known bugs for subset: sometimes the features don't get subset
# correctly for some unkown issue.

@fontMethod
def subset(font, glyphsToKeep, subsetName=None):
    """
    Subsets and saves the subsetted file into a new folder. `subsetName` will be a folder next to the ufo
    where the subset font will be saved. If this argument is not provided then the most
    common script name in the subset will be used for the folder name.
    """

    glyphsToKeep = [g for g in glyphsToKeep if g in font]
    if subsetName is None:
        scripts = []
        for g in glyphsToKeep:
            scripts.extend(font[g].scripts)
        scriptCounter = Counter(scripts)
        subsetName = scriptCounter.most_common()[0][0]

    subsetUfoPath = f'{font.folderPath}/{subsetName}/{font.fontFileName}'
    shutil.copytree(font.path, subsetUfoPath)
    subsetFont = Font(subsetUfoPath)
    subsetFont.features.text = str(font.features.subset(tuple(sorted(glyphsToKeep))))
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

    subsetFont.lib['public.glyphOrder'] = [gn for gn in subsetFont.glyphOrder if gn in glyphsToKeep]
    if 'com.typemytype.robofont.sort' in subsetFont.lib:
        del subsetFont.lib['com.typemytype.robofont.sort']

    newGroups = {}
    for groupName, glyphList in subsetFont.groups.items():
        glyphList = [g for g in glyphList if g in glyphsToKeep]
        if glyphList:
            newGroups[groupName] = glyphList
    subsetFont.groups.clear()
    subsetFont.groups.update(newGroups)

    newKerning = {}
    for pair, value in subsetFont.kerning.items():
        if subsetFont.kerning.isKerningPairValid(pair):
            newKerning[pair] = value

    subsetFont.kerning.clear()
    subsetFont.kerning.update(newKerning)
    subsetFont.save()
    return subsetFont

@fontMethod
def fontFileName(font):
    """
    Returns the file name of the font file.
    """
    return os.path.basename(font.path)

@fontMethod
def folderPath(font):
    """
    Returns the root path of the font file.
    """
    return os.path.dirname(font.path)

@fontMethod
def designSpaces(font):
    """
    Return the design space files on the root of the font file which
    contain this font as a source.
    """

    designSpaceFiles = {}
    for fontFileName in os.listdir(font.folderPath):
        if fontFileName.endswith(".designspace"):
            designSpaceFile = DesignSpaceDocument.fromfile(os.path.join(font.folderPath, fontFileName))
            for so in designSpaceFile.sources:
                if so.path == font.path:
                    designSpaceFiles[designSpaceFile.path] = designSpaceFile
    return designSpaceFiles

@fontMethod
def normalize(font, includedFeatures=True):
    font.features.normalize(includedFeatures)
    font.save()
    normalizeUFO(font.path, onlyModified=False, writeModTimes=False)

@fontMethod
def ligatures(font, ligatureFeatureTags=("dlig", "liga", "rlig")):
    """
    Returns names of glyphs which are used inside ligature features.
    """
    ligatureFeatureTags = set(ligatureFeatureTags)
    result = set()
    for glyph in font:
        if glyph.features.featureTags & ligatureFeatureTags:
            result.add(glyph.name)
            continue
    return result
