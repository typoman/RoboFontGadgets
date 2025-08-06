import types
import fontParts.fontshell
import defcon
import inspect
from functools import wraps
from warnings import warn
from collections import namedtuple
import typing
from typing import Type, List, Tuple, Union

VALID_DEFCON_NOTIFCATIONS = {
    "Glyph.Changed",
    "Glyph.BeginUndo",
    "Glyph.EndUndo",
    "Glyph.BeginRedo",
    "Glyph.EndRedo",
    "Glyph.NameWillChange",
    "Glyph.NameChanged",
    "Glyph.UnicodesChanged",
    "Glyph.WidthChanged",
    "Glyph.HeightChanged",
    "Glyph.LeftMarginWillChange",
    "Glyph.LeftMarginDidChange",
    "Glyph.RightMarginWillChange",
    "Glyph.RightMarginDidChange",
    "Glyph.TopMarginWillChange",
    "Glyph.TopMarginDidChange",
    "Glyph.BottomMarginWillChange",
    "Glyph.BottomMarginDidChange",
    "Glyph.NoteChanged",
    "Glyph.LibChanged",
    "Glyph.ImageChanged",
    "Glyph.ImageWillBeDeleted",
    "Glyph.ContourWillBeAdded",
    "Glyph.ContourWillBeDeleted",
    "Glyph.ContoursChanged",
    "Glyph.ComponentWillBeAdded",
    "Glyph.ComponentWillBeDeleted",
    "Glyph.ComponentsChanged",
    "Glyph.AnchorWillBeAdded",
    "Glyph.AnchorWillBeDeleted",
    "Glyph.AnchorsChanged",
    "Glyph.GuidelineWillBeAdded",
    "Glyph.GuidelineWillBeDeleted",
    "Glyph.GuidelinesChanged",
    "Glyph.MarkColorChanged",
    "Glyph.VerticalOriginChanged",
    "Kerning.Changed",
    "Kerning.BeginUndo",
    "Kerning.EndUndo",
    "Kerning.BeginRedo",
    "Kerning.EndRedo",
    "Kerning.PairSet",
    "Kerning.PairDeleted",
    "Kerning.Cleared",
    "Kerning.Updated",
    "Anchor.Changed",
    "Anchor.XChanged",
    "Anchor.YChanged",
    "Anchor.NameChanged",
    "Anchor.ColorChanged",
    "Anchor.IdentifierChanged",
    "Lib.Changed",
    "Lib.BeginUndo",
    "Lib.EndUndo",
    "Lib.BeginRedo",
    "Lib.EndRedo",
    "Lib.ItemSet",
    "Lib.ItemDeleted",
    "Lib.Cleared",
    "Lib.Updated",
    "LayerSet.Changed",
    "LayerSet.LayersChanged",
    "LayerSet.LayerChanged",
    "LayerSet.DefaultLayerWillChange",
    "LayerSet.DefaultLayerChanged",
    "LayerSet.LayerOrderChanged",
    "LayerSet.LayerAdded",
    "LayerSet.LayerDeleted",
    "LayerSet.LayerWillBeDeleted",
    "LayerSet.LayerNameChanged",
    "Features.Changed",
    "Features.BeginUndo",
    "Features.EndUndo",
    "Features.BeginRedo",
    "Features.EndRedo",
    "Features.TextChanged",
    "Font.Changed",
    "Font.ReloadedGlyphs",
    "Font.GlyphOrderChanged",
    "Font.GuidelinesChanged",
    "Font.GuidelineWillBeDeleted",
    "Font.GuidelineWillBeAdded",
    "Groups.Changed",
    "Groups.BeginUndo",
    "Groups.EndUndo",
    "Groups.BeginRedo",
    "Groups.EndRedo",
    "Groups.GroupSet",
    "Groups.GroupDeleted",
    "Groups.Cleared",
    "Groups.Updated",
    "DataSet.Changed",
    "UnicodeData.Changed",
    "Layer.Changed",
    "Layer.GlyphsChanged",
    "Layer.GlyphChanged",
    "Layer.GlyphWillBeAdded",
    "Layer.GlyphAdded",
    "Layer.GlyphWillBeDeleted",
    "Layer.GlyphDeleted",
    "Layer.GlyphNameChanged",
    "Layer.GlyphUnicodesChanged",
    "Layer.NameChanged",
    "Layer.ColorChanged",
    "Guideline.Changed",
    "Guideline.XChanged",
    "Guideline.YChanged",
    "Guideline.AngleChanged",
    "Guideline.NameChanged",
    "Guideline.IdentifierChanged",
    "Component.Changed",
    "Component.BaseGlyphChanged",
    "Component.BaseGlyphDataChanged",
    "Component.TransformationChanged",
    "Component.IdentifierChanged",
    "Info.Changed",
    "Info.BeginUndo",
    "Info.EndUndo",
    "Info.BeginRedo",
    "Info.EndRedo",
    "Info.ValueChanged",
    "ImageSet.Changed",
    "ImageSet.FileNamesChanged",
    "ImageSet.ImageChanged",
    "ImageSet.ImageWillBeAdded",
    "ImageSet.ImageAdded",
    "ImageSet.ImageWillBeDeleted",
    "ImageSet.ImageDeleted",
    "Contour.Changed",
    "Contour.WindingDirectionChanged",
    "Contour.PointsChanged",
    "Contour.IdentifierChanged",
    "Image.Changed",
    "Image.FileNameChanged",
    "Image.TransformationChanged",
    "Image.ColorChanged",
    "Image.ImageDataChanged",
    "BaseObject.Changed",
    "BaseObject.BeginUndo",
    "BaseObject.EndUndo",
    "BaseObject.BeginRedo",
    "BaseObject.EndRedo",
}


class FontGadgetsError(Exception):
    pass

def getEnvironment():
    """
    Depending on the environmet it will return either "RoboFont" or "Shell".
    """
    try:
        import mojo as _mj

        if hasattr(_mj, "roboFont"):
            return "RoboFont"
    except ImportError:
        pass
    return "Shell"


def _destroyRepresentationsForNotification(self, notification):
    notificationName = notification.name
    for name, dataDict in self.representationFactories.items():
        if notificationName in dataDict["destructiveNotifications"]:
            self.destroyRepresentation(name)
    # Overrids the defcon default behavior to make it possible for a child object
    # to destroy relevant representations on the parent. For example it would be
    # possible to make use of 'Kerning.Changed' destructive notification on the
    # 'Font' object, if 'Font' obj has a representaion with such destructive
    # notification:
    # https://github.com/robotools/defcon/issues/287
    try:
        p = self.getParent()
    except NotImplementedError:
        return
    p._destroyRepresentationsForNotification(notification)


defcon.objects.base.BaseObject._destroyRepresentationsForNotification = (
    _destroyRepresentationsForNotification
)

# All of the follwoing might be hacky, but it works!
_registeredMethods = []
DEBUG = False


def getFontPartsObject(objectName):
    """
    Return the corresponding fontParts object for a given object name.

    This function attempts to retrieve a fontParts object (e.g., RGlyph, RFont)
    based on the provided object name. It constructs the fontParts object name
    by prefixing the input `objectName` with "R" and attempts to retrieve it
    from the `fontParts.fontshell` module.

    Args:
        objectName (str): The name of the object to retrieve (e.g., "Glyph").

    Returns:
        object: The corresponding fontParts object if found, otherwise None.
    """

    try:
        return getattr(fontParts.fontshell, "R" + objectName)
    except AttributeError:
        return


def getDefconObject(objectName):
    """
    Get the defcon object corresponding to the given object name.

    Args:
        objectName (str): The name of the object to retrieve from the
            defcon module.

    Returns:
        The defcon object if found, otherwise None.
    """

    try:
        return getattr(defcon, objectName)
    except AttributeError:
        return


def isObjFromDefcon(obj):
    """
    Check if an object is a class defined in the defcon library.

    Args:
        obj: The object to check.

    Returns:
        True if the object is a defcon class, False otherwise.
    """

    try:
        if hasattr(defcon, obj.__name__):
            return True
    except AttributeError:
        pass
    return False


def isObjFromFontParts(obj):
    """
    Check if the given object is from the fontParts module.

    Args:
        obj: The object to check.

    Returns:
        True if the object is from the fontParts module, False otherwise.
    """

    try:
        if hasattr(fontParts.fontshell, obj.__name__):
            return True
    except AttributeError:
        pass
    return False


def getObjectPackageName(obj):
    """
    Return "defcon" or "fontParts" if the object is from that package.

    Return None if the object doesn't belong to those packages.

    Args:
        obj: The object to check.

    Returns:
        str: "defcon", "fontParts", or None.
    """

    if isObjFromDefcon(obj):
        return "defcon"
    if isObjFromFontParts(obj):
        return "fontParts"


def getWrapperClassForResultInFontParts(defconResult):
    """
    Return the fontParts wrapper class for a given defcon result.

    This function determines the appropriate fontParts wrapper class
    for a given defcon object result. If the input is a defcon object,
    it attempts to find a corresponding fontParts object (e.g., defcon.Glyph
    -> fontParts.fontshell.RGlyph) and returns it. If the input is already
    a fontParts object, it returns None, indicating that no further
    wrapping is needed.

    Args:
        defconResult: The defcon object for which to find a wrapper.

    Returns:
        The fontParts wrapper class, or None if no wrapper is needed.
    """

    if isObjFromDefcon(defconResult):
        return getFontPartsObject(defconResult.__name__)
    # if result is a fontParts object already, there shouldn't be a wrapper


def getIterableWrapperClassForResultInFontParts(defconResult):
    """
    Returns a tuple of wrapper classes for an iterable defcon result.

    This function takes a `defconResult` which is expected to be a
    `typing.GenericAlias` (e.g., `Tuple[defcon.Glyph, defcon.Point]`).
    It extracts the type arguments from the `GenericAlias` and finds
    corresponding wrapper classes in fontParts for each of them.

    Args:
        defconResult: A `typing.GenericAlias` representing the return
            type annotation for multiple variables, such as
            `Tuple[defcon.Glyph, defcon.Point]`.

    Returns:    
        tuple: A tuple containing the fontParts wrapper classes corresponding
        to the type arguments in `defconResult`. Returns `None` for each
        argument that doesn't have a fontParts wrapper. Can be an empty tuple.

    Raises:
        AssertionError: If `defconResult` is not a
            `typing.GenericAlias`.
    """

    assert isinstance(
        defconResult, types.GenericAlias
    ), "Return type annotation for mutliple variables should be wrapped inside a tuple[]!"
    result = []
    for dr in typing.get_args(defconResult):
        result.append(getWrapperClassForResultInFontParts(dr))
    return tuple(result)


def wrapIterableResultInFontParts(defconResult, wrapperClasses):
    """
    Wraps an iterable defcon result in corresponding fontParts objects.

    This function takes an iterable of defcon objects and a corresponding
    iterable of wrapper classes (from fontParts). It iterates through both
    iterables, wrapping each defcon object with its respective wrapper class
    if a wrapper is provided (not None). If no wrapper is provided for a
    specific defcon object, it is kept as is. The function returns a tuple
    containing the wrapped (or original) objects.

    Args:
        defconResult (iterable): An iterable of defcon objects to wrap.
        wrapperClasses (iterable): An iterable of fontParts wrapper classes,
            corresponding to the defcon objects in `defconResult`. Can
            contain None values for objects that should not be wrapped.

    Returns:
        tuple: A tuple containing the wrapped fontParts objects and/or the
            original defcon objects (if no wrapper was provided).
    """
    result = []
    for defconResult, wrapper in zip(defconResult, wrapperClasses):
        if wrapper is not None:
            result.append(wrapper(defconResult))
        else:
            result.append(defconResult)
    return tuple(result)


def getFontPartWrapperForFunctResult(returnType):
    """
    Gets the fontParts wrapper class for a defcon result.

    This function inspects the return type annotation of a function and
    determines if a corresponding fontParts wrapper class exists for the
    defcon object being returned. If so, it returns the wrapper class.
    If the return type is a collection of defcon objects, it returns a
    tuple of corresponding fontParts wrapper classes.

    Args:
        returnType: The return type annotation of a function.

    Returns:
        A fontParts wrapper class (e.g., RGlyph), a tuple of wrapper
        classes, or None if no wrapper is needed. Returns None if the
        return type is inspect._empty or if no corresponding fontParts
        object is found.

    Raises:
        AssertionError: If `defconResult` is a `types.GenericAlias`
            and not wrapped inside a Tuple[].
    """

    if returnType != inspect._empty:
        if isObjFromDefcon(returnType) or isObjFromFontParts(returnType):
            return getWrapperClassForResultInFontParts(returnType)
        return getIterableWrapperClassForResultInFontParts(returnType)


def convertDefconToFontPartsMethod(functInfo, defconObj, isProperty):
    """
    Converts a defcon method to work with fontParts objects.

    This function takes a function information object (`functInfo`), a
    defcon object (`defconObj`), and a boolean indicating whether the
    function is a property (`isProperty`). It checks if the defcon object
    has the method specified in `functInfo`. If it does, it creates a
    wrapper function (`actualDefconMethod`) that calls the defcon method on
    the underlying naked defcon object and wraps the result in the
    appropriate fontParts object, if a wrapper class is specified in
    `functInfo`.

    Args:
        functInfo (FontFunctionProperties): An object containing information
            about the function to be converted.
        defconObj (class): The defcon object to which the function belongs.
        isProperty (bool): A boolean indicating whether the function is a
            property.

    Returns:
        function: A wrapped function that can be called on fontParts objects.
            Returns None if the defcon object does not have the method
            specified in `functInfo`.
    """

    if hasattr(defconObj, functInfo.name):
        wrapperClass = functInfo.wrapperClass
        if isProperty is False:
            if wrapperClass is not None:
                if functInfo.iterableResult:

                    @wraps(functInfo.funct)
                    def actualDefconMethod(self, *args, **kwargs):
                        return wrapIterableResultInFontParts(
                            getattr(self.naked(), functInfo.name)(*args, **kwargs),
                            wrapperClass,
                        )

                else:

                    @wraps(functInfo.funct)
                    def actualDefconMethod(self, *args, **kwargs):
                        return wrapperClass(
                            getattr(self.naked(), functInfo.name)(*args, **kwargs)
                        )

            else:

                @wraps(functInfo.funct)
                def actualDefconMethod(self, *args, **kwargs):
                    return getattr(self.naked(), functInfo.name)(*args, **kwargs)

        else:
            if wrapperClass is not None:
                if functInfo.iterableResult:

                    @wraps(functInfo.funct)
                    def actualDefconMethod(self, *args, **kwargs):
                        return wrapIterableResultInFontParts(
                            getattr(self.naked(), functInfo.name), wrapperClass
                        )

                else:

                    @wraps(functInfo.funct)
                    def actualDefconMethod(self, *args, **kwargs):
                        return wrapperClass(getattr(self.naked(), functInfo.name))

            else:

                @wraps(functInfo.funct)
                def actualDefconMethod(self, *args, **kwargs):
                    return getattr(self.naked(), functInfo.name)

        return actualDefconMethod


def getDefconRepresentationForFunct(functInfo, functRepresentationKey):
    """
    Converts a function to work as a defcon representation.

    The representation must be registered separately using
    `defcon.registerRepresentationFactory`.  This function adapts the
    original function to retrieve and return the representation,
    effectively turning it into a representation accessor.

    Args:
        functInfo (FontFunctionProperties): An object containing
            information about the function, including its name,
            arguments, and the key used for representation registration.
        functRepresentationKey (str): The key used to register the
            representation factory with defcon.  This key is used to
            retrieve the representation when the adapted function is called.

    Returns:
        function: A new function that, when called, retrieves the
            defcon representation associated with the given key and
            passes any arguments to the representation factory.
    """

    argNames = functInfo.args[1:]

    @wraps(functInfo.funct)
    def defconRepresentationForFunction(self, *args, **kwargs):
        for arg, value in zip(argNames, args):
            kwargs[arg] = value
        return getattr(self, "getRepresentation")(functRepresentationKey, **kwargs)

    return defconRepresentationForFunction


# An object to pass around which holds the function information for the purpose
# of registering it as a method for fontParts and defcon
FontFunctionProperties = namedtuple(
    "FunctionProperties",
    [
        "funct",
        "name",
        "args",
        "docs",
        "packageHint",
        "objectName",
        "wrapperClass",
        "iterableResult",
    ],
)


def getFontFunctionProperties(funct):
    """
    Extracts relevant properties from a function for registration.

    It returns a namedtuple containing information such as function name,
    arguments, documentation, package hint (defcon/fontParts), object name,
    wrapper class for fontParts objects, and a boolean indicating if the
    result is iterable.

    Args:
        funct: The function to extract properties from.

    Returns:
        FontFunctionProperties: A namedtuple containing the extracted
        properties.
    """

    funcSignature = inspect.signature(funct)
    parameters = list(funcSignature.parameters.values())
    args = [p.name for p in parameters]
    packageHint = getObjectPackageName(parameters[0].annotation)
    wrapperClass = getFontPartWrapperForFunctResult(funcSignature.return_annotation)
    iterableResult = False
    if isinstance(wrapperClass, tuple):
        iterableResult = True
    if packageHint not in ("defcon", "fontParts"):
        packageHint = None
    objectName = args[0].capitalize()
    name = funct.__name__
    docs = funct.__doc__
    result = FontFunctionProperties(
        funct,  # <func>
        name,  # 'funcName'
        args,  # obj, arg1, arg2
        docs,  # 'bla, bla'
        packageHint,  # 'defcon'/None
        objectName,  # 'Glyph'
        wrapperClass,  # fontParts.fontshell.RGlyph
        iterableResult,  # True/False
    )
    return result


def registerAsfont_method(
    functInfo, isProperty=False, destructiveNotifications=[], isPropertySetter=False
):
    """
    Register a method for both defcon and fontParts objects.

    This function registers a given function as a method for both
    defcon and fontParts objects, based on the provided
    `FontFunctionProperties`. It handles the registration process for
    both libraries, including checking for existing attributes and
    converting defcon methods to work with fontParts objects.

    Args:
        functInfo (FontFunctionProperties): An object containing
            information about the function to be registered, such as its
            name, arguments, documentation, and the target object.
        isProperty (bool, optional): A flag indicating whether the
            function should be registered as a property. Defaults to
            False.
        destructiveNotifications (list, optional): A list of
            notifications that should trigger the destruction of
            representations when the registered method is used. Defaults
            to [].
        isPropertySetter (bool, optional): A flag indicating that the function
            is a setter for an existing property. Defaults to False.

    Raises:
        FontGadgetsError: If the target object does not exist in either
            defcon or fontParts, if there is a conflict with an
            existing attribute/method name, or if a function is registered
            as both a property and a setter.

    Warns:
        UserWarning: If the function is already registered using
            fontgadgets, and the DEBUG flag is enabled, a warning is
            issued to indicate that the existing method is being
            overridden.
    """
    if isProperty and isPropertySetter:
        raise FontGadgetsError(
            "A function cannot be registered as both a property and a setter in the same call."
        )

    defconObj = None
    packageHint = functInfo.packageHint
    if packageHint is None:
        packageHint = ("defcon", "fontParts")
    else:
        packageHint = (packageHint,)
    if "defcon" in packageHint:
        defconObj = registerMethodForDefcon(
            functInfo, isProperty, destructiveNotifications, isPropertySetter
        )
    if "fontParts" in packageHint:
        registerMethodForFontParts(functInfo, isProperty, defconObj, isPropertySetter)


def registerMethodForFontParts(functInfo, isProperty, defconObj=None, isPropertySetter=False):
    """
    Registers a method for a fontParts object.

    Args:
        functInfo (FontFunctionProperties): An object containing
            information about the function to be registered.
        isProperty (bool): A boolean indicating whether the function
            should be registered as a property.
        defconObj: The defcon object to convert the method from.
            Defaults to None.
        isPropertySetter (bool): A boolean indicating whether to register a
            setter for an existing property. Defaults to False.

    Raises:
        FontGadgetsError: If the corresponding RObject does not
            exist in fontParts, or if registering a setter for a
            non-existent property.
    """

    fontPartsObj = getFontPartsObject(functInfo.objectName)
    if fontPartsObj is None:
        raise FontGadgetsError(
            f"`R{functInfo.objectName}` does't exist in 'fontParts'."
        )

    if isPropertySetter:
        assert (
            len(functInfo.args) == 2
        ), f"{functInfo.funct} should have an font object name and a value arguments to be registered as a property setter."
        prop_name = functInfo.name
        if not hasattr(fontPartsObj, prop_name) or not isinstance(
            getattr(fontPartsObj, prop_name), property
        ):
            raise FontGadgetsError(
                f"Cannot register setter. Property '{prop_name}' does not exist on 'fontParts.R{functInfo.objectName}'."
            )

        existing_prop = getattr(fontPartsObj, prop_name)

        @wraps(functInfo.funct)
        def fontparts_setter(self, value):
            setattr(self.naked(), prop_name, value)

        new_prop = property(
            fget=existing_prop.fget,
            fset=fontparts_setter,
            fdel=existing_prop.fdel,
            doc=existing_prop.__doc__,
        )
        setattr(fontPartsObj, prop_name, new_prop)
        return

    methodID, exist = checkIfAttributeAlreadyExist(
        fontPartsObj, functInfo.objectName, functInfo.name, "fontParts"
    )
    fontPartsMethod = functInfo.funct
    if defconObj is not None:
        fontPartsMethod = convertDefconToFontPartsMethod(
            functInfo, defconObj, isProperty
        )
    if isProperty:
        assert (
            len(functInfo.args) == 1
        ), f"{functInfo.funct} should have only one argument to be registered as a property."
        setattr(
            fontPartsObj,
            functInfo.name,
            property(lambda o: fontPartsMethod(o), doc=functInfo.docs),
        )
    else:
        setattr(fontPartsObj, functInfo.name, fontPartsMethod)
    _registeredMethods.append(methodID)


def registerMethodForDefcon(
    functInfo, isProperty, destructiveNotifications=[], isPropertySetter=False
):
    """
    Registers a method for a Defcon object.

    This function registers a given function as a method for a Defcon
    object. It handles cases where the method might already exist and
    provides options for debugging and overriding existing methods.
    It also supports registering the function as a defcon representation
    if destructive notifications are provided.

    Args:
        functInfo (FontFunctionProperties): An object containing
            information about the function to be registered, such as
            its name, arguments, documentation, and package hint.
        isProperty (bool, optional): A flag indicating whether the
            function should be registered as a property. Defaults to
            False.
        destructiveNotifications (list, optional): A list of
            notifications that, when triggered, should destroy the
            representation associated with this function. Defaults to
            [].
        isPropertySetter (bool): A boolean indicating whether to register a
            setter for an existing property. Defaults to False.

    Returns:
        The Defcon object that the method was registered on, or None
        if the object does not exist and the package hint is not
        "defcon".

    Raises:
        FontGadgetsError: If the specified Defcon object does not exist
            and the package hint is "defcon", if the method already
            exists and cannot be overridden, or if registering a setter
            for a non-existent property.
    """

    defconObj = getDefconObject(functInfo.objectName)
    if defconObj is None:
        message = f"`{functInfo.objectName}` does't exist in 'defcon'."
        if functInfo.packageHint == "defcon":
            raise FontGadgetsError(message)
        else:
            warn(message)
            return

    if isPropertySetter:
        assert (
            len(functInfo.args) == 2
        ), f"{functInfo.funct} should have an font object name and a value arguments to be registered as a property setter."
        prop_name = functInfo.name
        if not hasattr(defconObj, prop_name) or not isinstance(
            getattr(defconObj, prop_name), property
        ):
            raise FontGadgetsError(
                f"Cannot register setter. Property '{prop_name}' does not exist on 'defcon.{functInfo.objectName}'."
            )

        existing_prop = getattr(defconObj, prop_name)
        new_setter = functInfo.funct

        new_prop = property(
            fget=existing_prop.fget,
            fset=new_setter,
            fdel=existing_prop.fdel,
            doc=existing_prop.__doc__,
        )
        setattr(defconObj, prop_name, new_prop)
        return defconObj

    methodID, exist = checkIfAttributeAlreadyExist(
        defconObj, functInfo.objectName, functInfo.name, "defcon"
    )
    defconFunct = functInfo.funct
    if destructiveNotifications != []:
        functRepresentationKey = (
            f"{functInfo.objectName}.{functInfo.name}.representation"
        )
        if exist and getEnvironment() == "RoboFont":
            from mojo.roboFont import AllFonts
            assert DEBUG is True
            if functRepresentationKey in defconObj.representationFactories:
                for font in AllFonts():
                    for glyph in font.naked():
                        glyph.destroyAllRepresentations()

        defcon.registerRepresentationFactory(
            defconObj,
            functRepresentationKey,
            functInfo.funct,
            destructiveNotifications=destructiveNotifications,
        )
        defconFunct = getDefconRepresentationForFunct(functInfo, functRepresentationKey)
    if isProperty:
        assert (
            len(functInfo.args) == 1
        ), f"{functInfo.funct} should have only one argument to be registered as a property."
        setattr(
            defconObj,
            functInfo.name,
            property(lambda o: defconFunct(o), doc=functInfo.docs),
        )
    else:
        setattr(defconObj, functInfo.name, defconFunct)
    _registeredMethods.append(methodID)
    return defconObj


def checkIfAttributeAlreadyExist(
    obj, objectName, funcName, moduleName, registerar="fontgadgets"
):
    """
    Check if a method/attribute already exists in a class.

    Args:
        obj: The class which the method will be added to.
        objectName: The name of the object (class).
        funcName: The name of the function to register.
        moduleName: "defcon" or "fontParts".
        registerar: The name of the registerar (default: "fontgadgets").

    Returns:
        A tuple containing:
            - methodID: A unique identifier for the method.
            - exist: A boolean indicating whether the attribute already exists.

    Raises:
        FontGadgetsError: If the attribute already exists and DEBUG is False.
        Warning: If DEBUG is True and the method is being overridden.
    """

    methodID = f"{registerar}.{moduleName}.{objectName}.{funcName}"
    if hasattr(obj, funcName):
        if DEBUG is False:
            if methodID not in _registeredMethods:
                raise FontGadgetsError(
                    f"Registration of `{funcName}` as a function "
                    f"for {obj} failed, because the object already has an "
                    "attribute/method with this exact name."
                )
            else:
                raise FontGadgetsError(
                    f"Function `{funcName}` is already registered using fontgadgets for `{moduleName}.{objectName}`."
                    f"Although you can execute the follwing line to overwrite the function:"
                    f"import fontgadgets; fontgadgets.tools.DEBUG = True"
                )
        elif methodID in _registeredMethods:
            message = f"Overriding an exising `{methodID}` {registerar} method."
            warn(message, category=Warning)
            return methodID, True
    return methodID, False
