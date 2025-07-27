"""Alexandria - Screenshot Recall Utility for Wayland compositors."""

__version__ = "0.1.0"
__author__ = "Aabish Malik"
__email__ = "aabishmalik3337@gmail.com"

from alexandria.config import Config, XDGDirs
from alexandria.core import Memory, MemoryDB, ScreenshotCapture, OCRProcessor
from alexandria.service import AlexandriaDaemon

__all__ = [
    "Config",
    "XDGDirs",
    "Memory",
    "MemoryDB",
    "ScreenshotCapture",
    "OCRProcessor",
    "AlexandriaDaemon",
]
