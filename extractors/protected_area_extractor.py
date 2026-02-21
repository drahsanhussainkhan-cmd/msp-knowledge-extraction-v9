"""
Protected Area Extractor - FULLY WORKING
Extracts protected area mentions (MPAs, conservation zones, national parks)
"""
import re
import logging
from typing import Dict, List, Optional

try:
    from ..core.enums import DocumentType
    from ..data_structures import ProtectedAreaExtraction
    from .base_extractor import BaseExtractor
except ImportError:
    from core.enums import DocumentType
    from data_structures import ProtectedAreaExtraction
    from extractors.base_extractor import BaseExtractor

logger = logging.getLogger(__name__)


class ProtectedAreaExtractor(BaseExtractor):
    """Extract protected area mentions from MSP documents"""

    def _compile_patterns(self):
        """Compile protected area patterns for both languages"""
        # Turkish patterns
        self.turkish_patterns = [
            # Marine protected areas
            re.compile(
                r'(?P<name>[\w\s]+?)?\s*'
                r'(?P<area_type>deniz\s+koruma\s+alan[ıi]|özel\s+çevre\s+koruma\s+bölgesi|'
                r'sit\s+alan[ıi]|tabiat\s+park[ıi]|milli\s+park|koruma\s+alan[ıi]|'
                r'deniz\s+rezervi|özel\s+koruma\s+alan[ıi])',
                re.IGNORECASE | re.UNICODE
            ),
            # Specific designations
            re.compile(
                r'(?P<name>[A-ZÇĞIÖŞÜ][\wçğıöşü\s]+?)\s*'
                r'(?P<designation>özel\s+çevre\s+koruma\s+bölgesi|deniz\s+koruma\s+alan[ıi]|'
                r'sit\s+alan[ıi]|milli\s+park)',
                re.UNICODE
            ),
            # Protection status
            re.compile(
                r'(?P<name>[\w\s]+?)\s*'
                r'(?:alan[ıi]|bölge(?:si)?)\s*'
                r'(?P<designation>koruma\s+altına\s+al[ıi]n(?:m[ıi][şs]|acak)|'
                r'koruma\s+statüsü\s+veril(?:mi[şs]|ecek))',
                re.IGNORECASE | re.UNICODE
            ),
        ]

        # English patterns
        self.english_patterns = [
            # Marine protected areas
            re.compile(
                r'(?P<name>[\w\s]+?)?\s*'
                r'(?P<area_type>marine\s+protected\s+area|special\s+area\s+of\s+conservation|'
                r'marine\s+reserve|national\s+park|sanctuary|conservation\s+zone|'
                r'protected\s+seascape|nature\s+reserve|MPA)',
                re.IGNORECASE
            ),
            # Specific designations
            re.compile(
                r'(?P<name>[A-Z][\w\s]+?)\s+'
                r'(?P<designation>Marine\s+Protected\s+Area|National\s+Park|'
                r'Marine\s+Reserve|Sanctuary|Conservation\s+Zone)',
                re.UNICODE
            ),
            # Protection designations
            re.compile(
                r'(?:designat(?:e|ed|ion)|establish(?:ed)?)\s+(?:as\s+)?'
                r'(?:a\s+)?(?P<designation>marine\s+protected\s+area|marine\s+reserve|'
                r'conservation\s+zone|sanctuary)',
                re.IGNORECASE
            ),
            # Under protection
            re.compile(
                r'(?P<name>[\w\s]+?)\s+(?:is|are)\s+(?:under\s+)?'
                r'(?P<designation>protected|conservation)',
                re.IGNORECASE
            ),
        ]

    def extract(self, text: str, page_texts: Dict[int, str],
                doc_type: DocumentType) -> List[ProtectedAreaExtraction]:
        """Extract protected areas from text"""
        results: List[ProtectedAreaExtraction] = []
        language = self._get_language(doc_type)

        # Convert written numbers
        converted_text = text
        if self.number_converter:
            converted_text = self.number_converter.convert_text(text, language)

        # Select patterns based on language
        patterns = self.turkish_patterns if language == "turkish" else self.english_patterns

        # Extract protected areas
        for pattern in patterns:
            for match in pattern.finditer(converted_text):
                result = self._process_match(match, converted_text, text, page_texts, language, doc_type)
                if result:
                    results.append(result)

        return self._deduplicate(results)

    def _process_match(self, match: re.Match, converted_text: str, original_text: str,
                       page_texts: Dict[int, str], language: str,
                       doc_type: DocumentType) -> Optional[ProtectedAreaExtraction]:
        """Process a protected area match"""
        try:

            # Skip bibliography and garbled text
            if self._should_skip_match(converted_text, match.start(), match.group(0), category="protected_area"):
                return None
            groups = match.groupdict()
            sentence, context = self._get_sentence_context(converted_text, match.start(), match.end())

            # Clean legal references
            cleaned_sentence = sentence
            if self.legal_ref_filter:
                cleaned_sentence = self.legal_ref_filter.clean_text(sentence)

            # False positive check
            is_fp, fp_reason = self._is_false_positive(cleaned_sentence, match.group(0), language)
            if is_fp:
                return None

            # Check marine relevance
            marine_score = self.fp_filter.get_marine_relevance_score(cleaned_sentence, language)
            min_marine_score = 0.1

            if marine_score < min_marine_score:
                return None

            # Parse protected area details
            area_type = groups.get('area_type', '').strip() if groups.get('area_type') else 'protected_area'
            name = groups.get('name', '').strip() if groups.get('name') else None
            designation = groups.get('designation', '').strip() if groups.get('designation') else None

            # Extract restrictions
            restrictions = self._extract_restrictions(context, language)

            # Extract legal reference
            legal_ref = self._extract_legal_reference(context, language)

            # Find page number
            page_num = self._find_page_number(match.start(), page_texts)

            # Calculate confidence
            confidence = self._calculate_confidence(
                marine_score, bool(name), bool(designation)
            )

            return ProtectedAreaExtraction(
                area_type=area_type[:100],
                name=name[:200] if name else None,
                designation=designation[:200] if designation else None,
                restrictions=restrictions,
                legal_reference=legal_ref,
                context=context[:200],
                exact_text=match.group(0),
                page_number=page_num,
                confidence=confidence,
                marine_relevance=marine_score
            )

        except Exception as e:
            logger.warning(f"Error processing protected area match: {e}")
            return None

    def _extract_restrictions(self, context: str, language: str) -> List[str]:
        """Extract restrictions from context"""
        restrictions = []

        if language == 'turkish':
            patterns = [
                r'(?:yasaklan(?:m[ıi][şs]|acak)|izin\s+verilme(?:z|yecek))\s*:?\s*([^.;]+)',
                r'([^.;]+?)\s+yasakt[ıi]r',
            ]
        else:
            patterns = [
                r'(?:prohibited|forbidden|not\s+allowed)\s*:?\s*([^.;]+)',
                r'no\s+([^.;]+?)\s+(?:is\s+)?(?:allowed|permitted)',
            ]

        for pattern in patterns:
            matches = re.finditer(pattern, context, re.IGNORECASE | re.UNICODE)
            for match in matches:
                restriction = match.group(1).strip()
                if restriction and len(restriction) < 100:
                    restrictions.append(restriction)

        return restrictions[:5]  # Limit to 5 restrictions

    def _extract_legal_reference(self, context: str, language: str) -> Optional[str]:
        """Extract legal reference from context"""
        if language == 'turkish':
            pattern = r'\d+\s*sayılı\s*(?:kanun|yönetmelik|tüzük)'
        else:
            pattern = r'(?:Act|Law|Regulation)\s+(?:No\.\s*)?\d+'

        match = re.search(pattern, context, re.IGNORECASE | re.UNICODE)
        if match:
            return match.group(0)
        return None

    def _calculate_confidence(self, marine_score: float, has_name: bool,
                             has_designation: bool) -> float:
        """Calculate confidence score"""
        base_confidence = 0.7

        if marine_score > 0.3:
            base_confidence += 0.1
        if has_name:
            base_confidence += 0.1
        if has_designation:
            base_confidence += 0.05

        return min(base_confidence, 1.0)
