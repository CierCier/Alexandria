"""Configuration management for Alexandria."""

import json
import logging
from pathlib import Path
from typing import Any, Dict, Optional

from .xdg import XDGDirs

logger = logging.getLogger(__name__)


class Config:
    """Configuration manager for Alexandria."""

    DEFAULT_CONFIG = {
        "screenshot": {
            "interval_minutes": 1,
            "max_screenshots_per_day": 1 * 24 * 60,  # 1 screenshot per minute
            "compression_quality": 85,
            "capture_cursor": False,
            "exclude_windows": [],
        },
        "storage": {
            "retention_days": 30,
            "auto_cleanup": True,
            "database_path": None,  # Will be set to data_home/memories.db
        },
        "ocr": {
            "enabled": True,
            "language": "eng",
            "confidence_threshold": 60,
            "preprocess_image": True,
        },
        "privacy": {
            "blur_sensitive_info": True,
            "exclude_private_windows": True,
            "password_fields_detection": True,
        },
        "gui": {
            "theme": "auto",  # auto, light, dark
            "window_size": [1200, 800],
            "thumbnails_per_row": 4,
        },
        "wayland": {
            "screenshot_backend": "grim",  # grim, wlr-randr
            "output_selection": "all",  # all, primary, specific
            "specific_output": None,
        },
    }

    def __init__(self):
        XDGDirs.ensure_dirs()
        self.config_file = XDGDirs.config_home() / "config.json"
        self._config = self._load_config()

        # Set database path if not configured
        if not self._config["storage"]["database_path"]:
            self._config["storage"]["database_path"] = str(
                XDGDirs.data_home() / "memories.db"
            )

    def _load_config(self) -> Dict[str, Any]:
        """Load configuration from file or create default."""
        if self.config_file.exists():
            try:
                with open(self.config_file, "r") as f:
                    user_config = json.load(f)

                # Merge with defaults
                config = self.DEFAULT_CONFIG.copy()
                self._deep_update(config, user_config)
                return config

            except (json.JSONDecodeError, IOError) as e:
                logger.error(f"Failed to load config: {e}")
                logger.info("Using default configuration")

        # Create default config file
        self.save_config(self.DEFAULT_CONFIG)
        return self.DEFAULT_CONFIG.copy()

    def _deep_update(
        self, base_dict: Dict[str, Any], update_dict: Dict[str, Any]
    ) -> None:
        """Recursively update nested dictionaries."""
        for key, value in update_dict.items():
            if (
                key in base_dict
                and isinstance(base_dict[key], dict)
                and isinstance(value, dict)
            ):
                self._deep_update(base_dict[key], value)
            else:
                base_dict[key] = value

    def get(self, section: str, key: Optional[str] = None) -> Any:
        """Get configuration value."""
        if key is None:
            return self._config.get(section, {})
        return self._config.get(section, {}).get(key)

    def set(self, section: str, key: str, value: Any) -> None:
        """Set configuration value."""
        if section not in self._config:
            self._config[section] = {}
        self._config[section][key] = value

    def save_config(self, config: Optional[Dict[str, Any]] = None) -> None:
        """Save configuration to file."""
        if config is None:
            config = self._config

        try:
            with open(self.config_file, "w") as f:
                json.dump(config, f, indent=2)
            logger.info(f"Configuration saved to {self.config_file}")
        except IOError as e:
            logger.error(f"Failed to save config: {e}")

    def save(self) -> None:
        """Save current configuration."""
        self.save_config()

    @property
    def screenshot_interval(self) -> int:
        """Get screenshot interval in minutes."""
        return self.get("screenshot", "interval_minutes")

    @property
    def data_dir(self) -> Path:
        """Get data directory path."""
        return XDGDirs.data_home()

    @property
    def cache_dir(self) -> Path:
        """Get cache directory path."""
        return XDGDirs.cache_home()

    @property
    def database_path(self) -> str:
        """Get database file path."""
        return self.get("storage", "database_path")
