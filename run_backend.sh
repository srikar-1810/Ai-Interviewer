#!/bin/bash
echo "Starting backend on http://127.0.0.1:8000"
echo "Keep this terminal open while using the app."
python3.11 -m uvicorn app.main:app --host 127.0.0.1 --port 8000
