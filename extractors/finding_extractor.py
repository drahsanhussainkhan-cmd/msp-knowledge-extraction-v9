"""
Finding Extractor - FULLY WORKING
Extracts research findings from scientific papers
"""
import re
import logging
from typing import Dict, List, Optional

try:
    from ..core.enums import DocumentType
    from ..data_structures import FindingExtraction
    from .base_extractor import BaseExtractor
except ImportError:
    from core.enums import DocumentType
    from data_structures import FindingExtraction
    from extractors.base_extractor import BaseExtractor

logger = logging.getLogger(__name__)


class FindingExtractor(BaseExtractor):
    """Extract research findings from scientific papers"""

    def _compile_patterns(self):
        """Compile finding patterns"""
        # Turkish patterns
        self.turkish_patterns = [
            re.compile(
                r'(?P<finding>bulgu|sonuç|saptama|tespit|gözlem)\s*(?:[:\-]\s*)?'
                r'(?P<description>[^.;]{20,200})',
                re.IGNORECASE | re.UNICODE
            ),
        ]

        # English patterns
        self.english_patterns = [
            re.compile(
                r'(?:results?\s+(?:show|indicate|demonstrate|suggest)|findings?\s+(?:show|indicate|reveal))\s+'
                r'(?:that\s+)?(?P<description>[^.;]{20,200})',
                re.IGNORECASE
            ),
            re.compile(
                r'(?:we|this\s+study)\s+(?:found|observed|identified)\s+(?:that\s+)?'
                r'(?P<description>[^.;]{20,200})',
                re.IGNORECASE
            ),
        ]

    def extract(self, text: str, page_texts: Dict[int, str],
                doc_type: DocumentType) -> List[FindingExtraction]:
        """Extract findings from text"""
        results: List[FindingExtraction] = []
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
                       doc_type: DocumentType) -> Optional[FindingExtraction]:
        """Process a finding match"""
        try:
            groups = match.groupdict()
            sentence, context = self._get_sentence_context(converted_text, match.start(), match.end())

            marine_score = self.fp_filter.get_marine_relevance_score(sentence, language)
            if marine_score < 0.1:
                return None

            description = (groups.get('description') or '').strip()
            if not description or len(description) < 20:
                return None

            finding_type = self._parse_finding_type(description, language)
            quantitative_result = self._extract_quantitative_result(description)
            significance = self._extract_significance(context, language)

            page_num = self._find_page_number(match.start(), page_texts)

            confidence = 0.7 + (0.1 if marine_score > 0.3 else 0) + (0.1 if quantitative_result else 0)

            return FindingExtraction(
                finding_type=finding_type,
                description=description[:200],
                quantitative_result=quantitative_result,
                significance=significance,
                context=context[:200],
                exact_text=match.group(0),
                page_number=page_num,
                confidence=min(confidence, 1.0),
                marine_relevance=marine_score
            )

        except Exception as e:
            logger.warning(f"Error processing finding match: {e}")
            return None

    def _parse_finding_type(self, description: str, language: str) -> str:
        """Parse finding type"""
        desc_lower = description.lower()

        if any(x in desc_lower for x in ['spatial', 'mekansal', 'alan', 'distribution']):
            return 'spatial_pattern'
        elif any(x in desc_lower for x in ['trend', 'eğilim', 'increase', 'decrease', 'artış', 'azalış']):
            return 'trend'
        elif any(x in desc_lower for x in ['correlation', 'korelasyon', 'relationship', 'ilişki']):
            return 'correlation'
        elif any(x in desc_lower for x in ['recommend', 'öner', 'suggest']):
            return 'recommendation'

        return 'finding'

    def _extract_quantitative_result(self, description: str) -> Optional[str]:
        """Extract quantitative results"""
        # Look for numbers with units/percentages
        patterns = [
            r'(\d+(?:[.,]\d+)?%)',
            r'(\d+(?:[.,]\d+)?\s*(?:km²|km2|ha|hectares))',
            r'(p\s*[<>=]\s*\d+(?:[.,]\d+)?)',
        ]

        for pattern in patterns:
            match = re.search(pattern, description, re.IGNORECASE)
            if match:
                return match.group(1)
        return None

    def _extract_significance(self, context: str, language: str) -> Optional[str]:
        """Extract statistical significance"""
        if language == 'turkish':
            patterns = [r'(?:anlaml[ıi]|istatistiksel)[:\s]+([^.;]+)']
        else:
            patterns = [r'(?:significant|significance|p\s*[<>=]\s*\d+[.,]\d+)']

        for pattern in patterns:
            match = re.search(pattern, context, re.IGNORECASE | re.UNICODE)
            if match:
                return match.group(0)[:50]
        return None
