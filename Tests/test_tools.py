from fontgadgets.tools import FontGadgetsError
from utils import *
import fontgadgets.tools
import fontgadgets.decorators
import inspect
import fontParts.fontshell

def test_getFontPartsObject():
	assert fontgadgets.tools.getFontPartsObject('Glyph') is fontParts.fontshell.RGlyph
	assert fontgadgets.tools.getFontPartsObject('foo') is None

def test_getDefconObject():
	assert fontgadgets.tools.getDefconObject('Glyph') is defcon.Glyph
	assert fontgadgets.tools.getDefconObject('foo') is None

def test_getObjectPackageName():
	assert fontgadgets.tools.getObjectPackageName(defcon.Glyph) == 'defcon'
	assert fontgadgets.tools.getObjectPackageName(fontParts.fontshell.RGlyph) == 'fontParts'

def test_wrapResultInFontParts(defcon_font_1):
	assert fontgadgets.tools.getWrapperClassForResultInFontParts(defcon.Font) is fontParts.fontshell.RFont
	assert fontgadgets.tools.getIterableWrapperClassForResultInFontParts(tuple[defcon.Font, dict]) == (fontParts.fontshell.RFont, None)
	assert fontgadgets.tools.wrapIterableResultInFontParts((defcon_font_1, {'a': 2}), (fontParts.fontshell.RFont, None)) == (fontParts.fontshell.RFont(defcon_font_1), {'a': 2})

def test_isObjFromFontParts():
	assert fontgadgets.tools.isObjFromFontParts(inspect._empty) is False
	assert fontgadgets.tools.isObjFromFontParts(defcon.Font) is False
	assert fontgadgets.tools.isObjFromFontParts(fontParts.fontshell.RContour) is True

def test_isObjFromDefcon():
	assert fontgadgets.tools.isObjFromDefcon(inspect._empty) is False
	assert fontgadgets.tools.isObjFromDefcon(defcon.Font) is True
	assert fontgadgets.tools.isObjFromDefcon(fontParts.fontshell.RContour) is False

def test_getFontPartWrapperForFunctResult():
	assert fontgadgets.tools.getFontPartWrapperForFunctResult(inspect._empty) is None

def funct_tester1(contour: defcon.Contour, arg2): # func without return annotation
	""" funct test doc """
	pass

def funct_tester2(segment, arg2) -> fontParts.fontshell.RContour: # func with one return annotation
	return fontParts.fontshell.RContour()

def funct_tester3(image: defcon.Image, arg2) -> tuple[defcon.Contour, tuple]: # func with mutliple return annotations
	return defcon.Contour(), tuple()

def property_tester1(contour): # property without return annotation
	""" property test doc 1 """
	pass

def property_tester2(segment) -> defcon.Contour: # property with one return annotation
	return defcon.Contour()

def property_tester3(anchor) -> tuple[fontParts.fontshell.RAnchor, str]: # property with mutliple return annotations
	""" property test doc 3 """
	return fontParts.fontshell.RAnchor(), str()

def test_getFontFunctionProperties():
	assert fontgadgets.tools.getFontFunctionProperties(funct_tester1) == fontgadgets.tools.FontFunctionProperties(
	funct_tester1,
	'funct_tester1',
	['contour', 'arg2'],
	""" funct test doc """,
	'defcon',
	'Contour',
	None,
	False,
	)
	assert fontgadgets.tools.getFontFunctionProperties(funct_tester2) == fontgadgets.tools.FontFunctionProperties(
	funct_tester2,
	'funct_tester2',
	['segment', 'arg2'],
	None,
	None,
	'Segment',
	None,
	False,
	)
	assert fontgadgets.tools.getFontFunctionProperties(funct_tester3) == fontgadgets.tools.FontFunctionProperties(
	funct_tester3,
	'funct_tester3',
	['image', 'arg2'],
	None,
	'defcon',
	'Image',
	(fontParts.fontshell.RContour, None),
	True,
	)
	assert fontgadgets.tools.getFontFunctionProperties(property_tester1) == fontgadgets.tools.FontFunctionProperties(
	property_tester1,
	'property_tester1',
	['contour'],
	""" property test doc 1 """,
	None,
	'Contour',
	None,
	False,
	)
	assert fontgadgets.tools.getFontFunctionProperties(property_tester2) == fontgadgets.tools.FontFunctionProperties(
	property_tester2,
	'property_tester2',
	['segment'],
	None,
	None,
	'Segment',
	fontParts.fontshell.RContour,
	False,
	)
	assert fontgadgets.tools.getFontFunctionProperties(property_tester3) == fontgadgets.tools.FontFunctionProperties(
	property_tester3,
	'property_tester3',
	['anchor'],
	""" property test doc 3 """,
	None,
	'Anchor',
	(None, None),
	True,
	)

def test_checkIfAttributeAlreadyExist():
	assert fontgadgets.tools.checkIfAttributeAlreadyExist(fontParts.fontshell.RFont, 'Font', 'testIfFunctExist1', 'fontParts') == ('fontgadgets.fontParts.Font.testIfFunctExist1', False)
	assert fontgadgets.tools.checkIfAttributeAlreadyExist(defcon.Font, 'Font', 'testIfFunctExist2', 'defcon') == ('fontgadgets.defcon.Font.testIfFunctExist2', False)
	with pytest.warns(Warning, match=r"Overriding an exising .+ fontgadgets method."):
		fontgadgets.tools.DEBUG = True

		@fontgadgets.decorators.font_method
		def testDebug(font):
			pass

		fontgadgets.tools.checkIfAttributeAlreadyExist(defcon.Font, 'Font', 'testDebug', 'defcon')
		fontgadgets.tools.DEBUG = False

def test_checkIfAttributeAlreadyExist_error():
	with pytest.raises(FontGadgetsError):
		fontgadgets.tools.checkIfAttributeAlreadyExist(fontParts.fontshell.RFont, 'Font', 'save', 'fontParts')
	with pytest.raises(FontGadgetsError):
		fontgadgets.tools.checkIfAttributeAlreadyExist(defcon.Font, 'Font', 'save', 'defcon')


def test_registerAsfont_method_error():
	def dummy_prop(glyph: defcon.Glyph): pass
	functInfo = fontgadgets.tools.getFontFunctionProperties(dummy_prop)
	with pytest.raises(FontGadgetsError, match="A function cannot be registered as both a property and a setter in the same call."):
		fontgadgets.tools.registerAsfont_method(functInfo, isProperty=True, isPropertySetter=True)


def test_font_property_setter():
    defcon_glyph_1 = defcon.Glyph()
    fontparts_glyph_1 = fontParts.fontshell.RGlyph(defcon_glyph_1)

    @fontgadgets.decorators.font_property
    def myCustomWidth(glyph):
        """Gets the custom width."""
        if not hasattr(glyph, '_customWidth'):
            glyph._customWidth = None
        return glyph._customWidth

    @fontgadgets.decorators.font_property_setter
    def myCustomWidth(glyph, value: int):
        """Sets the custom width."""
        glyph._customWidth = value

    assert isinstance(getattr(defcon.Glyph, 'myCustomWidth'), property)
    assert defcon_glyph_1.myCustomWidth == None
    defcon_glyph_1.myCustomWidth = 555
    assert defcon_glyph_1.myCustomWidth == 555
    assert fontparts_glyph_1.myCustomWidth == 555


def test_font_property_setter_errors():
	# Error: trying to
	with pytest.raises(FontGadgetsError, match="Cannot register setter. Property 'nonExistentProp' does not exist on 'defcon.Glyph'."):
		@fontgadgets.decorators.font_property_setter
		def nonExistentProp(glyph: defcon.Glyph, value):
			pass

	# Error: setter function with wrong number of arguments
	with pytest.raises(AssertionError, match="should have an font object name and a value arguments to be registered as a property"):
		# Need to define the property first
		@fontgadgets.decorators.font_property
		def anotherProp(glyph: defcon.Glyph):
			return 123

		@fontgadgets.decorators.font_property_setter
		def anotherProp(glyph: defcon.Glyph): # Missing value argument
			pass
