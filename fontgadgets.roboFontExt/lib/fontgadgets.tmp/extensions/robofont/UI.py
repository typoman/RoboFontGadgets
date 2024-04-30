import mojo.UI
from AppKit import NSApp
from mojo.roboFont import CurrentFont, CurrentGlyph
import AppKit


def _getCurrentSelectedGlyphNames():
    """
    Returns the selected glyph names based on what window is active.
    """
    cw = mojo.UI.CurrentWindow().doodleWindowName
    f = CurrentFont()
    selection = []
    if cw == "FontWindow":
        s = f.templateSelectedGlyphNames
        for gn in s:
            selection.append(gn)
    elif cw == "GlyphWindow":
        g = CurrentGlyph()
        if g is not None:
            selection.append(g.name)
    elif cw == "SpaceCenter":
        s = mojo.UI.CurrentSpaceCenter().glyphLineView.getSelectedGlyphRecord()
        if s:
            selection.append(s.glyph.name)
    return selection


mojo.UI.CurrentSelectedGlyphNames = _getCurrentSelectedGlyphNames


def _enableDarkMode():
    dark = AppKit.NSAppearance.appearanceNamed_(AppKit.NSAppearanceNameDarkAqua)
    AppKit.NSApp().setAppearance_(dark)


mojo.UI.enableDarkMode = _enableDarkMode


def _limitFontViewToGlyphSet(glyph_set):
    queryText = 'Name in {"%s"}' % '", "'.join(glyph_set)
    query = AppKit.NSPredicate.predicateWithFormat_(queryText)
    mojo.UI.CurrentFontWindow().getGlyphCollection().setQuery(query)


mojo.UI.limitFontViewToGlyphSet = _limitFontViewToGlyphSet


def _getVanillaWindows():
    """
    If you set the __name__ attribute of the class that contains a vanilla window
    you can retrive that window by that name attribute.
    """
    result = {}
    for w in NSApp().windows():
        delegate = w.delegate()
        if delegate:
            if not hasattr(delegate, "vanillaWrapper"):
                continue
            vanillaWrapper = delegate.vanillaWrapper()
            if hasattr(vanillaWrapper, "__name__"):
                result.setdefault(vanillaWrapper.__name__, []).append(vanillaWrapper)
    return result


mojo.UI.getVanillaWindows = _getVanillaWindows


def _getVisibleGlyphNames():
    visibleGlyphs = mojo.UI.CurrentFontWindow().getGlyphCollection().getVisibleGlyphs()
    return [g.name for g in visibleGlyphs]


mojo.UI.getVisibleGlyphNames = _getVisibleGlyphNames
