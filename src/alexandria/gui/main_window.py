"""Main window for Alexandria GUI using GTK3."""

import gi

gi.require_version("Gtk", "3.0")
gi.require_version("Gdk", "3.0")
gi.require_version("GdkPixbuf", "2.0")

import os
import sys
from pathlib import Path
from datetime import datetime, timedelta
from typing import List, Optional

from gi.repository import Gtk, Gdk, GdkPixbuf, GLib, Gio
import threading

from alexandria.config import Config
from alexandria.core.models import MemoryDB, Memory
from alexandria.service.daemon import AlexandriaDaemon
from alexandria.gui.theme import ThemeManager
from alexandria.gui.preferences import PreferencesWindow
from alexandria.gui.about import show_about


class MemoryListItem:
    """Represents a memory item in the list."""

    def __init__(self, memory: Memory):
        self.memory = memory
        self.thumbnail = None
        self.load_thumbnail()

    def load_thumbnail(self):
        """Load thumbnail image for the memory."""
        try:
            if self.memory.thumbnail_path and Path(self.memory.thumbnail_path).exists():
                pixbuf = GdkPixbuf.Pixbuf.new_from_file_at_scale(
                    str(self.memory.thumbnail_path), 200, 150, True
                )
                self.thumbnail = pixbuf
            elif (
                self.memory.screenshot_path
                and Path(self.memory.screenshot_path).exists()
            ):
                pixbuf = GdkPixbuf.Pixbuf.new_from_file_at_scale(
                    str(self.memory.screenshot_path), 200, 150, True
                )
                self.thumbnail = pixbuf
        except Exception as e:
            print(f"Error loading thumbnail: {e}")
            self.thumbnail = None


class AlexandriaGUI:
    """Main GUI application for Alexandria."""

    def __init__(self):
        self.config = Config()
        # Create database URL from the config path
        db_path = self.config.database_path
        self.database_url = f"sqlite:///{db_path}"
        self.db = MemoryDB(self.database_url)
        self.daemon = AlexandriaDaemon()
        self.memories: List[MemoryListItem] = []
        self.filtered_memories: List[MemoryListItem] = []

        # Initialize theme manager
        self.theme_manager = ThemeManager()

        self.setup_ui()
        self.load_memories()

    def setup_ui(self):
        """Set up the main UI."""
        # Main window
        self.window = Gtk.Window()
        self.window.set_title("Alexandria - Screenshot Recall")
        self.window.set_default_size(1200, 800)
        self.window.set_icon_name("camera-photo")
        self.window.connect("destroy", self.on_quit)

        # Apply system theme
        if self.theme_manager.detect_system_theme():
            self.theme_manager.set_dark_theme(True)

        # Header bar
        self.setup_header_bar()

        # Main container
        main_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        self.window.add(main_box)

        # Search and filter bar
        self.setup_search_bar(main_box)

        # Main content area
        paned = Gtk.Paned(orientation=Gtk.Orientation.HORIZONTAL)
        main_box.pack_start(paned, True, True, 0)

        # Left panel - Memory list
        self.setup_memory_list(paned)

        # Right panel - Memory details
        self.setup_details_panel(paned)

        # Status bar
        self.setup_status_bar(main_box)

    def setup_header_bar(self):
        """Set up the header bar with controls."""
        header_bar = Gtk.HeaderBar()
        header_bar.set_show_close_button(True)
        header_bar.set_title("Alexandria")
        header_bar.set_subtitle("Screenshot Recall")

        # Capture button
        capture_btn = Gtk.Button()
        capture_btn.set_image(
            Gtk.Image.new_from_icon_name("camera-photo", Gtk.IconSize.BUTTON)
        )
        capture_btn.set_tooltip_text("Take Screenshot Now")
        capture_btn.connect("clicked", self.on_capture_clicked)
        header_bar.pack_start(capture_btn)

        # Menu button with actions
        menu_btn = Gtk.MenuButton()
        menu_btn.set_image(
            Gtk.Image.new_from_icon_name("open-menu", Gtk.IconSize.BUTTON)
        )
        menu_btn.set_tooltip_text("Menu")

        # Create popover menu
        popover = Gtk.Popover()
        menu_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=0)

        # Preferences button
        prefs_btn = Gtk.ModelButton()
        prefs_btn.set_property("text", "Preferences")
        prefs_btn.connect("clicked", self.on_preferences_clicked)
        menu_box.pack_start(prefs_btn, False, False, 0)

        # Separator
        separator = Gtk.Separator(orientation=Gtk.Orientation.HORIZONTAL)
        menu_box.pack_start(separator, False, False, 0)

        # About button
        about_btn = Gtk.ModelButton()
        about_btn.set_property("text", "About")
        about_btn.connect("clicked", self.on_about_clicked)
        menu_box.pack_start(about_btn, False, False, 0)

        # Quit button
        quit_btn = Gtk.ModelButton()
        quit_btn.set_property("text", "Quit")
        quit_btn.connect("clicked", self.on_quit)
        menu_box.pack_start(quit_btn, False, False, 0)

        popover.add(menu_box)
        menu_btn.set_popover(popover)

        header_bar.pack_end(menu_btn)

        self.window.set_titlebar(header_bar)

    def setup_search_bar(self, parent):
        """Set up search and filter controls."""
        search_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)
        search_box.set_margin_left(12)
        search_box.set_margin_right(12)
        search_box.set_margin_top(6)
        search_box.set_margin_bottom(6)

        # Search entry
        self.search_entry = Gtk.SearchEntry()
        self.search_entry.set_placeholder_text("Search memories...")
        self.search_entry.set_hexpand(True)
        self.search_entry.connect("search-changed", self.on_search_changed)
        search_box.pack_start(self.search_entry, True, True, 0)

        # Date filter
        date_label = Gtk.Label("Date:")
        search_box.pack_start(date_label, False, False, 0)

        self.date_combo = Gtk.ComboBoxText()
        self.date_combo.append_text("All")
        self.date_combo.append_text("Today")
        self.date_combo.append_text("Yesterday")
        self.date_combo.append_text("Last 7 days")
        self.date_combo.append_text("Last 30 days")
        self.date_combo.set_active(0)
        self.date_combo.connect("changed", self.on_filter_changed)
        search_box.pack_start(self.date_combo, False, False, 0)

        # Tag filter
        tag_label = Gtk.Label("Tags:")
        search_box.pack_start(tag_label, False, False, 0)

        self.tag_combo = Gtk.ComboBoxText()
        self.tag_combo.append_text("All")
        self.tag_combo.set_active(0)
        self.tag_combo.connect("changed", self.on_filter_changed)
        search_box.pack_start(self.tag_combo, False, False, 0)

        parent.pack_start(search_box, False, False, 0)

    def setup_memory_list(self, parent):
        """Set up the memory list view."""
        # Scrolled window for the list
        scrolled = Gtk.ScrolledWindow()
        scrolled.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)
        scrolled.set_size_request(400, -1)

        # List box with custom styling
        self.memory_listbox = Gtk.ListBox()
        self.memory_listbox.set_selection_mode(Gtk.SelectionMode.SINGLE)
        self.memory_listbox.connect("row-selected", self.on_memory_selected)
        self.memory_listbox.get_style_context().add_class("memory-list")

        scrolled.add(self.memory_listbox)
        parent.pack1(scrolled, False, False)

    def setup_details_panel(self, parent):
        """Set up the details panel for selected memory."""
        details_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=12)
        details_box.set_margin_left(12)
        details_box.set_margin_right(12)
        details_box.set_margin_top(12)
        details_box.set_margin_bottom(12)

        # Image display
        self.image_frame = Gtk.Frame()
        self.image_frame.set_shadow_type(Gtk.ShadowType.IN)

        self.image_view = Gtk.Image()
        self.image_view.set_size_request(600, 400)
        self.image_frame.add(self.image_view)
        details_box.pack_start(self.image_frame, True, True, 0)

        # Details notebook
        notebook = Gtk.Notebook()
        details_box.pack_start(notebook, False, False, 0)

        # Info tab
        info_box = self.create_info_tab()
        notebook.append_page(info_box, Gtk.Label("Info"))

        # OCR text tab
        ocr_box = self.create_ocr_tab()
        notebook.append_page(ocr_box, Gtk.Label("Text"))

        # Tags tab
        tags_box = self.create_tags_tab()
        notebook.append_page(tags_box, Gtk.Label("Tags"))

        parent.pack2(details_box, True, False)

    def create_info_tab(self):
        """Create the info tab for memory details."""
        grid = Gtk.Grid()
        grid.set_column_spacing(12)
        grid.set_row_spacing(6)

        # Labels
        labels = ["Timestamp:", "Application:", "Window:", "Size:", "File Size:"]
        for i, label_text in enumerate(labels):
            label = Gtk.Label(label_text)
            label.set_halign(Gtk.Align.START)
            label.get_style_context().add_class("dim-label")
            grid.attach(label, 0, i, 1, 1)

        # Values
        self.timestamp_label = Gtk.Label()
        self.timestamp_label.set_halign(Gtk.Align.START)
        self.timestamp_label.set_selectable(True)
        grid.attach(self.timestamp_label, 1, 0, 1, 1)

        self.app_label = Gtk.Label()
        self.app_label.set_halign(Gtk.Align.START)
        self.app_label.set_selectable(True)
        grid.attach(self.app_label, 1, 1, 1, 1)

        self.window_label = Gtk.Label()
        self.window_label.set_halign(Gtk.Align.START)
        self.window_label.set_selectable(True)
        grid.attach(self.window_label, 1, 2, 1, 1)

        self.size_label = Gtk.Label()
        self.size_label.set_halign(Gtk.Align.START)
        self.size_label.set_selectable(True)
        grid.attach(self.size_label, 1, 3, 1, 1)

        self.filesize_label = Gtk.Label()
        self.filesize_label.set_halign(Gtk.Align.START)
        self.filesize_label.set_selectable(True)
        grid.attach(self.filesize_label, 1, 4, 1, 1)

        return grid

    def create_ocr_tab(self):
        """Create the OCR text tab."""
        scrolled = Gtk.ScrolledWindow()
        scrolled.set_policy(Gtk.PolicyType.AUTOMATIC, Gtk.PolicyType.AUTOMATIC)
        scrolled.set_size_request(-1, 200)

        self.ocr_textview = Gtk.TextView()
        self.ocr_textview.set_editable(False)
        self.ocr_textview.set_cursor_visible(False)
        self.ocr_textview.set_wrap_mode(Gtk.WrapMode.WORD)

        scrolled.add(self.ocr_textview)
        return scrolled

    def create_tags_tab(self):
        """Create the tags management tab."""
        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6)

        # Tags entry
        entry_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)

        self.tags_entry = Gtk.Entry()
        self.tags_entry.set_placeholder_text("Add tags (comma separated)")
        entry_box.pack_start(self.tags_entry, True, True, 0)

        add_btn = Gtk.Button("Add")
        add_btn.connect("clicked", self.on_add_tags)
        entry_box.pack_start(add_btn, False, False, 0)

        box.pack_start(entry_box, False, False, 0)

        # Tags list
        scrolled = Gtk.ScrolledWindow()
        scrolled.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)
        scrolled.set_size_request(-1, 150)

        self.tags_listbox = Gtk.ListBox()
        scrolled.add(self.tags_listbox)
        box.pack_start(scrolled, True, True, 0)

        return box

    def setup_status_bar(self, parent):
        """Set up the status bar."""
        self.status_bar = Gtk.Statusbar()
        self.status_context = self.status_bar.get_context_id("main")
        self.status_bar.push(self.status_context, "Ready")
        parent.pack_start(self.status_bar, False, False, 0)

    def load_memories(self):
        """Load memories from database."""

        def load_thread():
            """Thread to load memories from the database."""
            while True:
                try:
                    with self.db.get_session() as session:
                        memories = (
                            session.query(Memory)
                            .order_by(Memory.timestamp.desc())
                            .limit(100)
                            .all()
                        )

                        memory_items = []
                        for memory in memories:
                            item = MemoryListItem(memory)
                            memory_items.append(item)

                        GLib.idle_add(self.update_memory_list, memory_items)
                except Exception as e:
                    GLib.idle_add(self.show_error, f"Error loading memories: {e}")

                threading.Event().wait(10)  # Wait before next load

        # Start loading memories in a separate thread
        threading.Thread(target=load_thread, daemon=True).start()

    def update_memory_list(self, memory_items: List[MemoryListItem]):
        """Update the memory list in the UI."""
        self.memories = memory_items
        self.filtered_memories = memory_items.copy()

        # Clear existing items
        for child in self.memory_listbox.get_children():
            self.memory_listbox.remove(child)

        # Add new items
        for item in self.filtered_memories:
            row = self.create_memory_row(item)
            self.memory_listbox.add(row)

        self.memory_listbox.show_all()
        self.update_status(f"{len(self.memories)} memories loaded")

        # Update tag combo
        self.update_tag_combo()

    def create_memory_row(self, item: MemoryListItem) -> Gtk.ListBoxRow:
        """Create a row widget for a memory item."""
        row = Gtk.ListBoxRow()
        row.memory_item = item

        box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=12)
        box.set_margin_left(12)
        box.set_margin_right(12)
        box.set_margin_top(6)
        box.set_margin_bottom(6)

        # Thumbnail
        if item.thumbnail:
            image = Gtk.Image.new_from_pixbuf(item.thumbnail)
        else:
            image = Gtk.Image.new_from_icon_name("image-missing", Gtk.IconSize.DIALOG)

        image.set_size_request(80, 60)
        box.pack_start(image, False, False, 0)

        # Details
        details_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=3)

        # Timestamp
        timestamp_label = Gtk.Label()
        timestamp_label.set_text(item.memory.timestamp.strftime("%Y-%m-%d %H:%M:%S"))
        timestamp_label.set_halign(Gtk.Align.START)
        timestamp_label.get_style_context().add_class("heading")
        details_box.pack_start(timestamp_label, False, False, 0)

        # Application info
        if item.memory.application_name or item.memory.window_title:
            app_text = item.memory.application_name or "Unknown"
            if item.memory.window_title:
                app_text += f" - {item.memory.window_title[:50]}..."

            app_label = Gtk.Label()
            app_label.set_text(app_text)
            app_label.set_halign(Gtk.Align.START)
            app_label.get_style_context().add_class("dim-label")
            details_box.pack_start(app_label, False, False, 0)

        # OCR preview
        if item.memory.ocr_text:
            ocr_preview = (
                item.memory.ocr_text[:100] + "..."
                if len(item.memory.ocr_text) > 100
                else item.memory.ocr_text
            )
            ocr_label = Gtk.Label()
            ocr_label.set_text(ocr_preview)
            ocr_label.set_halign(Gtk.Align.START)
            ocr_label.set_ellipsize(3)  # ELLIPSIZE_END
            ocr_label.get_style_context().add_class("dim-label")
            details_box.pack_start(ocr_label, False, False, 0)

        box.pack_start(details_box, True, True, 0)
        row.add(box)

        return row

    def update_tag_combo(self):
        """Update the tag filter combo with available tags."""
        # Clear existing items except "All"
        while self.tag_combo.get_active_text() != "All" and len(self.tag_combo) > 1:
            self.tag_combo.remove(1)

        # Collect all unique tags
        all_tags = set()
        for item in self.memories:
            all_tags.update(item.memory.tags_list)

        # Add tags to combo
        for tag in sorted(all_tags):
            self.tag_combo.append_text(tag)

    def on_memory_selected(self, listbox, row):
        """Handle memory selection."""
        if row is None:
            return

        item = row.memory_item
        self.show_memory_details(item)

    def show_memory_details(self, item: MemoryListItem):
        """Show details for the selected memory."""
        memory = item.memory

        # Load image
        try:
            if memory.screenshot_path and Path(memory.screenshot_path).exists():
                pixbuf = GdkPixbuf.Pixbuf.new_from_file_at_scale(
                    str(memory.screenshot_path), 600, 400, True
                )
                self.image_view.set_from_pixbuf(pixbuf)
            else:
                self.image_view.set_from_icon_name("image-missing", Gtk.IconSize.DIALOG)
        except Exception as e:
            print(f"Error loading image: {e}")
            self.image_view.set_from_icon_name("image-missing", Gtk.IconSize.DIALOG)

        # Update info labels
        self.timestamp_label.set_text(memory.timestamp.strftime("%Y-%m-%d %H:%M:%S"))
        self.app_label.set_text(memory.application_name or "Unknown")
        self.window_label.set_text(memory.window_title or "Unknown")

        if memory.image_width and memory.image_height:
            self.size_label.set_text(f"{memory.image_width} × {memory.image_height}")
        else:
            self.size_label.set_text("Unknown")

        if memory.file_size:
            self.filesize_label.set_text(self.format_file_size(memory.file_size))
        else:
            self.filesize_label.set_text("Unknown")

        # Update OCR text
        buffer = self.ocr_textview.get_buffer()
        buffer.set_text(memory.ocr_text or "No text found")

        # Update tags
        self.update_tags_display(memory.tags_list)

    def update_tags_display(self, tags: List[str]):
        """Update the tags display."""
        # Clear existing tags
        for child in self.tags_listbox.get_children():
            self.tags_listbox.remove(child)

        # Add current tags
        for tag in tags:
            row = Gtk.ListBoxRow()
            box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)

            label = Gtk.Label(tag)
            box.pack_start(label, True, True, 0)

            remove_btn = Gtk.Button()
            remove_btn.set_image(
                Gtk.Image.new_from_icon_name("edit-delete", Gtk.IconSize.BUTTON)
            )
            remove_btn.connect("clicked", lambda btn, t=tag: self.on_remove_tag(t))
            box.pack_start(remove_btn, False, False, 0)

            row.add(box)
            self.tags_listbox.add(row)

        self.tags_listbox.show_all()

    def format_file_size(self, size_bytes: int) -> str:
        """Format file size in human readable format."""
        for unit in ["B", "KB", "MB", "GB"]:
            if size_bytes < 1024:
                return f"{size_bytes:.1f} {unit}"
            size_bytes /= 1024
        return f"{size_bytes:.1f} TB"

    def on_search_changed(self, entry):
        """Handle search text changes."""
        self.apply_filters()

    def on_filter_changed(self, combo):
        """Handle filter changes."""
        self.apply_filters()

    def apply_filters(self):
        """Apply current search and filter settings."""
        search_text = self.search_entry.get_text().lower()
        date_filter = self.date_combo.get_active_text()
        tag_filter = self.tag_combo.get_active_text()

        filtered = []

        for item in self.memories:
            memory = item.memory

            # Apply search filter
            if search_text:
                searchable_text = f"{memory.ocr_text or ''} {memory.application_name or ''} {memory.window_title or ''}".lower()
                if search_text not in searchable_text:
                    continue

            # Apply date filter
            if date_filter != "All":
                now = datetime.now()
                if date_filter == "Today":
                    if memory.timestamp.date() != now.date():
                        continue
                elif date_filter == "Yesterday":
                    yesterday = now.date() - timedelta(days=1)
                    if memory.timestamp.date() != yesterday:
                        continue
                elif date_filter == "Last 7 days":
                    week_ago = now - timedelta(days=7)
                    if memory.timestamp < week_ago:
                        continue
                elif date_filter == "Last 30 days":
                    month_ago = now - timedelta(days=30)
                    if memory.timestamp < month_ago:
                        continue

            # Apply tag filter
            if tag_filter != "All":
                if tag_filter not in memory.tags_list:
                    continue

            filtered.append(item)

        self.filtered_memories = filtered

        # Update display
        for child in self.memory_listbox.get_children():
            self.memory_listbox.remove(child)

        for item in self.filtered_memories:
            row = self.create_memory_row(item)
            self.memory_listbox.add(row)

        self.memory_listbox.show_all()
        self.update_status(
            f"{len(self.filtered_memories)} of {len(self.memories)} memories shown"
        )

    def on_preferences_clicked(self, button):
        """Handle preferences menu item."""
        prefs = PreferencesWindow(self.window)
        prefs.show()

    def on_about_clicked(self, button):
        """Handle about menu item."""
        show_about(self.window)

    def on_capture_clicked(self, button):
        """Handle capture button click."""

        def capture_thread():
            try:
                self.daemon.capture_and_process_screenshot()
                GLib.idle_add(self.update_status, "Screenshot captured")
                GLib.idle_add(self.load_memories)  # Refresh list
            except Exception as e:
                GLib.idle_add(self.show_error, f"Capture failed: {e}")

        threading.Thread(target=capture_thread, daemon=True).start()
        self.update_status("Capturing screenshot...")

    def on_add_tags(self, button):
        """Handle adding tags."""
        # This would need the currently selected memory
        tags_text = self.tags_entry.get_text().strip()
        if not tags_text:
            return

        # Implementation would update the selected memory's tags
        self.tags_entry.set_text("")

    def on_remove_tag(self, tag):
        """Handle removing a tag."""
        # Implementation would remove the tag from selected memory
        pass

    def update_status(self, message):
        """Update status bar message."""
        self.status_bar.pop(self.status_context)
        self.status_bar.push(self.status_context, message)

    def show_error(self, message):
        """Show error dialog."""
        dialog = Gtk.MessageDialog(
            transient_for=self.window,
            flags=0,
            message_type=Gtk.MessageType.ERROR,
            buttons=Gtk.ButtonsType.OK,
            text=message,
        )
        dialog.run()
        dialog.destroy()

    def on_quit(self, *args):
        """Handle application quit."""
        Gtk.main_quit()

    def run(self):
        """Run the application."""
        self.window.show_all()
        Gtk.main()


def main():
    """Main entry point for the GUI."""
    try:
        app = AlexandriaGUI()
        app.run()
    except KeyboardInterrupt:
        print("Application interrupted by user")
    except Exception as e:
        print(f"Application error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
