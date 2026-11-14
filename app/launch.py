"""Starts everything: Hermes (the brain), Henry's body server, and a small window showing Henry.

Run it with start.command (Mac), start.bat (Windows) or start.sh (Linux).
Close the window or press Ctrl+C in the terminal to stop.
"""

import json
import os
import shutil
import subprocess
import sys
import time
import urllib.request
import webbrowser
from pathlib import Path

APP = Path(__file__).resolve().parent
ROOT = APP.parent
os.environ.setdefault("HERMES_HOME", str(ROOT / "hermes"))
HERMES_HOME = Path(os.environ["HERMES_HOME"])
SETTINGS = {"port": 4750, "hermes_url": "http://127.0.0.1:8642"}
try:
    SETTINGS.update(json.loads((APP / "settings.json").read_text(encoding="utf-8")))
except (OSError, ValueError):
    pass
WIN = os.name == "nt"


def up(url):
    try:
        with urllib.request.urlopen(url, timeout=2) as r:
            return r.status == 200
    except OSError:
        return False


def hermes_cmd():
    bindir = HERMES_HOME / "hermes-agent" / ".hermes" / "bin"
    for name in (("hermes.cmd", "hermes.exe", "hermes.ps1", "hermes") if WIN else ("hermes",)):
        c = bindir / name
        if c.exists():
            return ["powershell", "-NoProfile", "-ExecutionPolicy", "Bypass", "-File", str(c)] \
                if c.suffix == ".ps1" else [str(c)]
    found = shutil.which("hermes")
    return [found] if found else None


def open_window(url):
    """A small app-style window if Chrome or Edge is installed, else the normal browser."""
    size = "--window-size=460,420"
    candidates = []
    if sys.platform == "darwin":
        candidates = ["/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
                      "/Applications/Microsoft Edge.app/Contents/MacOS/Microsoft Edge"]
    elif WIN:
        for base in (os.environ.get("ProgramFiles", ""), os.environ.get("ProgramFiles(x86)", ""),
                     os.environ.get("LOCALAPPDATA", "")):
            candidates += [os.path.join(base, "Google", "Chrome", "Application", "chrome.exe"),
                           os.path.join(base, "Microsoft", "Edge", "Application", "msedge.exe")]
    else:
        candidates = [shutil.which(n) or "" for n in ("google-chrome", "chromium", "microsoft-edge")]
    for c in candidates:
        if c and os.path.exists(c):
            subprocess.Popen([c, "--app=" + url, size], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            return
    webbrowser.open(url)


def electron_exe():
    """The Electron program installed in overlay/ (see overlay/main.js), or None."""
    dist = ROOT / "overlay" / "node_modules" / "electron" / "dist"
    exe = (dist / "electron.exe") if WIN else \
        (dist / "Electron.app" / "Contents" / "MacOS" / "Electron") if sys.platform == "darwin" else (dist / "electron")
    return exe if exe.exists() else None


def open_overlay(url):
    """Henry on top of the whole desktop. Falls back to the small window if Electron isn't installed."""
    exe = electron_exe()
    if not exe:
        print("The desktop overlay isn't installed here (see MOVING.md). Opening the normal window instead.")
        open_window(url)
        return None
    return subprocess.Popen([str(exe), str(ROOT / "overlay"), "--url=" + url],
                            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)


def start_voice():
    """Starts Pocket TTS with your own voice on a random port only this computer can reach."""
    if not SETTINGS.get("my_voice", True):
        return None
    vdir = ROOT / "voice"
    exe = vdir / "bin" / ("pocket-tts.exe" if WIN else "pocket-tts")
    vfile = ROOT / SETTINGS.get("voice_file", "voice/my-voice-2m.safetensors")
    if not (exe.exists() and vfile.exists()):
        return None
    import socket
    with socket.socket() as sk:
        sk.bind(("127.0.0.1", 0))
        port = sk.getsockname()[1]
    env = dict(os.environ, HF_HOME=str(vdir / "hf-cache"))
    log = open(vdir / "voice.log", "a", encoding="utf-8")
    p = subprocess.Popen([str(exe), "serve", "--host", "127.0.0.1", "--port", str(port),
                          "--language", SETTINGS.get("voice_model", "english_2m_2026-10"),
                          "--default-voice", str(vfile)], env=env, stdout=log, stderr=log)
    url = "http://127.0.0.1:%d" % port
    for _ in range(120):                      # loading the voice takes a little while
        if p.poll() is not None:
            print("Your voice didn't start (see voice/voice.log). Henry will use the computer voice.")
            return None
        if up(url + "/"):
            os.environ["HENRY_TTS_URL"] = url  # passed on to Henry's helper program
            print("Henry is speaking in your voice.")
            return p
        time.sleep(1)
    p.terminate()
    print("Your voice took too long to start. Henry will use the computer voice.")
    return None


def main():
    overlay = "--overlay" in sys.argv[1:]
    procs = []
    hermes_health = SETTINGS["hermes_url"].rstrip("/") + "/health"
    if not up(hermes_health):
        cmd = hermes_cmd()
        if not cmd:
            print("Hermes is not installed here yet. Run the set-up script first.")
            return 1
        print("Starting Hermes…")
        log = open(HERMES_HOME / "logs" / "henry-gateway.log", "a", encoding="utf-8") \
            if (HERMES_HOME / "logs").is_dir() else subprocess.DEVNULL
        procs.append(subprocess.Popen(cmd + ["gateway"], stdout=log, stderr=log))
        for _ in range(90):
            if up(hermes_health):
                break
            time.sleep(1)
        else:
            print("Hermes did not start. Look in", HERMES_HOME / "logs", "for clues.")
    url = "http://127.0.0.1:%d/" % int(SETTINGS["port"])
    if not up(url + "api/health"):
        vp = start_voice()
        if vp:
            procs.append(vp)
        procs.append(subprocess.Popen([sys.executable, str(APP / "server.py")]))
        for _ in range(20):
            if up(url + "api/health"):
                break
            time.sleep(0.5)
    if overlay:
        p = open_overlay(url)
        if p:
            procs.append(p)
            print("Henry is on your desktop. Ctrl+Shift+H (Cmd+Shift+H on a Mac) opens his chat box.")
    else:
        open_window(url)
    print("Henry is running. Keep this window open; press Ctrl+C here to stop him.")
    try:
        while all(p.poll() is None for p in procs) if procs else True:
            time.sleep(1)
    except KeyboardInterrupt:
        pass
    finally:
        for p in procs:
            p.terminate()
    return 0


if __name__ == "__main__":
    sys.exit(main())
