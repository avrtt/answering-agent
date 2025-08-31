#!/bin/bash

# Answering Agent Startup Script
# This script sets up and starts the answering agent bot

echo "🤖 Starting Answering Agent..."
echo "================================"

# Check if Python is installed
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 is not installed. Please install Python 3.8+ first."
    exit 1
fi

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "📦 Creating virtual environment..."
    python3 -m venv venv
fi

# Activate virtual environment
echo "🔧 Activating virtual environment..."
source venv/bin/activate

# Install dependencies
echo "📥 Installing dependencies..."
pip install -r requirements.txt

# Check if .env file exists
if [ ! -f ".env" ]; then
    echo "⚠️  No .env file found. Please create one based on env.example"
    echo "   Copy env.example to .env and configure your settings"
    exit 1
fi

# Check required environment variables
source .env

if [ -z "$TELEGRAM_BOT_TOKEN" ] || [ "$TELEGRAM_BOT_TOKEN" = "your_telegram_bot_token_here" ]; then
    echo "❌ TELEGRAM_BOT_TOKEN not configured in .env file"
    exit 1
fi

if [ -z "$TELEGRAM_CHAT_ID" ] || [ "$TELEGRAM_CHAT_ID" = "your_telegram_chat_id_here" ]; then
    echo "❌ TELEGRAM_CHAT_ID not configured in .env file"
    exit 1
fi

if [ -z "$OPENAI_API_KEY" ] || [ "$OPENAI_API_KEY" = "your_openai_api_key_here" ]; then
    echo "❌ OPENAI_API_KEY not configured in .env file"
    exit 1
fi

echo "✅ Configuration looks good!"
echo "🚀 Starting the bot..."

# Start the application
python main.py
