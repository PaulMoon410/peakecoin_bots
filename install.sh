#!/bin/bash

# PeakeCoin Bot One-Click Installer
# This script downloads and sets up the PeakeCoin bot

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

print_header() {
    echo -e "${BLUE}$1${NC}"
}

# Main installation function
main() {
    print_header "======================================="
    print_header "  PeakeCoin Bot Installer v1.0"
    print_header "======================================="
    
    # Check if Python is installed
    if ! command -v python3 &> /dev/null; then
        print_error "Python 3 is required but not installed."
        print_status "Please install Python 3.11 or higher and run this script again."
        exit 1
    fi
    
    PYTHON_VERSION=$(python3 -c 'import sys; print(".".join(map(str, sys.version_info[:2])))')
    print_status "Found Python $PYTHON_VERSION"
    
    # Create bot directory
    BOT_DIR="peakecoin_bot"
    if [ -d "$BOT_DIR" ]; then
        print_warning "Directory $BOT_DIR already exists. Backing up..."
        mv "$BOT_DIR" "${BOT_DIR}_backup_$(date +%Y%m%d_%H%M%S)"
    fi
    
    print_status "Creating bot directory..."
    mkdir -p "$BOT_DIR"
    cd "$BOT_DIR"
    
    # If this script is in a bot directory, copy files
    if [ -f "../main.py" ] && [ -f "../peake_droid.py" ]; then
        print_status "Copying bot files..."
        cp -r ../* .
    else
        print_status "Bot files should be extracted to this directory"
        print_status "Please extract the PeakeCoin bot files here and run ./setup.sh"
        exit 0
    fi
    
    # Run setup
    print_status "Running setup..."
    if [ -f "setup.sh" ]; then
        chmod +x setup.sh
        ./setup.sh
    else
        print_status "Creating virtual environment..."
        python3 -m venv venv
        source venv/bin/activate
        pip install -r requirements.txt
    fi
    
    print_header "======================================="
    print_header "  Installation Complete!"
    print_header "======================================="
    
    print_status "Bot installed in: $(pwd)"
    print_status ""
    print_status "To run the bot:"
    print_status "  Desktop GUI:     python main.py"
    print_status "  Command line:    python peake_droid.py"
    print_status "  Web interface:   python web_interface.py"
    print_status ""
    print_status "For server deployment, see SERVER_DEPLOYMENT.md"
    print_status ""
    print_warning "Remember to keep your private keys secure!"
}

# Run main function
main "$@"
