"""
Penalty Extractor - FULLY WORKING
Extracts penalties (fines, imprisonment, license revocation) from legal texts
"""
import re
import logging
from typing import Dict, List, Optional

try:
    from ..core.enums import DocumentType
    from ..data_structures import PenaltyExtraction
    from .base_extractor import BaseExtractor
except ImportError:
    from core.enums import DocumentType
    from data_structures import PenaltyExtraction
    from extractors.base_extractor import BaseExtractor

logger = logging.getLogger(__name__)


class PenaltyExtractor(BaseExtractor):
    """Extract penalty information from MSP documents"""

    def _compile_patterns(self):
        """Compile penalty patterns for both languages"""
        # Turkish patterns
        self.turkish_patterns = [
            # Fine amounts: X TL ceza/para cezası
            re.compile(
                r'(?P<amount>\d+(?:[.,]\d+)?)\s*'
                r'(?P<currency>TL|Türk\s*[Ll]irası|lira|₺)\s*'
                r'(?P<type>(?:para\s*)?ceza|idari\s*para\s*cezas[ıi]|para\s*cezas[ıi]|[aâ]ğ[ıi]r\s*para\s*cezas[ıi])',
                re.IGNORECASE | re.UNICODE
            ),
            # Fine ranges: X-Y TL
            re.compile(
                r'(?P<min>\d+(?:[.,]\d+)?)\s*(?:ila|ilâ|ile|-|–)\s*'
                r'(?P<max>\d+(?:[.,]\d+)?)\s*'
                r'(?P<currency>TL|Türk\s*[Ll]irası|lira|₺)\s*'
                r'(?:para\s*)?ceza',
                re.IGNORECASE | re.UNICODE
            ),
            # Imprisonment: X yıl/ay hapis
            re.compile(
                r'(?P<duration>\d+(?:[.,]\d+)?)\s*'
                r'(?P<unit>y[ıi]l|ay|gün)\s*'
                r'(?:(?:kadar|ile|ve|veya)\s+)?'
                r'(?P<type>hapis|hapsi?s\s*cezas[ıi]|özgürlü[ğg]ünden\s*mahrum)',
                re.IGNORECASE | re.UNICODE
            ),
            # Imprisonment ranges
            re.compile(
                r'(?P<min>\d+)\s*(?:ila|ilâ|ile|-|–)\s*(?P<max>\d+)\s*'
                r'(?P<unit>y[ıi]l|ay|gün)\s*'
                r'(?:hapis|hapsi?s\s*cezas[ıi])',
                re.IGNORECASE | re.UNICODE
            ),
            # License revocation
            re.compile(
                r'(?P<type>(?:r[uü]hsat|lisans|izin|belge)\s*(?:iptal[ıi]?|geri\s*al[ıi]n(?:mas[ıi]|[ıi]r)|kald[ıi]r[ıi]l(?:mas[ıi]|[ıi]r)))',
                re.IGNORECASE | re.UNICODE
            ),
            # Activity ban/suspension
            re.compile(
                r'(?P<duration>\d+)\s*(?P<unit>y[ıi]l|ay|gün)\s*'
                r'(?:süre(?:yle|li)?|için)?\s*'
                r'(?P<type>faaliyetten?\s*men|yasaklan(?:ma|[ıi]r)|durdur(?:ma|ul(?:ma|ur)))',
                re.IGNORECASE | re.UNICODE
            ),
            # Generic penalty mention
            re.compile(
                r'(?P<type>ceza(?:land[ıi]r[ıi]l[ıi]r|ya\s*tabi\s*tutulur)|yaptırım|idari\s*yaptırım)',
                re.IGNORECASE | re.UNICODE
            ),
        ]

        # English patterns
        self.english_patterns = [
            # Fine amounts: $X fine/penalty
            re.compile(
                r'(?P<amount>\d+(?:[.,]\d+)?)\s*'
                r'(?P<currency>USD|EUR|GBP|dollars?|\$|€|£)\s*'
                r'(?P<type>fine|penalty|civil\s+penalty|administrative\s+fine)',
                re.IGNORECASE
            ),
            # Fine with currency after: fine of $X
            re.compile(
                r'(?P<type>fine|penalty)\s+of\s+'
                r'(?P<currency>USD|EUR|GBP|\$|€|£)?\s*'
                r'(?P<amount>\d+(?:[.,]\d+)?)',
                re.IGNORECASE
            ),
            # Fine ranges
            re.compile(
                r'(?:fine|penalty)\s+(?:of\s+)?(?:from\s+|between\s+)?'
                r'(?P<currency>\$|€|£|USD|EUR|GBP)?\s*'
                r'(?P<min>\d+(?:[.,]\d+)?)\s*(?:to|and|-|–)\s*'
                r'(?P<currency2>\$|€|£|USD|EUR|GBP)?\s*'
                r'(?P<max>\d+(?:[.,]\d+)?)',
                re.IGNORECASE
            ),
            # Imprisonment: X years/months imprisonment
            re.compile(
                r'(?P<duration>\d+(?:[.,]\d+)?)\s*'
                r'(?P<unit>years?|months?|days?)\s*'
                r'(?:of\s+)?(?P<type>imprisonment|prison|jail|incarceration)',
                re.IGNORECASE
            ),
            # Imprisonment ranges
            re.compile(
                r'(?:between\s+|from\s+)?(?P<min>\d+)\s*(?:to|and|-|–)\s*(?P<max>\d+)\s*'
                r'(?P<unit>years?|months?|days?)\s*'
                r'(?:of\s+)?(?:imprisonment|prison)',
                re.IGNORECASE
            ),
            # License/permit revocation
            re.compile(
                r'(?P<type>(?:license|permit|authorization)\s+(?:revocation|suspension|cancellation|withdrawal))',
                re.IGNORECASE
            ),
            # Revocation of license/permit
            re.compile(
                r'(?:revocation|suspension|cancellation|withdrawal)\s+of\s+'
                r'(?P<license_type>(?:fishing\s+)?(?:license|permit|authorization))',
                re.IGNORECASE
            ),
            # Activity ban
            re.compile(
                r'(?P<type>ban(?:ned)?|prohibited|suspended)\s+(?:from|for)\s+'
                r'(?P<duration>\d+)\s*(?P<unit>years?|months?|days?)',
                re.IGNORECASE
            ),
        ]

    def extract(self, text: str, page_texts: Dict[int, str],
                doc_type: DocumentType) -> List[PenaltyExtraction]:
        """Extract penalties from text"""
        results: List[PenaltyExtraction] = []
        language = self._get_language(doc_type)

        # Convert written numbers
        converted_text = text
        if self.number_converter:
            converted_text = self.number_converter.convert_text(text, language)

        # Select patterns based on language
        patterns = self.turkish_patterns if language == "turkish" else self.english_patterns

        # Extract penalties
        for pattern in patterns:
            for match in pattern.finditer(converted_text):
                result = self._process_match(match, converted_text, text, page_texts, language, doc_type)
                if result:
                    results.append(result)

        return self._deduplicate(results)

    def _process_match(self, match: re.Match, converted_text: str, original_text: str,
                       page_texts: Dict[int, str], language: str,
                       doc_type: DocumentType) -> Optional[PenaltyExtraction]:
        """Process a penalty match"""
        try:
            groups = match.groupdict()
            sentence, context = self._get_sentence_context(converted_text, match.start(), match.end())

            # Clean legal references
            cleaned_sentence = sentence
            if self.legal_ref_filter:
                cleaned_sentence = self.legal_ref_filter.clean_text(sentence)
                if match.group(0) not in cleaned_sentence:
                    logger.debug(f"Match removed by legal ref filter: {match.group(0)[:50]}...")
                    return None

            # False positive check
            is_fp, fp_reason = self._is_false_positive(cleaned_sentence, match.group(0), language)
            if is_fp:
                logger.debug(f"FP rejected ({fp_reason}): {match.group(0)[:50]}...")
                return None

            # Check marine relevance
            marine_score = self.fp_filter.get_marine_relevance_score(cleaned_sentence, language)
            min_marine_score = 0.05 if doc_type in [DocumentType.LEGAL_TURKISH, DocumentType.LEGAL_ENGLISH] else 0.15

            if marine_score < min_marine_score:
                logger.debug(f"Low marine relevance ({marine_score:.2f}): {sentence[:50]}...")
                return None

            # Parse penalty details
            penalty_type = self._parse_penalty_type(groups, language)
            amount, min_amount, max_amount = self._parse_amount(groups)
            currency = self._parse_currency(groups, language)
            duration = self._parse_duration(groups)

            # Extract violation context
            violation = self._extract_violation(context, language)

            # Extract legal reference
            legal_ref = self._extract_legal_reference(context, language)

            # Find page number
            page_num = self._find_page_number(match.start(), page_texts)

            # Calculate confidence
            confidence = self._calculate_confidence(
                marine_score, bool(amount or duration), bool(violation)
            )

            return PenaltyExtraction(
                penalty_type=penalty_type,
                amount=amount if not min_amount else None,
                currency=currency,
                duration=duration,
                violation=violation,
                legal_reference=legal_ref,
                context=context[:200],
                exact_text=match.group(0),
                page_number=page_num,
                confidence=confidence,
                marine_relevance=marine_score
            )

        except Exception as e:
            logger.warning(f"Error processing penalty match: {e}")
            return None

    def _parse_penalty_type(self, groups: Dict, language: str) -> str:
        """Parse penalty type from match groups"""
        type_text = (groups.get('type') or '').lower()

        if language == 'turkish':
            if 'hapis' in type_text or 'özgürlü' in type_text:
                return 'imprisonment'
            elif 'ruhsat' in type_text or 'lisans' in type_text or 'izin' in type_text or 'belge' in type_text:
                return 'license_revocation'
            elif 'men' in type_text or 'yasaklan' in type_text or 'durdur' in type_text:
                return 'activity_suspension'
            elif 'ceza' in type_text or 'para' in type_text:
                return 'fine'
        else:
            if 'imprisonment' in type_text or 'prison' in type_text or 'jail' in type_text:
                return 'imprisonment'
            elif 'revocation' in type_text or 'suspension' in type_text or 'cancellation' in type_text:
                return 'license_revocation'
            elif 'ban' in type_text or 'prohibited' in type_text or 'suspended' in type_text:
                return 'activity_suspension'
            elif 'fine' in type_text or 'penalty' in type_text:
                return 'fine'

        return 'unspecified_penalty'

    def _parse_amount(self, groups: Dict) -> tuple:
        """Parse fine amount from match groups"""
        amount = None
        min_amount = None
        max_amount = None

        if 'amount' in groups and groups['amount']:
            amount = float(groups['amount'].replace(',', ''))
        elif 'min' in groups and groups['min']:
            min_amount = float(groups['min'].replace(',', ''))
            max_amount = float(groups['max'].replace(',', ''))

        return amount, min_amount, max_amount

    def _parse_currency(self, groups: Dict, language: str) -> Optional[str]:
        """Parse currency from match groups"""
        currency = groups.get('currency', '')
        if not currency:
            currency = groups.get('currency2', '')

        if not currency:
            return 'TL' if language == 'turkish' else None

        currency = currency.upper().replace('₺', 'TL')
        if 'LIRA' in currency or 'LİRA' in currency:
            return 'TL'

        return currency

    def _parse_duration(self, groups: Dict) -> Optional[str]:
        """Parse imprisonment duration"""
        if 'duration' in groups and groups['duration']:
            duration = groups['duration']
            unit = groups.get('unit', 'year')
            return f"{duration} {unit}"
        elif 'min' in groups and 'unit' in groups:
            return f"{groups['min']}-{groups['max']} {groups['unit']}"
        return None

    def _extract_violation(self, context: str, language: str) -> Optional[str]:
        """Extract violation description from context"""
        if language == 'turkish':
            patterns = [
                r'(?:ihlal|çi[ğg]ne|aykırı|yasak).*?(?:faaliyeti?|eylemi?|davranı[şs])',
                r'(?:izinsiz|ruhsatsız|kaçak).*?(?:av|balık|çıkarma|inşaat)',
            ]
        else:
            patterns = [
                r'(?:violation|breach|infringement)\s+of\s+\w+',
                r'(?:illegal|unlawful|unauthorized)\s+\w+(?:\s+\w+){0,3}',
            ]

        for pattern in patterns:
            match = re.search(pattern, context, re.IGNORECASE | re.UNICODE)
            if match:
                return match.group(0)[:100]

        return None

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

    def _calculate_confidence(self, marine_score: float, has_amount: bool,
                             has_violation: bool) -> float:
        """Calculate confidence score"""
        base_confidence = 0.7

        if marine_score > 0.3:
            base_confidence += 0.1
        if has_amount:
            base_confidence += 0.1
        if has_violation:
            base_confidence += 0.05

        return min(base_confidence, 1.0)
