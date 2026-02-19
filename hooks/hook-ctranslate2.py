"""PyInstaller hook for ctranslate2 — collect DLLs and .pyd files."""

import os
from PyInstaller.utils.hooks import get_package_paths

_, pkg_path = get_package_paths("ctranslate2")

binaries = []
for f in os.listdir(pkg_path):
    if f.endswith((".dll", ".pyd")):
        binaries.append((os.path.join(pkg_path, f), "ctranslate2"))
