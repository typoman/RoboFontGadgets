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

    def test_comment_toDict(self):
        doc = self.parse("# Initial comment")
        comment_node = doc.statements[0]
        self.assertIsInstance(comment_node, ast.Comment)
        expected_dict = {"Comment": "# Initial comment"}
        self.assertEqual(comment_node.toDict(), expected_dict)

    def test_glyphName_toDict(self):
        doc = self.parse("feature test { sub A by B; } test;")
        sub_statement = doc.statements[0].statements[0]
        glyph_a = sub_statement.glyphs[0]
        self.assertIsInstance(glyph_a, ast.GlyphName)
        expected_dict = {"Glyph": "A"}
        self.assertEqual(glyph_a.toDict(), expected_dict)

    def test_glyphClass_toDict_simple(self):
        doc = self.parse("@myClass = [A B C];")
        gc_def = doc.statements[0]
        glyph_class = gc_def.glyphs
        self.assertIsInstance(glyph_class, ast.GlyphClass)
        expected_dict = {"GlyphClass": [{"Glyph": "A"}, {"Glyph": "B"}, {"Glyph": "C"}]}
        self.assertEqual(glyph_class.toDict(), expected_dict)

    def test_glyphClass_toDict_range(self):
        doc = self.parse("@myRange = [A-C];")
        gc_def = doc.statements[0]
        glyph_class = gc_def.glyphs
        self.assertIsInstance(glyph_class, ast.GlyphClass)
        expected_dict = {
            "GlyphClass": [{"GlyphRange": ({"Glyph": "A"}, {"Glyph": "C"})}]
        }
        self.assertEqual(glyph_class.toDict(), expected_dict)

    def test_glyphClass_toDict_mixed(self):
        doc = self.parse("@myMixed = [X A-C Y];")
        gc_def = doc.statements[0]
        glyph_class = gc_def.glyphs
        self.assertIsInstance(glyph_class, ast.GlyphClass)
        expected_dict = {
            "GlyphClass": [
                {"Glyph": "X"},
                {"GlyphRange": ({"Glyph": "A"}, {"Glyph": "C"})},
                {"Glyph": "Y"},
            ]
        }
        self.assertEqual(glyph_class.toDict(), expected_dict)

    def test_glyphClassName_toDict(self):
        doc = self.parse("@myClass = [A B]; feature test { sub @myClass by C; } test;")
        sub_statement = doc.statements[1].statements[0]
        glyph_class_name = sub_statement.glyphs[0]
        self.assertIsInstance(glyph_class_name, ast.GlyphClassName)
        expected_dict = {"ClassName": "myClass"}
        self.assertEqual(glyph_class_name.toDict(), expected_dict)

    def test_anchor_toDict_simple(self):
        doc = self.parse(
            "feature test { pos cursive A <anchor 120 -20> <anchor NULL>; } test;"
        )
        cursive_pos = doc.statements[0].statements[0]
        anchor = cursive_pos.entryAnchor
        self.assertIsInstance(anchor, ast.Anchor)
        expected_dict = {"Anchor": {"X": 120, "Y": -20}}
        self.assertEqual(anchor.toDict(), expected_dict)

    def test_anchor_toDict_contourpoint(self):
        doc = self.parse(
            "feature test { pos cursive A <anchor 120 -20 contourpoint 5> <anchor NULL>; } test;"
        )
        cursive_pos = doc.statements[0].statements[0]
        anchor = cursive_pos.entryAnchor
        self.assertIsInstance(anchor, ast.Anchor)
        expected_dict = {"Anchor": {"X": 120, "Y": -20, "ContourPoint": 5}}
        self.assertEqual(anchor.toDict(), expected_dict)

    def test_anchor_toDict_device(self):
        doc = self.parse(
            "feature test { pos cursive A <anchor 120 -20 <device 11 111> <device NULL>> <anchor NULL>; } test;"
        )
        cursive_pos = doc.statements[0].statements[0]
        anchor = cursive_pos.entryAnchor
        self.assertIsInstance(anchor, ast.Anchor)
        expected_dict = {
            "Anchor": {
                "X": 120,
                "Y": -20,
                "XDevice": [{"Size": 11, "Value": 111}],
            }
        }
        self.assertEqual(anchor.toDict(), expected_dict)

    def test_anchor_toDict_named(self):
        doc = self.parse(
            "feature test { anchorDef 123 456 foo; pos cursive A <anchor foo> <anchor NULL>; } test;"
        )
        cursive_pos = doc.statements[0].statements[1]
        anchor = cursive_pos.entryAnchor
        self.assertIsInstance(anchor, ast.Anchor)
        expected_dict = {"Anchor": {"Name": "foo"}}
        self.assertEqual(anchor.toDict(), expected_dict)

    def test_anchorDefinition_toDict(self):
        doc = self.parse("anchorDef 123 456 foo;")
        anchor_def = doc.statements[0]
        self.assertIsInstance(anchor_def, ast.AnchorDefinition)
        expected_dict = {"AnchorDefinition": {"Name": "foo", "X": 123, "Y": 456}}
        self.assertEqual(anchor_def.toDict(), expected_dict)

    def test_anchorDefinition_toDict_contourpoint(self):
        doc = self.parse("anchorDef 123 456 contourpoint 5 foo;")
        anchor_def = doc.statements[0]
        self.assertIsInstance(anchor_def, ast.AnchorDefinition)
        expected_dict = {
            "AnchorDefinition": {"Name": "foo", "X": 123, "Y": 456, "ContourPoint": 5}
        }
        self.assertEqual(anchor_def.toDict(), expected_dict)

    def test_valueRecord_toDict_simple_horiz(self):
        doc = self.parse("feature kern { pos A B -50; } kern;")
        pair_pos = doc.statements[0].statements[0]
        value_rec = pair_pos.valuerecord1
        self.assertIsInstance(value_rec, ast.ValueRecord)
        expected_dict = {"ValueRecord": {"XAdvance": -50}}
        self.assertEqual(value_rec.toDict(), expected_dict)

    def test_valueRecord_toDict_simple_vert(self):
        doc = self.parse("feature vkrn { pos A B -50; } vkrn;")
        pair_pos = doc.statements[0].statements[0]
        value_rec = pair_pos.valuerecord1
        self.assertIsInstance(value_rec, ast.ValueRecord)
        expected_dict = {"ValueRecord": {"YAdvance": -50, "Vertical": True}}
        self.assertEqual(value_rec.toDict(), expected_dict)

    def test_valueRecord_toDict_full(self):
        doc = self.parse("feature kern { pos A <1 2 3 4> B; } kern;")
        pair_pos = doc.statements[0].statements[0]
        value_rec = pair_pos.valuerecord1
        self.assertIsInstance(value_rec, ast.ValueRecord)
        expected_dict = {
            "ValueRecord": {
                "XPlacement": 1,
                "YPlacement": 2,
                "XAdvance": 3,
                "YAdvance": 4,
            }
        }
        self.assertEqual(value_rec.toDict(), expected_dict)

    def test_valueRecord_toDict_device(self):
        doc = self.parse(
            "feature kern { pos A <1 2 3 4 <device 10 100> <device NULL> <device NULL> <device NULL>> B; } kern;"
        )
        pair_pos = doc.statements[0].statements[0]
        value_rec = pair_pos.valuerecord1
        self.assertIsInstance(value_rec, ast.ValueRecord)
        expected_dict = {
            "ValueRecord": {
                "XPlacement": 1,
                "YPlacement": 2,
                "XAdvance": 3,
                "YAdvance": 4,
                "XPlacementDevice": [{"Size": 10, "Value": 100}],
            }
        }
        self.assertEqual(value_rec.toDict(), expected_dict)

    def test_valueRecordDefinition_toDict(self):
        doc = self.parse("valueRecordDef 123 foo;")
        vr_def = doc.statements[0]
        self.assertIsInstance(vr_def, ast.ValueRecordDefinition)
        expected_dict = {
            "ValueRecordDefinition": {
                "Name": "foo",
                "Value": {"ValueRecord": {"XAdvance": 123}},
            }
        }
        self.assertEqual(vr_def.toDict(), expected_dict)

    def test_markClassName_toDict(self):
        doc = self.parse("markClass A <anchor 0 0> @MC; @GC = [@MC];")
        gc_def = doc.statements[1]
        mark_class_name_node = gc_def.glyphs.original[0]
        self.assertIsInstance(mark_class_name_node, ast.MarkClassName)
        expected_dict = {"ClassName": "MC"}
        self.assertEqual(mark_class_name_node.toDict(), expected_dict)

    def test_anonymousBlock_toDict(self):
        doc = self.parse("anon TEST {\n content \n} TEST;")
        anon_block = doc.statements[0]
        self.assertIsInstance(anon_block, ast.AnonymousBlock)
        expected_dict = {"AnonymousBlock": {"Tag": "TEST", "Content": "content"}}
        self.assertEqual(anon_block.toDict(), expected_dict)

    def test_featureFile_toDict(self):
        doc = self.parse("# File comment\nfeature liga { sub f i by f_i; } liga;")
        self.assertIsInstance(doc, ast.FeatureFile)
        expected_dict = {
            "FeatureFile": {
                "Statements": [
                    {"Comment": "# File comment"},
                    {
                        "FeatureBlock": {
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
        }
        self.assertEqual(doc.toDict(), expected_dict)

    def test_featureBlock_toDict(self):
        doc = self.parse("feature liga useExtension { sub f i by f_i; } liga;")
        feature_block = doc.statements[0]
        self.assertIsInstance(feature_block, ast.FeatureBlock)
        expected_dict = {
            "FeatureBlock": {
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
        }
        self.assertEqual(feature_block.toDict(), expected_dict)

    def test_nestedBlock_toDict(self):
        doc = self.parse('feature ss01 { featureNames { name "Alternate"; }; } ss01;')
        feature_block = doc.statements[0]
        nested_block = feature_block.statements[0]
        self.assertIsInstance(nested_block, ast.NestedBlock)
        expected_dict = {
            "NestedBlock": {
                "Tag": "ss01",
                "BlockName": "featureNames",
                "Statements": [
                    {
                        "FeatureName": {
                            "Type": "Name",
                            "String": "Alternate",
                            "PlatformID": 3,
                            "PlatformEncodingID": 1,
                            "LanguageID": 1033,
                        }
                    }
                ],
            }
        }
        self.assertEqual(nested_block.toDict(), expected_dict)

    def test_lookupBlock_toDict(self):
        doc = self.parse("lookup MYLOOKUP { sub A by B; } MYLOOKUP;")
        lookup_block = doc.statements[0]
        self.assertIsInstance(lookup_block, ast.LookupBlock)
        expected_dict = {
            "LookupBlock": {
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
        }
        self.assertEqual(lookup_block.toDict(), expected_dict)

    def test_tableBlock_toDict(self):
        doc = self.parse("table GDEF { GlyphClassDef [A], [f_i], [acute], ; } GDEF;")
        table_block = doc.statements[0]
        self.assertIsInstance(table_block, ast.TableBlock)
        expected_dict = {
            "TableBlock": {
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
        }
        self.assertEqual(table_block.toDict(), expected_dict)

    def test_glyphClassDefinition_toDict(self):
        doc = self.parse("@myClass = [A B C];")
        gc_def = doc.statements[0]
        self.assertIsInstance(gc_def, ast.GlyphClassDefinition)
        expected_dict = {
            "GlyphDefinitionClass": {
                "Name": "myClass",
                "Glyphs": {
                    "GlyphClass": [{"Glyph": "A"}, {"Glyph": "B"}, {"Glyph": "C"}]
                },
            }
        }
        self.assertEqual(gc_def.toDict(), expected_dict)

    def test_glyphClassDefStatement_toDict(self):
        doc = self.parse("table GDEF { GlyphClassDef [A], [f_i], [acute], [C]; } GDEF;")
        gcd_stmt = doc.statements[0].statements[0]
        self.assertIsInstance(gcd_stmt, ast.GlyphClassDefStatement)
        expected_dict = {
            "GlyphTypeDefinitions": {
                "BaseGlyphs": {"GlyphClass": [{"Glyph": "A"}]},
                "LigatureGlyphs": {"GlyphClass": [{"Glyph": "f_i"}]},
                "MarkGlyphs": {"GlyphClass": [{"Glyph": "acute"}]},
                "ComponentGlyphs": {"GlyphClass": [{"Glyph": "C"}]},
            }
        }
        self.assertEqual(gcd_stmt.toDict(), expected_dict)

    def test_markClassDefinition_toDict(self):
        doc = self.parse("markClass acute <anchor 300 500> @TOP_MARKS;")
        mcd_stmt = doc.statements[0]
        self.assertIsInstance(mcd_stmt, ast.MarkClassDefinition)
        expected_dict = {
            "MarkClassDefinition": {
                "Name": "TOP_MARKS",
                "Anchor": {"Anchor": {"X": 300, "Y": 500}},
                "Glyphs": {"Glyph": "acute"},
            }
        }
        self.assertEqual(mcd_stmt.toDict(), expected_dict)

    def test_alternateSubstStatement_toDict(self):
        doc = self.parse("feature test { sub a from [a.1 a.2]; } test;")
        alt_sub = doc.statements[0].statements[0]
        self.assertIsInstance(alt_sub, ast.AlternateSubstStatement)
        expected_dict = {
            "AlternateSubstitution": {
                "In": {"Glyph": "a"},
                "Out": {"GlyphClass": [{"Glyph": "a.1"}, {"Glyph": "a.2"}]},
            }
        }
        self.assertEqual(alt_sub.toDict(), expected_dict)

    def test_attachStatement_toDict(self):
        doc = self.parse("table GDEF { Attach a 1; } GDEF;")
        attach_stmt = doc.statements[0].statements[0]
        self.assertIsInstance(attach_stmt, ast.AttachStatement)
        expected_dict = {
            "Attach": {
                "Glyphs": {"Glyph": "a"},
                "ContourPoints": [
                    1
                ],  # Note: parser makes this a set, but spec shows list
            }
        }
        self.assertEqual(attach_stmt.toDict(), expected_dict)

    def test_chainContextPosStatement_toDict(self):
        doc = self.parse(
            "lookup L { pos A 10; } L; feature test { pos B A' lookup L C; } test;"
        )
        chain_pos = doc.statements[1].statements[0]
        self.assertIsInstance(chain_pos, ast.ChainContextPosStatement)
        expected_dict = {
            "ChainContextualPositioning": {
                "Prefix": [{"Glyph": "B"}],
                "ChainedLookups": [{"Glyph": "A", "Lookups": ["L"]}],
                "Suffix": [{"Glyph": "C"}],
            }
        }
        self.assertEqual(chain_pos.toDict(), expected_dict)

    def test_chainContextSubstStatement_toDict(self):
        doc = self.parse(
            "lookup L { sub A by B; } L; feature test { sub C A' lookup L D; } test;"
        )
        chain_sub = doc.statements[1].statements[0]
        self.assertIsInstance(chain_sub, ast.ChainContextSubstStatement)
        expected_dict = {
            "ChainContextualSubstitution": {
                "Prefix": [{"Glyph": "C"}],
                "ChainedLookups": [{"Glyph": "A", "Lookups": ["L"]}],
                "Suffix": [{"Glyph": "D"}],
            }
        }
        self.assertEqual(chain_sub.toDict(), expected_dict)

    def test_cursivePosStatement_toDict(self):
        doc = self.parse(
            "feature curs { pos cursive A <anchor 10 20> <anchor 30 40>; } curs;"
        )
        curs_pos = doc.statements[0].statements[0]
        self.assertIsInstance(curs_pos, ast.CursivePosStatement)
        expected_dict = {
            "CursivePositioning": {
                "Class": {"Glyph": "A"},
                "Entry": {"Anchor": {"X": 10, "Y": 20}},
                "Exit": {"Anchor": {"X": 30, "Y": 40}},
            }
        }
        self.assertEqual(curs_pos.toDict(), expected_dict)

    def test_featureReferenceStatement_toDict(self):
        doc = self.parse("feature aalt { feature salt; } aalt;")
        feat_ref = doc.statements[0].statements[0]
        self.assertIsInstance(feat_ref, ast.FeatureReferenceStatement)
        expected_dict = {"FeatureReference": "salt"}
        self.assertEqual(feat_ref.toDict(), expected_dict)

    def test_ignorePosStatement_toDict(self):
        doc = self.parse("feature test { ignore pos A B' C; } test;")
        ign_pos = doc.statements[0].statements[0]
        self.assertIsInstance(ign_pos, ast.IgnorePosStatement)
        expected_dict = {
            "IgnorePositioning": [
                {
                    "Prefix": [{"Glyph": "A"}],
                    "Glyphs": [{"Glyph": "B"}],
                    "Suffix": [{"Glyph": "C"}],
                }
            ]
        }
        self.assertEqual(ign_pos.toDict(), expected_dict)

    def test_ignoreSubstStatement_toDict(self):
        doc = self.parse("feature test { ignore sub A B' C; } test;")
        ign_sub = doc.statements[0].statements[0]
        self.assertIsInstance(ign_sub, ast.IgnoreSubstStatement)
        expected_dict = {
            "IgnoreSubstitution": [
                {
                    "Prefix": [{"Glyph": "A"}],
                    "Glyphs": [{"Glyph": "B"}],
                    "Suffix": [{"Glyph": "C"}],
                }
            ]
        }
        self.assertEqual(ign_sub.toDict(), expected_dict)

    def test_includeStatement_toDict(self):
        # Need followIncludes=False for the parser to return the IncludeStatement
        doc = self.parse("include(somefile.fea);", followIncludes=False)
        inc_stmt = doc.statements[0]
        self.assertIsInstance(inc_stmt, ast.IncludeStatement)
        expected_dict = {"Include": "somefile.fea"}
        self.assertEqual(inc_stmt.toDict(), expected_dict)

    def test_scriptStatement_toDict(self):
        doc = self.parse("feature test { script latn; } test;")
        script_stmt = doc.statements[0].statements[0]
        self.assertIsInstance(script_stmt, ast.ScriptStatement)
        expected_dict = {"Script": "latn"}
        self.assertEqual(script_stmt.toDict(), expected_dict)

    def test_languageStatement_toDict(self):
        doc = self.parse("feature test { language DEU required; } test;")
        lang_stmt = doc.statements[0].statements[0]
        self.assertIsInstance(lang_stmt, ast.LanguageStatement)
        expected_dict = {"Language": "DEU", "Required": True}
        self.assertEqual(lang_stmt.toDict(), expected_dict)

    def test_languageSystemStatement_toDict(self):
        doc = self.parse("languagesystem latn NLD;")
        langsys_stmt = doc.statements[0]
        self.assertIsInstance(langsys_stmt, ast.LanguageSystemStatement)
        expected_dict = {"LanguageSystem": {"Script": "latn", "Language": "NLD"}}
        self.assertEqual(langsys_stmt.toDict(), expected_dict)

    def test_fontRevisionStatement_toDict(self):
        doc = self.parse("table head { FontRevision 1.005; } head;")
        rev_stmt = doc.statements[0].statements[0]
        self.assertIsInstance(rev_stmt, ast.FontRevisionStatement)
        expected_dict = {"FontRevision": 1.005}
        self.assertEqual(rev_stmt.toDict(), expected_dict)

    def test_ligatureCaretByIndexStatement_toDict(self):
        doc = self.parse("table GDEF { LigatureCaretByIndex f_f_i 2 4; } GDEF;")
        lig_caret = doc.statements[0].statements[0]
        self.assertIsInstance(lig_caret, ast.LigatureCaretByIndexStatement)
        expected_dict = {
            "LigatureCaretByIndex": {
                "Glyphs": {"Glyph": "f_f_i"},
                "Carets": [2, 4],
            }
        }
        self.assertEqual(lig_caret.toDict(), expected_dict)

    def test_ligatureCaretByPosStatement_toDict(self):
        doc = self.parse("table GDEF { LigatureCaretByPos f_f_i 300 600; } GDEF;")
        lig_caret = doc.statements[0].statements[0]
        self.assertIsInstance(lig_caret, ast.LigatureCaretByPosStatement)
        expected_dict = {
            "LigatureCaretByPosition": {
                "Glyphs": {"Glyph": "f_f_i"},
                "Carets": [300, 600],
            }
        }
        self.assertEqual(lig_caret.toDict(), expected_dict)

    def test_ligatureSubstStatement_toDict(self):
        doc = self.parse("feature liga { sub f f i by f_f_i; } liga;")
        lig_sub = doc.statements[0].statements[0]
        self.assertIsInstance(lig_sub, ast.LigatureSubstStatement)
        expected_dict = {
            "LigatureSubstitution": {
                "In": [{"Glyph": "f"}, {"Glyph": "f"}, {"Glyph": "i"}],
                "Out": {"Glyph": "f_f_i"},
            }
        }
        self.assertEqual(lig_sub.toDict(), expected_dict)

    def test_lookupFlagStatement_toDict(self):
        doc = self.parse(
            "lookup L { lookupflag IgnoreMarks UseMarkFilteringSet [cedilla]; } L;"
        )
        lookup_flag = doc.statements[0].statements[0]
        self.assertIsInstance(lookup_flag, ast.LookupFlagStatement)
        expected_dict = {
            "LookupFlag": {
                "Flags": ["IgnoreMarks"],
                "UseMarkFilteringSet": {"GlyphClass": [{"Glyph": "cedilla"}]},
            }
        }
        self.assertEqual(lookup_flag.toDict(), expected_dict)

    def test_lookupReferenceStatement_toDict(self):
        doc = self.parse("lookup L {} L; feature test { lookup L; } test;")
        lookup_ref = doc.statements[1].statements[0]
        self.assertIsInstance(lookup_ref, ast.LookupReferenceStatement)
        expected_dict = {"LookupReference": "L"}
        self.assertEqual(lookup_ref.toDict(), expected_dict)

    def test_markBasePosStatement_toDict(self):
        doc = self.parse(
            "markClass acute <anchor 300 500> @TOP; feature test { pos base A <anchor 150 450> mark @TOP; } test;"
        )
        mark_base = doc.statements[1].statements[0]
        self.assertIsInstance(mark_base, ast.MarkBasePosStatement)
        expected_dict = {
            "MarkBasePositioning": {
                "Base": {"Glyph": "A"},
                "Marks": [
                    {"Anchor": {"Anchor": {"X": 150, "Y": 450}}, "MarkClass": "TOP"}
                ],
            }
        }
        self.assertEqual(mark_base.toDict(), expected_dict)

    def test_markLigPosStatement_toDict(self):
        doc = self.parse(
            "markClass acute <anchor 300 500> @TOP; feature test { pos ligature f_f_i <anchor 100 400> mark @TOP ligComponent <anchor 400 400> mark @TOP ligComponent <anchor NULL>; } test;"
        )
        mark_lig = doc.statements[1].statements[0]
        self.assertIsInstance(mark_lig, ast.MarkLigPosStatement)
        expected_dict = {
            "MarkLigaturePositioning": {
                "Ligatures": {"Glyph": "f_f_i"},
                "Marks": [
                    [{"Anchor": {"Anchor": {"X": 100, "Y": 400}}, "MarkClass": "TOP"}],
                    [{"Anchor": {"Anchor": {"X": 400, "Y": 400}}, "MarkClass": "TOP"}],
                    {"Anchor": None},  # Represents <anchor NULL>
                ],
            }
        }
        self.assertEqual(mark_lig.toDict(), expected_dict)

    def test_markMarkPosStatement_toDict(self):
        doc = self.parse(
            "markClass acute <anchor 300 500> @TOP; markClass grave <anchor 300 500> @TOP2; feature test { pos mark acute <anchor 0 50> mark @TOP2; } test;"
        )
        mark_mark = doc.statements[2].statements[0]
        self.assertIsInstance(mark_mark, ast.MarkMarkPosStatement)
        expected_dict = {
            "MarkToMarkPositioning": {
                "Base": {"Glyph": "acute"},
                "Marks": [
                    {"Anchor": {"Anchor": {"X": 0, "Y": 50}}, "MarkClass": "TOP2"}
                ],
            }
        }
        self.assertEqual(mark_mark.toDict(), expected_dict)

    def test_multipleSubstStatement_toDict(self):
        doc = self.parse("feature test { sub f_i by f i; } test;")
        multi_sub = doc.statements[0].statements[0]
        self.assertIsInstance(multi_sub, ast.MultipleSubstStatement)
        expected_dict = {
            "MultipleSubstitution": {
                "In": {"Glyph": "f_i"},
                "Out": [{"Glyph": "f"}, {"Glyph": "i"}],
            }
        }
        self.assertEqual(multi_sub.toDict(), expected_dict)

    def test_pairPosStatement_toDict_formatA(self):
        doc = self.parse("feature kern { pos A -50 B 20; } kern;")
        pair_pos = doc.statements[0].statements[0]
        self.assertIsInstance(pair_pos, ast.PairPosStatement)
        expected_dict = {
            "PairPositioning": {
                "First": {"Glyph": "A"},
                "Value1": {"ValueRecord": {"XAdvance": -50}},
                "Second": {"Glyph": "B"},
                "Value2": {"ValueRecord": {"XAdvance": 20}},
                "Enumerated": False,
            }
        }
        self.assertEqual(pair_pos.toDict(), expected_dict)

    def test_pairPosStatement_toDict_formatB(self):
        doc = self.parse("feature kern { pos A B -50; } kern;")
        pair_pos = doc.statements[0].statements[0]
        self.assertIsInstance(pair_pos, ast.PairPosStatement)
        expected_dict = {
            "PairPositioning": {
                "First": {"Glyph": "A"},
                "Value1": {"ValueRecord": {"XAdvance": -50}},
                "Second": {"Glyph": "B"},
                "Enumerated": False,
            }
        }
        self.assertEqual(pair_pos.toDict(), expected_dict)

    def test_pairPosStatement_toDict_enumerated(self):
        doc = self.parse("feature kern { enum pos A B -50; } kern;")
        pair_pos = doc.statements[0].statements[0]
        self.assertIsInstance(pair_pos, ast.PairPosStatement)
        expected_dict = {
            "PairPositioning": {
                "First": {"Glyph": "A"},
                "Value1": {"ValueRecord": {"XAdvance": -50}},
                "Second": {"Glyph": "B"},
                "Enumerated": True,
            }
        }
        self.assertEqual(pair_pos.toDict(), expected_dict)

    def test_reverseChainSingleSubstStatement_toDict(self):
        doc = self.parse("feature test { rsub A B' C by D; } test;")
        rsub = doc.statements[0].statements[0]
        self.assertIsInstance(rsub, ast.ReverseChainSingleSubstStatement)
        expected_dict = {
            "ReverseChainSingleSubstitution": {
                "Prefix": [{"Glyph": "A"}],
                "In": [{"Glyph": "B"}],
                "Suffix": [{"Glyph": "C"}],
                "Out": [{"Glyph": "D"}],
            }
        }
        self.assertEqual(rsub.toDict(), expected_dict)

    def test_singleSubstStatement_toDict(self):
        doc = self.parse("feature smcp { sub a by a.sc; } smcp;")
        single_sub = doc.statements[0].statements[0]
        self.assertIsInstance(single_sub, ast.SingleSubstStatement)
        expected_dict = {
            "SingleSubstitution": {
                "In": [{"Glyph": "a"}],
                "Out": [{"Glyph": "a.sc"}],
            }
        }
        self.assertEqual(single_sub.toDict(), expected_dict)

    def test_singlePosStatement_toDict(self):
        doc = self.parse("feature kern { pos A 50; } kern;")
        single_pos = doc.statements[0].statements[0]
        self.assertIsInstance(single_pos, ast.SinglePosStatement)
        expected_dict = {
            "SinglePositioning": {
                "Positions": [
                    {
                        "Glyph": {"Glyph": "A"},
                        "Value": {"ValueRecord": {"XAdvance": 50}},
                    }
                ]
            }
        }
        self.assertEqual(single_pos.toDict(), expected_dict)

    def test_subtableStatement_toDict(self):
        doc = self.parse("feature test { subtable; } test;")
        subtable_stmt = doc.statements[0].statements[0]
        self.assertIsInstance(subtable_stmt, ast.SubtableStatement)
        expected_dict = "Subtable"
        self.assertEqual(subtable_stmt.toDict(), expected_dict)

    def test_nameRecord_toDict(self):
        doc = self.parse('table name { nameid 1 "Family Name"; } name;')
        name_record = doc.statements[0].statements[0]
        self.assertIsInstance(name_record, ast.NameRecord)
        expected_dict = {
            "NameRecord": {
                "String": "Family Name",
                "PlatformID": 3,
                "PlatformEncodingID": 1,
                "LanguageID": 1033,
            }
        }
        actual_dict = name_record.toDict()
        self.assertEqual(name_record.toDict(), expected_dict)

    def test_featureNameStatement_toDict(self):
        doc = self.parse('feature ss01 { featureNames { name "Alternate 1"; }; } ss01;')
        name_stmt = doc.statements[0].statements[0].statements[0]
        self.assertIsInstance(name_stmt, ast.FeatureNameStatement)
        expected_dict = {
            "FeatureName": {
                "Type": "Name",
                "String": "Alternate 1",
                "PlatformID": 3,
                "PlatformEncodingID": 1,
                "LanguageID": 1033,
            }
        }
        # Simplify check for default name record attributes
        actual_dict = name_stmt.toDict()
        self.assertEqual(actual_dict["FeatureName"]["String"], "Alternate 1")
        self.assertEqual(actual_dict["FeatureName"]["Type"], "Name")
        self.assertIn("PlatformID", actual_dict["FeatureName"])
        self.assertIn("PlatformEncodingID", actual_dict["FeatureName"])
        self.assertIn("LanguageID", actual_dict["FeatureName"])

    def test_statNameStatement_toDict(self):
        doc = self.parse('table STAT { DesignAxis wght 0 { name "Weight"; }; } STAT;')
        name_stmt = doc.statements[0].statements[0].names[0]
        self.assertIsInstance(name_stmt, ast.STATNameStatement)
        expected_dict = {
            "STATName": {
                "String": "Weight",
                "PlatformID": 3,
                "PlatformEncodingID": 1,
                "LanguageID": 1033,
            }
        }
        # Simplify check for default name record attributes
        actual_dict = name_stmt.toDict()
        self.assertEqual(actual_dict["STATName"]["String"], "Weight")
        self.assertIn("PlatformID", actual_dict["STATName"])
        self.assertIn("PlatformEncodingID", actual_dict["STATName"])
        self.assertIn("LanguageID", actual_dict["STATName"])

    def test_cvParametersNameStatement_toDict(self):
        doc = self.parse(
            'feature cv01 { cvParameters { FeatUILabelNameID { name "Cv Param Name"; }; }; } cv01;'
        )
        name_stmt = doc.statements[0].statements[0].statements[0].statements[0]
        self.assertIsInstance(name_stmt, ast.CVParametersNameStatement)
        expected_dict = {
            "CVParametersName": {
                "String": "Cv Param Name",
                "PlatformID": 3,
                "PlatformEncodingID": 1,
                "LanguageID": 1033,
            }
        }
        actual_dict = name_stmt.toDict()
        self.assertEqual(actual_dict["CVParametersName"]["String"], "Cv Param Name")
        self.assertIn("PlatformID", actual_dict["CVParametersName"])
        self.assertIn("PlatformEncodingID", actual_dict["CVParametersName"])
        self.assertIn("LanguageID", actual_dict["CVParametersName"])

    def test_sizeParameters_toDict(self):
        doc = self.parse("feature size { parameters 10.0 1 80 120; } size;")
        size_params = doc.statements[0].statements[0]
        self.assertIsInstance(size_params, ast.SizeParameters)
        expected_dict = {
            "SizeParameters": {
                "DesignSize": 10.0,
                "SubfamilyID": 1,
                "RangeStart": 80,
                "RangeEnd": 120,
            }
        }
        self.assertEqual(size_params.toDict(), expected_dict)

    def test_characterStatement_toDict(self):
        doc = self.parse("feature cv01 { cvParameters { Character 65; }; } cv01;")
        char_stmt = doc.statements[0].statements[0].statements[0]
        self.assertIsInstance(char_stmt, ast.CharacterStatement)
        expected_dict = {"Character": 65}
        self.assertEqual(char_stmt.toDict(), expected_dict)

    def test_os2Field_toDict(self):
        doc = self.parse("table OS/2 { TypoAscender 750; } OS/2;")
        os2_field = doc.statements[0].statements[0]
        self.assertIsInstance(os2_field, ast.OS2Field)
        expected_dict = {"OS2Field": {"TypoAscender": 750}}
        self.assertEqual(os2_field.toDict(), expected_dict)

    def test_hheaField_toDict(self):
        doc = self.parse("table hhea { CaretOffset 50; } hhea;")
        hhea_field = doc.statements[0].statements[0]
        self.assertIsInstance(hhea_field, ast.HheaField)
        expected_dict = {"HheaField": {"CaretOffset": 50}}
        self.assertEqual(hhea_field.toDict(), expected_dict)

    def test_vheaField_toDict(self):
        doc = self.parse("table vhea { VertTypoAscender 800; } vhea;")
        vhea_field = doc.statements[0].statements[0]
        self.assertIsInstance(vhea_field, ast.VheaField)
        expected_dict = {"VheaField": {"VertTypoAscender": 800}}
        self.assertEqual(vhea_field.toDict(), expected_dict)

    def test_statDesignAxisStatement_toDict(self):
        doc = self.parse('table STAT { DesignAxis wght 0 { name "Weight"; }; } STAT;')
        design_axis = doc.statements[0].statements[0]
        self.assertIsInstance(design_axis, ast.STATDesignAxisStatement)
        expected_dict = {
            "STATDesignAxis": {
                "Tag": "wght",
                "AxisOrder": 0,
                "Names": [
                    {
                        "STATName": {
                            "String": "Weight",
                            "PlatformID": 3,
                            "PlatformEncodingID": 1,
                            "LanguageID": 1033,
                        }
                    }
                ],
            }
        }
        self.assertEqual(
            design_axis.toDict(),
            expected_dict,
        )

    def test_elidedFallbackName_toDict(self):
        doc = self.parse('table STAT { ElidedFallbackName { name "Regular"; }; } STAT;')
        elided_name = doc.statements[0].statements[0]
        self.assertIsInstance(elided_name, ast.ElidedFallbackName)
        expected_dict = {
            "ElidedFallbackName": {
                "Names": [
                    {
                        "STATName": {
                            "String": "Regular",
                            "PlatformID": 3,
                            "PlatformEncodingID": 1,
                            "LanguageID": 1033,
                        }
                    }
                ]
            }
        }
        self.assertEqual(elided_name.toDict(), expected_dict)

    def test_elidedFallbackNameID_toDict(self):
        doc = self.parse("table STAT { ElidedFallbackNameID 256; } STAT;")
        elided_id = doc.statements[0].statements[0]
        self.assertIsInstance(elided_id, ast.ElidedFallbackNameID)
        expected_dict = {"ElidedFallbackNameID": 256}
        self.assertEqual(elided_id.toDict(), expected_dict)

    def test_statAxisValueStatement_toDict(self):
        doc = self.parse(
            'table STAT { DesignAxis wght 0 { name "Weight"; }; AxisValue { location wght 400; name "Regular"; flag ElidableAxisValueName; }; } STAT;'
        )
        axis_value = doc.statements[0].statements[1]
        self.assertIsInstance(axis_value, ast.STATAxisValueStatement)
        expected_dict = {
            "STATAxisValue": {
                "Locations": [{"AxisValueLocation": {"Tag": "wght", "Values": [400]}}],
                "Names": [
                    {
                        "STATName": {
                            "String": "Regular",
                            "PlatformID": 3,
                            "PlatformEncodingID": 1,
                            "LanguageID": 1033,
                        }
                    }
                ],
                "Flags": ["ElidableAxisValueName"],
            }
        }
        self.assertEqual(axis_value.toDict(), expected_dict)

    def test_axisValueLocationStatement_toDict(self):
        doc = self.parse(
            'table STAT { DesignAxis wght 0 { name "Weight"; }; AxisValue { location wght 400 300 500; name "Regular"; }; } STAT;'
        )
        axis_value_statement = doc.statements[0].statements[
            1
        ]  # Get the AxisValue statement
        axis_loc = axis_value_statement.locations[0]  # Get the location from it
        self.assertIsInstance(axis_loc, ast.AxisValueLocationStatement)
        expected_dict = {
            "AxisValueLocation": {"Tag": "wght", "Values": [400, 300, 500]}
        }
        self.assertEqual(axis_loc.toDict(), expected_dict)

    def test_conditionsetStatement_toDict(self):
        doc = self.parse("conditionset Cond1 { wght 400 700; wdth 75 100; } Cond1;")
        cond_set = doc.statements[0]
        self.assertIsInstance(cond_set, ast.ConditionsetStatement)
        expected_dict = {
            "ConditionSet": {
                "Name": "Cond1",
                "Conditions": {
                    "wght": {"Min": 400, "Max": 700},
                    "wdth": {"Min": 75, "Max": 100},
                },
            }
        }
        self.assertEqual(cond_set.toDict(), expected_dict)

    def test_variationBlock_toDict(self):
        doc = self.parse(
            "conditionset Cond1 { wght 700 900; } Cond1; variation rvrn Cond1 { sub A by B; } rvrn;"
        )
        var_block = doc.statements[1]
        self.assertIsInstance(var_block, ast.VariationBlock)
        expected_dict = {
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
        }
        self.assertEqual(var_block.toDict(), expected_dict)

    def test_attachStatement_toDict_class(self):
        doc = self.parse("@C = [a e]; table GDEF { Attach @C 2; } GDEF;")
        attach_stmt = doc.statements[1].statements[0]
        self.assertIsInstance(attach_stmt, ast.AttachStatement)
        expected_dict = {
            "Attach": {
                "Glyphs": {"ClassName": "C"},
                "ContourPoints": [2],
            }
        }
        actual = attach_stmt.toDict()
        self.assertEqual(actual, expected_dict)

    def test_glyphClass_toDict_empty(self):
        doc = self.parse("@empty = [];")
        gc_def = doc.statements[0]
        glyph_class = gc_def.glyphs
        self.assertIsInstance(glyph_class, ast.GlyphClass)
        expected_dict = {"GlyphClass": []}
        self.assertEqual(glyph_class.toDict(), expected_dict)

    def test_glyphClass_toDict_from_markClass(self):
        doc = self.parse("markClass acute <anchor 0 0> @MC; @GC = [@MC ogonek];")
        gc_def = doc.statements[1]
        glyph_class = gc_def.glyphs
        self.assertIsInstance(glyph_class, ast.GlyphClass)
        expected_dict = {"GlyphClass": [{"ClassName": "MC"}, {"Glyph": "ogonek"}]}
        self.assertEqual(glyph_class.toDict(), expected_dict)

    def test_glyphClass_toDict_range_cid(self):
        doc = self.parse(r"@myRange = [\999-\1001];")
        gc_def = doc.statements[0]
        glyph_class = gc_def.glyphs
        self.assertIsInstance(glyph_class, ast.GlyphClass)
        expected_dict = {
            "GlyphClass": [{"GlyphRange": ({"Glyph": "\\999"}, {"Glyph": "\\1001"})}]
        }
        self.assertEqual(glyph_class.toDict(), expected_dict)

    def test_glyphClassDefStatement_toDict_empty(self):
        doc = self.parse("table GDEF { GlyphClassDef ,,,; } GDEF;")
        gcd_stmt = doc.statements[0].statements[0]
        self.assertIsInstance(gcd_stmt, ast.GlyphClassDefStatement)
        expected_dict = {"GlyphTypeDefinitions": {}}
        self.assertEqual(gcd_stmt.toDict(), expected_dict)

    def test_ignorePosStatement_toDict_multiple(self):
        doc = self.parse("feature test { ignore pos A B' C, X Y' Z; } test;")
        ign_pos = doc.statements[0].statements[0]
        self.assertIsInstance(ign_pos, ast.IgnorePosStatement)
        expected_dict = {
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
        }
        self.assertEqual(ign_pos.toDict(), expected_dict)

    def test_ignoreSubstStatement_toDict_multiple(self):
        doc = self.parse("feature test { ignore sub A B' C, X Y' Z; } test;")
        ign_sub = doc.statements[0].statements[0]
        self.assertIsInstance(ign_sub, ast.IgnoreSubstStatement)
        expected_dict = {
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
        }
        self.assertEqual(ign_sub.toDict(), expected_dict)

    def test_languageStatement_toDict_default(self):
        doc = self.parse("feature test { language NLD; } test;")
        lang_stmt = doc.statements[0].statements[0]
        self.assertIsInstance(lang_stmt, ast.LanguageStatement)
        expected_dict = {"Language": "NLD"}
        self.assertEqual(lang_stmt.toDict(), expected_dict)

    def test_languageStatement_toDict_exclude(self):
        doc = self.parse("feature test { language NLD exclude_dflt; } test;")
        lang_stmt = doc.statements[0].statements[0]
        self.assertIsInstance(lang_stmt, ast.LanguageStatement)
        expected_dict = {"Language": "NLD", "ExcludeDefault": True}
        self.assertEqual(lang_stmt.toDict(), expected_dict)

    def test_languageStatement_toDict_exclude_required(self):
        doc = self.parse("feature test { language NLD exclude_dflt required; } test;")
        lang_stmt = doc.statements[0].statements[0]
        self.assertIsInstance(lang_stmt, ast.LanguageStatement)
        expected_dict = {
                "Language": "NLD",
                "ExcludeDefault": True,
                "Required": True,
        }
        self.assertEqual(lang_stmt.toDict(), expected_dict)

    def test_ligatureCaretByIndexStatement_toDict_class(self):
        doc = self.parse(
            "@L = [f_f_i f_l]; table GDEF { LigatureCaretByIndex @L 2 4; } GDEF;"
        )
        lig_caret = doc.statements[1].statements[0]
        self.assertIsInstance(lig_caret, ast.LigatureCaretByIndexStatement)
        expected_dict = {
            "LigatureCaretByIndex": {
                "Glyphs": {"ClassName": "L"},
                "Carets": [2, 4],
            }
        }
        self.assertEqual(lig_caret.toDict(), expected_dict)

    def test_ligatureCaretByPosStatement_toDict_class(self):
        doc = self.parse(
            "@L = [f_f_i f_l]; table GDEF { LigatureCaretByPos @L 300 600; } GDEF;"
        )
        lig_caret = doc.statements[1].statements[0]
        self.assertIsInstance(lig_caret, ast.LigatureCaretByPosStatement)
        expected_dict = {
            "LigatureCaretByPosition": {
                "Glyphs": {"ClassName": "L"},
                "Carets": [300, 600],
            }
        }
        self.assertEqual(lig_caret.toDict(), expected_dict)

    def test_lookupBlock_toDict_useExtension(self):
        doc = self.parse("lookup MYLOOKUP useExtension { sub A by B; } MYLOOKUP;")
        lookup_block = doc.statements[0]
        self.assertIsInstance(lookup_block, ast.LookupBlock)
        expected_dict = {
            "LookupBlock": {
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
        }
        self.assertEqual(lookup_block.toDict(), expected_dict)

    def test_lookupFlagStatement_toDict_multiple_flags(self):
        doc = self.parse("lookup L { lookupflag RightToLeft IgnoreMarks; } L;")
        lookup_flag = doc.statements[0].statements[0]
        self.assertIsInstance(lookup_flag, ast.LookupFlagStatement)
        expected_dict = {"LookupFlag": {"Flags": ["RightToLeft", "IgnoreMarks"]}}
        self.assertEqual(lookup_flag.toDict(), expected_dict)

    def test_lookupFlagStatement_toDict_markAttachment(self):
        doc = self.parse(
            "markClass acute <anchor 0 0> @MC; lookup L { lookupflag MarkAttachmentType @MC; } L;"
        )
        lookup_flag = doc.statements[1].statements[0]
        self.assertIsInstance(lookup_flag, ast.LookupFlagStatement)
        expected_dict = {"LookupFlag": {"MarkAttachment": {"ClassName": "MC"}}}
        self.assertEqual(lookup_flag.toDict(), expected_dict)

    def test_lookupFlagStatement_toDict_markAttachment_class(self):
        doc = self.parse("lookup L { lookupflag MarkAttachmentType [acute grave]; } L;")
        lookup_flag = doc.statements[0].statements[0]
        self.assertIsInstance(lookup_flag, ast.LookupFlagStatement)
        expected_dict = {
            "LookupFlag": {
                "MarkAttachment": {
                    "GlyphClass": [{"Glyph": "acute"}, {"Glyph": "grave"}]
                }
            }
        }
        self.assertEqual(lookup_flag.toDict(), expected_dict)

    def test_lookupFlagStatement_toDict_numeric(self):
        doc = self.parse("lookup L { lookupflag 8; } L;")  # 8 = IgnoreMarks
        lookup_flag = doc.statements[0].statements[0]
        self.assertIsInstance(lookup_flag, ast.LookupFlagStatement)
        expected_dict = {"LookupFlag": {"Flags": ["IgnoreMarks"]}}
        self.assertEqual(lookup_flag.toDict(), expected_dict)

    def test_lookupFlagStatement_toDict_zero(self):
        doc = self.parse("lookup L { lookupflag 0; } L;")
        lookup_flag = doc.statements[0].statements[0]
        self.assertIsInstance(lookup_flag, ast.LookupFlagStatement)
        expected_dict = {"LookupFlag": {}}
        self.assertEqual(lookup_flag.toDict(), expected_dict)

    def test_singlePosStatement_toDict_class_horiz(self):
        doc = self.parse("feature kern { @V = [A V]; pos @V -50; } kern;")
        single_pos = doc.statements[0].statements[1]
        self.assertIsInstance(single_pos, ast.SinglePosStatement)
        expected_dict = {
            "SinglePositioning": {
                "Positions": [
                    {
                        "Glyph": {"ClassName": "V"},
                        "Value": {"ValueRecord": {"XAdvance": -50}},
                    }
                ]
            }
        }
        self.assertEqual(single_pos.toDict(), expected_dict)

    def test_pairPosStatement_toDict_formatA_multiple_values(self):
        doc = self.parse("feature kern { pos A 50 B 60; } kern;")
        pair_pos = doc.statements[0].statements[0]
        self.assertIsInstance(pair_pos, ast.PairPosStatement)
        expected_dict = {
            "PairPositioning": {
                "First": {"Glyph": "A"},
                "Value1": {"ValueRecord": {"XAdvance": 50}},
                "Second": {"Glyph": "B"},
                "Value2": {"ValueRecord": {"XAdvance": 60}},
                "Enumerated": False,
            }
        }
        self.assertEqual(pair_pos.toDict(), expected_dict)

    def test_singlePosStatement_toDict_chained(self):
        doc = self.parse("feature kern { pos A' 50 B; } kern;")
        single_pos = doc.statements[0].statements[0]
        self.assertIsInstance(single_pos, ast.SinglePosStatement)
        expected_dict = {
            "SinglePositioning": {
                "Positions": [
                    {
                        "Glyph": {"Glyph": "A"},
                        "Value": {"ValueRecord": {"XAdvance": 50}},
                    }
                ],
                "Suffix": [{"Glyph": "B"}],
            }
        }
        self.assertEqual(single_pos.toDict(), expected_dict)

    def test_pairPosStatement_toDict_formatA_class(self):
        doc = self.parse("feature kern { @A = [A]; @B = [B]; pos @A -50 @B 20; } kern;")
        pair_pos = doc.statements[0].statements[2]
        self.assertIsInstance(pair_pos, ast.PairPosStatement)
        expected_dict = {
            "PairPositioning": {
                "First": {"ClassName": "A"},
                "Value1": {"ValueRecord": {"XAdvance": -50}},
                "Second": {"ClassName": "B"},
                "Value2": {"ValueRecord": {"XAdvance": 20}},
                "Enumerated": False,
            }
        }
        self.assertEqual(pair_pos.toDict(), expected_dict)

    def test_pairPosStatement_toDict_formatA_enumerated(self):
        doc = self.parse("feature kern { enum pos A -50 B 20; } kern;")
        pair_pos = doc.statements[0].statements[0]
        self.assertIsInstance(pair_pos, ast.PairPosStatement)
        expected_dict = {
            "PairPositioning": {
                "First": {"Glyph": "A"},
                "Value1": {"ValueRecord": {"XAdvance": -50}},
                "Second": {"Glyph": "B"},
                "Value2": {"ValueRecord": {"XAdvance": 20}},
                "Enumerated": True,
            }
        }
        self.assertEqual(pair_pos.toDict(), expected_dict)

    def test_pairPosStatement_toDict_formatA_null_first(self):
        doc = self.parse("feature kern { pos A <NULL> B 20; } kern;")
        pair_pos = doc.statements[0].statements[0]
        self.assertIsInstance(pair_pos, ast.PairPosStatement)
        expected_dict = {
            "PairPositioning": {
                "First": {"Glyph": "A"},
                "Value1": None,
                "Second": {"Glyph": "B"},
                "Value2": {"ValueRecord": {"XAdvance": 20}},
                "Enumerated": False,
            }
        }
        self.assertEqual(pair_pos.toDict(), expected_dict)

    def test_pairPosStatement_toDict_formatA_null_second(self):
        doc = self.parse("feature kern { pos A -50 B <NULL>; } kern;")
        pair_pos = doc.statements[0].statements[0]
        self.assertIsInstance(pair_pos, ast.PairPosStatement)
        expected_dict = {
            "PairPositioning": {
                "First": {"Glyph": "A"},
                "Value1": {"ValueRecord": {"XAdvance": -50}},
                "Second": {"Glyph": "B"},
                "Value2": None,
                "Enumerated": False,
            }
        }
        self.assertEqual(pair_pos.toDict(), expected_dict)

    def test_pairPosStatement_toDict_formatB_class(self):
        doc = self.parse("feature kern { @A = [A]; @B = [B]; pos @A @B -50; } kern;")
        pair_pos = doc.statements[0].statements[2]
        self.assertIsInstance(pair_pos, ast.PairPosStatement)
        expected_dict = {
            "PairPositioning": {
                "First": {"ClassName": "A"},
                "Value1": {"ValueRecord": {"XAdvance": -50}},
                "Second": {"ClassName": "B"},
                "Enumerated": False,
            }
        }
        self.assertEqual(pair_pos.toDict(), expected_dict)

    def test_pairPosStatement_toDict_enumerated_class(self):
        doc = self.parse(
            "feature kern { @A = [A]; @B = [B]; enum pos @A @B -50; } kern;"
        )
        pair_pos = doc.statements[0].statements[2]
        self.assertIsInstance(pair_pos, ast.PairPosStatement)
        expected_dict = {
            "PairPositioning": {
                "First": {"ClassName": "A"},
                "Value1": {"ValueRecord": {"XAdvance": -50}},
                "Second": {"ClassName": "B"},
                "Enumerated": True,
            }
        }
        self.assertEqual(pair_pos.toDict(), expected_dict)

    def test_cursivePosStatement_toDict_class(self):
        doc = self.parse(
            "feature curs { @C = [A B]; pos cursive @C <anchor 10 20> <anchor 30 40>; } curs;"
        )
        curs_pos = doc.statements[0].statements[1]
        self.assertIsInstance(curs_pos, ast.CursivePosStatement)
        expected_dict = {
            "CursivePositioning": {
                "Class": {"ClassName": "C"},
                "Entry": {"Anchor": {"X": 10, "Y": 20}},
                "Exit": {"Anchor": {"X": 30, "Y": 40}},
            }
        }
        self.assertEqual(curs_pos.toDict(), expected_dict)

    def test_markBasePosStatement_toDict_class_multiple(self):
        doc = self.parse(
            "markClass acute <anchor 0 0> @TOP; markClass cedilla <anchor 0 0> @BOT;"
            "feature test { @B = [A E]; pos base @B <anchor 150 450> mark @TOP <anchor 150 -50> mark @BOT; } test;"
        )
        mark_base = doc.statements[2].statements[1]
        self.assertIsInstance(mark_base, ast.MarkBasePosStatement)
        expected_dict = {
            "MarkBasePositioning": {
                "Base": {"ClassName": "B"},
                "Marks": [
                    {"Anchor": {"Anchor": {"X": 150, "Y": 450}}, "MarkClass": "TOP"},
                    {"Anchor": {"Anchor": {"X": 150, "Y": -50}}, "MarkClass": "BOT"},
                ],
            }
        }
        self.assertEqual(mark_base.toDict(), expected_dict)

    def test_markLigPosStatement_toDict_class(self):
        doc = self.parse(
            "markClass acute <anchor 0 0> @TOP; feature test { @L = [f_f_i f_l]; pos ligature @L <anchor 100 400> mark @TOP ligComponent <anchor NULL>; } test;"
        )
        mark_lig = doc.statements[1].statements[1]
        self.assertIsInstance(mark_lig, ast.MarkLigPosStatement)
        expected_dict = {
            "MarkLigaturePositioning": {
                "Ligatures": {"ClassName": "L"},
                "Marks": [
                    [{"Anchor": {"Anchor": {"X": 100, "Y": 400}}, "MarkClass": "TOP"}],
                    {"Anchor": None},
                ],
            }
        }
        self.assertEqual(mark_lig.toDict(), expected_dict)

    def test_markMarkPosStatement_toDict_class(self):
        doc = self.parse(
            "markClass acute <anchor 0 0> @TOP; markClass grave <anchor 0 0> @TOP2; "
            "feature test { @M = [acute grave]; pos mark @M <anchor 0 50> mark @TOP2; } test;"
        )
        mark_mark = doc.statements[2].statements[1]
        self.assertIsInstance(mark_mark, ast.MarkMarkPosStatement)
        expected_dict = {
            "MarkToMarkPositioning": {
                "Base": {"ClassName": "M"},
                "Marks": [
                    {"Anchor": {"Anchor": {"X": 0, "Y": 50}}, "MarkClass": "TOP2"}
                ],
            }
        }
        self.assertEqual(mark_mark.toDict(), expected_dict)

    def test_chainContextPosStatement_toDict_multiple(self):
        doc = self.parse(
            "lookup L1 { pos I 10; } L1; lookup L2 { pos N 20; } L2; "
            "feature test { pos A B I' lookup L1 N' lookup L2 P; } test;"
        )
        chain_pos = doc.statements[2].statements[0]
        self.assertIsInstance(chain_pos, ast.ChainContextPosStatement)
        expected_dict = {
            "ChainContextualPositioning": {
                "Prefix": [{"Glyph": "A"}, {"Glyph": "B"}],
                "ChainedLookups": [
                    {"Glyph": "I", "Lookups": ["L1"]},
                    {"Glyph": "N", "Lookups": ["L2"]},
                ],
                "Suffix": [{"Glyph": "P"}],
            }
        }
        self.assertEqual(chain_pos.toDict(), expected_dict)

    def test_markClassDefinition_toDict_class(self):
        doc = self.parse("markClass [acute grave] <anchor 300 500> @TOP_MARKS;")
        mcd_stmt = doc.statements[0]
        self.assertIsInstance(mcd_stmt, ast.MarkClassDefinition)
        expected_dict = {
            "MarkClassDefinition": {
                "Name": "TOP_MARKS",
                "Anchor": {"Anchor": {"X": 300, "Y": 500}},
                "Glyphs": {"GlyphClass": [{"Glyph": "acute"}, {"Glyph": "grave"}]},
            }
        }
        self.assertEqual(mcd_stmt.toDict(), expected_dict)

    def test_nameRecord_toDict_specific_ids(self):
        doc = self.parse('table name { nameid 1 1 0 18 "Test Name"; } name;')
        name_record = doc.statements[0].statements[0]
        self.assertIsInstance(name_record, ast.NameRecord)
        expected_dict = {
            "NameRecord": {
                "String": "Test Name",
                "PlatformID": 1,
                "PlatformEncodingID": 0,
                "LanguageID": 18,
            }
        }
        self.assertEqual(name_record.toDict(), expected_dict)

    def test_reverseChainSingleSubstStatement_toDict_class(self):
        doc = self.parse("feature test { @B = [B b]; rsub A @B' C by D; } test;")
        rsub = doc.statements[0].statements[1]
        self.assertIsInstance(rsub, ast.ReverseChainSingleSubstStatement)
        expected_dict = {
            "ReverseChainSingleSubstitution": {
                "Prefix": [{"Glyph": "A"}],
                "In": [{"ClassName": "B"}],
                "Suffix": [{"Glyph": "C"}],
                "Out": [{"Glyph": "D"}],
            }
        }
        self.assertEqual(rsub.toDict(), expected_dict)

    def test_reverseChainSingleSubstStatement_toDict_range(self):
        doc = self.parse("feature test { rsub A [a-c]' D by X; } test;")
        rsub = doc.statements[0].statements[0]
        self.assertIsInstance(rsub, ast.ReverseChainSingleSubstStatement)
        expected_dict = {
            "ReverseChainSingleSubstitution": {
                "Prefix": [{"Glyph": "A"}],
                "In": [
                    {"GlyphClass": [{"GlyphRange": ({"Glyph": "a"}, {"Glyph": "c"})}]}
                ],
                "Suffix": [{"Glyph": "D"}],
                "Out": [{"Glyph": "X"}],
            }
        }
        self.assertEqual(rsub.toDict(), expected_dict)

    def test_elidedFallbackName_toDict_multiple(self):
        doc = self.parse(
            'table STAT { ElidedFallbackName { name "Reg"; name 1 0 18 "Rom"; }; } STAT;'
        )
        elided_name = doc.statements[0].statements[0]
        self.assertIsInstance(elided_name, ast.ElidedFallbackName)
        expected_dict = {
            "ElidedFallbackName": {
                "Names": [
                    {
                        "STATName": {
                            "String": "Reg",
                            "PlatformID": 3,
                            "PlatformEncodingID": 1,
                            "LanguageID": 1033,
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
        }
        self.assertEqual(elided_name.toDict(), expected_dict)

    def test_singleSubstStatement_toDict_chained(self):
        doc = self.parse("feature test { sub A' B by C; } test;")
        single_sub = doc.statements[0].statements[0]
        self.assertIsInstance(single_sub, ast.SingleSubstStatement)
        expected_dict = {
            "SingleSubstitution": {
                "In": [{"Glyph": "A"}],
                "Out": [{"Glyph": "C"}],
                "Suffix": [{"Glyph": "B"}],
            }
        }
        self.assertEqual(single_sub.toDict(), expected_dict)

    def test_singleSubstStatement_toDict_class(self):
        doc = self.parse("feature smcp { @lower = [a b]; sub @lower by a.sc; } smcp;")
        single_sub = doc.statements[0].statements[1]
        self.assertIsInstance(single_sub, ast.SingleSubstStatement)
        expected_dict = {
            "SingleSubstitution": {
                "In": [{"ClassName": "lower"}],
                "Out": [{"Glyph": "a.sc"}],
            }
        }
        self.assertEqual(single_sub.toDict(), expected_dict)

    def test_singleSubstStatement_toDict_class_chained(self):
        doc = self.parse(
            "feature smcp { @lower = [a b]; sub C @lower' D by a.sc; } smcp;"
        )
        single_sub = doc.statements[0].statements[1]
        self.assertIsInstance(single_sub, ast.SingleSubstStatement)
        expected_dict = {
            "SingleSubstitution": {
                "Prefix": [{"Glyph": "C"}],
                "In": [{"ClassName": "lower"}],
                "Suffix": [{"Glyph": "D"}],
                "Out": [{"Glyph": "a.sc"}],
            }
        }
        self.assertEqual(single_sub.toDict(), expected_dict)

    def test_singleSubstStatement_toDict_range(self):
        doc = self.parse("feature smcp { sub [a-c] by [A.sc-C.sc]; } smcp;")
        single_sub = doc.statements[0].statements[0]
        self.assertIsInstance(single_sub, ast.SingleSubstStatement)
        expected_dict = {
            "SingleSubstitution": {
                "In": [
                    {"GlyphClass": [{"GlyphRange": ({"Glyph": "a"}, {"Glyph": "c"})}]}
                ],
                "Out": [
                    {
                        "GlyphClass": [
                            {"GlyphRange": ({"Glyph": "A.sc"}, {"Glyph": "C.sc"})}
                        ]
                    }
                ],
            }
        }
        self.assertEqual(single_sub.toDict(), expected_dict)

    def test_singleSubstStatement_toDict_range_chained(self):
        doc = self.parse("feature smcp { sub X [a-c]' Y by [A.sc-C.sc]; } smcp;")
        single_sub = doc.statements[0].statements[0]
        self.assertIsInstance(single_sub, ast.SingleSubstStatement)
        expected_dict = {
            "SingleSubstitution": {
                "Prefix": [{"Glyph": "X"}],
                "In": [
                    {"GlyphClass": [{"GlyphRange": ({"Glyph": "a"}, {"Glyph": "c"})}]}
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
        }
        self.assertEqual(single_sub.toDict(), expected_dict)

    def test_multipleSubstStatement_toDict_chained(self):
        doc = self.parse("feature test { sub A f_i' B by f i; } test;")
        multi_sub = doc.statements[0].statements[0]
        self.assertIsInstance(multi_sub, ast.MultipleSubstStatement)
        expected_dict = {
            "MultipleSubstitution": {
                "Prefix": [{"Glyph": "A"}],
                "In": {"Glyph": "f_i"},
                "Suffix": [{"Glyph": "B"}],
                "Out": [{"Glyph": "f"}, {"Glyph": "i"}],
            }
        }
        self.assertEqual(multi_sub.toDict(), expected_dict)

    def test_multipleSubstStatement_toDict_force_chained(self):
        doc = self.parse("feature test { sub f_i' by f i; } test;")
        multi_sub = doc.statements[0].statements[0]
        self.assertIsInstance(multi_sub, ast.MultipleSubstStatement)
        expected_dict = {
            "MultipleSubstitution": {
                "In": {"Glyph": "f_i"},
                "Chained": True,
                "Out": [{"Glyph": "f"}, {"Glyph": "i"}],
            }
        }
        self.assertEqual(multi_sub.toDict(), expected_dict)

    def test_multipleSubstStatement_toDict_classes(self):
        doc = self.parse(
            "feature test { @IN = [f_i f_l]; @F = [f]; @IL = [i l]; sub @IN by @F @IL; } test;"
        )
        multi_sub = doc.statements[0].statements[3]
        self.assertIsInstance(multi_sub, ast.MultipleSubstStatement)
        expected_dict = {
            "MultipleSubstitution": {
                "In": {"ClassName": "IN"},
                "Out": [{"ClassName": "F"}, {"ClassName": "IL"}],
            }
        }
        self.assertEqual(multi_sub.toDict(), expected_dict)

    def test_multipleSubstStatement_toDict_classes_mixed(self):
        doc = self.parse(
            "feature test { @IN = [f_i f_l]; @IL = [i l]; sub @IN by f @IL; } test;"
        )
        multi_sub = doc.statements[0].statements[2]
        self.assertIsInstance(multi_sub, ast.MultipleSubstStatement)
        expected_dict = {
            "MultipleSubstitution": {
                "In": {"ClassName": "IN"},
                "Out": [{"Glyph": "f"}, {"ClassName": "IL"}],
            }
        }
        self.assertEqual(multi_sub.toDict(), expected_dict)

    def test_multipleSubstStatement_toDict_classes_mixed_singleton(self):
        doc = self.parse(
            "feature test { @IN = [f_i f_l]; @F = [f]; @IL = [i l]; sub @IN by @F @IL; } test;"
        )
        multi_sub = doc.statements[0].statements[
            3
        ]  # Re-using test_multipleSubstStatement_toDict_classes example as it fits
        self.assertIsInstance(multi_sub, ast.MultipleSubstStatement)
        expected_dict = {
            "MultipleSubstitution": {
                "In": {"ClassName": "IN"},
                "Out": [{"ClassName": "F"}, {"ClassName": "IL"}],
            }
        }
        self.assertEqual(multi_sub.toDict(), expected_dict)

    def test_alternateSubstStatement_toDict_chained(self):
        doc = self.parse("feature test { sub X a' Y from [a.1 a.2]; } test;")
        alt_sub = doc.statements[0].statements[0]
        self.assertIsInstance(alt_sub, ast.AlternateSubstStatement)
        expected_dict = {
            "AlternateSubstitution": {
                "Prefix": [{"Glyph": "X"}],
                "Suffix": [{"Glyph": "Y"}],
                "In": {"Glyph": "a"},
                "Out": {"GlyphClass": [{"Glyph": "a.1"}, {"Glyph": "a.2"}]},
            }
        }
        self.assertEqual(alt_sub.toDict(), expected_dict)

    def test_alternateSubstStatement_toDict_class(self):
        doc = self.parse("feature test { @ALT = [a.1 a.2]; sub a from @ALT; } test;")
        alt_sub = doc.statements[0].statements[1]
        self.assertIsInstance(alt_sub, ast.AlternateSubstStatement)
        expected_dict = {
            "AlternateSubstitution": {
                "In": {"Glyph": "a"},
                "Out": {"ClassName": "ALT"},
            }
        }
        self.assertEqual(alt_sub.toDict(), expected_dict)

    def test_ligatureSubstStatement_toDict_chained(self):
        doc = self.parse("feature liga { sub X f' f' i' Y by f_f_i; } liga;")
        lig_sub = doc.statements[0].statements[0]
        self.assertIsInstance(lig_sub, ast.LigatureSubstStatement)
        expected_dict = {
            "LigatureSubstitution": {
                "Prefix": [{"Glyph": "X"}],
                "In": [{"Glyph": "f"}, {"Glyph": "f"}, {"Glyph": "i"}],
                "Suffix": [{"Glyph": "Y"}],
                "Out": {"Glyph": "f_f_i"},
            }
        }
        self.assertEqual(lig_sub.toDict(), expected_dict)

    def test_chainContextSubstStatement_toDict_multiple(self):
        doc = self.parse(
            "lookup L1 { sub I by X; } L1; lookup L2 { sub N by Y; } L2; "
            "feature test { sub A B I' lookup L1 N' lookup L2 P; } test;"
        )
        chain_sub = doc.statements[2].statements[0]
        self.assertIsInstance(chain_sub, ast.ChainContextSubstStatement)
        expected_dict = {
            "ChainContextualSubstitution": {
                "Prefix": [{"Glyph": "A"}, {"Glyph": "B"}],
                "ChainedLookups": [
                    {"Glyph": "I", "Lookups": ["L1"]},
                    {"Glyph": "N", "Lookups": ["L2"]},
                ],
                "Suffix": [{"Glyph": "P"}],
            }
        }
        self.assertEqual(chain_sub.toDict(), expected_dict)

    def test_valueRecordDefinition_toDict_null(self):
        doc = self.parse("valueRecordDef <NULL> foo;")
        vr_def = doc.statements[0]
        self.assertIsInstance(vr_def, ast.ValueRecordDefinition)
        expected_dict = {
            "ValueRecordDefinition": {
                "Name": "foo",
                "Value": None,
            }
        }
        self.assertEqual(vr_def.toDict(), expected_dict)

    def test_valueRecordDefinition_toDict_named(self):
        doc = self.parse("valueRecordDef 100 foo; valueRecordDef <foo> bar;")
        vr_def = doc.statements[1]
        self.assertIsInstance(vr_def, ast.ValueRecordDefinition)
        expected_dict = {
            "ValueRecordDefinition": {
                "Name": "bar",
                "Value": {"ValueRecord": {"XAdvance": 100}},
            }
        }
        self.assertEqual(vr_def.toDict(), expected_dict)

    def test_valueRecord_toDict_multiple_devices(self):
        doc = self.parse(
            "feature kern { pos A <1 2 3 4 <device 10 100, 11 110> <device 12 120> <device NULL> <device NULL>> B; } kern;"
        )
        pair_pos = doc.statements[0].statements[0]
        value_rec = pair_pos.valuerecord1
        self.assertIsInstance(value_rec, ast.ValueRecord)
        expected_dict = {
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
        }
        self.assertEqual(value_rec.toDict(), expected_dict)

    def test_baseAxis_toDict(self):
        doc = self.parse(
            "table BASE { HorizAxis.BaseTagList foo  bar ; HorizAxis.BaseScriptList latn foo 0 0, DFLT bar 0 0 ; } BASE;"
        )
        base_axis = doc.statements[0].statements[0]
        self.assertIsInstance(base_axis, ast.BaseAxis)
        expected_dict = {
            "BaseAxis": {
                "Direction": "Horizontal",
                "Bases": ["foo", "bar"],
                "Scripts": [
                    {"Script": "latn", "Baseline": "foo", "Coordinates": [0, 0]},
                    {"Script": "DFLT", "Baseline": "bar", "Coordinates": [0, 0]},
                ],
            }
        }
        self.assertEqual(base_axis.toDict(), expected_dict)

    def test_os2Field_toDict_range(self):
        doc = self.parse("table OS/2 { UnicodeRange 0 1 2; } OS/2;")
        os2_field = doc.statements[0].statements[0]
        self.assertIsInstance(os2_field, ast.OS2Field)
        expected_dict = {"OS2Field": {"UnicodeRange": [0, 1, 2]}}
        self.assertEqual(os2_field.toDict(), expected_dict)

    def test_os2Field_toDict_vendor(self):
        doc = self.parse('table OS/2 { Vendor "TEST"; } OS/2;')
        os2_field = doc.statements[0].statements[0]
        self.assertIsInstance(os2_field, ast.OS2Field)
        expected_dict = {"OS2Field": {"Vendor": "TEST"}}
        self.assertEqual(os2_field.toDict(), expected_dict)

    def test_hheaField_toDict_lowercase(self):
        doc = self.parse("table hhea { Ascender 750; } hhea;")
        hhea_field = doc.statements[0].statements[0]
        self.assertIsInstance(hhea_field, ast.HheaField)
        expected_dict = {"HheaField": {"Ascender": 750}}


if __name__ == "__main__":
    unittest.main()
