# What is Font Gadgets?

This is a package that adds more methods to `FontParts` and `defcon` objects
using monkey patching. It's one way of adding more high level functions to
these packages without having to modify their code directly. Some methods and
attributes are already added using this package like `glyph.features` for
finding glyph related substitutions and some other methods to make it easier to
change kerning groups. Also you can use `font.scale` to scale the whole font or
`font.subset` to subset the font to a smaller glyph set.

# Usage

Add your own methods to FontParts/Defcon objects by simply defining a function.
The first argument of the function should be a name of a defcon object, like
`font`, `glyph`, etc. Before the function definition, use one of the decorators
from this package:

`font_method`: to add the function as a method to a `defcon/fontParts` class

`font_cached_method`: to add the function as a cached method to a `defcon/fontParts`
class. You need to pass destructive notifications to this decorator. See the
example below.

`font_property`: to add the function as a dynamic attribute (property) to a
`defcon/fontParts` class.

`font_cached_property`: to add the function as a cached dynamic attribute
(property) to a `defcon/fontParts` class. You need to pass destructive
notifications to this decorator. See the example below.

When you define a function with one of these decorators, `fontgadgets` first
adds it the `defcon` package and then also to `fontParts`. You can explicitly
ask `fontgadgets` to an object using type hints. More details below.

## Examples

### Adding a dynamic attribute (property)
Define a new dynamic attribute (property) for glyph object:

```py
from fontgadgets.decorators import font_property

@font_property
def isComposite(glyph):
    return len(glyph.contours) == 0 and len(glyph.components) > 0
```

Please note that the first argument is a glyph. This will tell `fontgadgets` to
register this method for `defcon.Glyph` and `fontParts.fontshell.RGlyph`
objects.

```
>>> glyph.isComposite
True
```

### Adding a cached method
You can also define a method that can be more efficient if the code is
performance heavy. Make sure the argument types are immutable (e.g. int, str,
etc.):

```py
from fontgadgets.decorators import font_cached_method
from drawBot import BezierPath
from defcon import Glyph
from fontTools.pens.cocoaPen import CocoaPen

@font_cached_method("Glyph.ContoursChanged", "Glyph.ComponentsChanged", "Component.BaseGlyphChanged")
def getStroked(glyph, strokeWidth):
    """
    Returns a stroked copy of the glyph with the defined stroked width. The `strokeWidth` is an integer.
    """
    print('One more time!')
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
from the `font_cached_method` have been posted from changes. This makes it faster
to fetch the result if you want to call it over and over. In the above example
if you run the code in RoboFont, you can see that in the output `'One more
time'` will be printed only when you run the code first time. The other times
the function body is not executed and only the result is returned.

The cached result is kept until there are changes in the glyph object. These
changes should be passed to the `font_cached_method` and they're from `defcon`
package. This way we have more explicit way of observing changes and what
causes the cached result to become obsolete.

### Choosing which package/object to add the method to

By default the defined functions will be added to `defcon` and if there is an equivalent
object in  `fontParts`, the fontParts object will also get the new methid. But these
packages are not same and sometimes there are object in one package that doesn't exist
in another. You can ask `fontgadgets` to add the function to only one package using type
hints.

Just pass the target object as the type hint to the first argument:
```py
from fontgadgets.decorators import font_method

@font_method
def myFunction(segment: RSegment):
    # do stuff on an instance of RSegment object
    pass
```

### Return type

Since `fontgadgets` to by default adds the method to `defcon`, if there is a
return type, it is also a defcon type of object. The problem is when this
method is also added to a `fontParts` object. Then it will also return
the `defcon` object not the `fontParts` one.

If you want the equivalent `fontParts` object to return the `fontParts` object
instead of `defcon`, you need to use type hints on the return type:

```py
from fontgadgets.decorators import font_method

@font_method
def subset(font) -> defcon.Font:
    # subset the font and return a new font
    return font
```

Here we are hinting `fontgadgets` that return type is a `defcon.Font` object.
Since there are no type hints for the first `font` argument, this method will
be added first to `defcon` and then `fontParts` font object.  When
`fontgadgets` registers the function for `fontParts.fontshell.RFont` object it
will make sure the return type of the method will be wrapped in an `RFont`
object to make the method consistent with its package.

# Warning
This package is in active development and while being stable enough to add methods to
font objects, it is currently in alpha stage. This means that occasionally the public
interface will change (for example names of options or functions added to the objects by
this package). Please report any problems in the issues section of the repo, I try to
fix them as soon as I can.
