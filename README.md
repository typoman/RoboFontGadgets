# What is Font Gadgets?

This is a package that adds more methods to `FontParts` and `Defcon` objects
using monkey patching. It's one way of adding more high level functions to
these packages without having to modify their code directly. Some examples are
`glyph.features` for finding glyph related substitutions and some other methods
to make it easier to change kerning groups. Also you can use `font.scale` to
scale the whole font or `font.subset` to subset the font to a smaller glyph
set.

# Usage

Add your own methods to FontParts/Defcon objects by simply defining a function.
The first argument of the function should be a name of a defcon object, like
`font`, `glyph`, etc. Before the function use the one of the decorators from
this package: `fontMethod` or `fontCachedMethod`. This function will also be
registered for the the equivalent fontPart object automatically.

## Examples

Define a new method for glyph object:

```py
from fontGadgets.tools import fontMethod

@fontMethod
def isComposite(glyph):
    return len(glyph.contours) == 0 and len(glyph.components) > 0
```

Now glyph object has a new property. `fontGadgets` adds functions which have
only one argument as a property.

```
>>> glyph.isComposite
True
```

You can also define a method that can be more efficient if the code is
performance heavy. Make sure the argument types are immutable (e.g. int, str,
etc.):

```py
from fontGadgets.tools import fontCachedMethod
from drawBot import BezierPath
from defcon import Glyph
from fontTools.pens.cocoaPen import CocoaPen

@fontCachedMethod("Glyph.ContoursChanged", "Glyph.ComponentsChanged", "Component.BaseGlyphChanged")
def getStroked(glyph, strokeWidth):
    """
    Returns a stroked copy of the glyph with the defined stroked width. The `strokeWidth` is an integer.
    """
    print('One more time')
    pen = CocoaPen(glyph.font)
    glyph.draw(pen)
    bezierPath = BezierPath(pen.path)
    bezierPath.removeOverlap()
    newPath = bezierPath.expandStroke(strokeWidth).removeOverlap()
    union = newPath.union(bezierPath)
    result = Glyph()
    p = result.getPen()
    union.drawToPen(p)
    return result

g = CurrentGlyph()
g.getStroked(10)
```

This new method will only be executed if any of the destructive notifications
from the `fontCachedMethod` have been posted from changes. This makes it faster
to fetch the result if you want to call it over and over. In the above example
if you run the code in RoboFont, you can see that in the output `'One more
time'` will be printed only when you run the code first time.
