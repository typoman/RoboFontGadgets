import pytest
from fontgadgets.extensions.collections import FontSet, CharacterSet, Family, FontCollectionsError
from unittest.mock import Mock

@pytest.fixture
def italic_fontSet_sample():
    return FontSet("Italic")

@pytest.fixture(scope="function", autouse=True)
def font_mock_1():
    font = Mock()
    font.path = "/path/to/font.ufo"
    font.fontSet = None
    return font

@pytest.fixture
def font_mock_2():
    font = Mock()
    font.path = "/path/to/font_2.ufo"
    font.fontSet = None
    return font

@pytest.fixture
def designspace_mock():
    designspace = Mock()
    designspace.path = "/path/to/designspace.designspace"
    return designspace

@pytest.fixture(scope="function", autouse=True)
def characterSet_sample_latin():
    return CharacterSet("Latin")

@pytest.fixture
def regular_fontSet_sample():
    regular_fontSet_sample = FontSet("Regular")
    return regular_fontSet_sample

@pytest.fixture
def family_sample_1():
    return Family("Test Family 1")

@pytest.fixture
def family_sample_2(characterSet_sample_latin):
    family_2 = Family("Test Family 2")
    family_2.addCharacterSet(characterSet_sample_latin)
    return family_2

@pytest.mark.parametrize("name", ["Upright", "Roman"])
def test_fontSet_init(italic_fontSet_sample, name):
    italic_fontSet_sample.name = name
    assert italic_fontSet_sample.name == name
    assert italic_fontSet_sample.fonts == []

def test_fontSet_baseFont(italic_fontSet_sample, regular_fontSet_sample, font_mock_1, font_mock_2):
    assert regular_fontSet_sample.baseFont is None
    italic_fontSet_sample.addFont(font_mock_1)
    assert italic_fontSet_sample.baseFont is font_mock_1
    italic_fontSet_sample.addFont(font_mock_2)
    assert italic_fontSet_sample.baseFont is font_mock_1
    italic_fontSet_sample.removeFont(font_mock_1)
    assert italic_fontSet_sample.baseFont is font_mock_2
    italic_fontSet_sample.removeFont(font_mock_2)
    assert italic_fontSet_sample.baseFont is None

def test_fontSet_addFont(italic_fontSet_sample, font_mock_1):
    italic_fontSet_sample.addFont(font_mock_1)
    assert font_mock_1.path in italic_fontSet_sample._fonts
    assert font_mock_1.fontSet is italic_fontSet_sample
    assert italic_fontSet_sample.fonts == [font_mock_1]
    with pytest.raises(FontCollectionsError):
        italic_fontSet_sample.addFont(font_mock_1)

def test_fontSet_removeFont(italic_fontSet_sample, font_mock_1):
    italic_fontSet_sample.addFont(font_mock_1)
    italic_fontSet_sample.removeFont(font_mock_1)
    assert font_mock_1.path not in italic_fontSet_sample._fonts
    assert font_mock_1.fontSet is None

def test_fontSet_getFontByPath(italic_fontSet_sample, font_mock_1):
    italic_fontSet_sample.addFont(font_mock_1)
    assert italic_fontSet_sample.getFontByPath(font_mock_1.path) == font_mock_1
    italic_fontSet_sample.removeFont(font_mock_1)
    with pytest.raises(KeyError):
        italic_fontSet_sample.getFontByPath(font_mock_1.path)

def test_fontSet_designspace(italic_fontSet_sample, designspace_mock):
    italic_fontSet_sample.designspace = designspace_mock
    assert italic_fontSet_sample.designspace.path == "/path/to/designspace.designspace"

def test_characterSet_init(characterSet_sample_latin):
    assert characterSet_sample_latin.name == "Latin"
    assert characterSet_sample_latin.family is None
    assert characterSet_sample_latin.fontSets == []
    assert characterSet_sample_latin._default_fontSet is None

def test_characterSet_add_remove_fontSet(characterSet_sample_latin, regular_fontSet_sample):
    characterSet_sample_latin.addFontSet(regular_fontSet_sample)
    assert regular_fontSet_sample in characterSet_sample_latin.fontSets
    assert regular_fontSet_sample.characterSet is characterSet_sample_latin
    assert characterSet_sample_latin.getFontSetByName("Regular") is regular_fontSet_sample
    assert characterSet_sample_latin.fontSets == [regular_fontSet_sample]

    # renaming fontset
    regular_fontSet_sample.name = "Bold"
    assert characterSet_sample_latin.defaultFontSet is regular_fontSet_sample
    assert characterSet_sample_latin.getFontSetByName("Bold") is regular_fontSet_sample

    characterSet_sample_latin.removeFontSet(regular_fontSet_sample)
    assert regular_fontSet_sample.name not in characterSet_sample_latin._fontSets
    assert regular_fontSet_sample.characterSet is None

def test_characterSet_default_fontSet(characterSet_sample_latin, regular_fontSet_sample):
    characterSet_sample_latin.addFontSet(regular_fontSet_sample)
    assert characterSet_sample_latin.defaultFontSet is regular_fontSet_sample
    characterSet_sample_latin.removeFontSet(regular_fontSet_sample)
    assert characterSet_sample_latin.defaultFontSet.name == 'default.fontSet'

def test_characterSet_getFontSetByName(characterSet_sample_latin, regular_fontSet_sample, italic_fontSet_sample):
    characterSet_sample_latin.addFontSet(regular_fontSet_sample)
    assert characterSet_sample_latin.getFontSetByName("Regular") == regular_fontSet_sample
    characterSet_sample_latin.addFontSet(italic_fontSet_sample)
    assert characterSet_sample_latin.getFontSetByName("Italic") == italic_fontSet_sample
    with pytest.raises(KeyError):
        characterSet_sample_latin.getFontSetByName("default.fontSet")

def test_characterSet_add_remove_font(characterSet_sample_latin, font_mock_2):
    characterSet_sample_latin.addFont(font_mock_2)
    assert characterSet_sample_latin.defaultFontSet.name == 'default.fontSet'
    assert font_mock_2.fontSet.name == 'default.fontSet'
    assert font_mock_2.fontSet is characterSet_sample_latin.getFontSetByName(font_mock_2.fontSet.name)
    characterSet_sample_latin.removeFont(font_mock_2)
    assert font_mock_2.fontSet is None
    with pytest.raises(KeyError):
        characterSet_sample_latin.defaultFontSet.getFontByPath(font_mock_2.path)

def test_characterSet_addFontSet_propogation(regular_fontSet_sample, italic_fontSet_sample, characterSet_sample_latin):
    characterSet_sample_latin.addFontSet(regular_fontSet_sample)
    characterSet_sample_latin.addFontSet(italic_fontSet_sample)
    assert regular_fontSet_sample.characterSet is characterSet_sample_latin
    assert italic_fontSet_sample.characterSet is characterSet_sample_latin

def test_family_name(family_sample_1):
    family_sample_1.name = "Another Name"
    assert family_sample_1.name == "Another Name"

def test_family_add_remove_characterSet(family_sample_1, characterSet_sample_latin):
    family_sample_1.addCharacterSet(characterSet_sample_latin)
    assert characterSet_sample_latin.family.name is family_sample_1.name
    assert family_sample_1.defaultCharacterSet is characterSet_sample_latin
    assert family_sample_1.characterSets == [characterSet_sample_latin]

    # renaming characterSet
    characterSet_sample_latin.name = "Greek"
    assert family_sample_1.defaultCharacterSet is characterSet_sample_latin
    assert family_sample_1.getCharacterSetByName("Greek") is characterSet_sample_latin

    family_sample_1.removeCharacterSet(characterSet_sample_latin)
    assert family_sample_1.defaultCharacterSet.name == "default.characterSet"
    assert characterSet_sample_latin.family is None

def test_family_getCharacterSetByName(family_sample_1, characterSet_sample_latin):
    family_sample_1.addCharacterSet(characterSet_sample_latin)
    retrieved_character_set = family_sample_1.getCharacterSetByName(characterSet_sample_latin.name)
    assert retrieved_character_set.name == characterSet_sample_latin.name
    with pytest.raises(KeyError):
        family_sample_1.getCharacterSetByName("default.characterSet")
    family_sample_1.removeCharacterSet(characterSet_sample_latin)
    assert family_sample_1.getCharacterSetByName("default.characterSet").name == "default.characterSet"

def test_family_addFontSet(family_sample_1, regular_fontSet_sample, family_sample_2, italic_fontSet_sample):
    family_sample_1.addFontSet(regular_fontSet_sample)
    assert family_sample_1.defaultCharacterSet.getFontSetByName("Regular") is regular_fontSet_sample
    assert family_sample_1.defaultCharacterSet.name == "default.characterSet"
    family_sample_2.addFontSet(italic_fontSet_sample)
    assert family_sample_2.defaultCharacterSet.name == "Latin"

def test_family_removeFontSet(family_sample_2, regular_fontSet_sample):
    family_sample_2.addFontSet(regular_fontSet_sample)
    family_sample_2.removeFontSet(regular_fontSet_sample)
    assert family_sample_2.defaultCharacterSet.defaultFontSet.name == "default.fontSet"
    with pytest.raises(FontCollectionsError):
        family_sample_2.removeFontSet(regular_fontSet_sample)

def test_family_addFont(family_sample_1, font_mock_1):
    family_sample_1.addFont(font_mock_1)
    assert font_mock_1.fontSet is family_sample_1.defaultCharacterSet.defaultFontSet

def test_family_removeFont(family_sample_1, font_mock_1, font_mock_2):
    family_sample_1.addFont(font_mock_1)
    family_sample_1.addFont(font_mock_2)
    family_sample_1.removeFont(font_mock_1)
    assert font_mock_1 not in family_sample_1.defaultCharacterSet.defaultFontSet.fonts
    assert family_sample_1.defaultCharacterSet.defaultFontSet.fonts == [font_mock_2]
