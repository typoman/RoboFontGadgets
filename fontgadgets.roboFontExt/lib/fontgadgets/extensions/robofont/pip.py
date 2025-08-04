import os
import sys
import subprocess
import AppKit
import pip

def getRoboFontExternalPackagesFolder():
    app_support_path = AppKit.NSSearchPathForDirectoriesInDomains(
        AppKit.NSApplicationSupportDirectory,
        AppKit.NSUserDomainMask, True)[0]
    version = f'{sys.version_info.major}.{sys.version_info.minor}'
    return os.path.join(app_support_path, f'RoboFont/Python{version}')

def installPIPPackage(package_name):
    target_path = getRoboFontExternalPackagesFolder()
    if not os.path.exists(target_path):
        os.makedirs(target_path)
    pip_args = [
        'install',
        '--upgrade',
        '--target', target_path,
        package_name
    ]
    return_code = pip.main(pip_args)
    if return_code == 0:
        return target_path
