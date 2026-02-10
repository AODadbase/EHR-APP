#!/bin/bash
echo "Stopping old servers..."
lsof -ti:8000,3000 | xargs kill -9 2>/dev/null

# Backend
echo "Starting Backend..."
cd ehr-data-pipeline-backend
source venv/bin/activate
python3 -m uvicorn api_server:app --reload --host 0.0.0.0 --port 8000 > ../backend.log 2>&1 &
BACKEND_PID=$!

sleep 3

# Frontend
echo "Starting Frontend..."
cd ../ehr-frontend-website
npm run dev

kill $BACKEND_PID