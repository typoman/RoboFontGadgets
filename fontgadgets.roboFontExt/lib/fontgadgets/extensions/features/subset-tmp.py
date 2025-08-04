from fontgadgets.decorators import *
from fontTools.feaLib import ast
from fontTools.feaLib.parser import Parser

"""
TODO:
- options to keep some features in the subset, for example if subsetters sees arabic script
  tag, they should keep the fina, medi, init, features in the subset and return the glyphs
  which are inside these features.
- by defualt if a rule has context: prefix or suffix, they should not become empty after subset
  otherwise the whole point of contextual rule is lost. we can do it by getting value 1 for each
  and then check if the sum is not chagned after subset.

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

after subseting the glyphs we should start to subset other objects in this order until
there are no changes in any objects.
so probably this should be a while loop which adds an attribute to an object
that indicates what is the index of the iteration, if the index is the same
then there was no changes in the object. Right now it seems comparing the ast objects
needs some work, in case we need to track if their attributes changed? or just check
if the non ast object are changed and return a value indicating that?
Order:
glyphs, rules, classes, lookups, features, class references, feature references

Notes on ast.Parser
parse_glyphclass_
    result = self.ast.NullGlyph(location=self.cur_token_location_)
    result = self.ast.GlyphName(glyph, location=self.cur_token_location_)
    result = self.ast.MarkClassName(gc, location=self.cur_token_location_)
    result = self.ast.GlyphClassName(gc, location=self.cur_token_location_)
    result = self.ast.GlyphClass(location=location)
    result.add_range(
    result.add_range(
    result.add_cid_range(
    result.append(glyph or glyph_name
    gcn = MarkClassName or GlyphClassName.add_class(result
    result.append(gcn

"""


# these are the attributes that can be iterated to find glyph containing objects
_AST_ATTR_TO_ITER = {'statements', 'glyph', 'block', 'componentGlyphs', 'glyphclass', 'glyphs1',
        'glyphs2', 'baseMarks', 'chainContexts', 'glyphs', 'lookups', 'lookup', 'marks',
        'pos', 'markGlyphs', 'markClass', 'baseGlyphs', 'replacement',
        'prefix', 'markAttachment', 'suffix', 'old_suffix', 'featureBlocks', 'subsetMarks',
        'base', 'replacements', 'old_prefix', 'ligatures', 'markFilteringSet',
        'ligatureGlyphs'}

# length of these paired attributes should be same after subset, otherwise rule is not valid
_AST_PAIR_ATTRS = {
    "SingleSubstStatement": ("glyphs", "replacements"),
    "AlternateSubstStatement": ("glyph", "replacement"),
    "ChainContextPosStatement": ("glyphs", {"lookups": "statements"}), # glyph should not be empty, and either of prefix and suffix should not be empty
    "ChainContextSubstStatement": ("glyphs", {"lookups": "statements"}), # same as ChainContextPosStatement
}

AST_RULE_TYPES = (AlternateSubstStatement,
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
                GlyphClassDefinition, )


def getGSUBSoruceAndTargetGlyphs():
    pass

def getContextGlyphs():
    pass

def filterRules(rules):
    for rule in rules:
        if isinstance(rule, AST_RULE_TYPES):
            yield rule

def flattenGlyphs(glyphs):
    # we need to make all the glyph statement consistent because feaLib parser
    # sometimes creates ast objects and sometimes string.
    result = []
    if isinstance(e, str):
        return [e, ]
    if isinstance(e, GlyphName):
        return [e.glyph, ]
    if isinstance(e, (list, tuple)):
        result = []
        for e2 in e:
            result.extend(flattenGlyphs(e2))
        return result
    if isinstance(e, GlyphClassName):
        return self._convertToListOfGlyphNames(e.glyphclass.glyphs)
    if isinstance(e, GlyphClass):
        e.parent = self._currentElement
        return self._convertToListOfGlyphNames(e.glyphs)
    raise FontGadgetsError(f"Uknown Element: {e}")

def getGlyphsFromAttrs(obj, attributeNames):
    result = []
    for attr in attributeNames:
        attr_value = getattr(obj, attr)
        result.append(flattenGlyphs(attr_value))
    return result

def getObjAttrsNumOfGlyphs(obj, attributeNames):
    # In order to check if obj is still valid we need to check the length of the
    # glyphset for some obj attributes after subset. Sometimes chnages in this
    # attr, makes the obj invalid. othertimes, if the length is not a certain
    # amount, then the obj is not valid. Also we need to check if the obj
    # contextual aspect changes after the subset, this will make it invalid.
    result = []
    for attr in attributeNames:
        attr_value = getattr(obj, attr, obj).glyphSet()
        result.append(len(attr_value))
    return result

def astIsInvalid(obj, objAttrGlyphLenBefoerSubset=None):
    if getattr(obj, "_droppedInSubset", False):
        return True
    # check all the attributes recursively based on the object type
    if isinstance(obj, Block):
        rules = filterRules(obj.statements)
        if rules and not all([astIsInvalid(rule) for rule in rules]):
            return False
    elif isinstance(obj, (ChainContextPosStatement, ChainContextSubstStatement)):
        if rules and not all([astIsInvalid(lookup) for lookup in obj.lookups]):
            return False
    elif isinstance(obj, (SingleSubstStatement, ReverseChainSingleSubstStatement)):
        # one to one/alternate shapes of a glyph
        inG, outG = getObjAttrsNumOfGlyphs(obj, ('glyphs', 'replacements'))
        if inG == outG or (inG != 0 and outG == 1):
            return False
    elif isinstance(obj, AlternateSubstStatement):
        # one to one/alternate shapes of a glyph
        inG, outG = getObjAttrsNumOfGlyphs(obj, ('glyph', 'replacement'))
        if inG > 1 and outG > 1:
            return False
    elif isinstance(obj, MultipleSubstStatement):
        # one to many/decomposing
        inG_after, outG_after = getObjAttrsNumOfGlyphs(obj, ('glyph', 'replacement'))
        if inG_after:
            inG_before, outG_before = objAttrGlyphLenBefoerSubset
            if outG_after == outG_before:
                return False
    elif isinstance(obj, LigatureSubstStatement):
        # many to one/decomposing
        inG_after, outG_after = getObjAttrsNumOfGlyphs(obj, ('glyphs', 'replacement'))
        if outG_after:
            inG_before, outG_before = objAttrGlyphLenBefoerSubset
            if inG_before == inG_after:
                return False
    elif isinstance(obj, CursivePosStatement):
        if getObjAttrsNumOfGlyphs(obj, ('glyphclass')):
            return False
    elif isinstance(obj, MarkBasePosStatement):
        if getObjAttrsNumOfGlyphs(obj, ('base')):
            return False
    elif isinstance(obj, MarkLigPosStatement):
        if getObjAttrsNumOfGlyphs(obj, ('ligatures')):
            return False
    elif isinstance(obj, MarkMarkPosStatement):
        if getObjAttrsNumOfGlyphs(obj, ('baseMarks')):
            return False
    elif isinstance(obj, SinglePosStatement):
        if getObjAttrsNumOfGlyphs(obj, ('pos')):
            return False
    elif isinstance(obj, PairPosStatement):
        if sum(getObjAttrsNumOfGlyphs(obj, ('glyphs1', 'glyphs2'))) >= 2:
            return False
    obj._droppedInSubset = True
    self.changed = True
    return True


# these are the attributes that should not be empty/dropped after subset, otherwise ast obj is not valid
_AST_ATTR_MAIN = {
    "GlyphName": ("glyph", ),
    "GlyphClass": ("glyphs", ),
    "Block": ("statements", ),
    "GlyphClassDefinition": ("glyphs", ),
    "GlyphClassDefStatement": ("glyph", ),
    "MarkClass": ("glyphs", ), # {glyphname: ast.MarkClassDefinitions}
    "MarkClassDefinition": ("glyphs", ), # is markclass rename enough?
    "AttachStatement": ("glyphs", ),
    "CursivePosStatement": ("glyphclass", ), # glyphclass is a GlyphClass obj, and if they're drop, this should drop too
    "IgnorePosStatement": ("chainContexts", ), # chainContexts is a 3-tuple and only the middle one is needed to make sure the obj is still valid
    "IgnoreSubstStatement": ("chainContexts", ), # same as IgnorePosStatement
    "LigatureCaretByIndexStatement": ("glyphs", ),
    "LigatureCaretByPosStatement": ("glyphs", ),
    "LigatureSubstStatement": ("prefix", "glyphs", "suffix", "replacement", ),
    "LookupFlagStatement": ("markAttachment", "markFilteringSet", ),
    "MarkBasePosStatement": ("base", ),
    "MarkLigPosStatement": ("ligatures", ),
    "MarkMarkPosStatement": ("baseMarks", ),
    "MultipleSubstStatement": ("prefix", "glyph", "suffix", "replacement", ),
    "PairPosStatement": ("glyphs1", "glyphs2", ),
    "ReverseChainSingleSubstStatement": ("old_prefix", "old_suffix", "glyphs",
                                        "replacements", ),
    "SinglePosStatement": ("pos", ), # it's tricky to subset since could be contextual and used for final adjusments
    }

def _filterNone(iterable):
    for e in iterable:
        if e is not None:
            yield e

def subsetIterable(iterable, glyphsToKeep):
    return list(_filterNone([_subsetGlyphs(obj, glyphsToKeep) for obj in iterable]))

def subsetDict(dictToSubset, glyphsToKeep):
    result = {}
    for k, v in dictToSubset.items():
        subset_key = _subsetIterable(list(dictToSubset.keys()), glyphsToKeep)
        subset_value = _subsetIterable(list(dictToSubset.values()), glyphsToKeep)
        if not any(subset_key or subset_value):
            continue
        result[k] = subset_value
    return result

# Parser.doc_.markClasses {name: ast.MarkClass} # drop name if class is empty or not referenced
# Parser.doc_.markClasses[name].definitions  = [ast.MarkClassDefinition, ...] # drop if empty
# Parser.doc_.markClasses[name].glyphs = {glyphname: ast.MarkClassDefinition} # drop name after glyphname subset
# Parser.lookups_ {name: ast.astLookup} # drop name after lookup block empty or not referenced
# Parser.glyphclasses_ {glyphclassname: ast.GlyphClassDefinition} # drop name if class is empty or not referenced

# how to subset glyph class range? first flatten the group, then subset?

'''


# to add
FeatureTree.default_language_systems_ = set()


lookup.id = all the attributes of a lookup that makes it unique except its rules, including it's order




base class for GlyphRule:
statement.lookup = this can override some of the following
statement.flag = 
statement.markFilterSet = 
statement.featureTags = frozenset(tag1, tag2, ...)
statement.languageSystems = frozenset((script, lang), ...)
statement.prefixContext
statement.suffixContext
statement.ignorePrefixContext
statement.ignoreSuffixContext

statement.id = all the above attributes flattend?

# class for sub
statement.inputGlyphs
statement.outputGlyphs


# class for pos
statement.inputGlyphs
statement.adjustments

# class for 

'''

class FeaturesTree(Parser):
    # subclass of fontTools.feaLib.parser.Parser to make it possible to
    # connect all the fea ast objects togther. All objects need to get a new
    # attr called block in order to know where are they in the feature. Rules
    # need to have lookup attr or languague or script based on the previous
    # statements in order to create a unique id for them. This makes it
    # possible to know if two feature files are merged, we can avoid
    # duplicates.

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.current_block_ = self.doc_
        # any statement or expression should belong to a block, it makes it
        # possible to create a unique id for any expression. Then this id
        # can be used during merge and subset.
        self.current_statement = None
        self.features_ = {}  # {featureTag: [ast.FeatureBlock, ...]} # this is used to check feature references or definitions elsewhere
        self.languages_ = {}  # references for {languageTag: [ast.LanguageStatement, ...]}
        self.scripts_ = {}  # references for {scriptTag: [ast.ScriptStatement, ...]}
        self.classReferences = {}  # className: ast
        self.featureReferences = {}  # featureTag: ast
        self._rules = {}  # statementType: [astObject,...]
        self._currentFeature = None
        self._currentLanguage = None
        self._currentScript = None
        self._currentBlock = None
        self._glyphFeatures = {}
        self._currentElement = self.featureFile
        for feaTag, feaRefList in self.featureReferences.items():
            for feaRef in feaRefList:
                feaRef.featureBlocks = self.features[feaTag]

    def parse_block_(
        self, block, vertical, stylisticset=None, size_feature=False, cv_feature=None
    ):
        previousBlock = self.current_block_
        if hasattr(block, 'tag'):
            self.features_[tag] = block
        self.current_block_ = block
        block.block = previousBlock
        super().parse_block_(block, vertical, stylisticset, size_feature, cv_feature)
        self.current_block_ = previousBlock

    def parse_attach_(self):
        result = super().parse_attach_()
        result.block = self.current_block_

    def parse_glyphclass_(self, accept_glyphname, accept_null=False):
        result = super().parse_glyphclass_(accept_glyphname, accept_null)
        if getattr(result, 'block', None) is None:
            result.block = self.current_block_



class Subsetter(FeaturesTree):

    def subset(self, glyphsToKeep):
        self.subset_iteration_Index_ = 0
        self.changed_in_subset_ = False
        result = self.doc_
        self.glyphsToKeep = glyphsToKeep
        while self.changed:
            self.changed = False
            self.iterationIndex += 1
            result = self.subsetGlyphs(result)
        return result

    def subsetGlyphs(self, objBeforeSubset):
        if isinstance(objBeforeSubset, str):
            if objBeforeSubset not in self.featuresglyphsToKeep:
                self.changed = True
                return
            return objBeforeSubset
        elif isinstance(objBeforeSubset, (list, tuple, set)):
            afterSubset = subsetIterable(objBeforeSubset, self.glyphsToKeep)
            return self.checkAfterSubset(objBeforeSubset, afterSubset)
        elif isinstance(objBeforeSubset, dict):
            afterSubset = subsetDict(objBeforeSubset, self.glyphsToKeep)
            return self.checkAfterSubset(objBeforeSubset, afterSubset)
        elif hasattr(objBeforeSubset, "__dict__"):
            if getattr(objBeforeSubset, "_iterationIndex", -1) != self.iterationIndex:
                if getattr(objBeforeSubset, "_droppedInSubset", False) is True:
                    return
                attributeNames = objBeforeSubset.__dict__.keys() & _AST_ATTR_TO_ITER
                for attributeName in attributeNames:
                    afterSubset = self.subsetGlyphs(getattr(objBeforeSubset, attributeName))
                    if afterSubset is None:
                        objBeforeSubset._droppedInSubset = True
                        return
                    setattr(objBeforeSubset, attributeName, afterSubset)
                objBeforeSubset._iterationIndex = iterationIndex # to avoid recursion
        return objBeforeSubset

    def checkAfterSubset(self, beforeSubset, afterSubset):
        # check if subset has changed the object and whether it is still a valid obj
        if isinstance(beforeSubset, (list, tuple, set, dict)):
            if len(afterSubset) != len(beforeSubset):
                self.changed = True
            if len(afterSubset) == 0:
                return
        # now we need to check if the ast obj is still valid
        return afterSubset

    def checkASTReferences(self, obj):
        # if class or feature or lookup doesn't have references, return None
        # to do this we need to add an attribute to the object that indicates
        # its references
        pass

    def checkEmptyAttrubutes(self, obj):
        # if an attr from an ast obj is None, return None
        pass

    def checkUnpairedAttributes(self, obj):
        # if certain paired attr from a rule doesn't match, return None
        # for exmaple single subst should have same length in source and target
        pass
