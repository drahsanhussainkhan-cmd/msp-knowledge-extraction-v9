"""
Objective Extractor - FULLY WORKING
Extracts research objectives, aims, hypotheses from scientific papers
"""
import re
import logging
from typing import Dict, List, Optional

try:
    from ..core.enums import DocumentType
    from ..data_structures import ResearchObjectiveExtraction
    from .base_extractor import BaseExtractor
except ImportError:
    from core.enums import DocumentType
    from data_structures import ResearchObjectiveExtraction
    from extractors.base_extractor import BaseExtractor

logger = logging.getLogger(__name__)


class ObjectiveExtractor(BaseExtractor):
    """Extract research objectives, aims, hypotheses from scientific papers"""

    # Focus on intro/abstract (first 5000 chars)
    INTRO_LIMIT = 5000

    def _compile_patterns(self):
        """Compile objective patterns"""
        # English patterns
        self.english_patterns = [
            re.compile(
                r'(?:aim|objective|goal)s?\s+(?:of\s+)?(?:this\s+)?(?:study|research|paper)\s+'
                r'(?:is|are|was|were)\s+to\s+(?P<obj>[^.]+)',
                re.IGNORECASE
            ),
            re.compile(
                r'(?:we|this\s+(?:study|paper|research))\s+(?:aim|seek|intend)s?\s+to\s+(?P<obj>[^.]+)',
                re.IGNORECASE
            ),
            re.compile(
                r'(?:purpose|goal)\s+(?:of\s+)?(?:this\s+)?(?:study|research)\s+'
                r'(?:is|was)\s+(?:to\s+)?(?P<obj>[^.]+)',
                re.IGNORECASE
            ),
            re.compile(
                r'(?:research\s+question|RQ)\s*(?:\d+)?[:\s]+(?P<obj>[^.?]+)',
                re.IGNORECASE
            ),
            re.compile(
                r'(?:we\s+)?hypothesi[sz]e\s+that\s+(?P<obj>[^.]+)',
                re.IGNORECASE
            ),
            re.compile(
                r'(?:H\d+)\s*[:\s]+(?P<obj>[^.]+)',
                re.IGNORECASE
            ),
        ]

        # Turkish patterns
        self.turkish_patterns = [
            re.compile(
                r'(?:bu\s+)?(?:çalışma|araştırma)(?:nın)?\s+(?:amacı|hedefi)\s+(?P<obj>[^.]+)',
                re.IGNORECASE | re.UNICODE
            ),
            re.compile(
                r'(?:amaç|hedef)\s+(?:olarak)?\s+(?P<obj>[^.]+)',
                re.IGNORECASE | re.UNICODE
            ),
        ]

    def extract(self, text: str, page_texts: Dict[int, str],
                doc_type: DocumentType) -> List[ResearchObjectiveExtraction]:
        """Extract research objectives from text"""
        results: List[ResearchObjectiveExtraction] = []
        language = self._get_language(doc_type)

        # Focus on intro/abstract (first 5000 chars)
        search_text = text[:self.INTRO_LIMIT]

        patterns = self.turkish_patterns if language == "turkish" else self.english_patterns

        for pattern in patterns:
            for match in pattern.finditer(search_text):
                result = self._process_match(match, search_text, text, page_texts, language, pattern)
                if result:
                    results.append(result)

        return self._deduplicate(results)

    def _process_match(self, match: re.Match, search_text: str, original_text: str,
                       page_texts: Dict[int, str], language: str,
                       pattern: re.Pattern) -> Optional[ResearchObjectiveExtraction]:
        """Process an objective match"""
        try:
            groups = match.groupdict()
            objective_text = (groups.get('obj') or '').strip()

            if not objective_text or len(objective_text) < 10:
                return None

            sentence, context = self._get_sentence_context(search_text, match.start(), match.end())

            marine_score = self.fp_filter.get_marine_relevance_score(sentence, language)
            if marine_score < 0.1:
                return None

            objective_type = self._classify_objective_type(match.group(0), pattern)
            study_area = self._extract_study_area(context, language)
            page_num = self._find_page_number(match.start(), page_texts)

            confidence = 0.7 + (0.1 if marine_score > 0.3 else 0) + (0.1 if study_area else 0)

            return ResearchObjectiveExtraction(
                objective_type=objective_type,
                objective_text=objective_text[:300],
                study_area=study_area,
                context=context[:200],
                exact_text=match.group(0),
                page_number=page_num,
                confidence=min(confidence, 1.0),
                marine_relevance=marine_score
            )

        except Exception as e:
            logger.warning(f"Error processing objective match: {e}")
            return None

    def _classify_objective_type(self, match_text: str, pattern: re.Pattern) -> str:
        """Classify the type of research objective"""
        match_lower = match_text.lower()

        if any(x in match_lower for x in ['hypothes', 'h1', 'h2', 'h3', 'h4']):
            return 'hypothesis'
        elif any(x in match_lower for x in ['research question', 'rq']):
            return 'research_question'
        elif any(x in match_lower for x in ['purpose', 'problem', 'sorun']):
            return 'problem_statement'

        return 'objective'

    def _extract_study_area(self, context: str, language: str) -> Optional[str]:
        """Extract study area from context"""
        patterns = [
            r'(?:in|at|along|within)\s+(?:the\s+)?(?P<area>[A-Z][a-zA-Z\s]{2,30}(?:Sea|Ocean|Bay|Coast|Region|Island|Basin))',
            r'(?:Mediterranean|Black\s+Sea|Aegean|Marmara|Atlantic|Pacific|Indian\s+Ocean)',
        ]
        if language == 'turkish':
            patterns.append(
                r'(?:Karadeniz|Akdeniz|Ege|Marmara|[A-ZÇĞİÖŞÜ][a-zçğıöşü]+\s+(?:Denizi|Körfezi|Kıyısı))'
            )

        for pat in patterns:
            m = re.search(pat, context, re.UNICODE)
            if m:
                return m.group(0).strip()

        return None
