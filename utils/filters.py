"""
Filters and normalizers for the MSP extractor pipeline.

Contains:
- LegalReferenceFilter: Removes legal references, dates, law numbers
- OCRNormalizer: Fixes common OCR errors in Turkish/English texts
- CrossPageHandler: Joins sentences split across page boundaries
- FalsePositiveFilter: Multi-signal filter for non-MSP false positives
"""

import re
from typing import Dict, List, Tuple, Optional


# =============================================================================
# Config stub with constants referenced by filter classes
# =============================================================================

class Config:
    """Minimal configuration stub for filter thresholds."""
    IMAR_TERM_THRESHOLD = 3
    MARINE_TERM_MINIMUM = 1


# =============================================================================
# === FROM V5.1 === LEGAL REFERENCE FILTER
# =============================================================================

class LegalReferenceFilter:
    """
    Filter out legal references, dates, and law numbers from text
    to prevent them from being misidentified as distance values.

    Removes:
    - Dates: DD/MM/YYYY, D/M/YYYY
    - Law numbers: "X sayılı", "X numbered"
    - Legal reference ranges: "1992-3830" (year-like ranges)
    - Article/regulation numbers: RG-DATE-NUMBER patterns
    """

    def __init__(self):
        self._compile_patterns()

    def _compile_patterns(self):
        """Compile patterns for legal references and dates."""
        # Date patterns
        self.date_patterns = [
            re.compile(r'\d{1,2}/\d{1,2}/\d{4}', re.UNICODE),  # DD/MM/YYYY
            re.compile(r'\d{1,2}\.\d{1,2}\.\d{4}', re.UNICODE),  # DD.MM.YYYY
        ]

        # Law number patterns (Turkish)
        self.law_number_patterns = [
            re.compile(r'\d{1,5}\s+sayılı', re.IGNORECASE | re.UNICODE),  # X sayılı
            re.compile(r'sayılı\s+\d{1,5}', re.IGNORECASE | re.UNICODE),  # sayılı X
        ]

        # Legal reference patterns
        self.legal_ref_patterns = [
            re.compile(r'RG[-\s]\d{1,2}/\d{1,2}/\d{4}[-\s]\d{1,5}', re.IGNORECASE),  # RG-DD/MM/YYYY-XXXX
            re.compile(r'R\.G\.[-\s]\d{1,2}/\d{1,2}/\d{4}', re.IGNORECASE),  # R.G.-DD/MM/YYYY
        ]

        # Year-like ranges (1900-2100) that should NOT be treated as distances
        self.year_range_pattern = re.compile(r'\b(19\d{2}|20\d{2})[-–—](19\d{2}|20\d{2})\b', re.UNICODE)

        # Amendment markers
        self.amendment_patterns = [
            re.compile(r'\(Değişik[^)]*?\)', re.IGNORECASE | re.UNICODE),
            re.compile(r'\(Ek[^)]*?\)', re.IGNORECASE | re.UNICODE),
            re.compile(r'\(İptal[^)]*?\)', re.IGNORECASE | re.UNICODE),
            re.compile(r'\(Amended[^)]*?\)', re.IGNORECASE),
        ]

    def clean_text(self, text: str) -> str:
        """
        Remove legal references and dates from text.

        Args:
            text: Input text

        Returns:
            Cleaned text with legal references removed
        """
        cleaned = text

        # Remove amendment markers (parentheticals with Değişik, Ek, İptal)
        for pattern in self.amendment_patterns:
            cleaned = pattern.sub(' ', cleaned)

        # Remove legal reference patterns
        for pattern in self.legal_ref_patterns:
            cleaned = pattern.sub(' ', cleaned)

        # Remove dates
        for pattern in self.date_patterns:
            cleaned = pattern.sub(' ', cleaned)

        # Remove law numbers
        for pattern in self.law_number_patterns:
            cleaned = pattern.sub(' ', cleaned)

        # Remove year ranges (but keep them for validation check)
        cleaned = self.year_range_pattern.sub(' ', cleaned)

        # Clean up multiple spaces
        cleaned = re.sub(r'\s+', ' ', cleaned)

        return cleaned.strip()

    def is_year_range(self, min_val: float, max_val: float) -> bool:
        """Check if a range looks like a year range (e.g., 1992-3830)."""
        if min_val is None or max_val is None:
            return False
        # Year ranges: both values between 1900-2100
        return (1900 <= min_val <= 2100) and (1900 <= max_val <= 2100)

    def contains_legal_reference(self, text: str) -> bool:
        """Check if text contains legal references or dates."""
        for pattern in self.date_patterns:
            if pattern.search(text):
                return True
        for pattern in self.law_number_patterns:
            if pattern.search(text):
                return True
        for pattern in self.legal_ref_patterns:
            if pattern.search(text):
                return True
        return False


# =============================================================================
# === FROM V5.1 === OCR ERROR NORMALIZER
# =============================================================================

class OCRNormalizer:
    """
    Normalize common OCR errors in Turkish and English legal texts.

    Handles:
    - Turkish character confusion (ı↔i, ş↔s, ç↔c, ğ↔g, ö↔o, ü↔u)
    - Broken diacritics (s¸ → ş, g˘ → ğ)
    - Common ligature issues
    - Whitespace normalization
    """

    SUBSTITUTIONS = [
        # Broken Turkish diacritics
        (r's¸', 'ş'), (r'S¸', 'Ş'),
        (r'c¸', 'ç'), (r'C¸', 'Ç'),
        (r'g˘', 'ğ'), (r'G˘', 'Ğ'),
        (r'o¨', 'ö'), (r'O¨', 'Ö'),
        (r'u¨', 'ü'), (r'U¨', 'Ü'),
        (r'i˙', 'i'), (r'I˙', 'İ'),
        # Quote normalization
        (r'[""]', '"'),
        (r"['']", "'"),
        # Common word breaks
        (r'me\s*tre', 'metre'),
        (r'ki\s*lo\s*met\s*re', 'kilometre'),
        (r'hek\s*tar', 'hektar'),
        (r'met\s*ers?', 'meters'),
        (r'kilo\s*met', 'kilomet'),
    ]

    def __init__(self):
        self.compiled_subs = [
            (re.compile(pattern, re.UNICODE), replacement)
            for pattern, replacement in self.SUBSTITUTIONS
        ]

    def normalize(self, text: str) -> str:
        """Apply OCR normalizations."""
        if not text:
            return text

        result = text
        for pattern, replacement in self.compiled_subs:
            result = pattern.sub(replacement, result)

        # Normalize whitespace
        result = re.sub(r'[ \t]+', ' ', result)
        result = re.sub(r'\n{3,}', '\n\n', result)

        return result

    def estimate_quality(self, text: str) -> float:
        """
        Estimate OCR quality (0-1 scale).

        Higher = better quality.
        """
        if not text:
            return 0.0

        suspicious = 0
        suspicious += len(re.findall(r'[¸˘¨˙]', text))
        suspicious += len(re.findall(r'[a-z][A-Z][a-z]', text))
        suspicious += len(re.findall(r'\d[a-zA-Z]\d', text))
        suspicious += len(re.findall(r'\b\w{25,}\b', text)) * 2

        quality = 1.0 - (suspicious / max(len(text) / 100, 1))
        return max(0.0, min(1.0, quality))


# =============================================================================
# === FROM V5.1 === CROSS-PAGE HANDLER
# =============================================================================

class CrossPageHandler:
    """
    Handle sentence continuation across page boundaries.

    Detects incomplete sentences at page ends and joins them
    with the beginning of the next page.
    """

    def __init__(self):
        self.complete_end = re.compile(r'[.!?]\s*$')
        self.incomplete_end = re.compile(r'[a-zğüşıöç,;:]\s*$', re.IGNORECASE)
        self.continuation_start = re.compile(r'^[a-zğüşıöç]|^\s*[,;]', re.IGNORECASE)

    def process_pages(self, page_texts: Dict[int, str]) -> Tuple[str, Dict[int, str]]:
        """
        Process page texts and join cross-page sentences.

        Args:
            page_texts: Dict of page_number -> text

        Returns:
            Tuple of (unified_text, processed_page_texts)
        """
        if not page_texts:
            return "", {}

        sorted_pages = sorted(page_texts.keys())
        processed = {}

        for i, page_num in enumerate(sorted_pages):
            current_text = page_texts[page_num].strip()

            if i == 0:
                processed[page_num] = current_text
                continue

            prev_page = sorted_pages[i - 1]
            prev_text = processed[prev_page]

            if self._needs_joining(prev_text, current_text):
                processed[prev_page] = prev_text.rstrip() + ' ' + current_text.lstrip()
                processed[page_num] = ""
            else:
                processed[page_num] = current_text

        # Build unified text
        unified = '\n\n'.join(
            processed[p] for p in sorted_pages if processed.get(p)
        )

        return unified, processed

    def _needs_joining(self, prev_text: str, current_text: str) -> bool:
        """Determine if texts should be joined."""
        if not prev_text or not current_text:
            return False

        prev_incomplete = (
            self.incomplete_end.search(prev_text) and
            not self.complete_end.search(prev_text)
        )
        current_continues = self.continuation_start.match(current_text)

        return prev_incomplete or bool(current_continues)


# =============================================================================
# === FROM V5.1 === MULTI-SIGNAL FALSE POSITIVE FILTER (Critical for Q1)
# =============================================================================

class GarbleDetector:
    """
    Detect garbled text from multi-column PDF extraction.

    Cross-line garbling occurs when PDF columns are merged, producing
    nonsensical text like "Cornwall benefits Maritime Strategy" or
    "Many implementation studies 2 Directive".
    """

    def __init__(self):
        # Pattern: multiple short capitalized fragments separated by spaces
        self.fragment_pattern = re.compile(
            r'(?:[A-Z][a-z]{0,3}\s+){4,}',  # 4+ short capitalized words in a row
        )

    def is_garbled(self, text: str) -> bool:
        """
        Check if extracted text appears to be garbled from PDF column merging.

        Args:
            text: The extracted text to check

        Returns:
            True if text appears garbled
        """
        if not text or len(text) < 10:
            return False

        # Check 1: Very long text with no sentence-ending punctuation
        if len(text) > 200 and not re.search(r'[.!?;:]', text[:200]):
            return True

        # Check 2: Text contains newlines within what should be a title/name
        # (e.g., "Full length article\nImplementing the EU MSP")
        lines = text.strip().split('\n')
        if len(lines) >= 2:
            # Multi-line extraction where lines don't form a coherent phrase
            for line in lines:
                line = line.strip()
                if line and len(line) < 30 and not line.endswith((',', '-', ':')):
                    # Short standalone line fragment - likely garbled
                    if not re.match(r'^[A-Z][a-z]+ [A-Z][a-z]+$', line):
                        # Not a proper name pattern
                        return True

        # Check 3: Copyright/journal boilerplate mixed in
        if re.search(r'(?:elsevier|springer|wiley|doi\.org|https?://|www\.)', text.lower()):
            return True

        # Check 4: CRediT statement fragments
        if re.search(r'Writing\s*[-–]\s*(?:review|original|draft)|Methodology|Funding acquisition|Visualization|Validation', text):
            return True

        return False


class FalsePositiveFilter:
    """
    Multi-signal false positive filter for non-MSP extractions.

    This is CRITICAL for precision. Combines 6 signals:
    1. Marine keyword presence
    2. Building/imar term density
    3. Building-specific measurement patterns
    4. Law reference proximity (prevents extracting "Madde 5" as distance)
    5. Sentence structure heuristics
    6. Non-marine domain detection (robotics, ML, path planning)

    Without this filter, the extractor would return many false positives
    from terrestrial planning documents, building regulations, etc.
    """

    # === Building/Imar terms that indicate NON-MSP content ===
    IMAR_BUILDING_TERMS = {
        # Turkish building terms
        'turkish': [
            # Building dimensions
            'kat yüksekliği', 'kat adedi', 'bina yüksekliği', 'bina derinliği',
            'bina cephesi', 'bina gabarisi', 'gabari', 'asma kat', 'ara kat',
            'bodrum kat', 'zemin kat', 'çatı katı', 'teras katı', 'çekme kat',
            # Areas
            'taban alanı', 'inşaat alanı', 'yapı alanı', 'brüt alan',
            'emsal', 'TAKS', 'KAKS', 'imar hakkı',
            # Setbacks (terrestrial)
            'çekme mesafesi', 'yapı yaklaşma', 'ön bahçe', 'yan bahçe', 'arka bahçe',
            'komşu mesafe', 'yol cephesi', 'cephe hattı', 'bina cephe',
            # Parcel
            'parsel', 'parsel sınır', 'parsel hudut', 'parsel köşe',
            'ifraz', 'tevhid', 'kadastro',
            # Building elements
            'pencere', 'kapı', 'merdiven genişliği', 'koridor genişliği',
            'oda yüksekliği', 'tavan yüksekliği', 'döşeme', 'duvar kalınlığı',
            'balkon', 'teras', 'saçak', 'parapet', 'baca',
            # Facilities
            'asansör', 'otopark', 'garaj', 'sığınak', 'kazan dairesi',
            # Zoning
            'konut alanı', 'ticaret alanı', 'sanayi alanı', 'yeşil alan',
            'imar planı', 'imar durumu', 'yapılaşma koşul',
            # Construction
            'temel', 'kolon', 'kiriş', 'çatı', 'cephe kaplama',
        ],
        # English building terms
        'english': [
            'building height', 'floor height', 'storey', 'story',
            'floor area', 'plot ratio', 'site coverage', 'setback',
            'front yard', 'rear yard', 'side yard', 'parcel', 'lot',
            'zoning', 'land use', 'residential', 'commercial',
            'construction', 'foundation', 'basement', 'attic',
            'parking', 'garage', 'elevator', 'stairwell',
        ]
    }

    # === Marine/MSP terms that indicate RELEVANT content ===
    MARINE_TERMS = {
        'turkish': [
            # Coastal
            'kıyı', 'sahil', 'deniz', 'okyanus', 'körfez', 'koy', 'ada',
            'kıyı çizgisi', 'kıyı kenar çizgisi', 'sahil şeridi',
            # Marine activities
            'su ürünleri', 'balık', 'balıkçı', 'balıkçılık', 'avcılık',
            'yetiştiricilik', 'kafes', 'ağ', 'trol', 'dalyan',
            # Infrastructure
            'liman', 'iskele', 'marina', 'tekne', 'gemi', 'yat',
            'dalgakıran', 'mendirek', 'rıhtım',
            # Navigation
            'seyrüsefer', 'seyir', 'demirleme', 'yanaşma',
            # Environment
            'deşarj', 'arıtma', 'atık su', 'deniz kirliliği',
            'koruma alanı', 'sit alanı', 'milli park', 'ÖÇKB',
            # Depth/bathymetry
            'derinlik', 'sığ', 'derin deniz', 'deniz tabanı',
        ],
        'english': [
            # Coastal
            'coast', 'coastal', 'coastline', 'shore', 'shoreline',
            'sea', 'ocean', 'marine', 'maritime', 'offshore',
            'bay', 'gulf', 'island', 'beach',
            # Marine activities
            'fishing', 'fishery', 'aquaculture', 'mariculture',
            'trawl', 'gillnet', 'longline', 'cage',
            # Infrastructure
            'port', 'harbor', 'harbour', 'marina', 'jetty', 'pier',
            'vessel', 'ship', 'boat', 'yacht',
            'breakwater', 'seawall',
            # Navigation
            'navigation', 'shipping', 'anchorage', 'mooring',
            # Environment
            'discharge', 'effluent', 'marine pollution',
            'MPA', 'marine protected', 'conservation',
            # Depth
            'depth', 'bathymetry', 'seabed', 'seafloor',
        ]
    }

    # === Patterns that indicate building context (regex) ===
    BUILDING_PATTERNS = [
        r'\bkat\s+(?:yüksekliği|adedi|sayısı)\b',
        r'\bbina\s+(?:yüksekliği|derinliği|gabarisi)\b',
        r'\b(?:ön|yan|arka)\s+bahçe\b',
        r'\bçekme\s+mesafe',
        r'\bparsel\s+(?:sınır|hudut)',
        r'\b(?:TAKS|KAKS|emsal)\b',
        r'\byapı\s+(?:yaklaşma|ruhsat)',
        r'\b\d+\s*(?:inci|nci|üncü|ncı)\s+kat\b',
        r'\bfloor\s+(?:height|area|ratio)\b',
        r'\bbuilding\s+(?:height|setback|coverage)\b',
        r'\b(?:front|rear|side)\s+yard\b',
        r'\bplot\s+(?:ratio|coverage|area)\b',
    ]

    # === Non-marine domain terms (robotics, ML, path planning) ===
    NON_MARINE_DOMAIN_TERMS = [
        'neural network', 'deep learning', 'machine learning',
        'convolutional', 'recurrent neural', 'backpropagation',
        'path planning', 'trajectory planning', 'motion planning',
        'robot', 'robotic', 'unmanned aerial vehicle', 'UAV',
        'autonomous vehicle', 'self-driving',
        'image classification', 'object detection', 'semantic segmentation',
        'reinforcement learning', 'supervised learning', 'unsupervised learning',
        'training epoch', 'batch size', 'learning rate', 'loss function',
        'CNN strategy', 'RNN', 'LSTM', 'transformer model',
    ]

    # === Patterns indicating law/article references (should not extract) ===
    LAW_REFERENCE_PATTERNS = [
        r'(?:Madde|MADDE|Mad\.)\s*\d+',
        r'\d+\s*sayılı\s*(?:Kanun|Yönetmelik|Tebliğ)',
        r'R\.?G\.?\s*[-:]\s*\d+',
        r'\(\d+\)\s*(?:fıkra|bent)',
        r'\d+[./]\d+[./]\d{4}\s*tarih',
        r'Article\s+\d+',
        r'Section\s+\d+',
        r'Regulation\s+\(\w+\)\s*(?:No\.?)?\s*\d+',
    ]

    def __init__(self):
        self._compile_patterns()

    def _compile_patterns(self):
        """Compile all filter patterns."""
        # Building term patterns
        self.imar_patterns = {}
        for lang, terms in self.IMAR_BUILDING_TERMS.items():
            pattern_str = '|'.join(re.escape(t) for t in terms)
            self.imar_patterns[lang] = re.compile(
                rf'\b({pattern_str})\b', re.IGNORECASE | re.UNICODE
            )

        # Marine term patterns
        self.marine_patterns = {}
        for lang, terms in self.MARINE_TERMS.items():
            pattern_str = '|'.join(re.escape(t) for t in terms)
            self.marine_patterns[lang] = re.compile(
                rf'\b({pattern_str})\b', re.IGNORECASE | re.UNICODE
            )

        # Building-specific patterns
        self.building_patterns = [
            re.compile(p, re.IGNORECASE | re.UNICODE)
            for p in self.BUILDING_PATTERNS
        ]

        # Law reference patterns
        self.law_ref_patterns = [
            re.compile(p, re.IGNORECASE | re.UNICODE)
            for p in self.LAW_REFERENCE_PATTERNS
        ]

        # Non-marine domain patterns
        non_marine_str = '|'.join(re.escape(t) for t in self.NON_MARINE_DOMAIN_TERMS)
        self.non_marine_pattern = re.compile(
            rf'\b({non_marine_str})\b', re.IGNORECASE
        )

        # Garble detector
        self.garble_detector = GarbleDetector()

    def is_false_positive(self, sentence: str, match_text: str,
                          language: str = "auto",
                          context_window: int = 50) -> Tuple[bool, str]:
        """
        Determine if extraction is likely a false positive.

        Args:
            sentence: Full sentence containing match
            match_text: The extracted text
            language: 'turkish', 'english', or 'auto'
            context_window: Characters around match for law ref check

        Returns:
            Tuple of (is_false_positive, reason)
        """
        if not sentence:
            return True, "empty_sentence"

        sentence_lower = sentence.lower()

        # Auto-detect language if needed
        if language == "auto":
            turkish_chars = sum(1 for c in sentence if c in 'çğışöüÇĞİŞÖÜ')
            language = "turkish" if turkish_chars > 2 else "english"

        # === Signal 1: Count building/imar terms ===
        imar_pattern = self.imar_patterns.get(language, self.imar_patterns['english'])
        imar_matches = imar_pattern.findall(sentence_lower)
        imar_count = len(imar_matches)

        # === Signal 2: Count marine terms ===
        marine_pattern = self.marine_patterns.get(language, self.marine_patterns['english'])
        marine_matches = marine_pattern.findall(sentence_lower)
        marine_count = len(marine_matches)

        # === Signal 3: Check building-specific patterns ===
        building_pattern_matches = sum(
            1 for p in self.building_patterns if p.search(sentence)
        )

        # === Signal 4: Check law reference proximity ===
        law_ref_nearby = self._check_law_reference_proximity(
            sentence, match_text, context_window
        )

        # === Signal 5: Check non-marine domain terms ===
        non_marine_matches = self.non_marine_pattern.findall(sentence_lower)
        non_marine_count = len(non_marine_matches)

        # === Decision Logic ===

        # REJECT: Non-marine domain content with no marine terms
        if non_marine_count >= 2 and marine_count == 0:
            return True, f"non_marine_domain({non_marine_count}_nonmarine,0_marine)"

        # REJECT: High imar density with no marine terms
        if imar_count >= Config.IMAR_TERM_THRESHOLD and marine_count == 0:
            return True, f"imar_density({imar_count}_imar,0_marine)"

        # REJECT: Multiple building patterns
        if building_pattern_matches >= 2:
            return True, f"building_patterns({building_pattern_matches})"

        # REJECT: Law reference immediately near the match
        if law_ref_nearby:
            return True, "law_reference_proximity"

        # REJECT: Weighted score check
        fp_score = (
            imar_count * 2 +
            building_pattern_matches * 3 -
            marine_count * 4
        )

        if fp_score > 5 and marine_count == 0:
            return True, f"weighted_score({fp_score})"

        # PASS
        return False, "passed"

    def _check_law_reference_proximity(self, sentence: str, match_text: str,
                                       window: int) -> bool:
        """Check if match is near a law reference pattern."""
        match_pos = sentence.find(match_text)
        if match_pos < 0:
            return False

        start = max(0, match_pos - window)
        end = min(len(sentence), match_pos + len(match_text) + window)
        local_context = sentence[start:end]

        for pattern in self.law_ref_patterns:
            if pattern.search(local_context):
                return True

        return False

    def get_marine_relevance_score(self, sentence: str, language: str = "auto") -> float:
        """
        Calculate marine relevance score (0-1).

        Higher = more likely to be MSP-relevant.
        """
        if not sentence:
            return 0.0

        if language == "auto":
            turkish_chars = sum(1 for c in sentence if c in 'çğışöüÇĞİŞÖÜ')
            language = "turkish" if turkish_chars > 2 else "english"

        sentence_lower = sentence.lower()

        marine_pattern = self.marine_patterns.get(language, self.marine_patterns['english'])
        imar_pattern = self.imar_patterns.get(language, self.imar_patterns['english'])

        marine_count = len(marine_pattern.findall(sentence_lower))
        imar_count = len(imar_pattern.findall(sentence_lower))

        total = marine_count + imar_count
        if total == 0:
            return 0.5  # Neutral

        return marine_count / total

    def is_document_marine_relevant(self, full_text: str, threshold: int = 5) -> bool:
        """
        Check if a document is marine-relevant at the document level.

        Args:
            full_text: Full document text
            threshold: Minimum marine keyword count to be considered relevant

        Returns:
            True if document has sufficient marine content
        """
        text_lower = full_text.lower()
        marine_count = 0
        for lang_pattern in self.marine_patterns.values():
            marine_count += len(lang_pattern.findall(text_lower))
        return marine_count >= threshold
