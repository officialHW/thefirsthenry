#!/bin/bash
# Set up Henry on a new Mac or Linux computer. Run it from inside the unzipped folder:
#     bash setup.sh
# It installs Hermes Agent with its official installer, puts back Henry's memory, skills and
# settings from the bundle, and asks for your Gemini key (typing stays hidden).
set -e
cd "$(dirname "$0")"
export HERMES_HOME="$PWD/hermes"

echo
echo "This will download and install Hermes Agent (about 1-2 GB) from the official site:"
echo "    https://hermes-agent.nousresearch.com/install.sh"
read -r -p "Go ahead? Type y and press Enter: " ok
[ "$ok" = "y" ] || [ "$ok" = "Y" ] || { echo "Stopped. Nothing was installed."; exit 1; }

curl -fsSL https://hermes-agent.nousresearch.com/install.sh | \
  bash -s -- --hermes-home "$HERMES_HOME" --skip-browser --skip-computer-use --non-interactive

PY="$(ls -d "$HERMES_HOME"/tools/python-*/bin/python3 2>/dev/null | tail -1)"
[ -x "$PY" ] || PY="$(command -v python3)"

if [ -d hermes-data ]; then
  echo "Putting back Henry's memory, skills and settings..."
  "$PY" tools/restore.py
fi

echo
echo "Now your Gemini key. Get it from https://aistudio.google.com/apikey or your password manager."
"$PY" tools/set_key.py

echo
if command -v npm >/dev/null; then
  read -r -p "Also install the desktop overlay (Electron, about 200 MB, lets Henry walk on top of your whole screen)? [y/N] " ov
  if [ "$ov" = "y" ] || [ "$ov" = "Y" ]; then (cd overlay && npm ci --no-fund --no-audit && npx electron --version); fi
else
  echo "(Optional: install Node.js from nodejs.org, then run this again to get the desktop overlay.)"
fi

chmod +x start.command start.sh start-overlay.command 2>/dev/null || true
echo
echo "All set. Start Henry by double-clicking start.command (Mac) or running ./start.sh (Linux)."
echo "For Henry on top of your whole desktop: start-overlay.command (needs the overlay installed)."
