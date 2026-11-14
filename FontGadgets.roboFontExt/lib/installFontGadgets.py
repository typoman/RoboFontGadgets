import importlib
from RFGadgets.pip import pipManager, PIP_PACKAGES
from mojo.extensions import setExtensionDefault, getExtensionDefault
import sys
import os
import logging
from RFGadgets.observers.startup import startActivatedObservers
from RFGadgets import UI
from mojo.UI import dontShowAgainYesOrNo
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

# Offer to update fontgadgets when remote master declares a different
# version than the one installed in RoboFont's packages folder.
FONTGADGETS_SETUP_PY_URL = "https://raw.githubusercontent.com/typoman/fontgadgets/master/setup.py"
DECLINED_UPDATE_VERSION_KEY = "design.bahman.fontgadgets.declinedUpdateVersion"

installed_fontgadgets_version = pipManager.get_installed_version("fontgadgets")
remote_fontgadgets_version = pipManager.get_repo_version(FONTGADGETS_SETUP_PY_URL)
declined_update_version = getExtensionDefault(DECLINED_UPDATE_VERSION_KEY, fallback=None)

if (installed_fontgadgets_version is not None
        and remote_fontgadgets_version is not None
        and remote_fontgadgets_version != installed_fontgadgets_version
        and remote_fontgadgets_version != declined_update_version):
    logger.warning(
        f"fontgadgets {remote_fontgadgets_version} is available, "
        f"{installed_fontgadgets_version} is installed."
    )

    def updateFontGadgetsCallback(result):
        # result is the index of the pressed button:
        # 0 Yes, 1 No, 2 Don't show this message again
        if result == 0:
            logger.warning(
                f"Updating fontgadgets {installed_fontgadgets_version} "
                f"-> {remote_fontgadgets_version} ..."
            )
            if pipManager.install_package(
                    PIP_PACKAGES["fontgadgets"], install_dependencies=False):
                logger.warning(
                    f"fontgadgets updated to {remote_fontgadgets_version}. "
                    "Restart RoboFont to load the new version.")
            else:
                logger.error("fontgadgets update failed.")
        elif result == 2:
            setExtensionDefault(
                DECLINED_UPDATE_VERSION_KEY, remote_fontgadgets_version)

    dontShowAgainYesOrNo(
        f"Update FontGadgets to {remote_fontgadgets_version}?",
        f"Version {remote_fontgadgets_version} is available in the fontgadgets "
        f"repository, version {installed_fontgadgets_version} is installed.",
        resultCallback=updateFontGadgetsCallback,
        dontShowAgainKey="design.bahman.fontgadgets.skipFontGadgetsUpdatePrompt",
    )
elif remote_fontgadgets_version == declined_update_version != installed_fontgadgets_version:
    logger.debug(
        f"Update to fontgadgets {remote_fontgadgets_version} was declined "
        "earlier, not asking again."
    )


try:
    import fontgadgets
    importlib.reload(fontgadgets)
except ImportError as e:
    logger.error(f"Failed to import a required module: {e}")
