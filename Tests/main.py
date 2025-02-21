from unittest.mock import MagicMock
from pathlib import Path
from fontgadgets.tools import FontGadgetsError
from fontTools.ttLib import TTFont
import defcon
import fontParts.fontshell
import pytest
import random
import operator
import tempfile
import shutil

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


def sample_random_glyph(seed: int) -> defcon.Glyph:
    """
    Generate a sample glyph object with random contents.

    Args:
    seed (int): The seed value for the random number generator.

    Returns:
    defcon.Glyph: A sample glyph object with random contents.
    """
    random.seed(seed)
    layer = defcon.Layer()
    source = layer.instantiateGlyphObject()
    source.name = f"random_glyph_{seed}"
    source.width = random.randint(1, 100)
    source.height = random.randint(1, 100)
    source.unicodes = [random.randint(1, 100) for _ in range(random.randint(1, 5))]
    source.note = f"random note {seed}"
    source.image = dict(
        fileName=f"random_image_{seed}",
        xScale=random.uniform(0.5, 2.0),
        xyScale=random.uniform(-1.0, 1.0),
        yxScale=random.uniform(-1.0, 1.0),
        yScale=random.uniform(0.5, 2.0),
        xOffset=random.randint(-100, 100),
        yOffset=random.randint(-100, 100),
        color=','.join(f"{random.random():.1f}" for _ in range(4))
    )
    source.anchors = [{"x": random.randint(-100, 100), "y": random.randint(-100, 100), "name": f"anchor {i}"} for i in range(random.randint(1, 5))]
    for i in range(random.randint(1, 5)):
        guideline = defcon.Guideline()
        guideline.x = random.randint(-100, 100)
        guideline.name = f"guideline {i}"
        source.appendGuideline(guideline)
    source.lib = {f"key {i}": f"value {i}" for i in range(random.randint(1, 5))}
    pen = source.getPointPen()
    segment_types = ["line", "curve"]
    pen.beginPath()
    for _ in range(random.randint(2, 10)):
        segment_type = random.choice(segment_types)
        pen.addPoint((random.randint(-100, 100), random.randint(-100, 100)), segmentType=segment_type)
    pen.endPath()
    for _ in range(random.randint(1, 5)):
        component = defcon.Component()
        component.baseGlyph = f"base {random.randint(1, 100)}"
        component.transformation = (random.uniform(-1, 1), random.uniform(-1, 1), random.uniform(-1, 1), random.uniform(-1, 1), random.randint(-100, 100), random.randint(-100, 100))
        source.appendComponent(component)
    return source

def _contour_points_as_list(glyph):
    result = []
    for contour in glyph:
        result.append([])
        for point in contour:
            result[-1].append((point.x, point.x,
                point.segmentType, point.name))
    return result

def _comps_as_tuples(glyph):
    result = []
    for comp in glyph.components:
        result.append((comp.baseGlyph, comp.transformation))
    return result

def _get_operator(condition):
    # Returns the equality operator (==) if condition is True, and the
    # inequality operator (!=) if condition is False. This allows for dynamic
    # switching between equality and inequality checks.
    _operator = operator.eq if condition else operator.ne
    return _operator

def assert_compared_glyphs_are_same(ref_glyph, other_glyph,
    width=False, height=False, unicodes=False, note=False, image=False,
    contours=False, components=False, anchors=False, guidelines=False,
    lib=False):
    # Assert that the attributes of ref_glyph are not changed
    # from other_glyph, except for the specified attributes.
    assert _get_operator(width)(ref_glyph.width, other_glyph.width), f"Inconsistent width for the argument {width}: {ref_glyph.width} != {other_glyph.width}"
    assert _get_operator(height)(ref_glyph.height, other_glyph.height), f"Inconsistent height for the argument {height}: {ref_glyph.height} != {other_glyph.height}"
    assert _get_operator(unicodes)(ref_glyph.unicodes, other_glyph.unicodes), f"Inconsistent unicodes for the argument {unicodes}: {ref_glyph.unicodes} != {other_glyph.unicodes}"
    assert _get_operator(note)(ref_glyph.note, other_glyph.note), f"Inconsistent note for the argument {note}: {ref_glyph.note} != {other_glyph.note}"
    assert _get_operator(image)(ref_glyph.image, other_glyph.image), f"Inconsistent image for the argument {image}: {ref_glyph.image} != {other_glyph.image}"
    sourceContours = _contour_points_as_list(other_glyph)
    targetContours = _contour_points_as_list(ref_glyph)
    assert _get_operator(contours)(sourceContours, targetContours), f"Inconsistent contours for the argument {contours}: {sourceContours} != {targetContours}"
    assert _get_operator(components)(_comps_as_tuples(ref_glyph), _comps_as_tuples(other_glyph)), f"Inconsistent components for the argument {components}: {_comps_as_tuples(ref_glyph)} != {_comps_as_tuples(other_glyph)}"
    assert _get_operator(anchors)([g.items() for g in ref_glyph.anchors], [g.items() for g in other_glyph.anchors]), f"Inconsistent anchors for the argument {anchors}: {[g.items() for g in ref_glyph.anchors]} != {[g.items() for g in other_glyph.anchors]}"
    assert _get_operator(guidelines)([g.items() for g in ref_glyph.guidelines], [g.items() for g in other_glyph.guidelines]), f"Inconsistent guidelines for the argument {guidelines}: {[g.items() for g in ref_glyph.guidelines]} != {[g.items() for g in other_glyph.guidelines]}"
    assert _get_operator(lib)(ref_glyph.lib, other_glyph.lib), f"Inconsistent lib for the argument {lib}: {ref_glyph.lib} != {other_glyph.lib}"

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

def fontIsSameAsTTXForGivenTables(font, ttx, tables=None):
    if tables is None:
        tables = set(font.keys())
    else:
        tables = set(tables)
        if not set(font.keys()).issuperset(tables):
            raise ValueError(f"Not all the tables are in the font: {tables}")

    tables.discard("GlyphOrder")
    arg_tables = list(sorted(tables))

    with tempfile.NamedTemporaryFile(mode='wb', suffix='.ttx', delete=False) as tmp:
        try:
            actual_ttx_path = Path(tmp.name)
            font.saveXML(tmp.name, tables=arg_tables)

            with open(actual_ttx_path, "r", encoding="utf-8") as actual_file:
                actual_lines = [line.rstrip() + "\n" for line in actual_file.readlines()]

            ttx_path = Path(__file__).parent.joinpath("data/ttx/" + ttx)
            with open(ttx_path, "r", encoding="utf-8") as expected_file:
                expected_lines = [line.rstrip() + "\n" for line in expected_file.readlines()]

            differences = []
            for line_num, (actual_line, expected_line) in enumerate(zip(actual_lines, expected_lines)):
                if actual_line != expected_line:
                    differences.append(
                        f"Line {line_num + 1}:\n"
                        f"Expected: {expected_line.strip()}\n"
                        f"Actual:   {actual_line.strip()}\n"
                    )
            if differences:
                error_message = "TTX output differs from expected:\n\n" + "\n".join(differences)
                save_path = ttx_path.parent / f"expected_{ttx}"
                shutil.copy(actual_ttx_path, save_path)
                raise AssertionError(error_message)
            return True

        except Exception as e:
            raise AssertionError(f"Error during TTX comparison: {str(e)}")
        finally:
            actual_ttx_path.unlink(missing_ok=True)

    return False


