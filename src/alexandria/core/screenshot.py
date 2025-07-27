"""Screenshot capture functionality for Wayland compositors."""

import json
import logging
import subprocess
import tempfile
from datetime import datetime
from pathlib import Path
from typing import Optional, Tuple, List
import os

from PIL import Image
import cv2
import numpy as np

from .wayland_info import WaylandWindowInfo

logger = logging.getLogger(__name__)


class ScreenshotCapture:
    """Screenshot capture using Wayland-native tools."""

    def __init__(self, config):
        self.config = config
        self.screenshot_backend = config.get("wayland", "screenshot_backend")
        self.output_selection = config.get("wayland", "output_selection")
        self.specific_output = config.get("wayland", "specific_output")

        # Initialize Wayland window information gatherer
        self.window_info = WaylandWindowInfo()

        # Verify backend availability
        if not self._check_backend_available():
            raise RuntimeError(
                f"Screenshot backend '{self.screenshot_backend}' not available"
            )

    def _check_backend_available(self) -> bool:
        """Check if the configured screenshot backend is available."""
        try:
            result = subprocess.run(
                [self.screenshot_backend, "-h"], capture_output=True, timeout=5
            )
            return result.returncode == 0
        except (subprocess.TimeoutExpired, FileNotFoundError):
            return False

    def _get_wayland_outputs(self) -> List[str]:
        """Get list of available Wayland outputs."""
        try:
            if self.screenshot_backend == "grim":
                # grim uses wlr-randr for output listing
                result = subprocess.run(
                    ["wlr-randr", "--json"], capture_output=True, text=True, timeout=5
                )
                if result.returncode == 0:
                    outputs = json.loads(result.stdout)
                    return [
                        output["name"] for output in outputs if output.get("enabled")
                    ]

            return []
        except (subprocess.TimeoutExpired, FileNotFoundError, json.JSONDecodeError):
            logger.warning("Could not get Wayland outputs list")
            return []

    def _build_screenshot_command(self, output_file: str) -> List[str]:
        """Build the screenshot command based on configuration."""
        if self.screenshot_backend == "grim":
            cmd = ["grim"]

            if self.output_selection == "specific" and self.specific_output:
                cmd.extend(["-o", self.specific_output])
            elif self.output_selection == "primary":
                # Try to get primary output
                outputs = self._get_wayland_outputs()
                if outputs:
                    cmd.extend(["-o", outputs[0]])

            # Add quality options based on file type
            if output_file.lower().endswith(".png"):
                # PNG compression level (0-9)
                quality = self.config.get("screenshot", "compression_quality")
                if quality and quality < 100:
                    # Convert quality percentage to PNG compression level
                    compression_level = max(0, min(9, 9 - int(quality / 11)))
                    cmd.extend(["-l", str(compression_level)])
            elif output_file.lower().endswith(".jpg") or output_file.lower().endswith(
                ".jpeg"
            ):
                # JPEG quality (0-100)
                quality = self.config.get("screenshot", "compression_quality")
                if quality:
                    cmd.extend(["-q", str(quality)])

            cmd.append(output_file)
            return cmd

        else:
            raise ValueError(
                f"Unsupported screenshot backend: {self.screenshot_backend}"
            )

    def capture_screenshot(self, output_dir: Path) -> Optional[Path]:
        """Capture a screenshot and return the file path."""
        timestamp = datetime.now()
        filename = f"screenshot_{timestamp.strftime('%Y%m%d_%H%M%S')}.png"
        output_file = output_dir / filename

        try:
            # Ensure output directory exists
            output_dir.mkdir(parents=True, exist_ok=True)

            # Build and execute screenshot command
            cmd = self._build_screenshot_command(str(output_file))

            logger.debug(f"Executing screenshot command: {' '.join(cmd)}")
            result = subprocess.run(cmd, capture_output=True, timeout=10)

            if result.returncode == 0 and output_file.exists():
                logger.info(f"Screenshot captured: {output_file}")
                return output_file
            else:
                error_msg = result.stderr.decode() if result.stderr else "Unknown error"
                logger.error(f"Screenshot capture failed: {error_msg}")
                return None

        except subprocess.TimeoutExpired:
            logger.error("Screenshot capture timed out")
            return None
        except Exception as e:
            logger.error(f"Screenshot capture error: {e}")
            return None

    def create_thumbnail(
        self, image_path: Path, thumbnail_path: Path, size: Tuple[int, int] = (200, 150)
    ) -> bool:
        """Create a thumbnail of the screenshot."""
        try:
            with Image.open(image_path) as img:
                # Create thumbnail maintaining aspect ratio
                img.thumbnail(size, Image.Resampling.LANCZOS)

                # Save thumbnail
                thumbnail_path.parent.mkdir(parents=True, exist_ok=True)
                img.save(thumbnail_path, "PNG", optimize=True)

                logger.debug(f"Thumbnail created: {thumbnail_path}")
                return True

        except Exception as e:
            logger.error(f"Thumbnail creation failed: {e}")
            return False

    def get_image_metadata(self, image_path: Path) -> dict:
        """Extract metadata from the screenshot."""
        try:
            with Image.open(image_path) as img:
                return {
                    "width": img.width,
                    "height": img.height,
                    "format": img.format,
                    "mode": img.mode,
                    "file_size": image_path.stat().st_size,
                }
        except Exception as e:
            logger.error(f"Failed to extract image metadata: {e}")
            return {}

    def analyze_image_content(self, image_path: Path) -> dict:
        """Analyze image content for dominant colors and features."""
        try:
            # Load image with OpenCV
            img = cv2.imread(str(image_path))
            if img is None:
                return {}

            # Convert BGR to RGB
            img_rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)

            # Get dominant colors
            dominant_colors = self._get_dominant_colors(img_rgb)

            # Basic image analysis
            has_text_regions = self._detect_text_regions(img)

            return {
                "dominant_colors": dominant_colors,
                "has_potential_text": has_text_regions,
                "image_complexity": self._calculate_complexity(img),
            }

        except Exception as e:
            logger.error(f"Image analysis failed: {e}")
            return {}

    def _get_dominant_colors(self, img: np.ndarray, k: int = 5) -> List[str]:
        """Extract dominant colors from the image."""
        try:
            # Reshape image to be a list of pixels
            data = img.reshape((-1, 3))

            # Apply k-means clustering
            criteria = (cv2.TERM_CRITERIA_EPS + cv2.TERM_CRITERIA_MAX_ITER, 20, 1.0)
            _, labels, centers = cv2.kmeans(
                data.astype(np.float32),
                k,
                None,
                criteria,
                10,
                cv2.KMEANS_RANDOM_CENTERS,
            )

            # Convert centers to hex colors
            hex_colors = []
            for center in centers:
                color = tuple(int(c) for c in center)
                hex_color = f"#{color[0]:02x}{color[1]:02x}{color[2]:02x}"
                hex_colors.append(hex_color)

            return hex_colors

        except Exception as e:
            logger.error(f"Dominant color extraction failed: {e}")
            return []

    def _detect_text_regions(self, img: np.ndarray) -> bool:
        """Detect if image likely contains text."""
        try:
            # Convert to grayscale
            gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

            # Apply edge detection
            edges = cv2.Canny(gray, 50, 150, apertureSize=3)

            # Find contours
            contours, _ = cv2.findContours(
                edges, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE
            )

            # Look for text-like rectangular regions
            text_regions = 0
            for contour in contours:
                x, y, w, h = cv2.boundingRect(contour)
                aspect_ratio = w / h if h > 0 else 0

                # Text regions typically have certain aspect ratios and sizes
                if 0.2 < aspect_ratio < 20 and w > 10 and h > 5:
                    text_regions += 1

            return text_regions > 10  # Threshold for "likely contains text"

        except Exception:
            return False

    def _calculate_complexity(self, img: np.ndarray) -> float:
        """Calculate image complexity based on edge density."""
        try:
            gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
            edges = cv2.Canny(gray, 50, 150)
            return np.sum(edges) / (img.shape[0] * img.shape[1] * 255)
        except Exception:
            return 0.0

    def is_screen_locked(self) -> bool:
        """Check if the screen is locked (basic detection)."""
        try:
            # Check for common lock screen processes
            lock_processes = ["swaylock", "waylock", "gtklock"]

            for process in lock_processes:
                result = subprocess.run(
                    ["pgrep", process], capture_output=True, timeout=2
                )
                if result.returncode == 0:
                    return True

            return False
        except (subprocess.TimeoutExpired, FileNotFoundError):
            return False

    def get_active_window_info(self) -> dict:
        """Get information about the currently active window."""
        return self.window_info.get_active_window_info()

    def get_window_list(self) -> List[dict]:
        """Get list of all windows."""
        return self.window_info.get_window_list()

    def get_compositor_type(self) -> str:
        """Get the detected compositor type."""
        return self.window_info.compositor_type
