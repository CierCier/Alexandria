"""Theme and styling utilities for Alexandria GUI."""

import gi

gi.require_version("Gtk", "3.0")

from gi.repository import Gtk, Gdk
import os


class ThemeManager:
    """Manages theme and styling for the Alexandria GUI."""

    def __init__(self):
        self.css_provider = Gtk.CssProvider()
        self.load_custom_styles()
        self.apply_styles()

    def load_custom_styles(self):
        """Load custom CSS styles."""
        css = """
        /* Alexandria custom styles */
        
        /* Header styling */
        headerbar {
            background: @theme_bg_color;
            border-bottom: 1px solid @borders;
        }
        
        /* Memory list styling */
        .memory-list {
            background: @theme_base_color;
        }
        
        .memory-row {
            padding: 8px;
            border-bottom: 1px solid alpha(@borders, 0.5);
        }
        
        .memory-row:hover {
            background: alpha(@theme_selected_bg_color, 0.1);
        }
        
        .memory-row:selected {
            background: @theme_selected_bg_color;
            color: @theme_selected_fg_color;
        }
        
        /* Typography */
        .heading {
            font-weight: bold;
            font-size: 1.1em;
        }
        
        .dim-label {
            opacity: 0.7;
            font-size: 0.9em;
        }
        
        /* Search bar */
        .search-bar {
            background: alpha(@theme_bg_color, 0.95);
            border-bottom: 1px solid @borders;
            padding: 6px;
        }
        
        /* Details panel */
        .details-panel {
            background: @theme_base_color;
            padding: 12px;
        }
        
        /* Image frame */
        .image-frame {
            border: 1px solid @borders;
            border-radius: 6px;
            background: @theme_base_color;
        }
        
        /* Tags */
        .tag-item {
            background: alpha(@theme_selected_bg_color, 0.2);
            border: 1px solid alpha(@theme_selected_bg_color, 0.4);
            border-radius: 12px;
            padding: 4px 8px;
            margin: 2px;
        }
        
        /* Buttons */
        button {
            border-radius: 4px;
        }
        
        button.suggested-action {
            background: @theme_selected_bg_color;
            color: @theme_selected_fg_color;
            border: none;
        }
        
        button.destructive-action {
            background: #e74c3c;
            color: white;
            border: none;
        }
        
        /* Notebook tabs */
        notebook tab {
            padding: 8px 16px;
        }
        
        /* Status bar */
        statusbar {
            background: @theme_bg_color;
            border-top: 1px solid @borders;
            font-size: 0.9em;
        }
        
        /* Scrollbars */
        scrollbar {
            background: transparent;
        }
        
        scrollbar slider {
            background: alpha(@theme_fg_color, 0.3);
            border-radius: 10px;
            min-width: 6px;
            min-height: 6px;
        }
        
        scrollbar slider:hover {
            background: alpha(@theme_fg_color, 0.5);
        }
        """

        self.css_provider.load_from_data(css.encode("utf-8"))

    def apply_styles(self):
        """Apply the custom styles to the default screen."""
        screen = Gdk.Screen.get_default()
        Gtk.StyleContext.add_provider_for_screen(
            screen, self.css_provider, Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION
        )

    def set_dark_theme(self, enable: bool):
        """Enable or disable dark theme."""
        settings = Gtk.Settings.get_default()
        settings.set_property("gtk-application-prefer-dark-theme", enable)

    def detect_system_theme(self) -> bool:
        """Detect if the system is using a dark theme."""
        try:
            # Check GTK theme setting
            settings = Gtk.Settings.get_default()
            theme_name = settings.get_property("gtk-theme-name")

            if theme_name and "dark" in theme_name.lower():
                return True

            # Check environment variables
            gtk_theme = os.getenv("GTK_THEME", "")
            if "dark" in gtk_theme.lower():
                return True

            # Check for GNOME dark mode preference
            try:
                import subprocess

                result = subprocess.run(
                    ["gsettings", "get", "org.gnome.desktop.interface", "gtk-theme"],
                    capture_output=True,
                    text=True,
                    timeout=2,
                )
                if result.returncode == 0 and "dark" in result.stdout.lower():
                    return True
            except:
                pass

            return False

        except Exception:
            return False

    def get_system_accent_color(self) -> str:
        """Try to get the system accent color."""
        try:
            # Try to get GNOME accent color
            import subprocess

            result = subprocess.run(
                ["gsettings", "get", "org.gnome.desktop.interface", "accent-color"],
                capture_output=True,
                text=True,
                timeout=2,
            )
            if result.returncode == 0:
                color = result.stdout.strip().strip("'\"")
                if color and color != "default":
                    return color
        except:
            pass

        # Fallback to default blue
        return "#3584e4"
