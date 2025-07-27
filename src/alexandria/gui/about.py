"""About dialog for Alexandria GUI."""

import gi

gi.require_version("Gtk", "3.0")

from gi.repository import Gtk, GdkPixbuf
import os


class AboutDialog:
    """About dialog for Alexandria."""

    def __init__(self, parent_window):
        self.parent_window = parent_window
        self.setup_dialog()

    def setup_dialog(self):
        """Set up the about dialog."""
        self.dialog = Gtk.AboutDialog()
        self.dialog.set_transient_for(self.parent_window)
        self.dialog.set_modal(True)

        # Basic info
        self.dialog.set_program_name("Alexandria")
        self.dialog.set_version("0.1.0")
        self.dialog.set_comments("Screenshot Recall Utility for Wayland")
        self.dialog.set_copyright("Copyright © 2025 Aabish Malik")

        # Description
        description = """Alexandria is a powerful screenshot recall utility for Linux Wayland compositors that automatically captures, analyzes, and makes your screen memories searchable.

Features:
• Automatic screenshot capture
• OCR text extraction and indexing
• Intelligent search through screenshot history
• Privacy-aware sensitive content detection
• Modern GTK3 interface with theme support
• Systemd integration for background operation"""

        self.dialog.set_comments(description)

        # License
        self.dialog.set_license_type(Gtk.License.GPL_3_0)

        # Website
        self.dialog.set_website("https://github.com/yourusername/alexandria")
        self.dialog.set_website_label("Alexandria on GitHub")

        # Authors
        self.dialog.set_authors(["Aabish Malik <aabishmalik3337@gmail.com>"])

        # Credits
        self.dialog.set_documenters(["Contributors and community members"])

        # Translator credits
        self.dialog.set_translator_credits("translator-credits")

        # Logo - try to load from icon theme or use default
        try:
            # Try to load custom logo
            logo_path = self.find_logo_path()
            if logo_path and os.path.exists(logo_path):
                pixbuf = GdkPixbuf.Pixbuf.new_from_file_at_scale(
                    logo_path, 128, 128, True
                )
                self.dialog.set_logo(pixbuf)
            else:
                # Fallback to icon name
                self.dialog.set_logo_icon_name("camera-photo")
        except Exception:
            # Final fallback
            self.dialog.set_logo_icon_name("application-x-executable")

    def find_logo_path(self):
        """Try to find the application logo."""
        # Common logo locations
        possible_paths = [
            "/usr/share/pixmaps/alexandria.png",
            "/usr/share/icons/hicolor/128x128/apps/alexandria.png",
            "/usr/local/share/pixmaps/alexandria.png",
            "assets/alexandria.png",
            "assets/logo.png",
        ]

        for path in possible_paths:
            if os.path.exists(path):
                return path

        return None

    def show(self):
        """Show the about dialog."""
        self.dialog.run()
        self.dialog.destroy()


def show_about(parent_window):
    """Convenience function to show the about dialog."""
    about = AboutDialog(parent_window)
    about.show()
