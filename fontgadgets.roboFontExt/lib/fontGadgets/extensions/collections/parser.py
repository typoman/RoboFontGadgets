import re
import os
import glob
from fontgadgets.log import logger
from collections import OrderedDict
import defcon
from fontgadgets.extensions.collections import *
from pathlib import Path

def remove_sort_digits(text):
    """
    Used to remove digits at the beginning of the string for manual charset sorting.
    """
    pattern = r'^([\d]+[-.]?\s?)' # matches digits at the beginning of the string
    replacement = ''

    output = re.sub(pattern, replacement, text)
    return output

class FamilyParser():
    """
    This class is used to parse a folder to create a family family file format
    or load a family file format.
    file suffix: fontfamily

    Family file format contains information about the designspace and font info
    and where this information is stored. It can contain information used to
    compile fonts, like the compiler and its flags.
    """

    def __init__(self, file_path=None, family_root=None):
        self.file_path = Path(file_path) if file_path is not None else None
        self.family_root = Path(family_root) if family_root is not None else None
        if all([x is None for x in [file_path, family_root]]):
            raise ValueError("Must provide either file_path or family_root")
        self.charsets = OrderedDict()
        self.fontsets = OrderedDict()
        self.input_path_to_font = {}  # path:defcon.Font
        if self.family_root is not None:
            self.parseFolderStructure()
        if file_path is not None:
            self.file_path = file_path
            self.family = Family.load(self.file_path)

    def parseFolderStructure(self):
        # recursively find ufo files under the family root using glob
        for ufo_path in glob.glob(str(self.family_root) + '/**/*.ufo', recursive=True):
            self.input_path_to_font[ufo_path] = defcon.Font(ufo_path)
            logger.info("READING %s" % os.path.relpath(ufo_path, self.family_root))
        self.parseCharacterSetFromFolderStructure()

    def parseCharacterSetFromFolderStructure(self):
        """
        Groups the fonts into different charsets. This is done by
        finding their highest parent dir name.
        """
        for path, font in sorted(self.input_path_to_font.items()):
            relative_path = os.path.relpath(self.family_root, path)
            charset_name = remove_sort_digits(relative_path)
            if charset_name not in self.charsets:
                charset = CharacterSet(charset_name)
                self.charsets[charset_name] = charset
            self.parseFontSetsFromFolderStructure(charset, font)
        charsets_list = list(self.charsets.keys())
        if charsets_list != []:
            logger.info("CHARSET GROUPS ARE: %s" %' '.join(charsets_list))
        else:
            logger.error("CANT PARSE CHARSET FOLDERS STRUCTURE!")

    def parseFontSetsFromFolderStructure(self, charset, font):
        """
        Groups charsets into fontsets. This is done by finding their lowest parent dir
        name. Font sets are usually interpolatable set of fonts (e.g. Roman, Italic)
        """
        fontset_raw_name = font.path.split("/")[-2]
        fontset_name = remove_sort_digits(fontset_raw_name)
        fontset = FontSet(name=fontset_name, characterSet=charset)
        self.fontsets[fontset_name] = fontset
        fontset.addFont(font)

    def getFamily(self):
        return Family(self.charsets)

