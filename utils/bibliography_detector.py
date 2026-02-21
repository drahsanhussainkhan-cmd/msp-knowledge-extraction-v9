"""
Bibliography Section Detector - Identifies reference/bibliography sections in documents.

Detects the start of bibliography/references sections so extractors can skip
matches that fall within these regions (a major source of false positives).
"""

import re
from typing import List, Tuple


class BibliographyDetector:
    """
    Detect bibliography/reference section boundaries in academic and legal texts.

    Returns ranges (start, end) marking bibliography sections that should be
    excluded from extraction.
    """

    # Section headers that signal the start of a bibliography
    BIBLIOGRAPHY_HEADERS = [
        # English - with optional numbering and whitespace
        r'^\s*(?:\d+\.?\s+)?References\s*$',
        r'^\s*REFERENCES\s*$',
        r'^\s*(?:\d+\.?\s+)?Bibliography\s*$',
        r'^\s*BIBLIOGRAPHY\s*$',
        r'^\s*Works\s+Cited\s*$',
        r'^\s*Literature\s+Cited\s*$',
        r'^\s*Reference\s+List\s*$',
        r'^\s*References\s*\n',
        # Turkish
        r'^\s*(?:\d+\.?\s+)?Kaynaklar\s*$',
        r'^\s*KAYNAKLAR\s*$',
        r'^\s*(?:\d+\.?\s+)?Kaynakça\s*$',
        r'^\s*KAYNAKÇA\s*$',
        r'^\s*Kaynak(?:lar)?\s+Listesi\s*$',
    ]

    # CRediT author statement markers
    CREDIT_HEADERS = [
        r'CRediT\s+author(?:ship)?\s+contribution',
        r'Author\s+contributions?\s*:',
        r'Declaration\s+of\s+(?:competing\s+)?interest',
        r'Acknowledgement',
        r'Data\s+availability',
        r'Funding\s*(?::|$)',
    ]

    def __init__(self):
        self._compile_patterns()

    def _compile_patterns(self):
        """Compile detection patterns."""
        self.header_pattern = re.compile(
            '|'.join(self.BIBLIOGRAPHY_HEADERS),
            re.MULTILINE | re.IGNORECASE
        )
        self.credit_pattern = re.compile(
            '|'.join(self.CREDIT_HEADERS),
            re.IGNORECASE
        )
        # Dense citation pattern: multiple [N] references in short span
        self.citation_density_pattern = re.compile(
            r'\[\d{1,3}\]\s*[A-Z][a-z]'
        )
        # DOI pattern for detecting reference blocks
        self.doi_pattern = re.compile(
            r'(?:doi|https?://doi\.org)[:/]\s*10\.\d{4,}',
            re.IGNORECASE
        )
        # Author-year citation pattern: "Author, A.B., Year."
        self.author_year_pattern = re.compile(
            r'[A-Z][a-z]+,\s*[A-Z]\.(?:[A-Z]\.)?,?\s*(?:et\s+al\.?,?\s*)?(?:19|20)\d{2}[.,]'
        )

    def detect_bibliography_ranges(self, text: str) -> List[Tuple[int, int]]:
        """
        Find all bibliography/reference section ranges in the text.

        Args:
            text: Full document text

        Returns:
            List of (start, end) tuples marking bibliography sections
        """
        ranges = []

        # Method 1: Find explicit section headers
        for match in self.header_pattern.finditer(text):
            bib_start = match.start()
            # Bibliography runs to end of text or next major section
            bib_end = self._find_section_end(text, match.end())
            ranges.append((bib_start, bib_end))

        # Method 2: Find CRediT/acknowledgment sections
        for match in self.credit_pattern.finditer(text):
            section_start = match.start()
            section_end = self._find_section_end(text, match.end(), max_length=3000)
            ranges.append((section_start, section_end))

        # Method 3: Detect dense citation blocks (e.g. [1] Author, Title...)
        # If we find 5+ numbered citations in a 2000-char window, mark as bibliography
        citation_matches = list(self.citation_density_pattern.finditer(text))
        if len(citation_matches) >= 5:
            # Check density: 5+ citations in 2000 chars
            for i in range(len(citation_matches) - 4):
                window_start = citation_matches[i].start()
                window_end = citation_matches[i + 4].end()
                if window_end - window_start < 2000:
                    # Dense citation block found - mark from first citation to end of text
                    ranges.append((window_start, len(text)))
                    break

        # Method 4: DOI-dense sections (3+ DOIs in 2000 chars)
        doi_matches = list(self.doi_pattern.finditer(text))
        if len(doi_matches) >= 3:
            for i in range(len(doi_matches) - 2):
                window_start = doi_matches[i].start()
                window_end = doi_matches[i + 2].end()
                if window_end - window_start < 2000:
                    ranges.append((window_start, len(text)))
                    break

        # Method 5: Author-year dense sections (5+ in 3000 chars)
        ay_matches = list(self.author_year_pattern.finditer(text))
        if len(ay_matches) >= 5:
            for i in range(len(ay_matches) - 4):
                window_start = ay_matches[i].start()
                window_end = ay_matches[i + 4].end()
                if window_end - window_start < 3000:
                    ranges.append((window_start, len(text)))
                    break

        # Merge overlapping ranges
        return self._merge_ranges(ranges)

    def _find_section_end(self, text: str, start: int, max_length: int = None) -> int:
        """
        Find where a bibliography/boilerplate section ends.

        For bibliography: usually runs to end of document.
        For CRediT/acknowledgments: runs until next section header or ~3000 chars.
        """
        if max_length is None:
            # Bibliography typically runs to end of document
            return len(text)

        # For bounded sections, look for next section header or max_length
        search_end = min(start + max_length, len(text))
        remaining = text[start:search_end]

        # Check for next major section header
        next_header = re.search(
            r'\n\s*\d+\.\s+[A-Z]|\n\s*[A-Z][a-z]+\s+[a-z]',
            remaining[200:]  # skip first 200 chars to avoid matching within current section
        )
        if next_header:
            return start + 200 + next_header.start()

        return search_end

    def is_in_bibliography(self, position: int, ranges: List[Tuple[int, int]]) -> bool:
        """Check if a text position falls within any bibliography range."""
        for start, end in ranges:
            if start <= position < end:
                return True
        return False

    @staticmethod
    def _merge_ranges(ranges: List[Tuple[int, int]]) -> List[Tuple[int, int]]:
        """Merge overlapping ranges."""
        if not ranges:
            return []
        sorted_ranges = sorted(ranges, key=lambda x: x[0])
        merged = [sorted_ranges[0]]
        for start, end in sorted_ranges[1:]:
            if start <= merged[-1][1]:
                merged[-1] = (merged[-1][0], max(merged[-1][1], end))
            else:
                merged.append((start, end))
        return merged
