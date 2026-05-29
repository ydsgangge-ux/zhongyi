#!/usr/bin/env bash
set -e

cd "$(dirname "$0")"

ROOT=$(pwd)
BACKEND="$ROOT/backend"
VENV="$BACKEND/venv"

echo "============================================"
echo "   TCM AI Health Advisor - TUI Mode"
echo "============================================"
echo ""

if ! command -v python3 &>/dev/null; then
    echo "[ERROR] Python 3 not found. Please install Python 3.11+"
    exit 1
fi

if [ ! -d "$VENV" ]; then
    echo "[INFO] Creating Python virtual environment..."
    python3 -m venv "$VENV"
fi

echo "[INFO] Checking backend dependencies..."
"$VENV/bin/pip" install -q -r "$BACKEND/requirements.txt"

if [ ! -f "$BACKEND/data/config.json" ]; then
    echo ""
    echo "[WARN] No API key configured."
    echo "       Press S key in the app to configure."
    echo ""
    sleep 2
fi

echo "[INFO] Launching TUI..."
echo ""
echo "  Controls:"
echo "    S     - Open Settings"
echo "    Q     - Quit"
echo "    Ctrl+A - Start Analysis (in inquiry)"
echo "    R     - Restart (in result)"
echo ""

cd "$BACKEND"
"$VENV/bin/python" run_tui.py