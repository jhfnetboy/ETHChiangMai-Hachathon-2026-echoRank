#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

"${ROOT_DIR}/kill-all.sh" || true

# Restart AI service
echo "[1/3] Starting AI service..."
cd "${ROOT_DIR}/services/ai"
if [ ! -d ".venv" ]; then
  python3 -m venv .venv
fi
.venv/bin/python -m pip install -r requirements.txt >/dev/null 2>&1 || true
nohup .venv/bin/python app.py >/dev/null 2>&1 &

# Restart Node backend
echo "[2/3] Starting Node backend..."
cd "${ROOT_DIR}"
nohup pnpm -C apps/server dev >/dev/null 2>&1 &

# Restart Telegram bot
echo "[3/3] Starting Telegram bot..."
cd "${ROOT_DIR}/services/bot"
if [ ! -d ".venv" ]; then
  python3 -m venv .venv
fi
.venv/bin/python -m pip install -r requirements.txt >/dev/null 2>&1 || true
nohup .venv/bin/python bot.py >/dev/null 2>&1 &

echo "kill and restart done."
