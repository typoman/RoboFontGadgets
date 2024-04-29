import os
import glob
import re
from pathlib import Path
from fontgadgets.log import logger
import pytest

def replaceWords(text, dictionary):
    # Add the re.IGNORECASE flag for case-insensitive matching
    regex = re.compile('|'.join(map(re.escape, dictionary)), re.IGNORECASE)

    def replacement(match):
        # Preserve the original case by using match.group(0) in the dictionary lookup
        return dictionary.get(match.group(0).lower(), match.group(0))

    return regex.sub(replacement, text)

def dirAsString(root_path, show_hidden=False, skip_patterns=None, file_suffixes=None, replace_map=None):
    """
    Convert the contents of a directory into a string, to be used for creating
    samples for tests.

    This function uses glob to recursively fetch all directories and files in
    the given root path, excluding certain patterns and hidden files if
    specified. It then converts the relative paths of these directories and
    files into a string, which is returned.

    Parameters:
    root_path (str): The root directory path to start the search from.
    show_hidden (bool, optional): If True, include hidden files in the result. Default is False.
    skip_patterns (list, optional): A list of string patterns to skip if it was inside the path. Default is None.
    file_suffixes (list, optional): A list of suffixes to consider for files. Default is None.
    replace_map (dict, optional): A dictionary to replace certain parts of the path. Default is None.

    Returns:
    str: A string containing the relative paths of all directories and files in the given root path,
         separated by newline characters.

    Example:
    dirAsString('git/private/test/UFO', skip_patterns=[".ufo/"], file_suffixes=['.fea', '.designspace'])
    """
    paths = []
    if replace_map is None:
        replace_map = {}
    if skip_patterns is None:
        skip_patterns = []
    for path in glob.glob(os.path.join(root_path, '**'), recursive=True):
        if any(pattern in path for pattern in skip_patterns):
            continue
        if not show_hidden and os.path.basename(path).startswith('.'):
            continue
        rel_path = os.path.relpath(path, root_path)
        if os.path.isdir(path):
            rel_path = rel_path + '/'
        elif file_suffixes is not None and not any(suffix in rel_path for suffix in file_suffixes):
            continue
        if rel_path.startswith('.'):
            continue
        rel_path = replaceWords(rel_path, replace_map)
        paths.append(rel_path)
    return "\n".join(paths)


def mockDirectoriesAndFiles(root_folder, sample_string):
    """
    To be used along with dirAsString to create sample directories and files for testing.
    """
    lines = sample_string.strip().split("\n")
    try:
        for line in lines:
            line = line.strip()
            path = Path(line)
            path = Path(root_folder) / path
            logger.debug(f"Creating file/folder `{path}`")  # Add this line
            if line.endswith("/"):
                is_dir = True
            else:
                is_dir = False
            if not path.exists():
                if is_dir:
                    path.mkdir(parents=True, exist_ok=True)
                else:
                    path.touch()
            else:
                logger.debug(f"File/Folder `{path}` already exists")
        return Path(root_folder)
    except Exception as e:
        logger.error(e)

@pytest.fixture
def sample_dir_structures():
    samples = {}
    samples["TEST_1"] = """
    HE/
    HE/Italic/
    HE/Italic/TEST_1-Display-Hebrew-Thin-Italic.ufo/
    HE/Italic/TEST_1-Display-Hebrew-Black-Italic.ufo/
    HE/Italic/TEST_1-Italic Hebrew.designspace
    HE/gsub-he.fea
    HE/Roman/
    HE/Roman/TEST_1-Hebrew.designspace
    HE/Roman/TEST_1-Display-Hebrew-Black.ufo/
    HE/Roman/TEST_1-Display-Hebrew-Thin.ufo/
    AR/
    AR/gsub-ar.fea
    AR/Roman/
    AR/Roman/TEST_1-Arabic-Black.ufo/
    AR/Roman/TEST_1-Arabic.designspace
    AR/Roman/TEST_1-Arabic-Thin.ufo/
    LA/
    LA/gsub-roman-lc.fea
    LA/Italic/
    LA/Italic/TEST_1-Display-Thin-Italic.ufo/
    LA/Italic/TEST_1-Display-Black-Italic.ufo/
    LA/gsub-italic-lc.fea
    LA/Roman/
    LA/Roman/TEST_1-Display-Black.ufo/
    LA/Roman/TEST_1-Display-Thin.ufo/
    """
    return samples

if __name__ == "__main__":
    import argparse

    def parse_arguments():
        parser = argparse.ArgumentParser(description='Convert the contents of a directory into a string.')
        parser.add_argument('root_path', type=str, help='The root directory path to start the search from.')
        parser.add_argument('-H', '--show_hidden', action='store_true', help='Include hidden files in the result.')
        parser.add_argument('-s', '--skip_patterns', nargs='+', help='A list of string patterns to skip if it was inside the path.'
                                                                     'Example: --skip_patterns ".ufo" ".git"')
        parser.add_argument('-f', '--file_suffixes', nargs='+', help='A list of suffixes to consider for files. '
                                                                     'Example: --file_suffixes ".fea" ".designspace"')
        parser.add_argument('-r', '--replace_map', nargs='+', metavar=('KEY', 'VALUE'), help='A dictionary to replace certain parts of the path. '
                                                                                             'Example: --replace_map old_name new_name')
        parser.add_argument('-e', '--example', action='store_true', help='Show an example command and exit.')
        args = parser.parse_args()
        if args.example:
            print("Example command:")
            print("python your_script.py /path/to/directory --show_hidden --skip_patterns '.ufo' '.git' --file_suffixes '.fea' '.designspace' --replace_map old_name new_name")
            exit()
        return args

    args = parse_arguments()

    if args.replace_map:
        replace_map = dict(zip(args.replace_map[::2], args.replace_map[1::2]))
    else:
        replace_map = None

    print(dirAsString(args.root_path, args.show_hidden, args.skip_patterns, args.file_suffixes, replace_map))
