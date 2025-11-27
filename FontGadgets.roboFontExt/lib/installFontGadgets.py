import importlib
from RFGadgets.pip import pipManager, PIP_PACKAGES
from mojo.extensions import setExtensionDefault, getExtensionDefault
import sys
import os
import logging
from RFGadgets.observers.startup import startActivatedObservers
from RFGadgets import UI
"""
This is the start up script for robofont.
"""

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
if (logger.hasHandlers()):
    logger.handlers.clear()
handler = logging.StreamHandler()
logger.addHandler(handler)

logs = startActivatedObservers()
logger.debug("\n".join(logs))

root = os.path.dirname(__file__)
if root not in sys.path:
    sys.path.append(root)

not_found_pip_packages = {}
for import_name, package_spec in PIP_PACKAGES.items():
    dist_name = import_name
    if 'git+' in package_spec:
        dist_name = 'fontgadgets'

    if not pipManager._is_package_installed(dist_name):
         logger.warning(f"Package '{package_spec}' (as '{import_name}') will be installed.")
         not_found_pip_packages[import_name] = package_spec
    else:
        logger.debug(f"Package '{package_spec}' (as '{import_name}') is already installed.")

if not_found_pip_packages:
    installed_packages = getExtensionDefault(
        "design.bahman.fontgadgets.installedByPIP", fallback=[]
    )
    for import_name, package_spec in not_found_pip_packages.items():
        logger.warning(
            f"Attempting installation of package '{package_spec}' ..."
        )
        if pipManager.install_package(package_spec, install_dependencies=False):
            # if installation is successful, add it to the list and save immediately
            if package_spec not in installed_packages:
                installed_packages.append(package_spec)
                setExtensionDefault(
                    "design.bahman.fontgadgets.installedByPIP", installed_packages
                )
        else:
            logger.error(f"Installation of '{package_spec}' failed.")

try:
    import fontgadgets
    importlib.reload(fontgadgets)
except ImportError as e:
    logger.error(f"Failed to import a required module: {e}")
