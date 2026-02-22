#!/bin/bash

# PeakeCoin Bot - Simple Server Deployment Script
# This script helps you quickly deploy the bot on a fresh server

set -e

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
RED='\033[0;31m'
NC='\033[0m'

print_header() {
    echo -e "${BLUE}=======================================${NC}"
    echo -e "${BLUE}  🚀 PeakeCoin Bot Server Deployer${NC}"
    echo -e "${BLUE}=======================================${NC}"
}

print_status() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

check_system() {
    print_status "Checking system requirements..."
    
    # Check if we're on Linux
    if [[ "$OSTYPE" != "linux-gnu"* ]]; then
        print_warning "This script is designed for Linux. For other systems, see SERVER_DEPLOYMENT.md"
    fi
    
    # Check Python
    if ! command -v python3 &> /dev/null; then
        print_error "Python 3 is required. Installing..."
        sudo apt update
        sudo apt install -y python3 python3-pip python3-venv
    fi
    
    # Check screen
    if ! command -v screen &> /dev/null; then
        print_status "Installing screen for background operation..."
        sudo apt install -y screen
    fi
    
    print_status "System check complete ✅"
}

setup_bot() {
    print_status "Setting up PeakeCoin bot..."
    
    # Run setup script if it exists
    if [ -f "setup.sh" ]; then
        chmod +x setup.sh
        ./setup.sh
    else
        print_status "Running manual setup..."
        python3 -m venv venv
        source venv/bin/activate
        pip install -r requirements.txt
    fi
    
    print_status "Bot setup complete ✅"
}

show_menu() {
    echo ""
    echo "Choose deployment option:"
    echo "1) Run bot interactively (test mode)"
    echo "2) Run bot in background (production mode)"
    echo "3) Set up as system service (auto-start)"
    echo "4) Just setup, don't start"
    echo "0) Exit"
    echo ""
    read -p "Enter your choice (0-4): " choice
}

run_interactive() {
    print_status "Starting bot in interactive mode..."
    print_status "You can stop it anytime with Ctrl+C"
    echo ""
    source venv/bin/activate
    python server_bot.py
}

run_background() {
    print_status "Starting bot in background using screen..."
    
    # Kill existing session if it exists
    screen -S peakebot -X quit 2>/dev/null || true
    
    # Start new session
    screen -S peakebot -d -m bash -c "source venv/bin/activate; python server_bot.py"
    
    print_status "Bot started in background! ✅"
    echo ""
    echo -e "${YELLOW}Useful commands:${NC}"
    echo "  View bot:    screen -r peakebot"
    echo "  Stop bot:    screen -X -S peakebot quit"
    echo "  List bots:   screen -ls"
    echo ""
    print_status "Bot is now running 24/7. You can safely close this terminal."
}

setup_service() {
    print_status "Setting up systemd service..."
    
    BOT_PATH=$(pwd)
    USER=$(whoami)
    
    # Create service file
    sudo tee /etc/systemd/system/peakebot.service > /dev/null <<EOF
[Unit]
Description=PeakeCoin Trading Bot
After=network.target

[Service]
Type=simple
User=$USER
WorkingDirectory=$BOT_PATH
Environment=PATH=$BOT_PATH/venv/bin
ExecStart=$BOT_PATH/venv/bin/python server_bot.py
Restart=always
RestartSec=30
StandardOutput=append:/var/log/peakebot.log
StandardError=append:/var/log/peakebot-error.log

[Install]
WantedBy=multi-user.target
EOF

    # Enable and start service
    sudo systemctl daemon-reload
    sudo systemctl enable peakebot
    
    print_status "Service created! ✅"
    echo ""
    echo "To start the service:"
    echo "  sudo systemctl start peakebot"
    echo ""
    echo "To view logs:"
    echo "  sudo journalctl -u peakebot -f"
    echo ""
    echo "To stop service:"
    echo "  sudo systemctl stop peakebot"
}

main() {
    print_header
    
    # Check if we're in the right directory
    if [ ! -f "server_bot.py" ]; then
        print_error "Please run this script from the PeakeCoin bot directory"
        exit 1
    fi
    
    check_system
    setup_bot
    
    while true; do
        show_menu
        
        case $choice in
            1)
                run_interactive
                break
                ;;
            2)
                run_background
                break
                ;;
            3)
                setup_service
                break
                ;;
            4)
                print_status "Setup complete! You can now run 'python server_bot.py'"
                break
                ;;
            0)
                print_status "Goodbye!"
                exit 0
                ;;
            *)
                print_error "Invalid option. Please try again."
                ;;
        esac
    done
}

main "$@"
