#!/bin/bash
# Kill any existing processes
pkill -f "uvicorn app.main" 2>/dev/null
pkill -f "node.*vite" 2>/dev/null
sleep 1

# Start backend
cd backend
nohup python3.11 -m uvicorn app.main:app --host 127.0.0.1 --port 8000 > /tmp/backend.log 2>&1 &
echo "Backend PID: $!" >> /tmp/server_pids.txt

# Start frontend
cd ../frontend
nohup npm run dev > /tmp/frontend.log 2>&1 &
echo "Frontend PID: $!" >> /tmp/server_pids.txt

sleep 3

# Verify
echo "=== Backend Health ==="
curl -s http://127.0.0.1:8000/api/health || echo "Backend failed"
echo "=== Frontend ==="
curl -s http://127.0.0.1:5173 | grep -o "<title>.*</title>" || echo "Frontend failed"

echo "=== Both servers should now be running ==="
echo "Backend: http://localhost:8000"
echo "Frontend: http://localhost:5173"
