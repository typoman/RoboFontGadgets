from fontTools.feaLib.parser import Parser
from fontTools.feaLib.ast import *
from fontTools.feaLib.error import FeatureLibError
from warnings import warn
from copy import deepcopy
from ufo2ft.featureCompiler import FeatureCompiler
from ufo2ft.featureWriters import (
                GdefFeatureWriter,
                CursFeatureWriter,
                KernFeatureWriter,
                MarkFeatureWriter)
from collections import OrderedDict
from fontGadgets.tools import fontMethod, fontCachedMethod
import os
from io import StringIO

"""
- add sctipt and language tags to the rules and glyphs
"""

class GlyphFeautres():

    def __init__(self, glyph):
        self._glyph = glyph
        self.sourceGlyphs = {}  # g.name: AlternateSubstStatement...
        self.targetGlyphs = {}  # g.name: AlternateSubstStatement...

    @property
    def featureTags(self):
        """
        returns a set of tags
        """
        tags = set()
        for gs, sublist in self._glyph.features.sourceGlyphs.items():
            for sub in sublist:
                tags.update([f[0] for f in sub.features])
        return tags

    def _getLookups(self):
        # fetch lookups objects from the statements
        pass

    def _getLanguages(self):
        pass

    def _getScripts(slef):
        pass

    @property
    def glyph(self):
        return self._glyph

@fontMethod
def features(glyph):
    return glyph.font.features.parsed[glyph.name]

def getParsedFontToolsFeatureFile(font, featureFilePath=None, followIncludes=True):
    if featureFilePath is None:
        featxt = font.features.text or ""
    else:
        with open(featureFilePath, "r", encoding="utf-8") as feaFile:
            featxt = feaFile.read()

    buf = StringIO(featxt)
    ufoPath = font.path
    includeDir = None
    if ufoPath is not None:
        ufoPath = os.path.normpath(ufoPath)
        buf.name = os.path.join(ufoPath, "features.fea")
        includeDir = os.path.dirname(ufoPath)
    glyphNames = set(font.keys())
    try:
        return Parser(buf, glyphNames, includeDir=includeDir, followIncludes=followIncludes).parse()
    except FeatureLibError as e:
        logger.error(e)

@fontMethod
def isLigature(glyph):
    if glyph.isMark:
        return False

    for gnames, rules in glyph.features.sourceGlyphs.items():
        for r in rules:
            if isinstance(r, LigatureSubstStatement):
                return True
    return False

class ParsedFeatureFile():

    gsubGlyphsAttrs = {
        # one to one, alternate shapes of a glyph
        AlternateSubstStatement: ('glyph', 'replacement'),
        # one to many, decomposing one glyph to many glyphs
        MultipleSubstStatement: ('glyph', 'replacement'),
        # many to one, ligatures
        LigatureSubstStatement: ('glyphs', 'replacement'),
        # one to one, alternate shapes of a glyph
        SingleSubstStatement: ('glyphs', 'replacements'),
        # one to one, alternate shapes of a glyph
        ReverseChainSingleSubstStatement: ('glyphs', 'replacements'),
    }

    gposGlyphsAttrs = {
        CursivePosStatement: ('glyphs', ),
        MarkBasePosStatement: ('base', ),
        MarkLigPosStatement: ('ligatures', ),
        MarkMarkPosStatement: ('baseMarks', ),
        PairPosStatement: ('glyphs1', 'glyphs2', ),
        SinglePosStatement: ('pos', ),
    }

    rules = list(gsubGlyphsAttrs.keys())
    rules.extend(gposGlyphsAttrs)
    rules = tuple(rules)

    def __init__(self, font, featureFilePath=None, followIncludes=True):
        self._font = font
        self.featureFile = getParsedFontToolsFeatureFile(font, featureFilePath=featureFilePath, followIncludes=followIncludes)
        self.lookups = {}  # lookupName: astLookupBlock
        self.classes = {}  # className: astGlyphClassDefinition
        self.features = {}  # featureTag: [astFeatureBlock, ]
        self.languagesReferences = {}  # languageTag: ast
        self.scriptReferences = {}  # scriptTag: ast
        self.classReferences = {}   # className: ast
        self.featureReferences = {} # featureTag: ast
        self._rules = {}  # statementType: [astObject,...]
        self._currentFeature = None
        self._currentLanguage = None
        self._currentScript = None
        self._currentBlock = None
        self._glyphFeatures = {}
        self._currentElement = self.featureFile
        self._parseStatements()
        for feaTag, feaRefList in self.featureReferences.items():
            for feaRef in feaRefList:
                feaRef.featureBlocks = self.features[feaTag]
        self._currentElement = None

    def _parseElement(self, e):
        self._currentElement = e
        e.block = self._currentBlock
        if isinstance(e, FeatureBlock):
            self._currentFeature = e
            self.features.setdefault(self._currentFeature.name, []).append(e)
            self._parseStatements()
            self._currentFeature = None
            self._currentLanguage = None
            self._currentScript = None
        elif isinstance(e, NestedBlock):
            self._parseStatements()
        elif isinstance(e, LookupBlock):
            self.lookups[e.name] = e
            self._parseStatements()
            self._assignTagReferences(e)
        elif isinstance(e, LookupReferenceStatement):
            self._assignTagReferences(e.lookup)
        elif isinstance(e, GlyphClassDefinition):
            self.classes[e.name] = e
        elif isinstance(e, self.rules):
            self._rules.setdefault(type(e), []).append(e)
            self._assignTagReferences(e)
            self._parseStatementAttributes()
        elif isinstance(e, LanguageStatement):
            self.languagesReferences.setdefault(e.language, []).append(e)
            self._currentLanguage = e
        elif isinstance(e, ScriptStatement):
            self.scriptReferences.setdefault(e.script, []).append(e)
            self._currentScript = e
        elif isinstance(e, GlyphClassName):
            self._assignClassReferences(e.glyphclass)
        elif isinstance(e, FeatureReferenceStatement):
            self.featureReferences.setdefault(e.featureName,  []).append(e)

    def _assignTagReferences(self, e):
        for attr in ('features', 'languages', 'scripts'):
            if not hasattr(e, attr):
                setattr(e, attr, {})
        if self._currentFeature is not None:
            key = (self._currentFeature.name, self._currentFeature.location)
            e.features[key] = self._currentFeature
        if self._currentScript is not None:
            key = (self._currentScript.script, self._currentScript.location)
            e.scripts[key] = self._currentScript
        if self._currentLanguage is not None:
            key = (self._currentLanguage.language, self._currentLanguage.location)
            e.languages[key] = self._currentLanguage

    def _assignClassReferences(self, e):
        # this helps for subsetting when a class is not referenced anymore
        if not hasattr(e, 'references'):
            e.references = []
        e.references.append(self._currentElement)

    def __getitem__(self, glyphName):
        if glyphName in self._glyphFeatures:
            return self._glyphFeatures[glyphName]
        try:
            self._glyphFeatures[glyphName] = GlyphFeautres(self._font[glyphName])
        except KeyError:
            warn(f"Ignoring the missing glyph `{glyphName}` in the features, statement:\n{str(self._currentElement)}")
            return
        return self._glyphFeatures[glyphName]

    def _parseStatements(self):
        block = self._currentBlock = self._currentElement
        language = self._currentLanguage
        script = self._currentScript
        for element in self._currentElement.statements:
            self._parseElement(element)
        self._currentBlock = block
        self._currentLanguage = language
        self._currentScript = script

    def _parseStatementAttributes(self):
        # add nested features, lookups, classes, statements attr to RGlyph objects
        statement = self._currentElement
        if type(statement) in self.gsubGlyphsAttrs:
            source, target = self._getGsubStatementGlyphs()
            if isinstance(statement, (AlternateSubstStatement, SingleSubstStatement, ReverseChainSingleSubstStatement)):
                for sg, tg in zip(source, target):
                    self._addGsubAttributesToGlyph([sg], [tg])
            elif isinstance(statement, (LigatureSubstStatement, MultipleSubstStatement)):
                self._addGsubAttributesToGlyph(source, target)

    def _addGsubAttributesToGlyph(self, sourceGlyphs, targetGlyphs):
        statement = self._currentElement
        sourceGlyphs, targetGlyphs = tuple(sourceGlyphs), tuple(targetGlyphs)
        for gn in targetGlyphs:
            glyphFeatures = self[gn]
            if glyphFeatures is not None:
                glyphFeatures.sourceGlyphs.setdefault(sourceGlyphs, []).append(statement)
        for gn in sourceGlyphs:
            glyphFeatures = self[gn]
            if glyphFeatures is not None:
                glyphFeatures.targetGlyphs.setdefault(targetGlyphs, []).append(statement)

    def _getGsubStatementGlyphs(self):
        statement = self._currentElement
        return [self._convertToListOfGlyphNames(getattr(statement, a)) for a in self.gsubGlyphsAttrs[type(statement)]]

    def _convertToListOfGlyphNames(self, e):
        # we need to make all the glyph statement consistent because feaLib parser
        # sometimes creates ast objects and sometimes string.
        if isinstance(e, str):
            return [e, ]
        if isinstance(e, GlyphName):
            return [e.glyph, ]
        if isinstance(e, (list, tuple)):
            result = []
            for e2 in e:
                result.extend(self._convertToListOfGlyphNames(e2))
            return result
        if isinstance(e, GlyphClassName):
            self._assignClassReferences(e.glyphclass)
            return self._convertToListOfGlyphNames(e.glyphclass.glyphs)
        if isinstance(e, GlyphClass):
            e.parent = self._currentElement
            return self._convertToListOfGlyphNames(e.glyphs)

    def statementsByType(self, elementType, featureTags=set()):
        """
        Get all the elements by type from the feature file. If you provide a featureTags argument,
        then only the statements within those features will be reutrned.
        """
        result = []
        featureTags = self._featureTags(featureTags)
        for element in self._rules.get(elementType, []):
            if element.features & featureTags:
                result.append(element)
        return result

    def _featureTags(self, featureTags):
        if not featureTags:
            return self.features.keys()
        else:
            return set(featureTags)

def _renameGlyphNames(e, trasnlateMap):
    if isinstance(e, str):
        return trasnlateMap.get(e, e)
    elif isinstance(e, GlyphName):
        e = deepcopy(e)
        e.glyph = trasnlateMap.get(e.glyph, e.glyph)
    elif isinstance(e, GlyphClass):
        e.glyphs = _renameGlyphNames(e.glyphs, trasnlateMap)
    elif isinstance(e, list):
        for e2 in e:
            _renameGlyphNames(e2, trasnlateMap)
    return e

@fontCachedMethod("Features.Changed")
def parsed(features):
    return ParsedFeatureFile(features.font)

#  subsetting
"""
Todo:
KNOWN BUGS:
- If these objects are not referenced, they should be removed:
    Classes, LanguageSystemStatement, FeatureReferenceStatement
- if a class doesn't exist it shouldn't be referenced inside another class
    definition.
"""

def _isRule(statement):
    if isinstance(statement,
        (AlternateSubstStatement,
        ChainContextPosStatement,
        ChainContextSubstStatement,
        CursivePosStatement,
        LigatureSubstStatement,
        LookupReferenceStatement,
        LookupBlock,
        MarkBasePosStatement,
        MarkLigPosStatement,
        MarkMarkPosStatement,
        LigatureCaretByIndexStatement,
        LigatureCaretByPosStatement,
        MultipleSubstStatement,
        PairPosStatement,
        ReverseChainSingleSubstStatement,
        SingleSubstStatement,
        SinglePosStatement,
        FeatureReferenceStatement,
        )):
        return True
    return False

def _subsetGlyphs(listOfGlyphSets, glyphsToKeep, appendToResult=True):
    result = []
    for glyphs in listOfGlyphSets:
        if isinstance(glyphs, (list, tuple)):
            result.append(_subsetGlyphs(glyphs, glyphsToKeep, appendToResult=False))
        elif isinstance(glyphs, str):
            if glyphs in glyphsToKeep:
                result.append(glyphs)
            else:
                result.append(None)
        elif glyphs:
            subsetGlyphSet = glyphs.subset(glyphsToKeep)
            if subsetGlyphSet:
                result.append(subsetGlyphSet)
            elif appendToResult:
                result.append([])
        elif appendToResult:
            result.append([])
    return result

def _subsetStatements(statementList, glyphsToKeep):
    result = []
    for statement in statementList:
        if statement.subset(glyphsToKeep):
            result.append(statement)
    return result

def elementSubset(self, glyphsToKeep):
    return self

def glyphNameSubset(self, glyphsToKeep):
    if self.glyph in glyphsToKeep:
        return self

def glyphClassSubset(self, glyphsToKeep):
    remainedGlyphs = []
    for g in self.glyphs:
        if hasattr(g, 'subset'):
            if g.subset(glyphsToKeep):
                remainedGlyphs.append(g)
        elif g in glyphsToKeep:
            remainedGlyphs.append(g)
    self.glyphs = remainedGlyphs
    if self.glyphs:
        return self

def glyphClassNameSubset(self, glyphsToKeep):
    self.glyphclass = self.glyphclass.subset(glyphsToKeep)
    if self.glyphclass:
        return self

def glyphClassDefinitionSubset(self, glyphsToKeep):
    if self.glyphs:
        self.glyphs = self.glyphs.subset(glyphsToKeep)
        if self.glyphs:
            return self

def markClassSubset(self, glyphsToKeep):
    remainedGlyphs = {}
    for glyph, mark in self.glyphs.items():
        result = _subsetGlyphs([glyph], glyphsToKeep)
        if result:
            remainedGlyphs[glyph] = mark
    self.glyphs = remainedGlyphs
    if self.glyphs:
        return self

def markClassNameSubset(self, glyphsToKeep):
    self.markClass = self.markClass.subset(glyphsToKeep)
    if self.markClass:
        return self

def markClassDefinitionSubset(self, glyphsToKeep):
    self.glyphs, self.markClass = _subsetGlyphs([
    self.glyphs, self.markClass], glyphsToKeep)
    if self.glyphs and self.markClass:
        return self

def blockSubset(self, glyphsToKeep):
    self.statements = _subsetStatements(self.statements, glyphsToKeep)

def glyphClassDefStatementSubset(self, glyphsToKeep):
    self.baseGlyphs, self.markGlyphs, self.ligatureGlyphs, self.componentGlyphs = _subsetGlyphs([
    self.baseGlyphs, self.markGlyphs, self.ligatureGlyphs, self.componentGlyphs], glyphsToKeep, appendToResult=True)
    if self.baseGlyphs or self.markGlyphs or self.ligatureGlyphs or self.componentGlyphs:
        return self

def alternateSubstStatementSubset(self, glyphsToKeep):
    self.prefix, self.glyph, self.suffix, self.replacement = _subsetGlyphs([
    self.prefix, self.glyph, self.suffix, self.replacement], glyphsToKeep)
    if self.glyph and self.replacement:
        return self

def numInputGlyphs(self):
    if hasattr(self, 'glyphs'):
        return len(self.glyphs)
    return len(self.glyph)

def chainContextStatementSubset(self, glyphsToKeep):
    self.prefix, self.glyphs, self.suffix = _subsetGlyphs([
    self.prefix, self.glyphs, self.suffix], glyphsToKeep)
    if self.glyphs:
        remainedLookups = []
        numInputGlyphs = len(self.glyphs.glyphSet())
        for lookup in self.lookups:
            if lookup.subset(glyphsToKeep):
                lookupStatements = []
                for s in lookup.statements:
                    if hasattr(s, 'numInputGlyphs'):
                        if s.numInputGlyphs() != numInputGlyphs:
                            continue
                    lookupStatements.append(s)
                lookup.statements = lookupStatements
            if not lookup.isEmpty():
                self.lookups.append(remainedLookups)
        if self.lookups:
            return self

def ignoreStatementsSubset(self, glyphsToKeep):
    self.chainContexts = _subsetGlyphs(self.chainContexts, glyphsToKeep)
    prefix, glyphs, suffix = self.chainContexts[0]
    if glyphs and (prefix or suffix):
        return self

def ligatureSubstStatementSubset(self, glyphsToKeep):
    numComponents = self.numInputGlyphs()
    self.prefix, self.glyphs, self.suffix, self.replacement = _subsetGlyphs([
    self.prefix, self.glyphs, self.suffix, self.replacement
    ], glyphsToKeep)
    if self.glyphs and self.replacement and self.numInputGlyphs() == numComponents:
        return self

def lookupFlagStatementSubset(self, glyphsToKeep):
    if self.markAttachment is not None:
        self.markAttachment = self.markAttachment.subset(glyphsToKeep)
    if self.markFilteringSet is not None:
        self.markFilteringSet = self.markFilteringSet.subset(glyphsToKeep)
    if self.value or self.markAttachment or self.markFilteringSet:
        return self

def lookupReferenceStatementSubset(self, glyphsToKeep):
    self.lookup = self.lookup.subset(glyphsToKeep)
    if self.lookup:
        return self

def subsetMarks(self, glyphsToKeep):
    remainedMarks = {}
    for anchor, mark in dict(self.marks).items():
        if isinstance(mark, tuple):
            continue
        subsetMarkClass = mark.subset(glyphsToKeep)
        if subsetMarkClass:
            remainedMarks[anchor] = subsetMarkClass
    self.marks = remainedMarks.items()
    if self.marks:
        return self

def markBasePosStatementSubset(self, glyphsToKeep):
    self.base = self.base.subset(glyphsToKeep)
    if self.base:
        return self.subsetMarks(glyphsToKeep)

def markLigPosStatementSubset(self, glyphsToKeep):
    self.ligatures = self.ligatures.subset(glyphsToKeep)
    if self.ligatures:
        return self.subsetMarks(glyphsToKeep)

def markMarkPosStatementSubset(self, glyphsToKeep):
    self.baseMarks = self.baseMarks.subset(glyphsToKeep)
    if self.baseMarks:
        return self.subsetMarks(glyphsToKeep)

def multipleSubstStatementSubset(self, glyphsToKeep):
    if hasattr(self.glyph, 'glyphSet'):
        if self.glyph.subset(glyphsToKeep):
            return
    else:
        if self.glyph not in glyphsToKeep:
            return
    numTargetGlyphs = len(self.replacement.glyphSet())
    self.replacement, self.prefix, self.suffix = _subsetGlyphs([
    self.replacement, self.prefix, self.suffix
    ], glyphsToKeep)
    if len(self.replacement.glyphSet()) == numTargetGlyphs:
        return self

def pairPosStatementSubset(self, glyphsToKeep):
    self.glyphs1, self.glyphs2 = _subsetGlyphs([
    self.glyphs1, self.glyphs2], glyphsToKeep)
    if self.glyphs1 and self.glyphs2:
        return self

def singleSubstStatementSubset(self, glyphsToKeep):
    self.prefix, self.suffix, self.glyphs, self.replacements = _subsetGlyphs([
    self.prefix, self.suffix, self.glyphs, self.replacements], glyphsToKeep)
    if self.glyphs and self.replacements:
        if len(self.glyphs[0].glyphSet()) == len(self.replacements[0].glyphSet()):
            return self
        elif len(self.replacements[0].glyphSet()) == 1 and len(self.glyphs[0].glyphSet()) != 0:
            return self

def reverseSingleSubstStatementSubset(self, glyphsToKeep):
    self.old_prefix, self.old_suffix, self.glyphs, self.replacements = _subsetGlyphs([
    self.old_prefix, self.old_suffix, self.glyphs, self.replacements], glyphsToKeep)
    if self.glyphs and self.replacements:
        if len(self.glyphs[0].glyphSet()) == len(self.replacements[0].glyphSet()):
            return self
        elif len(self.replacements[0].glyphSet()) == 1 and len(self.glyphs[0].glyphSet()) != 0:
            return self

def singlePosStatementSubset(self, glyphsToKeep):
    inputGlyphSubset = self.pos[0][0].subset(glyphsToKeep)
    self.pos = [(inputGlyphSubset, self.pos[0][-1])]
    if inputGlyphSubset:
        return self

def dropInSubset(self, glyphsToKeep):
    return

def blockRulesSubset(self, glyphsToKeep):
    self.statements = _subsetStatements(self.statements, glyphsToKeep)
    if not self.isEmpty():
        return self

def blockIsEmpty(self):
    # should be used only after _subsetStatements
    for s in self.statements:
        if _isRule(s):
            return False
    return True

def featureReferenceSubset(self, glyphsToKeep):
    if any([feaBlock.subset(glyphsToKeep) is not None for feaBlock in self.featureBlocks]):
        return self

def nestedBlockSubset(self, glyphsToKeep):
    result = []
    for statement in self.block.statements:
        if statement == self:
            continue
        if statement.subset(glyphsToKeep):
            result.append(statement)
    if result:
        return self

LookupBlock.isEmpty = blockIsEmpty
FeatureBlock.isEmpty = blockIsEmpty
Element.subset = elementSubset
GlyphName.subset = glyphNameSubset
GlyphClass.subset = glyphClassSubset
Block.subset = blockSubset
FeatureReferenceStatement.subset = featureReferenceSubset
AttachStatement.subset = glyphClassSubset
LigatureCaretByIndexStatement.subset = glyphClassSubset
LigatureCaretByPosStatement.subset = glyphClassSubset
GlyphClassDefinition.subset = glyphClassDefinitionSubset
GlyphClassName.subset = glyphClassNameSubset
MarkClass.subset = markClassSubset
MarkClassName.subset = markClassNameSubset
MarkClassDefinition.subset = markClassDefinitionSubset
GlyphClassDefStatement.subset = glyphClassDefStatementSubset
AlternateSubstStatement.subset = alternateSubstStatementSubset
ChainContextPosStatement.subset = chainContextStatementSubset
ChainContextSubstStatement.subset = chainContextStatementSubset
CursivePosStatement.subset = glyphClassNameSubset
IgnoreSubstStatement.subset = ignoreStatementsSubset
IgnorePosStatement.subset = ignoreStatementsSubset
LigatureSubstStatement.subset = ligatureSubstStatementSubset
LookupFlagStatement.subset = lookupFlagStatementSubset
LookupReferenceStatement.subset = lookupReferenceStatementSubset
MarkBasePosStatement.subset = markBasePosStatementSubset
MarkLigPosStatement.subset = markLigPosStatementSubset
MarkMarkPosStatement.subset = markMarkPosStatementSubset
MarkBasePosStatement.subsetMarks = subsetMarks
MarkLigPosStatement.subsetMarks = subsetMarks
MarkMarkPosStatement.subsetMarks = subsetMarks
LigatureCaretByIndexStatement.subset = glyphClassSubset
LigatureCaretByPosStatement.subset = glyphClassSubset
MultipleSubstStatement.subset = multipleSubstStatementSubset
PairPosStatement.subset = pairPosStatementSubset
ReverseChainSingleSubstStatement.subset = reverseSingleSubstStatementSubset
SingleSubstStatement.subset = singleSubstStatementSubset
SinglePosStatement.subset = singlePosStatementSubset
SubtableStatement.subset = dropInSubset
LookupBlock.subset = blockRulesSubset
FeatureBlock.subset = blockRulesSubset
NestedBlock.subset = nestedBlockSubset
AlternateSubstStatement.numInputGlyphs = numInputGlyphs
LigatureSubstStatement.numInputGlyphs = numInputGlyphs
CursivePosStatement.numInputGlyphs = numInputGlyphs
MarkBasePosStatement.numInputGlyphs = numInputGlyphs
MarkLigPosStatement.numInputGlyphs = numInputGlyphs
MarkMarkPosStatement.numInputGlyphs = numInputGlyphs
MultipleSubstStatement.numInputGlyphs = numInputGlyphs
PairPosStatement.numInputGlyphs = numInputGlyphs
SingleSubstStatement.numInputGlyphs = numInputGlyphs
SinglePosStatement.numInputGlyphs = numInputGlyphs

@fontCachedMethod("Features.Changed")
def subset(features, glyphsToKeep=None, subsetIncludedFiles=True):
    """
    Return a new features text file with features limited to the glyphsToKeep. If subsetIncludedFiles
    is True then all the included files will be overwritten with the new subset features.
    """
    files = set([features.path, ])
    if subsetIncludedFiles:
        files.update(features.getIncludedFilesPaths())
    font = features.font
    if glyphsToKeep is None:
        glyphsToKeep = set(font.keys()) - set(font.lib.get("public.skipExportGlyphs", []))

    for featureFilePath in files:
        parsed = ParsedFeatureFile(features.font, featureFilePath, followIncludes=False)
        parsed.featureFile.subset(glyphsToKeep)
        with open(featureFilePath, "w", encoding="utf-8") as oldFile:
            oldFile.write(str(parsed.featureFile))

@fontMethod
def path(features):
    return os.path.join(features.font.path, "features.fea")

@fontMethod
def getIncludedFilesPaths(features, absolutePaths=True):
    """
    Returns paths of included feature files.
    If absoulutePaths is True, the abs path of the included files will be returned,
    other wise the path that is used inside the feature file.
    """
    includeFiles = set()
    font = features.font
    parsed = getParsedFontToolsFeatureFile(font, followIncludes=False)
    ufoName = font.fontFileName
    ufoRoot = font.folderPath
    for s in parsed.statements:
        if isinstance(s, IncludeStatement):
            path = os.path.join(ufoRoot, s.filename)
            normalPath = os.path.normpath(path)
            if os.path.exists(normalPath):
                if absolutePaths:
                    includeFiles.add(normalPath)
                else:
                    includeFiles.add(s.filename)
            else:
                warn(f"{ufoName} | Feature file doesn't exist in:\n{normalPath}")
    return includeFiles

class IsolatedFeatureCompiler(FeatureCompiler):
    """
    overrides ufo2ft to exclude ufo existing features in the generated GPOS.
    """

    def setupFeatures(self):
        featureFile = self.ufo.features.defaultScripts # ufo2ft requires default scripts to function properly
        lenExtraScripts = len(self.ufo.features.defaultScripts.asFea())
        for writerClass in self.featureWriters:
            writerClass().write(self.ufo, featureFile, compiler=self)
        self.features = featureFile.asFea()[lenExtraScripts+1:]

@fontMethod
def getCompiler(features, featureWriters=None, ttFont=None, glyphSet=None):
    """
    Returns a `ufo2ft.featureCompiler.FeatureCompiler` based on the given featurewitres.
    """
    font = features.font
    skipExport = font.lib.get("public.skipExportGlyphs", [])
    glyphOrder = (gn for gn in font.glyphOrder if gn not in skipExport)
    if featureWriters is not None:
        featuresCompiler = IsolatedFeatureCompiler(font, ttFont=ttFont, glyphSet=glyphSet, featureWriters=featureWriters)
        featuresCompiler.featureWriters = featureWriters
    else:
        featuresCompiler = FeatureCompiler(font, ttFont=ttFont, glyphSet=glyphSet, featureWriters=featureWriters)
    featuresCompiler.glyphSet = OrderedDict((gn, font[gn]) for gn in glyphOrder)
    featuresCompiler.compile()
    return featuresCompiler

@fontCachedMethod("Kerning.Changed", "Layer.GlyphAdded", "Layer.GlyphDeleted")
def kern(features):
    """
    Compiled kerning feature using ufo2ft.
    """
    return features.getCompiler([KernFeatureWriter, GdefFeatureWriter]).features

@fontCachedMethod("Glyph.AnchorsChanged", "Layer.GlyphAdded", "Layer.GlyphDeleted")
def mark(features):
    """
    Compiled mark feature using ufo2ft.
    """
    return features.getCompiler([MarkFeatureWriter, ]).features

@fontMethod
def gdef(features):
    """
    Compiled GDEF feature using ufo2ft.
    """
    return features.getCompiler([GdefFeatureWriter, ]).features

@fontCachedMethod("Glyph.AnchorsChanged", "Layer.GlyphAdded", "Layer.GlyphDeleted")
def curs(features):
    """
    Compiled cursive attatchment feature using ufo2ft.
    """
    return features.getCompiler([CursFeatureWriter, ]).features

@fontMethod
def normalize(features, includeFiles=True):
    """
    Normalizes the feature files using fontTools.fealib parser.
    """
    files = [features.path]
    if includeFiles:
        files.extend(features.getIncludedFilesPaths())
    for feaPath in files:
        normalizedFea = Parser(featureFilePath, followIncludes=False).parse()
        with open(feaPath, "w", encoding="utf-8") as f:
            f.write(str(normalizedFea))

# caching the following property causes the IsolatedFeatureCompiler to malfunction
@fontMethod
def defaultScripts(features):
    """
    Returns the default scripts in form of a feature file.
    """
    doc = FeatureFile()
    for s in features.parsed.featureFile.statements:
        if isinstance(s, LanguageSystemStatement):
            if s.language == 'dflt' and s.script != 'DFLT':
                doc.statements.append(s)
    return doc
