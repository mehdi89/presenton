#!/bin/bash

# Start FastAPI server for Presenton
# This script starts the FastAPI backend server needed for export functionality

echo "Starting Presenton FastAPI backend..."
echo "Make sure you have Python 3.11 and uv installed"
echo ""

cd servers/fastapi

# Check if uv is installed
if ! command -v uv &> /dev/null; then
    echo "❌ 'uv' is not installed. Please install it first:"
    echo "   curl -LsSf https://astral.sh/uv/install.sh | sh"
    exit 1
fi

# Install dependencies if needed
if [ ! -d ".venv" ]; then
    echo "📦 Installing Python dependencies..."
    uv sync
fi

# Start the FastAPI server
echo "🚀 Starting FastAPI server on http://localhost:8000"
echo "   Press Ctrl+C to stop"
echo ""

uv run uvicorn api.main:app --host 0.0.0.0 --port 8000
