"""
Prohibition Extractor - FULLY WORKING
Extracts prohibitions, bans, and restrictions from legal and scientific texts
"""
import re
import logging
from typing import Dict, List, Optional

try:
    from ..core.enums import DocumentType
    from ..data_structures import ProhibitionExtraction
    from .base_extractor import BaseExtractor
except ImportError:
    from core.enums import DocumentType
    from data_structures import ProhibitionExtraction
    from extractors.base_extractor import BaseExtractor

logger = logging.getLogger(__name__)


class ProhibitionExtractor(BaseExtractor):
    """Extract prohibitions and restrictions from MSP documents"""

    def _compile_patterns(self):
        """Compile prohibition patterns for both languages"""
        # Turkish patterns
        self.turkish_patterns = [
            # Activity banned: X yasaklanmıştır/yasaktır
            re.compile(
                r'(?P<activity>avcılık|balıkçılık|av\s+ve\s+balıkçılık|trol|sürütme|dinamit|kıyı\s+doldurma|'
                r'dolgu|inşaat|kazı|tahribat|atık\s+boşaltma|deşarj|çıkarma|hafriyat)\s*'
                r'(?P<prohibition>yasak(?:lanm[ıi][şs]t[ıi]r|t[ıi]r|)|yasaklanm[ıi][şs]|men\s+edilmi[şs]|'
                r'men\s+olunmu[şs]|izin\s+verilmez)',
                re.IGNORECASE | re.UNICODE
            ),
            # Generic prohibition: yasaktır/yasaklanmıştır
            re.compile(
                r'(?P<activity>[\w\s]+?)\s*'
                r'(?P<prohibition>yasak(?:t[ıi]r|lanm[ıi][şs]t[ıi]r)|men\s+edilmi[şs]tir|'
                r'izin\s+verilmez|kabul\s+edilmez)',
                re.IGNORECASE | re.UNICODE
            ),
            # Prohibited areas: X bölgesinde yasaktır
            re.compile(
                r'(?P<area>koruma\s+alan[ıi]|rezerv|sit\s+alan[ıi]|yasak\s+bölge|özel\s+alan)\s*'
                r'(?:nda|nde|sında|sinde|içinde)?\s*'
                r'(?P<activity>[\w\s]+?)\s*'
                r'(?P<prohibition>yasakt[ıi]r|izin\s+verilmez)',
                re.IGNORECASE | re.UNICODE
            ),
            # Method prohibitions: X ile avlanma yasaktır
            re.compile(
                r'(?P<method>trol|dinamit|zehir|elektrik|ağ|patlayıcı)\s*'
                r'(?:ile|kullanarak|kullan[ıi]larak)?\s*'
                r'(?:avlanma|balıkçılık|yakalama)\s*'
                r'(?P<prohibition>yasakt[ıi]r|men\s+edilmi[şs]tir)',
                re.IGNORECASE | re.UNICODE
            ),
            # Exceptions: hariç/müstesna
            re.compile(
                r'(?P<exception>[\w\s]+?)\s*(?:hariç|müstesna|dışında|istisna)',
                re.IGNORECASE | re.UNICODE
            ),
        ]

        # English patterns
        self.english_patterns = [
            # Activity prohibited: X is prohibited/banned
            re.compile(
                r'(?P<activity>fishing|trawling|hunting|extraction|dumping|discharge|'
                r'construction|dredging|mining|anchoring)\s*'
                r'(?:is\s+)?(?P<prohibition>prohibited|banned|forbidden|not\s+permitted|'
                r'not\s+allowed|illegal)',
                re.IGNORECASE
            ),
            # Generic prohibition patterns
            re.compile(
                r'(?P<prohibition>prohibit(?:s|ed)?|ban(?:s|ned)?|forbid(?:s|den)?)\s+'
                r'(?P<activity>[\w\s]+?)(?:\s+in|\s+from|\s+within)',
                re.IGNORECASE
            ),
            # No X allowed/permitted
            re.compile(
                r'no\s+(?P<activity>fishing|trawling|hunting|extraction|dumping|construction)\s*'
                r'(?P<prohibition>allowed|permitted|authorized)',
                re.IGNORECASE
            ),
            # Prohibited areas: X in Y is prohibited
            re.compile(
                r'(?P<activity>[\w\s]+?)\s+(?:in|within)\s+'
                r'(?P<area>protected\s+areas?|marine\s+reserves?|sanctuaries|conservation\s+zones?)\s*'
                r'(?:is\s+)?(?P<prohibition>prohibited|banned|forbidden)',
                re.IGNORECASE
            ),
            # Method prohibitions: fishing with X is prohibited
            re.compile(
                r'(?:fishing|hunting)\s+(?:with|using)\s+'
                r'(?P<method>trawl|dynamite|poison|explosives|nets)\s*'
                r'(?:is\s+)?(?P<prohibition>prohibited|banned|illegal)',
                re.IGNORECASE
            ),
            # Except/excluding patterns
            re.compile(
                r'(?:except|excluding|with\s+the\s+exception\s+of)\s+(?P<exception>[\w\s]+)',
                re.IGNORECASE
            ),
        ]

    def extract(self, text: str, page_texts: Dict[int, str],
                doc_type: DocumentType) -> List[ProhibitionExtraction]:
        """Extract prohibitions from text"""
        results: List[ProhibitionExtraction] = []
        language = self._get_language(doc_type)

        # Convert written numbers
        converted_text = text
        if self.number_converter:
            converted_text = self.number_converter.convert_text(text, language)

        # Select patterns based on language
        patterns = self.turkish_patterns if language == "turkish" else self.english_patterns

        # Extract prohibitions
        for pattern in patterns:
            for match in pattern.finditer(converted_text):
                result = self._process_match(match, converted_text, text, page_texts, language, doc_type)
                if result:
                    results.append(result)

        return self._deduplicate(results)

    def _process_match(self, match: re.Match, converted_text: str, original_text: str,
                       page_texts: Dict[int, str], language: str,
                       doc_type: DocumentType) -> Optional[ProhibitionExtraction]:
        """Process a prohibition match"""
        try:
            groups = match.groupdict()
            sentence, context = self._get_sentence_context(converted_text, match.start(), match.end())

            # Clean legal references
            cleaned_sentence = sentence
            if self.legal_ref_filter:
                cleaned_sentence = self.legal_ref_filter.clean_text(sentence)
                if match.group(0) not in cleaned_sentence:
                    return None

            # False positive check
            is_fp, fp_reason = self._is_false_positive(cleaned_sentence, match.group(0), language)
            if is_fp:
                return None

            # Check marine relevance
            marine_score = self.fp_filter.get_marine_relevance_score(cleaned_sentence, language)
            min_marine_score = 0.05 if doc_type in [DocumentType.LEGAL_TURKISH, DocumentType.LEGAL_ENGLISH] else 0.15

            if marine_score < min_marine_score:
                return None

            # Parse prohibition details
            prohibition_type = self._parse_prohibition_type(groups, language)
            activity = groups.get('activity', '').strip() if groups.get('activity') else None
            scope = self._parse_scope(groups, context, language)
            exceptions = self._extract_exceptions(context, language)

            # Extract legal reference
            legal_ref = self._extract_legal_reference(context, language)

            # Find page number
            page_num = self._find_page_number(match.start(), page_texts)

            # Calculate confidence
            confidence = self._calculate_confidence(
                marine_score, bool(activity), bool(scope)
            )

            return ProhibitionExtraction(
                prohibition_type=prohibition_type,
                activity=activity,
                scope=scope,
                exceptions=exceptions,
                legal_reference=legal_ref,
                context=context[:200],
                exact_text=match.group(0),
                page_number=page_num,
                confidence=confidence,
                marine_relevance=marine_score
            )

        except Exception as e:
            logger.warning(f"Error processing prohibition match: {e}")
            return None

    def _parse_prohibition_type(self, groups: Dict, language: str) -> str:
        """Parse prohibition type from match groups"""
        prohibition = (groups.get('prohibition') or '').lower()
        method = groups.get('method', '')
        area = groups.get('area', '')

        if method:
            return 'method_prohibited'
        elif area:
            return 'area_restricted'
        elif language == 'turkish':
            if 'yasak' in prohibition or 'men' in prohibition:
                return 'activity_banned'
            elif 'izin verilmez' in prohibition:
                return 'not_permitted'
        else:
            if 'prohibit' in prohibition or 'ban' in prohibition:
                return 'activity_banned'
            elif 'not permitted' in prohibition or 'not allowed' in prohibition:
                return 'not_permitted'

        return 'restriction'

    def _parse_scope(self, groups: Dict, context: str, language: str) -> Optional[str]:
        """Parse scope of prohibition from match groups and context"""
        area = groups.get('area', '')
        if area:
            return area

        # Try to extract scope from context
        if language == 'turkish':
            scope_patterns = [
                r'(?:bölgede|alanda|sahada|sınırlar\s+içinde)',
                r'(?:koruma\s+alan[ıi]|özel\s+alan|yasak\s+bölge)',
            ]
        else:
            scope_patterns = [
                r'(?:in\s+the\s+area|within\s+the\s+zone|in\s+the\s+region)',
                r'(?:protected\s+area|marine\s+reserve|conservation\s+zone)',
            ]

        for pattern in scope_patterns:
            match = re.search(pattern, context, re.IGNORECASE | re.UNICODE)
            if match:
                return match.group(0)

        return None

    def _extract_exceptions(self, context: str, language: str) -> List[str]:
        """Extract exceptions from context"""
        exceptions = []

        if language == 'turkish':
            patterns = [
                r'(?:hariç|müstesna|dışında|istisna)[\s:]+([^.;]+)',
                r'([^.;]+?)\s+(?:hariç|müstesna)',
            ]
        else:
            patterns = [
                r'(?:except|excluding|with\s+the\s+exception\s+of)[\s:]+([^.;]+)',
                r'([^.;]+?)\s+(?:are\s+)?excepted',
            ]

        for pattern in patterns:
            matches = re.finditer(pattern, context, re.IGNORECASE | re.UNICODE)
            for match in matches:
                exception = match.group(1).strip()
                if exception and len(exception) < 100:
                    exceptions.append(exception)

        return exceptions[:3]  # Limit to 3 exceptions

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

    def _calculate_confidence(self, marine_score: float, has_activity: bool,
                             has_scope: bool) -> float:
        """Calculate confidence score"""
        base_confidence = 0.7

        if marine_score > 0.3:
            base_confidence += 0.1
        if has_activity:
            base_confidence += 0.1
        if has_scope:
            base_confidence += 0.05

        return min(base_confidence, 1.0)
