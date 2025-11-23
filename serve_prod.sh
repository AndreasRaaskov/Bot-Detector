#!/usr/bin/env bash
# Copy simple frontend to dist and start the backend to serve it

set -euo pipefail

echo "Preparing simple frontend for production..."
# Create frontend/dist directory if it doesn't exist
mkdir -p frontend/dist

# Copy simple frontend files to where backend expects them
echo "Copying files from frontend_simple to frontend/dist..."
cp -r frontend_simple/* frontend/dist/

echo "Starting backend to serve frontend..."
# If there's a venv in the project, activate it
if [ -f "./venv/bin/activate" ]; then
  # shellcheck disable=SC1091
  source ./venv/bin/activate
fi

echo ""
echo "=================================================="
echo "  Bot Detector is starting in PRODUCTION mode"
echo "=================================================="
echo "  URL:          http://localhost:8000"
echo "  API Docs:     http://localhost:8000/docs"
echo "=================================================="
echo ""

# Start the backend (it will mount frontend/dist if present)
python -m backend.main
