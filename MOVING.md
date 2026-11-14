# Moving Henry to another computer

Henry moves as one `.zip` file. It holds his memory, skills, personality, settings, chat
history, the 3D body and the app. It does **not** hold your Gemini key or any other secret,
and it does not hold Hermes itself (the new computer downloads a fresh copy).

## 1. Pack up (on the old computer)

1. Stop Henry first (press Ctrl+C in his terminal window, or close it).
2. Mac: open Terminal, then type `cd ~/Projects/thefirsthenry` and press Enter.
   Windows: open the `thefirsthenry` folder, click the address bar, type `cmd`, press Enter.
3. Mac or Linux: type this and press Enter:

       hermes/tools/python-*/bin/python3 -I tools/pack_up.py

   Windows: type this and press Enter:

       for /d %D in (hermes\tools\python-*) do "%D\python.exe" -I tools\pack_up.py

4. It makes a file called `thefirsthenry-pack-<date>.zip` next to the `thefirsthenry` folder.
   Copy it to the new computer (USB stick, AirDrop, cloud drive: it has no secrets in it,
   but it does hold your memories and chats, so treat it as private).

## 2. Set up (on the new computer)

1. Unzip it somewhere outside Desktop and Documents, for example
   Mac: `~/Projects/thefirsthenry`   Windows: `C:\Users\<you>\Projects\thefirsthenry`.
2. Mac or Linux: open Terminal in that folder and type `bash setup.sh`, then press Enter.
   Windows: double-click `setup.bat`.
3. Type `y` to let it install Hermes (official installer, about 1-2 GB, 10-20 minutes).
4. When it asks for your Gemini key, paste it and press Enter. Nothing shows while you
   paste: that is on purpose.
5. Start Henry: double-click `start.command` (Mac) or `start.bat` (Windows), or run
   `./start.sh` (Linux).

## Carrying your key safely

The key is never in the zip. Pick one:

- **Easiest and safest:** make a new key at https://aistudio.google.com/apikey on the new
  computer, paste it in step 2.4, then delete the old key on the same page.
- **Keep the same key:** save it in a password manager (Apple Passwords, Bitwarden,
  1Password) and copy it from there in step 2.4.

Never email, text or chat the key to yourself, and never put it in a file inside the zip.

## Phone access on the new computer

Install Tailscale on the new computer, sign in with the same account, then run the
`tailscale serve` command from README.md again. Turn it off on the old computer with
`tailscale serve reset`.

## Turning the graphics up

On a stronger computer, open `app/settings.json` and change `"graphics": "low"` to
`"graphics": "high"`, then restart Henry.

## The desktop overlay

The zip leaves out Electron (`overlay/node_modules`, about 290 MB). The set-up script asks if
you want it again; it needs Node.js (free, from https://nodejs.org). Or later, in the Henry
folder, run:

    cd overlay
    npm ci

## Henry's ChatGPT brain

Henry's main brain is your ChatGPT plan (model gpt-6-luna), with free Gemini as backup. The
ChatGPT sign-in is never packed. On the new computer, after set-up, sign in again with:

    HERMES_HOME="$PWD/hermes" hermes/hermes-agent/.hermes/bin/hermes auth add openai-codex --browser

(Windows: `set HERMES_HOME=%CD%\hermes` first, then run `hermes\hermes-agent\.hermes\bin\hermes.cmd auth add openai-codex --browser`.)

## Henry speaking in your voice

Your voice files travel in the zip (`voice/`). The voice program and your Hugging Face key
don't. On the new computer:

1. Download the Pocket TTS file for that computer from
   https://github.com/kyutai-labs/pocket-tts/releases (Mac Intel: `x86_64-apple-darwin`,
   Mac M-chip: `aarch64-apple-darwin`, Windows: `x86_64-pc-windows-msvc.zip`), and put the
   `pocket-tts` program in `voice/bin/`.
2. Save your Hugging Face key again: `python tools/set_hf_token.py` (use Hermes' Python as in the steps above).
3. Start Henry. If anything is missing he simply uses the computer voice.
