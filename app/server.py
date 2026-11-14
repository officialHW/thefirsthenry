"""Henry's body server.

Serves the 3D body page and passes what you type or say to Hermes Agent, then hands the
reply back so Henry can say it. Only standard Python, so it runs anywhere Hermes runs.

Safety:
- Listens on this computer only (127.0.0.1). The phone reaches it through Tailscale Serve,
  which only your own signed-in devices can use.
- Hermes' access key stays in this program. The web page never sees it.
- Every chat request must carry a random token that is written into the page when it
  loads. Other websites open in your browser cannot read that page, so they cannot
  talk to Henry (and through him, to Hermes).
"""

import datetime
import json
import os
import re
import secrets
import sys
import urllib.error
import urllib.request
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

APP = Path(__file__).resolve().parent
ROOT = APP.parent
RIG = ROOT / "rig"
HERMES_HOME = Path(os.environ.get("HERMES_HOME") or ROOT / "hermes")
TOKEN = secrets.token_urlsafe(24)
# Your own voice (Pocket TTS, started by launch.py on a random local port). Empty = not running.
TTS_URL = os.environ.get("HENRY_TTS_URL", "").rstrip("/")
MOODS = {"neutral", "calm", "happy", "excited", "playful", "thinking", "curious", "confused",
         "surprised", "shock", "nervous", "embarrassment", "sad", "crying", "angry", "arrogance"}
TAG = re.compile(r"\[\s*([a-zA-Z]+)\s*(?::\s*([a-zA-Z0-9.\-]+))?\s*\]")


def load_settings():
    s = {"graphics": "low", "size": 110, "voice": "", "port": 4750,
         "hermes_url": "http://127.0.0.1:8642", "session": "henry"}
    try:
        s.update(json.loads((APP / "settings.json").read_text(encoding="utf-8")))
    except (OSError, ValueError):
        pass
    return s


SETTINGS = load_settings()


def hermes_key():
    """Reads only the API_SERVER_KEY line from Hermes' .env. Never printed or sent to the page."""
    try:
        for line in (HERMES_HOME / ".env").read_text(encoding="utf-8").splitlines():
            k, _, v = line.partition("=")
            if k.strip() == "API_SERVER_KEY":
                return v.strip().strip('"').strip("'")
    except OSError:
        pass
    return ""


def split_reply(text):
    """Pulls [mood] and [action] tags out of Hermes' reply. Returns (mood, actions, clean text)."""
    mood, actions = None, []
    for m in TAG.finditer(text or ""):
        name, arg = m.group(1).lower(), m.group(2)
        if name in MOODS and mood is None:
            mood = name
        elif name in ("wave", "comehere"):
            actions.append({"do": name})
        elif name == "walk" and arg in ("left", "right", "middle"):
            actions.append({"do": "walk", "to": {"left": -1, "right": 1, "middle": 0}[arg]})
    if mood is None and "⚠" in (text or ""):    # Hermes' own warning messages
        mood = "confused"
    clean = TAG.sub("", text or "")
    clean = re.sub(r"[*_`#>]+", "", clean)          # no markdown symbols read aloud
    clean = re.sub("[☀-➿️\U0001f000-\U0001faff]", "", clean)   # no emoji read aloud
    clean = re.sub(r"[ \t]+", " ", clean).strip()
    return mood or "neutral", actions, clean


# One conversation per day keeps each chat short and quick. Long-term facts live in Hermes'
# memory files, so nothing is forgotten when the day changes. If Hermes puts a conversation on
# hold (409: for example Henry was closed mid-reply), the next one is used instead.
_roll = {"day": None, "n": 0}


def session_id():
    day = datetime.date.today().isoformat()
    if _roll["day"] != day:
        _roll.update(day=day, n=0)
    return "%s-%s%s" % (SETTINGS["session"], day, "-%d" % _roll["n"] if _roll["n"] else "")


def ask_hermes(text, retry=True):
    body = json.dumps({
        "model": "hermes-agent",
        "messages": [{"role": "user", "content": text}],
    }).encode()
    req = urllib.request.Request(
        SETTINGS["hermes_url"].rstrip("/") + "/v1/chat/completions", data=body, method="POST",
        headers={"Content-Type": "application/json",
                 "Authorization": "Bearer " + hermes_key(),
                 "X-Hermes-Session-Id": session_id()})
    try:
        with urllib.request.urlopen(req, timeout=300) as r:
            data = json.loads(r.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        if e.code == 409 and retry:
            _roll["n"] += 1
            return ask_hermes(text, retry=False)
        raise
    return data["choices"][0]["message"]["content"] or ""


class Handler(SimpleHTTPRequestHandler):
    def speak(self, text):
        """Streams Henry's reply as speech in your own voice, as it is being made."""
        if not TTS_URL:
            return self.send_json(503, {"error": "Your voice isn't running."})
        try:
            r = tts_request(text)
        except (urllib.error.URLError, OSError):
            return self.send_json(503, {"error": "Your voice isn't running."})
        with r:
            self.send_response(200)
            self.send_header("Content-Type", "audio/wav")
            self.send_header("Cache-Control", "no-store")
            self.end_headers()
            try:
                while True:
                    chunk = r.read1(8192) if hasattr(r, "read1") else r.read(8192)
                    if not chunk:
                        break
                    self.wfile.write(chunk)
                    self.wfile.flush()
            except (OSError, ValueError):
                pass   # the page stopped listening (for example you sent a new message)

    server_version = "Henry"
    sys_version = ""

    def log_message(self, fmt, *args):   # keep the console quiet: no chat text in logs
        pass

    # --- safety checks -------------------------------------------------------------
    def host_ok(self):
        host = (self.headers.get("Host") or "").lower()
        name = host.rsplit(":", 1)[0] if not host.startswith("[") else host.split("]")[0] + "]"
        return name in ("127.0.0.1", "localhost", "[::1]") or name.endswith(".ts.net")

    def origin_ok(self):
        origin = self.headers.get("Origin")
        if not origin:
            return True
        host = self.headers.get("Host") or ""
        return origin in ("http://" + host, "https://" + host)

    def send_json(self, code, obj):
        out = json.dumps(obj).encode()
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(out)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(out)

    def end_headers(self):
        self.send_header("X-Content-Type-Options", "nosniff")
        self.send_header("Referrer-Policy", "no-referrer")
        super().end_headers()

    # --- pages ---------------------------------------------------------------------
    def translate_path(self, path):
        path = path.split("?", 1)[0].split("#", 1)[0]
        if path.startswith("/rig/"):
            base, rest = RIG, path[len("/rig/"):]
        else:
            base, rest = APP / "web", path.lstrip("/")
        target = (base / rest).resolve()
        if base.resolve() not in target.parents and target != base.resolve():
            return str(APP / "web" / "missing")
        return str(target)

    def do_GET(self):
        if not self.host_ok():
            return self.send_error(403)
        if self.path.split("?")[0] in ("/", "/index.html"):
            html = (APP / "web" / "index.html").read_text(encoding="utf-8")
            cfg = {k: SETTINGS[k] for k in ("graphics", "size", "voice")}
            # your own 3D body if it is there, otherwise the stand-in "Buddy"
            own = RIG / str(SETTINGS.get("model") or "henry-rigged.glb")
            cfg["model"] = "/rig/" + (own.name if own.is_file() else "buddy.glb")
            cfg["myvoice"] = bool(TTS_URL)
            # how much of a reply to collect before starting to speak: slower voices need more
            cfg["voicelead"] = float(SETTINGS.get("voice_lead") or
                                     (0.35 if "2m" in str(SETTINGS.get("voice_model", "")) else 0.65))
            html = html.replace("__HENRY_TOKEN__", TOKEN).replace("__HENRY_SETTINGS__", json.dumps(cfg))
            out = html.encode()
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.send_header("Content-Length", str(len(out)))
            self.send_header("Cache-Control", "no-store")
            self.end_headers()
            return self.wfile.write(out)
        if self.path == "/api/health":
            return self.send_json(200, {"ok": True})
        if self.path.startswith("/rig/tools"):
            return self.send_error(404)
        return super().do_GET()

    def do_POST(self):
        if not (self.host_ok() and self.origin_ok()):
            return self.send_error(403)
        if self.headers.get("X-Henry-Token") != TOKEN:
            return self.send_json(403, {"error": "Please reload the page."})
        if self.path not in ("/api/chat", "/api/speak"):
            return self.send_error(404)
        try:
            n = min(int(self.headers.get("Content-Length") or 0), 20000)
            text = str(json.loads(self.rfile.read(n) or b"{}").get("text", "")).strip()[:4000]
        except ValueError:
            return self.send_json(400, {"error": "bad request"})
        if not text:
            return self.send_json(400, {"error": "Say something first."})
        if self.path == "/api/speak":
            return self.speak(text[:1500])
        try:
            mood, actions, say = split_reply(ask_hermes(text))
            return self.send_json(200, {"mood": mood, "actions": actions, "say": say})
        except urllib.error.HTTPError as e:
            msg = "Hermes said no (error %d)." % e.code
            if e.code == 401:
                msg = "Hermes did not accept the access key. Run the set-up again."
            elif e.code == 429:
                msg = "The free Gemini limit is used up for now. Try again in a minute."
            return self.send_json(502, {"error": msg, "mood": "confused"})
        except (urllib.error.URLError, OSError):
            up = True
            try:
                urllib.request.urlopen(SETTINGS["hermes_url"].rstrip("/") + "/health", timeout=3).close()
            except OSError:
                up = False
            msg = ("My brain hit a problem with that one. Its log is in hermes/logs/agent.log."
                   if up else "I can't reach my brain. Is Hermes running?")
            return self.send_json(502, {"error": msg, "mood": "confused"})


def tts_request(text):
    """Asks Pocket TTS (on this computer only) to say the text in your voice. Returns the open reply."""
    boundary = "henry" + secrets.token_hex(8)
    body = ("--%s\r\nContent-Disposition: form-data; name=\"text\"\r\n\r\n%s\r\n--%s--\r\n"
            % (boundary, text, boundary)).encode("utf-8")
    req = urllib.request.Request(TTS_URL + "/tts", data=body, method="POST",
                                 headers={"Content-Type": "multipart/form-data; boundary=" + boundary})
    return urllib.request.urlopen(req, timeout=120)


def main():
    port = int(SETTINGS["port"])
    if not hermes_key():
        print("Warning: no API_SERVER_KEY found in", HERMES_HOME / ".env", "- run the set-up first.")
    httpd = ThreadingHTTPServer(("127.0.0.1", port), Handler)
    print("Henry is at http://127.0.0.1:%d  (press Ctrl+C to stop)" % port)
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        pass


if __name__ == "__main__":
    sys.exit(main())
