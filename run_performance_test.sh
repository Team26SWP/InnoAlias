#!/bin/bash

# InnoAlias Performance Test Runner
# This script sets up the environment and runs the performance test

set -e

echo "🚀 InnoAlias Performance Test Runner"
echo "======================================"

# Check if we're in the right directory
if [ ! -f "backend/app/main.py" ]; then
    echo "❌ Error: Please run this script from the InnoAlias project root"
    exit 1
fi

# Check if MongoDB is running
echo "📊 Checking MongoDB status..."
if ! systemctl is-active --quiet mongodb; then
    echo "⚠️  MongoDB is not running. Attempting to start it..."
    sudo systemctl start mongodb
    sleep 2
    if ! systemctl is-active --quiet mongodb; then
        echo "❌ Failed to start MongoDB. Please start it manually:"
        echo "   sudo systemctl start mongodb"
        exit 1
    fi
fi
echo "✅ MongoDB is running"

# Check if aiohttp is installed
echo "📦 Checking dependencies..."
if ! python -c "import aiohttp" 2>/dev/null; then
    echo "📥 Installing aiohttp..."
    pip install aiohttp
fi
echo "✅ Dependencies are installed"

# Check if backend server is running
echo "🔍 Checking if backend server is running..."
if ! curl -s http://localhost:8000/docs > /dev/null 2>&1; then
    echo "⚠️  Backend server is not running on port 8000"
    echo "🚀 Starting backend server in background..."
    python -m uvicorn backend.app.main:app --reload --host 0.0.0.0 --port 8000 > /dev/null 2>&1 &
    BACKEND_PID=$!
    echo "⏳ Waiting for server to start..."
    sleep 5
    
    # Check if server started successfully
    if ! curl -s http://localhost:8000/docs > /dev/null 2>&1; then
        echo "❌ Failed to start backend server"
        exit 1
    fi
    echo "✅ Backend server is running (PID: $BACKEND_PID)"
    echo "💡 To stop the server later, run: kill $BACKEND_PID"
else
    echo "✅ Backend server is already running"
    BACKEND_PID=""
fi

# Run the performance test
echo ""
echo "🧪 Running performance test..."
echo "================================"

# Get command line arguments
BASE_URL=${1:-"http://localhost:8000"}
ITERATIONS=${2:-10}

echo "📍 Testing URL: $BASE_URL"
echo "🔄 Iterations: $ITERATIONS"
echo ""

python docs/architecture/dynamic-view/performance-test.py "$BASE_URL" --iterations "$ITERATIONS"

echo ""
echo "✅ Performance test completed!"

# Cleanup
if [ ! -z "$BACKEND_PID" ]; then
    echo "🧹 Cleaning up..."
    echo "💡 Backend server is still running. To stop it, run: kill $BACKEND_PID"
fi 