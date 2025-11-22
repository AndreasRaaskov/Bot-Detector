#!/usr/bin/env bash
# Build the frontend and start the backend to serve the built assets

set -euo pipefail

echo "Building frontend..."
cd frontend
if [ -f package-lock.json ]; then
  npm ci
else
  npm install
fi
npm run build

echo "Starting backend to serve built frontend..."
cd ..
# If there's a venv in the project, activate it
if [ -f "./venv/bin/activate" ]; then
  # shellcheck disable=SC1091
  source ./venv/bin/activate
fi

# Start the backend (it will mount frontend/dist if present)
python -m backend.main
