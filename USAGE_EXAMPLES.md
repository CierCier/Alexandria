# USAGE_EXAMPLES.md

## Alexandria Usage Examples

### Quick Start

1. **Install and setup:**
```bash
./install.sh
systemctl --user enable alexandria.service
systemctl --user start alexandria.service
```

2. **Check that it's working:**
```bash
alexandria status
```

3. **Take a manual screenshot:**
```bash
alexandria daemon --one-shot
```

4. **Launch the GUI:**
```bash
alexandria-gui
```

### Configuration Examples

#### Basic Configuration (`~/.config/alexandria/config.json`)

```json
{
  "screenshot": {
    "interval_minutes": 3,
    "exclude_windows": ["keepass", "bitwarden", "firefox-private"]
  },
  "privacy": {
    "exclude_private_windows": true,
    "blur_sensitive_info": true
  },
  "storage": {
    "retention_days": 14
  }
}
```

#### High Privacy Setup

```json
{
  "screenshot": {
    "interval_minutes": 10,
    "exclude_windows": [
      "keepass", "bitwarden", "1password",
      "firefox", "chrome", "chromium",
      "telegram", "signal", "discord"
    ]
  },
  "privacy": {
    "exclude_private_windows": true,
    "blur_sensitive_info": true,
    "password_fields_detection": true
  },
  "ocr": {
    "enabled": false
  }
}
```

### Command Line Usage

#### Search Examples

```bash
# Search for specific text
alexandria search "meeting notes"
alexandria search "password"
alexandria search "TODO"

# Search with limits
alexandria search "email" --limit 5
```

#### Maintenance

```bash
# Clean up old screenshots (older than 7 days)
alexandria cleanup --days 7

# Clean up without confirmation
alexandria cleanup --days 30 --confirm

# Show configuration
alexandria config

# Show status and statistics
alexandria status
```

#### Service Management

```bash
# Check service status
systemctl --user status alexandria.service

# View service logs
journalctl --user -u alexandria.service -f

# Restart service
systemctl --user restart alexandria.service

# Stop service temporarily
systemctl --user stop alexandria.service
```

### Wayland Compositor Specific Setup

#### Sway

Add to your Sway config (`~/.config/sway/config`):

```
# Optional: Bind screenshot to key
bindsym $mod+Print exec alexandria daemon --one-shot
```

#### Hyprland

Add to your Hyprland config:

```
# Optional: Bind screenshot to key  
bind = $mainMod, Print, exec, alexandria daemon --one-shot
```

### Advanced Usage

#### Custom Screenshot Backend

If you want to use a different screenshot tool:

```json
{
  "wayland": {
    "screenshot_backend": "wlr-randr",
    "output_selection": "primary"
  }
}
```

#### OCR Language Configuration

For non-English text recognition:

```bash
# Install language data (example for German)
sudo apt install tesseract-ocr-deu

# Configure in config.json
{
  "ocr": {
    "language": "deu",
    "confidence_threshold": 70
  }
}
```

#### Database Backup

```bash
# Backup your memories database
cp ~/.local/share/alexandria/memories.db ~/backups/

# Restore from backup
cp ~/backups/memories.db ~/.local/share/alexandria/
```

### Troubleshooting

#### Screenshots not being captured

```bash
# Test grim manually
grim test.png

# Check if service is running
systemctl --user status alexandria.service

# Run daemon manually with debug output
alexandria daemon --debug
```

#### OCR not working

```bash
# Test tesseract
tesseract --version
echo "Test text" | tesseract stdin stdout

# Check OCR configuration
alexandria config | grep -A5 "OCR Settings"
```

#### GUI not starting

```bash
# Check GTK dependencies
python3 -c "import gi; gi.require_version('Gtk', '4.0')"

# Run with debug output
LIBADWAITA_DEBUG=1 alexandria-gui
```

### Integration with Other Tools

#### Rofi/Dmenu Search

Create a script to search memories with rofi:

```bash
#!/bin/bash
# ~/.local/bin/alexandria-rofi
query=$(echo "" | rofi -dmenu -p "Search memories:")
if [ -n "$query" ]; then
    alexandria search "$query"
fi
```

#### Notification on Sensitive Content

Add to your config to get notified of sensitive screenshots:

```json
{
  "privacy": {
    "notify_on_sensitive": true
  }
}
```

### Performance Tuning

#### For Low-End Systems

```json
{
  "screenshot": {
    "interval_minutes": 10,
    "compression_quality": 60
  },
  "ocr": {
    "preprocess_image": false
  }
}
```

#### For High-Resolution Displays

```json
{
  "screenshot": {
    "compression_quality": 95
  },
  "ocr": {
    "preprocess_image": true,
    "confidence_threshold": 80
  }
}
