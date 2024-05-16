from fontgadgets.decorators import *

FONTPATH_2_GLIFPATHS = {} # todo: cache glifPaths based on fontpaths

class GLIFPaths():

    def __init__(self, layer):
        self._layer = layer
        self._glyphSet = layer._glyphSet
        self._fileName2GlyphName = self._glyphSet.getReverseContents()
        self._glyphName2FileName = self._glyphSet.contents

    def glyphModificationTime(self, glyphName):
        """
        returns the modification time for the given glyphName
        """
        self._glyphSet.getGLIFModificationTime(glyphName)

    def getGlyphFilePath(self, glyphName):
        """
        returns the absolute file path for the given glyphName
        """
        fileName = self._glyphName2FileName[glyphName]
        return self._glyphSet.fs.getsyspath(fileName)

@font_cached_property("Layer.GlyphAdded", "Layer.GlyphDeleted", "Layer.NameChanged", "Layer.GlyphNameChanged")
def glifPaths(layer):
    """
    returns a `GLIFPaths` object for the given layer that can be used to get the
    file path for a glyphName.
    """
    return GLIFPaths(layer)

@font_property
def glifPath(glyph):
    """
    returns the absolute file path for the given `glyphName`
    """
    glifPaths = glyph.layer.glifPaths
    return glifPaths.getGlyphFilePath(glyph.name)

@font_method
def getGlyphForGlifFileName(font, glifFileName, layerName=None):
    """
    returns the glyph name for the given `glifFileName`. `glifFileName` doesn't
    contain the directory path.
    """
    if layerName is None:
        layer = font.layers.defaultLayer
    else:
        layer = font.getLayer(layerName)
    glifPaths = layer.glifPaths
    return glifPaths._fileName2GlyphName[glifFileName]
