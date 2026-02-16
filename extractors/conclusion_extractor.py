"""
Conclusion Extractor - FULLY WORKING
Extracts conclusions and policy implications from scientific papers
"""
import re
import logging
from typing import Dict, List, Optional

try:
    from ..core.enums import DocumentType
    from ..data_structures import ConclusionExtraction
    from .base_extractor import BaseExtractor
except ImportError:
    from core.enums import DocumentType
    from data_structures import ConclusionExtraction
    from extractors.base_extractor import BaseExtractor

logger = logging.getLogger(__name__)


class ConclusionExtractor(BaseExtractor):
    """Extract conclusions and policy implications from scientific papers"""

    # Focus on last 30% of document
    TAIL_FRACTION = 0.30

    def _compile_patterns(self):
        """Compile conclusion patterns"""
        # English patterns
        self.english_patterns = [
            re.compile(
                r'(?:we\s+conclude|in\s+conclusion|our\s+findings\s+(?:indicate|suggest|show))\s+(?:that\s+)?(?P<conc>[^.]+)',
                re.IGNORECASE
            ),
            re.compile(
                r'(?:this\s+study\s+(?:concludes|demonstrates|shows))\s+(?:that\s+)?(?P<conc>[^.]+)',
                re.IGNORECASE
            ),
            re.compile(
                r'(?:(?:we|the\s+authors?)\s+)?recommend\s+(?:that\s+)?(?P<conc>[^.]+)',
                re.IGNORECASE
            ),
            re.compile(
                r'(?:policy\s*(?:makers?|implication))\s+(?:should\s+)?(?P<conc>[^.]+)',
                re.IGNORECASE
            ),
            re.compile(
                r'(?:management\s+(?:implication|recommendation))\s+(?P<conc>[^.]+)',
                re.IGNORECASE
            ),
        ]

        # Turkish patterns
        self.turkish_patterns = [
            re.compile(
                r'(?:sonuç\s+olarak)\s+(?P<conc>[^.]+)',
                re.IGNORECASE | re.UNICODE
            ),
            re.compile(
                r'(?:önerilen|tavsiye\s+edilen)\s+(?P<conc>[^.]+)',
                re.IGNORECASE | re.UNICODE
            ),
        ]

        # Evidence strength indicators
        self.strong_indicators = re.compile(
            r'\b(?:clearly|demonstrates?|confirms?|establishes?|proves?)\b',
            re.IGNORECASE
        )
        self.moderate_indicators = re.compile(
            r'\b(?:suggests?|indicates?|supports?|shows?)\b',
            re.IGNORECASE
        )
        self.weak_indicators = re.compile(
            r'\b(?:may|could|might|possibly|potentially)\b',
            re.IGNORECASE
        )
        self.speculative_indicators = re.compile(
            r'\b(?:speculate|future|preliminary|tentative|exploratory)\b',
            re.IGNORECASE
        )

    def extract(self, text: str, page_texts: Dict[int, str],
                doc_type: DocumentType) -> List[ConclusionExtraction]:
        """Extract conclusions from text"""
        results: List[ConclusionExtraction] = []
        language = self._get_language(doc_type)

        # Focus on last 30% of document
        tail_start = int(len(text) * (1 - self.TAIL_FRACTION))
        search_text = text[tail_start:]
        offset = tail_start  # offset for page number calculation

        patterns = self.turkish_patterns if language == "turkish" else self.english_patterns

        for pattern in patterns:
            for match in pattern.finditer(search_text):
                result = self._process_match(
                    match, search_text, text, page_texts, language, offset, pattern
                )
                if result:
                    results.append(result)

        return self._deduplicate(results)

    def _process_match(self, match: re.Match, search_text: str, original_text: str,
                       page_texts: Dict[int, str], language: str,
                       offset: int, pattern: re.Pattern) -> Optional[ConclusionExtraction]:
        """Process a conclusion match"""
        try:
            groups = match.groupdict()
            conclusion_text = (groups.get('conc') or '').strip()

            if not conclusion_text or len(conclusion_text) < 10:
                return None

            sentence, context = self._get_sentence_context(search_text, match.start(), match.end())

            marine_score = self.fp_filter.get_marine_relevance_score(sentence, language)
            if marine_score < 0.1:
                return None

            conclusion_type = self._classify_conclusion_type(match.group(0), pattern)
            evidence_strength = self._assess_evidence_strength(context)
            target_audience = self._identify_target_audience(context, language)

            # Use offset for correct page number in full document
            page_num = self._find_page_number(offset + match.start(), page_texts)

            confidence = 0.7 + (0.1 if marine_score > 0.3 else 0) + \
                         (0.1 if evidence_strength in ('strong', 'moderate') else 0)

            return ConclusionExtraction(
                conclusion_type=conclusion_type,
                conclusion_text=conclusion_text[:300],
                evidence_strength=evidence_strength,
                target_audience=target_audience,
                context=context[:200],
                exact_text=match.group(0),
                page_number=page_num,
                confidence=min(confidence, 1.0),
                marine_relevance=marine_score
            )

        except Exception as e:
            logger.warning(f"Error processing conclusion match: {e}")
            return None

    def _classify_conclusion_type(self, match_text: str, pattern: re.Pattern) -> str:
        """Classify the type of conclusion"""
        match_lower = match_text.lower()

        if any(x in match_lower for x in ['recommend', 'önerilen', 'tavsiye']):
            return 'management_recommendation'
        elif any(x in match_lower for x in ['policy', 'implication']):
            return 'policy_implication'

        return 'main_conclusion'

    def _assess_evidence_strength(self, context: str) -> str:
        """Assess evidence strength from context language"""
        if self.strong_indicators.search(context):
            return 'strong'
        elif self.moderate_indicators.search(context):
            return 'moderate'
        elif self.speculative_indicators.search(context):
            return 'speculative'
        elif self.weak_indicators.search(context):
            return 'weak'

        return 'moderate'

    def _identify_target_audience(self, context: str, language: str) -> Optional[str]:
        """Identify target audience from context"""
        context_lower = context.lower()

        if any(x in context_lower for x in ['policy', 'policymaker', 'government', 'regulation',
                                              'politika', 'hükümet', 'yönetmelik']):
            return 'policymakers'
        elif any(x in context_lower for x in ['manager', 'management', 'practitioner',
                                                'yönetici', 'yönetim']):
            return 'managers'
        elif any(x in context_lower for x in ['researcher', 'future research', 'scientist',
                                                'araştırmacı', 'bilim insanı']):
            return 'researchers'

        return None
