#!/usr/bin/env bash
# Development launcher script for Alexandria GUI

set -e

# Change to project directory
cd "$(dirname "$0")"

echo "🚀 Launching Alexandria GUI with rye..."
echo "📍 Project directory: $(pwd)"
echo ""

# Check if rye is available
if ! command -v rye &> /dev/null; then
    echo "❌ Error: rye is not installed or not in PATH"
    echo "   Please install rye: https://rye.astral.sh/"
    exit 1
fi

# Check if project is synced
if [ ! -d ".venv" ]; then
    echo "📦 Virtual environment not found. Running rye sync..."
    rye sync
    echo ""
fi

# Launch the GUI
echo "🎨 Starting Alexandria GUI..."
echo "   Use Ctrl+C to stop"
echo ""

# Run the GUI with proper error handling
rye run alexandria-gui || {
    echo ""
    echo "❌ Error: Failed to launch Alexandria GUI"
    echo ""
    echo "🔧 Troubleshooting:"
    echo "   1. Make sure GTK3 dependencies are installed:"
    echo "      Ubuntu/Debian: sudo apt install python3-gi python3-gi-cairo gir1.2-gtk-3.0"
    echo "      Arch: sudo pacman -S python-gobject gtk3"
    echo "      Fedora: sudo dnf install python3-gobject gtk3-devel"
    echo ""
    echo "   2. Check if display is available: echo \$DISPLAY"
    echo "   3. For Wayland, ensure grim is installed: which grim"
    echo ""
    exit 1
}
