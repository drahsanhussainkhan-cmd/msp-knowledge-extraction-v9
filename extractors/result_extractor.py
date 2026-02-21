"""
Result Extractor - FULLY WORKING
Extracts research results/findings with quantitative values from scientific papers
"""
import re
import logging
from typing import Dict, List, Optional

try:
    from ..core.enums import DocumentType
    from ..data_structures import ResultExtraction
    from .base_extractor import BaseExtractor
except ImportError:
    from core.enums import DocumentType
    from data_structures import ResultExtraction
    from extractors.base_extractor import BaseExtractor

logger = logging.getLogger(__name__)


class ResultExtractor(BaseExtractor):
    """Extract research results/findings from scientific papers"""

    def _compile_patterns(self):
        """Compile result patterns"""
        # English patterns
        self.english_patterns = [
            re.compile(
                r'(?:results?\s+(?:show|indicate|demonstrate|reveal|suggest))\s+(?:that\s+)?(?P<result>[^.]+)',
                re.IGNORECASE
            ),
            re.compile(
                r'(?:we\s+found|analysis\s+(?:show|reveal)ed)\s+(?:that\s+)?(?P<result>[^.]+)',
                re.IGNORECASE
            ),
            re.compile(
                r'(?:significant(?:ly)?)\s+(?:increase|decrease|difference|correlation|relationship)\s+(?P<result>[^.]+)',
                re.IGNORECASE
            ),
        ]

        # Turkish patterns
        self.turkish_patterns = [
            re.compile(
                r'(?:sonuçlar|bulgular)\s+(?P<result>[^.]+)',
                re.IGNORECASE | re.UNICODE
            ),
            re.compile(
                r'(?:analiz\s+sonuçları)\s+(?P<result>[^.]+)',
                re.IGNORECASE | re.UNICODE
            ),
        ]

        # Quantitative value pattern
        self.quantitative_pattern = re.compile(
            r'(?P<quant>\d+(?:\.\d+)?)\s*(?:%|percent|km²|ha|individuals|species)',
            re.IGNORECASE
        )

        # Statistical significance pattern
        self.statistical_pattern = re.compile(
            r'(?:p\s*[<>=]\s*\d+\.\d+|r\s*=\s*\d+\.\d+|CI\s*=|SD\s*=)[^,;.)]*',
            re.IGNORECASE
        )

    def extract(self, text: str, page_texts: Dict[int, str],
                doc_type: DocumentType) -> List[ResultExtraction]:
        """Extract results from text"""
        results: List[ResultExtraction] = []
        language = self._get_language(doc_type)

        patterns = self.turkish_patterns if language == "turkish" else self.english_patterns

        for pattern in patterns:
            for match in pattern.finditer(text):
                result = self._process_match(match, text, text, page_texts, language)
                if result:
                    results.append(result)

        return self._deduplicate(results)

    def _process_match(self, match: re.Match, converted_text: str, original_text: str,
                       page_texts: Dict[int, str], language: str) -> Optional[ResultExtraction]:
        """Process a result match"""
        try:

            # Skip bibliography and garbled text
            if self._should_skip_match(converted_text, match.start(), match.group(0), category="result"):
                return None
            groups = match.groupdict()
            result_text = (groups.get('result') or '').strip()

            if not result_text or len(result_text) < 10:
                return None

            # Reject cross-line garbled text (newlines in result text)
            if '\n' in result_text or '\r' in result_text:
                return None

            # Reject results that are clearly garbled (no spaces = concatenated words)
            words = result_text.split()
            if words and any(len(w) > 30 for w in words):
                return None

            sentence, context = self._get_sentence_context(converted_text, match.start(), match.end())

            # Require quantitative content (numbers, percentages, statistics)
            has_quant = bool(re.search(r'\d+(?:\.\d+)?%|\d+(?:\.\d+)?\s*(?:km|ha|m²|species|individuals|dB)', result_text, re.IGNORECASE))
            has_stat = bool(re.search(r'p\s*[<>=]|r\s*=|CI\s*=|SD\s*=|±', result_text))
            if not has_quant and not has_stat:
                return None

            marine_score = self.fp_filter.get_marine_relevance_score(sentence, language)
            if marine_score < 0.1:
                return None

            result_type = self._classify_result_type(context)
            quantitative_value = self._extract_quantitative_value(context)
            statistical_significance = self._extract_statistical_significance(context)
            related_method = self._extract_related_method(context, language)

            page_num = self._find_page_number(match.start(), page_texts)

            confidence = 0.6 + (0.1 if marine_score > 0.3 else 0) + \
                         (0.1 if quantitative_value else 0) + \
                         (0.1 if statistical_significance else 0)

            return ResultExtraction(
                result_type=result_type,
                result_text=result_text[:300],
                quantitative_value=quantitative_value,
                statistical_significance=statistical_significance,
                related_method=related_method,
                context=context[:200],
                exact_text=match.group(0),
                page_number=page_num,
                confidence=min(confidence, 1.0),
                marine_relevance=marine_score
            )

        except Exception as e:
            logger.warning(f"Error processing result match: {e}")
            return None

    def _classify_result_type(self, context: str) -> str:
        """Classify the type of result"""
        context_lower = context.lower()

        if self.statistical_pattern.search(context):
            return 'statistical'
        elif self.quantitative_pattern.search(context):
            return 'quantitative'
        elif any(x in context_lower for x in ['spatial', 'map', 'area', 'region', 'zone', 'location']):
            return 'spatial'

        return 'qualitative'

    def _extract_quantitative_value(self, context: str) -> Optional[str]:
        """Extract quantitative value from context"""
        match = self.quantitative_pattern.search(context)
        if match:
            return match.group(0).strip()
        return None

    def _extract_statistical_significance(self, context: str) -> Optional[str]:
        """Extract statistical significance from context"""
        match = self.statistical_pattern.search(context)
        if match:
            return match.group(0).strip()
        return None

    def _extract_related_method(self, context: str, language: str) -> Optional[str]:
        """Extract related method from context"""
        method_terms = [
            'survey', 'interview', 'GIS', 'analysis', 'modeling', 'modelling',
            'sampling', 'experiment', 'simulation', 'assessment', 'monitoring'
        ]
        if language == 'turkish':
            method_terms.extend([
                'anket', 'analiz', 'modelleme', 'örnekleme', 'izleme'
            ])

        context_lower = context.lower()
        for term in method_terms:
            if term.lower() in context_lower:
                return term

        return None
