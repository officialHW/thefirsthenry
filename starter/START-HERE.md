# Start here

This is a starter kit for your own tiny 3D desktop buddy. He lives on your screen, talks
out loud, listens through the microphone, shows moods, walks around, and remembers things
about you. His brain is Hermes Agent, running on your own computer.

He starts out as **Buddy**, a simple cartoon stand-in. You can give him your own face, name,
personality and voice later (see README.md).

## What you need

- A Mac, Windows or Linux computer with about 3 GB of free space.
- An internet connection for set-up.
- A free Google Gemini key: go to https://aistudio.google.com/apikey, sign in with a Google
  account, click **Create API key** and keep the page open. Treat the key like a password.
- Optional, for the see-through desktop version: Node.js (free, https://nodejs.org, the
  "LTS" button).

## Set up (about 20 minutes, once)

1. Unzip this kit somewhere **outside** Desktop and Documents (cloud syncing there slows it
   down). For example, Mac: a `Projects` folder in your home folder. Windows:
   `C:\Users\<you>\Projects`.
2. **Mac or Linux:** open Terminal, type `cd ` (with a space), drag the unzipped
   `henry-starter-kit` folder onto the Terminal window, press Enter. Then type
   `bash setup.sh` and press Enter.
   **Windows:** open the unzipped folder and double-click `setup.bat`.
3. Type `y` and press Enter to let it install Hermes Agent (official installer, 1-2 GB).
4. When it asks for your Gemini key, paste it and press Enter. Nothing appears while you
   paste: that is on purpose.
5. If you installed Node.js, type `y` when it offers the desktop overlay.

## Start him

- In a small window: double-click `start.command` (Mac) or `start.bat` (Windows), or run
  `./start.sh` (Linux).
- On top of your whole desktop: double-click `start-overlay.command` (Mac) or
  `start-overlay.bat` (Windows).

Mac: the first time, macOS may say it can't check the file. Right-click it, choose **Open**,
then **Open** again.

Type to him, or click the microphone and talk. Stop him by closing the Terminal window.

## Next

- README.md: everything he can do, his settings, and how to make him yours.
- voice/README.md: make him speak in your own voice (free).
- NOTICE.md: credits and licences, please keep it when you share the kit.
