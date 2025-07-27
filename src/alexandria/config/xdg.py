"""XDG Base Directory specification implementation."""

import os
from pathlib import Path


class XDGDirs:
    """XDG Base Directory specification for Alexandria."""

    APP_NAME = "alexandria"

    @classmethod
    def config_home(cls) -> Path:
        """Return XDG_CONFIG_HOME/alexandria directory."""
        xdg_config = os.environ.get("XDG_CONFIG_HOME")
        if xdg_config:
            return Path(xdg_config) / cls.APP_NAME
        return Path.home() / ".config" / cls.APP_NAME

    @classmethod
    def data_home(cls) -> Path:
        """Return XDG_DATA_HOME/alexandria directory."""
        xdg_data = os.environ.get("XDG_DATA_HOME")
        if xdg_data:
            return Path(xdg_data) / cls.APP_NAME
        return Path.home() / ".local" / "share" / cls.APP_NAME

    @classmethod
    def cache_home(cls) -> Path:
        """Return XDG_CACHE_HOME/alexandria directory."""
        xdg_cache = os.environ.get("XDG_CACHE_HOME")
        if xdg_cache:
            return Path(xdg_cache) / cls.APP_NAME
        return Path.home() / ".cache" / cls.APP_NAME

    @classmethod
    def runtime_dir(cls) -> Path:
        """Return XDG_RUNTIME_DIR/alexandria directory."""
        xdg_runtime = os.environ.get("XDG_RUNTIME_DIR")
        if not xdg_runtime:
            # Fallback to temp directory
            return Path("/tmp") / f"{cls.APP_NAME}-{os.getuid()}"
        return Path(xdg_runtime) / cls.APP_NAME

    @classmethod
    def ensure_dirs(cls) -> None:
        """Create all necessary directories."""
        dirs = [
            cls.config_home(),
            cls.data_home(),
            cls.cache_home(),
            cls.runtime_dir(),
        ]

        for directory in dirs:
            directory.mkdir(parents=True, exist_ok=True)

        # Set proper permissions for runtime directory
        runtime = cls.runtime_dir()
        if runtime.exists():
            os.chmod(runtime, 0o700)
