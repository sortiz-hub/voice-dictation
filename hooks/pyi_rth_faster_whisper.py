"""Runtime hook: ensure faster_whisper.utils.get_assets_path() works in frozen builds."""

import os
import sys


def _patch_assets_path():
    if not getattr(sys, "frozen", False):
        return

    import faster_whisper.utils as utils

    meipass = sys._MEIPASS
    assets = os.path.join(meipass, "faster_whisper", "assets")
    if os.path.isdir(assets):
        utils.get_assets_path = lambda: assets


_patch_assets_path()
