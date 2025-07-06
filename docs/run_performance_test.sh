#!/bin/bash

# InnoAlias Performance Test Runner
# This script sets up the environment and runs the performance test

set -e

echo "🚀 InnoAlias Performance Test Runner"
echo "======================================"

cd ..

# Check if we're in the right directory
if [ ! -f "backend/app/main.py" ]; then
    echo "❌ Error: Please run this script from the InnoAlias project root"
    exit 1
fi

# 1. Start MongoDB
echo "1️⃣ Starting MongoDB..."
sudo systemctl start mongodb

echo "✅ MongoDB is running or started"

# 2. Install dependencies
echo "2️⃣ Installing backend dependencies from requirements.txt..."
python -m pip install -r backend/requirements.txt

echo "✅ Dependencies are installed"

# 3. Start backend server
# (User should run this in a separate terminal if they want to keep the server running)
echo "3️⃣ Starting backend server..."
echo "   (Stop this process with Ctrl+C when ready to run the performance test)"
echo "   Or run the performance test in a new terminal."
echo "   Command: python -m uvicorn backend.app.main:app --reload --port 8000"
python -m uvicorn backend.app.main:app --reload --port 8000

# 4. Run performance test (examples)
echo "\n🧪 To run the performance test, use one of the following commands in a new terminal:"
echo "   python docs/architecture/dynamic-view/performance-test.py http://localhost:8000"
echo "   python docs/architecture/dynamic-view/performance-test.py http://localhost:8000 --iterations 5"