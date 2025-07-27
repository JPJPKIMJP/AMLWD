#!/bin/bash

echo "Starting AI Image Generator locally..."

# Install backend dependencies
echo "Setting up backend..."
cd backend
pip install -r requirements.txt

# Start backend in background
echo "Starting backend API on http://localhost:8000"
python main.py &
BACKEND_PID=$!

# Simple Python HTTP server for frontend
echo "Starting frontend on http://localhost:3000"
cd ../frontend
python3 -m http.server 3000 &
FRONTEND_PID=$!

echo ""
echo "✅ Services started!"
echo "Frontend: http://localhost:3000"
echo "Backend API: http://localhost:8000"
echo ""
echo "Press Ctrl+C to stop all services"

# Wait and cleanup on exit
trap "kill $BACKEND_PID $FRONTEND_PID 2>/dev/null" EXIT
wait