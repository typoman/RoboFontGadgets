from utils import *
import fontgadgets.extensions.layer

def test_font_background_property(defcon_font_1):
    font = defcon_font_1
    assert 'public.background' not in font.layers
    background_layer_1 = font.background
    assert 'public.background' in font.layers
    assert background_layer_1 is font.layers['public.background']
    background_layer_2 = font.background
    assert background_layer_2 is background_layer_1
    assert len(font.layers) == 2

def test_layer_dirPath_property(defcon_ar_font_1):
    font = defcon_ar_font_1
    layer = font.layers.defaultLayer
    dir_path = layer.dirPath
    font_path = defcon_ar_font_1.path
    expected_dir_path = str(Path(font_path) / "glyphs")
    assert dir_path == expected_dir_path, f"dirPath '{dir_path}' does not match expected path '{expected_dir_path}'."
