from utils import *
from fontgadgets.extensions.features.serialize import *
import unittest
from fontTools.feaLib.parser import Parser
from io import StringIO

GLYPHNAMES = (
    (
        """
    .notdef space A B C D E F G H I J K L M N O P Q R S T U V W X Y Z
    A.sc B.sc C.sc D.sc E.sc F.sc G.sc H.sc I.sc J.sc K.sc L.sc M.sc
    N.sc O.sc P.sc Q.sc R.sc S.sc T.sc U.sc V.sc W.sc X.sc Y.sc Z.sc
    A.swash B.swash X.swash Y.swash Z.swash
    a b c d e f g h i j k l m n o p q r s t u v w x y z
    a.sc b.sc c.sc d.sc e.sc f.sc g.sc h.sc i.sc j.sc k.sc l.sc m.sc
    n.sc o.sc p.sc q.sc r.sc s.sc t.sc u.sc v.sc w.sc x.sc y.sc z.sc
    a.swash b.swash x.swash y.swash z.swash
    foobar foo.09 foo.1234 foo.9876
    one two five six acute grave dieresis umlaut cedilla ogonek macron
    a_f_f_i o_f_f_i f_i f_l f_f_i one.fitted one.oldstyle a.1 a.2 a.3 c_t
    PRE SUF FIX BACK TRACK LOOK AHEAD ampersand ampersand.1 ampersand.2
    cid00001 cid00002 cid00003 cid00004 cid00005 cid00006 cid00007
    cid12345 cid78987 cid00999 cid01000 cid01001 cid00998 cid00995
    cid00111 cid00222
    comma endash emdash figuredash damma hamza
    c_d d.alt n.end s.end f_f
"""
    ).split()
    + ["foo.%d" % i for i in range(1, 200)]
    + ["G" * 600]
)


class AstToDictTest(unittest.TestCase):
    def parse(self, text, glyphNames=GLYPHNAMES, followIncludes=True):
        featurefile = StringIO(text)
        p = Parser(featurefile, glyphNames, followIncludes=followIncludes)
        return p.parse()

    def _select_node(self, doc, selector):
        """Select a node from the AST using a dot-notation selector string."""
        node = doc
        for part in selector.split("."):
            if part.isdigit():
                node = node[int(part)]
            elif part == "glyphs":
                # Special case for glyph classes
                node = node.glyphs
            elif hasattr(node, part):
                node = getattr(node, part)
            elif hasattr(node, "statements"):
                # Try to find in statements if direct attribute doesn't exist
                found = False
                for stmt in node.statements:
                    if hasattr(stmt, part):
                        node = getattr(stmt, part)
                        found = True
                        break
                if not found:
                    raise ValueError(f"Couldn't find node part '{part}'")
            else:
                raise ValueError(f"Couldn't find node part '{part}'")
        return node

    def assertAstToDictEqual(self, feature_text, expected_dict, node_selector=None):
        doc = self.parse(feature_text)
        if isinstance(node_selector, str):
            node = self._select_node(doc, node_selector)
        elif callable(node_selector):
            node = node_selector(doc)
        else:
            node = doc.statements[0]
        self.assertEqual(node.toDict(), expected_dict)

    def test_comment(self):
        self.assertAstToDictEqual("# Initial comment", {"Comment": "# Initial comment"})

    def test_glyphName(self):
        self.assertAstToDictEqual(
            "feature test { sub A by B; } test;",
            {"Glyph": "A"},
            "statements.0.statements.0.glyphs.0",
        )

    def test_glyphClass_simple(self):
        self.assertAstToDictEqual(
            "@myClass = [A B C];",
            {"GlyphClass": [{"Glyph": "A"}, {"Glyph": "B"}, {"Glyph": "C"}]},
            "statements.0.glyphs",
        )

    def test_glyphClass_range(self):
        self.assertAstToDictEqual(
            "@myRange = [A-C];",
            {"GlyphClass": [{"GlyphRange": ({"Glyph": "A"}, {"Glyph": "C"})}]},
            "statements.0.glyphs",
        )

    def test_glyphClass_mixed(self):
        self.assertAstToDictEqual(
            "@myMixed = [X A-C Y];",
            {
                "GlyphClass": [
                    {"Glyph": "X"},
                    {"GlyphRange": ({"Glyph": "A"}, {"Glyph": "C"})},
                    {"Glyph": "Y"},
                ]
            },
            "statements.0.glyphs",
        )

    def test_glyphClassName(self):
        self.assertAstToDictEqual(
            "@myClass = [A B]; feature test { sub @myClass by C; } test;",
            {"ClassName": "myClass"},
            "statements.1.statements.0.glyphs.0",
        )

    def test_anchor_simple(self):
        self.assertAstToDictEqual(
            "feature test { pos cursive A <anchor 120 -20> <anchor NULL>; } test;",
            {"Anchor": {"X": 120, "Y": -20}},
            "statements.0.statements.0.entryAnchor",
        )

    def test_anchor_contourpoint(self):
        self.assertAstToDictEqual(
            "feature test { pos cursive A <anchor 120 -20 contourpoint 5> <anchor NULL>; } test;",
            {"Anchor": {"X": 120, "Y": -20, "ContourPoint": 5}},
            "statements.0.statements.0.entryAnchor",
        )

    def test_anchor_device(self):
        self.assertAstToDictEqual(
            "feature test { pos cursive A <anchor 120 -20 <device 11 111> <device NULL>> <anchor NULL>; } test;",
            {
                "Anchor": {
                    "X": 120,
                    "Y": -20,
                    "XDevice": [{"Size": 11, "Value": 111}],
                }
            },
            "statements.0.statements.0.entryAnchor",
        )

    def test_anchor_named(self):
        self.assertAstToDictEqual(
            "feature test { anchorDef 123 456 foo; pos cursive A <anchor foo> <anchor NULL>; } test;",
            {"Anchor": {"Name": "foo"}},
            "statements.0.statements.1.entryAnchor",
        )

    def test_anchorDefinition(self):
        self.assertAstToDictEqual(
            "anchorDef 123 456 foo;",
            {"AnchorDefinition": {"Name": "foo", "X": 123, "Y": 456}},
        )

    def test_anchorDefinition_contourpoint(self):
        self.assertAstToDictEqual(
            "anchorDef 123 456 contourpoint 5 foo;",
            {
                "AnchorDefinition": {
                    "Name": "foo",
                    "X": 123,
                    "Y": 456,
                    "ContourPoint": 5,
                }
            },
        )

    def test_valueRecord_simple_horiz(self):
        self.assertAstToDictEqual(
            "feature kern { pos A B -50; } kern;",
            {"ValueRecord": {"XAdvance": -50}},
            "statements.0.statements.0.valuerecord1",
        )

    def test_valueRecord_simple_vert(self):
        self.assertAstToDictEqual(
            "feature vkrn { pos A B -50; } vkrn;",
            {"ValueRecord": {"YAdvance": -50, "Vertical": True}},
            "statements.0.statements.0.valuerecord1",
        )

    def test_valueRecord_full(self):
        self.assertAstToDictEqual(
            "feature kern { pos A <1 2 3 4> B; } kern;",
            {
                "ValueRecord": {
                    "XPlacement": 1,
                    "YPlacement": 2,
                    "XAdvance": 3,
                    "YAdvance": 4,
                }
            },
            "statements.0.statements.0.valuerecord1",
        )

    def test_valueRecord_device(self):
        self.assertAstToDictEqual(
            "feature kern { pos A <1 2 3 4 <device 10 100> <device NULL> <device NULL> <device NULL>> B; } kern;",
            {
                "ValueRecord": {
                    "XPlacement": 1,
                    "YPlacement": 2,
                    "XAdvance": 3,
                    "YAdvance": 4,
                    "XPlacementDevice": [{"Size": 10, "Value": 100}],
                }
            },
            "statements.0.statements.0.valuerecord1",
        )

    def test_valueRecordDefinition(self):
        self.assertAstToDictEqual(
            "valueRecordDef 123 foo;",
            {
                "ValueRecordDefinition": {
                    "Name": "foo",
                    "Value": {"ValueRecord": {"XAdvance": 123}},
                }
            },
        )

    def test_markClassName(self):
        self.assertAstToDictEqual(
            "markClass A <anchor 0 0> @MC; @GC = [@MC];",
            {"ClassName": "MC"},
            "statements.1.glyphs.original.0",  # Accessing MarkClassName within GlyphClassDefinition
        )

    def test_anonymousBlock(self):
        self.assertAstToDictEqual(
            "anon TEST {\n content \n} TEST;",
            {"Anonymous": {"Tag": "TEST", "Content": "content"}},
        )

    def test_featureFile(self):
        self.assertAstToDictEqual(
            "# File comment\nfeature liga { sub f i by f_i; } liga;",
            {
                "FeatureFile": {
                    "Statements": [
                        {"Comment": "# File comment"},
                        {
                            "Feature": {
                                "Name": "liga",
                                "Statements": [
                                    {
                                        "LigatureSubstitution": {
                                            "In": [{"Glyph": "f"}, {"Glyph": "i"}],
                                            "Out": {"Glyph": "f_i"},
                                        }
                                    }
                                ],
                            }
                        },
                    ],
                }
            },
            lambda doc: doc,
        )

    def test_featureBlock(self):
        self.assertAstToDictEqual(
            "feature liga useExtension { sub f i by f_i; } liga;",
            {
                "Feature": {
                    "Name": "liga",
                    "UseExtension": True,
                    "Statements": [
                        {
                            "LigatureSubstitution": {
                                "In": [{"Glyph": "f"}, {"Glyph": "i"}],
                                "Out": {"Glyph": "f_i"},
                            }
                        }
                    ],
                }
            },
        )

    def test_nestedBlock(self):
        self.assertAstToDictEqual(
            'feature ss01 { featureNames { name "Alternate"; }; } ss01;',
            {
                "Block": {
                    "Tag": "ss01",
                    "BlockName": "featureNames",
                    "Statements": [
                        {
                            "FeatureName": {
                                "Type": "Name",
                                "String": "Alternate",
                            }
                        }
                    ],
                }
            },
            "statements.0.statements.0",
        )

    def test_lookupBlock(self):
        self.assertAstToDictEqual(
            "lookup MYLOOKUP { sub A by B; } MYLOOKUP;",
            {
                "Lookup": {
                    "Name": "MYLOOKUP",
                    "Statements": [
                        {
                            "SingleSubstitution": {
                                "In": [{"Glyph": "A"}],
                                "Out": [{"Glyph": "B"}],
                            }
                        }
                    ],
                }
            },
        )

    def test_tableBlock(self):
        self.assertAstToDictEqual(
            "table GDEF { GlyphClassDef [A], [f_i], [acute], ; } GDEF;",
            {
                "Table": {
                    "Name": "GDEF",
                    "Statements": [
                        {
                            "GlyphTypeDefinitions": {
                                "BaseGlyphs": {"GlyphClass": [{"Glyph": "A"}]},
                                "LigatureGlyphs": {"GlyphClass": [{"Glyph": "f_i"}]},
                                "MarkGlyphs": {"GlyphClass": [{"Glyph": "acute"}]},
                            }
                        }
                    ],
                }
            },
        )

    def test_glyphClassDefinition(self):
        self.assertAstToDictEqual(
            "@myClass = [A B C];",
            {
                "GlyphDefinitionClass": {
                    "Name": "myClass",
                    "Glyphs": {
                        "GlyphClass": [{"Glyph": "A"}, {"Glyph": "B"}, {"Glyph": "C"}]
                    },
                }
            },
        )

    def test_glyphClassDefStatement(self):
        self.assertAstToDictEqual(
            "table GDEF { GlyphClassDef [A], [f_i], [acute], [C]; } GDEF;",
            {
                "GlyphTypeDefinitions": {
                    "BaseGlyphs": {"GlyphClass": [{"Glyph": "A"}]},
                    "LigatureGlyphs": {"GlyphClass": [{"Glyph": "f_i"}]},
                    "MarkGlyphs": {"GlyphClass": [{"Glyph": "acute"}]},
                    "ComponentGlyphs": {"GlyphClass": [{"Glyph": "C"}]},
                }
            },
            "statements.0.statements.0",
        )

    def test_markClassDefinition(self):
        self.assertAstToDictEqual(
            "markClass acute <anchor 300 500> @TOP_MARKS;",
            {
                "MarkClassDefinition": {
                    "Name": "TOP_MARKS",
                    "Anchor": {"Anchor": {"X": 300, "Y": 500}},
                    "Glyphs": {"Glyph": "acute"},
                }
            },
        )

    def test_alternateSubstStatement(self):
        self.assertAstToDictEqual(
            "feature test { sub a from [a.1 a.2]; } test;",
            {
                "AlternateSubstitution": {
                    "In": {"Glyph": "a"},
                    "Out": {"GlyphClass": [{"Glyph": "a.1"}, {"Glyph": "a.2"}]},
                }
            },
            "statements.0.statements.0",
        )

    def test_attachStatement(self):
        self.assertAstToDictEqual(
            "table GDEF { Attach a 1; } GDEF;",
            {
                "Attach": {
                    "Glyphs": {"Glyph": "a"},
                    "ContourPoints": [1],
                }
            },
            "statements.0.statements.0",
        )

    def test_chainContextPosStatement(self):
        self.assertAstToDictEqual(
            "lookup L { pos A 10; } L; feature test { pos B A' lookup L C; } test;",
            {
                "ChainContextualPositioning": {
                    "Prefix": [{"Glyph": "B"}],
                    "ChainedLookups": [{"Glyph": "A", "Lookups": ["L"]}],
                    "Suffix": [{"Glyph": "C"}],
                }
            },
            "statements.1.statements.0",
        )

    def test_chainContextSubstStatement(self):
        self.assertAstToDictEqual(
            "lookup L { sub A by B; } L; feature test { sub C A' lookup L D; } test;",
            {
                "ChainContextualSubstitution": {
                    "Prefix": [{"Glyph": "C"}],
                    "ChainedLookups": [{"Glyph": "A", "Lookups": ["L"]}],
                    "Suffix": [{"Glyph": "D"}],
                }
            },
            "statements.1.statements.0",
        )

    def test_cursivePosStatement(self):
        self.assertAstToDictEqual(
            "feature curs { pos cursive A <anchor 10 20> <anchor 30 40>; } curs;",
            {
                "CursivePositioning": {
                    "Class": {"Glyph": "A"},
                    "Entry": {"Anchor": {"X": 10, "Y": 20}},
                    "Exit": {"Anchor": {"X": 30, "Y": 40}},
                }
            },
            "statements.0.statements.0",
        )

    def test_featureReferenceStatement(self):
        self.assertAstToDictEqual(
            "feature aalt { feature salt; } aalt;",
            {"FeatureReference": "salt"},
            "statements.0.statements.0",
        )

    def test_ignorePosStatement(self):
        self.assertAstToDictEqual(
            "feature test { ignore pos A B' C; } test;",
            {
                "IgnorePositioning": [
                    {
                        "Prefix": [{"Glyph": "A"}],
                        "Glyphs": [{"Glyph": "B"}],
                        "Suffix": [{"Glyph": "C"}],
                    }
                ]
            },
            "statements.0.statements.0",
        )

    def test_ignoreSubstStatement(self):
        self.assertAstToDictEqual(
            "feature test { ignore sub A B' C; } test;",
            {
                "IgnoreSubstitution": [
                    {
                        "Prefix": [{"Glyph": "A"}],
                        "Glyphs": [{"Glyph": "B"}],
                        "Suffix": [{"Glyph": "C"}],
                    }
                ]
            },
            "statements.0.statements.0",
        )

    def test_includeStatement(self):
        doc = self.parse("include(somefile.fea);", followIncludes=False)
        self.assertEqual(doc.statements[0].toDict(), {"Include": "somefile.fea"})

    def test_scriptStatement(self):
        self.assertAstToDictEqual(
            "feature test { script latn; } test;",
            {"Script": "latn"},
            "statements.0.statements.0",
        )

    def test_languageStatement(self):
        self.assertAstToDictEqual(
            "feature test { language DEU required; } test;",
            {"Language": "DEU", "Required": True},
            "statements.0.statements.0",
        )

    def test_languageSystemStatement(self):
        self.assertAstToDictEqual(
            "languagesystem latn NLD;",
            {"LanguageSystem": {"Script": "latn", "Language": "NLD"}},
            "statements.0",
        )

    def test_fontRevisionStatement(self):
        self.assertAstToDictEqual(
            "table head { FontRevision 1.005; } head;",
            {"FontRevision": 1.005},
            "statements.0.statements.0",
        )

    def test_ligatureCaretByIndexStatement(self):
        self.assertAstToDictEqual(
            "table GDEF { LigatureCaretByIndex f_f_i 2 4; } GDEF;",
            {
                "LigatureCaretByIndex": {
                    "Glyphs": {"Glyph": "f_f_i"},
                    "Carets": [2, 4],
                }
            },
            "statements.0.statements.0",
        )

    def test_ligatureCaretByPosStatement(self):
        self.assertAstToDictEqual(
            "table GDEF { LigatureCaretByPos f_f_i 300 600; } GDEF;",
            {
                "LigatureCaretByPosition": {
                    "Glyphs": {"Glyph": "f_f_i"},
                    "Carets": [300, 600],
                }
            },
            "statements.0.statements.0",
        )

    def test_ligatureSubstStatement(self):
        self.assertAstToDictEqual(
            "feature liga { sub f f i by f_f_i; } liga;",
            {
                "LigatureSubstitution": {
                    "In": [{"Glyph": "f"}, {"Glyph": "f"}, {"Glyph": "i"}],
                    "Out": {"Glyph": "f_f_i"},
                }
            },
            "statements.0.statements.0",
        )

    def test_lookupFlagStatement(self):
        self.assertAstToDictEqual(
            "lookup L { lookupflag IgnoreMarks UseMarkFilteringSet [cedilla]; } L;",
            {
                "LookupFlag": {
                    "Flags": ["IgnoreMarks"],
                    "UseMarkFilteringSet": {"GlyphClass": [{"Glyph": "cedilla"}]},
                }
            },
            "statements.0.statements.0",
        )

    def test_lookupReferenceStatement(self):
        self.assertAstToDictEqual(
            "lookup L {} L; feature test { lookup L; } test;",
            {"LookupReference": "L"},
            "statements.1.statements.0",
        )

    def test_markBasePosStatement(self):
        self.assertAstToDictEqual(
            "markClass acute <anchor 300 500> @TOP; feature test { pos base A <anchor 150 450> mark @TOP; } test;",
            {
                "MarkBasePositioning": {
                    "Base": {"Glyph": "A"},
                    "Marks": [
                        {"Anchor": {"Anchor": {"X": 150, "Y": 450}}, "MarkClass": "TOP"}
                    ],
                }
            },
            "statements.1.statements.0",
        )

    def test_markLigPosStatement(self):
        self.assertAstToDictEqual(
            "markClass acute <anchor 300 500> @TOP; feature test { pos ligature f_f_i <anchor 100 400> mark @TOP ligComponent <anchor 400 400> mark @TOP ligComponent <anchor NULL>; } test;",
            {
                "MarkLigaturePositioning": {
                    "Ligatures": {"Glyph": "f_f_i"},
                    "Marks": [
                        [
                            {
                                "Anchor": {"Anchor": {"X": 100, "Y": 400}},
                                "MarkClass": "TOP",
                            }
                        ],
                        [
                            {
                                "Anchor": {"Anchor": {"X": 400, "Y": 400}},
                                "MarkClass": "TOP",
                            }
                        ],
                        {"Anchor": None},
                    ],
                }
            },
            "statements.1.statements.0",
        )

    def test_markMarkPosStatement(self):
        self.assertAstToDictEqual(
            "markClass acute <anchor 300 500> @TOP; markClass grave <anchor 300 500> @TOP2; feature test { pos mark acute <anchor 0 50> mark @TOP2; } test;",
            {
                "MarkToMarkPositioning": {
                    "Base": {"Glyph": "acute"},
                    "Marks": [
                        {"Anchor": {"Anchor": {"X": 0, "Y": 50}}, "MarkClass": "TOP2"}
                    ],
                }
            },
            "statements.2.statements.0",
        )

    def test_multipleSubstStatement(self):
        self.assertAstToDictEqual(
            "feature test { sub f_i by f i; } test;",
            {
                "MultipleSubstitution": {
                    "In": {"Glyph": "f_i"},
                    "Out": [{"Glyph": "f"}, {"Glyph": "i"}],
                }
            },
            "statements.0.statements.0",
        )

    def test_pairPosStatement_formatA(self):
        self.assertAstToDictEqual(
            "feature kern { pos A -50 B 20; } kern;",
            {
                "PairPositioning": {
                    "First": {"Glyph": "A"},
                    "Value1": {"ValueRecord": {"XAdvance": -50}},
                    "Second": {"Glyph": "B"},
                    "Value2": {"ValueRecord": {"XAdvance": 20}},
                }
            },
            "statements.0.statements.0",
        )

    def test_pairPosStatement_formatB(self):
        self.assertAstToDictEqual(
            "feature kern { pos A B -50; } kern;",
            {
                "PairPositioning": {
                    "First": {"Glyph": "A"},
                    "Value1": {"ValueRecord": {"XAdvance": -50}},
                    "Second": {"Glyph": "B"},
                }
            },
            "statements.0.statements.0",
        )

    def test_pairPosStatement_enumerated(self):
        self.assertAstToDictEqual(
            "feature kern { enum pos A B -50; } kern;",
            {
                "PairPositioning": {
                    "First": {"Glyph": "A"},
                    "Value1": {"ValueRecord": {"XAdvance": -50}},
                    "Second": {"Glyph": "B"},
                    "Enumerated": True,
                }
            },
            "statements.0.statements.0",
        )

    def test_reverseChainSingleSubstStatement(self):
        self.assertAstToDictEqual(
            "feature test { rsub A B' C by D; } test;",
            {
                "ReverseChainSingleSubstitution": {
                    "Prefix": [{"Glyph": "A"}],
                    "In": [{"Glyph": "B"}],
                    "Suffix": [{"Glyph": "C"}],
                    "Out": [{"Glyph": "D"}],
                }
            },
            "statements.0.statements.0",
        )

    def test_singleSubstStatement(self):
        self.assertAstToDictEqual(
            "feature smcp { sub a by a.sc; } smcp;",
            {
                "SingleSubstitution": {
                    "In": [{"Glyph": "a"}],
                    "Out": [{"Glyph": "a.sc"}],
                }
            },
            "statements.0.statements.0",
        )

    def test_singlePosStatement(self):
        self.assertAstToDictEqual(
            "feature kern { pos A 50; } kern;",
            {
                "SinglePositioning": {
                    "Positions": [
                        {
                            "Glyph": {"Glyph": "A"},
                            "Value": {"ValueRecord": {"XAdvance": 50}},
                        }
                    ]
                }
            },
            "statements.0.statements.0",
        )

    def test_subtableStatement(self):
        self.assertAstToDictEqual(
            "feature test { subtable; } test;", "Subtable", "statements.0.statements.0"
        )

    def test_nameRecord(self):
        self.assertAstToDictEqual(
            'table name { nameid 1 "Family Name"; } name;',
            {
                "NameRecord": {
                    "String": "Family Name",
                }
            },
            "statements.0.statements.0",
        )

    def test_featureNameStatement(self):
        self.assertAstToDictEqual(
            'feature ss01 { featureNames { name "Alternate 1"; }; } ss01;',
            {
                "FeatureName": {
                    "Type": "Name",
                    "String": "Alternate 1",
                }
            },
            "statements.0.statements.0.statements.0",
        )

    def test_statNameStatement(self):
        self.assertAstToDictEqual(
            'table STAT { DesignAxis wght 0 { name "Weight"; }; } STAT;',
            {
                "STATName": {
                    "String": "Weight",
                }
            },
            "statements.0.statements.0.names.0",
        )

    def test_cvParametersNameStatement(self):
        self.assertAstToDictEqual(
            'feature cv01 { cvParameters { FeatUILabelNameID { name "Cv Param Name"; }; }; } cv01;',
            {
                "CVParametersName": {
                    "String": "Cv Param Name",
                }
            },
            "statements.0.statements.0.statements.0.statements.0",
        )

    def test_sizeParameters(self):
        self.assertAstToDictEqual(
            "feature size { parameters 10.0 1 80 120; } size;",
            {
                "SizeParameters": {
                    "DesignSize": 10.0,
                    "SubfamilyID": 1,
                    "RangeStart": 80,
                    "RangeEnd": 120,
                }
            },
            "statements.0.statements.0",
        )

    def test_characterStatement(self):
        self.assertAstToDictEqual(
            "feature cv01 { cvParameters { Character 65; }; } cv01;",
            {"Character": 65},
            "statements.0.statements.0.statements.0",
        )

    def test_os2Field(self):
        self.assertAstToDictEqual(
            "table OS/2 { TypoAscender 750; } OS/2;",
            {"OS2Field": {"TypoAscender": 750}},
            "statements.0.statements.0",
        )

    def test_hheaField(self):
        self.assertAstToDictEqual(
            "table hhea { CaretOffset 50; } hhea;",
            {"HheaField": {"CaretOffset": 50}},
            "statements.0.statements.0",
        )

    def test_vheaField(self):
        self.assertAstToDictEqual(
            "table vhea { VertTypoAscender 800; } vhea;",
            {"VheaField": {"VertTypoAscender": 800}},
            "statements.0.statements.0",
        )

    def test_statDesignAxisStatement(self):
        self.assertAstToDictEqual(
            'table STAT { DesignAxis wght 0 { name "Weight"; }; } STAT;',
            {
                "STATDesignAxis": {
                    "Tag": "wght",
                    "AxisOrder": 0,
                    "Names": [
                        {
                            "STATName": {
                                "String": "Weight",
                            }
                        }
                    ],
                }
            },
            "statements.0.statements.0",
        )

    def test_elidedFallbackName(self):
        self.assertAstToDictEqual(
            'table STAT { ElidedFallbackName { name "Regular"; }; } STAT;',
            {
                "ElidedFallbackName": {
                    "Names": [
                        {
                            "STATName": {
                                "String": "Regular",
                            }
                        }
                    ]
                }
            },
            "statements.0.statements.0",
        )

    def test_elidedFallbackNameID(self):
        self.assertAstToDictEqual(
            "table STAT { ElidedFallbackNameID 256; } STAT;",
            {"ElidedFallbackNameID": 256},
            "statements.0.statements.0",
        )

    def test_statAxisValueStatement(self):
        self.assertAstToDictEqual(
            'table STAT { DesignAxis wght 0 { name "Weight"; }; AxisValue { location wght 400; name "Regular"; flag ElidableAxisValueName; }; } STAT;',
            {
                "STATAxisValue": {
                    "Locations": [
                        {"AxisValueLocation": {"Tag": "wght", "Values": [400]}}
                    ],
                    "Names": [
                        {
                            "STATName": {
                                "String": "Regular",
                            }
                        }
                    ],
                    "Flags": ["ElidableAxisValueName"],
                }
            },
            "statements.0.statements.1",
        )

    def test_axisValueLocationStatement(self):
        self.assertAstToDictEqual(
            'table STAT { DesignAxis wght 0 { name "Weight"; }; AxisValue { location wght 400 300 500; name "Regular"; }; } STAT;',
            {"AxisValueLocation": {"Tag": "wght", "Values": [400, 300, 500]}},
            "statements.0.statements.1.locations.0",
        )

    def test_conditionsetStatement(self):
        self.assertAstToDictEqual(
            "conditionset Cond1 { wght 400 700; wdth 75 100; } Cond1;",
            {
                "ConditionSet": {
                    "Name": "Cond1",
                    "Conditions": {
                        "wght": {"Min": 400, "Max": 700},
                        "wdth": {"Min": 75, "Max": 100},
                    },
                }
            },
            "statements.0",
        )

    def test_variationBlock(self):
        self.assertAstToDictEqual(
            "conditionset Cond1 { wght 700 900; } Cond1; variation rvrn Cond1 { sub A by B; } rvrn;",
            {
                "Variation": {
                    "Name": "rvrn",
                    "ConditionSet": "Cond1",
                    "Statements": [
                        {
                            "SingleSubstitution": {
                                "In": [{"Glyph": "A"}],
                                "Out": [{"Glyph": "B"}],
                            }
                        }
                    ],
                }
            },
            "statements.1",
        )

    def test_attachStatement_class(self):
        self.assertAstToDictEqual(
            "@C = [a e]; table GDEF { Attach @C 2; } GDEF;",
            {"Attach": {"Glyphs": {"ClassName": "C"}, "ContourPoints": [2]}},
            "statements.1.statements.0",
        )

    def test_glyphClass_empty(self):
        self.assertAstToDictEqual(
            "@empty = [];",
            {"GlyphClass": []},
            "statements.0.glyphs",
        )

    def test_glyphClass_from_markClass(self):
        self.assertAstToDictEqual(
            "markClass acute <anchor 0 0> @MC; @GC = [@MC ogonek];",
            {"GlyphClass": [{"ClassName": "MC"}, {"Glyph": "ogonek"}]},
            "statements.1.glyphs",
        )

    def test_glyphClass_range_cid(self):
        self.assertAstToDictEqual(
            r"@myRange = [\999-\1001];",
            {"GlyphClass": [{"GlyphRange": ({"Glyph": "\\999"}, {"Glyph": "\\1001"})}]},
            "statements.0.glyphs",
        )

    def test_glyphClassDefStatement_empty(self):
        self.assertAstToDictEqual(
            "table GDEF { GlyphClassDef ,,,; } GDEF;",
            {"GlyphTypeDefinitions": {}},
            "statements.0.statements.0",
        )

    def test_ignorePosStatement_multiple(self):
        self.assertAstToDictEqual(
            "feature test { ignore pos A B' C, X Y' Z; } test;",
            {
                "IgnorePositioning": [
                    {
                        "Prefix": [{"Glyph": "A"}],
                        "Glyphs": [{"Glyph": "B"}],
                        "Suffix": [{"Glyph": "C"}],
                    },
                    {
                        "Prefix": [{"Glyph": "X"}],
                        "Glyphs": [{"Glyph": "Y"}],
                        "Suffix": [{"Glyph": "Z"}],
                    },
                ]
            },
            "statements.0.statements.0",
        )

    def test_ignoreSubstStatement_multiple(self):
        self.assertAstToDictEqual(
            "feature test { ignore sub A B' C, X Y' Z; } test;",
            {
                "IgnoreSubstitution": [
                    {
                        "Prefix": [{"Glyph": "A"}],
                        "Glyphs": [{"Glyph": "B"}],
                        "Suffix": [{"Glyph": "C"}],
                    },
                    {
                        "Prefix": [{"Glyph": "X"}],
                        "Glyphs": [{"Glyph": "Y"}],
                        "Suffix": [{"Glyph": "Z"}],
                    },
                ]
            },
            "statements.0.statements.0",
        )

    def test_languageStatement_default(self):
        self.assertAstToDictEqual(
            "feature test { language NLD; } test;",
            {"Language": "NLD"},
            "statements.0.statements.0",
        )

    def test_languageStatement_exclude(self):
        self.assertAstToDictEqual(
            "feature test { language NLD exclude_dflt; } test;",
            {"Language": "NLD", "ExcludeDefault": True},
            "statements.0.statements.0",
        )

    def test_languageStatement_exclude_required(self):
        self.assertAstToDictEqual(
            "feature test { language NLD exclude_dflt required; } test;",
            {"Language": "NLD", "ExcludeDefault": True, "Required": True},
            "statements.0.statements.0",
        )

    def test_ligatureCaretByIndexStatement_class(self):
        self.assertAstToDictEqual(
            "@L = [f_f_i f_l]; table GDEF { LigatureCaretByIndex @L 2 4; } GDEF;",
            {"LigatureCaretByIndex": {"Glyphs": {"ClassName": "L"}, "Carets": [2, 4]}},
            "statements.1.statements.0",
        )

    def test_ligatureCaretByPosStatement_class(self):
        self.assertAstToDictEqual(
            "@L = [f_f_i f_l]; table GDEF { LigatureCaretByPos @L 300 600; } GDEF;",
            {
                "LigatureCaretByPosition": {
                    "Glyphs": {"ClassName": "L"},
                    "Carets": [300, 600],
                }
            },
            "statements.1.statements.0",
        )

    def test_lookupBlock_useExtension(self):
        self.assertAstToDictEqual(
            "lookup MYLOOKUP useExtension { sub A by B; } MYLOOKUP;",
            {
                "Lookup": {
                    "Name": "MYLOOKUP",
                    "UseExtension": True,
                    "Statements": [
                        {
                            "SingleSubstitution": {
                                "In": [{"Glyph": "A"}],
                                "Out": [{"Glyph": "B"}],
                            }
                        }
                    ],
                }
            },
            "statements.0",
        )

    def test_lookupFlagStatement_multiple_flags(self):
        self.assertAstToDictEqual(
            "lookup L { lookupflag RightToLeft IgnoreMarks; } L;",
            {"LookupFlag": {"Flags": ["RightToLeft", "IgnoreMarks"]}},
            "statements.0.statements.0",
        )

    def test_lookupFlagStatement_markAttachment(self):
        self.assertAstToDictEqual(
            "markClass acute <anchor 0 0> @MC; lookup L { lookupflag MarkAttachmentType @MC; } L;",
            {"LookupFlag": {"MarkAttachment": {"ClassName": "MC"}}},
            "statements.1.statements.0",
        )

    def test_lookupFlagStatement_markAttachment_class(self):
        self.assertAstToDictEqual(
            "lookup L { lookupflag MarkAttachmentType [acute grave]; } L;",
            {
                "LookupFlag": {
                    "MarkAttachment": {
                        "GlyphClass": [{"Glyph": "acute"}, {"Glyph": "grave"}]
                    }
                }
            },
            "statements.0.statements.0",
        )

    def test_lookupFlagStatement_numeric(self):
        self.assertAstToDictEqual(
            "lookup L { lookupflag 8; } L;",  # 8 = IgnoreMarks
            {"LookupFlag": {"Flags": ["IgnoreMarks"]}},
            "statements.0.statements.0",
        )

    def test_lookupFlagStatement_zero(self):
        self.assertAstToDictEqual(
            "lookup L { lookupflag 0; } L;",
            {"LookupFlag": {}},
            "statements.0.statements.0",
        )

    def test_singlePosStatement_class_horiz(self):
        self.assertAstToDictEqual(
            "feature kern { @V = [A V]; pos @V -50; } kern;",
            {
                "SinglePositioning": {
                    "Positions": [
                        {
                            "Glyph": {"ClassName": "V"},
                            "Value": {"ValueRecord": {"XAdvance": -50}},
                        }
                    ]
                }
            },
            "statements.0.statements.1",
        )

    def test_pairPosStatement_formatA_multiple_values(self):
        self.assertAstToDictEqual(
            "feature kern { pos A 50 B 60; } kern;",
            {
                "PairPositioning": {
                    "First": {"Glyph": "A"},
                    "Value1": {"ValueRecord": {"XAdvance": 50}},
                    "Second": {"Glyph": "B"},
                    "Value2": {"ValueRecord": {"XAdvance": 60}},
                }
            },
            "statements.0.statements.0",
        )

    def test_singlePosStatement_chained(self):
        self.assertAstToDictEqual(
            "feature kern { pos A' 50 B; } kern;",
            {
                "SinglePositioning": {
                    "Positions": [
                        {
                            "Glyph": {"Glyph": "A"},
                            "Value": {"ValueRecord": {"XAdvance": 50}},
                        }
                    ],
                    "Suffix": [{"Glyph": "B"}],
                }
            },
            "statements.0.statements.0",
        )

    def test_pairPosStatement_formatA_class(self):
        self.assertAstToDictEqual(
            "feature kern { @A = [A]; @B = [B]; pos @A -50 @B 20; } kern;",
            {
                "PairPositioning": {
                    "First": {"ClassName": "A"},
                    "Value1": {"ValueRecord": {"XAdvance": -50}},
                    "Second": {"ClassName": "B"},
                    "Value2": {"ValueRecord": {"XAdvance": 20}},
                }
            },
            "statements.0.statements.2",
        )

    def test_pairPosStatement_formatA_enumerated(self):
        self.assertAstToDictEqual(
            "feature kern { enum pos A -50 B 20; } kern;",
            {
                "PairPositioning": {
                    "First": {"Glyph": "A"},
                    "Value1": {"ValueRecord": {"XAdvance": -50}},
                    "Second": {"Glyph": "B"},
                    "Value2": {"ValueRecord": {"XAdvance": 20}},
                    "Enumerated": True,
                }
            },
            "statements.0.statements.0",
        )

    def test_pairPosStatement_formatA_null_first(self):
        self.assertAstToDictEqual(
            "feature kern { pos A <NULL> B 20; } kern;",
            {
                "PairPositioning": {
                    "First": {"Glyph": "A"},
                    "Value1": None,
                    "Second": {"Glyph": "B"},
                    "Value2": {"ValueRecord": {"XAdvance": 20}},
                }
            },
            "statements.0.statements.0",
        )

    def test_pairPosStatement_formatA_null_second(self):
        self.assertAstToDictEqual(
            "feature kern { pos A -50 B <NULL>; } kern;",
            {
                "PairPositioning": {
                    "First": {"Glyph": "A"},
                    "Value1": {"ValueRecord": {"XAdvance": -50}},
                    "Second": {"Glyph": "B"},
                    "Value2": None,
                }
            },
            "statements.0.statements.0",
        )

    def test_pairPosStatement_formatB_class(self):
        self.assertAstToDictEqual(
            "feature kern { @A = [A]; @B = [B]; pos @A @B -50; } kern;",
            {
                "PairPositioning": {
                    "First": {"ClassName": "A"},
                    "Value1": {"ValueRecord": {"XAdvance": -50}},
                    "Second": {"ClassName": "B"},
                }
            },
            "statements.0.statements.2",
        )

    def test_pairPosStatement_enumerated_class(self):
        self.assertAstToDictEqual(
            "feature kern { @A = [A]; @B = [B]; enum pos @A @B -50; } kern;",
            {
                "PairPositioning": {
                    "First": {"ClassName": "A"},
                    "Value1": {"ValueRecord": {"XAdvance": -50}},
                    "Second": {"ClassName": "B"},
                    "Enumerated": True,
                }
            },
            "statements.0.statements.2",
        )

    def test_cursivePosStatement_class(self):
        self.assertAstToDictEqual(
            "feature curs { @C = [A B]; pos cursive @C <anchor 10 20> <anchor 30 40>; } curs;",
            {
                "CursivePositioning": {
                    "Class": {"ClassName": "C"},
                    "Entry": {"Anchor": {"X": 10, "Y": 20}},
                    "Exit": {"Anchor": {"X": 30, "Y": 40}},
                }
            },
            "statements.0.statements.1",
        )

    def test_markBasePosStatement_class_multiple(self):
        self.assertAstToDictEqual(
            "markClass acute <anchor 0 0> @TOP; markClass cedilla <anchor 0 0> @BOT;"
            "feature test { @B = [A E]; pos base @B <anchor 150 450> mark @TOP <anchor 150 -50> mark @BOT; } test;",
            {
                "MarkBasePositioning": {
                    "Base": {"ClassName": "B"},
                    "Marks": [
                        {
                            "Anchor": {"Anchor": {"X": 150, "Y": 450}},
                            "MarkClass": "TOP",
                        },
                        {
                            "Anchor": {"Anchor": {"X": 150, "Y": -50}},
                            "MarkClass": "BOT",
                        },
                    ],
                }
            },
            "statements.2.statements.1",
        )

    def test_markLigPosStatement_class(self):
        self.assertAstToDictEqual(
            "markClass acute <anchor 0 0> @TOP; feature test { @L = [f_f_i f_l]; pos ligature @L <anchor 100 400> mark @TOP ligComponent <anchor NULL>; } test;",
            {
                "MarkLigaturePositioning": {
                    "Ligatures": {"ClassName": "L"},
                    "Marks": [
                        [
                            {
                                "Anchor": {"Anchor": {"X": 100, "Y": 400}},
                                "MarkClass": "TOP",
                            }
                        ],
                        {"Anchor": None},
                    ],
                }
            },
            "statements.1.statements.1",
        )

    def test_markMarkPosStatement_class(self):
        self.assertAstToDictEqual(
            "markClass acute <anchor 0 0> @TOP; markClass grave <anchor 0 0> @TOP2; "
            "feature test { @M = [acute grave]; pos mark @M <anchor 0 50> mark @TOP2; } test;",
            {
                "MarkToMarkPositioning": {
                    "Base": {"ClassName": "M"},
                    "Marks": [
                        {"Anchor": {"Anchor": {"X": 0, "Y": 50}}, "MarkClass": "TOP2"}
                    ],
                }
            },
            "statements.2.statements.1",
        )

    def test_chainContextPosStatement_multiple(self):
        self.assertAstToDictEqual(
            "lookup L1 { pos I 10; } L1; lookup L2 { pos N 20; } L2; "
            "feature test { pos A B I' lookup L1 N' lookup L2 P; } test;",
            {
                "ChainContextualPositioning": {
                    "Prefix": [{"Glyph": "A"}, {"Glyph": "B"}],
                    "ChainedLookups": [
                        {"Glyph": "I", "Lookups": ["L1"]},
                        {"Glyph": "N", "Lookups": ["L2"]},
                    ],
                    "Suffix": [{"Glyph": "P"}],
                }
            },
            "statements.2.statements.0",
        )

    def test_markClassDefinition_class(self):
        self.assertAstToDictEqual(
            "markClass [acute grave] <anchor 300 500> @TOP_MARKS;",
            {
                "MarkClassDefinition": {
                    "Name": "TOP_MARKS",
                    "Anchor": {"Anchor": {"X": 300, "Y": 500}},
                    "Glyphs": {"GlyphClass": [{"Glyph": "acute"}, {"Glyph": "grave"}]},
                }
            },
            "statements.0",
        )

    def test_nameRecord_specific_ids(self):
        self.assertAstToDictEqual(
            'table name { nameid 1 1 0 18 "Test Name"; } name;',
            {
                "NameRecord": {
                    "String": "Test Name",
                    "PlatformID": 1,
                    "PlatformEncodingID": 0,
                    "LanguageID": 18,
                }
            },
            "statements.0.statements.0",
        )

    def test_reverseChainSingleSubstStatement_class(self):
        self.assertAstToDictEqual(
            "feature test { @B = [B b]; rsub A @B' C by D; } test;",
            {
                "ReverseChainSingleSubstitution": {
                    "Prefix": [{"Glyph": "A"}],
                    "In": [{"ClassName": "B"}],
                    "Suffix": [{"Glyph": "C"}],
                    "Out": [{"Glyph": "D"}],
                }
            },
            "statements.0.statements.1",
        )

    def test_reverseChainSingleSubstStatement_range(self):
        self.assertAstToDictEqual(
            "feature test { rsub A [a-c]' D by X; } test;",
            {
                "ReverseChainSingleSubstitution": {
                    "Prefix": [{"Glyph": "A"}],
                    "In": [
                        {
                            "GlyphClass": [
                                {"GlyphRange": ({"Glyph": "a"}, {"Glyph": "c"})}
                            ]
                        }
                    ],
                    "Suffix": [{"Glyph": "D"}],
                    "Out": [{"Glyph": "X"}],
                }
            },
            "statements.0.statements.0",
        )

    def test_elidedFallbackName_multiple(self):
        self.assertAstToDictEqual(
            'table STAT { ElidedFallbackName { name "Reg"; name 1 0 18 "Rom"; }; } STAT;',
            {
                "ElidedFallbackName": {
                    "Names": [
                        {
                            "STATName": {
                                "String": "Reg",
                            }
                        },
                        {
                            "STATName": {
                                "String": "Rom",
                                "PlatformID": 1,
                                "PlatformEncodingID": 0,
                                "LanguageID": 18,
                            }
                        },
                    ]
                }
            },
            "statements.0.statements.0",
        )

    def test_singleSubstStatement_chained(self):
        self.assertAstToDictEqual(
            "feature test { sub A' B by C; } test;",
            {
                "SingleSubstitution": {
                    "In": [{"Glyph": "A"}],
                    "Out": [{"Glyph": "C"}],
                    "Suffix": [{"Glyph": "B"}],
                }
            },
            "statements.0.statements.0",
        )

    def test_singleSubstStatement_class(self):
        self.assertAstToDictEqual(
            "feature smcp { @lower = [a b]; sub @lower by a.sc; } smcp;",
            {
                "SingleSubstitution": {
                    "In": [{"ClassName": "lower"}],
                    "Out": [{"Glyph": "a.sc"}],
                }
            },
            "statements.0.statements.1",
        )

    def test_singleSubstStatement_class_chained(self):
        self.assertAstToDictEqual(
            "feature smcp { @lower = [a b]; sub C @lower' D by a.sc; } smcp;",
            {
                "SingleSubstitution": {
                    "Prefix": [{"Glyph": "C"}],
                    "In": [{"ClassName": "lower"}],
                    "Suffix": [{"Glyph": "D"}],
                    "Out": [{"Glyph": "a.sc"}],
                }
            },
            "statements.0.statements.1",
        )

    def test_singleSubstStatement_range(self):
        self.assertAstToDictEqual(
            "feature smcp { sub [a-c] by [A.sc-C.sc]; } smcp;",
            {
                "SingleSubstitution": {
                    "In": [
                        {
                            "GlyphClass": [
                                {"GlyphRange": ({"Glyph": "a"}, {"Glyph": "c"})}
                            ]
                        }
                    ],
                    "Out": [
                        {
                            "GlyphClass": [
                                {"GlyphRange": ({"Glyph": "A.sc"}, {"Glyph": "C.sc"})}
                            ]
                        }
                    ],
                }
            },
            "statements.0.statements.0",
        )

    def test_singleSubstStatement_range_chained(self):
        self.assertAstToDictEqual(
            "feature smcp { sub X [a-c]' Y by [A.sc-C.sc]; } smcp;",
            {
                "SingleSubstitution": {
                    "Prefix": [{"Glyph": "X"}],
                    "In": [
                        {
                            "GlyphClass": [
                                {"GlyphRange": ({"Glyph": "a"}, {"Glyph": "c"})}
                            ]
                        }
                    ],
                    "Suffix": [{"Glyph": "Y"}],
                    "Out": [
                        {
                            "GlyphClass": [
                                {"GlyphRange": ({"Glyph": "A.sc"}, {"Glyph": "C.sc"})}
                            ]
                        }
                    ],
                }
            },
            "statements.0.statements.0",
        )

    def test_multipleSubstStatement_chained(self):
        self.assertAstToDictEqual(
            "feature test { sub A f_i' B by f i; } test;",
            {
                "MultipleSubstitution": {
                    "Prefix": [{"Glyph": "A"}],
                    "In": {"Glyph": "f_i"},
                    "Suffix": [{"Glyph": "B"}],
                    "Out": [{"Glyph": "f"}, {"Glyph": "i"}],
                }
            },
            "statements.0.statements.0",
        )

    def test_multipleSubstStatement_force_chained(self):
        self.assertAstToDictEqual(
            "feature test { sub f_i' by f i; } test;",
            {
                "MultipleSubstitution": {
                    "In": {"Glyph": "f_i"},
                    "Chained": True,
                    "Out": [{"Glyph": "f"}, {"Glyph": "i"}],
                }
            },
            "statements.0.statements.0",
        )

    def test_multipleSubstStatement_classes(self):
        self.assertAstToDictEqual(
            "feature test { @IN = [f_i f_l]; @F = [f]; @IL = [i l]; sub @IN by @F @IL; } test;",
            {
                "MultipleSubstitution": {
                    "In": {"ClassName": "IN"},
                    "Out": [{"ClassName": "F"}, {"ClassName": "IL"}],
                }
            },
            "statements.0.statements.3",
        )

    def test_multipleSubstStatement_classes_mixed(self):
        self.assertAstToDictEqual(
            "feature test { @IN = [f_i f_l]; @IL = [i l]; sub @IN by f @IL; } test;",
            {
                "MultipleSubstitution": {
                    "In": {"ClassName": "IN"},
                    "Out": [{"Glyph": "f"}, {"ClassName": "IL"}],
                }
            },
            "statements.0.statements.2",
        )

    def test_alternateSubstStatement_chained(self):
        self.assertAstToDictEqual(
            "feature test { sub X a' Y from [a.1 a.2]; } test;",
            {
                "AlternateSubstitution": {
                    "Prefix": [{"Glyph": "X"}],
                    "Suffix": [{"Glyph": "Y"}],
                    "In": {"Glyph": "a"},
                    "Out": {"GlyphClass": [{"Glyph": "a.1"}, {"Glyph": "a.2"}]},
                }
            },
            "statements.0.statements.0",
        )

    def test_alternateSubstStatement_class(self):
        self.assertAstToDictEqual(
            "feature test { @ALT = [a.1 a.2]; sub a from @ALT; } test;",
            {
                "AlternateSubstitution": {
                    "In": {"Glyph": "a"},
                    "Out": {"ClassName": "ALT"},
                }
            },
            "statements.0.statements.1",
        )

    def test_ligatureSubstStatement_chained(self):
        self.assertAstToDictEqual(
            "feature liga { sub X f' f' i' Y by f_f_i; } liga;",
            {
                "LigatureSubstitution": {
                    "Prefix": [{"Glyph": "X"}],
                    "In": [{"Glyph": "f"}, {"Glyph": "f"}, {"Glyph": "i"}],
                    "Suffix": [{"Glyph": "Y"}],
                    "Out": {"Glyph": "f_f_i"},
                }
            },
            "statements.0.statements.0",
        )

    def test_chainContextSubstStatement_multiple(self):
        self.assertAstToDictEqual(
            "lookup L1 { sub I by X; } L1; lookup L2 { sub N by Y; } L2; "
            "feature test { sub A B I' lookup L1 N' lookup L2 P; } test;",
            {
                "ChainContextualSubstitution": {
                    "Prefix": [{"Glyph": "A"}, {"Glyph": "B"}],
                    "ChainedLookups": [
                        {"Glyph": "I", "Lookups": ["L1"]},
                        {"Glyph": "N", "Lookups": ["L2"]},
                    ],
                    "Suffix": [{"Glyph": "P"}],
                }
            },
            "statements.2.statements.0",
        )

    def test_valueRecordDefinition_null(self):
        self.assertAstToDictEqual(
            "valueRecordDef <NULL> foo;",
            {"ValueRecordDefinition": {"Name": "foo", "Value": None}},
            "statements.0",
        )

    def test_valueRecordDefinition_named(self):
        self.assertAstToDictEqual(
            "valueRecordDef 100 foo; valueRecordDef <foo> bar;",
            {
                "ValueRecordDefinition": {
                    "Name": "bar",
                    "Value": {"ValueRecord": {"XAdvance": 100}},
                }
            },
            "statements.1",
        )

    def test_valueRecord_multiple_devices(self):
        self.assertAstToDictEqual(
            "feature kern { pos A <1 2 3 4 <device 10 100, 11 110> <device 12 120> <device NULL> <device NULL>> B; } kern;",
            {
                "ValueRecord": {
                    "XPlacement": 1,
                    "YPlacement": 2,
                    "XAdvance": 3,
                    "YAdvance": 4,
                    "XPlacementDevice": [
                        {"Size": 10, "Value": 100},
                        {"Size": 11, "Value": 110},
                    ],
                    "YPlacementDevice": [{"Size": 12, "Value": 120}],
                }
            },
            "statements.0.statements.0.valuerecord1",
        )

    def test_baseAxis(self):
        self.assertAstToDictEqual(
            "table BASE { HorizAxis.BaseTagList foo  bar ; HorizAxis.BaseScriptList latn foo 0 0, DFLT bar 0 0 ; } BASE;",
            {
                "BaseAxis": {
                    "Direction": "Horizontal",
                    "Bases": ["foo", "bar"],
                    "Scripts": [
                        {"Script": "latn", "Baseline": "foo", "Coordinates": [0, 0]},
                        {"Script": "DFLT", "Baseline": "bar", "Coordinates": [0, 0]},
                    ],
                }
            },
            "statements.0.statements.0",
        )

    def test_os2Field_range(self):
        self.assertAstToDictEqual(
            "table OS/2 { UnicodeRange 0 1 2; } OS/2;",
            {"OS2Field": {"UnicodeRange": [0, 1, 2]}},
            "statements.0.statements.0",
        )

    def test_os2Field_vendor(self):
        self.assertAstToDictEqual(
            'table OS/2 { Vendor "TEST"; } OS/2;',
            {"OS2Field": {"Vendor": "TEST"}},
            "statements.0.statements.0",
        )

    def test_hheaField_lowercase(self):
        self.assertAstToDictEqual(
            "table hhea { Ascender 750; } hhea;",
            {"HheaField": {"Ascender": 750}},
            "statements.0.statements.0",
        )


if __name__ == "__main__":
    unittest.main()
