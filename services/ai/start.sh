#!/bin/bash
# start.sh - 启动 EchoRank AI Backend 服务

echo "=================================="
echo "EchoRank AI Backend Service"
echo "=================================="
echo ""

# 检查 Python 版本
python3 --version

# 检查 .env 文件
if [ ! -f .env ]; then
    echo "⚠️  Warning: .env file not found!"
    echo "Please run: python scripts/generate_keys.py"
    echo "Or copy .env.example to .env and fill in the values"
    exit 1
fi

# 检查依赖
echo "Checking dependencies..."
pip3 list | grep -q fastapi
if [ $? -ne 0 ]; then
    echo "Installing dependencies..."
    pip3 install -r requirements.txt
fi

# 启动服务
echo ""
echo "Starting service..."
echo "API will be available at: http://localhost:8001"
echo "API documentation at: http://localhost:8001/docs"
echo ""

python3 app.py