#!/usr/bin/env bash
# Simple development runner: starts backend and serves simple frontend

set -euo pipefail

# If there's a venv in the project, activate it
if [ -f "./venv/bin/activate" ]; then
  # shellcheck disable=SC1091
  source ./venv/bin/activate
fi

echo "Starting backend (FastAPI) on port 8000..."
# Start backend in background
python -m backend.main &
BACKEND_PID=$!

echo "Starting frontend server on port 8080..."
# Start a simple HTTP server for the frontend
cd frontend_simple
python3 -m http.server 8080 &
FRONTEND_PID=$!

echo ""
echo "=================================================="
echo "  Bot Detector is running!"
echo "=================================================="
echo "  Backend API:  http://localhost:8000"
echo "  Frontend:     http://localhost:8080"
echo "  API Docs:     http://localhost:8000/docs"
echo "=================================================="
echo ""
echo "Press Ctrl+C to stop both servers"
echo ""

# Wait for user interrupt
trap "echo 'Stopping servers...'; kill $BACKEND_PID $FRONTEND_PID 2>/dev/null || true; exit 0" SIGINT SIGTERM

# Keep script running
wait
