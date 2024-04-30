from fontgadgets.tools import *

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


def decorateAll():
    """
    Decorates all the fontParts and defcon object from this package extensions.
    """
    from fontgadgets import extensions as _fontgadgets_extensions

    _fontgadgets_extensions.loadExtensions()


def reloadAll():
    """
    This functions is only used inside RF and can be used to relaod all the
    fontgadgets modules. This is used during the development of this package
    inside RF.
    """
    assert getEnvironment() == "RoboFont"
    import fontgadgets.tools
    from fontgadgets.extensions.robofont.tools import reloadSubModules

    reloadSubModules("fontgadgets.tools")
    fontgadgets.tools.DEBUG = True
    reloadSubModules("fontgadgets", skipSubModules=set(["tools"]))
    fontgadgets.tools.DEBUG = False
    reloadSubModules("fontgadgets.robofont")
