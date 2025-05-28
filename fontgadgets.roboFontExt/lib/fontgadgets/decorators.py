import fontgadgets.tools
from fontgadgets.tools import *


def checkNotifications(destructiveNotifications):
    invalidNotifations = set(destructiveNotifications) - VALID_DEFCON_NOTIFCATIONS
    if invalidNotifations:
        raise FontGadgetsError(
            f"Invalid passed destructive notification(s):\n{'\n'.join(invalidNotifations)}\n"
            f"\nValid choices are:\n{'\n'.join(sorted(VALID_DEFCON_NOTIFCATIONS))}"
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
