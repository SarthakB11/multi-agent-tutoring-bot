#!/bin/bash

# Colors for better readability
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${GREEN}=== Multi-Agent AI Tutoring System Setup ===${NC}"
echo -e "This script will set up the development environment for both backend and frontend."

# Check if Python is installed
if command -v python3 &>/dev/null; then
    PYTHON_VERSION=$(python3 --version)
    echo -e "${GREEN}✓${NC} $PYTHON_VERSION is installed"
else
    echo -e "${RED}✗ Python 3 is not installed. Please install Python 3.10 or higher.${NC}"
    exit 1
fi

# Check if Node.js is installed
if command -v node &>/dev/null; then
    NODE_VERSION=$(node --version)
    echo -e "${GREEN}✓${NC} Node.js $NODE_VERSION is installed"
else
    echo -e "${RED}✗ Node.js is not installed. Please install Node.js 18 or higher.${NC}"
    exit 1
fi

# Check if npm is installed
if command -v npm &>/dev/null; then
    NPM_VERSION=$(npm --version)
    echo -e "${GREEN}✓${NC} npm $NPM_VERSION is installed"
else
    echo -e "${RED}✗ npm is not installed. Please install npm.${NC}"
    exit 1
fi

# Check if MongoDB is installed/running
echo -e "${YELLOW}Checking MongoDB connection...${NC}"
if command -v mongod &>/dev/null; then
    echo -e "${GREEN}✓${NC} MongoDB is installed"
else
    echo -e "${YELLOW}⚠ MongoDB is not installed locally. Make sure you have a MongoDB instance available.${NC}"
fi

# Create virtual environment
echo -e "\n${YELLOW}Setting up Python virtual environment...${NC}"
if [ ! -d "venv" ]; then
    python3 -m venv venv
    echo -e "${GREEN}✓${NC} Virtual environment created"
else
    echo -e "${GREEN}✓${NC} Virtual environment already exists"
fi

# Activate virtual environment
echo -e "${YELLOW}Activating virtual environment...${NC}"
source venv/bin/activate
echo -e "${GREEN}✓${NC} Virtual environment activated"

# Install Python dependencies
echo -e "\n${YELLOW}Installing Python dependencies...${NC}"
pip install -r requirements.txt
echo -e "${GREEN}✓${NC} Python dependencies installed"

# Set up React frontend
echo -e "\n${YELLOW}Setting up React frontend...${NC}"
if [ -d "frontend" ]; then
    cd frontend
    echo -e "${YELLOW}Installing React dependencies...${NC}"
    npm install
    echo -e "${GREEN}✓${NC} React dependencies installed"
    cd ..
else
    echo -e "${RED}✗ Frontend directory not found.${NC}"
fi

# Set up Next.js frontend
echo -e "\n${YELLOW}Setting up Next.js frontend...${NC}"
if [ -d "frontend-next" ]; then
    cd frontend-next
    echo -e "${YELLOW}Installing Next.js dependencies...${NC}"
    npm install
    echo -e "${GREEN}✓${NC} Next.js dependencies installed"
    cd ..
else
    echo -e "${RED}✗ Frontend-next directory not found.${NC}"
fi

# Check if .env file exists, if not create from example
if [ ! -f ".env" ]; then
    if [ -f ".env.example" ]; then
        cp .env.example .env
        echo -e "\n${YELLOW}⚠ .env file created from .env.example. Please update it with your API keys and MongoDB connection string.${NC}"
    else
        echo -e "\n${YELLOW}Creating basic .env file...${NC}"
        cat > .env << EOL
# API Keys
GEMINI_API_KEY=your_gemini_api_key_here

# MongoDB Configuration
MONGODB_URI=mongodb://localhost:27017/tutoring_bot

# Application Settings
DEBUG=True
LOG_LEVEL=INFO
EOL
        echo -e "${GREEN}✓${NC} Basic .env file created. Please update it with your actual API keys and MongoDB connection string."
    fi
else
    echo -e "\n${GREEN}✓${NC} .env file already exists"
fi

echo -e "\n${GREEN}=== Setup Complete ===${NC}"
echo -e "To run the application:"
echo -e "1. Activate the virtual environment: ${YELLOW}source venv/bin/activate${NC}"
echo -e "2. Start the backend: ${YELLOW}uvicorn src.api.main:app --reload${NC}"
echo -e "3. In a separate terminal, start the frontend:"
echo -e "   - React: ${YELLOW}cd frontend && npm run dev${NC}"
echo -e "   - Next.js: ${YELLOW}cd frontend-next && npm run dev${NC}"
echo -e "4. Alternatively, use the run script: ${YELLOW}./run.sh${NC}"
echo -e "\nHappy coding! 🚀"
