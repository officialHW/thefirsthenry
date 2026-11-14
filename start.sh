#!/bin/bash
# Double-click this file (Mac) to start Henry. On Linux run ./start.sh
cd "$(dirname "$0")" || exit 1
export HERMES_HOME="$PWD/hermes"
PY="$(ls -d "$HERMES_HOME"/tools/python-*/bin/python3 2>/dev/null | tail -1)"
[ -x "$PY" ] || PY="$(command -v python3 || command -v python)"
exec "$PY" -I app/launch.py
