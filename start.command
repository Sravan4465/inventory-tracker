#!/bin/sh
# Mac: double-click this file. Needs Python 3 installed (python.org).
cd "$(dirname "$0")" || exit 1
fail() { echo; echo "ERROR: $1"; echo "Press Enter to close."; read _; exit 1; }
command -v python3 >/dev/null || fail "Python 3 not found. Install it from https://www.python.org/downloads/"
if [ ! -d .venv ]; then
  echo "First start: installing (needs internet, takes a minute)..."
  python3 -m venv .venv && .venv/bin/pip install -q -r requirements.txt || { rm -rf .venv; fail "Install failed. Check your internet connection."; }
fi
(sleep 2; open http://localhost:5050) &
echo "Inventory Tracker running at http://localhost:5050  (close this window to stop)"
.venv/bin/python app.py || fail "The app stopped. If it says the address is in use, it is already running: open http://localhost:5050"
