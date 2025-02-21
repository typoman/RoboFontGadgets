# Main
- add tests for property decorators
- track file changes and post notifications. Example notifcations:
    'Features.IncludedFeaturesChanged'
    'Font.FileNameChanged'
- alternate name for functions

# todo
- separate the modules into files that solve a problem, this will give the user ability
  to load specific modules to prevent bloating the memory from all the functions
- don't load all the methods in the main __init__


## Tests
- regsitration tests

## fontGadgets.tools
- For cached methods how to handle unhashble args?
- decorator for setting a value for a custom font property. This can be used to
  set kerning groups for a glyph.
- Throw a warning when an object can't get destructive notification from a
  child or a same type as the first arg.
- Expand destructive notifcations for cached functions depending on wether a function
  has been executed or not. For exmaple when `font.save` has been executed, then the
  cache will be removed.

  Example:
    ```py
    # this will delete the '_repo' and '_glyphCommits' attributes after font save
    CACHE_ATTRIBUTES = ('_repo', '_glyphCommits')
    def deleteRepoCache(function):
        @wraps(function)
        def wrapper(self, *args, **kwargs):
            for a in CACHE_ATTRIBUTES:
                if hasattr(self, a):
                    delattr(self, a)
            for g in self:
                if hasattr(g, '_path'):
                    delattr(g, '_path')
            return function(self, *args, **kwargs)
        return wrapper

    Font.save = deleteRepoCache(Font.save)
    ```

## defcon
- Keep track of changes in the included feature files for posting notifications.
- this can be done using the mac.fileObserver from fontgoggles. Then whenever the font
opens, start observing these files and post "Features.IncludedFeaturesChanged"
when a change is detected.

## glyph.GlyphTypeInterpreter
- For glyph types use features to find the glyph type. 

## Unicode
take a loot at unicodedata obj and if you can just use everything from there.
- override the unicode property and change it to a subclass of tuple which provides
  these attributes: script, direction, interpreted (which stands for interpreted
  unicodes from features or glyph name)

## Font Sets
- Font sets, such as fonts with similar attribute inside the current folder or just
  arbitrary number of fonts that are added to the object.
- Make groups compatible inside a fontset and also change the kerning for the new groups
- Sort fonts based on os2/weight class or shared glyph widths or shared glyph bounds

## features
- Add sctipt, language, lookups to the rules and glyphs to GlyphFeatures object
- Add glyph.features.definitions from GDEF (glyphdefs or gdef or GDEF as the name?)
- Add "IncludedFeatures.Changed" notification to defcon by keep tracking of the changes
  in the included feature files too.
- Add "IncludeStatement.subset".
- Editing features inside the GlyphFeatures object and saving them back to disk
- Possibility of caching GPOS, GSUB tables and destroying them with defcon notfications
  on glyphs being removed/added.
- Possibility of changing GPOS table attributes when a glyph anchors or kerning is changed.
```
this for the compiler object
def _compileFeatures(self, kern=True, mark=True, gdef=True, curs=True):
    # how to cache features? Is it possible to have some cached tables on the font level
    # that get destroyed if a certain feature changed? 
    # Maybe we can parse the base features, have a base parsed/compliled bare feature cache,
    # then add GPOS, GDEF, GSUB, based on the changes which will be caught by defcon cache.
    pass
```

### subsetter
KNOWN BUGS:
- Subsetting classes can cause the statement `sub @init_src by @init_des;` to drop. This
  could be because the subsetter doesn't subset the classes by making sure the matching
  items between src and des inside these type of clasess also gets subset.
- If these objects are not referenced, they should be removed:
    Classes, LanguageSystemStatement, FeatureReferenceStatement
- If a class doesn't exist it shouldn't be referenced inside another class
    definition.

## Kerning
- merge (add kerning from another font without overriding the current)
- copy/override (add kerning from another font by overriding the current)
- Copy kerning from another font per glyph basis, and same for groups
- diff report from another font which can be easily visualized
- Contextual kerning object
- copyKerning method on the glyph obj

## Groups
- merge (add kerning from another font without overriding the current)
- diff report
- remove groups and kerning methods for glyph obj

Font:
	- getAllAnchorNames
	- getLigatureNames
	- getSkipExportGlyphs

Glyph:
	- removeAnchorsByName(anchorNames)
	- getGlyphAlternates()
	- getFeatureTags() # in which features the glyph is used?
  - copyAnchors from another glyph with an optoin to change the poisitons 
  based on the bounding box
Features:
	- subsetFeatures(`glyphsToRemove`)
	- renameGlyphs(`renameMap`)

# Composites
- glyph.relatedComposites: returns glyphs that are using the current glyph in their composite.