import sys
import os

root = os.path.dirname(__file__)
sys.path.append(root)

import fontGadgets
from importlib import reload
reload(fontGadgets)
