from main import *
from fontgadgets.extensions.collections.parser import *
from mockdir import *
import shutil

@pytest.mark.parametrize(
    "input_text, expected_output",
    [
        ("1- Arabic Latin", "Arabic Latin"),
        ("Cyrillic Latin", "Cyrillic Latin"),
        ("23. English 2 Arabic", "English 2 Arabic"),
    ],
)
def test_remove_sort_digits(input_text, expected_output):
    assert remove_sort_digits(input_text) == expected_output

@pytest.fixture
def sample_dir_Test_1(tmp_path, sample_dir_structures):
    mock_string = sample_dir_structures["TEST_1"]
    mock_path = tmp_path / "TEST_1"
    mockDirectoriesAndFiles(mock_path, mock_string)
    yield mock_path
    shutil.rmtree(mock_path)


def test_1(sample_dir_Test_1, mock_defcon_font_module):
    family_1 = FamilyParser(family_root=sample_dir_Test_1)
    assert family_1.getFamily().to_dict() == {
    }
