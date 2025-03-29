import fontTools.feaLib.ast as ast
from fontgadgets import patch
from fontTools.feaLib.error import FeatureLibError
from fontTools.misc.encodingTools import getEncoding


def _glyphsToDict(g):
    if hasattr(g, "toDict"):
        return g.toDict()
    elif isinstance(g, tuple) and len(g) == 2:
        return {"GlyphRange": (_glyphsToDict(g[0]), _glyphsToDict(g[1]))}
    else:
        return {"Glyph": g}


def _deviceToDict(device, key_name="Device"):
    if device is None:
        return {key_name: None}
    return {key_name: [{"Size": size, "Value": value} for size, value in device]}


def _attrToDict(value, key=None):
    result = {}
    if value:
        converted = value
        if isinstance(value, dict):
            converted = {}
            for k, v in dic.items():
                converted.update(_attrToDict(v, k))
        elif hasattr(value, "toDict"):
            converted = value.toDict()
        elif isinstance(value, (list, set, tuple)):
            converted = [_attrToDict(s) for s in value]
        if key is None:
            return converted
        else:
            result[key] = converted
    return result


def _attr_is_not_set(attribute):
    if attribute is None:
        return True
    if isinstance(attribute, (list, dict, set, tuple)):
        return not bool(attribute)
    if attribute is False:
        return True
    return False


@patch.method(ast.Element)
def toDict(self):
    result = {}
    class_name = getattr(self, "_serialize_name", self.__class__.__name__)

    if not hasattr(self, "_serialize_attrs") or self._serialize_attrs is None:
        return class_name

    if isinstance(self._serialize_attrs, str):
        value = getattr(self, self._serialize_attrs)
        processed_value = _attrToDict(value)
        return {class_name: processed_value}

    for source_name, conversion_spec in self._serialize_attrs.items():
        base_value = getattr(self, source_name)
        if isinstance(conversion_spec, str):
            converted_name = conversion_spec
            if isinstance(base_value, str):
                base_value = base_value.strip()
            result.update(_attrToDict(base_value, converted_name))
        elif isinstance(conversion_spec, dict):
            if _attr_is_not_set(base_value):
                continue
            for nested_source, nested_target in conversion_spec.items():
                nested_value = getattr(base_value, nested_source)
                result.update(_attrToDict(nested_value, nested_target))

    return {class_name: result}


ast.Element._serialize_attrs = None
ast.Element._serialize_name = None
for astObjName in dir(ast):
    cls = getattr(ast, astObjName)
    if hasattr(cls, "toDict"):
        cls._serialize_name = astObjName

ast.Comment._serialize_attrs = "text"
ast.GlyphName._serialize_attrs = "glyph"
ast.GlyphName._serialize_name = "Glyph"


@patch.method(ast.NullGlyph)
def toDict(self):
    return {"Glyph": None}


@patch.method(ast.GlyphClass)
def toDict(self):
    glyphSet = self.glyphs
    if len(self.original):
        if self.curr < len(self.glyphs):
            self.original.extend(self.glyphs[self.curr :])
            self.curr = len(self.glyphs)
        return {"GlyphClass": list(map(_glyphsToDict, self.original))}
    else:
        return {"GlyphClass": list(map(_glyphsToDict, self.glyphs))}


@patch.method(ast.GlyphClassName)
def toDict(self):
    return {"ClassName": self.glyphclass.name}


@patch.method(ast.MarkClassName)
def toDict(self):
    return {"ClassName": self.markClass.name}


ast.AnonymousBlock._serialize_attrs = {"tag": "Tag", "content": "Content"}

ast.FeatureFile._serialize_attrs = {
    "statements": "Statements",
    "markClasses": "MarkClasses",
}

ast.FeatureBlock._serialize_attrs = {
    "statements": "Statements",
    "name": "Name",
    "use_extension": "UseExtension",
}

ast.NestedBlock._serialize_attrs = {
    "tag": "Tag",
    "block_name": "BlockName",
    "statements": "Statements",
}

ast.LookupBlock._serialize_attrs = {
    "name": "Name",
    "use_extension": "UseExtension",
    "statements": "Statements",
}


ast.TableBlock._serialize_attrs = {"name": "Name", "statements": "Statements"}


ast.GlyphClassDefinition._serialize_name = "GlyphDefinitionClass"
ast.GlyphClassDefinition._serialize_attrs = {
    "name": "Name",
    "glyphs": "Glyphs",
}

ast.GlyphClassDefStatement._serialize_name = "GlyphTypeDefinitions"
ast.GlyphClassDefStatement._serialize_attrs = {
    "baseGlyphs": "BaseGlyphs",
    "markGlyphs": "MarkGlyphs",
    "ligatureGlyphs": "LigatureGlyphs",
    "componentGlyphs": "ComponentGlyphs",
}


ast.MarkClass._serialize_attrs = "definitions"


ast.MarkClassDefinition._serialize_name = "MarkClassDefinition"
ast.MarkClassDefinition._serialize_attrs = {
    "markClass": {"name": "Name"},
    "anchor": "Anchor",
    "glyphs": "Glyphs",
}


ast.AlternateSubstStatement._serialize_name = "AlternateSubstitution"
ast.AlternateSubstStatement._serialize_attrs = {
    "prefix": "Prefix",
    "suffix": "Suffix",
    "glyph": "In",
    "replacement": "Out",
}


@patch.method(ast.Anchor)
def toDict(self):
    if self.name is not None:
        return {"Anchor": {"Name": self.name}}

    anchor = {}
    if self.x is not None:
        anchor["X"] = self.x
    if self.y is not None:
        anchor["Y"] = self.y

    if self.contourpoint is not None:
        anchor["ContourPoint"] = self.contourpoint

    if self.xDeviceTable:
        anchor.update(_deviceToDict(self.xDeviceTable, "XDevice"))
    if self.yDeviceTable:
        anchor.update(_deviceToDict(self.yDeviceTable, "YDevice"))

    return {"Anchor": anchor}


@patch.method(ast.ValueRecord)
def toDict(self):
    result = {}
    if self.xPlacement is not None:
        result["XPlacement"] = self.xPlacement
    if self.yPlacement is not None:
        result["YPlacement"] = self.yPlacement
    if self.xAdvance is not None:
        result["XAdvance"] = self.xAdvance
    if self.yAdvance is not None:
        result["YAdvance"] = self.yAdvance
    if self.vertical:
        result["Vertical"] = True

    if self.xPlaDevice:
        result.update(_deviceToDict(self.xPlaDevice, "XPlacementDevice"))
    if self.yPlaDevice:
        result.update(_deviceToDict(self.yPlaDevice, "YPlacementDevice"))
    if self.xAdvDevice:
        result.update(_deviceToDict(self.xAdvDevice, "XAdvanceDevice"))
    if self.yAdvDevice:
        result.update(_deviceToDict(self.yAdvDevice, "YAdvanceDevice"))

    return {"ValueRecord": result}


ast.AnchorDefinition._serialize_attrs = {
    "name": "Name",
    "x": "X",
    "y": "Y",
    "contourpoint": "ContourPoint",
}


ast.AttachStatement._serialize_attrs = {
    "glyphs": "Glyphs",
    "contourPoints": "ContourPoints",
}
ast.AttachStatement._serialize_name = "Attach"


def _chain_context_to_dict(self, key):
    result = {}
    if len(self.prefix) or len(self.suffix) or any(x is not None for x in self.lookups):
        if len(self.prefix):
            result["Prefix"] = [p.toDict() for p in self.prefix]
        glyph_lookups = []
        for i, g in enumerate(self.glyphs):
            glyph_entry = {"Glyph": g.toDict()}
            if self.lookups[i]:
                glyph_entry["Lookups"] = [lu.name for lu in self.lookups[i]]
            glyph_lookups.append(glyph_entry)
        result["ChainedLookups"] = glyph_lookups
        if len(self.suffix):
            result["Suffix"] = [s.toDict() for s in self.suffix]
    else:
        result["Glyph"] = [g.toDict() for g in self.glyphs]
    return {key: result}


@patch.method(ast.ChainContextPosStatement)
def toDict(self):
    return _chain_context_to_dict(self, "ChainContextualPositioning")


@patch.method(ast.ChainContextSubstStatement)
def toDict(self):
    return _chain_context_to_dict(self, "ChainContextualSubstitution")


ast.CursivePosStatement._serialize_name = "CursivePositioning"
ast.CursivePosStatement._serialize_attrs = {
    "glyphclass": "Class",
    "entryAnchor": "Entry",
    "exitAnchor": "Exit",
}


ast.FeatureReferenceStatement._serialize_name = "FeatureReference"
ast.FeatureReferenceStatement._serialize_attrs = "featureName"


def _ignore_to_dict(self, key):
    contexts = []
    for prefix, glyphs, suffix in self.chainContexts:
        context = {}
        if len(prefix):
            context["Prefix"] = [p.toDict() for p in prefix]
        context["Glyphs"] = [g.toDict() for g in glyphs]
        if len(suffix):
            context["Suffix"] = [s.toDict() for s in suffix]
        contexts.append(context)
    return {key: contexts}


@patch.method(ast.IgnorePosStatement)
def toDict(self):
    return _ignore_to_dict(self, "IgnorePositioning")


@patch.method(ast.IgnoreSubstStatement)
def toDict(self):
    return _ignore_to_dict(self, "IgnoreSubstitution")


ast.IncludeStatement._serialize_name = "Include"
ast.IncludeStatement._serialize_attrs = "filename"

ast.ScriptStatement._serialize_name = "Script"
ast.ScriptStatement._serialize_attrs = "script"


@patch.method(ast.LanguageStatement)
def toDict(self):
    result = {"Language": self.language.strip()}
    if not self.include_default:
        result["ExcludeDefault"] = True
    if self.required:
        result["Required"] = True
    return result


ast.LanguageSystemStatement._serialize_name = "LanguageSystem"
ast.LanguageSystemStatement._serialize_attrs = {
    "script": "Script",
    "language": "Language",
}


@patch.method(ast.FontRevisionStatement)
def toDict(self):
    return {"FontRevision": round(self.revision, 3)}


def _ligature_caret_to_dict(self, key):
    return {key: {"Glyphs": self.glyphs.toDict(), "Carets": self.carets}}


@patch.method(ast.LigatureCaretByIndexStatement)
def toDict(self):
    return _ligature_caret_to_dict(self, "LigatureCaretByIndex")


@patch.method(ast.LigatureCaretByPosStatement)
def toDict(self):
    return _ligature_caret_to_dict(self, "LigatureCaretByPosition")


def _optional_context_to_dict(self):
    result = {}
    has_context = False
    if len(self.prefix):
        result["Prefix"] = [p.toDict() for p in self.prefix]
        has_context = True
    if len(self.suffix):
        result["Suffix"] = [s.toDict() for s in self.suffix]
        has_context = True

    if not has_context and self.forceChain:
        result["Chained"] = True
    return result


@patch.method(ast.LigatureSubstStatement)
def toDict(self):
    result = {
        "In": [g.toDict() for g in self.glyphs],
        "Out": _glyphsToDict(self.replacement),
    }
    result.update(_optional_context_to_dict(self))
    return {"LigatureSubstitution": result}


@patch.method(ast.LookupFlagStatement)
def toDict(self):
    result = {}
    flags = ["RightToLeft", "IgnoreBaseGlyphs", "IgnoreLigatures", "IgnoreMarks"]
    for i, flag in enumerate(flags):
        if self.value & (1 << i):
            result.setdefault("Flags", []).append(flag)
    if self.markAttachment is not None:
        result["MarkAttachment"] = self.markAttachment.toDict()
    if self.markFilteringSet is not None:
        result["UseMarkFilteringSet"] = self.markFilteringSet.toDict()
    return {"LookupFlag": result}


@patch.method(ast.LookupReferenceStatement)
def toDict(self):
    return {"LookupReference": self.lookup.name}


@patch.method(ast.MarkBasePosStatement)
def toDict(self):
    return {
        "MarkBasePositioning": {
            "Base": self.base.toDict(),
            "Marks": [
                {"Anchor": a.toDict(), "MarkClass": m.name} for a, m in self.marks
            ],
        }
    }


@patch.method(ast.MarkLigPosStatement)
def toDict(self):
    marks = []
    for l in self.marks:
        if l is None or not len(l):
            marks.append({"Anchor": None})
        else:
            component_marks = []
            for a, m in l:
                component_marks.append({"Anchor": a.toDict(), "MarkClass": m.name})
            marks.append(component_marks)
    return {
        "MarkLigaturePositioning": {
            "Ligatures": self.ligatures.toDict(),
            "Marks": marks,
        }
    }


@patch.method(ast.MarkMarkPosStatement)
def toDict(self):
    return {
        "MarkToMarkPositioning": {
            "Base": self.baseMarks.toDict(),
            "Marks": [
                {"Anchor": a.toDict(), "MarkClass": m.name} for a, m in self.marks
            ],
        }
    }


@patch.method(ast.MultipleSubstStatement)
def toDict(self):
    result = {
        "In": self.glyph.toDict(),
        "Out": [_glyphsToDict(r) for r in self.replacement],
    }

    result.update(_optional_context_to_dict(self))
    return {"MultipleSubstitution": result}


@patch.method(ast.PairPosStatement)
def toDict(self):
    def value_record_to_dict(vr):
        if vr is None:
            return None
        vr_dict = vr.toDict()
        if not vr_dict.get("ValueRecord"):
            return None
        return vr_dict

    result = {
        "First": self.glyphs1.toDict(),
        "Value1": value_record_to_dict(self.valuerecord1),
        "Second": self.glyphs2.toDict(),
        "Enumerated": self.enumerated,
    }

    if hasattr(self, "valuerecord2") and self.valuerecord2 is not None:
        result["Value2"] = value_record_to_dict(self.valuerecord2)
    elif (
        hasattr(self, "valuerecord2")
        and self.valuerecord2 is None
        and result.get("Value1") is not None
    ):
        potential_value2 = value_record_to_dict(self.valuerecord2)
        if self.valuerecord2 is not None:
            result["Value2"] = potential_value2

    return {"PairPositioning": result}


ast.ReverseChainSingleSubstStatement._serialize_name = "ReverseChainSingleSubstitution"
ast.ReverseChainSingleSubstStatement._serialize_attrs = {
    "glyphs": "In",
    "replacements": "Out",
    "old_prefix": "Prefix",
    "old_suffix": "Suffix",
}


@patch.method(ast.SingleSubstStatement)
def toDict(self):
    result = {
        "In": [_glyphsToDict(g) for g in self.glyphs],
        "Out": [_glyphsToDict(r) for r in self.replacements],
    }
    result.update(_optional_context_to_dict(self))
    return {"SingleSubstitution": result}


@patch.method(ast.SinglePosStatement)
def toDict(self):
    positions_list = []
    for g, v in self.pos:
        positions_list.append(
            {"Glyph": _glyphsToDict(g), "Value": v.toDict() if v else None}
        )
    result = {"Positions": positions_list}
    result.update(_optional_context_to_dict(self))
    return {"SinglePositioning": result}


ast.SubtableStatement._serialize_name = "Subtable"


@patch.method(ast.ValueRecordDefinition)
def toDict(self):
    value_dict = self.value.toDict()
    if value_dict == {"ValueRecord": {}}:
        value_dict = None
    return {"ValueRecordDefinition": {"Name": self.name, "Value": value_dict}}


def _platform_record_to_dict(self, string):
    result = {"String": string}
    if self.platformID is not None:
        result["PlatformID"] = self.platformID
    if self.platEncID is not None:
        result["PlatformEncodingID"] = self.platEncID
    if self.langID is not None:
        result["LanguageID"] = self.langID
    return result


@patch.method(ast.NameRecord)
def toDict(self):
    return {"NameRecord": _platform_record_to_dict(self, self.string)}


@patch.method(ast.FeatureNameStatement)
def toDict(self):
    result = {"Type": "Name"}
    if self.nameID == "size":
        result["Type"] = "Size"

    result.update(_platform_record_to_dict(self, self.string))
    return {"FeatureName": result}


@patch.method(ast.STATNameStatement)
def toDict(self):
    return {"STATName": _platform_record_to_dict(self, self.string)}


@patch.method(ast.CVParametersNameStatement)
def toDict(self):
    return {"CVParametersName": _platform_record_to_dict(self, self.string)}


@patch.method(ast.SizeParameters)
def toDict(self):
    result = {"DesignSize": round(self.DesignSize, 1), "SubfamilyID": self.SubfamilyID}
    if self.RangeStart != 0 or self.RangeEnd != 0:
        result.update(
            {
                "RangeStart": int(self.RangeStart * 10),
                "RangeEnd": int(self.RangeEnd * 10),
            }
        )
    return {"SizeParameters": result}


@patch.method(ast.CharacterStatement)
def toDict(self):
    return {"Character": self.character}


@patch.method(ast.BaseAxis)
def toDict(self):
    scripts = []
    for s in self.scripts:
        tag, baseline, coordinates = s
        scripts.append(
            {
                "Script": tag.strip(),
                "Baseline": baseline.strip(),
                "Coordinates": list(coordinates),
            }
        )
    direction = "Vertical" if self.vertical else "Horizontal"

    return {
        "BaseAxis": {
            "Direction": direction,
            "Bases": [b.strip() for b in self.bases],
            "Scripts": scripts,
        }
    }


@patch.method(ast.OS2Field)
def toDict(self):
    key_map = {
        "fstype": "FSType",
        "typoascender": "TypoAscender",
        "typodescender": "TypoDescender",
        "typolinegap": "TypoLineGap",
        "winascent": "winAscent",
        "windescent": "winDescent",
        "xheight": "XHeight",
        "capheight": "CapHeight",
        "weightclass": "WeightClass",
        "widthclass": "WidthClass",
        "loweropsize": "LowerOpSize",
        "upperopsize": "UpperOpSize",
        "unicoderange": "UnicodeRange",
        "codepagerange": "CodePageRange",
        "panose": "Panose",
        "vendor": "Vendor",
    }
    proper_key = key_map.get(self.key)

    if proper_key is None:
        raise

    match self.key:
        case key if key in (
            "fstype",
            "typoascender",
            "typodescender",
            "typolinegap",
            "winascent",
            "windescent",
            "xheight",
            "capheight",
            "weightclass",
            "widthclass",
            "loweropsize",
            "upperopsize",
        ):
            return {"OS2Field": {proper_key: self.value}}
        case "unicoderange" | "codepagerange" | "panose":
            return {"OS2Field": {proper_key: list(self.value)}}
        case "vendor":
            return {"OS2Field": {proper_key: self.value}}


@patch.method(ast.HheaField)
def toDict(self):
    fields = ("CaretOffset", "Ascender", "Descender", "LineGap")
    canonical_key = next((f for f in fields if f.lower() == self.key), self.key)
    return {"HheaField": {canonical_key: self.value}}


@patch.method(ast.VheaField)
def toDict(self):
    fields = ("VertTypoAscender", "VertTypoDescender", "VertTypoLineGap")
    canonical_key = next((f for f in fields if f.lower() == self.key), self.key)
    return {"VheaField": {canonical_key: self.value}}


@patch.method(ast.STATDesignAxisStatement)
def toDict(self):
    return {
        "STATDesignAxis": {
            "Tag": self.tag,
            "AxisOrder": self.axisOrder,
            "Names": [n.toDict() for n in self.names],
        }
    }


ast.ElidedFallbackName._serialize_attrs = {"names": "Names"}
ast.ElidedFallbackNameID._serialize_attrs = "value"


@patch.method(ast.STATAxisValueStatement)
def toDict(self):
    result = {
        "Locations": [loc.toDict() for loc in self.locations],
        "Names": [name.toDict() for name in self.names],
    }

    if self.flags:
        flags = ["OlderSiblingFontAttribute", "ElidableAxisValueName"]
        flagStrings = []
        curr = 1
        for i in range(len(flags)):
            if self.flags & curr != 0:
                flagStrings.append(flags[i])
            curr = curr << 1
        result["Flags"] = flagStrings
    return {"STATAxisValue": result}


ast.AxisValueLocationStatement._serialize_name = "AxisValueLocation"
ast.AxisValueLocationStatement._serialize_attrs = {
    "tag": "Tag",
    "values": "Values",
}


@patch.method(ast.ConditionsetStatement)
def toDict(self):
    return {
        "ConditionSet": {
            "Name": self.name,
            "Conditions": {
                tag: {"Min": minvalue, "Max": maxvalue}
                for tag, (minvalue, maxvalue) in self.conditions.items()
            },
        }
    }


ast.VariationBlock._serialize_attrs = {
    "name": "Name",
    "conditionset": "ConditionSet",
    "use_extension": "UseExtension",
    "statements": "Statements",
}
ast.VariationBlock._serialize_name = "Variation"
