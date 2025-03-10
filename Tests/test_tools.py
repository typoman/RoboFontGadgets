from fontgadgets.tools import FontGadgetsError, inject
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

# Test basic injection into a single class
def test_basic_injection():
   class MyClass1:
       pass

   @inject(MyClass1)
   def injected_method_1(self, x):
       return x * 2

   my_instance_1 = MyClass1()
   assert my_instance_1.injected_method_1(5) == 10

# Test injection into multiple classes
def test_multiple_class_injection():
   class MyClass2:
       pass
   class MyClass3:
       pass

   @inject(MyClass2, MyClass3)
   def injected_method_2(self, y):
       return y + 10

   my_instance_2 = MyClass2()
   my_instance_3 = MyClass3()
   assert my_instance_2.injected_method_2(3) == 13
   assert my_instance_3.injected_method_2(7) == 17

# Test method name conflict with existing method (ValueError in normal mode)
def test_method_name_conflict():
   class MyClass5:
       def existing_method(self):
           return "Existing method"

   with pytest.raises(ValueError):
       @inject(MyClass5)
       def existing_method(self):  # Conflict with existing method
           return "Injected method"

# Test non-conflicting injection
def test_non_conflicting_injection():
   class MyClass5:
       def existing_method(self):
           return "Existing method"

   @inject(MyClass5)
   def injected_method_4(self):
       return "Non-conflicting injected method"

   my_instance_5 = MyClass5()
   assert my_instance_5.injected_method_4() == "Non-conflicting injected method"

# Test no target classes provided (TypeError)
def test_no_target_classes():
   with pytest.raises(TypeError):
       @inject()
       def some_method(self):
           pass

# Test empty list of target classes (TypeError)
def test_empty_target_classes():
   with pytest.raises(TypeError):
       @inject([])
       def some_method(self):
           pass

# Test invalid target class (not a class) (TypeError)
def test_invalid_target_class():
   my_variable = 10
   with pytest.raises(TypeError):
       @inject(my_variable)
       def some_method(self):
           pass

def test_reinjection_same_module():
    class MyClass4:
        pass

    @inject(MyClass4)
    def injected_method_3_v1(self):
        return "Initial injection"

    @inject(MyClass4)
    def injected_method_3_v2(self):  # Clearer naming
        return "Re-injected method"

    my_instance_4 = MyClass4()
    assert my_instance_4.injected_method_3_v2() == "Re-injected method"

def test_debug_mode_overwrite():
    try:
        fontgadgets.tools.DEBUG = True
        class MyClass6:
            def conflicting_method(self):
                return "Original method"

        @inject(MyClass6)
        def conflicting_method(self):
            return "Injected method in DEBUG mode"

        my_instance_6 = MyClass6()
        assert my_instance_6.conflicting_method() == "Injected method in DEBUG mode"
    finally:
        fontgadgets.tools.DEBUG = False

def test_error_messages():
    class MyClass7:
        pass

    with pytest.raises(TypeError, match="Expected a class in the decorator, but got:"):
        @inject("not_a_class")  # Invalid type
        def some_method(self):
            pass

