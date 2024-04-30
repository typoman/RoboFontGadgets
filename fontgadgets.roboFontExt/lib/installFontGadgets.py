import sys
import os
"""
This is the start up script for robofont.
"""

root = os.path.dirname(__file__)
sys.path.append(root)

import fontgadgets
try:
    # in py2
    reload
except NameError:
    # in py3
    from importlib import reload

reload(fontgadgets)