import os
import sys
import AppKit
import subprocess
from importlib import metadata

PIP_PACKAGES = {
    "git": "GitPython",
    "gitdb": "gitdb>=4.0.1,<5",
    "fontGit": "fontGit",
    "bidi": "python-bidi==0.4.2",
    "uharfbuzz": "uharfbuzz==0.45.0",
    "fontgadgets": "git+https://github.com/typoman/fontgadgets.git",
}


class PIPManager:

    def __init__(self):
        self.target_path = self._get_robo_font_external_packages_folder()
        self._ensure_target_path_exists()

    def _get_robo_font_external_packages_folder(self):
        app_support_path = AppKit.NSSearchPathForDirectoriesInDomains(
            AppKit.NSApplicationSupportDirectory, AppKit.NSUserDomainMask, True
        )[0]
        version = f"{sys.version_info.major}.{sys.version_info.minor}"
        return os.path.join(app_support_path, f"RoboFont/Python{version}")

    def _ensure_target_path_exists(self):
        if not os.path.exists(self.target_path):
            os.makedirs(self.target_path)

    def _run_pip_command(self, pip_args):
        command = [sys.executable, "-m", "pip"] + pip_args
        try:
            result = subprocess.run(command, check=True, capture_output=True, text=True)
            print(result.stdout)
            return result.returncode
        except subprocess.CalledProcessError as e:
            print(f"Error executing pip command: {e}")
            print(e.stderr)
            return e.returncode

    def install_package(self, package_name, install_dependencies=True):
        pip_args = ["install", "--upgrade", "--target", self.target_path]
        if not install_dependencies:
            pip_args.append("--no-deps")
        pip_args.append(package_name)
        return_code = self._run_pip_command(pip_args)
        if return_code == 0:
            return self.target_path
        return None

    def _get_dist_name_from_spec(self, package_spec):
        if package_spec.startswith("git+"):
            # 'git+https:.../repo.git'
            basename = os.path.basename(package_spec)
            dist_name, _ = os.path.splitext(basename)
            return dist_name
        else:
            # 'package==version' or 'package>=version'
            for separator in ["==", ">=", "<=", ">", "<", "~="]:
                if separator in package_spec:
                    return package_spec.split(separator)[0]
            return package_spec

    def uninstall_package(self, package_spec):
        dist_name = self._get_dist_name_from_spec(package_spec)

        if not self._is_package_installed(dist_name):
            print(
                f"Package '{dist_name}' not found in '{self.target_path}'. Already uninstalled."
            )
            return True
        pip_args = ["uninstall", "--yes", dist_name]
        original_sys_path = sys.path[:]
        if self.target_path not in sys.path:
            sys.path.insert(0, self.target_path)

        return_code = self._run_pip_command(pip_args)

        sys.path[:] = original_sys_path
        return return_code == 0

    def _is_package_installed(self, package_name):
        original_sys_path = sys.path[:]
        if self.target_path not in sys.path:
            sys.path.insert(0, self.target_path)

        found = False
        try:
            metadata.distribution(package_name)
            found = True
        except metadata.PackageNotFoundError:
            found = False
        finally:
            sys.path[:] = original_sys_path

        return found


pipManager = PIPManager()
