#!/bin/bash
# Double-click this file (Mac) to put Henry on top of your whole desktop. Linux: ./start-overlay.command
cd "$(dirname "$0")" || exit 1
export HERMES_HOME="$PWD/hermes"
PY="$(ls -d "$HERMES_HOME"/tools/python-*/bin/python3 2>/dev/null | tail -1)"
[ -x "$PY" ] || PY="$(command -v python3 || command -v python)"
exec "$PY" -I app/launch.py --overlay
