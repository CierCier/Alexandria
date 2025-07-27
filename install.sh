#!/bin/bash
set -e

echo "Alexandria Installation Script"
echo "=============================="

# Check if running on Wayland
if [ -z "$WAYLAND_DISPLAY" ]; then
    echo "Warning: WAYLAND_DISPLAY not set. Make sure you're running on Wayland."
fi

# Check dependencies
echo "Checking system dependencies..."

check_command() {
    if ! command -v "$1" &> /dev/null; then
        echo "Error: $1 is not installed"
        exit 1
    fi
}

check_command grim
check_command tesseract
check_command rye

echo "✓ All dependencies found"

# Install Python package
echo "Installing Alexandria..."
rye sync

# Install system integration
echo "Installing system integration..."
rye run alexandria install

# Create initial configuration
echo "Setting up configuration..."
rye run alexandria config > /dev/null

echo ""
echo "Installation complete!"
echo ""
echo "To start using Alexandria:"
echo "  1. Enable the service: systemctl --user enable alexandria.service"
echo "  2. Start the service:  systemctl --user start alexandria.service"
echo "  3. Check status:       alexandria status"
echo "  4. Launch GUI:         alexandria-gui"
echo ""
echo "Configuration file: ~/.config/alexandria/config.json"
echo "Screenshots will be saved to: ~/.local/share/alexandria/screenshots/"
