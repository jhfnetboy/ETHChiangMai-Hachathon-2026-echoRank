#!/usr/bin/env bash
set -euo pipefail

# kill dev servers and bot/ai processes for echoRank
ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

kill_by_pattern() {
  local pattern="$1"
  pgrep -f "$pattern" | xargs -r kill || true
}

kill_by_port() {
  local port="$1"
  lsof -ti tcp:"$port" | xargs -r kill || true
}

# Node server (tsx/dev/start)
kill_by_pattern "pnpm -C apps/server dev"
kill_by_pattern "tsx src/index.ts"
kill_by_pattern "node dist/index.js"

# Python AI service
kill_by_pattern "${ROOT_DIR}/services/ai/.venv/bin/python app.py"
kill_by_pattern "python3 services/ai/app.py"
kill_by_pattern "uvicorn"

# Telegram bot
kill_by_pattern "${ROOT_DIR}/services/bot/.venv/bin/python bot.py"
kill_by_pattern "python3 services/bot/bot.py"

# Common dev ports
kill_by_port 8000  # Node backend
kill_by_port 8001  # AI service
kill_by_port 5173  # Web dev

echo "echoRank: attempted to terminate all dev processes."
