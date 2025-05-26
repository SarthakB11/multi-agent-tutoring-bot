#!/bin/bash

# Script to run the Multi-Agent AI Tutoring System

# Check if .env file exists
if [ ! -f .env ]; then
  echo "Error: .env file not found. Please create one based on .env.example"
  exit 1
fi

# Check if MongoDB is running
check_mongodb() {
  echo "Checking MongoDB connection..."
  if command -v mongosh &> /dev/null; then
    if ! mongosh --eval "db.runCommand({ ping: 1 })" > /dev/null 2>&1; then
      echo "Warning: MongoDB is not running. Please start MongoDB first."
      echo "You can start MongoDB with: sudo systemctl start mongod"
      read -p "Continue anyway? (y/n): " -n 1 -r
      echo
      if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
      fi
    else
      echo "MongoDB is running."
    fi
  else
    echo "Warning: mongosh command not found. Cannot verify MongoDB connection."
    echo "Please ensure MongoDB is installed and running."
    read -p "Continue anyway? (y/n): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
      exit 1
    fi
  fi
}

# Function to run the backend
run_backend() {
  echo "Starting backend server..."
  cd "$(dirname "$0")"
  python -m uvicorn src.api.main:app --host 0.0.0.0 --port 8000 --reload
}

# Function to run the frontend
run_frontend() {
  echo "Starting Next.js frontend server..."
  cd "$(dirname "$0")/frontend-next"
  npm run dev
}

# Check command line arguments
if [ "$1" == "backend" ]; then
  check_mongodb
  run_backend
elif [ "$1" == "frontend" ]; then
  run_frontend
elif [ "$1" == "mongodb" ]; then
  echo "Starting MongoDB..."
  if command -v systemctl &> /dev/null; then
    sudo systemctl start mongod
    echo "MongoDB started. Status:"
    sudo systemctl status mongod --no-pager
  else
    echo "Cannot start MongoDB automatically. Please start it manually."
    exit 1
  fi
else
  # Run both in separate terminals if available
  check_mongodb
  
  if command -v gnome-terminal &> /dev/null; then
    gnome-terminal -- bash -c "cd '$(dirname "$0")' && ./run.sh backend; exec bash"
    gnome-terminal -- bash -c "cd '$(dirname "$0")' && ./run.sh frontend; exec bash"
  elif command -v xterm &> /dev/null; then
    xterm -e "cd '$(dirname "$0")' && ./run.sh backend" &
    xterm -e "cd '$(dirname "$0")' && ./run.sh frontend" &
  else
    echo "Please run the backend and frontend separately:"
    echo "  ./run.sh backend"
    echo "  ./run.sh frontend"
  fi
fi
