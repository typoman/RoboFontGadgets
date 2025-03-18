from fontgadgets.decorators import font_cached_method
from fontgadgets.extensions.features import *

"""
TODO:
# Subset undefined markclassess
keep track of defined markclasses, and if they're not defined, subset the positioning rules
following is defining a class
```
markClass [dotbelow-ar] <anchor 0 50> @mark_bottom;
```
following is using it
```
pos base zero.sansSerifCircled  <anchor 409 350> mark @mark_bottom;
```
- prune the unused classes

for merge:
    - how to filter duplicate rules?
"""

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
    if isinstance(self.glyphs, (GlyphName, str)):
        if self.glyphs in glyphsToKeep:
            remainedGlyphs = self.glyphs
    else:
        for g in self.glyphs:
            if hasattr(g, "subset"):
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
    self.glyphs, self.markClass = _subsetGlyphs(
        [self.glyphs, self.markClass], glyphsToKeep
    )
    if self.glyphs and self.markClass:
        return self


def blockSubset(self, glyphsToKeep):
    self.statements = _subsetStatements(self.statements, glyphsToKeep)
    if not self.isEmpty():
        return self


def glyphClassDefStatementSubset(self, glyphsToKeep):
    (
        self.baseGlyphs,
        self.markGlyphs,
        self.ligatureGlyphs,
        self.componentGlyphs,
    ) = _subsetGlyphs(
        [self.baseGlyphs, self.markGlyphs, self.ligatureGlyphs, self.componentGlyphs],
        glyphsToKeep,
        appendToResult=True,
    )
    if (self.baseGlyphs or self.markGlyphs or self.ligatureGlyphs or self.componentGlyphs):
        return self


def alternateSubstStatementSubset(self, glyphsToKeep):
    self.prefix, self.glyph, self.suffix, self.replacement = _subsetGlyphs(
        [self.prefix, self.glyph, self.suffix, self.replacement], glyphsToKeep
    )
    if self.glyph and self.replacement:
        return self


def numInputGlyphs(self):
    if hasattr(self, "glyphs"):
        return len(self.glyphs)
    return len(self.glyph)


def chainContextStatementSubset(self, glyphsToKeep):
    self.prefix, self.glyphs, self.suffix = _subsetGlyphs(
        [self.prefix, self.glyphs, self.suffix], glyphsToKeep
    )
    if self.glyphs:
        remainedLookups = []
        numInputGlyphs = len(self.glyphs.glyphSet())
        for lookup in self.lookups:
            if lookup.subset(glyphsToKeep):
                lookupStatements = []
                for s in lookup.statements:
                    if hasattr(s, "numInputGlyphs"):
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
    self.prefix, self.glyphs, self.suffix, self.replacement = _subsetGlyphs(
        [self.prefix, self.glyphs, self.suffix, self.replacement], glyphsToKeep
    )
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
    if self.lookup:
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
    if hasattr(self.glyph, "glyphSet"):
        if self.glyph.subset(glyphsToKeep):
            return
    else:
        if self.glyph not in glyphsToKeep:
            return
    numTargetGlyphs = len(self.replacement.glyphSet())
    self.replacement, self.prefix, self.suffix = _subsetGlyphs(
        [self.replacement, self.prefix, self.suffix], glyphsToKeep
    )
    if len(self.replacement.glyphSet()) == numTargetGlyphs:
        return self


def pairPosStatementSubset(self, glyphsToKeep):
    self.glyphs1, self.glyphs2 = _subsetGlyphs(
        [self.glyphs1, self.glyphs2], glyphsToKeep
    )
    if self.glyphs1 and self.glyphs2:
        return self


def singleSubstStatementSubset(self, glyphsToKeep):
    self.prefix, self.suffix, self.glyphs, self.replacements = _subsetGlyphs(
        [self.prefix, self.suffix, self.glyphs, self.replacements], glyphsToKeep
    )
    if self.glyphs and self.replacements:
        if len(self.glyphs[0].glyphSet()) == len(self.replacements[0].glyphSet()):
            return self
        elif (
            len(self.replacements[0].glyphSet()) == 1 and len(self.glyphs[0].glyphSet()) != 0
        ):
            return self


def reverseSingleSubstStatementSubset(self, glyphsToKeep):
    self.old_prefix, self.old_suffix, self.glyphs, self.replacements = _subsetGlyphs(
        [self.old_prefix, self.old_suffix, self.glyphs, self.replacements], glyphsToKeep
    )
    if self.glyphs and self.replacements:
        if len(self.glyphs[0].glyphSet()) == len(self.replacements[0].glyphSet()):
            return self
        elif (
            len(self.replacements[0].glyphSet()) == 1 and len(self.glyphs[0].glyphSet()) != 0
        ):
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
    if any(
        [
            isinstance(
                s,
                (
                    AlternateSubstStatement,
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
                    GlyphClassDefStatement,
                    GlyphClassDefinition,
                ),
            )
            for s in self.statements
        ]
    ):
        return False
    return True


def featureReferenceSubset(self, glyphsToKeep):
    if any(
        [feaBlock.subset(glyphsToKeep) is not None for feaBlock in self.featureBlocks]
    ):
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


def featureFileIsEmpty(self):
    if any(
        [
            isinstance(
                s,
                (
                    FeatureBlock,
                    IncludeStatement,
                ),
            )
            for s in self.statements
        ]
    ):
        return self


LookupBlock.isEmpty = blockIsEmpty
FeatureBlock.isEmpty = blockIsEmpty
FeatureFile.isEmpty = featureFileIsEmpty
TableBlock.isEmpty = blockIsEmpty
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


@font_method
def subset(features, glyphsToKeep=None, subsetIncludedFiles=True):
    """
    Returns a dictionary of {path: features} of subset feature files in which the key
    is the path to the feature file and the value is the subset feature file
    contents.
    """
    files = set(
        [
            features.path,
        ]
    )
    if subsetIncludedFiles:
        files.update(features.getIncludedFilesPaths().keys())
    font = features.font
    if glyphsToKeep is None:
        glyphsToKeep = set(font.keys()) - set(
            font.lib.get("public.skipExportGlyphs", [])
        )

    result = {}
    for featureFilePath in files:
        parsed = ParsedFeatureFile(features.font, featureFilePath, followIncludes=False)
        if parsed.featureFile is None:
            continue
        parsed.featureFile.subset(glyphsToKeep)
        if parsed.featureFile:
            result[featureFilePath] = parsed.featureFile
    return result
