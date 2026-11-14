"""Makes a clean starter kit: the buddy with none of your personal things in it.

    hermes/tools/python-*/bin/python3 -I tools/make_starter_kit.py

It writes henry-starter-kit-<date>.zip next to this folder. That zip is for learners or
customers. What goes in: the app, the body code, the stand-in body "Buddy", the desktop
overlay code, the set-up and start scripts, and the files in starter/ (generic personality,
default settings, guides, credits).
What stays out: your 3D likeness, your voice, your memory and chats, Hermes itself, every
key and token, and your settings.
Before finishing, it checks every file for your keys, your memories, your home folder and
your user name, and for files that should never be in it. If anything turns up, no zip is made.
"""

import datetime
import getpass
import os
import re
import stat
import sys
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
HERMES = Path(os.environ.get("HERMES_HOME") or ROOT / "hermes")
KIT = "henry-starter-kit"

# from your project, as they are
FROM_PROJECT = [
    "app/launch.py", "app/server.py", "app/web",
    "rig/henry.js", "rig/demo.html", "rig/view.html", "rig/README.md", "rig/buddy.glb",
    "rig/tools", "rig/vendor",
    "overlay",
    "tools/set_key.py", "tools/set_hf_token.py", "tools/pack_up.py", "tools/restore.py",
    "start.command", "start.sh", "start.bat", "start-overlay.command", "start-overlay.bat",
    "setup.sh", "setup.ps1", "setup.bat",
]
# everything in starter/ goes in at the same place (starter/app/settings.json -> app/settings.json)
STARTER = ROOT / "starter"
EMPTY_DIRS = ["voice/bin/"]

SKIP_NAMES = {".env", "auth.json", "__pycache__", ".DS_Store", "node_modules", "hf-cache"}
SKIP_SUFFIXES = (".pyc", ".lock", ".tmp", ".log")
NEVER = re.compile(r"\.(env|db|sqlite|wav|m4a|mp3|safetensors|pem|key)$|(^|/)(auth|token)(\.json)?$", re.I)
ALLOWED_GLB = {"rig/buddy.glb"}
EXECUTABLE = (".command", ".sh")


def files_under(path):
    if path.is_file():
        yield path
        return
    for dirpath, dirnames, filenames in os.walk(path):
        dirnames[:] = sorted(d for d in dirnames if d not in SKIP_NAMES)
        for f in sorted(filenames):
            if f not in SKIP_NAMES and not f.endswith(SKIP_SUFFIXES):
                yield Path(dirpath) / f


def personal_needles():
    """Things of yours that must not appear anywhere in the kit. Never printed."""
    found = set()

    def add(v):
        v = v.strip().strip('"').strip("'")
        if len(v) >= 8:
            found.add(v.encode())

    try:
        add((ROOT / "voice" / "hf-cache" / "token").read_text(encoding="utf-8"))
    except OSError:
        pass
    for env in (HERMES / ".env", ROOT / ".env"):
        try:
            for line in env.read_text(encoding="utf-8").splitlines():
                k, sep, v = line.partition("=")
                if sep and not k.strip().startswith("#") and len(v.strip()) >= 12:
                    add(v)
        except OSError:
            pass
    try:   # every long string inside the sign-in file (tokens, account ids, emails)
        for v in re.findall(r'"([^"\\]{16,})"', (HERMES / "auth.json").read_text(encoding="utf-8")):
            if not v.startswith(("http://", "https://")):   # public web addresses are not personal
                add(v)
    except OSError:
        pass
    for mem in ("USER.md", "MEMORY.md"):   # each thing Henry remembers about you
        try:
            for part in re.split(r"\n|§", (HERMES / "memories" / mem).read_text(encoding="utf-8")):
                if len(part.strip()) >= 12:
                    add(part)
        except OSError:
            pass
    home = str(Path.home())
    add(home)
    add(home.replace("\\", "/"))
    try:
        user = getpass.getuser()
        if len(user) >= 6:
            add(user)
    except Exception:
        pass
    return found


def main():
    if not (ROOT / "rig" / "buddy.glb").is_file():
        print("rig/buddy.glb is missing. Make it first:  python3 rig/tools/make_buddy.py rig/buddy.glb")
        return 1
    items = []   # (path inside the kit, file on disk)
    for item in FROM_PROJECT:
        p = ROOT / item
        if not p.exists():
            print("Missing, so left out:", item)
            continue
        for f in files_under(p):
            items.append((f.relative_to(ROOT).as_posix(), f))
    for f in files_under(STARTER):
        items.append((f.relative_to(STARTER).as_posix(), f))
    kit = {}
    for rel, f in items:          # starter/ files replace project files of the same name
        kit[rel] = f

    needles = personal_needles()
    problems = []
    for rel, f in sorted(kit.items()):
        if NEVER.search(rel) or (rel.endswith(".glb") and rel not in ALLOWED_GLB):
            problems.append(rel + "  (this kind of file never goes in a starter kit)")
            continue
        data = f.read_bytes()
        if any(n in data for n in needles):
            problems.append(rel + "  (holds one of your keys, memories, or your user name / home folder)")
    if problems:
        print("Stopped: no kit was made, because of these files:")
        for p in problems:
            print("   ", p)
        return 1

    stamp = datetime.date.today().isoformat()
    out = ROOT.parent / ("%s-%s.zip" % (KIT, stamp))
    with zipfile.ZipFile(out, "w", zipfile.ZIP_DEFLATED, compresslevel=6) as z:
        for rel, f in sorted(kit.items()):
            info = zipfile.ZipInfo("%s/%s" % (KIT, rel), date_time=(2026, 1, 1, 0, 0, 0))
            info.compress_type = zipfile.ZIP_DEFLATED
            mode = 0o755 if rel.endswith(EXECUTABLE) else 0o644
            info.external_attr = (stat.S_IFREG | mode) << 16
            z.writestr(info, f.read_bytes())
        for d in EMPTY_DIRS:
            info = zipfile.ZipInfo("%s/%s" % (KIT, d), date_time=(2026, 1, 1, 0, 0, 0))
            info.external_attr = (stat.S_IFDIR | 0o755) << 16
            z.writestr(info, b"")
    print("Made %s: %d files, %.1f MB." % (out, len(kit), out.stat().st_size / 1e6))
    print("Checked: none of your keys, memories, voice, face or user name are inside.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
