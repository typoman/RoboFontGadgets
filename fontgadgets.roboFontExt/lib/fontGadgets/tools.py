import defcon
import fontParts.world
import logging
import inspect

logger = logging.getLogger(__name__)
# logging.basicConfig(level=logging.DEBUG)

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

defcon.objects.base.BaseObject._destroyRepresentationsForNotification = _destroyRepresentationsForNotification

# All of the follwoing might be hacky, but it works!
_registeredMethods = []
DEBUG = False

class FontMethodsRegistrar():

    def __init__(self, funct):
        self.funct = funct
        self.funcSignature = inspect.signature(funct)
        self.args = [p.name for p in self.funcSignature.parameters.values()]
        self.objectName = self.args[0].capitalize()
        self.funcName = funct.__name__

    @property
    def fontPartsObject(self):
        try:
            return getattr(fontParts.fontshell, "R"+self.objectName)
        except AttributeError:
            self._failObjectName('fontParts')

    @property
    def defconObject(self):
        try:
            return getattr(defcon, self.objectName)
        except AttributeError:
            self._failObjectName('defcon')

    def _failObjectName(self, package):
        logger.exception(f"{self.objectName} is not a {package} object. "
                        f"First argument in your function should be a "
                        f"{package} object name:\nFunction: {self.funcName}\n Argument:{self.args[0]}"
                        )

    def registerAsFontMethod(self):
        if self._attributeAlreadyExist():
            return
        if self.args[1:]:
            setattr(self.defconObject, self.funcName, self.funct)
            funcName = f"fp{self.funcName}"
            code = [f"def {funcName}{self.funcSignature}:"]
            code.append(f"\treturn {self.args[0]}.naked().{self.funcName}({', '.join(self.args[1:])})")
            code.append(f"fontParts.fontshell.{self.args[0]}.{'R'+self.objectName}.{self.funcName} = {funcName}")
            exec("\n".join(code))
        else:
            # register the function as property
            setattr(self.fontPartsObject, self.funcName, property(lambda o: self.funct(o.naked())))
            setattr(self.defconObject, self.funcName, property(lambda o: self.funct(o)))
        _registeredMethods.append(f'{self.objectName}.{self.funcName}')

    def _attributeAlreadyExist(self):
        method = f'{self.objectName}.{self.funcName}'
        if method not in _registeredMethods and not DEBUG:
            for obj in (self.defconObject, self.fontPartsObject):
                if hasattr(obj, self.funcName):
                    msg = f"""Registration of `{self.funcName}` as a function for the class `{obj}` failed,
                            because the object already has an attribute/method with this exact name."""
                    print(msg)
                    logger.error(msg)
                    return True
        else:
            logger.warning(f"Overriding an exising `{method}` method.")
        return False

    def _createPresentationMethodWtihArgs(self, isDefconMethod=False):
        nakedCode = ''
        funcName = self.funcName.capitalize()
        if isDefconMethod:
            funcName = 'defcon' + self.funcName
        else:
            nakedCode = '.naked()'
        code = [f"def {funcName}{self.funcSignature}:"]
        if self.funct.__doc__ is not None:
            code.append(f"\t\"\"\"\n\t{self.funct.__doc__.strip()}\n\t\"\"\"")
        code.append(f"\treturn {self.args[0]}{nakedCode}.getRepresentation('{self.funcRepresentationKey}', {', '.join([f'{v}={v}' for v in self.args[1:]])})")
        if isDefconMethod:
            code.append(f"defcon.{self.objectName}.{self.funcName} = {funcName}")
        else:
            code.append(f"fontParts.fontshell.{self.args[0]}.{'R'+self.objectName}.{self.funcName} = {funcName}")
        exec("\n".join(code))

    def registerAsFontCachedMethod(self, *destructiveNotifications):
        if self._attributeAlreadyExist():
            return
        self.funcRepresentationKey = f"{self.objectName}.{self.funcName}.representation"
        defobjc = self.defconObject
        defcon.registerRepresentationFactory(defobjc, self.funcRepresentationKey, self.funct, destructiveNotifications=destructiveNotifications)
        if self.args[1:]:
            self._createPresentationMethodWtihArgs()
            self._createPresentationMethodWtihArgs(isDefconMethod=True)
        else:
            # register the function as property
            setattr(defobjc, self.funcName, property(lambda o: o.getRepresentation(self.funcRepresentationKey)))
            setattr(self.fontPartsObject, self.funcName, property(lambda o: o.naked().getRepresentation(self.funcRepresentationKey)))
        _registeredMethods.append(f'{self.objectName}.{self.funcName}')

def fontCachedMethod(*destructiveNotifications):
    """
    This is a decorator that makes it possible to convert self standing functions to
    methods on the fontParts and defcon objects. The results will be cached using
    defcon representations according to the destructiveNotifications. Note that if
    the function only has one argument then it will become a property.
    """
    def wrapper(funct):
        registrar = FontMethodsRegistrar(funct)
        registrar.registerAsFontCachedMethod(*destructiveNotifications)
    return wrapper

def fontMethod(funct):
    """
    This is a decorator that makes it possible to convert self standing functions to
    methods on defcon/fontParts objects. If the function only has one argument then
    it will become a property.
    """
    registrar = FontMethodsRegistrar(funct)
    registrar.registerAsFontMethod()
