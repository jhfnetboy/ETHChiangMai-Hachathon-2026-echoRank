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
CONDA_PYTHON="/usr/local/Caskroom/miniconda/base/envs/echorank_v2/bin/python"

if [ -f "${ROOT_DIR}/.python-version" ]; then
  PY_VER=$(cat "${ROOT_DIR}/.python-version")
  PYENV_BIN="$HOME/.pyenv/versions/${PY_VER}/bin/python"
  if [ -x "$PYENV_BIN" ]; then
    echo "Using pyenv python: $PYENV_BIN"
    PYTHON_CMD="$PYENV_BIN"
  fi
fi

# Override with Conda for AI service if available (Special case for Mac dependencies)
if [ -x "$CONDA_PYTHON" ]; then
  echo "Using optimized Conda python for AI: $CONDA_PYTHON"
  PYTHON_CMD="$CONDA_PYTHON"
  echo "Running AI service directly with Conda environment..."
  nohup "$PYTHON_CMD" app.py > ai_service.log 2>&1 &
else
  if [ ! -d ".venv" ]; then
    echo "Creating Python venv for AI service..."
    "$PYTHON_CMD" -m venv .venv
  fi
  # Try to install dependencies
  .venv/bin/pip install -r requirements.txt >/dev/null 2>&1 || true
  # Start in background
  nohup .venv/bin/python app.py > ai_service.log 2>&1 &
fi
echo "AI Service started (PID $!). Log: services/ai/ai_service.log"

# Function to wait for a service to be ready
wait_for_service() {
    local url="$1"
    local name="$2"
    local max_retries=45
    local count=0
    
    echo -n "Waiting for $name to be ready..."
    until curl -s "$url" > /dev/null; do
        sleep 2
        count=$((count+1))
        echo -n "."
        if [ $count -ge $max_retries ]; then
            echo " Timeout!"
            echo "❌ $name failed to start within $((max_retries*2)) seconds."
            return 1
        fi
    done
    echo " ✅ Ready!"
}

# Wait for AI completely (Model loading takes time)
wait_for_service "http://localhost:8001/status" "AI Service (Loading Models...)"

# 2. Restart Node backend
echo "[2/3] Starting Node backend..."
cd "${ROOT_DIR}"
nohup pnpm -C apps/server dev > backend.log 2>&1 &
echo "Backend started (PID $!). Log: backend.log"

wait_for_service "http://localhost:8000/status" "Node Backend"

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

# Check if Bot is still alive after a few seconds
sleep 3
if ps -p $! > /dev/null; then
    echo "Bot Process is running."
else
    echo "❌ Bot Process died immediately. Check logs."
fi

echo ""
echo "✅ All services restarted & verified!"
echo "AI API: http://localhost:8001"
echo "Backend: http://localhost:8000"
echo "Web: http://localhost:5173 (run 'pnpm dev:web' separately)"
