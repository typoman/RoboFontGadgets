from fontTools.feaLib.parser import Parser
from fontTools.feaLib.ast import *
from fontTools.feaLib.error import FeatureLibError
from fontgadgets.tools import FontGadgetsError
import fontgadgets.extensions.font
import fontgadgets.extensions.glyph.type
from warnings import warn
from copy import deepcopy
from fontgadgets.decorators import *
from fontgadgets import patch
import os
from io import StringIO

SHIFT = " " * 4


class GlyphFeatures:
    """
    Holds open type feature information for a glyph.

    The GlyphFeatures class makes it possible to fetch substitution rules,
    lookups, and language system related to this specific glyph. It helps in
    understanding how a glyph participates in font features, particularly in
    substitutions. The `sourceGlyphs` and `targetGlyphs` properties are key
    for identifying glyph substitutions.

    Args:
        glyph: The glyph object to analyze features for.

    Properties:
        glyph: The glyph object associated with the features.

        sourceGlyphs: Returns a dictionary mapping tuples of glyph name(s) to a
        list of substitution statements. Each key represents glyph name(s) are
        the glyphs that this glyph is substituted from.

            Example assuming the glyph.Features belongs to the ligature glyph
            "f_i" which is substitued from other glyphs (source).
                {
                    ('f', 'i'): [LigatureSubstStatement],
                }

        targetGlyphs:
        Returns a dictionary mapping tuples of glyph name(s) to lists of
        substitution statements. The target glyphs are the glyphs which
        replace this glyph when a feature is triggered.

            Example assuming the glyph.Features belongs to glyph "f" or "i"
            which are substitued by a ligature (target).
                {
                    ('f_i', ): [LigatureSubstStatement],
                }
        rules: A list of all substitution rules associated with the
            glyph.
        lookups: A list of lookups associated with the glyph's rules.
        languageSystems: A dictionary mapping language system tags
            (script, lang) to lists of rules associated with this glyph.
        numberOfSourceGlyphs: The number of source glyphs involved in
            substitutions that result in this glyph.

    Methods:
        keys(): Returns feature names.
        values(): Returns lists of rules for each feature.
        items(): Returns a dict of {feature name : rule lists}.
        __getitem__(key): Returns the list of rules for a given
            feature name.
        __iter__(): Iterates through feature names.
    """

    def __init__(self, glyph):
        self._glyph = glyph
        self._font = glyph.font
        self._features = {}  # feature.name: [rule, ...]
        self._languageSystems = {}  # (script, lang): [rule, ...]
        self._lookups = []
        self._rules = []
        self._sourceGlyphs = {}  # g.name: [subRule, ...]
        self._targetGlyphs = {}  # g.name: [subRule, ...]
        self._checked_for_num_source_glyphs = {}  # to avoid infinite recursion
        self._featureFile = None

    @property
    def rules(self):
        """
        Returns: A list of all substitution rules for this glyph.
        """
        return self._rules

    @property
    def sourceGlyphs(self):
        return self._sourceGlyphs

    def targetGlyphs(self):
        return self._targetGlyphs

    @property
    def lookups(self):
        """
        Returns: A list of all lookups associated with the substitution rules
            related to this glyph.
        """
        if self._lookups != []:
            return self._lookups
        for r in self.rules:
            if r.lookup not in self._lookups:
                self._lookups.append(r.lookup)
        return self._lookups

    def _getFeatures(self):
        if self._features != {}:
            return self._features
        for r in self.rules:
            for fea in r.lookup.features:
                self._features.setdefault(fea, []).append(r)
        return self._features

    def __iter__(self):
        return iter(self._getFeatures())

    def keys(self):
        return self._getFeatures().keys()

    def values(self):
        return self._getFeatures().values()

    def items(self):
        return self._getFeatures().items()

    def __getitem__(self, key):
        return self._getFeatures()[key]

    @property
    def languageSystems(self):
        """
        Returns: A dictionary where keys are language system tags
            (script, lang) and values are lists of open type substitusion
            rules which are used in those systems.
        """
        if self._languageSystems != {}:
            return self._languageSystems
        for r in self.rules:
            for scriptLang in r.lookup.languageSystems:
                self._languageSystems.setdefault(scriptLang, []).append(r)
        return self._languageSystems

    @property
    def glyph(self):
        return self._glyph

    @property
    def numberOfSourceGlyphs(self):
        return self._getNumberOfSourceGlyphs(self._glyph.name)

    def _getNumberOfSourceGlyphs(self, gname):
        # this can be more complicated than just returning length of any item
        # from features.sourceGlyphs since a ligature could just be a stylistic
        # set of a another ligature or just a base glyph for ligatures
        g = self._font[gname]
        if gname in self._checked_for_num_source_glyphs:
            return self._checked_for_num_source_glyphs[gname]
        for sgnames in g.features._sourceGlyphs:
            num_comp = len(sgnames)
            if not g.isLigature:
                self._checked_for_num_source_glyphs[gname] = num_comp
                return num_comp
            elif num_comp > 1:
                self._checked_for_num_source_glyphs[gname] = num_comp
                return num_comp
            num_comp = 0
            for sg in sgnames:
                sub_num_comp = self._getNumberOfSourceGlyphs(sg)
                num_comp += sub_num_comp
            if num_comp > 1:
                self._checked_for_num_source_glyphs[gname] = num_comp
                return num_comp
        return 0

    @property
    def rulesDict(self):
        """
        Returns:
            dict: A dictionary representation of the rules associated with the
            glyph, organized by feature and language system. The keys of the
            dictionary are feature names (e.g., "liga", "smcp"). Each feature
            name maps to another dictionary where keys are language system
            tuples (script, lang) and values are lists of rule strings in
            Feature File syntax (e.g., "sub f i by f_i;").

            For example, for the glyph "lam_alef-ar" in an Arabic font, the
            `rulesDict` might look like this:

            ```python
            {
                "rlig": {
                    ("DFLT", "dflt"): ["sub lam-ar.init alef-ar.fina by lam_alef-ar;"]
                },
            }
            ```

            This indicates that for the "rlig" feature in the default language
            system, the sequence "lam-ar.init alef-ar.fina" is substituted by
            "lam_alef-ar".
        """

        features = {}
        for rule in self.rules:
            lookup = rule.lookup
            for scriptLang, featuresList in lookup.langsysFeatureMap.items():
                for fea in featuresList:
                    features.setdefault(fea.name, {}).setdefault(
                        scriptLang, []
                    ).append(rule.asFea())
        return features

    def __str__(self):
        return f"<GlyphFeatures: {str(self.rulesDict)}>"


@font_property
def features(glyph):
    """
    Returns:
        GlyphFeatures: The GlyphFeatures object for this glyph.
    """
    return glyph.font.features.parsed[glyph.name]


def getParsedFontToolsFeatureFile(
    font, featureFilePath=None, followIncludes=True, ignoreMissingGlyphs=True
):
    if featureFilePath is None:
        featxt = font.features.text or ""
    else:
        try:
            with open(featureFilePath, "r", encoding="utf-8") as feaFile:
                featxt = feaFile.read()
        except FileNotFoundError:
            return

    buf = StringIO(featxt)
    ufoPath = font.path
    includeDir = None
    if ufoPath is not None:
        ufoPath = os.path.normpath(ufoPath)
        buf.name = os.path.join(ufoPath, "features.fea")
        includeDir = os.path.dirname(ufoPath)
    glyphNames = ()
    if not ignoreMissingGlyphs:
        glyphNames = tuple(font.keys())
    return Parser(
        buf, glyphNames=glyphNames, includeDir=includeDir, followIncludes=followIncludes
    ).parse()


class NamelessLookup(LookupBlock):
    """A lookup that doesn't exist in feature file source, but it will be
    build at compile.
    """

    def __init__(self, location=None):
        self.name = None
        self.flag = None
        self.location = location
        self.rules = []

    def asFea(self, indent=""):
        indent += SHIFT
        return (
            indent
            + ("\n" + indent).join([s.asFea(indent=indent) for s in self.rules])
            + "\n"
        )


DFLT_LANGUAGE = LanguageStatement("dflt")
DFLT_SCRIPT = ScriptStatement("DFLT")
DFLT_LANGSYS = LanguageSystemStatement("DFLT", "dflt")


@patch.method(LanguageSystemStatement)
def __iter__(self):
    # for unpacking
    return iter((ScriptStatement(self.script), LanguageStatement(self.language)))


class ParsedFeatureFile:
    gsubGlyphsAttrs = {
        # one to one, alternate shapes of a glyph
        AlternateSubstStatement: ("glyph", "replacement"),
        # one to many, decomposing one glyph to many glyphs
        MultipleSubstStatement: ("glyph", "replacement"),
        # many to one, ligatures
        LigatureSubstStatement: ("glyphs", "replacement"),
        # one to one, alternate shapes of a glyph
        SingleSubstStatement: ("glyphs", "replacements"),
        # one to one, alternate shapes of a glyph
        ReverseChainSingleSubstStatement: ("glyphs", "replacements"),
    }

    gsubChainGlyphAttrs = {
        ChainContextSubstStatement: ("prefix", "glyphs", "suffix"),
    }

    gposGlyphsAttrs = {
        CursivePosStatement: ("glyphs",),
        MarkBasePosStatement: ("base",),
        MarkLigPosStatement: ("ligatures",),
        MarkMarkPosStatement: ("baseMarks",),
        PairPosStatement: (
            "glyphs1",
            "glyphs2",
        ),
        SinglePosStatement: ("pos",),
    }

    gposChainGlyphAttrs = {
        ChainContextPosStatement: ("prefix", "glyphs", "suffix"),
    }

    rules = tuple(
        statement_type
        for rule_dict in [
            gsubGlyphsAttrs,
            gsubChainGlyphAttrs,
            gposGlyphsAttrs,
            gposChainGlyphAttrs,
        ]
        for statement_type in rule_dict.keys()
    )

    def __init__(
        self, font, featureFilePath=None, followIncludes=True, ignoreMissingGlyphs=True
    ):
        self._font = font
        self.featureFile = getParsedFontToolsFeatureFile(
            font,
            featureFilePath=featureFilePath,
            followIncludes=followIncludes,
            ignoreMissingGlyphs=ignoreMissingGlyphs,
        )
        self.namedLookups = {}  # lookupName: [ast.LookupBlock, ...]
        self.classes = {}  # className: ast.GlyphClassDefinition
        self.features = {}  # featureName: [ast.FeatureBlock, ...]
        self.languageStatements = {}  # (script, language): ast.LanguageSystemStatement
        self._lookups = {}  # (fea, scr, lan): [lookup, ...]
        self._featureReferences = {}  # featureName: [ast.FeatureBlock, ...]
        self._rules = {}  # statementType: [astObject,...]
        self._currentFeature = None
        self._currentLanguage = DFLT_LANGUAGE
        self._currentScript = DFLT_SCRIPT
        self._currentBlock = None
        self._seenNonDFLTScript = False
        self._currentLookup = None
        self._currentlanguageSystems = {}
        self._glyphFeatures = {}
        self._currentElement = self.featureFile
        self._parseStatements(self.featureFile)
        for feaTag, feaRefList in self._featureReferences.items():
            for feaRef in feaRefList:
                feaRef.featureBlocks = self.features[feaTag]
            for featureBlock in self.features[feaTag]:
                self._appendToListAttribute(featureBlock, "references", feaRefList)
        self._currentElement = None

    def _parseElement(self, e):
        self._currentElement = e
        e.block = self._currentBlock
        match e:
            case LanguageSystemStatement():
                self.addLanguageSystem(e)
            case FeatureBlock():
                self.setFeature(e)
            case NestedBlock():
                self._parseStatements(e)
            case LookupBlock():
                self.startNamedLookup(e)
                self._parseStatements(e)
                self.endNamedLookupBlock()
            case LookupFlagStatement():
                self._currentLookupFlag = e
            case LookupReferenceStatement(lookup=lookup):
                self.addLookupCall(lookup.name)
            case GlyphClassDefinition(name=name):
                self.classes[name] = e
            case _ if isinstance(e, self.rules):
                self._rules.setdefault(type(e), []).append(e)
                self.setLookupForRule(e)
                self._parseStatementAttributes()
            case LanguageStatement():
                self.setLanguage(e)
            case ScriptStatement():
                self.setScript(e)
            case GlyphClassName(glyphclass=glyphclass):
                self._appendToListAttribute(glyphclass, "references", e)
            case FeatureReferenceStatement(featureName=featureName):
                self._featureReferences.setdefault(featureName, []).append(e)

    def addLanguageSystem(self, languageSystemStatement):
        location = languageSystemStatement.location
        scriptLang = (languageSystemStatement.script, languageSystemStatement.language)

        if scriptLang == ("DFLT", "dflt") and self.languageStatements:
            raise FeatureLibError(
                'If "languagesystem DFLT dflt" is present, it must be '
                "the first of the languagesystem statements",
                location,
            )

        if languageSystemStatement.script == "DFLT":
            if self._seenNonDFLTScript:
                raise FeatureLibError(
                    'languagesystems using the "DFLT" script tag must '
                    "precede all other languagesystems",
                    location,
                )
        else:
            self._seenNonDFLTScript = True

        if scriptLang in self.languageStatements:
            raise FeatureLibError(
                '"languagesystem %s %s" has already been specified' % scriptLang,
                location,
            )
        self.languageStatements[scriptLang] = languageSystemStatement

    def getDefaultLanguageSystems(self):
        if self.languageStatements:
            return self.languageStatements
        else:
            return {("DFLT", "dflt"): DFLT_LANGSYS}

    def setScript(self, script=None):
        self._currentLookup = None
        if script is None:
            self._currentScript = DFLT_SCRIPT
            self._currentlanguageSystems = self.getDefaultLanguageSystems()
        else:
            self._currentScript = script
            scriptName = self._currentScript.script
        self._currentLanguage = DFLT_LANGUAGE

    def setLanguage(self, language=None):
        self._currentLookup = None
        if language is None:
            self._currentLanguage = DFLT_LANGUAGE
        else:
            self._currentLanguage = language
            languageName = self._currentLanguage.language
            includeDefault = self._currentLanguage.include_default
            scriptName = self._currentScript.script
            scriptLang = (scriptName, languageName)
            feature = self._currentFeature
            defLangLookups = feature.lookups.get((scriptName, "dflt"))
            langSys = (self._currentScript, self._currentLanguage)
            if (languageName == "dflt" or includeDefault) and defLangLookups:
                newLookups = defLangLookups[:]
            else:
                newLookups = feature.lookups.get(scriptLang, [])
            self._currentlanguageSystems = {(scriptName, languageName): langSys}
            for lookup in newLookups:
                self.addCurrentLangSysToLookup(lookup)

    def setFeature(self, feature):
        self._currentFeature = feature
        self._currentLookupFlag = None
        self._currentlanguageSystems = self.getDefaultLanguageSystems()
        self._currentFeature.lookups = {}
        self.features.setdefault(feature.name, []).append(feature)
        self.setScript()
        self._parseStatements(feature)
        self._currentlanguageSystems = {}
        self._currentLookup = None
        self._currentLookupFlag = None

    def startNamedLookup(self, lookup):
        name, location = lookup.name, lookup.location
        if name in self.namedLookups:
            raise FeatureLibError(
                'Lookup "%s" has already been defined' % name, location
            )
        if self._currentFeature.name == "aalt":
            raise FeatureLibError(
                "Lookup blocks cannot be placed inside 'aalt' features; "
                "move it out, and then refer to it with a lookup statement",
                location,
            )
        self.namedLookups[name] = lookup
        self._currentLookup = lookup
        if self._currentFeature is None:
            self._currentLookupFlag = None
        lookup.flag = self._currentLookupFlag
        lookup.rules = []

    def endNamedLookupBlock(self):
        self._currentLookup = None
        if self._currentFeature is None:
            self._currentLookupFlag = None

    def addLookupCall(self, lookupName):
        self._currentLookup = None
        lookup = self.namedLookups[lookupName]
        self.addCurrentLangSysToLookup(lookup)

    def addCurrentLangSysToLookup(self, lookup):
        for scriptLang, langSys in self._currentlanguageSystems.items():
            self._appendToDictAttribute(
                self._currentFeature, "lookups", lookup, scriptLang
            )
            self._appendToDictAttribute(lookup, "languageSystems", langSys, scriptLang)
            self._appendToDictAttribute(
                lookup, "features", self._currentFeature, self._currentFeature.name
            )
            self._appendToDictAttribute(
                lookup, "langsysFeatureMap", self._currentFeature, scriptLang
            )

    def _appendToDictAttribute(self, element, attributeNameInElement, astObject, key):
        if astObject is not None:
            existing = getattr(element, attributeNameInElement, {})
            for existingTags, existingReferences in existing.items():
                for r in existingReferences:
                    if r == astObject:
                        # this element is already referenced
                        return
            existing.setdefault(key, []).append(astObject)
            setattr(element, attributeNameInElement, existing)

    def _appendToListAttribute(self, element, attributeNameInElement, astObject):
        if element is None:
            return
        existing = getattr(element, attributeNameInElement, [])
        existing.append(astObject)
        setattr(element, attributeNameInElement, existing)

    def setLookupForRule(self, rule):
        if self._currentLookup and self._currentLookup.rules:
            if (
                type(rule) is type(self._currentLookup.rules[0])
                and self._currentLookup.flag == self._currentLookupFlag
            ):
                # lookup type is same
                rule.lookup = self._currentLookup
                self._currentLookup.rules.append(rule)
                return

            if (
                type(rule) is not type(self._currentLookup.rules[0])
                and self._currentLookup.name is not None
            ):
                raise FeatureLibError(
                    "Within a named lookup block, all rules must be of "
                    "the same lookup type and flag",
                    rule.location,
                )

        if self._currentLookup is None:
            self._currentLookup = NamelessLookup()
            self._currentLookup.flag = self._currentLookupFlag
            self._currentLookup.location = rule.location

        rule.lookup = self._currentLookup
        self._currentLookup.rules.append(rule)
        if self._currentFeature is not None:
            self.addCurrentLangSysToLookup(self._currentLookup)

    def __getitem__(self, glyphName):
        if glyphName in self._glyphFeatures:
            return self._glyphFeatures[glyphName]
        try:
            self._glyphFeatures[glyphName] = GlyphFeatures(self._font[glyphName])
        except KeyError:
            warn(
                f"Ignoring the missing glyph `{glyphName}` in the features,"
                f"statement:\n{str(self._currentElement)}"
            )
            return
        return self._glyphFeatures[glyphName]

    def _parseStatements(self, element):
        if element is None:
            return
        block = self._currentBlock
        language = self._currentLanguage
        script = self._currentScript
        self._currentBlock = self._currentElement
        for statement in element.statements:
            self._parseElement(statement)
        self._currentBlock = block
        self._currentLanguage = language
        self._currentScript = script

    def _parseStatementAttributes(self):
        # add nested features, lookups, classes, statements attr to RGlyph objects
        statement = self._currentElement
        if type(statement) in self.gsubGlyphsAttrs:
            source, target = self._getGsubStatementGlyphs()
            if isinstance(
                statement,
                (
                    SingleSubstStatement,
                    ReverseChainSingleSubstStatement,
                ),
            ):
                for sg, tg in zip(source, target):
                    self._addGsubAttributesToGlyph([sg], [tg])
            elif isinstance(
                statement,
                (
                    LigatureSubstStatement,
                    MultipleSubstStatement,
                    AlternateSubstStatement,
                ),
            ):
                self._addGsubAttributesToGlyph(source, target)

    def _addGsubAttributesToGlyph(self, sourceGlyphs, targetGlyphs):
        statement = self._currentElement
        sourceGlyphs, targetGlyphs = tuple(sourceGlyphs), tuple(targetGlyphs)
        for gn in targetGlyphs:
            glyphFeatures = self[gn]
            if glyphFeatures is not None:
                glyphFeatures._rules.append(statement)
                glyphFeatures._sourceGlyphs.setdefault(sourceGlyphs, []).append(
                    statement
                )
                glyphFeatures._featureFile = self
        for gn in sourceGlyphs:
            glyphFeatures = self[gn]
            if glyphFeatures is not None:
                glyphFeatures._rules.append(statement)
                glyphFeatures._targetGlyphs.setdefault(targetGlyphs, []).append(
                    statement
                )
                glyphFeatures._featureFile = self

    def _getGsubStatementGlyphs(self):
        statement = self._currentElement
        return [
            self._convertToListOfGlyphNames(getattr(statement, a))
            for a in self.gsubGlyphsAttrs[type(statement)]
        ]

    def _convertToListOfGlyphNames(self, e):
        # we need to make all the glyph statement consistent because feaLib parser
        # sometimes creates ast objects and sometimes string.
        if isinstance(e, str):
            return [
                e,
            ]
        if isinstance(e, GlyphName):
            return [
                e.glyph,
            ]
        if isinstance(e, (list, tuple)):
            result = []
            for e2 in e:
                result.extend(self._convertToListOfGlyphNames(e2))
            return result
        if isinstance(e, GlyphClassName):
            self._appendToListAttribute(
                e.glyphclass, "references", self._currentElement
            )
            return self._convertToListOfGlyphNames(e.glyphclass.glyphs)
        if isinstance(e, GlyphClass):
            e.parent = self._currentElement
            return self._convertToListOfGlyphNames(e.glyphs)
        raise FontGadgetsError(f"Uknown Element: {e}")

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


@font_cached_property("Features.TextChanged", "Layer.GlyphAdded", " Layer.GlyphDeleted")
def parsed(features):
    return ParsedFeatureFile(features.font)


@font_property
def path(features):
    return os.path.join(features.font.path, "features.fea")


def getIncludedFilesPathsFromParseFeatureFile(parsedFeatureFile):
    includeFiles = {}
    for thisStatement in parsedFeatureFile.statements:
        if isinstance(thisStatement, IncludeStatement):
            includeFiles[thisStatement.filename] = thisStatement
    return includeFiles


@font_method
def getIncludedFilesPaths(features, absolutePaths=True):
    """
    Returns a dictionary of {str: fontTools.feaLib.ast.IncludeStatement} of
    the included feature files. If absoulutePaths is True, the abs path of the
    included files will be returned, other wise the path that is used inside
    the feature file.
    """
    font = features.font
    ufoName = font.fontFileName
    ufoRoot = font.folderPath
    parsedFeatureFile = getParsedFontToolsFeatureFile(font, followIncludes=False)
    includeFiles = {}
    for inclFilePath, inclStatement in getIncludedFilesPathsFromParseFeatureFile(
        parsedFeatureFile
    ).items():
        absPath = os.path.join(ufoRoot, inclFilePath)
        normalPath = os.path.normpath(absPath)
        if os.path.exists(normalPath):
            if absolutePaths:
                includeFiles[normalPath] = inclStatement
            else:
                includeFiles[inclFilePath] = inclStatement
        else:
            warn(f"{ufoName} | Feature file doesn't exist in:\n{normalPath}")
    return includeFiles


@font_method
def normalize(features, includeFiles=True):
    """
    Normalizes the feature files using fontTools.fealib parser.
    """
    files = [features.path]
    if includeFiles:
        files.extend(features.getIncludedFilesPaths().keys())
    for feaPath in files:
        normalizedFea = Parser(feaPath, followIncludes=False).parse()
        with open(feaPath, "w", encoding="utf-8") as f:
            f.write(str(normalizedFea))


# caching the following property causes the IsolatedFeatureCompiler to malfunction
@font_property
def defaultScripts(features):
    """
    Returns the default scripts in form of a feature file.
    """
    doc = FeatureFile()
    for s in features.parsed.featureFile.statements:
        if isinstance(s, LanguageSystemStatement):
            if s.language == "dflt" and s.script != "DFLT":
                doc.statements.append(s)
    return doc


@font_method
def getLigatures(font, ligatureFeatureTags=("dlig", "liga", "rlig")):
    """
    Returns names of glyphs which are used inside the given `ligatureFeatureTags`.
    """
    ligatureFeatureTags = set(ligatureFeatureTags)
    result = set()
    for glyph in font:
        if glyph.features.featureTags & ligatureFeatureTags:
            result.add(glyph.name)
            continue
    return result
