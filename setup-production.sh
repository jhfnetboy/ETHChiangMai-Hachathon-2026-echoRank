#!/bin/bash
# EchoRank One-Click Production Setup

echo "🚀 Welcome to EchoRank Production Setup"
echo "--------------------------------------"

# Check for Docker
if ! command -v docker &> /dev/null; then
    echo "❌ Error: Docker is not installed. Please install Docker Desktop for Mac."
    exit 1
fi

# Create .env if not exists
if [ ! -f .env ]; then
    echo "📝 Creating configuration..."
    read -p "Enter Telegram BOT_TOKEN: " bot_token
    read -p "Enter Google GEMINI_API_KEY: " gemini_key
    
    cat > .env <<EOF
BOT_TOKEN=$bot_token
GEMINI_API_KEY=$gemini_key
POSTGRES_USER=postgres
POSTGRES_PASSWORD=echorank_pass
POSTGRES_DB=echorank_crawler
EOF
    echo "✅ .env created."
else
    echo "ℹ️  Using existing .env file."
fi

echo "📦 Starting services via Docker Compose..."
docker-compose up -d --build

echo "--------------------------------------"
echo "✅ EchoRank is starting up!"
echo "AI Service: http://localhost:8001/health"
echo "Logs: docker-compose logs -f"
echo "--------------------------------------"
