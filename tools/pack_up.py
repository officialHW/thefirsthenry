"""Packs Henry into one zip file to move him to another computer. See MOVING.md.

What goes in: the app, the 3D body, the scripts, and Hermes' personality, settings, memory,
skills, scheduled jobs and chat history (copied into hermes-data/ inside the zip).
What stays out: every secret (.env, auth files, tokens), Hermes' program files (the new
computer downloads a fresh copy), caches and logs.
Before finishing, it checks that none of your secret values ended up in the zip.
"""

import datetime
import os
import sqlite3
import sys
import tempfile
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
HERMES = Path(os.environ.get("HERMES_HOME") or ROOT / "hermes")
NAME = ROOT.name

PROJECT_ITEMS = ["app", "rig", "tools", "overlay", "MOVING.md", "README.md", "start.command", "start.sh",
                 "start.bat", "start-overlay.command", "start-overlay.bat", "voice", "setup.sh", "setup.ps1", "setup.bat",
                 "starter", "extras", "START-HERE.md", "NOTICE.md"]
HERMES_ITEMS = ["config.yaml", "SOUL.md", "memories", "skills", "sessions", "cron", "hooks",
                "plugins", "state.db"]
SKIP_NAMES = {".env", "auth.json", "honcho.json", "mem0.json", "__pycache__", ".DS_Store",
              "mcp-tokens", ".ssh", ".aws", "pairing",
              "node_modules", "hf-cache", "pocket-tts", "pocket-tts.exe"}   # Electron is downloaded again on the new computer
SKIP_SUFFIXES = (".pyc", ".lock", ".tmp", "-wal", "-shm", ".log")


def secret_values():
    vals = set()
    tok = ROOT / "voice" / "hf-cache" / "token"
    try:
        v = tok.read_text(encoding="utf-8").strip()
        if len(v) >= 12:
            vals.add(v.encode())
    except OSError:
        pass
    for env in (HERMES / ".env", ROOT / ".env"):
        try:
            for line in env.read_text(encoding="utf-8").splitlines():
                k, sep, v = line.partition("=")
                v = v.strip().strip('"').strip("'")
                if sep and len(v) >= 12 and not k.strip().startswith("#"):
                    vals.add(v.encode())
        except OSError:
            pass
    return vals


def files_under(path):
    if path.is_file():
        yield path
        return
    for dirpath, dirnames, filenames in os.walk(path):
        dirnames[:] = [d for d in dirnames if d not in SKIP_NAMES]
        for f in filenames:
            if f not in SKIP_NAMES and not f.endswith(SKIP_SUFFIXES):
                yield Path(dirpath) / f


def main():
    stamp = datetime.date.today().isoformat()
    out = ROOT.parent / ("%s-pack-%s.zip" % (NAME, stamp))
    secrets = secret_values()
    added, problems = 0, []

    def check(data, label):
        if any(s in data for s in secrets):
            problems.append(label)

    with tempfile.TemporaryDirectory() as tmp, \
            zipfile.ZipFile(out, "w", zipfile.ZIP_DEFLATED, compresslevel=6) as z:
        for item in PROJECT_ITEMS:
            p = ROOT / item
            if not p.exists():
                continue
            for f in files_under(p):
                data = f.read_bytes()
                check(data, str(f.relative_to(ROOT)))
                z.writestr(str(Path(NAME) / f.relative_to(ROOT)), data)
                added += 1
        for item in HERMES_ITEMS:
            p = HERMES / item
            if not p.exists():
                continue
            if p.suffix == ".db":
                # safe copy of the chat history even while Hermes is running
                copy = Path(tmp) / p.name
                with sqlite3.connect(p) as src, sqlite3.connect(copy) as dst:
                    src.backup(dst)
                p_files = [(copy, Path(item))]
            else:
                p_files = [(f, f.relative_to(HERMES)) for f in files_under(p)]
            for f, rel in p_files:
                data = f.read_bytes()
                check(data, "hermes/" + str(rel))
                z.writestr(str(Path(NAME) / "hermes-data" / rel), data)
                added += 1

    if problems:
        out.unlink(missing_ok=True)
        print("Stopped: a secret value was found inside these files, so no zip was made:")
        for p in problems:
            print("   ", p)
        print("Remove the key from those files (or ask Henry to forget it), then try again.")
        return 1
    size = out.stat().st_size / 1e6
    print("Packed %d files into %s (%.0f MB)." % (added, out, size))
    print("No secrets inside. Your Gemini key is NOT in it: see MOVING.md for how to carry it.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
