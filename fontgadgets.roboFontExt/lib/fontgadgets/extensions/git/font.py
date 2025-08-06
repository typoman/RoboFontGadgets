from fontgadgets.decorators import *
from fontGit.objects.font import FontGit
from fontGit.utils import RepoCache
import logging

logger = logging.getLogger(__name__)


class FontGitLoader:

    def __init__(self, font):
        self._font = font
        path = font.path
        if path is None:
            raise ValueError("Font must have a path to access Git history.")
        self._repo = RepoCache(path)

    def getFontAtCommit(self, commit_index=None):
        """
        Returns a FontGit instance of the font at the specified commit index.

        Parameters:
            commit_index (int or None): Index of the commit in the Git history.
                                    Higher index means older commits.
                                    If None, returns the current commit.

        Returns:
            FontGit: A FontGit instance representing the font at that commit.
        """
        commit_sha = None
        if commit_index is not None:
            commits = self._repo.commits
            if commit_index >= len(commits):
                raise IndexError(
                    f"Commit index {commit_index} is out of range. Only {len(commits)} commits available."
                )
            commit_sha = commits[commit_index]
        return FontGit.open_at_commit(self._font.path, commit_sha=commit_sha)

    def getChangedGlyphsAtCommit(self, commit_index=None) -> set:
        """
        Returns a set of glyph names that have changed at a specific commit
        index. If no commit_index is given, then the changed glyphs since the
        last commit will be returned.

        Parameters:
            commit_index (int or None): Index of the commit in the Git history.
                                    Higher index means older commits.
                                    If None, compares to the previous commit.

        Returns:
            set: A set of glyph names that differ from the specified commit.
        """
        fc = self.getFontAtCommit(commit_index)
        diff = fc.diffGlyphNames()
        result = set()
        for _, glyph_set in diff.items():
            result.update(glyph_set)
        return result

    @property
    def commits(self):
        return self._repo.commits

    @property
    def commitsMessages(self):
        """Returns a list of all commit messages for the repository."""
        messages = []
        for commit_hash in self._repo.commits:
            try:
                commit_object = self._repo.get_commit_by_hash(commit_hash)
                messages.append(commit_object.message)
            except Exception as e:
                logger.error(f"Failed to get commit message for {commit_hash}: {e}")
                messages.append("<Error retrieving commit message>")
        return messages


@font_property
def git(font):
    return FontGitLoader(font)
