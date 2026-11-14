"""Saves your Hugging Face access key so Henry's voice tool (Pocket TTS) may use the
voice-copying model. Typing stays hidden and the key is never printed.

    python tools/set_hf_token.py

It is stored in voice/hf-cache/token, readable only by you, and is never put in the
pack-up zip.
"""

import getpass
import os
import stat
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
TOKEN = ROOT / "voice" / "hf-cache" / "token"


def main():
    key = getpass.getpass("Paste your Hugging Face access key (it stays hidden), then press Enter: ").strip()
    if not key:
        print("No key entered. Nothing changed.")
        return 1
    if not key.startswith("hf_"):
        print("That doesn't look like a Hugging Face key (they start with hf_). Nothing changed.")
        return 1
    TOKEN.parent.mkdir(parents=True, exist_ok=True)
    tmp = TOKEN.with_suffix(".tmp")
    tmp.write_text(key, encoding="utf-8")
    try:
        os.chmod(tmp, stat.S_IRUSR | stat.S_IWUSR)
    except OSError:
        pass
    os.replace(tmp, TOKEN)
    print("Done: the Hugging Face key is saved for Henry's voice.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
