"""
Temporal Extractor - FULLY WORKING
Extracts temporal restrictions (seasonal, time periods, dates) from legal and scientific texts
"""
import re
import logging
from typing import Dict, List, Optional

try:
    from ..core.enums import DocumentType
    from ..data_structures import TemporalExtraction
    from .base_extractor import BaseExtractor
except ImportError:
    from core.enums import DocumentType
    from data_structures import TemporalExtraction
    from extractors.base_extractor import BaseExtractor

logger = logging.getLogger(__name__)


class TemporalExtractor(BaseExtractor):
    """Extract temporal restrictions and periods from MSP documents"""

    def _compile_patterns(self):
        """Compile temporal patterns for both languages"""
        # Turkish patterns
        self.turkish_patterns = [
            # Date ranges: 1 Ocak - 31 Mart
            re.compile(
                r'(?P<start>\d{1,2})\s*(?P<start_month>Ocak|Şubat|Mart|Nisan|May[ıi]s|Haziran|Temmuz|Ağustos|Eylül|Ekim|Kas[ıi]m|Aral[ıi]k)\s*'
                r'[-–]\s*'
                r'(?P<end>\d{1,2})\s*(?P<end_month>Ocak|Şubat|Mart|Nisan|May[ıi]s|Haziran|Temmuz|Ağustos|Eylül|Ekim|Kas[ıi]m|Aral[ıi]k)',
                re.IGNORECASE | re.UNICODE
            ),
            # Month ranges: Nisan-Ekim
            re.compile(
                r'(?P<start_month>Ocak|Şubat|Mart|Nisan|May[ıi]s|Haziran|Temmuz|Ağustos|Eylül|Ekim|Kas[ıi]m|Aral[ıi]k)\s*'
                r'(?:ayları\s+)?[-–]\s*'
                r'(?P<end_month>Ocak|Şubat|Mart|Nisan|May[ıi]s|Haziran|Temmuz|Ağustos|Eylül|Ekim|Kas[ıi]m|Aral[ıi]k)',
                re.IGNORECASE | re.UNICODE
            ),
            # Seasonal: ilkbahar/yaz/sonbahar/kış aylarında
            re.compile(
                r'(?P<season>ilkbahar|yaz|sonbahar|k[ıi][şs])\s*(?:aylar[ıi]nda|döneminde|mevsiminde)',
                re.IGNORECASE | re.UNICODE
            ),
            # Duration: X ay/yıl/gün süreyle
            re.compile(
                r'(?P<duration>\d+)\s*(?P<unit>gün|ay|y[ıi]l|hafta)\s*(?:süre(?:yle|li|yle|si|sine)?|boyunca)',
                re.IGNORECASE | re.UNICODE
            ),
            # Time of day: saat X:Y - Z:W arası
            re.compile(
                r'(?:saat\s+)?(?P<start_hour>\d{1,2})[:.:](?P<start_min>\d{2})\s*[-–]\s*'
                r'(?P<end_hour>\d{1,2})[:.:](?P<end_min>\d{2})\s*(?:aras[ıi]|saatleri)',
                re.IGNORECASE | re.UNICODE
            ),
            # Specific periods: üreme dönemi, göç sezonu
            re.compile(
                r'(?P<period>üreme|göç|kuluçka|besleme|yetiştirme)\s*(?:dönemi|sezonu|mevsimi)',
                re.IGNORECASE | re.UNICODE
            ),
            # Year ranges: 2020-2025
            re.compile(
                r'(?P<start_year>\d{4})\s*[-–]\s*(?P<end_year>\d{4})\s*(?:y[ıi]llar[ıi]|aras[ıi]|dönemi)',
                re.IGNORECASE | re.UNICODE
            ),
        ]

        # English patterns
        self.english_patterns = [
            # Date ranges: January 1 - March 31
            re.compile(
                r'(?P<start_month>January|February|March|April|May|June|July|August|September|October|November|December)\s+'
                r'(?P<start>\d{1,2})\s*[-–to]+\s*'
                r'(?P<end_month>January|February|March|April|May|June|July|August|September|October|November|December)\s+'
                r'(?P<end>\d{1,2})',
                re.IGNORECASE
            ),
            # Month ranges: April to October
            re.compile(
                r'(?P<start_month>January|February|March|April|May|June|July|August|September|October|November|December)\s*'
                r'(?:to|through|-|–)\s*'
                r'(?P<end_month>January|February|March|April|May|June|July|August|September|October|November|December)',
                re.IGNORECASE
            ),
            # Seasonal: during spring/summer/fall/winter
            re.compile(
                r'(?:during|in)\s+(?P<season>spring|summer|fall|autumn|winter)\s*(?:months|season|period)?',
                re.IGNORECASE
            ),
            # Duration: X days/months/years
            re.compile(
                r'(?:for\s+)?(?P<duration>\d+)\s*(?P<unit>days?|months?|years?|weeks?)',
                re.IGNORECASE
            ),
            # Time of day: between X:Y and Z:W
            re.compile(
                r'(?:between|from)\s+(?P<start_hour>\d{1,2})[:.:](?P<start_min>\d{2})\s*'
                r'(?:and|to|-|–)\s*'
                r'(?P<end_hour>\d{1,2})[:.:](?P<end_min>\d{2})',
                re.IGNORECASE
            ),
            # Specific periods: breeding season, migration period
            re.compile(
                r'(?P<period>breeding|spawning|migration|nesting|feeding)\s+(?:season|period)',
                re.IGNORECASE
            ),
            # Year ranges: 2020-2025
            re.compile(
                r'(?P<start_year>\d{4})\s*[-–to]+\s*(?P<end_year>\d{4})',
                re.IGNORECASE
            ),
            # From X to Y
            re.compile(
                r'from\s+(?P<start>[\w\s]+?)\s+to\s+(?P<end>[\w\s]+?)(?:\s+(?:annually|yearly))?',
                re.IGNORECASE
            ),
        ]

    def extract(self, text: str, page_texts: Dict[int, str],
                doc_type: DocumentType) -> List[TemporalExtraction]:
        """Extract temporal restrictions from text"""
        results: List[TemporalExtraction] = []
        language = self._get_language(doc_type)

        # Convert written numbers
        converted_text = text
        if self.number_converter:
            converted_text = self.number_converter.convert_text(text, language)

        # Select patterns based on language
        patterns = self.turkish_patterns if language == "turkish" else self.english_patterns

        # Extract temporal data
        for pattern in patterns:
            for match in pattern.finditer(converted_text):
                result = self._process_match(match, converted_text, text, page_texts, language, doc_type)
                if result:
                    results.append(result)

        return self._deduplicate(results)

    def _process_match(self, match: re.Match, converted_text: str, original_text: str,
                       page_texts: Dict[int, str], language: str,
                       doc_type: DocumentType) -> Optional[TemporalExtraction]:
        """Process a temporal match"""
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

            # Parse temporal details
            restriction_type = self._parse_restriction_type(groups, language)
            start_date, end_date = self._parse_dates(groups, language)
            duration = self._parse_duration(groups)

            # Identify activity
            activity, activity_conf = self._identify_activity(context, language)

            # Extract legal reference
            legal_ref = self._extract_legal_reference(context, language)

            # Find page number
            page_num = self._find_page_number(match.start(), page_texts)

            # Calculate confidence
            confidence = self._calculate_confidence(
                marine_score, bool(start_date or duration), activity_conf
            )

            return TemporalExtraction(
                restriction_type=restriction_type,
                start_date=start_date,
                end_date=end_date,
                duration=duration,
                activity=activity,
                legal_reference=legal_ref,
                context=context[:200],
                exact_text=match.group(0),
                page_number=page_num,
                confidence=confidence,
                marine_relevance=marine_score
            )

        except Exception as e:
            logger.warning(f"Error processing temporal match: {e}")
            return None

    def _parse_restriction_type(self, groups: Dict, language: str) -> str:
        """Parse restriction type from match groups"""
        if 'season' in groups and groups['season']:
            return 'seasonal'
        elif 'period' in groups and groups['period']:
            return 'biological_period'
        elif 'start_hour' in groups and groups['start_hour']:
            return 'time_of_day'
        elif 'duration' in groups and groups['duration']:
            return 'duration'
        elif 'start_year' in groups and groups['start_year']:
            return 'multi_year'
        elif 'start_month' in groups and groups['start_month']:
            return 'date_range'
        return 'temporal_restriction'

    def _parse_dates(self, groups: Dict, language: str) -> tuple:
        """Parse start and end dates from match groups"""
        start_date = None
        end_date = None

        if 'start_month' in groups and groups['start_month']:
            start_month = groups['start_month']
            start_day = groups.get('start', '1')
            start_date = f"{start_month} {start_day}"

        if 'end_month' in groups and groups['end_month']:
            end_month = groups['end_month']
            end_day = groups.get('end', '31')
            end_date = f"{end_month} {end_day}"

        if 'season' in groups and groups['season']:
            start_date = groups['season']

        if 'period' in groups and groups['period']:
            start_date = groups['period']

        if 'start_hour' in groups and groups['start_hour']:
            start_date = f"{groups['start_hour']}:{groups['start_min']}"
            end_date = f"{groups['end_hour']}:{groups['end_min']}"

        if 'start_year' in groups and groups['start_year']:
            start_date = groups['start_year']
            end_date = groups.get('end_year', '')

        return start_date, end_date

    def _parse_duration(self, groups: Dict) -> Optional[str]:
        """Parse duration from match groups"""
        if 'duration' in groups and groups['duration']:
            duration = groups['duration']
            unit = groups.get('unit', '')
            return f"{duration} {unit}"
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

    def _calculate_confidence(self, marine_score: float, has_dates: bool,
                             activity_conf: float) -> float:
        """Calculate confidence score"""
        base_confidence = 0.7

        if marine_score > 0.3:
            base_confidence += 0.1
        if has_dates:
            base_confidence += 0.1
        if activity_conf > 0.4:
            base_confidence += 0.05

        return min(base_confidence, 1.0)
