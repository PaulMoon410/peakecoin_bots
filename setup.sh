#!/bin/bash

# PeakeCoin Bot Server Setup Script
# This script sets up the environment and starts the bot server

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${GREEN}======================================${NC}"
echo -e "${GREEN}  PeakeCoin Bot Server Setup${NC}"
echo -e "${GREEN}======================================${NC}"

# Check if Python is installed
if ! command -v python3 &> /dev/null; then
    echo -e "${RED}Error: Python 3 is not installed${NC}"
    echo "Please install Python 3.11 or higher"
    exit 1
fi

# Check Python version
PYTHON_VERSION=$(python3 -c 'import sys; print(".".join(map(str, sys.version_info[:2])))')
echo -e "${YELLOW}Python version: ${PYTHON_VERSION}${NC}"

# Create virtual environment if it doesn't exist
if [ ! -d "venv" ]; then
    echo -e "${YELLOW}Creating virtual environment...${NC}"
    python3 -m venv venv
fi

# Activate virtual environment
echo -e "${YELLOW}Activating virtual environment...${NC}"
source venv/bin/activate

# Install requirements
echo -e "${YELLOW}Installing requirements...${NC}"
pip install -r requirements.txt

echo -e "${GREEN}Setup complete!${NC}"
echo -e "${YELLOW}Available options:${NC}"
echo "1. Run GUI version: python main.py"
echo "2. Run command-line version: python peake_droid.py"
echo ""
echo -e "${YELLOW}For server deployment:${NC}"
echo "- Copy this entire directory to your server"
echo "- Run this setup script on the server"
echo "- Use screen or tmux to run the bot in background"
echo "- Example: screen -S peakebot python peake_droid.py"
