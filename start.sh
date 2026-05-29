#!/usr/bin/env bash
set -e

cd "$(dirname "$0")"

ROOT=$(pwd)
BACKEND="$ROOT/backend"
FRONTEND="$ROOT/frontend"
VENV="$BACKEND/venv"
PORT=5328

echo "============================================"
echo "   TCM AI Health Advisor - Quick Start"
echo "============================================"
echo ""

# Check Python
if ! command -v python3 &>/dev/null; then
    echo "[ERROR] Python 3 not found. Please install Python 3.11+"
    echo "       Install: https://python.org/downloads/"
    exit 1
fi

# Check Node.js
if ! command -v node &>/dev/null; then
    echo "[ERROR] Node.js not found. Please install Node.js 18+"
    echo "       Install: https://nodejs.org/"
    exit 1
fi

# Setup backend venv
if [ ! -d "$VENV" ]; then
    echo "[INFO] Creating Python virtual environment..."
    python3 -m venv "$VENV"
fi

echo "[INFO] Checking backend dependencies..."
"$VENV/bin/pip" install -q -r "$BACKEND/requirements.txt"

# Install & build frontend
if [ ! -d "$FRONTEND/node_modules" ]; then
    echo "[INFO] Installing frontend dependencies..."
    cd "$FRONTEND"
    npm install
    cd "$ROOT"
fi

if [ ! -d "$FRONTEND/dist" ] || [ -z "$(ls -A "$FRONTEND/dist")" ]; then
    echo "[INFO] Building frontend..."
    cd "$FRONTEND"
    npm run build
    cd "$ROOT"
else
    echo "[INFO] Frontend already built."
fi

# Check config
if [ ! -f "$BACKEND/data/config.json" ]; then
    echo ""
    echo "[WARN] No API key configured."
    echo "       Visit http://localhost:$PORT/settings after startup."
    echo ""
fi

echo ""
echo "============================================"
echo "  Starting server..."
echo "============================================"
echo ""

cd "$BACKEND"
"$VENV/bin/python" -m uvicorn main:app --host 0.0.0.0 --port "$PORT" &
BACKEND_PID=$!

echo ""
echo "============================================"
echo "  Server started!"
echo "============================================"
echo ""
echo "  Web:       http://localhost:$PORT"
echo "  API Docs:  http://localhost:$PORT/docs"
echo "  Settings:  http://localhost:$PORT/settings"
echo ""
echo "  Press Ctrl+C to stop"
echo ""

trap "kill $BACKEND_PID 2>/dev/null; echo ''; echo '[INFO] All services stopped.'; exit 0" SIGINT SIGTERM

# Open browser
sleep 3
if command -v xdg-open &>/dev/null; then
    xdg-open "http://localhost:$PORT"
elif command -v open &>/dev/null; then
    open "http://localhost:$PORT"
fi

wait $BACKEND_PID