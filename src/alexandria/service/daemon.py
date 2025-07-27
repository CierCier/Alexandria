"""Main daemon service for Alexandria screenshot capture."""

import json
import logging
import signal
import sys
import time
from datetime import datetime
from pathlib import Path
from threading import Event, Thread
from typing import Optional

import schedule

from alexandria.config import Config, XDGDirs
from alexandria.core import MemoryDB, ScreenshotCapture, OCRProcessor, Memory
from alexandria.core.text_processor import TextProcessor

logger = logging.getLogger(__name__)


class AlexandriaDaemon:
    """Main daemon service for Alexandria."""

    def __init__(self):
        self.config = Config()
        self.running = Event()
        self.running.set()

        # Initialize components
        self._init_logging()
        self._init_database()
        self._init_screenshot_capture()
        self._init_ocr_processor()

        # Initialize text processor for advanced tagging
        self.text_processor = TextProcessor()

        # Setup directories
        self.screenshots_dir = self.config.data_dir / "screenshots"
        self.thumbnails_dir = self.config.cache_dir / "thumbnails"

        # Create directories
        self.screenshots_dir.mkdir(parents=True, exist_ok=True)
        self.thumbnails_dir.mkdir(parents=True, exist_ok=True)

        # Setup signal handlers
        signal.signal(signal.SIGTERM, self._signal_handler)
        signal.signal(signal.SIGINT, self._signal_handler)

        logger.info("Alexandria daemon initialized")

    def _init_logging(self):
        """Initialize logging configuration."""
        log_level = logging.INFO
        log_format = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"

        # Setup file logging
        log_dir = XDGDirs.cache_home() / "logs"
        log_dir.mkdir(parents=True, exist_ok=True)
        log_file = log_dir / "alexandria-daemon.log"

        logging.basicConfig(
            level=log_level,
            format=log_format,
            handlers=[logging.FileHandler(log_file), logging.StreamHandler(sys.stdout)],
        )

    def _init_database(self):
        """Initialize database connection."""
        db_path = self.config.database_path
        db_url = f"sqlite:///{db_path}"

        # Ensure database directory exists
        Path(db_path).parent.mkdir(parents=True, exist_ok=True)

        self.db = MemoryDB(db_url)
        logger.info(f"Database initialized: {db_path}")

    def _init_screenshot_capture(self):
        """Initialize screenshot capture backend."""
        try:
            self.screenshot_capture = ScreenshotCapture(self.config)
            compositor_type = self.screenshot_capture.get_compositor_type()
            logger.info(
                f"Screenshot capture initialized with backend: {self.config.get('wayland', 'screenshot_backend')}"
            )
            logger.info(f"Detected Wayland compositor: {compositor_type}")
        except Exception as e:
            logger.error(f"Failed to initialize screenshot capture: {e}")
            self.screenshot_capture = None

    def _init_ocr_processor(self):
        """Initialize OCR processor."""
        if self.config.get("ocr", "enabled"):
            try:
                self.ocr_processor = OCRProcessor(self.config)
                logger.info("OCR processor initialized")
            except RuntimeError as e:
                logger.error(f"Failed to initialize OCR processor: {e}")
                self.ocr_processor = None
        else:
            self.ocr_processor = None
            logger.info("OCR processing disabled")

    def _signal_handler(self, signum, frame):
        """Handle shutdown signals."""
        logger.info(f"Received signal {signum}, shutting down...")
        self.stop()

    def capture_and_process_screenshot(self):
        """Capture and process a screenshot."""
        try:
            # Skip if screen is locked
            if self.screenshot_capture.is_screen_locked():
                logger.debug("Screen is locked, skipping screenshot")
                return

            # Capture screenshot
            screenshot_path = self.screenshot_capture.capture_screenshot(
                self.screenshots_dir
            )
            if not screenshot_path:
                logger.warning("Failed to capture screenshot")
                return

            # Create memory record
            memory = Memory()
            memory.screenshot_path = str(screenshot_path)
            memory.timestamp = datetime.utcnow()

            # Get image metadata
            metadata = self.screenshot_capture.get_image_metadata(screenshot_path)
            memory.image_width = metadata.get("width")
            memory.image_height = metadata.get("height")
            memory.file_size = metadata.get("file_size")

            # Analyze image content
            content_analysis = self.screenshot_capture.analyze_image_content(
                screenshot_path
            )
            if content_analysis.get("dominant_colors"):
                memory.dominant_colors = json.dumps(content_analysis["dominant_colors"])

            # Get window information (enhanced with Wayland support)
            window_info = self.screenshot_capture.get_active_window_info()
            memory.window_title = window_info.get("title")
            memory.application_name = window_info.get("app_id")
            memory.window_class = window_info.get("window_class")

            # Create thumbnail
            timestamp_str = memory.timestamp.strftime("%Y%m%d_%H%M%S")
            thumbnail_path = self.thumbnails_dir / f"thumb_{timestamp_str}.png"

            if self.screenshot_capture.create_thumbnail(
                screenshot_path, thumbnail_path
            ):
                memory.thumbnail_path = str(thumbnail_path)

            # Process with OCR if enabled
            if self.ocr_processor:
                ocr_result = self.ocr_processor.process_image(screenshot_path)

                memory.ocr_text = ocr_result.get("text", "")
                memory.ocr_confidence = ocr_result.get("confidence", 0)
                memory.has_text = ocr_result.get("has_text", False)
                memory.is_sensitive = ocr_result.get("has_sensitive", False)

                if ocr_result.get("structured_data"):
                    memory.ocr_data = json.dumps(ocr_result["structured_data"])

                # Generate comprehensive tags using NLTK and window information
                comprehensive_tags = self.text_processor.generate_content_tags(
                    memory.ocr_text, window_info, max_total_tags=25
                )
                memory.tags_list = comprehensive_tags

                logger.debug(
                    f"Generated {len(comprehensive_tags)} tags: {comprehensive_tags}"
                )

            # Mark as private if sensitive content detected
            if memory.is_sensitive or self._should_mark_private(window_info):
                memory.is_private = True

            # Save to database
            saved_memory = self.db.add_memory(memory)

            logger.info(f"Screenshot processed and saved: {saved_memory.id}")

            # Cleanup old screenshots if auto-cleanup is enabled
            if self.config.get("storage", "auto_cleanup"):
                self._cleanup_old_memories()

        except Exception as e:
            logger.error(f"Error processing screenshot: {e}")

    def _should_mark_private(self, window_info: dict) -> bool:
        """Determine if a screenshot should be marked as private."""
        if not self.config.get("privacy", "exclude_private_windows"):
            return False

        # Check against excluded applications
        excluded_windows = self.config.get("screenshot", "exclude_windows") or []

        app_id = window_info.get("app_id", "").lower()
        window_class = window_info.get("window_class", "").lower()
        window_title = window_info.get("title", "").lower()

        for exclude_pattern in excluded_windows:
            exclude_pattern = exclude_pattern.lower()
            if (
                exclude_pattern in app_id
                or exclude_pattern in window_class
                or exclude_pattern in window_title
            ):
                return True

        # Common private applications
        private_apps = {
            "firefox",
            "chrome",
            "chromium",
            "brave",
            "edge",  # Browsers (potentially private browsing)
            "keepass",
            "bitwarden",
            "1password",  # Password managers
            "telegram",
            "signal",
            "discord",
            "slack",  # Messaging
            "evolution",
            "thunderbird",  # Email clients
        }

        for private_app in private_apps:
            if private_app in app_id or private_app in window_class:
                return True

        return False

    def _cleanup_old_memories(self):
        """Clean up old memories based on retention policy."""
        retention_days = self.config.get("storage", "retention_days")
        if retention_days and retention_days > 0:
            deleted_count = self.db.cleanup_old_memories(retention_days)
            if deleted_count > 0:
                logger.info(f"Cleaned up {deleted_count} old memories")

    def setup_schedule(self):
        """Setup the screenshot capture schedule."""
        interval = self.config.screenshot_interval

        schedule.every(interval).minutes.do(self.capture_and_process_screenshot)

        # Schedule daily cleanup at 3 AM
        schedule.every().day.at("03:00").do(self._cleanup_old_memories)

        logger.info(f"Scheduled screenshot capture every {interval} minutes")

    def run(self):
        """Main daemon loop."""
        logger.info("Starting Alexandria daemon")

        self.setup_schedule()

        # Take an initial screenshot
        self.capture_and_process_screenshot()

        # Main loop
        while self.running.is_set():
            try:
                schedule.run_pending()
                time.sleep(1)
            except KeyboardInterrupt:
                break
            except Exception as e:
                logger.error(f"Error in main loop: {e}")
                time.sleep(5)  # Wait before retrying

        logger.info("Alexandria daemon stopped")

    def stop(self):
        """Stop the daemon."""
        self.running.clear()

    def status(self) -> dict:
        """Get daemon status information."""
        stats = self.db.get_statistics()

        return {
            "running": self.running.is_set(),
            "config_file": str(self.config.config_file),
            "database_path": self.config.database_path,
            "screenshots_dir": str(self.screenshots_dir),
            "screenshot_backend": self.config.get("wayland", "screenshot_backend"),
            "ocr_enabled": self.config.get("ocr", "enabled"),
            "interval_minutes": self.config.screenshot_interval,
            "statistics": stats,
        }


def main():
    """Main entry point for the daemon."""
    import argparse

    parser = argparse.ArgumentParser(description="Alexandria screenshot daemon")
    parser.add_argument("--debug", action="store_true", help="Enable debug logging")
    parser.add_argument(
        "--one-shot", action="store_true", help="Take one screenshot and exit"
    )
    parser.add_argument("--status", action="store_true", help="Show daemon status")

    args = parser.parse_args()

    if args.debug:
        logging.getLogger().setLevel(logging.DEBUG)

    daemon = AlexandriaDaemon()

    if args.status:
        status = daemon.status()
        print(json.dumps(status, indent=2, default=str))
        return

    if args.one_shot:
        daemon.capture_and_process_screenshot()
        return

    try:
        daemon.run()
    except KeyboardInterrupt:
        logger.info("Daemon interrupted by user")
    except Exception as e:
        logger.error(f"Daemon crashed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
