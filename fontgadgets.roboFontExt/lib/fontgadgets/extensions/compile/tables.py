from fontTools.ttLib import TTFont, newTable
from ufo2ft.fontInfoData import intListToNum, normalizeStringForPostscript

def _isNonBMP(s):
    for c in s:
        if ord(c) > 65535:
            return True
    return False

def create_head_table(
    versionMajor,
    versionMinor,
    unitsPerEm,
    styleMapStyleName,
    openTypeHeadFlags,
    openTypeHeadLowestRecPPEM,
    created=3527779198,
    modified=3623536770,
    xMin=0,
    yMin=0,
    xMax=0,
    yMax=0
):
    head = newTable("head")
    head.checkSumAdjustment = 0
    head.tableVersion = 1.0
    head.magicNumber = 0x5F0F3CF5
    head.fontDirectionHint = 2
    head.indexToLocFormat = 0
    head.glyphDataFormat = 0
    fullFontRevision = float("%d.%03d" % (versionMajor, versionMinor))
    head.fontRevision = round(fullFontRevision, 3)
    head.unitsPerEm = unitsPerEm

    macStyle = []
    if styleMapStyleName == "bold":
        macStyle = [0]
    elif styleMapStyleName == "bold italic":
        macStyle = [0, 1]
    elif styleMapStyleName == "italic":
        macStyle = [1]
    head.macStyle = intListToNum(macStyle, 0, 16)

    head.flags = intListToNum(openTypeHeadFlags, 0, 16)
    head.lowestRecPPEM = round(openTypeHeadLowestRecPPEM)

    head.xMin = xMin
    head.yMin = yMin
    head.xMax = xMax
    head.yMax = yMax
    head.created = created
    head.modified = modified

    return head


def create_name_table(
    openTypeNameRecords,
    styleMapFamilyName,
    styleMapStyleName,
    copyright,
    openTypeNameUniqueID,
    openTypeNameVersion,
    postscriptFontName,
    trademark,
    openTypeNameManufacturer,
    openTypeNameDesigner,
    openTypeNameDescription,
    openTypeNameManufacturerURL,
    openTypeNameDesignerURL,
    openTypeNameLicense,
    openTypeNameLicenseURL,
    openTypeNamePreferredFamilyName,
    openTypeNamePreferredSubfamilyName,
    openTypeNameCompatibleFullName,
    openTypeNameSampleText,
    openTypeNameWWSFamilyName,
    openTypeNameWWSSubfamilyName
):
    name = newTable("name")
    name.names = []

    familyName = styleMapFamilyName
    styleName = styleMapStyleName.title()
    preferredFamilyName = openTypeNamePreferredFamilyName
    preferredSubfamilyName = openTypeNamePreferredSubfamilyName

    fullName = f'{preferredFamilyName} {preferredSubfamilyName}'

    nameVals = {
        0: copyright,
        1: familyName,
        2: styleName,
        3: openTypeNameUniqueID,
        4: fullName,
        5: openTypeNameVersion,
        6: postscriptFontName,
        7: trademark,
        8: openTypeNameManufacturer,
        9: openTypeNameDesigner,
        10: openTypeNameDescription,
        11: openTypeNameManufacturerURL,
        12: openTypeNameDesignerURL,
        13: openTypeNameLicense,
        14: openTypeNameLicenseURL,
        16: preferredFamilyName,
        17: preferredSubfamilyName,
        18: openTypeNameCompatibleFullName,
        19: openTypeNameSampleText,
        21: openTypeNameWWSFamilyName,
        22: openTypeNameWWSSubfamilyName
    }

    if nameVals.get(1) == nameVals.get(16) and nameVals.get(2) == nameVals.get(17):
        del nameVals[16]
        del nameVals[17]

    if nameVals.get(6):
        nameVals[6] = normalizeStringForPostscript(nameVals[6])

    for nameId in sorted(nameVals.keys()):
        nameVal = nameVals[nameId]
        if not nameVal:
            continue
        platformId = 3
        platEncId = 10 if _isNonBMP(nameVal) else 1
        langId = 1033
        if name.getName(nameId, platformId, platEncId, langId):
            continue
        name.setName(nameVal, nameId, platformId, platEncId, langId)

    for nameRecord in openTypeNameRecords:
        nameId = nameRecord['nameID']
        platformId = nameRecord['platformID']
        platEncId = nameRecord['encodingID']
        langId = nameRecord['languageID']
        nameVal = nameRecord['string']
        name.setName(nameVal, nameId, platformId, platEncId, langId)

    return name