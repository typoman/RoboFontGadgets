from fontgadgets.decorators import font_property
import fontgadgets.extensions.git.font
import fontgadgets.extensions.glyph

"""
todo:
- add options for resetting left and right margin
"""

class GlyphGit:

    def __init__(self, glyph):
        self._glyph = glyph
        self._layer = glyph.layer
        self._fontGit = glyph.font.git

    def copyContentsFromCommit(
        self,
        other_glyph=None,
        commit_index=None,
        replace_data=True,
        base_glyphs=False,
        width=True,
        height=True,
        unicodes=False,
        note=True,
        image=True,
        contours=True,
        components=True,
        anchors=True,
        guidelines=True,
        lib=True,
    ):
        """
        Copies selected data from a historical commit of the current glyph to
        a target glyph. This operation can be very slow if ran on multiple
        glyphs with the option `base_glyphs` is set to `True` as it can cause
        the already loaded base glyphs of each composite to be retrieved on
        each glyph recursively.

        This method retrieves the state of the glyph at a specific Git commit
        and copies its attributes to `other_glyph`. If `other_glyph` is not
        provided, the data is copied back into the original glyph.

        Args:
            other_glyph (defcon.Glyph, optional): The target glyph object to copy data into.
                If None, data is copied to the glyph associated with this `GlyphGit` instance.
                Defaults to None.
            commit_index (int, optional): The index of the commit in the font's Git history
                from which to retrieve the glyph data. Higher index means older commits
                (0 is the latest). If None, data from the current (latest) commit
                is used. Defaults to None.
            replace_data (bool, optional): If True, the specified attributes in `other_glyph`
                will be cleared before copying. If False, new data will be added on top of
                existing data (e.g., new contours will be appended). Defaults to True.
            base_glyphs (bool, optional): If True, and the glyph at the commit contains
                components, this method will recursively call itself to ensure that the base
                glyphs of those components are also restored to their state at the specified
                `commit_index` in the target font. Defaults to False.
            width (bool, optional): Whether to copy the glyph's width. Defaults to True.
            height (bool, optional): Whether to copy the glyph's height. Defaults to True.
            unicodes (bool, optional): Whether to copy the glyph's unicodes. Defaults to False.
            note (bool, optional): Whether to copy the glyph's note. Defaults to True.
            image (bool, optional): Whether to copy the glyph's image. Defaults to True.
            contours (bool, optional): Whether to copy the glyph's contours. Defaults to True.
            components (bool, optional): Whether to copy the glyph's components. Defaults to True.
            anchors (bool, optional): Whether to copy the glyph's anchors. Defaults to True.
            guidelines (bool, optional): Whether to copy the glyph's guidelines. Defaults to True.
            lib (bool, optional): Whether to copy the glyph's lib data. Defaults to True.

        Returns:
            None

        Raises:
            IndexError: If `commit_index` is out of range for the font's commit history.
            ValueError: If the font associated with the glyph does not have a path (required for Git operations).

        """
        if other_glyph is None:
            other_glyph = self._glyph
        font_at_commit = self._fontGit.getFontAtCommit(commit_index)
        glyph_at_commit = font_at_commit[self._glyph.name]
        other_glyph_layer = other_glyph.layer
        if base_glyphs:
            for c in glyph_at_commit.components:
                bgn = c.baseGlyph
                sg = self._layer[bgn]  # source glyph but we need it at a commit
                tg = other_glyph_layer[bgn]  # the glyph that will recieve the data
                sg.git.copyContentsFromCommit(
                    other_glyph=tg,
                    commit_index=commit_index,
                    replace_data=replace_data,
                    width=width,
                    height=height,
                    unicodes=unicodes,
                    note=note,
                    image=image,
                    contours=contours,
                    components=components,
                    anchors=anchors,
                    guidelines=guidelines,
                    lib=lib,
                )
        if replace_data:
            other_glyph.clearData(
                unicodes=unicodes,
                note=note,
                image=image,
                contours=contours,
                components=components,
                anchors=anchors,
                guidelines=guidelines,
                lib=lib,
            )
        other_glyph.copyContentsFromGlyph(
            glyph_at_commit,
            width=width,
            height=height,
            unicodes=unicodes,
            note=note,
            image=image,
            contours=contours,
            components=components,
            anchors=anchors,
            guidelines=guidelines,
            lib=lib,
        )

    def reset(
        self,
        commit_index=None,
        base_glyphs=False,
        width=True,
        height=True,
        unicodes=False,
        note=True,
        image=True,
        contours=True,
        components=True,
        anchors=True,
        guidelines=True,
        lib=True,
    ):
        """
        Resets the glyph data to the state of a specified commit.

        This method is a convenience wrapper around `copyContentsFromCommit`. It resets
        the current glyph (`self._glyph`) to its state at a given `commit_index`.

        Args:
            commit_index (int, optional): The index of the commit in the font's Git history
                to which the glyph data should be reset. Higher index means older commits
                (0 is the latest). If None, the glyph is reset to the state of the
                current (latest) commit. Defaults to None.
            base_glyphs (bool, optional): If True, and the glyph at the commit
                contains components, this method will recursively ensure that the base glyphs
                of those components are also reset to their state at the specified
                `commit_index`. Defaults to False.
            width (bool, optional): Whether to reset the glyph's width. Defaults to True.
            height (bool, optional): Whether to reset the glyph's height. Defaults to True.
            unicodes (bool, optional): Whether to reset the glyph's unicodes. Defaults to False.
            note (bool, optional): Whether to reset the glyph's note. Defaults to True.
            image (bool, optional): Whether to reset the glyph's image. Defaults to True.
            contours (bool, optional): Whether to reset the glyph's contours. Defaults to True.
            components (bool, optional): Whether to reset the glyph's components. Defaults to True.
            anchors (bool, optional): Whether to reset the glyph's anchors. Defaults to True.
            guidelines (bool, optional): Whether to reset the glyph's guidelines. Defaults to True.
            lib (bool, optional): Whether to reset the glyph's lib data. Defaults to True.

        Returns:
            None

        """
        self.copyContentsFromCommit(
            other_glyph=self._glyph,
            commit_index=commit_index,
            replace_data=True,
            base_glyphs=base_glyphs,
            width=width,
            height=height,
            unicodes=unicodes,
            note=note,
            image=image,
            contours=contours,
            components=components,
            anchors=anchors,
            guidelines=guidelines,
            lib=lib,
        )


@font_property
def git(glyph):
    return GlyphGit(glyph)
