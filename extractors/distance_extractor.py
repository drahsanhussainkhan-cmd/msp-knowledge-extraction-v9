"""
Distance/Buffer Zone Extractor - FULLY WORKING
Extracts distance measurements, buffer zones, setbacks from legal and scientific texts
"""
import re
import logging
from typing import Dict, List, Optional

try:
    from ..core.enums import DocumentType
    from ..data_structures import DistanceExtraction
    from .base_extractor import BaseExtractor
except ImportError:
    from core.enums import DocumentType
    from data_structures import DistanceExtraction
    from extractors.base_extractor import BaseExtractor

logger = logging.getLogger(__name__)


class DistanceExtractor(BaseExtractor):
    """Extract distance/buffer zone measurements from MSP documents"""

    def _compile_patterns(self):
        """Compile distance patterns for both languages"""
        # Turkish patterns
        self.turkish_patterns = [
            # Basic: [qualifier] X metre/km
            re.compile(
                r'(?P<qualifier>en\s+az|en\s+fazla|en\s+çok|asgari|azami|minimum|maksimum)?\s*'
                r'(?P<value>\d+(?:[.,]\d+)?)\s*'
                r'(?P<unit>metre|metrelik|mt|m\.?|km|kilometre|deniz\s*mili|mil)\b',
                re.IGNORECASE | re.UNICODE
            ),
            # X metreden fazla/az
            re.compile(
                r'(?P<value>\d+(?:[.,]\d+)?)\s*'
                r'(?P<unit>metre|m\.?|km)\s*'
                r"['\u2019]?\s*"
                r'(?P<qualifier>[dD][eaEA]n\s+(?:fazla|az|çok)|altında|üstünde|üzerinde|ve\s+üzeri)',
                re.IGNORECASE | re.UNICODE
            ),
            # Range: X-Y metre
            re.compile(
                r'(?P<min>\d+(?:[.,]\d+)?)\s*[-–—]\s*(?P<max>\d+(?:[.,]\d+)?)\s*'
                r'(?P<unit>metre|m\.?|km)',
                re.IGNORECASE | re.UNICODE
            ),
            # X ilâ Y metre
            re.compile(
                r'(?P<min>\d+(?:[.,]\d+)?)\s*(?:ilâ|ila|ile)\s*(?P<max>\d+(?:[.,]\d+)?)\s*'
                r'(?P<unit>metre|m\.?|km)',
                re.IGNORECASE | re.UNICODE
            ),
            # Reference + distance: kıyıdan 100 metre
            re.compile(
                r'(?P<reference>kıyı|sahil|deniz|liman|iskele|tesis|koruma\s*alanı)'
                r'(?:dan|den|[ıiuü]ndan|sınırından|çizgisinden)?\s*'
                r'(?:itibaren\s+)?'
                r'(?P<value>\d+(?:[.,]\d+)?)\s*'
                r'(?P<unit>metre|m\.?|km)',
                re.IGNORECASE | re.UNICODE
            ),
            # Depth: X metre derinlik
            re.compile(
                r'(?P<value>\d+(?:[.,]\d+)?)\s*'
                r'(?P<unit>metre|m\.?)\s*'
                r'(?P<context>derinlik|derinliğe|derinliğinde|derinlikte)',
                re.IGNORECASE | re.UNICODE
            ),
        ]

        # English patterns
        self.english_patterns = [
            # Basic: [qualifier] X meters/km
            re.compile(
                r'(?P<qualifier>at\s+least|minimum|maximum|up\s+to|approximately|about|around)?\s*'
                r'(?P<value>\d+(?:[.,]\d+)?)\s*'
                r'(?P<unit>meters?|metres?|m|km|kilometers?|kilometres?|nautical\s*miles?|nm|nmi|miles?)\b',
                re.IGNORECASE
            ),
            # Range: X-Y meters
            re.compile(
                r'(?P<min>\d+(?:[.,]\d+)?)\s*[-–to]+\s*(?P<max>\d+(?:[.,]\d+)?)\s*'
                r'(?P<unit>m|km|meters?|metres?|nm)',
                re.IGNORECASE
            ),
            # Buffer/setback specific
            re.compile(
                r'(?P<type>buffer|setback|distance)\s+(?:zone\s+)?(?:of\s+)?'
                r'(?P<value>\d+(?:[.,]\d+)?)\s*(?P<unit>m|km|meters?|metres?)',
                re.IGNORECASE
            ),
            # From X: distance from coast
            re.compile(
                r'(?:distance\s+)?(?:of\s+)?(?P<value>\d+(?:[.,]\d+)?)\s*'
                r'(?P<unit>m|km|meters?|metres?|nm)\s+'
                r'(?:from\s+(?:the\s+)?)?(?P<reference>coast|shore|coastline|baseline|port|facility)',
                re.IGNORECASE
            ),
            # Between X and Y
            re.compile(
                r'between\s+(?P<min>\d+(?:[.,]\d+)?)\s*(?:and|to)\s*(?P<max>\d+(?:[.,]\d+)?)\s*'
                r'(?P<unit>m|km|meters?|metres?)',
                re.IGNORECASE
            ),
            # Depth: depth of X meters
            re.compile(
                r'(?P<context>depth)\s+(?:of\s+)?(?P<value>\d+(?:[.,]\d+)?)\s*'
                r'(?P<unit>m|meters?|metres?)',
                re.IGNORECASE
            ),
        ]

    def extract(self, text: str, page_texts: Dict[int, str],
                doc_type: DocumentType) -> List[DistanceExtraction]:
        """Extract distances from text"""
        results: List[DistanceExtraction] = []
        language = self._get_language(doc_type)

        # Convert written numbers first (if converter available)
        converted_text = text
        if self.number_converter:
            converted_text = self.number_converter.convert_text(text, language)

        # Select patterns based on language
        patterns = self.turkish_patterns if language == "turkish" else self.english_patterns

        # Extract from numeric patterns
        for pattern in patterns:
            for match in pattern.finditer(converted_text):
                result = self._process_match(match, converted_text, text, page_texts, language, doc_type)
                if result:
                    results.append(result)

        return self._deduplicate(results)

    def _process_match(self, match: re.Match, converted_text: str, original_text: str,
                       page_texts: Dict[int, str], language: str,
                       doc_type: DocumentType) -> Optional[DistanceExtraction]:
        """Process a distance match"""
        try:

            # Skip bibliography and garbled text
            if self._should_skip_match(converted_text, match.start(), match.group(0), category="distance"):
                return None
            groups = match.groupdict()
            sentence, context = self._get_sentence_context(converted_text, match.start(), match.end())

            # Clean sentence from legal references and dates BEFORE processing (if filter available)
            cleaned_sentence = sentence
            if self.legal_ref_filter:
                cleaned_sentence = self.legal_ref_filter.clean_text(sentence)

                # If cleaning removed the match, it was probably a legal reference
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
            min_marine_score = 0.15 if doc_type in [DocumentType.LEGAL_TURKISH, DocumentType.LEGAL_ENGLISH] else 0.15

            if marine_score < min_marine_score:
                logger.debug(f"Low marine relevance ({marine_score:.2f}): {sentence[:50]}...")
                return None

            # Reject building/construction/urban planning context (non-marine measurements)
            context_lower = context.lower() if context else ''
            building_terms_tr = [
                'kat yüksekli', 'bina yüksekli', 'iç yükseklik', 'tavan yüksekli',
                'bodrum kat', 'zemin kat', 'asma kat', 'merdiven', 'rampa ',
                'konut ', 'oturma odası', 'yatak odası', 'mutfak', 'banyo', 'tuvalet',
                'pencere', 'parmaklık', 'duvar kalınlı', 'piyes',
                'yapı ruhsat', 'fenni mesul', 'müstakil konut',
                'mescit', 'spor salon', 'çocuk bahçe',
                'nüfus', 'yapı yoğunluğu', 'kat adedi',
                'erişilebilirlik', 'engelli tuvalet', 'yaya kaldırım',
                'ticaret yapıl', 'karma kullanım',
            ]
            building_terms_en = [
                'floor height', 'ceiling height', 'building height',
                'room dimension', 'stairwell', 'basement',
                'residential', 'bedroom', 'kitchen', 'bathroom',
            ]
            building_terms = building_terms_tr if language == 'turkish' else building_terms_en
            if any(term in context_lower for term in building_terms):
                return None

            # Parse value/range
            value, min_val, max_val, is_range = self._parse_value(groups)

            # Validate values
            if not self._validate_value(value, min_val, max_val, groups.get('unit', 'metre')):
                return None

            # Normalize unit
            unit = self._normalize_unit(groups.get('unit', ''), language)

            # Convert km to metres
            if unit == 'kilometre':
                if value:
                    value *= 1000
                if min_val:
                    min_val *= 1000
                if max_val:
                    max_val *= 1000
                unit = 'metre'

            # Parse qualifier
            qualifier = self._parse_qualifier(groups.get('qualifier', ''), language)

            # Identify activity
            activity, activity_conf = self._identify_activity(context, language)

            # Identify reference point
            ref_type, ref_text = self._identify_reference_point(context, language)

            # Find page number
            page_num = self._find_page_number(match.start(), page_texts)

            # Calculate confidence
            confidence = self._calculate_confidence(
                marine_score, activity_conf, bool(ref_type), bool(qualifier)
            )

            return DistanceExtraction(
                activity=activity,
                value=value,
                min_value=min_val,
                max_value=max_val,
                unit=unit,
                qualifier=qualifier,
                reference_point=ref_text,
                reference_point_type=ref_type,
                context=context[:200],
                exact_text=match.group(0),
                page_number=page_num,
                confidence=confidence,
                activity_confidence=activity_conf,
                marine_relevance=marine_score,
                is_range=is_range,
                filter_status="passed",
                document_type=doc_type.value,
                language=language
            )

        except Exception as e:
            logger.warning(f"Error processing distance match: {e}")
            return None

    def _parse_value(self, groups: Dict) -> tuple:
        """Parse value or range from match groups"""
        value = None
        min_val = None
        max_val = None
        is_range = False

        if 'min' in groups and groups['min']:
            # Range
            min_val = float(groups['min'].replace(',', '.'))
            max_val = float(groups['max'].replace(',', '.'))
            is_range = True
        elif 'value' in groups and groups['value']:
            # Single value
            value = float(groups['value'].replace(',', '.'))

        return value, min_val, max_val, is_range

    def _validate_value(self, value: Optional[float], min_val: Optional[float],
                        max_val: Optional[float], unit: str) -> bool:
        """Validate extracted values"""
        # Reject unrealistic metre values
        if unit in ['metre', 'metrelik', 'mt', 'm', 'm.']:
            if value and value > 10000:
                logger.debug(f"Rejected unrealistic metre value: {value}m")
                return False
            if value and value > 1900:
                logger.debug(f"Rejected year-like metre value: {value}m")
                return False

        # Reject year-like values in ranges
        if min_val and min_val > 1900:
            logger.debug(f"Rejected: min value looks like year: {min_val}")
            return False
        if max_val and max_val > 1900:
            logger.debug(f"Rejected: max value looks like year: {max_val}")
            return False

        # Reject ranges where min >= max
        if min_val and max_val and min_val >= max_val:
            logger.debug(f"Rejected invalid range: {min_val}-{max_val}")
            return False

        return True

    def _normalize_unit(self, unit: str, language: str) -> str:
        """Normalize unit to standard form"""
        unit_lower = unit.lower()

        # Turkish units
        if 'metre' in unit_lower or 'mt' in unit_lower or unit_lower in ['m', 'm.']:
            return 'metre'
        if 'km' in unit_lower or 'kilometre' in unit_lower:
            return 'kilometre'
        if 'mil' in unit_lower or 'deniz' in unit_lower:
            return 'nautical_mile'

        # English units
        if 'meter' in unit_lower or unit_lower == 'm':
            return 'metre'
        if 'km' in unit_lower or 'kilometer' in unit_lower or 'kilometre' in unit_lower:
            return 'kilometre'
        if 'nm' in unit_lower or 'nmi' in unit_lower or 'nautical' in unit_lower:
            return 'nautical_mile'
        if 'mile' in unit_lower:
            return 'mile'

        return 'metre'  # default

    def _parse_qualifier(self, qualifier_text: str, language: str) -> Optional[str]:
        """Parse qualifier from text"""
        if not qualifier_text:
            return None

        qualifier_lower = qualifier_text.lower()

        # Turkish qualifiers
        if language == 'turkish':
            if 'en az' in qualifier_lower or 'asgari' in qualifier_lower:
                return 'minimum'
            if 'en fazla' in qualifier_lower or 'en çok' in qualifier_lower or 'azami' in qualifier_lower:
                return 'maximum'
            if 'fazla' in qualifier_lower or 'üzeri' in qualifier_lower:
                return 'greater_than'
            if 'az' in qualifier_lower or 'altında' in qualifier_lower:
                return 'less_than'

        # English qualifiers
        if 'minimum' in qualifier_lower or 'at least' in qualifier_lower:
            return 'minimum'
        if 'maximum' in qualifier_lower or 'up to' in qualifier_lower:
            return 'maximum'
        if 'approximately' in qualifier_lower or 'about' in qualifier_lower or 'around' in qualifier_lower:
            return 'approximately'

        return None

    def _calculate_confidence(self, marine_score: float, activity_conf: float,
                             has_reference: bool, has_qualifier: bool) -> float:
        """Calculate overall confidence score"""
        base_confidence = 0.7

        # Boost for marine relevance
        if marine_score > 0.3:
            base_confidence += 0.1
        if marine_score > 0.6:
            base_confidence += 0.1

        # Boost for activity identification
        if activity_conf > 0.4:
            base_confidence += 0.05

        # Boost for reference point
        if has_reference:
            base_confidence += 0.05

        return min(base_confidence, 1.0)
