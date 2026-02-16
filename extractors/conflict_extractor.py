"""
Conflict Extractor - FULLY WORKING
Extracts use conflicts and incompatibilities from scientific papers
"""
import re
import logging
from typing import Dict, List, Optional

try:
    from ..core.enums import DocumentType
    from ..data_structures import ConflictExtraction
    from .base_extractor import BaseExtractor
except ImportError:
    from core.enums import DocumentType
    from data_structures import ConflictExtraction
    from extractors.base_extractor import BaseExtractor

logger = logging.getLogger(__name__)


class ConflictExtractor(BaseExtractor):
    """Extract use conflicts from scientific papers"""

    def _compile_patterns(self):
        """Compile conflict patterns"""
        # Turkish patterns
        self.turkish_patterns = [
            re.compile(
                r'(?P<activity1>[\w\s]+?)\s+(?:ile|ve)\s+(?P<activity2>[\w\s]+?)\s+'
                r'(?:aras[ıi]nda\s+)?(?P<type>çat[ıi][şs]ma|uyumsuzluk|çeli[şs]ki|ç[aâ]k[ıi][şs]ma)',
                re.IGNORECASE | re.UNICODE
            ),
        ]

        # English patterns
        self.english_patterns = [
            re.compile(
                r'(?P<type>conflict|incompatibility|incompatible)\s+between\s+'
                r'(?P<activity1>[\w\s]+?)\s+and\s+(?P<activity2>[\w\s]+)',
                re.IGNORECASE
            ),
            re.compile(
                r'(?P<activity1>[\w\s]+?)\s+(?:conflicts?|incompatible)\s+with\s+(?P<activity2>[\w\s]+)',
                re.IGNORECASE
            ),
        ]

    def extract(self, text: str, page_texts: Dict[int, str],
                doc_type: DocumentType) -> List[ConflictExtraction]:
        """Extract conflicts from text"""
        results: List[ConflictExtraction] = []
        language = self._get_language(doc_type)

        patterns = self.turkish_patterns if language == "turkish" else self.english_patterns

        for pattern in patterns:
            for match in pattern.finditer(text):
                result = self._process_match(match, text, text, page_texts, language, doc_type)
                if result:
                    results.append(result)

        return self._deduplicate(results)

    def _process_match(self, match: re.Match, converted_text: str, original_text: str,
                       page_texts: Dict[int, str], language: str,
                       doc_type: DocumentType) -> Optional[ConflictExtraction]:
        """Process a conflict match"""
        try:
            groups = match.groupdict()
            sentence, context = self._get_sentence_context(converted_text, match.start(), match.end())

            marine_score = self.fp_filter.get_marine_relevance_score(sentence, language)
            if marine_score < 0.1:
                return None

            conflict_type = 'spatial'  # Default
            activity_1 = (groups.get('activity1') or '').strip()[:100]
            activity_2 = (groups.get('activity2') or '').strip()[:100]
            severity = self._extract_severity(context, language)
            resolution = self._extract_resolution(context, language)

            page_num = self._find_page_number(match.start(), page_texts)

            confidence = 0.7 + (0.1 if marine_score > 0.3 else 0) + (0.1 if severity else 0)

            return ConflictExtraction(
                conflict_type=conflict_type,
                activity_1=activity_1 if activity_1 else None,
                activity_2=activity_2 if activity_2 else None,
                severity=severity,
                resolution=resolution,
                context=context[:200],
                exact_text=match.group(0),
                page_number=page_num,
                confidence=min(confidence, 1.0),
                marine_relevance=marine_score
            )

        except Exception as e:
            logger.warning(f"Error processing conflict match: {e}")
            return None

    def _extract_severity(self, context: str, language: str) -> Optional[str]:
        """Extract conflict severity"""
        context_lower = context.lower()

        if language == 'turkish':
            if any(x in context_lower for x in ['yüksek', 'ciddi', 'şiddetli']):
                return 'high'
            elif any(x in context_lower for x in ['orta', 'normal']):
                return 'medium'
            elif any(x in context_lower for x in ['düşük', 'az']):
                return 'low'
        else:
            if any(x in context_lower for x in ['high', 'severe', 'major', 'significant']):
                return 'high'
            elif any(x in context_lower for x in ['medium', 'moderate']):
                return 'medium'
            elif any(x in context_lower for x in ['low', 'minor', 'small']):
                return 'low'

        return None

    def _extract_resolution(self, context: str, language: str) -> Optional[str]:
        """Extract conflict resolution"""
        if language == 'turkish':
            patterns = [r'(?:çözüm|çözülme)[:\s]+([^.;]+)']
        else:
            patterns = [r'(?:resolution|solution|resolve)[:\s]+([^.;]+)']

        for pattern in patterns:
            match = re.search(pattern, context, re.IGNORECASE | re.UNICODE)
            if match:
                return match.group(1).strip()[:100]
        return None
