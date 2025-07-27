"""OCR processing functionality."""

import logging
from pathlib import Path
from typing import Dict, List, Optional, Tuple
import json

import pytesseract
from PIL import Image, ImageEnhance, ImageFilter
import cv2
import numpy as np

from .text_processor import TextProcessor

logger = logging.getLogger(__name__)


class OCRProcessor:
    """OCR processing using Tesseract."""

    def __init__(self, config):
        self.config = config
        self.language = config.get("ocr", "language")
        self.confidence_threshold = config.get("ocr", "confidence_threshold")
        self.preprocess_enabled = config.get("ocr", "preprocess_image")

        # Initialize text processor for advanced keyword extraction
        self.text_processor = TextProcessor()

        # Verify Tesseract is available
        if not self._check_tesseract_available():
            raise RuntimeError("Tesseract OCR is not available")

    def _check_tesseract_available(self) -> bool:
        """Check if Tesseract is available."""
        try:
            pytesseract.get_tesseract_version()
            return True
        except Exception:
            return False

    def process_image(self, image_path: Path) -> Dict[str, any]:
        """Process image with OCR and return results."""
        try:
            # Load image
            image = Image.open(image_path)

            # Preprocess if enabled
            if self.preprocess_enabled:
                image = self._preprocess_image(image)

            # Perform OCR with detailed data
            ocr_data = pytesseract.image_to_data(
                image,
                lang=self.language,
                output_type=pytesseract.Output.DICT,
                config="--psm 6",  # Assume a single uniform block of text
            )

            # Extract text with confidence filtering
            text, confidence = self._extract_text_with_confidence(ocr_data)

            # Get structured OCR data
            structured_data = self._structure_ocr_data(ocr_data)

            # Detect sensitive information
            has_sensitive = self._detect_sensitive_info(text)

            return {
                "text": text,
                "confidence": confidence,
                "has_text": bool(text.strip()),
                "has_sensitive": has_sensitive,
                "structured_data": structured_data,
                "word_count": len(text.split()) if text else 0,
                "character_count": len(text) if text else 0,
            }

        except Exception as e:
            logger.error(f"OCR processing failed for {image_path}: {e}")
            return {
                "text": "",
                "confidence": 0,
                "has_text": False,
                "has_sensitive": False,
                "structured_data": {},
                "word_count": 0,
                "character_count": 0,
            }

    def _preprocess_image(self, image: Image.Image) -> Image.Image:
        """Preprocess image to improve OCR accuracy."""
        try:
            # Convert to grayscale if not already
            if image.mode != "L":
                image = image.convert("L")

            # Enhance contrast
            enhancer = ImageEnhance.Contrast(image)
            image = enhancer.enhance(1.5)

            # Enhance sharpness
            enhancer = ImageEnhance.Sharpness(image)
            image = enhancer.enhance(2.0)

            # Apply slight blur to reduce noise
            image = image.filter(ImageFilter.MedianFilter(size=3))

            # Scale up if image is too small
            width, height = image.size
            if width < 1000 or height < 1000:
                scale_factor = max(1000 / width, 1000 / height)
                new_size = (int(width * scale_factor), int(height * scale_factor))
                image = image.resize(new_size, Image.Resampling.LANCZOS)

            return image

        except Exception as e:
            logger.warning(f"Image preprocessing failed: {e}")
            return image

    def _extract_text_with_confidence(self, ocr_data: Dict) -> Tuple[str, float]:
        """Extract text with confidence filtering."""
        words = []
        confidences = []

        for i, conf in enumerate(ocr_data["conf"]):
            if int(conf) >= self.confidence_threshold:
                text = ocr_data["text"][i].strip()
                if text:
                    words.append(text)
                    confidences.append(int(conf))

        full_text = " ".join(words)
        avg_confidence = sum(confidences) / len(confidences) if confidences else 0

        return full_text, avg_confidence

    def _structure_ocr_data(self, ocr_data: Dict) -> Dict:
        """Structure OCR data into a more useful format."""
        try:
            words = []
            lines = []
            paragraphs = []

            current_line = []
            current_paragraph = []

            prev_line_num = None
            prev_par_num = None

            for i in range(len(ocr_data["text"])):
                conf = int(ocr_data["conf"][i])
                text = ocr_data["text"][i].strip()

                if conf >= self.confidence_threshold and text:
                    word_data = {
                        "text": text,
                        "confidence": conf,
                        "left": ocr_data["left"][i],
                        "top": ocr_data["top"][i],
                        "width": ocr_data["width"][i],
                        "height": ocr_data["height"][i],
                    }
                    words.append(word_data)

                    line_num = ocr_data["line_num"][i]
                    par_num = ocr_data["par_num"][i]

                    # Track lines
                    if prev_line_num is not None and line_num != prev_line_num:
                        if current_line:
                            lines.append(
                                {
                                    "text": " ".join([w["text"] for w in current_line]),
                                    "words": current_line,
                                    "bbox": self._get_bounding_box(current_line),
                                }
                            )
                            current_line = []

                    current_line.append(word_data)

                    # Track paragraphs
                    if prev_par_num is not None and par_num != prev_par_num:
                        if current_paragraph:
                            paragraphs.append(
                                {
                                    "text": " ".join(
                                        [w["text"] for w in current_paragraph]
                                    ),
                                    "words": current_paragraph,
                                    "bbox": self._get_bounding_box(current_paragraph),
                                }
                            )
                            current_paragraph = []

                    current_paragraph.append(word_data)

                    prev_line_num = line_num
                    prev_par_num = par_num

            # Add final line and paragraph
            if current_line:
                lines.append(
                    {
                        "text": " ".join([w["text"] for w in current_line]),
                        "words": current_line,
                        "bbox": self._get_bounding_box(current_line),
                    }
                )

            if current_paragraph:
                paragraphs.append(
                    {
                        "text": " ".join([w["text"] for w in current_paragraph]),
                        "words": current_paragraph,
                        "bbox": self._get_bounding_box(current_paragraph),
                    }
                )

            return {
                "words": words,
                "lines": lines,
                "paragraphs": paragraphs,
                "total_words": len(words),
                "total_lines": len(lines),
                "total_paragraphs": len(paragraphs),
            }

        except Exception as e:
            logger.error(f"OCR data structuring failed: {e}")
            return {}

    def _get_bounding_box(self, elements: List[Dict]) -> Dict[str, int]:
        """Calculate bounding box for a list of text elements."""
        if not elements:
            return {"left": 0, "top": 0, "width": 0, "height": 0}

        lefts = [e["left"] for e in elements]
        tops = [e["top"] for e in elements]
        rights = [e["left"] + e["width"] for e in elements]
        bottoms = [e["top"] + e["height"] for e in elements]

        left = min(lefts)
        top = min(tops)
        right = max(rights)
        bottom = max(bottoms)

        return {"left": left, "top": top, "width": right - left, "height": bottom - top}

    def _detect_sensitive_info(self, text: str) -> bool:
        """Detect potentially sensitive information in text."""
        if not text:
            return False

        text_lower = text.lower()

        # Common sensitive patterns
        sensitive_patterns = [
            # Authentication
            "password",
            "passwd",
            "pwd",
            "login",
            "username",
            "pin",
            # Financial
            "credit card",
            "debit card",
            "bank account",
            "routing number",
            "ssn",
            "social security",
            # Personal identifiers
            "driver license",
            "passport",
            "id number",
            "employee id",
            # Common form fields
            "confirm password",
            "current password",
            "new password",
            # URLs that might be sensitive
            "token",
            "api key",
            "secret",
        ]

        for pattern in sensitive_patterns:
            if pattern in text_lower:
                return True

        # Check for credit card number patterns (basic)
        import re

        credit_card_pattern = r"\b\d{4}[\s-]?\d{4}[\s-]?\d{4}[\s-]?\d{4}\b"
        if re.search(credit_card_pattern, text):
            return True

        # Check for SSN pattern (basic)
        ssn_pattern = r"\b\d{3}[-.]?\d{2}[-.]?\d{4}\b"
        if re.search(ssn_pattern, text):
            return True

        return False

    def extract_keywords(self, text: str) -> List[str]:
        """Extract potential keywords/tags from text using advanced NLTK processing."""
        return self.text_processor.extract_keywords_from_text(text, max_keywords=10)
