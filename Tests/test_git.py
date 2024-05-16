from fontgadgets.tools import FontGadgetsError
from main import *
from unittest.mock import patch
import fontgadgets.extensions.git as fontGit

@pytest.fixture
def mock_font_1():
    font = MagicMock()
    font.path = "/repo/path/font1"
    return font

@pytest.fixture
def mock_font_2():
    font = MagicMock()
    font.path = "/repo/path/font2"
    return font

@pytest.fixture(scope="function")
def mock_repo():
    with patch("git.Repo") as mockGitRepo:
        mock_repo = mockGitRepo.return_value
        mock_repo.head.commit.hexsha = "fakehash1"
        mock_repo.working_dir = "/repo/path"
        yield mock_repo
        fontGit.GITROOT_2_FONTGIT = {}
        fontGit.FONTPATH_2_GITROOT = {}

def test_mock_repo(mock_repo):
    old_hash = mock_repo.head.commit.hexsha
    new_hash = "newfakehash"
    mock_repo.head.commit.hexsha = new_hash
    assert mock_repo.head.commit.hexsha != old_hash

def test_fontgit_singleton(mock_font_1, mock_font_2, mock_repo):
    font_git_1 = fontGit.FontGit(mock_font_1)
    font_git_2 = fontGit.FontGit(mock_font_1)
    assert font_git_1 is font_git_2
    font_git_3 = fontGit.FontGit(mock_font_2)
    assert font_git_1 is font_git_3

def test_fontgit_changed_repo(mock_font_1, mock_repo):
    font_git_1 = fontGit.FontGit(mock_font_1)
    mock_repo.head.commit.hexsha = "newfakehash"
    cached_repo = fontGit.GITROOT_2_FONTGIT[mock_repo.working_dir]["fakehash1"]._repo
    assert cached_repo is mock_repo
    font_git_2 = fontGit.FontGit(mock_font_1)
    assert font_git_1 is not font_git_2
