#!/bin/bash
# Startup script for Profile Scout API

echo "🚀 Starting Profile Scout API..."

# Check if .env file exists
if [ ! -f .env ]; then
    echo "⚠️  Warning: .env file not found. Please copy .env.example to .env and add your API keys."
    echo "   cp .env.example .env"
    echo ""
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
echo "📚 Installing dependencies..."
pip install -r requirements.txt

# Start the server
echo "🌐 Starting FastAPI server on http://localhost:8000"
echo "📝 API Documentation available at http://localhost:8000/docs"
echo ""
python main.py