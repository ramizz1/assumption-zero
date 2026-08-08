#!/usr/bin/env bash
set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BACKEND="$SCRIPT_DIR/backend"
FRONTEND="$SCRIPT_DIR/frontend"
VENV="$BACKEND/.venv"

echo ""
echo "╔══════════════════════════════════════════════════════════╗"
echo "║         ASSUMPTION ZERO — Web App Launcher               ║"
echo "║         Stress-test your MVP before you build it         ║"
echo "╚══════════════════════════════════════════════════════════╝"
echo ""

# Check Python
if ! command -v python3 &>/dev/null; then
    echo "[ERROR] python3 is not installed. Install from https://www.python.org/"
    exit 1
fi

# Check Node.js
if ! command -v node &>/dev/null; then
    echo "[ERROR] node is not installed. Install from https://nodejs.org/"
    exit 1
fi

# Setup backend venv
if [ ! -f "$VENV/bin/python" ]; then
    echo "[INFO] Creating Python virtual environment..."
    python3 -m venv "$VENV"
    echo "[INFO] Installing backend dependencies..."
    "$VENV/bin/pip" install -e "$BACKEND" --quiet
    echo "[INFO] Backend dependencies installed."
else
    echo "[INFO] Backend virtual environment found."
fi

# Install frontend dependencies
if [ ! -d "$FRONTEND/node_modules" ]; then
    echo "[INFO] Installing frontend npm dependencies..."
    cd "$FRONTEND" && npm install --silent
    echo "[INFO] Frontend dependencies installed."
else
    echo "[INFO] Frontend node_modules found."
fi

# Create data directories
mkdir -p "$SCRIPT_DIR/azero_data/analyses"

# Start backend
echo "[INFO] Starting backend API on http://localhost:8000 ..."
cd "$BACKEND"
"$VENV/bin/uvicorn" assumption_zero.main:app --host 0.0.0.0 --port 8000 --reload &
BACKEND_PID=$!

# Wait for backend
sleep 2

# Start frontend
echo "[INFO] Starting frontend on http://localhost:5173 ..."
cd "$FRONTEND"
npm run dev &
FRONTEND_PID=$!

# Wait for Vite to compile
sleep 3

# Open browser
URL="http://localhost:5173"
echo "[INFO] Opening $URL ..."
if command -v xdg-open &>/dev/null; then
    xdg-open "$URL"
elif command -v open &>/dev/null; then
    open "$URL"
fi

echo ""
echo "╔══════════════════════════════════════════════════════════╗"
echo "║  ✓  Assumption Zero is running!                          ║"
echo "║                                                          ║"
echo "║  Frontend:  http://localhost:5173                        ║"
echo "║  Backend:   http://localhost:8000                        ║"
echo "║  API Docs:  http://localhost:8000/docs                   ║"
echo "║                                                          ║"
echo "║  Press Ctrl+C to stop both servers.                      ║"
echo "╚══════════════════════════════════════════════════════════╝"
echo ""

# Wait and cleanup on Ctrl+C
trap "echo ''; echo '[INFO] Shutting down...'; kill $BACKEND_PID $FRONTEND_PID 2>/dev/null; exit 0" INT TERM
wait $BACKEND_PID $FRONTEND_PID
