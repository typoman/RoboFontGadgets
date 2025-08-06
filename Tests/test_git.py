from fontParts import base
from fontParts.base import BaseGlyph, glyph
from utils import *
import fontgadgets.extensions.git


TEST_FONT_PATH = Path(__file__).parent.joinpath("git_data/fonts/font_1.ufo")


@pytest.fixture(scope="function")
def test_font():
    return defcon.Font(TEST_FONT_PATH)


def test_font_git_property(test_font):
    assert hasattr(test_font, "git")
    from fontgadgets.extensions.git.font import FontGitLoader

    assert isinstance(test_font.git, FontGitLoader)


def test_glyph_git_property(test_font):
    glyph = test_font["A"]
    from fontgadgets.extensions.git.glyph import GlyphGit

    assert isinstance(glyph.git, GlyphGit)


def test_font_git_commits_retrieval(test_font):
    commits = test_font.git.commits
    messages = test_font.git.commitsMessages
    expected_commit_count = 8
    assert len(commits) == expected_commit_count
    assert len(messages) == expected_commit_count
    assert messages[0].strip() == "add contours to C"
    assert messages[-1].strip() == "init"
    assert commits[0].startswith("469ee93")


def test_get_changed_glyphs_at_commit(test_font):
    changed_glyphs = test_font.git.getChangedGlyphsAtCommit(commit_index=4)
    assert changed_glyphs == {"A"}
    changed_glyphs_added = test_font.git.getChangedGlyphsAtCommit(commit_index=3)
    assert changed_glyphs_added == {"C", "D", "E"}


def test_glyph_reset_to_head(test_font):
    glyph_A = test_font["A"]
    original_width = glyph_A.width
    original_contour_count = len(glyph_A)
    glyph_A.width = 1000
    glyph_A.clearContours()
    assert glyph_A.width != original_width
    assert len(glyph_A) != original_contour_count
    glyph_A.git.reset()
    assert glyph_A.width == original_width
    assert len(glyph_A) == original_contour_count


def test_glyph_reset_to_older_commit(test_font):
    glyph_C = test_font["C"]
    assert len(glyph_C) > 0
    # Reset to commit 3 ('3d1870b'), where 'C' was added but was empty.
    glyph_C.git.reset(commit_index=3)
    # Verify 'C' is now empty of contours, as it was in that commit.
    assert len(glyph_C) == 0
    # Verify its width matches the width from that historical commit.
    font_at_commit = test_font.git.getFontAtCommit(commit_index=3)
    width_at_commit = font_at_commit["C"].width
    assert glyph_C.width == width_at_commit


def test_glyph_reset_with_base_glyphs(test_font):
    glyph_B = test_font["B"]
    glyph_A = test_font["A"]
    original_B_contours = len(glyph_B)
    original_B_components = len(glyph_B.components)
    original_A_contours = len(glyph_A)

    assert original_A_contours != 0
    assert original_B_contours != 0

    # Modify both glyphs (B and its base glyph A)
    glyph_B.clearData()
    glyph_A.clearData()
    assert len(glyph_A) == 0
    assert len(glyph_B) == 0
    assert len(glyph_B.components) == 0

    # Reset glyph B to where it had components
    # This should restore both B and its base glyph A
    glyph_B.git.reset(base_glyphs=True)

    assert len(glyph_B) == original_B_contours
    assert len(glyph_B.components) == original_B_components
    assert len(glyph_A) == original_A_contours
