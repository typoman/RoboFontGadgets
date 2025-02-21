from utils import *
import fontgadgets.extensions.compile
from fontTools.pens.t2CharStringPen import T2CharStringPen

@pytest.fixture
def compile_sample_1(defcon_font_1):
    f = defcon_font_1
    # add more required font data for compile
    f.info.unitsPerEm = 1000
    f.info.familyName = 'sample_1'
    f.info.styleName = 'style_1'
    f.info.ascender = 800
    f.info.descender = -200
    f.newGlyph(".notdef")
    f.newGlyph("space")
    f.features.text = "feature liga {sub seen sad by tah;} liga;"
    return f

def test_compile_sample_1(compile_sample_1):
    otf = compile_sample_1._emptyOTF
    # for comparing order of tables matter
    tables_to_check = list(sorted(['CFF ', 'hmtx', 'cmap']))
    assert fontIsSameAsTTXForGivenTables(otf, ttx='compile_sample_1-metrics_False-outlines_False-features_False.ttx', tables=tables_to_check)

def test_compile_sample_1_metrics(compile_sample_1):
    otf = compile_sample_1._otfWithMetrics
    tables_to_check = ['hmtx']
    assert fontIsSameAsTTXForGivenTables(otf, ttx='compile_sample_1-metrics_True-outlines_False-features_False.ttx', tables=tables_to_check)
#
def test_compile_sample_1_outlines(compile_sample_1):
    otf = compile_sample_1._otfWithOutlines
    tables_to_check = ['CFF ']
    assert fontIsSameAsTTXForGivenTables(otf, ttx='compile_sample_1-metrics_False-outlines_True-features_False.ttx', tables=tables_to_check)
#
def test_compile_sample_1_features(compile_sample_1):
    otf = compile_sample_1._emptyOTFWithFeatures
    tables_to_check = ['GSUB', ]
    assert fontIsSameAsTTXForGivenTables(otf, ttx='compile_sample_1-metrics_False-outlines_False-features_True.ttx', tables=tables_to_check)

