#!/usr/bin/env bash
# Start SwarnaSetu on macOS or Linux: ./start.sh
set -euo pipefail
cd "$(dirname "$0")"

PY=${PYTHON:-python3}
command -v "$PY" >/dev/null || { echo "Python 3.10+ is needed."; exit 1; }

if [ ! -x backend/.venv/bin/python ]; then
  echo "Creating the Python environment (first run only)..."
  "$PY" -m venv backend/.venv
fi
backend/.venv/bin/python -m pip install --quiet --disable-pip-version-check -r backend/requirements.txt

if [ ! -f frontend/dist/index.html ]; then
  command -v npm >/dev/null || { echo "Node.js 18+ is needed to build the web app."; exit 1; }
  echo "Building the web app (first run only)..."
  (cd frontend && npm install --no-audit --no-fund && npm run build)
fi

echo
echo "Open http://localhost:8000 in your browser. Press Ctrl+C to stop."
echo
cd backend
exec .venv/bin/python -m uvicorn app.main:app --host 127.0.0.1 --port 8000
