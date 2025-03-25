from fontgadgets.decorators import *

_AST_ATTR_TO_ITER = {
    "base",
    "baseGlyphs",
    "baseMarks",
    "block",
    "chainContexts",
    "componentGlyphs",
    "featureBlocks",
    "glyph",
    "glyphclass",
    "glyphs",
    "glyphs1",
    "glyphs2",
    "ligatureGlyphs",
    "ligatures",
    "lookup",
    "lookups",
    "markAttachment",
    "markClass",
    "markFilteringSet",
    "markGlyphs",
    "marks",
    "old_prefix",
    "old_suffix",
    "pos",
    "prefix",
    "replacement",
    "replacements",
    "statements",
    "subsetMarks",
    "suffix",
}

def _renameGlyphsInObj(obj, renameMap, checked=None):
    if checked is None:
        checked = set()
    obj_id = id(obj)
    if obj_id in checked:
        return obj
    checked.add(obj_id)

    if isinstance(obj, str):
        obj = renameMap.get(obj, obj)
    elif isinstance(obj, (list, tuple, set)):
        obj = [_renameGlyphsInObj(e2, renameMap, checked) for e2 in obj]
    elif isinstance(obj, dict):
        obj = {
            _renameGlyphsInObj(e2, renameMap, checked): _renameGlyphsInObj(
                e3, renameMap, checked
            )
            for e2, e3 in obj.items()
        }
    elif hasattr(obj, "__dict__"):
        for attributeName in obj.__dict__.keys() & _AST_ATTR_TO_ITER:
            old_value = getattr(obj, attributeName)
            setattr(
                obj, attributeName, _renameGlyphsInObj(old_value, renameMap, checked)
            )
    return obj


@font_method
def renameGlyphs(features, renameMap):
    parsedFea = features.parsed.featureFile
    renamed = _renameGlyphsInObj(parsedFea, renameMap)
    features.text = str(renamed)
