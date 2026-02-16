"""
Text processing utilities for MSP Extractor.

Contains:
- TurkishLegalSentenceSegmenter: Sentence segmentation for Turkish legal texts
- MultilingualNumberConverter: Convert written numbers to digits (Turkish/English)
- RangeResult / RangeParser: Parse numeric ranges in Turkish and English text
"""

import re
from typing import Dict, List, Optional, Tuple, NamedTuple


# ---------------------------------------------------------------------------
# Config stub – only the constants referenced by classes in this module
# ---------------------------------------------------------------------------

class Config:
    """Minimal configuration stub for text processing utilities."""
    MIN_SENTENCE_LENGTH = 15


# =============================================================================
# === TURKISH LEGAL SENTENCE SEGMENTER
# =============================================================================

class TurkishLegalSentenceSegmenter:
    """
    Robust sentence segmentation for Turkish legal texts.

    Handles:
    - Legal abbreviations: Mad., m., fık., bent, par., vd., vb., vs.
    - Semicolon-heavy legal writing style
    - Parenthetical clauses with internal punctuation
    - Article numbering patterns (Madde 5 -, 5 inci madde)
    - Enumeration patterns (a), b), 1., 2.)

    This is critical for Turkish legal documents where naive splitting
    on periods would break many sentences incorrectly.
    """

    # Abbreviations that should NOT end sentences
    TURKISH_LEGAL_ABBREVIATIONS = [
        r'Mad\.', r'mad\.', r'MADDE\.?',
        r'm\.', r'M\.',
        r'fık\.', r'Fık\.', r'fıkra\.?',
        r'bent\.?', r'Bent\.?',
        r'par\.', r'Par\.', r'paragraf\.?',
        r'vd\.', r'vb\.', r'vs\.', r'bkz\.',
        r'Dr\.', r'Prof\.', r'Doç\.',
        r'No\.', r'no\.', r'Nr\.',
        r'yön\.', r'Yön\.', r'kan\.', r'Kan\.',
        r'md\.', r'Md\.',
        r'tarih\.?', r'tar\.',
        r'say\.', r'sayılı\.?',
        r'R\.G\.', r'RG\.',
        r'T\.C\.', r'TC\.',
        r'a\.', r'b\.', r'c\.', r'ç\.', r'd\.',
        r'ş\.', r'Ş\.',
    ]

    ENGLISH_ABBREVIATIONS = [
        r'Dr\.', r'Mr\.', r'Mrs\.', r'Ms\.', r'Prof\.', r'Jr\.', r'Sr\.',
        r'Fig\.', r'fig\.', r'Tab\.', r'tab\.', r'Vol\.', r'vol\.',
        r'No\.', r'no\.', r'vs\.', r'etc\.', r'e\.g\.', r'i\.e\.',
        r'al\.', r'pp\.', r'ed\.', r'eds\.', r'ch\.', r'sec\.',
        r'Art\.', r'art\.', r'Reg\.', r'reg\.',
    ]

    def __init__(self):
        self._compile_patterns()

    def _compile_patterns(self):
        """Compile regex patterns for segmentation."""
        all_abbrevs = self.TURKISH_LEGAL_ABBREVIATIONS + self.ENGLISH_ABBREVIATIONS
        abbrev_pattern = '|'.join(all_abbrevs)
        self.abbrev_regex = re.compile(rf'({abbrev_pattern})\s*$', re.IGNORECASE)

        # Sentence-ending punctuation followed by uppercase
        self.sent_end_pattern = re.compile(
            r'(?<![A-Za-zğüşıöçĞÜŞİÖÇ])([.!?])\s+(?=[A-ZĞÜŞİÖÇ(0-9])',
            re.UNICODE
        )

        # Article headers (major boundaries)
        self.article_header = re.compile(
            r'(?:MADDE|Madde)\s+\d+\s*[-–—]',
            re.UNICODE
        )

    def segment(self, text: str) -> List[str]:
        """
        Segment text into sentences with legal-aware rules.

        Args:
            text: Input text

        Returns:
            List of sentences
        """
        if not text or len(text.strip()) < Config.MIN_SENTENCE_LENGTH:
            return [text.strip()] if text and text.strip() else []

        # Remove footnote references (standalone numbers at start of line followed by dates)
        text = self._remove_footnotes(text)

        # Split on definition patterns first (helps with glossary sections)
        text = self._split_definitions(text)

        # Protect abbreviations
        protected = self._protect_abbreviations(text)

        # Split on article headers first
        chunks = self._split_on_articles(protected)

        # Split each chunk on sentence endings
        sentences = []
        for chunk in chunks:
            parts = self._split_on_punctuation(chunk)
            sentences.extend(parts)

        # Restore and clean
        sentences = [self._restore_abbreviations(s).strip() for s in sentences]
        sentences = [s for s in sentences if len(s) >= Config.MIN_SENTENCE_LENGTH]

        return sentences

    def _remove_footnotes(self, text: str) -> str:
        """Remove legal footnotes that contain references and dates."""
        # Pattern: newline followed by single digit, then date pattern or legal ref
        # Example: "\n1 31/10/2016 tarihli ve 678 sayılı..."
        footnote_pattern = re.compile(
            r'\n\d{1,2}\s+\d{1,2}/\d{1,2}/\d{4}[^\n]*?(?=\n[A-ZĞÜŞIÖÇ]|\n\n|$)',
            re.UNICODE
        )
        text = footnote_pattern.sub('', text)

        # Also remove parenthetical amendments with dates and law numbers
        # Example: "(Değişik:RG-1/7/1992-3830/1 md.)"
        amendment_pattern = re.compile(
            r'\([^)]*?\d{1,2}/\d{1,2}/\d{4}[^)]*?\)',
            re.UNICODE
        )
        text = amendment_pattern.sub('', text)

        return text

    def _split_definitions(self, text: str) -> str:
        """Add sentence breaks after definition patterns."""
        # Pattern: "Term: Definition text"
        # Add period before next definition to help segmentation
        definition_pattern = re.compile(
            r'((?:[A-ZĞÜŞİÖÇ][a-zğüşıöç]+\s*)+):\s+([^,\n]+(?:,\s*)?)',
            re.UNICODE
        )
        # Replace with term: definition. to help segmentation
        # But only if not already followed by punctuation
        def add_period(match):
            term = match.group(1)
            definition = match.group(2).rstrip(',. ')
            # Check if followed by another capital letter (next definition)
            return f"{term}: {definition}."

        return definition_pattern.sub(add_period, text)

    def _protect_abbreviations(self, text: str) -> str:
        """Replace abbreviation periods with placeholder."""
        result = text
        all_abbrevs = self.TURKISH_LEGAL_ABBREVIATIONS + self.ENGLISH_ABBREVIATIONS
        for abbrev in all_abbrevs:
            literal = abbrev.replace(r'\.', '.').replace('?', '')
            if '.' in literal:
                protected = literal.replace('.', '\u2E30')
                result = re.sub(re.escape(literal), protected, result, flags=re.IGNORECASE)
        return result

    def _restore_abbreviations(self, text: str) -> str:
        """Restore protected periods."""
        return text.replace('\u2E30', '.')

    def _split_on_articles(self, text: str) -> List[str]:
        """Split on article headers."""
        matches = list(self.article_header.finditer(text))
        if not matches:
            return [text]

        result = []
        last_end = 0
        for match in matches:
            if match.start() > last_end:
                result.append(text[last_end:match.start()])
            last_end = match.start()

        if last_end < len(text):
            result.append(text[last_end:])

        return [p for p in result if p.strip()]

    def _split_on_punctuation(self, text: str) -> List[str]:
        """Split on sentence-ending punctuation."""
        parts = []
        last_end = 0

        for match in self.sent_end_pattern.finditer(text):
            end_pos = match.end() - 1
            candidate = text[last_end:end_pos].strip()

            if not self.abbrev_regex.search(candidate):
                parts.append(candidate)
                last_end = match.end() - 1

        if last_end < len(text):
            remaining = text[last_end:].strip()
            if remaining:
                parts.append(remaining)

        return parts if parts else [text]


# =============================================================================
# === MULTILINGUAL NUMBER CONVERTER (Turkish + English)
# =============================================================================

class MultilingualNumberConverter:
    """
    Convert written numbers to digits in Turkish and English.

    Turkish examples:
    - "yüz elli" → 150
    - "iki bin beş yüz" → 2500
    - "iki buçuk milyon" → 2,500,000
    - "on beş" → 15

    English examples:
    - "one hundred fifty" → 150
    - "two thousand five hundred" → 2500
    - "two and a half million" → 2,500,000
    """

    # Turkish numbers
    TURKISH_ONES = {
        'sıfır': 0, 'bir': 1, 'iki': 2, 'üç': 3, 'dört': 4, 'beş': 5,
        'altı': 6, 'yedi': 7, 'sekiz': 8, 'dokuz': 9
    }

    TURKISH_TENS = {
        'on': 10, 'yirmi': 20, 'otuz': 30, 'kırk': 40, 'elli': 50,
        'altmış': 60, 'yetmiş': 70, 'seksen': 80, 'doksan': 90
    }

    TURKISH_MAGNITUDES = {
        'yüz': 100, 'bin': 1000, 'milyon': 1000000, 'milyar': 1000000000
    }

    TURKISH_FRACTIONS = {'yarım': 0.5, 'buçuk': 0.5, 'çeyrek': 0.25}

    # English numbers
    ENGLISH_ONES = {
        'zero': 0, 'one': 1, 'two': 2, 'three': 3, 'four': 4, 'five': 5,
        'six': 6, 'seven': 7, 'eight': 8, 'nine': 9, 'ten': 10,
        'eleven': 11, 'twelve': 12, 'thirteen': 13, 'fourteen': 14, 'fifteen': 15,
        'sixteen': 16, 'seventeen': 17, 'eighteen': 18, 'nineteen': 19
    }

    ENGLISH_TENS = {
        'twenty': 20, 'thirty': 30, 'forty': 40, 'fifty': 50,
        'sixty': 60, 'seventy': 70, 'eighty': 80, 'ninety': 90
    }

    ENGLISH_MAGNITUDES = {
        'hundred': 100, 'thousand': 1000, 'million': 1000000, 'billion': 1000000000
    }

    ENGLISH_FRACTIONS = {'half': 0.5, 'quarter': 0.25}

    def __init__(self):
        self._build_patterns()

    def _build_patterns(self):
        """Build regex patterns for number detection."""
        # Turkish
        tr_words = (list(self.TURKISH_ONES.keys()) + list(self.TURKISH_TENS.keys()) +
                   list(self.TURKISH_MAGNITUDES.keys()) + list(self.TURKISH_FRACTIONS.keys()))
        self.turkish_pattern = re.compile(
            r'\b((?:(?:' + '|'.join(tr_words) + r')\s*)+)\b',
            re.IGNORECASE | re.UNICODE
        )

        # English
        en_words = (list(self.ENGLISH_ONES.keys()) + list(self.ENGLISH_TENS.keys()) +
                   list(self.ENGLISH_MAGNITUDES.keys()) + list(self.ENGLISH_FRACTIONS.keys()))
        self.english_pattern = re.compile(
            r'\b((?:(?:' + '|'.join(en_words) + r')[\s-]*)+)\b',
            re.IGNORECASE
        )

    def convert_text(self, text: str, language: str = "auto") -> str:
        """
        Convert all written numbers in text to digits.

        Args:
            text: Input text
            language: 'turkish', 'english', or 'auto'

        Returns:
            Text with written numbers converted to digits
        """
        if language == "auto":
            # Try both
            text = self._convert_turkish(text)
            text = self._convert_english(text)
            return text
        elif language == "turkish":
            return self._convert_turkish(text)
        else:
            return self._convert_english(text)

    def _convert_turkish(self, text: str) -> str:
        """Convert Turkish written numbers."""
        def replace_match(match):
            value = self.parse_turkish(match.group(1))
            if value is not None and value > 0:
                return str(int(value)) if value == int(value) else str(value)
            return match.group(0)

        return self.turkish_pattern.sub(replace_match, text)

    def _convert_english(self, text: str) -> str:
        """Convert English written numbers."""
        def replace_match(match):
            value = self.parse_english(match.group(1))
            if value is not None and value > 0:
                return str(int(value)) if value == int(value) else str(value)
            return match.group(0)

        return self.english_pattern.sub(replace_match, text)

    def parse_turkish(self, text: str) -> Optional[float]:
        """Parse Turkish written number to float."""
        if not text:
            return None

        words = text.lower().strip().split()
        total = 0
        current = 0
        has_fraction = False
        fraction_val = 0

        for word in words:
            if word in self.TURKISH_ONES:
                current += self.TURKISH_ONES[word]
            elif word in self.TURKISH_TENS:
                current += self.TURKISH_TENS[word]
            elif word in self.TURKISH_FRACTIONS:
                has_fraction = True
                fraction_val = self.TURKISH_FRACTIONS[word]
            elif word in self.TURKISH_MAGNITUDES:
                mag = self.TURKISH_MAGNITUDES[word]
                if current == 0:
                    current = 1
                if has_fraction and mag >= 1000:
                    current = (current + fraction_val) * mag
                    has_fraction = False
                else:
                    current *= mag
                if mag >= 1000000:
                    total += current
                    current = 0

        total += current
        if has_fraction:
            total += fraction_val

        return total if total > 0 else None

    def parse_english(self, text: str) -> Optional[float]:
        """Parse English written number to float."""
        if not text:
            return None

        words = text.lower().replace('-', ' ').strip().split()
        total = 0
        current = 0

        for word in words:
            if word in self.ENGLISH_ONES:
                current += self.ENGLISH_ONES[word]
            elif word in self.ENGLISH_TENS:
                current += self.ENGLISH_TENS[word]
            elif word == 'hundred':
                if current == 0:
                    current = 1
                current *= 100
            elif word in self.ENGLISH_MAGNITUDES:
                if current == 0:
                    current = 1
                current *= self.ENGLISH_MAGNITUDES[word]
                total += current
                current = 0
            elif word in self.ENGLISH_FRACTIONS:
                current += self.ENGLISH_FRACTIONS[word]

        total += current
        return total if total > 0 else None


# =============================================================================
# === RANGE PARSER
# =============================================================================

class RangeResult(NamedTuple):
    """Result of range parsing."""
    min_value: Optional[float]
    max_value: Optional[float]
    is_range: bool
    qualifier: Optional[str]


class RangeParser:
    """
    Parse numeric ranges in Turkish and English legal/scientific text.

    Handles:
    - "100-500 metre" → (100, 500, True)
    - "100 ilâ 500 metre" → (100, 500, True)
    - "en az 200 en çok 800" → (200, 800, True)
    - "at least 100 to 500 meters" → (100, 500, True)
    - "between 100 and 500 m" → (100, 500, True)
    """

    def __init__(self):
        self._compile_patterns()

    def _compile_patterns(self):
        """Compile range patterns for both languages."""
        self.patterns = [
            # Dash ranges: 100-500
            re.compile(
                r'(?P<min>\d+(?:[.,]\d+)?)\s*[-–—]\s*(?P<max>\d+(?:[.,]\d+)?)',
                re.UNICODE
            ),
            # Turkish: X ilâ/ile Y
            re.compile(
                r'(?P<min>\d+(?:[.,]\d+)?)\s*(?:ilâ|ila|ile)\s*(?P<max>\d+(?:[.,]\d+)?)',
                re.IGNORECASE | re.UNICODE
            ),
            # Turkish: X ile Y arası
            re.compile(
                r'(?P<min>\d+(?:[.,]\d+)?)\s*(?:ile|ve)\s*(?P<max>\d+(?:[.,]\d+)?)\s*(?:arası|arasında)',
                re.IGNORECASE | re.UNICODE
            ),
            # Turkish: en az X en çok Y
            re.compile(
                r'en\s+az\s+(?P<min>\d+(?:[.,]\d+)?)\s*[,\s]\s*en\s+(?:çok|fazla)\s+(?P<max>\d+(?:[.,]\d+)?)',
                re.IGNORECASE | re.UNICODE
            ),
            # Turkish: asgari X azami Y
            re.compile(
                r'asgari\s+(?P<min>\d+(?:[.,]\d+)?)\s*[,\s]\s*azami\s+(?P<max>\d+(?:[.,]\d+)?)',
                re.IGNORECASE | re.UNICODE
            ),
            # English: between X and Y
            re.compile(
                r'between\s+(?P<min>\d+(?:[.,]\d+)?)\s*(?:and|to)\s*(?P<max>\d+(?:[.,]\d+)?)',
                re.IGNORECASE
            ),
            # English: from X to Y
            re.compile(
                r'from\s+(?P<min>\d+(?:[.,]\d+)?)\s*to\s*(?P<max>\d+(?:[.,]\d+)?)',
                re.IGNORECASE
            ),
        ]

        # Single value qualifiers
        self.qualifier_patterns = [
            # Turkish minimum
            (re.compile(r'en\s+az\s+(?P<value>\d+(?:[.,]\d+)?)', re.IGNORECASE), 'minimum'),
            (re.compile(r'asgari\s+(?P<value>\d+(?:[.,]\d+)?)', re.IGNORECASE), 'minimum'),
            # Turkish maximum
            (re.compile(r'en\s+(?:fazla|çok)\s+(?P<value>\d+(?:[.,]\d+)?)', re.IGNORECASE), 'maximum'),
            (re.compile(r'azami\s+(?P<value>\d+(?:[.,]\d+)?)', re.IGNORECASE), 'maximum'),
            (re.compile(r'(?P<value>\d+(?:[.,]\d+)?)[\'ıiuü]?[yni]?[ıi]?\s*geçemez', re.IGNORECASE), 'maximum'),
            (re.compile(r'(?P<value>\d+(?:[.,]\d+)?)[\'ıiuü]?[yni]?[ıi]?\s*aşamaz', re.IGNORECASE), 'maximum'),
            # English minimum
            (re.compile(r'at\s+least\s+(?P<value>\d+(?:[.,]\d+)?)', re.IGNORECASE), 'minimum'),
            (re.compile(r'minimum\s+(?:of\s+)?(?P<value>\d+(?:[.,]\d+)?)', re.IGNORECASE), 'minimum'),
            (re.compile(r'no\s+less\s+than\s+(?P<value>\d+(?:[.,]\d+)?)', re.IGNORECASE), 'minimum'),
            # English maximum
            (re.compile(r'at\s+most\s+(?P<value>\d+(?:[.,]\d+)?)', re.IGNORECASE), 'maximum'),
            (re.compile(r'maximum\s+(?:of\s+)?(?P<value>\d+(?:[.,]\d+)?)', re.IGNORECASE), 'maximum'),
            (re.compile(r'up\s+to\s+(?P<value>\d+(?:[.,]\d+)?)', re.IGNORECASE), 'maximum'),
            (re.compile(r'(?P<value>\d+(?:[.,]\d+)?)\s+or\s+less', re.IGNORECASE), 'maximum'),
            (re.compile(r'not\s+(?:to\s+)?exceed\s+(?P<value>\d+(?:[.,]\d+)?)', re.IGNORECASE), 'maximum'),
            # Approximately
            (re.compile(r'(?:approximately|about|around|circa|~)\s*(?P<value>\d+(?:[.,]\d+)?)', re.IGNORECASE), 'approximately'),
            (re.compile(r'(?:yaklaşık|civarında)\s*(?P<value>\d+(?:[.,]\d+)?)', re.IGNORECASE), 'approximately'),
        ]

    def parse(self, text: str) -> Optional[RangeResult]:
        """
        Parse range or qualified value from text.

        Args:
            text: Input text

        Returns:
            RangeResult or None
        """
        # Try range patterns first
        for pattern in self.patterns:
            match = pattern.search(text)
            if match:
                min_val = self._parse_number(match.group('min'))
                max_val = self._parse_number(match.group('max'))
                if min_val is not None and max_val is not None:
                    if min_val > max_val:
                        min_val, max_val = max_val, min_val
                    return RangeResult(min_val, max_val, True, 'between')

        # Try qualifier patterns
        for pattern, qualifier in self.qualifier_patterns:
            match = pattern.search(text)
            if match:
                value = self._parse_number(match.group('value'))
                if value is not None:
                    if qualifier in ('minimum', 'greater_than'):
                        return RangeResult(value, None, False, qualifier)
                    elif qualifier == 'approximately':
                        return RangeResult(value, value, False, qualifier)
                    else:
                        return RangeResult(None, value, False, qualifier)

        return None

    def _parse_number(self, value_str: str) -> Optional[float]:
        """Parse number string to float."""
        if not value_str:
            return None
        try:
            return float(value_str.replace(',', '.').replace(' ', ''))
        except (ValueError, TypeError):
            return None
