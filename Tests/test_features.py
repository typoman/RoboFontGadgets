from utils import *
from fontgadgets.extensions.features import *


@pytest.mark.parametrize(
    "glyphName, expectedNumberOfSourceGlyphs",
    [
        ("shadda-ar", 0),
        ("dot-ar", 0),
        ("_part.connectionFlat-ar", 0),
        ("alef-ar.fina.short", 0),
        ("yehbarree-ar.fina", 1),
        ("alefMaksura-ar.fina", 1),
        ("shaddaFathatan-ar", 2),
        ("_alefMaksura_meem-ar", 0),
    ],
)
def test_numberOfSourceGlyphs(
    defcon_ar_font_1, glyphName, expectedNumberOfSourceGlyphs
):
    glyph = defcon_ar_font_1[glyphName]
    assert glyph.features.numberOfSourceGlyphs == expectedNumberOfSourceGlyphs


@pytest.mark.parametrize(
    "glyphName, expectedNumLookups, expectedfeatures",
    [
        ("yehbarree-ar.fina", 1, ["fina"]),
        ("alefMaksura-ar.fina", 2, ["fina", "rlig"]),
        ("shaddaFathatan-ar", 1, ["ccmp"]),
    ],
)
def test_lookups(defcon_ar_font_1, glyphName, expectedNumLookups, expectedfeatures):
    glyph = defcon_ar_font_1[glyphName]
    lookups = glyph.features.lookups
    assert len(lookups) == expectedNumLookups, [l.asFea() for l in lookups.values()]


@pytest.mark.parametrize(
    "glyphName, expected_source_glyphs",
    [
        ("lam_alef-ar", ("lam-ar.init", "alef-ar.fina")),
        (
            "lam_alefMadda-ar",
            (
                "lam-ar.init",
                "alefMadda-ar.fina",
            ),
        ),
        ("allah-ar", ("alef-ar", "lam-ar.init", "lam-ar.medi", "heh-ar.fina")),
    ],
)
def test_sourceGlyphs(defcon_ar_font_1, glyphName, expected_source_glyphs):
    glyph = defcon_ar_font_1[glyphName]
    source_glyphs = glyph.features.sourceGlyphs
    assert tuple(source_glyphs.keys())[0] == expected_source_glyphs


@pytest.mark.parametrize(
    "glyphName, expected_features",
    [
        (
            "lam_alef-ar",
            {
                "fina": {("DFLT", "dflt"): ["sub lam_alef-ar by lam_alef-ar.fina;"]},
                "rlig": {
                    ("DFLT", "dflt"): ["sub lam-ar.init alef-ar.fina by lam_alef-ar;"]
                },
            },
        ),
        (
            "lam_alefMadda-ar",
            {
                "fina": {
                    ("DFLT", "dflt"): ["sub lam_alefMadda-ar by lam_alefMadda-ar.fina;"]
                },
                "rlig": {
                    ("DFLT", "dflt"): [
                        "sub lam-ar.init alefMadda-ar.fina by lam_alefMadda-ar;"
                    ]
                },
            },
        ),
        (
            "allah-ar",
            {
                "rlig": {
                    ("DFLT", "dflt"): [
                        "sub alef-ar lam-ar.init lam-ar.medi heh-ar.fina "
                        "by allah-ar;"
                    ]
                }
            },
        ),
    ],
)
def test_sourceGlyphs(defcon_ar_font_1, glyphName, expected_features):
    glyph = defcon_ar_font_1[glyphName]
    actual_features = glyph.features.rulesDict
    assert actual_features == expected_features
