"""Advanced text processing and tagging for Alexandria using NLTK."""

import logging
import re
import string
from typing import List, Set, Dict, Optional
from pathlib import Path

logger = logging.getLogger(__name__)

try:
    import nltk
    from nltk.tokenize import word_tokenize, sent_tokenize
    from nltk.corpus import stopwords
    from nltk.stem import WordNetLemmatizer
    from nltk.tag import pos_tag
    from nltk.chunk import ne_chunk
    from nltk.tree import Tree

    NLTK_AVAILABLE = True
except ImportError:
    NLTK_AVAILABLE = False
    logger.warning("NLTK not available, falling back to basic text processing")


class TextProcessor:
    """Advanced text processing with NLTK for tag generation."""

    def __init__(self):
        self.nltk_ready = False
        self.lemmatizer = None
        self.stop_words = set()

        if NLTK_AVAILABLE:
            self._setup_nltk()
        else:
            logger.warning("NLTK not available, using basic processing")

    def _setup_nltk(self):
        """Set up NLTK components and download required data."""
        try:
            # Try to use existing data first
            try:
                nltk.data.find("tokenizers/punkt")
                nltk.data.find("corpora/stopwords")
                nltk.data.find("corpora/wordnet")
                nltk.data.find("taggers/averaged_perceptron_tagger")
                nltk.data.find("chunkers/maxent_ne_chunker")
                nltk.data.find("corpora/words")
            except LookupError:
                # Download required NLTK data
                logger.info("Downloading required NLTK data...")
                nltk.download("punkt", quiet=True)
                nltk.download("stopwords", quiet=True)
                nltk.download("wordnet", quiet=True)
                nltk.download("averaged_perceptron_tagger", quiet=True)
                nltk.download("maxent_ne_chunker", quiet=True)
                nltk.download("words", quiet=True)
                # Also download the newer tagger if available
                try:
                    nltk.download("averaged_perceptron_tagger_eng", quiet=True)
                    nltk.download("maxent_ne_chunker_tab", quiet=True)
                except:
                    pass

            # Initialize components
            self.lemmatizer = WordNetLemmatizer()
            self.stop_words = set(stopwords.words("english"))
            self.nltk_ready = True
            logger.info("NLTK initialized successfully")

        except Exception as e:
            logger.error(f"Failed to initialize NLTK: {e}")
            self.nltk_ready = False

    def extract_keywords_from_text(
        self, text: str, max_keywords: int = 15
    ) -> List[str]:
        """Extract and lemmatize keywords from OCR text."""
        if not text or not text.strip():
            return []

        if self.nltk_ready:
            return self._extract_keywords_nltk(text, max_keywords)
        else:
            return self._extract_keywords_basic(text, max_keywords)

    def _extract_keywords_nltk(self, text: str, max_keywords: int) -> List[str]:
        """Extract keywords using NLTK with lemmatization."""
        try:
            # Tokenize and clean text
            tokens = word_tokenize(text.lower())

            # Remove punctuation and non-alphabetic tokens
            tokens = [token for token in tokens if token.isalpha() and len(token) > 2]

            # Remove stop words
            tokens = [token for token in tokens if token not in self.stop_words]

            # Part-of-speech tagging with error handling
            try:
                pos_tags = pos_tag(tokens)
            except LookupError as e:
                logger.warning(
                    f"POS tagging failed: {e}, falling back to basic processing"
                )
                return self._extract_keywords_basic(text, max_keywords)

            # Keep only nouns, verbs, and adjectives
            interesting_pos = {
                "NN",
                "NNS",
                "NNP",
                "NNPS",
                "VB",
                "VBD",
                "VBG",
                "VBN",
                "VBP",
                "VBZ",
                "JJ",
                "JJR",
                "JJS",
            }
            filtered_tokens = [
                token for token, pos in pos_tags if pos in interesting_pos
            ]

            # Lemmatize tokens
            lemmatized = []
            for token in filtered_tokens:
                try:
                    # Get the appropriate POS for lemmatization
                    pos = self._get_wordnet_pos(pos_tags, token)
                    lemma = self.lemmatizer.lemmatize(token, pos)
                    lemmatized.append(lemma)
                except Exception as e:
                    # If lemmatization fails, use the original token
                    lemmatized.append(token)

            # Extract named entities with error handling
            try:
                named_entities = self._extract_named_entities(text)
            except Exception as e:
                logger.debug(f"Named entity extraction failed: {e}")
                named_entities = []

            # Combine and count frequency
            all_keywords = lemmatized + named_entities
            keyword_freq = {}
            for keyword in all_keywords:
                keyword_freq[keyword] = keyword_freq.get(keyword, 0) + 1

            # Sort by frequency and return top keywords
            sorted_keywords = sorted(
                keyword_freq.items(), key=lambda x: x[1], reverse=True
            )
            return [keyword for keyword, freq in sorted_keywords[:max_keywords]]

        except Exception as e:
            logger.error(f"Error in NLTK keyword extraction: {e}")
            return self._extract_keywords_basic(text, max_keywords)

    def _extract_keywords_basic(self, text: str, max_keywords: int) -> List[str]:
        """Basic keyword extraction without NLTK."""
        # Simple word extraction and filtering
        words = re.findall(r"\b[a-zA-Z]{3,}\b", text.lower())

        # Basic stop words
        basic_stop_words = {
            "the",
            "and",
            "or",
            "but",
            "in",
            "on",
            "at",
            "to",
            "for",
            "of",
            "with",
            "by",
            "from",
            "up",
            "about",
            "into",
            "through",
            "during",
            "before",
            "after",
            "above",
            "below",
            "out",
            "off",
            "down",
            "under",
            "again",
            "further",
            "then",
            "once",
            "here",
            "there",
            "when",
            "where",
            "why",
            "how",
            "all",
            "any",
            "both",
            "each",
            "few",
            "more",
            "most",
            "other",
            "some",
            "such",
            "only",
            "own",
            "same",
            "than",
            "too",
            "very",
            "can",
            "will",
            "just",
            "should",
            "now",
            "this",
            "that",
            "these",
            "those",
        }

        # Filter words
        filtered_words = [word for word in words if word not in basic_stop_words]

        # Count frequency
        word_freq = {}
        for word in filtered_words:
            word_freq[word] = word_freq.get(word, 0) + 1

        # Sort by frequency
        sorted_words = sorted(word_freq.items(), key=lambda x: x[1], reverse=True)
        return [word for word, freq in sorted_words[:max_keywords]]

    def _get_wordnet_pos(self, pos_tags: List[tuple], token: str) -> str:
        """Convert POS tag to WordNet POS for lemmatization."""
        # Find the POS tag for the token
        pos = None
        for word, tag in pos_tags:
            if word == token:
                pos = tag
                break

        if not pos:
            return "n"  # Default to noun

        # Convert to WordNet POS
        if pos.startswith("J"):
            return "a"  # Adjective
        elif pos.startswith("V"):
            return "v"  # Verb
        elif pos.startswith("R"):
            return "r"  # Adverb
        else:
            return "n"  # Noun (default)

    def _extract_named_entities(self, text: str) -> List[str]:
        """Extract named entities from text."""
        try:
            tokens = word_tokenize(text)
            pos_tags = pos_tag(tokens)
            chunks = ne_chunk(pos_tags)

            entities = []
            for chunk in chunks:
                if isinstance(chunk, Tree):
                    # This is a named entity
                    entity = " ".join([token for token, pos in chunk.leaves()])
                    entities.append(entity.lower())

            return entities

        except Exception as e:
            logger.error(f"Error extracting named entities: {e}")
            return []

    def generate_window_app_tags(self, window_info: Dict) -> List[str]:
        """Generate tags from window and application information."""
        tags = []

        # Process application name
        app_id = window_info.get("app_id", "")
        if app_id:
            # Clean and lemmatize app name
            app_clean = self._clean_app_name(app_id)
            if app_clean:
                tags.append(f"app:{app_clean}")

                # Add lemmatized version if different
                if self.nltk_ready and self.lemmatizer:
                    lemmatized = self.lemmatizer.lemmatize(app_clean.lower())
                    if lemmatized != app_clean.lower():
                        tags.append(f"app:{lemmatized}")

        # Process window title
        title = window_info.get("title", "")
        if title:
            # Extract keywords from window title
            title_keywords = self.extract_keywords_from_text(title, max_keywords=5)
            for keyword in title_keywords:
                tags.append(f"title:{keyword}")

        # Process window class
        window_class = window_info.get("window_class", "")
        if window_class and window_class != app_id:
            class_clean = self._clean_app_name(window_class)
            if class_clean:
                tags.append(f"class:{class_clean}")

        # Add workspace information
        workspace = window_info.get("workspace", "")
        if workspace:
            tags.append(f"workspace:{workspace}")

        # Add geometry category
        geometry = window_info.get("geometry", "")
        if geometry:
            tags.append(f"geometry:{geometry}")

            # Extract size category
            size_category = self._categorize_window_size(geometry)
            if size_category:
                tags.append(f"size:{size_category}")

        return tags

    def _clean_app_name(self, app_name: str) -> str:
        """Clean and normalize application names."""
        if not app_name:
            return ""

        # Remove common suffixes and prefixes
        cleaned = app_name.lower()
        cleaned = re.sub(r"\.(exe|app|desktop)$", "", cleaned)
        cleaned = re.sub(r"^(org\.|com\.|net\.)", "", cleaned)

        # Remove version numbers
        cleaned = re.sub(r"[-_]?\d+(\.\d+)*$", "", cleaned)

        # Replace separators with spaces for keyword extraction
        cleaned = re.sub(r"[-_.]", " ", cleaned)

        # Get the main part (usually the first word)
        words = cleaned.split()
        if words:
            main_word = words[0]
            # Lemmatize if possible
            if self.nltk_ready and self.lemmatizer:
                main_word = self.lemmatizer.lemmatize(main_word)
            return main_word

        return cleaned

    def _categorize_window_size(self, geometry: str) -> Optional[str]:
        """Categorize window size based on geometry string."""
        try:
            # Parse geometry string like "1920x1080+0+0"
            match = re.match(r"(\d+)x(\d+)", geometry)
            if match:
                width, height = int(match.group(1)), int(match.group(2))
                area = width * height

                # Categorize by area
                if area < 300000:  # < 300k pixels (e.g., 640x480)
                    return "small"
                elif area < 1000000:  # < 1M pixels (e.g., 1024x768)
                    return "medium"
                elif area < 2000000:  # < 2M pixels (e.g., 1920x1080)
                    return "large"
                else:
                    return "xlarge"

        except Exception:
            pass

        return None

    def generate_content_tags(
        self, ocr_text: str, window_info: Dict, max_total_tags: int = 20
    ) -> List[str]:
        """Generate comprehensive tags from OCR text and window information."""
        all_tags = []

        # Extract keywords from OCR text
        if ocr_text:
            text_keywords = self.extract_keywords_from_text(ocr_text, max_keywords=10)
            all_tags.extend(text_keywords)

        # Add window/app information tags
        window_tags = self.generate_window_app_tags(window_info)
        all_tags.extend(window_tags)

        # Add timestamp-based tags (could be added by caller)

        # Remove duplicates while preserving order
        seen = set()
        unique_tags = []
        for tag in all_tags:
            if tag not in seen:
                seen.add(tag)
                unique_tags.append(tag)

        # Limit total number of tags
        return unique_tags[:max_total_tags]

    def analyze_text_sentiment(self, text: str) -> Dict[str, float]:
        """Basic sentiment analysis (could be enhanced with additional libraries)."""
        if not text:
            return {"sentiment": "neutral", "confidence": 0.0}

        # Simple keyword-based sentiment analysis
        positive_words = {
            "good",
            "great",
            "excellent",
            "amazing",
            "wonderful",
            "fantastic",
            "success",
            "successful",
            "complete",
            "completed",
            "done",
            "finished",
            "yes",
            "correct",
            "right",
            "perfect",
            "awesome",
            "love",
            "like",
        }

        negative_words = {
            "bad",
            "terrible",
            "awful",
            "horrible",
            "error",
            "fail",
            "failed",
            "wrong",
            "incorrect",
            "problem",
            "issue",
            "bug",
            "crash",
            "broken",
            "no",
            "not",
            "never",
            "hate",
            "dislike",
            "impossible",
        }

        words = re.findall(r"\b[a-zA-Z]+\b", text.lower())

        positive_count = sum(1 for word in words if word in positive_words)
        negative_count = sum(1 for word in words if word in negative_words)
        total_sentiment_words = positive_count + negative_count

        if total_sentiment_words == 0:
            return {"sentiment": "neutral", "confidence": 0.0}

        if positive_count > negative_count:
            confidence = positive_count / total_sentiment_words
            return {"sentiment": "positive", "confidence": confidence}
        elif negative_count > positive_count:
            confidence = negative_count / total_sentiment_words
            return {"sentiment": "negative", "confidence": confidence}
        else:
            return {"sentiment": "neutral", "confidence": 0.5}
