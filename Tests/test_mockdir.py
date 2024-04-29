from mockdir import *
import shutil

def test_font_family_dir_TEST_1(tmp_path, sample_dir_structures):
    fontFamilyName = "TEST_1"
    structure = sample_dir_structures[fontFamilyName]
    path = Path(tmp_path) / fontFamilyName
    font_family_dir_mock = mockDirectoriesAndFiles(path, structure)
    clean_dirStructure = [s.strip() for s in structure.strip().split("\n")]
    assert set(clean_dirStructure) == set(dirAsString(font_family_dir_mock).split("\n"))
    shutil.rmtree(font_family_dir_mock)
