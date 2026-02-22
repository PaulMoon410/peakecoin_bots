#!/bin/bash

# PeakeCoin Bot Launcher
# Quick launcher for the PeakeCoin trading bot

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

print_header() {
    echo -e "${BLUE}=======================================${NC}"
    echo -e "${BLUE}  🚀 PeakeCoin Bot Launcher${NC}"
    echo -e "${BLUE}=======================================${NC}"
}

print_status() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

activate_venv() {
    if [ -d "venv" ]; then
        print_status "Activating virtual environment..."
        source venv/bin/activate
    fi
}

main() {
    print_header
    
    echo "Select an option:"
    echo "1) Run Desktop GUI (main.py)"
    echo "2) Run Server GUI (main_server.py) - Enhanced GUI with continuous mode"
    echo "3) Run Command Line (peake_droid.py) - Single run"
    echo "4) Run Server Mode (server_bot.py) - Continuous trading"
    echo "5) Start Web Interface (web_interface.py)"
    echo "6) Run in Background (screen)"
    echo "7) View Background Process"
    echo "8) Stop Background Process"
    echo "0) Exit"
    
    read -p "Enter your choice (0-8): " choice
    
    activate_venv
    
    case $choice in
        1)
            print_status "Starting Desktop GUI..."
            python main.py
            ;;
        2)
            print_status "Starting Enhanced Server GUI..."
            python main_server.py
            ;;
        3)
            print_status "Starting Command Line Interface (single run)..."
            python peake_droid.py
            ;;
        4)
            print_status "Starting Server Mode (continuous trading)..."
            python server_bot.py
            ;;
        5)
            print_status "Starting Web Interface..."
            print_status "Open http://localhost:8080 in your browser"
            python web_interface.py
            ;;
        6)
            print_status "Starting bot in background..."
            screen -S peakebot -d -m bash -c "source venv/bin/activate; python server_bot.py"
            print_status "Bot started in background. Use option 7 to view."
            ;;
        7)
            print_status "Connecting to background process..."
            screen -r peakebot
            ;;
        8)
            print_status "Stopping background process..."
            screen -X -S peakebot quit
            print_status "Background process stopped."
            ;;
        0)
            print_status "Goodbye!"
            exit 0
            ;;
        *)
            echo "Invalid option. Please try again."
            main
            ;;
    esac
}

# Check if we're in the right directory
if [ ! -f "main.py" ] || [ ! -f "peake_droid.py" ]; then
    echo "Error: Please run this script from the PeakeCoin bot directory"
    exit 1
fi

main
