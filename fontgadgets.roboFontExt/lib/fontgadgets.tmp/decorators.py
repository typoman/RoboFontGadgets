import fontgadgets.tools
from fontgadgets.tools import *


def _raisInvalidNotification(funct):
    raise FontGadgetsError(
        f"Invalid destructive notification type in the function {funct}"
    )


def font_cached_method(*destructiveNotifications):
    """
    This is a decorator that makes it possible to convert self standing
    functions to methods on the fontParts and defcon objects. The results will
    be cached using defcon representations according to the
    destructiveNotifications.
    """
    if any([not isinstance(n, str) for n in destructiveNotifications]):
        _raisInvalidNotification(destructiveNotifications[0])

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
    if any([not isinstance(n, str) for n in destructiveNotifications]):
        _raisInvalidNotification(destructiveNotifications[0])

    def wrapper(funct):
        functInfo = fontgadgets.tools.getFontFunctionProperties(funct)
        fontgadgets.tools.registerAsfont_method(
            functInfo, True, destructiveNotifications
        )

    return wrapper
