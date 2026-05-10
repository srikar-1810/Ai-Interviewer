#!/bin/bash
echo "Starting backend on http://localhost:8000"
echo "Keep this terminal open while using the app."
python3.11 -m uvicorn app.main:app --host 0.0.0.0 --port 8000
