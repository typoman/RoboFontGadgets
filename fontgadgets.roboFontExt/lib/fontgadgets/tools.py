import types
import fontParts.fontshell
import defcon
import inspect
from functools import wraps
from warnings import warn
from collections import namedtuple
import typing
from typing import Type, List, Tuple, Union

class FontGadgetsError(Exception):
    pass

def getEnvironment():
    """
    Depending on the environmet it will return either "RoboFont" or "Shell".
    """
    try:
        import mojo as _mj

        if hasattr(_mj, "RoboFont"):
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
    try:
        return getattr(fontParts.fontshell, "R" + objectName)
    except AttributeError:
        return


def getDefconObject(objectName):
    try:
        return getattr(defcon, objectName)
    except AttributeError:
        return


def isObjFromDefcon(obj):
    try:
        if hasattr(defcon, obj.__name__):
            return True
    except AttributeError:
        pass
    return False


def isObjFromFontParts(obj):
    try:
        if hasattr(fontParts.fontshell, obj.__name__):
            return True
    except AttributeError:
        pass
    return False


def getObjectPackageName(obj):
    if isObjFromDefcon(obj):
        return "defcon"
    if isObjFromFontParts(obj):
        return "fontParts"


def getWrapperClassForResultInFontParts(defconResult):
    if isObjFromDefcon(defconResult):
        return getFontPartsObject(defconResult.__name__)
    # if result is a fontParts object already, there shouldn't be a wrapper


def getIterableWrapperClassForResultInFontParts(defconResult):
    assert isinstance(
        defconResult, types.GenericAlias
    ), "Return type annotation for mutliple variables should be wrapped inside a tuple[]!"
    result = []
    for dr in typing.get_args(defconResult):
        result.append(getWrapperClassForResultInFontParts(dr))
    return tuple(result)


def wrapIterableResultInFontParts(defconResult, wrapperClasses):
    result = []
    for defconResult, wrapper in zip(defconResult, wrapperClasses):
        if wrapper is not None:
            result.append(wrapper(defconResult))
        else:
            result.append(defconResult)
    return tuple(result)


def getFontPartWrapperForFunctResult(returnType):
    if returnType != inspect._empty:
        if isObjFromDefcon(returnType) or isObjFromFontParts(returnType):
            return getWrapperClassForResultInFontParts(returnType)
        return getIterableWrapperClassForResultInFontParts(returnType)


def convertDefconToFontPartsMethod(functInfo, defconObj, isProperty):
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
    Converts the function so it will work like a defcon representaion.
    The represenation should be registered separately.
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


def registerAsfont_method(functInfo, isProperty=False, destructiveNotifications=[]):
    defconObj = None
    packageHint = functInfo.packageHint
    if packageHint is None:
        packageHint = ("defcon", "fontParts")
    else:
        packageHint = (packageHint,)
    if "defcon" in packageHint:
        defconObj = registerMethodForDefcon(
            functInfo, isProperty, destructiveNotifications
        )
    if "fontParts" in packageHint:
        registerMethodForFontParts(functInfo, isProperty, defconObj)


def registerMethodForFontParts(functInfo, isProperty, defconObj=None):
    fontPartsObj = getFontPartsObject(functInfo.objectName)
    if fontPartsObj is None:
        raise FontGadgetsError(
            f"`R{functInfo.objectName}` does't exist in 'fontParts'."
        )
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


def registerMethodForDefcon(functInfo, isProperty, destructiveNotifications=[]):
    defconObj = getDefconObject(functInfo.objectName)
    if defconObj is None:
        message = f"`{functInfo.objectName}` does't exist in 'defcon'."
        if functInfo.packageHint == "defcon":
            raise FontGadgetsError(message)
        else:
            warn(message)
            return
    methodID, exist = checkIfAttributeAlreadyExist(
        defconObj, functInfo.objectName, functInfo.name, "defcon"
    )
    defconFunct = functInfo.funct
    if destructiveNotifications != []:
        functRepresentationKey = (
            f"{functInfo.objectName}.{functInfo.name}.representation"
        )
        if exist and getEnvironment() == "RoboFont":
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
    moduleName: defcon or fontParts
    obj: the class which the method will be added to
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
    # method is registered successfully

def inject(target_classes: Union[Type, List[Type], Tuple[Type, ...]]):
    """
    Decorator factory that injects a decorated function as a method to one or
    more target classes, tracking the module of injection and handling conflicts.

    Args:
        target_classes:  A single class or an iterable (list, tuple) of classes
                         to which the decorated function will be added as a method.

    Returns:
        A decorator that, when applied to a function, adds that function as a method
        to the specified target class(es).

    Raises:
        TypeError: If target_classes is not a class or an iterable of classes, or if no class is passed.
        ValueError: If a method with the same name already exists in any of the target classes
                    and was not injected by this decorator from the same module (and DEBUG is False).
    """
    def decorator(func):
        """
        Decorator that adds the decorated function to the target class(es).

        Args:
            func: The function to be added as a method to the target class(es).

        Returns:
            The original function (unmodified). The side effect is adding it to the class(es).

        Raises:
            ValueError: If a method with the same name already exists in any of the target classes
                        and was not injected by this decorator from the same module (and DEBUG is False).
        """
        @wraps(func)
        def wrapper(*args, **kwargs):
            return func(*args, **kwargs)

        if target_classes is None:
            raise TypeError("No target class(es) provided to the inject decorator.")

        module_name = func.__module__
        method_name = func.__name__

        if isinstance(target_classes, type): # Single class case
            target_classes_list = [target_classes]
        elif isinstance(target_classes, (list, tuple)): # Multiple classes case
            if not target_classes: # Check if the list or tuple is empty
                raise TypeError("No target class(es) provided in the list/tuple to the inject decorator.")
            target_classes_list = target_classes
        else:
            raise TypeError(f"Expected a class or a list/tuple of classes in the decorator, but got: {type(target_classes)}")

        for target_class in target_classes_list:
            if not isinstance(target_class, type):
                raise TypeError(f"Expected a class in the decorator, but got: {type(target_class)}")

            if not hasattr(target_class, '__injected_methods__'):
                setattr(target_class, '__injected_methods__', {})

            if hasattr(target_class, method_name):
                injected_methods_dict = target_class.__injected_methods__
                if method_name in injected_methods_dict:
                    if injected_methods_dict[method_name] == module_name:
                        warn(f"Method '{method_name}' already injected into class '{target_class.__name__}' from the same module '{module_name}'. Re-injecting.")
                    else:
                        if not DEBUG:
                            raise ValueError(f"Method '{method_name}' already exists in class '{target_class.__name__}' and was injected from module '{injected_methods_dict[method_name]}', not from the current module '{module_name}'. Conflict.")
                        else:
                            warn(f"Overriding existing method '{method_name}' in class '{target_class.__name__}' that was injected from module '{injected_methods_dict[method_name]}', not from the current module '{module_name}'. Overwriting due to DEBUG mode.")
                else:
                    if not DEBUG:
                        raise ValueError(f"Method '{method_name}' already exists in class '{target_class.__name__}' and was not injected by this decorator. Conflict.")
                    else:
                        warn(f"Method '{method_name}' already exists in class '{target_class.__name__}' and was not injected by this decorator. Overwriting due to DEBUG mode.")
            else:
                warn(f"Injecting method '{method_name}' into class '{target_class.__name__}' from module '{module_name}'.")

            setattr(target_class, method_name, wrapper)
            target_class.__injected_methods__[method_name] = module_name # Track injection source

        return func
    return decorator
