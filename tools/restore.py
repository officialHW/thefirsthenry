"""Copies Henry's packed memory, skills and settings (hermes-data/) into the fresh Hermes folder.
Run by setup.sh / setup.ps1 after Hermes is installed."""

import os
import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SRC = ROOT / "hermes-data"
DST = Path(os.environ.get("HERMES_HOME") or ROOT / "hermes")


def main():
    if not SRC.is_dir():
        print("No hermes-data folder: nothing to restore.")
        return 0
    DST.mkdir(parents=True, exist_ok=True)
    for item in SRC.iterdir():
        target = DST / item.name
        if item.is_dir():
            shutil.copytree(item, target, dirs_exist_ok=True)
        else:
            shutil.copy2(item, target)
    print("Restored:", ", ".join(sorted(p.name for p in SRC.iterdir())))
    return 0


if __name__ == "__main__":
    sys.exit(main())
