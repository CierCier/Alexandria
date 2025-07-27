"""Preferences window for Alexandria GUI."""

import gi

gi.require_version("Gtk", "3.0")

from gi.repository import Gtk, GLib
from alexandria.config import Config


class PreferencesWindow:
    """Preferences window for Alexandria settings."""

    def __init__(self, parent_window):
        self.parent_window = parent_window
        self.config = Config()
        self.setup_ui()

    def setup_ui(self):
        """Set up the preferences UI."""
        self.window = Gtk.Window()
        self.window.set_title("Alexandria Preferences")
        self.window.set_transient_for(self.parent_window)
        self.window.set_modal(True)
        self.window.set_default_size(600, 500)
        self.window.set_resizable(True)

        # Header bar
        header_bar = Gtk.HeaderBar()
        header_bar.set_show_close_button(True)
        header_bar.set_title("Preferences")
        self.window.set_titlebar(header_bar)

        # Main container
        main_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        self.window.add(main_box)

        # Notebook for different preference categories
        notebook = Gtk.Notebook()
        main_box.pack_start(notebook, True, True, 0)

        # General tab
        general_page = self.create_general_page()
        notebook.append_page(general_page, Gtk.Label("General"))

        # Capture tab
        capture_page = self.create_capture_page()
        notebook.append_page(capture_page, Gtk.Label("Capture"))

        # Privacy tab
        privacy_page = self.create_privacy_page()
        notebook.append_page(privacy_page, Gtk.Label("Privacy"))

        # Storage tab
        storage_page = self.create_storage_page()
        notebook.append_page(storage_page, Gtk.Label("Storage"))

        # Button box
        button_box = Gtk.ButtonBox(orientation=Gtk.Orientation.HORIZONTAL)
        button_box.set_layout(Gtk.ButtonBoxStyle.END)
        button_box.set_margin_left(12)
        button_box.set_margin_right(12)
        button_box.set_margin_top(6)
        button_box.set_margin_bottom(12)

        # Reset button
        reset_btn = Gtk.Button("Reset to Defaults")
        reset_btn.connect("clicked", self.on_reset_clicked)
        button_box.pack_start(reset_btn, False, False, 0)

        # Close button
        close_btn = Gtk.Button("Close")
        close_btn.get_style_context().add_class("suggested-action")
        close_btn.connect("clicked", self.on_close_clicked)
        button_box.pack_end(close_btn, False, False, 0)

        main_box.pack_start(button_box, False, False, 0)

    def create_general_page(self):
        """Create the general preferences page."""
        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=12)
        box.set_margin_left(12)
        box.set_margin_right(12)
        box.set_margin_top(12)
        box.set_margin_bottom(12)

        # Theme section
        theme_frame = Gtk.Frame()
        theme_frame.set_label("Appearance")
        theme_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6)
        theme_box.set_margin_left(12)
        theme_box.set_margin_right(12)
        theme_box.set_margin_top(6)
        theme_box.set_margin_bottom(12)

        # Dark theme toggle
        dark_theme_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)
        dark_theme_label = Gtk.Label("Use dark theme:")
        dark_theme_label.set_halign(Gtk.Align.START)
        dark_theme_box.pack_start(dark_theme_label, True, True, 0)

        self.dark_theme_switch = Gtk.Switch()
        self.dark_theme_switch.set_halign(Gtk.Align.END)
        self.dark_theme_switch.connect("notify::active", self.on_dark_theme_toggled)
        dark_theme_box.pack_start(self.dark_theme_switch, False, False, 0)

        theme_box.pack_start(dark_theme_box, False, False, 0)

        # Auto-detect theme
        auto_theme_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)
        auto_theme_label = Gtk.Label("Follow system theme:")
        auto_theme_label.set_halign(Gtk.Align.START)
        auto_theme_box.pack_start(auto_theme_label, True, True, 0)

        self.auto_theme_switch = Gtk.Switch()
        self.auto_theme_switch.set_halign(Gtk.Align.END)
        self.auto_theme_switch.connect("notify::active", self.on_auto_theme_toggled)
        auto_theme_box.pack_start(self.auto_theme_switch, False, False, 0)

        theme_box.pack_start(auto_theme_box, False, False, 0)

        theme_frame.add(theme_box)
        box.pack_start(theme_frame, False, False, 0)

        # Startup section
        startup_frame = Gtk.Frame()
        startup_frame.set_label("Startup")
        startup_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6)
        startup_box.set_margin_left(12)
        startup_box.set_margin_right(12)
        startup_box.set_margin_top(6)
        startup_box.set_margin_bottom(12)

        # Start daemon on login
        daemon_startup_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)
        daemon_startup_label = Gtk.Label("Start daemon on login:")
        daemon_startup_label.set_halign(Gtk.Align.START)
        daemon_startup_box.pack_start(daemon_startup_label, True, True, 0)

        self.daemon_startup_switch = Gtk.Switch()
        self.daemon_startup_switch.set_halign(Gtk.Align.END)
        daemon_startup_box.pack_start(self.daemon_startup_switch, False, False, 0)

        startup_box.pack_start(daemon_startup_box, False, False, 0)

        # Minimize to tray
        tray_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)
        tray_label = Gtk.Label("Minimize to system tray:")
        tray_label.set_halign(Gtk.Align.START)
        tray_box.pack_start(tray_label, True, True, 0)

        self.tray_switch = Gtk.Switch()
        self.tray_switch.set_halign(Gtk.Align.END)
        tray_box.pack_start(self.tray_switch, False, False, 0)

        startup_box.pack_start(tray_box, False, False, 0)

        startup_frame.add(startup_box)
        box.pack_start(startup_frame, False, False, 0)

        return box

    def create_capture_page(self):
        """Create the capture preferences page."""
        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=12)
        box.set_margin_left(12)
        box.set_margin_right(12)
        box.set_margin_top(12)
        box.set_margin_bottom(12)

        # Automatic capture section
        auto_frame = Gtk.Frame()
        auto_frame.set_label("Automatic Capture")
        auto_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6)
        auto_box.set_margin_left(12)
        auto_box.set_margin_right(12)
        auto_box.set_margin_top(6)
        auto_box.set_margin_bottom(12)

        # Enable automatic capture
        auto_capture_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)
        auto_capture_label = Gtk.Label("Enable automatic capture:")
        auto_capture_label.set_halign(Gtk.Align.START)
        auto_capture_box.pack_start(auto_capture_label, True, True, 0)

        self.auto_capture_switch = Gtk.Switch()
        self.auto_capture_switch.set_halign(Gtk.Align.END)
        auto_capture_box.pack_start(self.auto_capture_switch, False, False, 0)

        auto_box.pack_start(auto_capture_box, False, False, 0)

        # Capture interval
        interval_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)
        interval_label = Gtk.Label("Capture interval (seconds):")
        interval_label.set_halign(Gtk.Align.START)
        interval_box.pack_start(interval_label, True, True, 0)

        self.interval_spin = Gtk.SpinButton()
        self.interval_spin.set_range(5, 3600)  # 5 seconds to 1 hour
        self.interval_spin.set_increments(5, 60)
        self.interval_spin.set_value(30)  # Default 30 seconds
        interval_box.pack_start(self.interval_spin, False, False, 0)

        auto_box.pack_start(interval_box, False, False, 0)

        auto_frame.add(auto_box)
        box.pack_start(auto_frame, False, False, 0)

        # Screenshot settings
        screenshot_frame = Gtk.Frame()
        screenshot_frame.set_label("Screenshot Settings")
        screenshot_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6)
        screenshot_box.set_margin_left(12)
        screenshot_box.set_margin_right(12)
        screenshot_box.set_margin_top(6)
        screenshot_box.set_margin_bottom(12)

        # Quality setting
        quality_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)
        quality_label = Gtk.Label("JPEG Quality:")
        quality_label.set_halign(Gtk.Align.START)
        quality_box.pack_start(quality_label, True, True, 0)

        self.quality_scale = Gtk.Scale.new_with_range(
            Gtk.Orientation.HORIZONTAL, 1, 100, 5
        )
        self.quality_scale.set_value(85)
        self.quality_scale.set_hexpand(True)
        self.quality_scale.set_show_fill_level(True)
        quality_box.pack_start(self.quality_scale, True, True, 0)

        screenshot_box.pack_start(quality_box, False, False, 0)

        # Format selection
        format_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)
        format_label = Gtk.Label("Image format:")
        format_label.set_halign(Gtk.Align.START)
        format_box.pack_start(format_label, True, True, 0)

        self.format_combo = Gtk.ComboBoxText()
        self.format_combo.append_text("PNG")
        self.format_combo.append_text("JPEG")
        self.format_combo.append_text("WebP")
        self.format_combo.set_active(0)  # Default to PNG
        format_box.pack_start(self.format_combo, False, False, 0)

        screenshot_box.pack_start(format_box, False, False, 0)

        screenshot_frame.add(screenshot_box)
        box.pack_start(screenshot_frame, False, False, 0)

        return box

    def create_privacy_page(self):
        """Create the privacy preferences page."""
        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=12)
        box.set_margin_left(12)
        box.set_margin_right(12)
        box.set_margin_top(12)
        box.set_margin_bottom(12)

        # Privacy section
        privacy_frame = Gtk.Frame()
        privacy_frame.set_label("Privacy Settings")
        privacy_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6)
        privacy_box.set_margin_left(12)
        privacy_box.set_margin_right(12)
        privacy_box.set_margin_top(6)
        privacy_box.set_margin_bottom(12)

        # Auto-detect sensitive content
        sensitive_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)
        sensitive_label = Gtk.Label("Auto-detect sensitive content:")
        sensitive_label.set_halign(Gtk.Align.START)
        sensitive_box.pack_start(sensitive_label, True, True, 0)

        self.sensitive_switch = Gtk.Switch()
        self.sensitive_switch.set_halign(Gtk.Align.END)
        sensitive_box.pack_start(self.sensitive_switch, False, False, 0)

        privacy_box.pack_start(sensitive_box, False, False, 0)

        # Exclude private windows
        private_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)
        private_label = Gtk.Label("Skip private browsing windows:")
        private_label.set_halign(Gtk.Align.START)
        private_box.pack_start(private_label, True, True, 0)

        self.private_switch = Gtk.Switch()
        self.private_switch.set_halign(Gtk.Align.END)
        private_box.pack_start(self.private_switch, False, False, 0)

        privacy_box.pack_start(private_box, False, False, 0)

        privacy_frame.add(privacy_box)
        box.pack_start(privacy_frame, False, False, 0)

        # Excluded applications
        exclude_frame = Gtk.Frame()
        exclude_frame.set_label("Excluded Applications")
        exclude_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6)
        exclude_box.set_margin_left(12)
        exclude_box.set_margin_right(12)
        exclude_box.set_margin_top(6)
        exclude_box.set_margin_bottom(12)

        # Instructions
        instructions = Gtk.Label("Applications to exclude from automatic capture:")
        instructions.set_halign(Gtk.Align.START)
        instructions.get_style_context().add_class("dim-label")
        exclude_box.pack_start(instructions, False, False, 0)

        # Scrolled window for excluded apps list
        scrolled = Gtk.ScrolledWindow()
        scrolled.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)
        scrolled.set_size_request(-1, 150)

        self.exclude_listbox = Gtk.ListBox()
        scrolled.add(self.exclude_listbox)
        exclude_box.pack_start(scrolled, True, True, 0)

        # Add/remove buttons
        exclude_buttons = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)

        add_exclude_btn = Gtk.Button("Add Application")
        add_exclude_btn.connect("clicked", self.on_add_exclude_clicked)
        exclude_buttons.pack_start(add_exclude_btn, False, False, 0)

        remove_exclude_btn = Gtk.Button("Remove Selected")
        remove_exclude_btn.connect("clicked", self.on_remove_exclude_clicked)
        exclude_buttons.pack_start(remove_exclude_btn, False, False, 0)

        exclude_box.pack_start(exclude_buttons, False, False, 0)

        exclude_frame.add(exclude_box)
        box.pack_start(exclude_frame, False, False, 0)

        return box

    def create_storage_page(self):
        """Create the storage preferences page."""
        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=12)
        box.set_margin_left(12)
        box.set_margin_right(12)
        box.set_margin_top(12)
        box.set_margin_bottom(12)

        # Storage paths
        paths_frame = Gtk.Frame()
        paths_frame.set_label("Storage Paths")
        paths_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6)
        paths_box.set_margin_left(12)
        paths_box.set_margin_right(12)
        paths_box.set_margin_top(6)
        paths_box.set_margin_bottom(12)

        # Screenshots directory
        screenshots_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)
        screenshots_label = Gtk.Label("Screenshots directory:")
        screenshots_label.set_halign(Gtk.Align.START)
        screenshots_box.pack_start(screenshots_label, False, False, 0)

        self.screenshots_entry = Gtk.Entry()
        self.screenshots_entry.set_hexpand(True)
        screenshots_box.pack_start(self.screenshots_entry, True, True, 0)

        screenshots_browse_btn = Gtk.Button("Browse")
        screenshots_browse_btn.connect("clicked", self.on_browse_screenshots_clicked)
        screenshots_box.pack_start(screenshots_browse_btn, False, False, 0)

        paths_box.pack_start(screenshots_box, False, False, 0)

        # Database path
        db_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)
        db_label = Gtk.Label("Database file:")
        db_label.set_halign(Gtk.Align.START)
        db_box.pack_start(db_label, False, False, 0)

        self.db_entry = Gtk.Entry()
        self.db_entry.set_hexpand(True)
        db_box.pack_start(self.db_entry, True, True, 0)

        db_browse_btn = Gtk.Button("Browse")
        db_browse_btn.connect("clicked", self.on_browse_db_clicked)
        db_box.pack_start(db_browse_btn, False, False, 0)

        paths_box.pack_start(db_box, False, False, 0)

        paths_frame.add(paths_box)
        box.pack_start(paths_frame, False, False, 0)

        # Cleanup settings
        cleanup_frame = Gtk.Frame()
        cleanup_frame.set_label("Cleanup Settings")
        cleanup_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6)
        cleanup_box.set_margin_left(12)
        cleanup_box.set_margin_right(12)
        cleanup_box.set_margin_top(6)
        cleanup_box.set_margin_bottom(12)

        # Auto cleanup
        auto_cleanup_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)
        auto_cleanup_label = Gtk.Label("Automatically delete old screenshots:")
        auto_cleanup_label.set_halign(Gtk.Align.START)
        auto_cleanup_box.pack_start(auto_cleanup_label, True, True, 0)

        self.auto_cleanup_switch = Gtk.Switch()
        self.auto_cleanup_switch.set_halign(Gtk.Align.END)
        auto_cleanup_box.pack_start(self.auto_cleanup_switch, False, False, 0)

        cleanup_box.pack_start(auto_cleanup_box, False, False, 0)

        # Cleanup age
        age_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)
        age_label = Gtk.Label("Delete screenshots older than (days):")
        age_label.set_halign(Gtk.Align.START)
        age_box.pack_start(age_label, True, True, 0)

        self.age_spin = Gtk.SpinButton()
        self.age_spin.set_range(1, 365)
        self.age_spin.set_increments(1, 7)
        self.age_spin.set_value(30)  # Default 30 days
        age_box.pack_start(self.age_spin, False, False, 0)

        cleanup_box.pack_start(age_box, False, False, 0)

        cleanup_frame.add(cleanup_box)
        box.pack_start(cleanup_frame, False, False, 0)

        return box

    def load_settings(self):
        """Load current settings into the UI."""
        # Load settings from config
        pass

    def save_settings(self):
        """Save current settings from the UI."""
        # Save settings to config
        pass

    def on_dark_theme_toggled(self, switch, param):
        """Handle dark theme toggle."""
        is_active = switch.get_active()
        # Apply dark theme
        settings = Gtk.Settings.get_default()
        settings.set_property("gtk-application-prefer-dark-theme", is_active)

    def on_auto_theme_toggled(self, switch, param):
        """Handle auto theme detection toggle."""
        pass

    def on_browse_screenshots_clicked(self, button):
        """Handle browse screenshots directory."""
        dialog = Gtk.FileChooserDialog(
            title="Choose Screenshots Directory",
            parent=self.window,
            action=Gtk.FileChooserAction.SELECT_FOLDER,
        )
        dialog.add_buttons(
            Gtk.STOCK_CANCEL,
            Gtk.ResponseType.CANCEL,
            Gtk.STOCK_SELECT,
            Gtk.ResponseType.OK,
        )

        response = dialog.run()
        if response == Gtk.ResponseType.OK:
            self.screenshots_entry.set_text(dialog.get_filename())

        dialog.destroy()

    def on_browse_db_clicked(self, button):
        """Handle browse database file."""
        dialog = Gtk.FileChooserDialog(
            title="Choose Database File",
            parent=self.window,
            action=Gtk.FileChooserAction.SAVE,
        )
        dialog.add_buttons(
            Gtk.STOCK_CANCEL,
            Gtk.ResponseType.CANCEL,
            Gtk.STOCK_SAVE,
            Gtk.ResponseType.OK,
        )

        response = dialog.run()
        if response == Gtk.ResponseType.OK:
            self.db_entry.set_text(dialog.get_filename())

        dialog.destroy()

    def on_add_exclude_clicked(self, button):
        """Handle adding excluded application."""
        dialog = Gtk.MessageDialog(
            transient_for=self.window,
            flags=0,
            message_type=Gtk.MessageType.QUESTION,
            buttons=Gtk.ButtonsType.OK_CANCEL,
            text="Add Excluded Application",
        )
        dialog.format_secondary_text(
            "Enter the application name or window class to exclude:"
        )

        entry = Gtk.Entry()
        entry.set_placeholder_text("e.g., firefox, gnome-terminal")
        dialog.get_content_area().pack_start(entry, False, False, 0)
        dialog.show_all()

        response = dialog.run()
        if response == Gtk.ResponseType.OK:
            app_name = entry.get_text().strip()
            if app_name:
                # Add to exclude list
                row = Gtk.ListBoxRow()
                label = Gtk.Label(app_name)
                label.set_halign(Gtk.Align.START)
                row.add(label)
                self.exclude_listbox.add(row)
                self.exclude_listbox.show_all()

        dialog.destroy()

    def on_remove_exclude_clicked(self, button):
        """Handle removing excluded application."""
        selected_row = self.exclude_listbox.get_selected_row()
        if selected_row:
            self.exclude_listbox.remove(selected_row)

    def on_reset_clicked(self, button):
        """Handle reset to defaults."""
        dialog = Gtk.MessageDialog(
            transient_for=self.window,
            flags=0,
            message_type=Gtk.MessageType.WARNING,
            buttons=Gtk.ButtonsType.YES_NO,
            text="Reset to Defaults",
        )
        dialog.format_secondary_text(
            "This will reset all preferences to their default values. Continue?"
        )

        response = dialog.run()
        if response == Gtk.ResponseType.YES:
            # Reset all settings
            self.load_default_settings()

        dialog.destroy()

    def load_default_settings(self):
        """Load default settings into the UI."""
        # Reset all controls to defaults
        self.dark_theme_switch.set_active(False)
        self.auto_theme_switch.set_active(True)
        self.daemon_startup_switch.set_active(True)
        self.tray_switch.set_active(False)
        self.auto_capture_switch.set_active(True)
        self.interval_spin.set_value(30)
        self.quality_scale.set_value(85)
        self.format_combo.set_active(0)
        self.sensitive_switch.set_active(True)
        self.private_switch.set_active(True)
        self.auto_cleanup_switch.set_active(False)
        self.age_spin.set_value(30)

    def on_close_clicked(self, button):
        """Handle close button."""
        self.save_settings()
        self.window.destroy()

    def show(self):
        """Show the preferences window."""
        self.load_settings()
        self.window.show_all()
