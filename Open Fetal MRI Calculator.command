#!/bin/zsh

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$SCRIPT_DIR"

if [ ! -x ".venv/bin/python" ]; then
  echo "Missing virtual environment at .venv"
  echo "Create it first with:"
  echo "python3 -m venv .venv"
  echo ".venv/bin/pip install fastapi uvicorn jinja2 scipy python-multipart pytest httpx"
  echo
  read -k 1 "?Press any key to close..."
  echo
  exit 1
fi

if [ ! -f "app/data/kyriakopoulou_2017_formulas.json" ] || [ ! -f "app/data/harreld_2011_corpus_callosum.json" ]; then
  echo "Missing data files in app/data."
  echo "This copy of the project expects the versioned JSON data files to be present."
  echo
  read -k 1 "?Press any key to close..."
  echo
  exit 1
fi

echo "Starting Fetal MRI Calculator..."
echo "The browser should open automatically at http://127.0.0.1:8001"
echo "Leave this Terminal window open while using the app."
echo

if lsof -iTCP:8001 -sTCP:LISTEN >/dev/null 2>&1; then
  echo "An existing calculator server is already running on port 8001."
  open "http://127.0.0.1:8001"
  exit 0
fi

( sleep 2; open "http://127.0.0.1:8001" ) &
exec .venv/bin/uvicorn app.main:app --host 127.0.0.1 --port 8001 --reload
