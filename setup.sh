#!/bin/bash

# Stop on error
set -e

echo "Beginning Project Setup"

# --- BACKEND SETUP ---
echo "Setting up Python Backend"
cd ehr-data-pipeline-backend

if [ ! -d "venv" ]; then
    echo "   Creating virtual environment..."
    python3 -m venv venv
fi

# Activate and Install
source venv/bin/activate
echo "   Installing Python requirements..."
pip install -r requirements.txt

# --- FRONTEND SETUP ---
echo "Setting up React Frontend..."
cd ../ehr-frontend-website

if [ ! -d "node_modules" ]; then
    echo "   Installing Node modules (this may take a moment)..."
    npm install
else
    echo "   Node modules already installed. Skipping..."
fi

echo "Setup Complete! You can now run: ./start_app.sh"