from utils import assertTableSameAsTTX
import unittest
from fontgadgets.extensions.compile.tables import *

class FontTablesTest(unittest.TestCase):

    def test_head(self):
        versionMajor = 1
        versionMinor = 0
        unitsPerEm = 1000
        styleMapStyleName = "Regular"
        openTypeHeadFlags = []
        openTypeHeadLowestRecPPEM = 0
        head_table = create_head_table(
            versionMajor=versionMajor,
            versionMinor=versionMinor,
            unitsPerEm=unitsPerEm,
            styleMapStyleName=styleMapStyleName,
            openTypeHeadFlags=openTypeHeadFlags,
            openTypeHeadLowestRecPPEM=openTypeHeadLowestRecPPEM
        )

        assertTableSameAsTTX(head_table, 'tables/test_head_table.ttx')

    def test_name(self):
        openTypeNameRecords = [
            {'nameID': 256, 'platformID': 1, 'encodingID': 0, 'languageID': 0, 'string': 'Custom Name'},
        ]
        styleMapFamilyName = "Test Font"
        styleMapStyleName = "Regular"
        copyright = "Copyright 2023 Test Font"
        openTypeNameUniqueID = "1.000;TEST;TestFont-Regular"
        openTypeNameVersion = "Version 1.000"
        postscriptFontName = "TestFont-Regular"
        trademark = "Test Font is a trademark"
        openTypeNameManufacturer = "Test Foundry"
        openTypeNameDesigner = "Test Designer"
        openTypeNameDescription = "A test font"
        openTypeNameManufacturerURL = "http://testfoundry.com"
        openTypeNameDesignerURL = "http://testdesigner.com"
        openTypeNameLicense = "Test License"
        openTypeNameLicenseURL = "http://testlicense.com"
        openTypeNamePreferredFamilyName = "Test Font"
        openTypeNamePreferredSubfamilyName = "Regular"
        openTypeNameCompatibleFullName = "Test Font Regular"
        openTypeNameSampleText = "Testing 123"
        openTypeNameWWSFamilyName = "Test Font"
        openTypeNameWWSSubfamilyName = "Regular"

        name_table = create_name_table(
            openTypeNameRecords=openTypeNameRecords,
            styleMapFamilyName=styleMapFamilyName,
            styleMapStyleName=styleMapStyleName,
            copyright=copyright,
            openTypeNameUniqueID=openTypeNameUniqueID,
            openTypeNameVersion=openTypeNameVersion,
            postscriptFontName=postscriptFontName,
            trademark=trademark,
            openTypeNameManufacturer=openTypeNameManufacturer,
            openTypeNameDesigner=openTypeNameDesigner,
            openTypeNameDescription=openTypeNameDescription,
            openTypeNameManufacturerURL=openTypeNameManufacturerURL,
            openTypeNameDesignerURL=openTypeNameDesignerURL,
            openTypeNameLicense=openTypeNameLicense,
            openTypeNameLicenseURL=openTypeNameLicenseURL,
            openTypeNamePreferredFamilyName=openTypeNamePreferredFamilyName,
            openTypeNamePreferredSubfamilyName=openTypeNamePreferredSubfamilyName,
            openTypeNameCompatibleFullName=openTypeNameCompatibleFullName,
            openTypeNameSampleText=openTypeNameSampleText,
            openTypeNameWWSFamilyName=openTypeNameWWSFamilyName,
            openTypeNameWWSSubfamilyName=openTypeNameWWSSubfamilyName
        )

        assertTableSameAsTTX(name_table, 'tables/test_name_table.ttx')


if __name__ == "__main__":
    unittest.main()