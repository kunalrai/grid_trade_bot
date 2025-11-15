#!/bin/bash

# SOL/USDT Grid Trading Bot - Server Startup Script

echo "=================================================="
echo "  SOL/USDT Grid Trading Bot - CoinDCX Edition"
echo "=================================================="
echo ""

# Check if .env exists
if [ ! -f .env ]; then
    echo "⚠️  Error: .env file not found!"
    echo "Please copy .env.example to .env and configure your API keys"
    echo ""
    echo "Run: cp .env.example .env"
    echo "Then edit .env with your credentials"
    exit 1
fi

# Check if requirements are installed
echo "📦 Checking dependencies..."
pip install -r requirements.txt --quiet

if [ $? -ne 0 ]; then
    echo "⚠️  Error installing dependencies"
    exit 1
fi

echo "✅ Dependencies installed"
echo ""

# Start the API server
echo "🚀 Starting API server on http://localhost:5000"
echo ""
echo "Web UI will be available at:"
echo "   http://localhost:8080"
echo ""
echo "To view the UI, run in another terminal:"
echo "   cd frontend && python -m http.server 8080"
echo ""
echo "Press Ctrl+C to stop the server"
echo ""
echo "=================================================="
echo ""

cd backend
python api_server.py
