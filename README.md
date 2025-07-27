# Alexandria

A powerful screenshot recall utility for Linux Wayland compositors that automatically captures, analyzes, and makes your screen memories searchable.

## Features

- **Automatic Screenshot Capture**: Regularly captures screenshots using Wayland-native tools
- **OCR Text Extraction**: Extracts and indexes text from screenshots using Tesseract
- **Intelligent Search**: Search through your screenshot history by text content, date, or application
- **Advanced Tagging System**: Uses NLTK for intelligent keyword extraction and lemmatization
- **Wayland Compositor Support**: Enhanced support for Sway, Hyprland, GNOME, and KDE
- **Window Context Awareness**: Automatically tags with application, window title, and workspace information
- **Privacy-Aware**: Automatically detects and handles sensitive information
- **FreeDesktop Compliant**: Follows XDG standards for configuration and data storage
- **GTK3 GUI**: Modern, native Linux interface with full theme support
- **Systemd Integration**: Runs as a user service in the background

## Requirements

### System Dependencies

- **Wayland Compositor**: Sway, GNOME/Mutter, KDE/KWin, or other wlr-protocols compatible compositor
- **Screenshot Backend**: `grim` (recommended) or compatible Wayland screenshot tool
- **OCR Engine**: `tesseract-ocr` with language data
- **Python**: 3.8 or higher

### For Ubuntu/Debian:
```bash
sudo apt install grim tesseract-ocr tesseract-ocr-eng python3-gi python3-gi-cairo gir1.2-gtk-3.0 python3-nltk
```

### For Arch Linux:
```bash
sudo pacman -S grim tesseract tesseract-data-eng python-gobject gtk3 python-nltk
```

### For Fedora:
```bash
sudo dnf install grim tesseract python3-gobject gtk3-devel python3-nltk
```

## Installation

### Using Rye (Recommended)

```bash
# Clone the repository
git clone https://github.com/CierCier/alexandria.git
cd alexandria

# Install with rye
rye sync
```

### From Source

```bash
git clone https://github.com/CierCier/alexandria.git
cd alexandria
pip install -e .
```

## Setup

### 1. Install System Integration

```bash
# With rye
rye run alexandria install

# Or if installed with pip
alexandria install
```

### 2. Enable the Service

```bash
# Enable and start the background service
systemctl --user enable alexandria.service
systemctl --user start alexandria.service
```

### 3. Verify Installation

```bash
# Check service status (with rye)
rye run alexandria status

# Take a test screenshot (with rye)
rye run alexandria daemon --one-shot

# Or if installed with pip
alexandria status
alexandria daemon --one-shot
```

## Usage

### Command Line Interface

```bash
# With rye:
rye run alexandria status              # Show status and statistics
rye run alexandria search "password"   # Search your memories
rye run alexandria gui                 # Launch the GUI
rye run alexandria daemon --debug      # Run daemon manually
rye run alexandria cleanup --days 7    # Clean up old memories
rye run alexandria config              # Show current configuration

# Direct script access with rye:
rye run alexandria-gui                 # Launch GUI directly
rye run alexandria-daemon              # Run daemon directly

# Or if installed with pip:
alexandria status
alexandria search "password"
alexandria gui
# etc.
```

### GUI Application

Launch the GUI with:
```bash
# Using rye
rye run alexandria gui
# or
rye run alexandria-gui

# Or if installed with pip
alexandria-gui
```

Features:
- Browse screenshots by date
- Search by text content
- View detailed memory information
- Filter by application or window
- Thumbnail grid view
- Full-size image preview

### Configuration

Configuration is stored in `~/.config/alexandria/config.json` following XDG standards.

#### Key Settings

```json
{
  "screenshot": {
    "interval_minutes": 5,
    "max_screenshots_per_day": 288,
    "compression_quality": 85,
    "exclude_windows": ["keepass", "bitwarden"]
  },
  "storage": {
    "retention_days": 30,
    "auto_cleanup": true
  },
  "ocr": {
    "enabled": true,
    "language": "eng",
    "confidence_threshold": 60
  },
  "privacy": {
    "blur_sensitive_info": true,
    "exclude_private_windows": true
  },
  "wayland": {
    "screenshot_backend": "grim",
    "output_selection": "all"
  }
}
```

## File Locations (XDG Compliant)

- **Configuration**: `~/.config/alexandria/`
- **Screenshots**: `~/.local/share/alexandria/screenshots/`
- **Database**: `~/.local/share/alexandria/memories.db`
- **Thumbnails**: `~/.cache/alexandria/thumbnails/`
- **Logs**: `~/.cache/alexandria/logs/`

## Privacy Features

Alexandria includes several privacy-focused features:

- **Sensitive Content Detection**: Automatically detects passwords, credit cards, and other sensitive information
- **Private Window Exclusion**: Excludes screenshots of password managers, private browsing, etc.
- **Configurable Retention**: Automatically deletes old screenshots
- **Local Storage**: All data stays on your machine

## Wayland Compositor Support

### Tested Compositors

- **Sway**: Full support with `swaymsg` integration
- **GNOME/Mutter**: Works with `grim`
- **KDE/KWin**: Basic support
- **Hyprland**: Supported via `grim`

### Required Protocols

- `wlr-screencopy-unstable-v1` (for screenshot capture)
- `wlr-foreign-toplevel-management-unstable-v1` (for window information)

## Development

### Project Structure

```
src/alexandria/
├── __init__.py          # Main package
├── cli.py              # Command-line interface
├── config/             # Configuration management
│   ├── config.py       # Config class
│   └── xdg.py         # XDG directories
├── core/               # Core functionality
│   ├── models.py       # Database models
│   ├── screenshot.py   # Screenshot capture
│   └── ocr.py         # OCR processing
├── service/            # Background service
│   └── daemon.py       # Main daemon
├── gui/                # GUI application
│   └── main_window.py  # GTK4 interface
└── manager/            # Existing managers
    ├── password.py     # Password management
    └── storage.py      # Storage utilities
```

### Running Tests

```bash
# Install development dependencies
rye sync --dev

# Run tests (when available)
pytest tests/
```

### Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## Troubleshooting

### Common Issues

**Screenshots not being captured:**
```bash
# Check if grim is available
which grim

# Test manual screenshot
grim test.png

# Check service logs
journalctl --user -u alexandria.service -f
```

**OCR not working:**
```bash
# Check tesseract installation
tesseract --version

# Test OCR manually
tesseract image.png output.txt
```

**GUI not launching:**
```bash
# Check GTK4/Libadwaita dependencies
python3 -c "import gi; gi.require_version('Gtk', '4.0'); gi.require_version('Adw', '1')"
```

### Debug Mode

```bash
# Run daemon with debug output
alexandria daemon --debug

# Check detailed logs
tail -f ~/.cache/alexandria/logs/alexandria-daemon.log
```

## License

GNU General Public License v3.0 - see LICENSE file for details.

## Acknowledgments

- [Tesseract OCR](https://github.com/tesseract-ocr/tesseract) for text recognition
- [grim](https://sr.ht/~emersion/grim/) for Wayland screenshot capture
- [GTK4](https://gtk.org/) and [Libadwaita](https://gitlab.gnome.org/GNOME/libadwaita)
- The Wayland Community
