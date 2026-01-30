#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# 0. Kill existing processes
echo "[0/3] Stopping all services..."
"${ROOT_DIR}/kill-all.sh" || true
echo "Waiting 2s for processes to exit..."
sleep 2

# 1. Restart AI service
echo "[1/3] Starting AI service..."
cd "${ROOT_DIR}/services/ai"

# Determine Python interpreter
PYTHON_CMD="python3"
if [ -f "${ROOT_DIR}/.python-version" ]; then
  PY_VER=$(cat "${ROOT_DIR}/.python-version")
  PYENV_BIN="$HOME/.pyenv/versions/${PY_VER}/bin/python"
  if [ -x "$PYENV_BIN" ]; then
    echo "Using pyenv python: $PYENV_BIN"
    PYTHON_CMD="$PYENV_BIN"
  fi
fi

if [ ! -d ".venv" ]; then
  echo "Creating Python venv for AI service..."
  "$PYTHON_CMD" -m venv .venv
fi
# Try to install dependencies (may fail on some systems, so we allow failure for non-critical deps)
.venv/bin/pip install -r requirements.txt >/dev/null 2>&1 || true

# Start in background
nohup .venv/bin/python app.py > ai_service.log 2>&1 &
echo "AI Service started (PID $!). Log: services/ai/ai_service.log"

# 2. Restart Node backend
echo "[2/3] Starting Node backend..."
cd "${ROOT_DIR}"
nohup pnpm -C apps/server dev > backend.log 2>&1 &
echo "Backend started (PID $!). Log: backend.log"

# 3. Restart Telegram bot
echo "[3/3] Starting Telegram bot..."
cd "${ROOT_DIR}/services/bot"
if [ ! -d ".venv" ]; then
  echo "Creating Python venv for Bot service..."
  "$PYTHON_CMD" -m venv .venv
fi
.venv/bin/pip install -r requirements.txt >/dev/null 2>&1 || true

# Start in background
nohup .venv/bin/python bot.py > bot_service.log 2>&1 &
echo "Bot Service started (PID $!). Log: services/bot/bot_service.log"

echo ""
echo "✅ All services restarted!"
echo "AI API: http://localhost:8001"
echo "Backend: http://localhost:8000"
echo "Web: http://localhost:5173 (run 'pnpm dev:web' separately)"
