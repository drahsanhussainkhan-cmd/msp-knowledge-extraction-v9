"""
Base extractor class - all extractors inherit from this
"""
from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Tuple
import re
import logging

try:
    from ..core.enums import DocumentType
except ImportError:
    from core.enums import DocumentType

try:
    from ..utils.bibliography_detector import BibliographyDetector
    from ..utils.filters import GarbleDetector
    from ..utils.nlp_filters import NLPFilter
except ImportError:
    from utils.bibliography_detector import BibliographyDetector
    from utils.filters import GarbleDetector
    from utils.nlp_filters import NLPFilter

logger = logging.getLogger(__name__)

# Shared singleton instances to avoid re-instantiation per extractor
_shared_bib_detector = None
_shared_garble_detector = None
_shared_nlp_filter = None


def _get_bib_detector():
    global _shared_bib_detector
    if _shared_bib_detector is None:
        _shared_bib_detector = BibliographyDetector()
    return _shared_bib_detector


def _get_garble_detector():
    global _shared_garble_detector
    if _shared_garble_detector is None:
        _shared_garble_detector = GarbleDetector()
    return _shared_garble_detector


def _get_nlp_filter():
    global _shared_nlp_filter
    if _shared_nlp_filter is None:
        _shared_nlp_filter = NLPFilter()
    return _shared_nlp_filter


class BaseExtractor(ABC):
    """Base class for all extractors"""

    def __init__(self, keywords, sentence_segmenter, fp_filter,
                 legal_ref_filter=None, number_converter=None):
        """
        Initialize base extractor

        Args:
            keywords: Keywords dictionary
            sentence_segmenter: Sentence segmentation utility
            fp_filter: False positive filter
            legal_ref_filter: Legal reference filter (optional)
            number_converter: Written number converter (optional)
        """
        self.keywords = keywords
        self.sentence_segmenter = sentence_segmenter
        self.fp_filter = fp_filter
        self.legal_ref_filter = legal_ref_filter
        self.number_converter = number_converter
        self.bib_detector = _get_bib_detector()
        self.garble_detector = _get_garble_detector()
        self.nlp_filter = _get_nlp_filter()

        # Cache for bibliography ranges per document (keyed by id(text))
        self._bib_cache = {}

        # Compile patterns
        self._compile_patterns()

    @abstractmethod
    def _compile_patterns(self):
        """Compile regex patterns - must be implemented by subclass"""
        pass

    @abstractmethod
    def extract(self, text: str, page_texts: Dict[int, str],
                doc_type: DocumentType) -> List:
        """
        Extract information from text

        Args:
            text: Full text to extract from
            page_texts: Dict of page_number -> text
            doc_type: Document type

        Returns:
            List of extraction results
        """
        pass

    def _get_language(self, doc_type: DocumentType) -> str:
        """Get language string from document type"""
        if doc_type.value.endswith('_turkish'):
            return 'turkish'
        elif doc_type.value.endswith('_english'):
            return 'english'
        return 'english'  # default

    def _get_sentence_context(self, text: str, start: int, end: int,
                              window: int = 300) -> Tuple[str, str]:
        """
        Get sentence containing match with legal-aware boundaries

        Args:
            text: Full text
            start: Match start position
            end: Match end position
            window: Context window size

        Returns:
            Tuple of (sentence, broader_context)
        """
        # Get broader context
        search_start = max(0, start - window)
        search_end = min(len(text), end + window)
        context = text[search_start:search_end]

        # Use segmenter to find proper sentence boundary
        sentences = self.sentence_segmenter.segment(context)
        match_text = text[start:end]

        # Find sentence containing the match
        for sent in sentences:
            if match_text in sent:
                return sent.strip(), context.strip()

        # Fallback
        return context.strip(), context.strip()

    def _find_page_number(self, position: int, page_texts: Dict[int, str]) -> Optional[int]:
        """Find page number for text position"""
        current = 0
        for page_num in sorted(page_texts.keys()):
            page_end = current + len(page_texts[page_num]) + 2
            if current <= position < page_end:
                return page_num
            current = page_end
        return None

    def _get_bibliography_ranges(self, text: str) -> List[Tuple[int, int]]:
        """
        Get bibliography ranges for a document, with caching.

        Args:
            text: Full document text

        Returns:
            List of (start, end) tuples marking bibliography sections
        """
        text_id = id(text)
        if text_id not in self._bib_cache:
            self._bib_cache[text_id] = self.bib_detector.detect_bibliography_ranges(text)
        return self._bib_cache[text_id]

    def _is_in_bibliography(self, text: str, position: int) -> bool:
        """Check if a match position falls within a bibliography section."""
        ranges = self._get_bibliography_ranges(text)
        return self.bib_detector.is_in_bibliography(position, ranges)

    def _is_garbled(self, text: str) -> bool:
        """Check if extracted text appears to be garbled from PDF column merging."""
        return self.garble_detector.is_garbled(text)

    def _should_skip_match(self, text: str, match_start: int, match_text: str,
                           category: str = "", context: str = "") -> bool:
        """
        Quick pre-filter check before processing a match.
        Returns True if the match should be skipped.

        Applies: bibliography detection, garble detection, NLP validation.
        Call this at the start of _process_match() in each extractor.
        """
        # Skip matches in bibliography/references sections
        if self._is_in_bibliography(text, match_start):
            return True

        # Skip garbled text (regex-based)
        if self._is_garbled(match_text):
            return True

        # NLP validation (NER, POS, coherence, citation, species)
        if category and match_text:
            nlp_result = self.nlp_filter.validate_extraction(
                match_text, category, context=context
            )
            if not nlp_result['is_valid']:
                return True

        return False

    def _get_nlp_confidence(self, text: str, category: str,
                            context: str = "") -> float:
        """
        Get NLP-adjusted confidence multiplier for an extraction.

        Returns a multiplier (0.1-1.5) to adjust the extraction confidence.
        """
        result = self.nlp_filter.validate_extraction(text, category, context=context)
        return result['confidence_multiplier']

    def _is_false_positive(self, sentence: str, match_text: str,
                           language: str = "auto") -> Tuple[bool, str]:
        """
        Check if extraction is a false positive

        Returns:
            Tuple of (is_false_positive, reason)
        """
        return self.fp_filter.is_false_positive(sentence, match_text, language)

    def _identify_activity(self, text: str, language: str) -> Tuple[str, float]:
        """
        Identify MSP activity mentioned in text

        Returns:
            Tuple of (activity_name, confidence)
        """
        text_lower = text.lower()
        scores: Dict[str, int] = {}

        for activity, data in self.keywords.ACTIVITIES.items():
            weight = data.get('weight', 1)
            keywords = data.get(language, data.get('english', []))

            score = sum(weight for kw in keywords if kw.lower() in text_lower)
            if score > 0:
                scores[activity] = score

        if scores:
            best = max(scores.items(), key=lambda x: x[1])
            max_possible = max(d.get('weight', 1) * 5 for d in self.keywords.ACTIVITIES.values())
            confidence = min(best[1] / max_possible, 1.0)
            if best[1] >= 2:
                return best[0], max(confidence, 0.4)

        return 'unspecified', 0.25

    def _identify_reference_point(self, text: str, language: str) -> Tuple[Optional[str], Optional[str]]:
        """
        Identify spatial reference point

        Returns:
            Tuple of (reference_type, reference_text)
        """
        text_lower = text.lower()

        # Get reference points list for this language
        refs = self.keywords.DISTANCE_TERMS.get('reference_points', {}).get(language, [])
        if not refs:
            refs = self.keywords.DISTANCE_TERMS.get('reference_points', {}).get('english', [])

        # refs is a list of terms, not a dict
        for term in refs:
            if term.lower() in text_lower:
                # Extract the actual reference phrase
                pattern = re.compile(rf'\b{re.escape(term)}\w*\b', re.IGNORECASE | re.UNICODE)
                match = pattern.search(text)
                if match:
                    # Classify reference type based on content
                    ref_type = self._classify_reference_type(term)
                    return ref_type, match.group(0)

        return None, None

    def _classify_reference_type(self, term: str) -> str:
        """Classify reference point type based on term"""
        term_lower = term.lower()
        if 'kıyı' in term_lower or 'coast' in term_lower or 'shore' in term_lower:
            return 'coastline'
        elif 'liman' in term_lower or 'port' in term_lower:
            return 'port'
        elif 'koruma' in term_lower or 'protected' in term_lower:
            return 'protected_area'
        elif 'tesis' in term_lower or 'facility' in term_lower:
            return 'facility'
        return 'reference_point'

    def _deduplicate(self, results: List) -> List:
        """Remove duplicate extractions based on extraction_hash"""
        seen = set()
        deduplicated = []

        for result in results:
            hash_val = result.extraction_hash
            if hash_val not in seen:
                seen.add(hash_val)
                deduplicated.append(result)

        return deduplicated
