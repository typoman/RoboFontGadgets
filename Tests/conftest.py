from fontTools.ttLib import TTFont
import shutil
from utils import *

@pytest.fixture
def defcon_font_1():
    groups = {
        "public.kern1.C": ("C", "Ccedilla"), # right side
        "public.kern1.O": ("D", "O", "Ograve"), # right side
        "public.kern1.sin.fina": ("seen", "sad"), # left side
        "public.kern2.H": ("D", "E"), # right side
        "public.kern2.O": ("C", "Ccedilla", "O", "Ograve"), # right side
        "public.kern2.sad.init": ("sad", "tah"), # right side
        "public.kern2.sin.init": ("seen", "seen.init"), # right side
        "control": ("seen",),
    }

    cmap = {
        67: "C",
        199: "Ccedilla",
        68: "D",
        69: "E",
        70: "F",
        46: "period",
        79: "O",
        210: "Ograve",
        1587: "seen",
        1589: "sad",
        1591: "tah",
        65203: "seen.init",
        65228: "ain.medi",
    }

    font = defcon.Font()
    font.groups.update(groups)
    for un, gn in cmap.items():
        font.newGlyph(gn).unicodes = [un]
    return font


@pytest.fixture
def fontParts_font_1(defcon_font_1):
    return fontParts.fontshell.RFont(defcon_font_1)


@pytest.fixture
def glyph_1():
    glyph = MagicMock()
    glyph.contours = [MagicMock() for _ in range(3)]
    glyph.anchors = [MagicMock() for _ in range(3)]
    glyph.guidelines = [MagicMock() for _ in range(3)]
    glyph.components = [
        MagicMock(transformation=(1, 0, 0, 1, 10, 13)) for _ in range(3)
    ]  # Mock transformation
    glyph.width = 100
    return glyph

@pytest.fixture(scope="module", autouse=True)
def defcon_ar_font_1():
    """
    arabic test font inc. features, unicodes, kerning, groups, components
    """
    ufo_path = Path(__file__).parent.joinpath("data/ar-font-test-1.ufo")
    font = defcon.Font(ufo_path)
    return font

class DefconFontMock:
    # This will not work with fontgadets decorators and only is used for
    # testing the collections module where a lot of ufo files are loaded.
    __slots__ = "path", "kerning", "groups", "glyphs", "fontSet"

    def __init__(self, path=None):
        self.path = path
        self.kerning = {}
        self.groups = {}
        self.glyphs = {}
        self.fontSet = None

    def keys(self):
        return list(self.glyphs.keys())

    def newGlyph(self, name):
        glyph = MagicMock()
        glyph.name = name
        self.glyphs[name] = glyph
        return glyph

    def clear(self):
        self.kerning.clear()
        self.groups.clear()
        self.glyphs.clear()

# Mock defcon.Font to make it light for testing
@pytest.fixture()
def mock_defcon_font_module():
    original_font = defcon.Font
    defcon.Font = DefconFontMock
    yield
    defcon.Font = original_font

@pytest.fixture(scope="function")
def kerning_with_missing_glyphs():
    f = defcon.Font()

    f.newGlyph('A')
    f.newGlyph('B')
    f.newGlyph('C')
    f.newGlyph('D')
    f.newGlyph('E')

    kerning = {
        ('A', 'B'): 50,
        ('C', 'D'): 30,
        ('E', 'missing_glyph'): 20,
        ('missing_glyph', 'A'): 10,
        ('B', 'B'): 40,
        ('E', 'empty_group'): 10,
        ('E', 'not_group_not_glyph'): 10,
        ('group_that_going_to_be_deleted', 'A'): 10,
        ('group_with_missing_glyph', 'A'): 15,
        ('group_that_going_to_be_deleted', 'empty_group'): 20,
        ('missing_glyph', 'group_with_missing_glyph'): 20,
    }
    f.kerning.update(kerning)

    groups = {
        'group1': ['A', 'B', 'C'],
        'group2': ['D', 'E'],
        'empty_group': [],
        'group_with_missing_glyph': ['A', 'missing_glyph'],
        'group_that_going_to_be_deleted': ['missing_glyph_2'],
    }
    f.groups.update(groups)
    return f


@pytest.fixture(scope='function')
def COPY_GLYPH_KWARGS():
    return dict(width=True, height=True, unicodes=True, note=True,
        image=True, contours=True, components=True, anchors=True,
        guidelines=True, lib=True)

@pytest.fixture(scope='function')
def sample_font_with_random_glyph_contents():
    f = defcon.Font()
    for i in range(10):
        g = sample_random_glyph(i+100)
        name = f'random glyph {i}'
        f.newGlyph(name).copyDataFromGlyph(g)
    yield f


from string import ascii_lowercase
from random import choice

def sample_random_font(path: Path, seed: int, num_glyphs=0):
    font = defcon.Font()
    for i in range(num_glyphs):
        SAMPLE_G_NAME = choice(ascii_lowercase)
        glyph = sample_random_glyph(seed)
        font.newGlyph(SAMPLE_G_NAME).copyDataFromGlyph(glyph)
        font.save(path)

