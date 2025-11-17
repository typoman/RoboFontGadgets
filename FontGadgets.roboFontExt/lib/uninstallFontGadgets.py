from RFGadgets.pip import pipManager
from mojo.extensions import getExtensionDefault, setExtensionDefault
import logging

logger = logging.getLogger(__name__)
failed_packages = []
installed_packages = getExtensionDefault('design.bahman.fontgadgets.installedByPIP', fallback=[])
for package_spec in installed_packages:
    logger.warning(f"Attempting to uninstall '{package_spec}' ...")
    if not pipManager.uninstall_package(package_spec):
        logger.error(f"Uninstallation of '{package_spec}' failed.")
        failed_packages.append(package_spec)

setExtensionDefault('design.bahman.fontgadgets.installedByPIP', failed_packages)
