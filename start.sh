#!/bin/bash
# Start both servers for InterviewAI

# Kill existing processes
pkill -f "uvicorn app.main" 2>/dev/null
pkill -f "node.*vite" 2>/dev/null
sleep 2

# Start backend
cd backend
nohup python3.11 -m uvicorn app.main:app --host 127.0.0.1 --port 8000 > /tmp/interview_backend.log 2>&1 &
BACKEND_PID=$!
echo "Backend started (PID: $BACKEND_PID)"

# Start frontend
cd ../frontend
nohup npm run dev > /tmp/interview_frontend.log 2>&1 &
FRONTEND_PID=$!
echo "Frontend started (PID: $FRONTEND_PID)"

sleep 5

# Verify
echo "=== Checking Backend ==="
curl -s http://127.0.0.1:8000/api/health | python3.11 -m json.tool

echo ""
echo "=== Checking Frontend ==="
curl -s http://127.0.0.1:5173 | grep -o "<title>.*</title>"

echo ""
echo "=== Servers should now be running ==="
echo "Open: http://localhost:5173"
echo "Backend: http://localhost:8000"
