import pytest
from main import *
import fontgadgets.extensions.anchors.propogate

@pytest.fixture(scope="module", autouse=True)
def anchors_dict_font_test():
    ufo_path = Path(__file__).parent.joinpath("data/anchors-propogate-test.ufo")
    font = defcon.Font(ufo_path)
    yield font

