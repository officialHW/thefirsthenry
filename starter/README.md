# Your tiny desktop buddy (starter kit)

A tiny 3D character who lives on your screen, talks out loud, listens through the mic, shows
moods, walks around, and remembers things about you. His brain is Hermes Agent. First-time
set-up is in START-HERE.md.

## What is where

| Folder / file | What it is |
| --- | --- |
| `rig/` | The 3D body. `buddy.glb` is the stand-in body; put your own as `henry-rigged.glb`. `henry.js` moves him. See `rig/README.md`. |
| `app/` | His page (`web/index.html`), the helper that links him to Hermes (`server.py`), the starter (`launch.py`) and his settings (`settings.json`). |
| `hermes-data/` | His starting personality (`SOUL.md`) and brain settings (`config.yaml`), copied into `hermes/` by set-up. |
| `hermes/` | Made by set-up: Hermes Agent, its settings, memory and chat history. Your key lives in `hermes/.env` and nowhere else. |
| `tools/` | `set_key.py` (puts your key in safely), `set_hf_token.py` (voice key), `pack_up.py` and `restore.py` (moving computers). |
| `overlay/` | The see-through desktop window (Electron). |
| `voice/` | Your own voice (optional). See `voice/README.md`. |
| `extras/` | Optional add-ons, like letting him read your files. |
| `start.*`, `start-overlay.*`, `setup.*` | Double-click to start him, or to set him up. |

## Using him

- Type in the box and press Enter, or click 🎤 and just talk. Click 🎤 again to stop listening.
- Pick him up with the mouse and put him anywhere. Say "come here" to bring him back.
- He notices you: he watches your pointer, gets curious when it comes close, jumps if you
  swipe past fast, waves if you hover on him, giggles if you poke (quick click) him, walks to
  where you click, looks at the box while you type, and dozes off if left alone.
- On the whole desktop (`start-overlay`): clicks on empty space go through to the windows
  underneath. Hover on him for the chat box, or press **Cmd+Shift+H** (Windows:
  **Ctrl+Shift+H**). The microphone only works in the normal window.

## Settings (`app/settings.json`)

Restart him after changing them.

- `"graphics"`: `"low"` (default, fine for older computers) or `"high"`.
- `"size"`: his height in pixels. 110 is about thumb height.
- `"voice"`: the name of a computer voice, or `""` for the default.
- `"model"`: the body file in `rig/`. If it isn't there, he uses `buddy.glb`.
- `"my_voice"`, `"voice_model"`, `"voice_file"`: your own voice, see `voice/README.md`.

## Make him yours

1. **Name and personality.** Open `hermes/SOUL.md` in any text editor. Change "Henry" to his
   new name and describe how he should talk. Keep the "Mood and body tags" part: that is what
   makes him move. Changes apply to new conversations.
2. **Colours.** Edit the colours at the top of `rig/tools/make_buddy.py`, then run
   `python3 rig/tools/make_buddy.py rig/buddy.glb` (Windows: `python` instead of `python3`).
3. **Your own 3D body.** Make a full-body character from a photo with an online 3D tool,
   give it a skeleton, and save it as `rig/henry-rigged.glb`. The bones must use the usual
   "Mixamo" names (Hips, Spine, Neck, Head, LeftArm, LeftForeArm, LeftUpLeg, LeftLeg,
   LeftFoot and the Right ones); a `Jaw` bone makes the mouth move. Details in `rig/README.md`.
   Check the body with `rig/demo.html` first (see `rig/README.md`).
4. **Your voice.** See `voice/README.md`.
5. **Let him read your files** (optional). See `extras/full-access-SOUL-section.md`. Only do
   this if you are happy for what he reads to go to your AI service.

## A different brain

He uses Google Gemini by default (free key). Hermes Agent can also use other services, such
as an OpenAI or Anthropic key, or a ChatGPT plan with `hermes auth add openai-codex --browser`.
To pick one, run this from the kit folder, then restart him:

    HERMES_HOME="$PWD/hermes" hermes/hermes-agent/.hermes/bin/hermes model

## Talking to him from your phone (private, with Tailscale)

Tailscale makes a private network between only your own devices. Nothing is opened to the
public internet.

1. Install Tailscale on the computer and on your phone (https://tailscale.com/download), and
   sign in to both with the **same** account.
2. On https://login.tailscale.com/admin/dns turn on **MagicDNS** and **HTTPS Certificates**.
3. With him running, open Terminal and type `tailscale serve --bg 4750` (Mac, if that isn't
   found: `/Applications/Tailscale.app/Contents/MacOS/Tailscale serve --bg 4750`).
4. Open the `https://...ts.net` address it prints on your phone. To stop: `tailscale serve reset`.

Never use `tailscale funnel`: that one opens things to the public internet.

## Moving to another computer

Stop him, then in the kit folder run `hermes/tools/python-*/bin/python3 -I tools/pack_up.py`
(Windows: `for /d %D in (hermes\tools\python-*) do "%D\python.exe" -I tools\pack_up.py`).
It makes one zip next to the folder with his memory and chats, but no keys. On the new
computer unzip it and run set-up again. Make a fresh Gemini key there, or bring yours in a
password manager. Never email or text a key to yourself.

## Safety

- Hermes and the helper only listen on your own computer (127.0.0.1).
- Your key never reaches the web page; the page uses a random one-time token.
- When asked through the buddy, Hermes refuses risky computer commands automatically.
- He asks before deleting, sending, buying or changing anything.
