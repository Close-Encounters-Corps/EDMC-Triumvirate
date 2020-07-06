"""
Синхронизирует python-файлы проекта с каталогом плагина.
"""

import os
import sys
from pathlib import Path
import shutil

FILES = ["load.py", "settings.py", "settings_local.py"]

DEST = Path.home() / "AppData" / "Local" / "EDMarketConnector" / "plugins" / "EDMC-Triumvirate"

DEST.mkdir(parents=True, exist_ok=True)

def do_copy(src, dst):
    if "-q" not in sys.argv:
        print("Copying", src, "to", dst)
    shutil.copyfile(src, dst)

for folder, _, files in os.walk("modules"):
    dst_folder = DEST / folder
    dst_folder.mkdir(exist_ok=True)
    for item in files:
        src = Path(folder, item)
        if src.suffix != '.py':
            continue
        dst = dst_folder / item
        do_copy(src, dst)

for item in FILES:
    if not Path(item).exists:
        print(f"Warning: {item} does not exist, skipping")
        continue
    do_copy(item, DEST / item)
