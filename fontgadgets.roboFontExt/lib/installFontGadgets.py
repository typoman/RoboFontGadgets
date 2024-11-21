import sys
import os
"""
This is the start up script for robofont.
"""

root = os.path.dirname(__file__)
if root not in sys.path:
    sys.path.append(root)

import fontgadgets
try:
    # in py2
    reload
except NameError:
    # in py3
    from importlib import reload

reload(fontgadgets)

import fontgadgets.extensions.robofont.font
import fontgadgets.extensions.robofont.tools
import fontgadgets.extensions.robofont.UI

