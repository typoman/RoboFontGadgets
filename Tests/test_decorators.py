import fontgadgets.decorators
from utils import *

FUNCT_EXECUTED_NUM = {}


@fontgadgets.decorators.font_method
def font_method_funct_tester1(font):
    """
    font_method funct tester 1 doc
    """
    return "test font_method 1"


@fontgadgets.decorators.font_method
def font_method_funct_tester2(font: defcon.Font):
    """
    font_method funct tester 2 doc
    """
    return "test font_method 2"


@fontgadgets.decorators.font_method
def font_method_funct_tester3(font) -> defcon.Contour:
    """
    font_method funct tester 3 doc
    """
    return defcon.Contour()


@fontgadgets.decorators.font_method
def font_method_funct_tester4(font) -> tuple[defcon.Font, str]:
    """
    font_method funct tester 4 doc
    """
    return defcon.Font(), "test 2"


def test_font_method(defcon_font_1, fontParts_font_1):
    assert defcon_font_1.font_method_funct_tester1() == "test font_method 1"
    assert fontParts_font_1.font_method_funct_tester1() == "test font_method 1"
    assert defcon_font_1.font_method_funct_tester2() == "test font_method 2"
    assert isinstance(defcon_font_1.font_method_funct_tester3(), defcon.Contour)
    assert isinstance(
        fontParts_font_1.font_method_funct_tester3(), fontParts.fontshell.RContour
    )
    assert isinstance(defcon_font_1.font_method_funct_tester4()[0], defcon.Font)
    assert isinstance(
        fontParts_font_1.font_method_funct_tester4()[0], fontParts.fontshell.RFont
    )
    assert defcon_font_1.font_method_funct_tester4()[1] == "test 2"


def test_destroyRepresentationsForNotification(defcon_font_1, fontParts_font_1):
    defcon_font_1.font_cached_method_funct_tester1()
    defcon_font_1.font_cached_method_funct_tester1()
    assert FUNCT_EXECUTED_NUM["font_cached_method_funct_tester"] == 1
    fontParts_font_1.font_cached_method_funct_tester1()
    assert FUNCT_EXECUTED_NUM["font_cached_method_funct_tester"] == 1
    defcon_font_1["C"].width += 1
    fontParts_font_1.font_cached_method_funct_tester1()
    assert FUNCT_EXECUTED_NUM["font_cached_method_funct_tester"] == 2


@fontgadgets.decorators.font_cached_method("Glyph.WidthChanged")
def font_cached_method_funct_tester1(font):
    """
    font_cached_method funct tester 1 doc
    """
    execute_num = FUNCT_EXECUTED_NUM.get("font_cached_method_funct_tester", 0)
    execute_num += 1
    FUNCT_EXECUTED_NUM["font_cached_method_funct_tester"] = execute_num
    return "test font_cached_method 1"


@fontgadgets.decorators.font_cached_method("Glyph.Changed")
def font_cached_method_funct_tester2(font: defcon.Font):
    """
    font_cached_method funct tester 2 doc
    """
    return "test font_cached_method 2"


@fontgadgets.decorators.font_cached_method("Glyph.Changed")
def font_cached_method_funct_tester3(font) -> defcon.Glyph:
    """
    font_cached_method funct tester 3 doc
    """
    return defcon.Glyph()


@fontgadgets.decorators.font_cached_method("Font.Changed")
def font_cached_method_funct_tester4(font) -> tuple[defcon.Glyph, str]:
    """
    font_cached_method funct tester 4 doc
    """
    return defcon.Glyph(), "test font_cached_method 4"


def test_font_cached_method(defcon_font_1, fontParts_font_1):
    assert defcon_font_1.font_cached_method_funct_tester1() == "test font_cached_method 1"
    assert fontParts_font_1.font_cached_method_funct_tester1() == "test font_cached_method 1"
    with pytest.raises(AttributeError):
        fontParts_font_1.font_cached_method_funct_tester2()
    assert defcon_font_1.font_cached_method_funct_tester2() == "test font_cached_method 2"
    assert isinstance(defcon_font_1.font_cached_method_funct_tester3(), defcon.Glyph)
    assert isinstance(defcon_font_1.font_cached_method_funct_tester4()[0], defcon.Glyph)
    assert defcon_font_1.font_cached_method_funct_tester4()[1], "test font_cached_method 4"

def test_invalid_notification(defcon_font_1, fontParts_font_1):
    with pytest.raises(FontGadgetsError, match="Invalid passed destructive notification"):
        @fontgadgets.decorators.font_cached_method("Glyph.MarginsChanged")
        def font_cached_method_funct_tester1(font):
            return
