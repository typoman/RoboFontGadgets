from fontTools.feaLib.ast import LigatureSubstStatement
import fontgadgets.extensions.unicode
from fontgadgets.decorators import *
import fontgadgets.extensions.glyph.composite

"""
todo
set, get type of a glyph using this lib:
testufo.lib["public.openTypeCategories"] = {
    "a": "base",
    "f.component": "component",
    "f_i": "ligature",
    "acutecomb": "mark",
}
"""

class GlyphTypeInterpreter:
    MARK_UNI_STR = "FBB2..FBC1 0060 00A8 00AF 00B4 00B8 02B0..02C1 FC5E..FC63 02C2..02C5 02C6..02D1 02D2..02DF 02E0..02E4 02E5..02EB 02EC 02ED 02EE 02EF..02FF 0300..034E 0350..0357 035D..0362 0374 0375 037A 0384..0385 0483..0487 0559 0591..05A1 05A3..05BD 05BF 05C1..05C2 05C4 064B..0652 0657..0658 06DF..06E0 06E5..06E6 06EA..06EC 0730..074A 07A6..07B0 07EB..07F3 07F4..07F5 0818..0819 08E4..08FE 093C 094D 0951..0954 0971 09BC 09CD 0A3C 0A4D 0ABC 0ACD 0B3C 0B4D 0BCD 0C4D 0CBC 0CCD 0D4D 0DCA 0E47..0E4C 0E4E 0EC8..0ECC 0F18..0F19 0F35 0F37 0F39 0F3E..0F3F 0F82..0F84 0F86..0F87 0FC6 1037 1039..103A 1087..108C 108D 108F 109A..109B 17C9..17D3 17DD 1939..193B 1A75..1A7C 1A7F 1AB0..1ABD 1B34 1B44 1B6B..1B73 1BAA 1BAB 1C36..1C37 1C78..1C7D 1CD0..1CD2 1CD3 1CD4..1CE0 1CE1 1CE2..1CE8 1CED 1CF4 1CF8..1CF9 1D2C..1D6A 1DC4..1DCF 1DF5 1DFD..1DFF 1FBD 1FBF..1FC1 1FCD..1FCF 1FDD..1FDF 1FED..1FEF 1FFD..1FFE 2CEF..2CF1 2E2F 302A..302D 302E..302F 3099..309A 309B..309C 30FC A66F A67C..A67D A67F A69C..A69D A6F0..A6F1 A717..A71F A720..A721 A788 A7F8..A7F9 A8C4 A8E0..A8F1 A92B..A92D A92E A953 A9B3 A9C0 A9E5 AA7B AA7C AA7D AABF AAC0 AAC1 AAC2 AAF6 AB5B AB5C..AB5F ABEC ABED FB1E FE20..FE2D FF3E FF40 FF70 FF9E..FF9F FFE3 102E0 10AE5..10AE6 110B9..110BA 11133..11134 11173 111C0 11235 11236 112E9..112EA 1133C 1134D 11366..1136C 11370..11374 114C2..114C3 115BF..115C0 1163F 116B6 116B7 16AF0..16AF4 16F8F..16F92 16F93..16F9F 1D167..1D169 1D16D..1D172 1D17B..1D182 1D185..1D18B 1D1AA..1D1AD 1E8D0..1E8D6 ################CombinationMarks 0080..0084 0086..009F 0300..034E 0350..035B 0363..036F 0483..0487 0488..0489 0591..05BD 05BF 05C1..05C2 05C4..05C5 05C7 0610..061A 061C 064B..065F 0670 06D6..06DC 06DF..06E4 06E7..06E8 06EA..06ED 0711 0730..074A 07A6..07B0 07EB..07F3 0816..0819 081B..0823 0825..0827 0829..082D 0859..085B 08E4..08FF 0900..0902 0903 093A 093B 093C 093E..0940 0941..0948 0949..094C 094D 094E..094F 0951..0957 0962..0963 0981 0982..0983 09BC 09BE..09C0 09C1..09C4 09C7..09C8 09CB..09CC 09CD 09D7 09E2..09E3 0A01..0A02 0A03 0A3C 0A3E..0A40 0A41..0A42 0A47..0A48 0A4B..0A4D 0A51 0A70..0A71 0A75 0A81..0A82 0A83 0ABC 0ABE..0AC0 0AC1..0AC5 0AC7..0AC8 0AC9 0ACB..0ACC 0ACD 0AE2..0AE3 0B01 0B02..0B03 0B3C 0B3E 0B3F 0B40 0B41..0B44 0B47..0B48 0B4B..0B4C 0B4D 0B56 0B57 0B62..0B63 0B82 0BBE..0BBF 0BC0 0BC1..0BC2 0BC6..0BC8 0BCA..0BCC 0BCD 0BD7 0C00 0C01..0C03 0C3E..0C40 0C41..0C44 0C46..0C48 0C4A..0C4D 0C55..0C56 0C62..0C63 0C81 0C82..0C83 0CBC 0CBE 0CBF 0CC0..0CC4 0CC6 0CC7..0CC8 0CCA..0CCB 0CCC..0CCD 0CD5..0CD6 0CE2..0CE3 0D01 0D02..0D03 0D3E..0D40 0D41..0D44 0D46..0D48 0D4A..0D4C 0D4D 0D57 0D62..0D63 0D82..0D83 0DCA 0DCF..0DD1 0DD2..0DD4 0DD6 0DD8..0DDF 0DF2..0DF3 0F18..0F19 0F35 0F37 0F39 0F3E..0F3F 0F71..0F7E 0F80..0F84 0F86..0F87 0F8D..0F97 0F99..0FBC 0FC6 135D..135F 1712..1714 1732..1734 1752..1753 1772..1773 180B..180D 18A9 1920..1922 1923..1926 1927..1928 1929..192B 1930..1931 1932 1933..1938 1939..193B 1A17..1A18 1A19..1A1A 1A1B 1A7F 1AB0..1ABD 1ABE 1B00..1B03 1B04 1B34 1B35 1B36..1B3A 1B3B 1B3C 1B3D..1B41 1B42 1B43..1B44 1B6B..1B73 1B80..1B81 1B82 1BA1 1BA2..1BA5 1BA6..1BA7 1BA8..1BA9 1BAA 1BAB..1BAD 1BE6 1BE7 1BE8..1BE9 1BEA..1BEC 1BED 1BEE 1BEF..1BF1 1BF2..1BF3 1C24..1C2B 1C2C..1C33 1C34..1C35 1C36..1C37 1CD0..1CD2 1CD4..1CE0 1CE1 1CE2..1CE8 1CED 1CF2..1CF3 1CF4 1CF8..1CF9 1DC0..1DF5 1DFC..1DFF 202A..202E 2066..206F 20D0..20DC 20DD..20E0 20E1 20E2..20E4 20E5..20F0 2CEF..2CF1 2D7F 2DE0..2DFF 302A..302D 302E..302F 3035 3099..309A A66F A670..A672 A674..A67D A69F A6F0..A6F1 A802 A806 A80B A823..A824 A825..A826 A827 A880..A881 A8B4..A8C3 A8C4 A8E0..A8F1 A926..A92D A947..A951 A952..A953 A980..A982 A983 A9B3 A9B4..A9B5 A9B6..A9B9 A9BA..A9BB A9BC A9BD..A9C0 AA29..AA2E AA2F..AA30 AA31..AA32 AA33..AA34 AA35..AA36 AA43 AA4C AA4D AAEB AAEC..AAED AAEE..AAEF AAF5 AAF6 ABE3..ABE4 ABE5 ABE6..ABE7 ABE8 ABE9..ABEA ABEC ABED FB1E FE00..FE0F FE20..FE2D FFF9..FFFB 101FD 102E0 10376..1037A 10A01..10A03 10A05..10A06 10A0C..10A0F 10A38..10A3A 10A3F 10AE5..10AE6 11000 11001 11002 11038..11046 1107F 11080..11081 11082 110B0..110B2 110B3..110B6 110B7..110B8 110B9..110BA 11100..11102 11127..1112B 1112C 1112D..11134 11173 11180..11181 11182 111B3..111B5 111B6..111BE 111BF..111C0 1122C..1122E 1122F..11231 11232..11233 11234 11235 11236..11237 112DF 112E0..112E2 112E3..112EA 11301 11302..11303 1133C 1133E..1133F 11340 11341..11344 11347..11348 1134B..1134D 11357 11362..11363 11366..1136C 11370..11374 114B0..114B2 114B3..114B8 114B9 114BA 114BB..114BE 114BF..114C0 114C1 114C2..114C3 115AF..115B1 115B2..115B5 115B8..115BB 115BC..115BD 115BE 115BF..115C0 11630..11632 11633..1163A 1163B..1163C 1163D 1163E 1163F..11640 116AB 116AC 116AD 116AE..116AF 116B0..116B5 116B6 116B7 16AF0..16AF4 16B30..16B36 16F51..16F7E 16F8F..16F92 1BC9D..1BC9E 1BCA0..1BCA3 1D165..1D166 1D167..1D169 1D16D..1D172 1D173..1D17A 1D17B..1D182 1D185..1D18B 1D1AA..1D1AD 1D242..1D244 1E8D0..1E8D6 E0001 E0020..E007F E0100..E01EF".split(
        " "
    )
    MARK_UNI_SINGLES = set()
    MARK_UNI_RANGES = set()

    def __init__(self, font):
        self.font = font
        self.glyphTypesCache = {}
        self.checkedGlyphs = {} # glyphs that was checked already to avoid infinite loops
        for line in self.MARK_UNI_STR:
            if line and line[0] != "#":
                splittedLine = line.split("..")
                if len(splittedLine) < 2:
                    self.MARK_UNI_SINGLES.add(int(splittedLine[0], 16))
                else:
                    self.MARK_UNI_RANGES.add(
                        (int(splittedLine[0], 16), int(splittedLine[1], 16))
                    )

    def _isUnicodeDiacritic(self, univalue):
        if univalue in self.MARK_UNI_SINGLES:
            return True
        for entry in self.MARK_UNI_RANGES:
            if univalue >= entry[0] and univalue <= entry[1]:
                return True
        return False

    def _setGlyphType(self, glyphName, typeName):
        self.glyphTypesCache[glyphName] = typeName
        return True

    def _checkCache(self, glyphName, typeName):
        if glyphName in self.glyphTypesCache:
            return self.glyphTypesCache[glyphName] == typeName

    def isMark(self, glyphName):
        cache = self._checkCache(glyphName, "mark")
        if cache is not None:
            return cache
        if self.checkedGlyphs.get(glyphName, {}).get("mark", False) is True:
            return
        self.checkedGlyphs.setdefault(glyphName, {})["mark"] = True
        glyph = self.font[glyphName]
        for uni in glyph.pseudoUnicodes:
            if self._isUnicodeDiacritic(uni):
                return self._setGlyphType(glyphName, "mark")
        if glyph.width == 0:
            for a in glyph.anchors:
                if a.name[0] == "_":
                    return self._setGlyphType(glyphName, "mark")
        if glyph.isComposite and all((map(self.isMark, [c.baseGlyph for c in glyph.components]))):
            return self._setGlyphType(glyphName, "mark")
        return False

    def isBase(self, glyphName):
        cache = self._checkCache(glyphName, "base")
        if cache is not None:
            return cache
        if any([self.isLigature(glyphName), self.isMark(glyphName)]):
            return False
        return self._setGlyphType(glyphName, "base")

    def isLigature(self, glyphName):
        cache = self._checkCache(glyphName, "ligature")
        if cache is not None:
            return cache
        if self.checkedGlyphs.get(glyphName, {}).get("ligature", False) is True:
            return # avoids recursion
        self.checkedGlyphs.setdefault(glyphName, {})["ligature"] = True
        if self.isMark(glyphName) is True:
            return False
        glyph = self.font[glyphName]
        for sgnames, rules in glyph.features.sourceGlyphs.items():
            for rule in rules:
                if isinstance(rule, LigatureSubstStatement):
                    return self._setGlyphType(glyphName, "ligature")
            for sgname in sgnames:
                if self.isLigature(sgname) is True:
                    return self._setGlyphType(glyphName, "ligature")
        return False

    def getGlyphType(self, glyphName):
        if self.isMark(glyphName) is True:
            return "mark"
        elif self.isLigature(glyphName) is True:
            return "ligature"
        return "base"


@font_cached_property(
    "UnicodeData.Changed",
    "Features.Changed",
    "Layer.GlyphAdded",
    "Layer.GlyphDeleted",
    "Glyph.AnchorsChanged",
)
def glyphTypeInterpreter(font):
    return GlyphTypeInterpreter(font)


@font_property
def isMark(glyph):
    """
    Returns True if glyph type is mark, otherwise it returns False.
    """
    return glyph.font.glyphTypeInterpreter.isMark(glyph.name)


@font_property
def isLigature(glyph):
    """
    Returns True if glyph type is ligature, otherwise it returns False.
    """
    return glyph.font.glyphTypeInterpreter.isLigature(glyph.name)


@font_property
def isBase(glyph):
    """
    Returns True if glyph type is base, otherwise it returns False.
    """
    return glyph.font.glyphTypeInterpreter.isBase(glyph.name)


@font_method
def getType(glyph):
    """
    Returns the glyph type as `base`, `ligature`, `mark`.
    """
    return glyph.font.glyphTypeInterpreter.getGlyphType(glyph.name)
