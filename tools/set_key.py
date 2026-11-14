"""Puts your Gemini API key into Hermes' private settings file without ever showing it.

    python tools/set_key.py                 asks you to paste the key (typing stays hidden)
    python tools/set_key.py --from FILE     copies the Gemini key line out of another .env file

It also makes sure Hermes' local API is switched on with its own random access key, so
Henry's body can talk to Hermes. Nothing is printed except "done" messages.
"""

import getpass
import os
import secrets
import stat
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
ENV = Path(os.environ.get("HERMES_HOME") or ROOT / "hermes") / ".env"
NAMES = ("GEMINI_API_KEY", "GOOGLE_API_KEY")


def read_env(path):
    vals = {}
    try:
        for line in path.read_text(encoding="utf-8").splitlines():
            k, sep, v = line.partition("=")
            k = k.strip().removeprefix("export ").strip()
            if sep and k and not k.startswith("#"):
                vals[k] = v.strip().strip('"').strip("'")
    except OSError:
        pass
    return vals


def write_env(path, updates):
    lines = []
    try:
        lines = path.read_text(encoding="utf-8").splitlines()
    except OSError:
        pass
    done = set()
    for i, line in enumerate(lines):
        k = line.partition("=")[0].strip()
        if k in updates:
            lines[i] = "%s=%s" % (k, updates[k])
            done.add(k)
    lines += ["%s=%s" % (k, v) for k, v in updates.items() if k not in done]
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(".tmp")
    tmp.write_text("\n".join(lines) + "\n", encoding="utf-8")
    try:
        os.chmod(tmp, stat.S_IRUSR | stat.S_IWUSR)   # only you can read it (Mac/Linux)
    except OSError:
        pass
    os.replace(tmp, path)


def main(argv):
    key = ""
    if argv == ["--link-only"]:   # only switch on Henry's link to Hermes, no Gemini key
        current = read_env(ENV)
        updates = {"API_SERVER_ENABLED": "true"}
        if not current.get("API_SERVER_KEY"):
            updates["API_SERVER_KEY"] = secrets.token_urlsafe(32)
        write_env(ENV, updates)
        print("Done: Henry's link to Hermes is on.")
        return 0
    if len(argv) >= 2 and argv[0] == "--from":
        src = read_env(Path(argv[1]).expanduser())
        key = next((src[n] for n in NAMES if src.get(n)), "")
        if not key:
            print("No GEMINI_API_KEY or GOOGLE_API_KEY line found in that file. Nothing changed.")
            return 1
    elif argv:
        print(__doc__)
        return 1
    else:
        key = getpass.getpass("Paste your Gemini API key (it stays hidden), then press Enter: ").strip()
        if not key:
            print("No key entered. Nothing changed.")
            return 1

    current = read_env(ENV)
    updates = {"GEMINI_API_KEY": key, "API_SERVER_ENABLED": "true"}
    if not current.get("API_SERVER_KEY"):
        updates["API_SERVER_KEY"] = secrets.token_urlsafe(32)
    write_env(ENV, updates)
    print("Done: the Gemini key is saved in Hermes' private settings, and Henry's link to Hermes is on.")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
