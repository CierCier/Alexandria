"""Wayland window information gathering using pywayland."""

import json
import logging
import os
import subprocess
from typing import Dict, Optional, List
import time

logger = logging.getLogger(__name__)


class WaylandWindowInfo:
    """Gather window information from Wayland compositors."""

    def __init__(self):
        self.compositor_type = self._detect_compositor()
        logger.info(f"Detected Wayland compositor: {self.compositor_type}")

    def _detect_compositor(self) -> str:
        """Detect the running Wayland compositor."""
        # Check environment variables
        if os.getenv("SWAYSOCK"):
            return "sway"
        elif os.getenv("HYPRLAND_INSTANCE_SIGNATURE"):
            return "hyprland"
        elif os.getenv("QTILE_XEPHYR"):
            return "qtile"
        elif os.getenv("XDG_CURRENT_DESKTOP"):
            desktop = os.getenv("XDG_CURRENT_DESKTOP", "").lower()
            if "gnome" in desktop:
                return "gnome"
            elif "kde" in desktop or "plasma" in desktop:
                return "kde"
            elif "wlroots" in desktop:
                return "wlroots"

        # Try to detect by process name
        try:
            result = subprocess.run(
                ["pgrep", "-x", "sway"], capture_output=True, timeout=2
            )
            if result.returncode == 0:
                return "sway"

            result = subprocess.run(
                ["pgrep", "-x", "Hyprland"], capture_output=True, timeout=2
            )
            if result.returncode == 0:
                return "hyprland"

            result = subprocess.run(
                ["pgrep", "-x", "gnome-shell"], capture_output=True, timeout=2
            )
            if result.returncode == 0:
                return "gnome"

            result = subprocess.run(
                ["pgrep", "-x", "kwin_wayland"], capture_output=True, timeout=2
            )
            if result.returncode == 0:
                return "kde"

        except (subprocess.TimeoutExpired, FileNotFoundError):
            pass

        return "unknown"

    def get_active_window_info(self) -> Dict[str, Optional[str]]:
        """Get information about the currently active window."""
        if self.compositor_type == "sway":
            return self._get_sway_window_info()
        elif self.compositor_type == "hyprland":
            return self._get_hyprland_window_info()
        elif self.compositor_type == "gnome":
            return self._get_gnome_window_info()
        elif self.compositor_type == "kde":
            return self._get_kde_window_info()
        else:
            return self._get_generic_window_info()

    def _get_sway_window_info(self) -> Dict[str, Optional[str]]:
        """Get window info from Sway compositor."""
        try:
            result = subprocess.run(
                ["swaymsg", "-t", "get_tree"], capture_output=True, text=True, timeout=5
            )

            if result.returncode == 0:
                tree = json.loads(result.stdout)
                focused_window = self._find_focused_window(tree)

                if focused_window:
                    return {
                        "title": focused_window.get("name", ""),
                        "app_id": focused_window.get("app_id", ""),
                        "window_class": focused_window.get("window_class", ""),
                        "pid": str(focused_window.get("pid", "")),
                        "workspace": self._get_sway_workspace(tree),
                        "geometry": self._format_geometry(
                            focused_window.get("rect", {})
                        ),
                    }

            return self._empty_window_info()

        except (
            subprocess.TimeoutExpired,
            FileNotFoundError,
            json.JSONDecodeError,
        ) as e:
            logger.debug(f"Failed to get Sway window info: {e}")
            return self._empty_window_info()

    def _get_hyprland_window_info(self) -> Dict[str, Optional[str]]:
        """Get window info from Hyprland compositor."""
        try:
            # Get active window
            result = subprocess.run(
                ["hyprctl", "activewindow", "-j"],
                capture_output=True,
                text=True,
                timeout=5,
            )

            if result.returncode == 0:
                window = json.loads(result.stdout)

                return {
                    "title": window.get("title", ""),
                    "app_id": window.get("class", ""),
                    "window_class": window.get("class", ""),
                    "pid": str(window.get("pid", "")),
                    "workspace": window.get("workspace", {}).get("name", ""),
                    "geometry": f"{window.get('size', [0, 0])[0]}x{window.get('size', [0, 0])[1]}+{window.get('at', [0, 0])[0]}+{window.get('at', [0, 0])[1]}",
                }

            return self._empty_window_info()

        except (
            subprocess.TimeoutExpired,
            FileNotFoundError,
            json.JSONDecodeError,
        ) as e:
            logger.debug(f"Failed to get Hyprland window info: {e}")
            return self._empty_window_info()

    def _get_gnome_window_info(self) -> Dict[str, Optional[str]]:
        """Get window info from GNOME Shell."""
        try:
            # Try using gdbus to get window info from GNOME Shell
            result = subprocess.run(
                [
                    "gdbus",
                    "call",
                    "--session",
                    "--dest",
                    "org.gnome.Shell",
                    "--object-path",
                    "/org/gnome/Shell",
                    "--method",
                    "org.gnome.Shell.Eval",
                    "global.get_window_actors().filter(a => a.meta_window.has_focus())[0]?.meta_window",
                ],
                capture_output=True,
                text=True,
                timeout=5,
            )

            if result.returncode == 0:
                # Parse the result to get window information
                # This is a simplified approach - GNOME Shell introspection is complex
                return {
                    "title": "GNOME Window",  # Would need more complex parsing
                    "app_id": "unknown",
                    "window_class": "unknown",
                    "pid": "",
                    "workspace": "",
                    "geometry": "",
                }

            return self._empty_window_info()

        except (subprocess.TimeoutExpired, FileNotFoundError) as e:
            logger.debug(f"Failed to get GNOME window info: {e}")
            return self._empty_window_info()

    def _get_kde_window_info(self) -> Dict[str, Optional[str]]:
        """Get window info from KDE Plasma."""
        try:
            # Try using qdbus to get window info from KWin
            result = subprocess.run(
                ["qdbus", "org.kde.KWin", "/KWin", "org.kde.KWin.activeWindow"],
                capture_output=True,
                text=True,
                timeout=5,
            )

            if result.returncode == 0:
                window_id = result.stdout.strip()

                # Get window title
                title_result = subprocess.run(
                    [
                        "qdbus",
                        "org.kde.KWin",
                        f"/KWin/Window_{window_id}",
                        "org.kde.KWin.Window.caption",
                    ],
                    capture_output=True,
                    text=True,
                    timeout=5,
                )

                # Get window class
                class_result = subprocess.run(
                    [
                        "qdbus",
                        "org.kde.KWin",
                        f"/KWin/Window_{window_id}",
                        "org.kde.KWin.Window.resourceClass",
                    ],
                    capture_output=True,
                    text=True,
                    timeout=5,
                )

                return {
                    "title": (
                        title_result.stdout.strip()
                        if title_result.returncode == 0
                        else ""
                    ),
                    "app_id": (
                        class_result.stdout.strip()
                        if class_result.returncode == 0
                        else ""
                    ),
                    "window_class": (
                        class_result.stdout.strip()
                        if class_result.returncode == 0
                        else ""
                    ),
                    "pid": "",
                    "workspace": "",
                    "geometry": "",
                }

            return self._empty_window_info()

        except (subprocess.TimeoutExpired, FileNotFoundError) as e:
            logger.debug(f"Failed to get KDE window info: {e}")
            return self._empty_window_info()

    def _get_generic_window_info(self) -> Dict[str, Optional[str]]:
        """Fallback method for unknown compositors."""
        try:
            # Try to get info from /proc/self/environ of focused application
            # This is a very basic fallback
            result = subprocess.run(
                ["xprop", "-root", "_NET_ACTIVE_WINDOW"],
                capture_output=True,
                text=True,
                timeout=2,
            )

            # Note: xprop won't work on pure Wayland, this is just a placeholder
            # In practice, we'd need compositor-specific protocols

            return self._empty_window_info()

        except (subprocess.TimeoutExpired, FileNotFoundError) as e:
            logger.debug(f"Generic window info failed: {e}")
            return self._empty_window_info()

    def _find_focused_window(self, node: Dict) -> Optional[Dict]:
        """Recursively find the focused window in Sway tree."""
        if node.get("focused"):
            return node

        for child in node.get("nodes", []):
            result = self._find_focused_window(child)
            if result:
                return result

        for child in node.get("floating_nodes", []):
            result = self._find_focused_window(child)
            if result:
                return result

        return None

    def _get_sway_workspace(self, tree: Dict) -> str:
        """Get the current workspace name from Sway tree."""
        try:
            result = subprocess.run(
                ["swaymsg", "-t", "get_workspaces"],
                capture_output=True,
                text=True,
                timeout=2,
            )

            if result.returncode == 0:
                workspaces = json.loads(result.stdout)
                for ws in workspaces:
                    if ws.get("focused"):
                        return ws.get("name", "")
        except (subprocess.TimeoutExpired, FileNotFoundError, json.JSONDecodeError):
            pass

        return ""

    def _format_geometry(self, rect: Dict) -> str:
        """Format geometry from rect dictionary."""
        if not rect:
            return ""

        return f"{rect.get('width', 0)}x{rect.get('height', 0)}+{rect.get('x', 0)}+{rect.get('y', 0)}"

    def _empty_window_info(self) -> Dict[str, Optional[str]]:
        """Return empty window info dictionary."""
        return {
            "title": "",
            "app_id": "",
            "window_class": "",
            "pid": "",
            "workspace": "",
            "geometry": "",
        }

    def get_window_list(self) -> List[Dict[str, Optional[str]]]:
        """Get list of all windows (compositor-specific)."""
        if self.compositor_type == "sway":
            return self._get_sway_window_list()
        elif self.compositor_type == "hyprland":
            return self._get_hyprland_window_list()
        else:
            return []

    def _get_sway_window_list(self) -> List[Dict[str, Optional[str]]]:
        """Get all windows from Sway."""
        try:
            result = subprocess.run(
                ["swaymsg", "-t", "get_tree"], capture_output=True, text=True, timeout=5
            )

            if result.returncode == 0:
                tree = json.loads(result.stdout)
                windows = []
                self._collect_sway_windows(tree, windows)
                return windows

            return []

        except (subprocess.TimeoutExpired, FileNotFoundError, json.JSONDecodeError):
            return []

    def _collect_sway_windows(self, node: Dict, windows: List[Dict]):
        """Recursively collect windows from Sway tree."""
        if node.get("app_id") or node.get("window_class"):
            windows.append(
                {
                    "title": node.get("name", ""),
                    "app_id": node.get("app_id", ""),
                    "window_class": node.get("window_class", ""),
                    "pid": str(node.get("pid", "")),
                    "workspace": "",
                    "geometry": self._format_geometry(node.get("rect", {})),
                }
            )

        for child in node.get("nodes", []):
            self._collect_sway_windows(child, windows)

        for child in node.get("floating_nodes", []):
            self._collect_sway_windows(child, windows)

    def _get_hyprland_window_list(self) -> List[Dict[str, Optional[str]]]:
        """Get all windows from Hyprland."""
        try:
            result = subprocess.run(
                ["hyprctl", "clients", "-j"], capture_output=True, text=True, timeout=5
            )

            if result.returncode == 0:
                clients = json.loads(result.stdout)
                windows = []

                for client in clients:
                    windows.append(
                        {
                            "title": client.get("title", ""),
                            "app_id": client.get("class", ""),
                            "window_class": client.get("class", ""),
                            "pid": str(client.get("pid", "")),
                            "workspace": client.get("workspace", {}).get("name", ""),
                            "geometry": f"{client.get('size', [0, 0])[0]}x{client.get('size', [0, 0])[1]}+{client.get('at', [0, 0])[0]}+{client.get('at', [0, 0])[1]}",
                        }
                    )

                return windows

            return []

        except (subprocess.TimeoutExpired, FileNotFoundError, json.JSONDecodeError):
            return []
