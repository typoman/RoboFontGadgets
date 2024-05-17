from fontgadgets.decorators import *
from fontgadgets.log import logger
from fontTools.ufoLib.glifLib import (readGlyphFromString, GlifLibError)
import fontgadgets.extensions.layer.glifPath
import os
import git as gitPython
from itertools import islice

# seperate dict for fontGit and git.Repo since multiple font could exist in the same repo
FONTPATH_2_GITROOT = {} # {fontPath: gitRoot}
# caching fontGit using the fontGit._repo.root helps to reduce the number of calls to git
GITROOT_2_FONTGIT = {} # {gitRoot: {hash: fontGit}}

class FontGit:
    """
    A class to interact and collect information from a git repo that contains
    font(s).
    """

    def __new__(cls, font):
        # check if an instance of fontGit is already created, if so return it
        gitRoot = FONTPATH_2_GITROOT.get(font.path)
        if gitRoot is not None:
            cachedRepoDict = GITROOT_2_FONTGIT.get(gitRoot)
            if cachedRepoDict is not None:
                # check for last commit hash to see if the repo has changed
                for last_hash, fontGit in cachedRepoDict.items():
                    current_last_commit_hash = fontGit._repo.head.commit.hexsha
                    # assert False, (last_hash, current_last_commit_hash)
                    if current_last_commit_hash == last_hash:
                        return fontGit
            del GITROOT_2_FONTGIT[gitRoot]

        # check if the git.Repo instance has already been created
        repo = gitPython.Repo(font.path, search_parent_directories=True)
        root = repo.working_dir
        last_hash = repo.head.commit.hexsha
        if last_hash not in GITROOT_2_FONTGIT.get(root, {}):
            fontGit = super().__new__(cls)
            fontGit._repo = repo
            fontGit._root = root
            fontGit._fonts = {}
            GITROOT_2_FONTGIT[root] = {last_hash: fontGit}
        else:
            fontGit = GITROOT_2_FONTGIT[root][last_hash]
        FONTPATH_2_GITROOT[font.path] = root
        fontGit._fonts[font.path] = font
        return fontGit

    @property
    def root(self):
        """
        Return the path to the repo root.
        """
        return self._root

    def pathInRepo(self, filePath):
        """
        Removes the repo root from the given absolute `filePath`.
        """
        return filePath.replace(self._root + "/", '')

    def absPathInRepo(self, filePath):
        """
        Adds the repo root to the given `filePath`.
        """
        return os.path.join(self._root, filePath)

    @property
    def modifiedFiles(self):
        diff = self._repo.index.diff(None)
        return [self.absPathInRepo(f.a_path) for f in diff.iter_change_type('M')]

    @property
    def newFiles(self):
        untracked_files = self._repo.untracked_files
        return [self.absPathInRepo(f) for f in untracked_files]

    @property
    def removedFiles(self):
        diff = self._repo.index.diff(None)
        return [self.absPathInRepo(f.a_path) for f in diff.iter_change_type('D')]

    @property
    def commits(self):
        return self._repo.iter_commits()

    def getCommitByIndex(self, index):
        return next(islice(self.commits, index, index + 1))

    def iterCommitsForFilePath(self, filePath):
        """
        Return a list of commits that contain the given `filePath`. `filePath`
        should be absolute file path.
        """
        return self._repo.iter_commits(paths=filePath)

    def getCommitForFilePathByIndex(self, filePath, index):
        """
        Return the commit that contains the given `filePath` at a given `index`.
        The index only iterates the commits for the given `filePath` and does
        not correspond to the all the commits in the repo.
        """
        commits = self.iterCommitsForFilePath(filePath)
        return next(islice(commits, index, index + 1))

    def loadFileAtCommit(self, filePath, commit):
        """
        `filePath` should be absolute file path.
        """
        filePath = self.pathInRepo(filePath)
        try:
            blob = self._repo.commit(commit).tree[filePath]
        except KeyError:
            logger.error(f"File `{filePath}` not found at the given commit `{commit}`.")
            return
        return blob.data_stream.read()

        # ---------------------  Font Related Methods --------------------- #

    def _fontLayersFallback(self, fontPath, layerName):
        """
        if no layerName is provided then return all layers.
        """
        font = self._fonts[fontPath]
        if layerName is None:
            return font.layers
        return [font.getLayer(layerName), ]

    def getModifiedGLyphsForFontPath(self, fontPath, layerName=None):
        """
        Returns a list of glyphs which have been modified in the given
        `layerName` compared to the latest commit for the `fontPath`. If
        `layerName` is None then all layers are checked.

        `fontPath` is the asbolute path to the font.
        `layerName` is the name of the layer.
        """
        return self._getGlyphsForFontLayerFromFileList(fontPath, layerName, self.modifiedFiles)

    def getNewGLyphsForFontPath(self, fontPath, layerName=None):
        """
        Returns a list of glyphs which have been added in the given
        `layerName` compared to the latest commit for the `fontPath`. If
        `layerName` is None then all layers are checked.

        `fontPath` is the asbolute path to the font.
        `layerName` is the name of the layer.
        """
        return self._getGlyphsForFontLayerFromFileList(fontPath, layerName, self.newFiles)

    def _getGlyphsForFontLayerFromFileList(self, fontPath, layerName, files):
        glyphs = []
        for layer in self._fontLayersFallback(fontPath, layerName):
            glyphNames = self._getGLyphNamesForLayerFromFilelist(layer, files)
            glyphs.extend([layer[glyphName] for glyphName in glyphNames])
        return glyphs

    def _getGLyphNamesForLayerFromFilelist(self, layer, filesList):
        # file list is a list of absolute paths files that is glif files
        glyphNames = []
        file2glyphName = layer.glifPaths._fileName2GlyphName # glifFileName doesn't containt dir paths
        layerDirPath = layer.dirPath + "/"
        for filePath in filesList:
            if os.path.splitext(filePath)[-1] == '.glif' and filePath.startswith(layerDirPath):
                glifName = filePath.replace(layerDirPath, '')
                glyphNames.append(file2glyphName[glifName.lower()])
        return glyphNames

    def iterCommitsForFontPathAndGlyphName(self, fontPath, glyphName, layerName=None):
        """
        Iterates the commits for the given `fontPath` and `glyphName`.
        layerName: is optional and is the name of the layer. If no layerName
        is provided then the default layer is checked.
        """
        font = self._fonts[fontPath]
        if layerName is None:
            layer = font.layers.defaultLayer
        else:
            layer = font.getLayer(layerName)
        glyph = layer[glyphName]
        glifPath = glyph.glifPath
        for commit in self.iterCommitsForFilePath(glifPath):
            result = layer.instantiateGlyphObject()
            glyphString = self.loadFileAtCommit(glifPath, commit)
            pointPen = glyph.getPointPen()
            readGlyphFromString(glyphString, glyphObject=targetGlyph, pointPen=pointPen)
            yield result

    def loadPreviousCommitForFontPathAndGlyphName(self, fontPath,
                    glyphName, layerName=None, index=None, targetGlyph=None,
                    clearTarget=True, validate=True):
        """
        Loads a previous commit for the given `fontPath` and `glyphName` and
        returns the glyph object for that commit.

        index: An interger indicating the index of the commit. The higher the
        `index` the older the commit. 0 is the latest commit and the default
        value. The index only iterates the commits for the given `glyphName`
        and does not correspond to all the commits in the repo.

        targetGlyph: is optional to load the result into that glyph. If it is
        not provided a new glyph is returned.

        clearTarget: is optional to clear the glyph before loading.
        """
        font = self._fonts[fontPath]
        if layerName is None:
            layer = font.layers.defaultLayer
        else:
            layer = font.getLayer(layerName)
        glyph = layer[glyphName]
        if targetGlyph is None:
            targetGlyph = layer.instantiateGlyphObject()
        if clearTarget:
            targetGlyph.clear()
        if index is None:
            index = 0
        glifPath = glyph.glifPath
        commit = self.getCommitForFilePathByIndex(glifPath, index)
        glifData = self.loadFileAtCommit(glifPath, commit)
        try:
            readGlyphFromString(
                aString=glifData,
                glyphObject=targetGlyph,
                pointPen=targetGlyph.getPointPen(),
                validate=validate
            )
        except GlifLibError:
            raise
        return targetGlyph

@font_property
def git(font):
    return FontGit(font)
