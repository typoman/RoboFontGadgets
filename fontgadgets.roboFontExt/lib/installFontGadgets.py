import sys
import os
import logging
logger = logging.getLogger(__name__)

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

pip_packages = {
    "bidi": "python-bidi==0.4.2",
    "git": "GitPython"
}

from fontgadgets.extensions.robofont.pip import installPIPPackage

for import_name, package_spec in pip_packages.items():
    try:
        __import__(import_name)
        logger.debug(f"Package '{package_spec}' (as '{import_name}') is already installed.")
    except ImportError:
        logger.warning(f"Package '{package_spec}' (as '{import_name}') not found. Attempting installation...")
        if not installPIPPackage(package_spec):
            logger.error(f"Installation of '{package_spec}' failed.")

import fontgadgets.extensions.robofont.font
import fontgadgets.extensions.robofont.tools
import fontgadgets.extensions.robofont.UI

