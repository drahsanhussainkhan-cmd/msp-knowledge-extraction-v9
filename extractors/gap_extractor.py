"""
Gap Extractor - FULLY WORKING
Extracts research gaps identified in scientific papers
"""
import re
import logging
from typing import Dict, List, Optional

try:
    from ..core.enums import DocumentType
    from ..data_structures import GapIdentifiedExtraction
    from .base_extractor import BaseExtractor
except ImportError:
    from core.enums import DocumentType
    from data_structures import GapIdentifiedExtraction
    from extractors.base_extractor import BaseExtractor

logger = logging.getLogger(__name__)


class GapExtractor(BaseExtractor):
    """Extract research gaps identified in scientific papers"""

    # Focus on Discussion/Conclusion sections (last 40% of document)
    TAIL_FRACTION = 0.40

    def _compile_patterns(self):
        """Compile gap patterns"""
        # English patterns
        self.english_patterns = [
            re.compile(
                r'(?:lack\s+of|limited)\s+(?P<gap>[^.]+)',
                re.IGNORECASE
            ),
            re.compile(
                r'(?:no\s+(?:data|information|studies?))\s+(?:on|about|regarding)\s+(?P<gap>[^.]+)',
                re.IGNORECASE
            ),
            re.compile(
                r'(?:poorly|little)\s+(?:understood|known|studied)\s+(?P<gap>[^.]+)',
                re.IGNORECASE
            ),
            re.compile(
                r'(?:future\s+(?:research|studies?|work)\s+(?:should|need|is\s+needed))\s+(?:to\s+)?(?P<gap>[^.]+)',
                re.IGNORECASE
            ),
            re.compile(
                r'(?:gap\s+in|missing|absent|unavailable)\s+(?P<gap>[^.]+)',
                re.IGNORECASE
            ),
            re.compile(
                r'(?:more\s+(?:research|data|information)\s+(?:is|are)\s+needed)\s+(?:on|for|to)?\s*(?P<gap>[^.]+)',
                re.IGNORECASE
            ),
        ]

        # Turkish patterns
        self.turkish_patterns = [
            re.compile(
                r'(?:eksikli[kğ]i?|yetersiz(?:li[kğ])?)\s+(?P<gap>[^.]+)',
                re.IGNORECASE | re.UNICODE
            ),
            re.compile(
                r'(?:gelecek\s+(?:çalışmalar|araştırmalar))\s+(?P<gap>[^.]+)',
                re.IGNORECASE | re.UNICODE
            ),
        ]

        # Severity indicators
        self.critical_indicators = re.compile(
            r'\b(?:critical|essential|urgent|crucial|fundamental)\b',
            re.IGNORECASE
        )
        self.important_indicators = re.compile(
            r'\b(?:important|significant|considerable|substantial|notable)\b',
            re.IGNORECASE
        )
        self.minor_indicators = re.compile(
            r'\b(?:minor|potential|slight|marginal|modest)\b',
            re.IGNORECASE
        )

    def extract(self, text: str, page_texts: Dict[int, str],
                doc_type: DocumentType) -> List[GapIdentifiedExtraction]:
        """Extract research gaps from text"""
        results: List[GapIdentifiedExtraction] = []
        language = self._get_language(doc_type)

        # Focus on last 40% of document (Discussion/Conclusion)
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
                       offset: int, pattern: re.Pattern) -> Optional[GapIdentifiedExtraction]:
        """Process a gap match"""
        try:
            groups = match.groupdict()
            gap_description = (groups.get('gap') or '').strip()

            if not gap_description or len(gap_description) < 10:
                return None

            sentence, context = self._get_sentence_context(search_text, match.start(), match.end())

            marine_score = self.fp_filter.get_marine_relevance_score(sentence, language)
            if marine_score < 0.1:
                return None

            # Check false positives
            is_fp, fp_reason = self._is_false_positive(sentence, match.group(0), language)
            if is_fp:
                return None

            gap_type = self._classify_gap_type(match.group(0), context, pattern)
            severity = self._assess_severity(context)
            proposed_solution = self._extract_proposed_solution(context, language)
            domain = self._identify_domain(context, language)

            # Use offset for correct page number in full document
            page_num = self._find_page_number(offset + match.start(), page_texts)

            confidence = 0.6 + (0.1 if marine_score > 0.3 else 0) + \
                         (0.1 if proposed_solution else 0) + \
                         (0.1 if domain else 0)

            return GapIdentifiedExtraction(
                gap_type=gap_type,
                gap_description=gap_description[:300],
                severity=severity,
                proposed_solution=proposed_solution,
                domain=domain,
                context=context[:200],
                exact_text=match.group(0),
                page_number=page_num,
                confidence=min(confidence, 1.0),
                marine_relevance=marine_score
            )

        except Exception as e:
            logger.warning(f"Error processing gap match: {e}")
            return None

    def _classify_gap_type(self, match_text: str, context: str, pattern: re.Pattern) -> str:
        """Classify the type of research gap"""
        combined = (match_text + ' ' + context).lower()

        if any(x in combined for x in ['data', 'information', 'dataset', 'veri']):
            return 'data_gap'
        elif any(x in combined for x in ['method', 'approach', 'technique', 'yöntem']):
            return 'methodological_gap'
        elif any(x in combined for x in ['future', 'need', 'should', 'gelecek']):
            return 'research_need'

        return 'knowledge_gap'

    def _assess_severity(self, context: str) -> str:
        """Assess severity of the identified gap"""
        if self.critical_indicators.search(context):
            return 'critical'
        elif self.important_indicators.search(context):
            return 'important'
        elif self.minor_indicators.search(context):
            return 'minor'

        return 'important'

    def _extract_proposed_solution(self, context: str, language: str) -> Optional[str]:
        """Extract proposed solution from context"""
        patterns = [
            r'(?:should|could|need\s+to|recommend)\s+(?P<sol>[^.]+)',
            r'(?:by\s+(?:using|applying|developing))\s+(?P<sol>[^.]+)',
        ]
        if language == 'turkish':
            patterns.append(
                r'(?:gerekli|önerilmektedir|yapılmalıdır)\s+(?P<sol>[^.]+)'
            )

        for pat in patterns:
            m = re.search(pat, context, re.IGNORECASE | re.UNICODE)
            if m:
                sol = m.group('sol') if 'sol' in m.groupdict() else m.group(0)
                return sol.strip()[:200]

        return None

    def _identify_domain(self, context: str, language: str) -> Optional[str]:
        """Identify the domain of the research gap"""
        context_lower = context.lower()

        domain_map = {
            'marine_ecology': ['ecology', 'biodiversity', 'species', 'habitat', 'ecosystem',
                               'ekoloji', 'biyoçeşitlilik', 'tür', 'habitat', 'ekosistem'],
            'spatial_planning': ['spatial', 'planning', 'zoning', 'zone', 'area',
                                 'mekansal', 'planlama', 'zonlama'],
            'fisheries': ['fish', 'fishing', 'fishery', 'catch', 'stock',
                          'balık', 'balıkçılık', 'av'],
            'climate_change': ['climate', 'warming', 'sea level', 'temperature',
                               'iklim', 'ısınma', 'deniz seviyesi'],
            'socioeconomic': ['economic', 'social', 'stakeholder', 'community', 'livelihood',
                              'ekonomik', 'sosyal', 'paydaş'],
            'governance': ['governance', 'policy', 'regulation', 'institutional',
                           'yönetişim', 'politika', 'düzenleme'],
        }

        for domain, keywords in domain_map.items():
            if any(kw in context_lower for kw in keywords):
                return domain

        return None
