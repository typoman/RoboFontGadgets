import fontgadgets.tools
from fontgadgets.tools import *


def checkNotifications(destructiveNotifications):
    invalidNotifations = set(destructiveNotifications) - VALID_DEFCON_NOTIFCATIONS
    if invalidNotifations:
        nl = "\n"
        raise FontGadgetsError(
            f"Invalid passed destructive notification(s):\n"
            f"{nl.join(invalidNotifations)}\n\n"
            f"Valid choices are:\n"
            f"{nl.join(sorted(VALID_DEFCON_NOTIFCATIONS))}"
        )


def font_cached_method(*destructiveNotifications):
    """
    This is a decorator that makes it possible to convert self standing
    functions to methods on the fontParts and defcon objects. The results will
    be cached using defcon representations according to the
    destructiveNotifications.
    """
    checkNotifications(destructiveNotifications)

    def wrapper(funct):
        functInfo = fontgadgets.tools.getFontFunctionProperties(funct)
        fontgadgets.tools.registerAsfont_method(
            functInfo, False, destructiveNotifications
        )

    return wrapper


def font_method(funct):
    """
    This is a decorator that makes it possible to convert self standing
    functions to methods on defcon/fontParts objects.
    """
    functInfo = fontgadgets.tools.getFontFunctionProperties(funct)

    fontgadgets.tools.registerAsfont_method(functInfo)
    return funct


def font_property(funct):
    """
    This is a decorator that makes it possible to convert self standing
    functions to properties on defcon/fontParts objects.
    """
    functInfo = fontgadgets.tools.getFontFunctionProperties(funct)

    fontgadgets.tools.registerAsfont_method(functInfo, True)
    return funct


def font_cached_property(*destructiveNotifications):
    """
    This is a decorator that makes it possible to convert self standing
    functions to a cached property on defcon/fontParts objects.

    The results will be cached using defcon representations according to the
    passed destructiveNotifications arguments.
    """
    checkNotifications(destructiveNotifications)

    def wrapper(funct):
        functInfo = fontgadgets.tools.getFontFunctionProperties(funct)
        fontgadgets.tools.registerAsfont_method(
            functInfo, True, destructiveNotifications
        )

    return wrapper


def font_property_setter(funct):
    """
    This is a decorator that makes it possible to register a setter for an
    existing property on defcon/fontParts objects.

    The property must have been previously registered, for example, using
    @font_property. The name of the setter function must match the name
    of the property.

    Example:
        @font_property
        def myProp(glyph: defcon.Glyph):
            # make sure to set its defualt value before retrieving it
            if not hasattr(glyph, '_myProp'):
                glyph._myProp = None
            return glyph._myProp

        @font_property_setter
        def myProp(glyph: defcon.Glyph, value):
            glyph._myProp = value
    """
    functInfo = fontgadgets.tools.getFontFunctionProperties(funct)
    fontgadgets.tools.registerAsfont_method(functInfo, isPropertySetter=True)
    return funct
