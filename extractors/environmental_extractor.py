"""
Environmental Extractor - Extracts environmental conditions, parameters, and requirements
Fixed: added broader patterns for qualitative environmental mentions
"""
import re
import logging
from typing import Dict, List, Optional

try:
    from ..core.enums import DocumentType
    from ..data_structures import EnvironmentalExtraction
    from .base_extractor import BaseExtractor
except ImportError:
    from core.enums import DocumentType
    from data_structures import EnvironmentalExtraction
    from extractors.base_extractor import BaseExtractor

logger = logging.getLogger(__name__)


class EnvironmentalExtractor(BaseExtractor):
    """Extract environmental conditions and requirements from MSP documents"""

    def _compile_patterns(self):
        """Compile environmental patterns for both languages"""
        # Turkish patterns
        self.turkish_patterns = [
            # Water quality with numeric values
            re.compile(
                r'(?P<parameter>pH|tuzluluk|çözünmüş\s*oksijen|sıcaklık|bulanıklık|klorofil)\s*'
                r'(?:değeri|seviyesi|oranı)?\s*'
                r'(?P<threshold>en\s+az|en\s+fazla|maksimum|minimum)?\s*'
                r'(?P<value>\d+(?:[.,]\d+)?)\s*'
                r'(?P<unit>mg/L|ppm|ppt|°C|derece|NTU)?',
                re.IGNORECASE | re.UNICODE
            ),
            # Qualitative environmental requirements (Turkish)
            re.compile(
                r'(?P<parameter>su\s*kalitesi|hava\s*kalitesi|çevre\s*kirliliği|deniz\s*kirliliği|'
                r'atık\s*su|gürültü\s*kirliliği|toprak\s*kirliliği)\s+'
                r'(?P<type>[^.;]{5,80})',
                re.IGNORECASE | re.UNICODE
            ),
            # Environmental impact (Turkish)
            re.compile(
                r'(?:çevresel\s+etki|ÇED)\s+(?P<type>[^.;]{5,80})',
                re.IGNORECASE | re.UNICODE
            ),
            # Pollution limits with units
            re.compile(
                r'(?P<value>\d+(?:[.,]\d+)?)\s*'
                r'(?P<unit>mg/L|ppm|ppb|µg/L)\s*'
                r'(?P<pollutant>nitrat|fosfat|amonyak|ağır\s*metal|petrol|hidrokarbon)',
                re.IGNORECASE | re.UNICODE
            ),
        ]

        # English patterns
        self.english_patterns = [
            # Water quality parameters with values
            re.compile(
                r'(?P<parameter>pH|salinity|dissolved\s+oxygen|temperature|turbidity|chlorophyll)\s*'
                r'(?:level|value)?\s*'
                r'(?:of\s+)?(?P<threshold>maximum|minimum|at\s+least|up\s+to)?\s*'
                r'(?P<value>\d+(?:[.,]\d+)?)\s*'
                r'(?P<unit>mg/L|ppm|ppt|°C|degrees?|NTU)?',
                re.IGNORECASE
            ),
            # Qualitative environmental mentions (broader)
            re.compile(
                r'(?P<parameter>water\s+quality|air\s+quality|noise\s+pollution|'
                r'marine\s+pollution|oil\s+spill|eutrophication|ocean\s+acidification|'
                r'habitat\s+degradation|biodiversity\s+loss|underwater\s+noise)\s+'
                r'(?P<type>[^.;]{5,80})',
                re.IGNORECASE
            ),
            # Environmental impact assessment
            re.compile(
                r'(?:environmental\s+impact\s+assessment|EIA|cumulative\s+(?:impact|effect)s?)\s+'
                r'(?P<type>[^.;]{5,80})',
                re.IGNORECASE
            ),
            # Pollution with values
            re.compile(
                r'(?P<value>\d+(?:[.,]\d+)?)\s*'
                r'(?P<unit>mg/L|ppm|ppb|µg/L)\s*'
                r'(?:of\s+)?(?P<pollutant>nitrate|phosphate|ammonia|heavy\s+metals?|petroleum|hydrocarbons?)',
                re.IGNORECASE
            ),
            # Noise limits
            re.compile(
                r'(?P<value>\d+(?:[.,]\d+)?)\s*'
                r'(?P<unit>dB|decibels?)\s*'
                r'(?P<type>noise|sound\s+level|acoustic)',
                re.IGNORECASE
            ),
            # Concentration levels
            re.compile(
                r'(?P<pollutant>nitrogen|phosphorus|BOD|COD|DO|SST)\s+(?:concentration|level)\s*'
                r'(?:of\s+)?(?P<value>\d+(?:[.,]\d+)?)\s*'
                r'(?P<unit>mg/L|ppm)',
                re.IGNORECASE
            ),
            # Threshold statements
            re.compile(
                r'(?P<parameter>water\s+quality|pollution|emission|discharge)\s*'
                r'(?:must\s+not\s+exceed|shall\s+not\s+exceed|maximum\s+of)\s*'
                r'(?P<value>\d+(?:[.,]\d+)?)\s*'
                r'(?P<unit>mg/L|ppm|%)',
                re.IGNORECASE
            ),
        ]

    def extract(self, text: str, page_texts: Dict[int, str],
                doc_type: DocumentType) -> List[EnvironmentalExtraction]:
        """Extract environmental conditions from text"""
        results: List[EnvironmentalExtraction] = []
        language = self._get_language(doc_type)

        converted_text = text
        if self.number_converter:
            converted_text = self.number_converter.convert_text(text, language)

        patterns = self.turkish_patterns if language == "turkish" else self.english_patterns

        for pattern in patterns:
            for match in pattern.finditer(converted_text):
                result = self._process_match(match, converted_text, text, page_texts, language, doc_type)
                if result:
                    results.append(result)

        return self._deduplicate(results)

    def _process_match(self, match: re.Match, converted_text: str, original_text: str,
                       page_texts: Dict[int, str], language: str,
                       doc_type: DocumentType) -> Optional[EnvironmentalExtraction]:
        """Process an environmental match"""
        try:
            groups = match.groupdict()
            sentence, context = self._get_sentence_context(converted_text, match.start(), match.end())

            cleaned_sentence = sentence
            if self.legal_ref_filter:
                cleaned_sentence = self.legal_ref_filter.clean_text(sentence)
                if match.group(0) not in cleaned_sentence:
                    return None

            is_fp, fp_reason = self._is_false_positive(cleaned_sentence, match.group(0), language)
            if is_fp:
                return None

            marine_score = self.fp_filter.get_marine_relevance_score(cleaned_sentence, language)
            min_marine_score = 0.05 if doc_type in [DocumentType.LEGAL_TURKISH, DocumentType.LEGAL_ENGLISH] else 0.1

            if marine_score < min_marine_score:
                return None

            condition_type = self._parse_condition_type(groups, language)
            description = self._build_description(groups, language)
            value = self._parse_value(groups)
            unit = (groups.get('unit') or '')
            threshold_type = self._parse_threshold_type(groups, language)

            legal_ref = self._extract_legal_reference(context, language)
            page_num = self._find_page_number(match.start(), page_texts)

            confidence = self._calculate_confidence(marine_score, bool(value), bool(unit))

            return EnvironmentalExtraction(
                condition_type=condition_type,
                description=description,
                value=value,
                unit=unit,
                threshold_type=threshold_type,
                legal_reference=legal_ref,
                context=context[:200],
                exact_text=match.group(0),
                page_number=page_num,
                confidence=confidence,
                marine_relevance=marine_score
            )

        except Exception as e:
            logger.warning(f"Error processing environmental match: {e}")
            return None

    def _parse_condition_type(self, groups: Dict, language: str) -> str:
        parameter = (groups.get('parameter') or '').lower()
        pollutant = (groups.get('pollutant') or '').lower()
        type_text = (groups.get('type') or '').lower()

        if 'ph' in parameter:
            return 'water_quality_ph'
        elif any(x in parameter or x in pollutant for x in ['oxygen', 'oksijen', 'do']):
            return 'water_quality_oxygen'
        elif any(x in parameter or x in pollutant for x in ['salinity', 'tuzluluk']):
            return 'water_quality_salinity'
        elif any(x in parameter for x in ['water quality', 'su kalitesi']):
            return 'water_quality'
        elif any(x in parameter or x in pollutant for x in ['nitrogen', 'nitrat', 'phosph', 'fosfat', 'eutrophication']):
            return 'pollution_nutrients'
        elif any(x in parameter or x in pollutant for x in ['metal', 'heavy']):
            return 'pollution_heavy_metals'
        elif any(x in parameter or x in pollutant for x in ['petroleum', 'petrol', 'oil', 'hydrocarbon', 'spill']):
            return 'pollution_petroleum'
        elif any(x in type_text or x in parameter for x in ['noise', 'gürültü', 'acoustic', 'akustik', 'underwater noise']):
            return 'noise'
        elif any(x in parameter for x in ['emission', 'emisyon', 'discharge', 'deşarj']):
            return 'emission'
        elif any(x in parameter or x in type_text for x in ['impact', 'etki', 'eia', 'ced', 'cumulative']):
            return 'environmental_impact'
        elif any(x in parameter for x in ['habitat', 'biodiversity']):
            return 'habitat_condition'
        elif any(x in parameter for x in ['pollution', 'kirlilik']):
            return 'pollution'
        return 'environmental_condition'

    def _build_description(self, groups: Dict, language: str) -> str:
        parts = []
        for key in ['parameter', 'pollutant', 'type', 'threshold']:
            if key in groups and groups[key]:
                parts.append(groups[key].strip())
        return ' '.join(parts) if parts else 'environmental condition'

    def _parse_value(self, groups: Dict) -> Optional[float]:
        if 'value' in groups and groups['value']:
            try:
                return float(groups['value'].replace(',', '.'))
            except ValueError:
                return None
        return None

    def _parse_threshold_type(self, groups: Dict, language: str) -> Optional[str]:
        threshold = (groups.get('threshold') or '').lower()
        if language == 'turkish':
            if 'en az' in threshold or 'minimum' in threshold:
                return 'minimum'
            elif 'en fazla' in threshold or 'maksimum' in threshold:
                return 'maximum'
            elif 'aşamaz' in threshold or 'geçemez' in threshold:
                return 'maximum'
        else:
            if 'minimum' in threshold or 'at least' in threshold:
                return 'minimum'
            elif 'maximum' in threshold or 'up to' in threshold or 'not exceed' in threshold:
                return 'maximum'
        return None

    def _extract_legal_reference(self, context: str, language: str) -> Optional[str]:
        if language == 'turkish':
            pattern = r'\d+\s*sayılı\s*(?:kanun|yönetmelik|tüzük)'
        else:
            pattern = r'(?:Act|Law|Regulation)\s+(?:No\.\s*)?\d+'
        match = re.search(pattern, context, re.IGNORECASE | re.UNICODE)
        return match.group(0) if match else None

    def _calculate_confidence(self, marine_score: float, has_value: bool,
                             has_unit: bool) -> float:
        base_confidence = 0.7
        if marine_score > 0.3:
            base_confidence += 0.1
        if has_value:
            base_confidence += 0.1
        if has_unit:
            base_confidence += 0.05
        return min(base_confidence, 1.0)
