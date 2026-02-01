#!/usr/bin/env bash
set -euo pipefail

# kill dev servers and bot/ai processes for echoRank
ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

kill_by_pattern() {
  local pattern="$1"
  # Use pgrep to find pids, then kill them. 
  # -f matches against full command line
  pids=$(pgrep -f "$pattern" || true)
  if [ -n "$pids" ]; then
    echo "Killing processes for pattern '$pattern': $pids"
    echo "$pids" | xargs kill
  else
    echo "No processes found for '$pattern'"
  fi
}

kill_by_port() {
  local port="$1"
  pids=$(lsof -ti tcp:"$port" || true)
  if [ -n "$pids" ]; then
     echo "Killing process on port $port: $pids"
     echo "$pids" | xargs kill
  else
     echo "No process found on port $port"
  fi
}

echo "Stopping EchoRank services..."

# Node server (tsx/dev/start)
kill_by_pattern "pnpm -C apps/server dev"
kill_by_pattern "apps/server"
kill_by_port 8000

# Python AI service
kill_by_pattern "app.py"
kill_by_port 8001

# Telegram bot
kill_by_pattern "bot.py"

# Web frontend (optional, usually run separately but good to have option)
# kill_by_port 5173

echo "Cleanup complete."
