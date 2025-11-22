#!/usr/bin/env bash
# Simple development runner: starts backend and frontend dev server

set -euo pipefail

# If there's a venv in the project, activate it
if [ -f "./venv/bin/activate" ]; then
  # shellcheck disable=SC1091
  source ./venv/bin/activate
fi

echo "Starting backend (FastAPI)..."
# Start backend in background
python -m backend.main &
BACKEND_PID=$!

echo "Starting frontend (Vite)..."
cd frontend
npm run dev

# If frontend exits, kill backend
echo "Stopping backend (pid: $BACKEND_PID)"
kill $BACKEND_PID 2>/dev/null || true
