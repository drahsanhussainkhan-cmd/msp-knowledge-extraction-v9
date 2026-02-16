"""
Coordinate Extractor - FULLY WORKING
Extracts geographic coordinates (latitude/longitude) from legal and scientific texts
"""
import re
import logging
from typing import Dict, List, Optional

try:
    from ..core.enums import DocumentType
    from ..data_structures import CoordinateExtraction
    from .base_extractor import BaseExtractor
except ImportError:
    from core.enums import DocumentType
    from data_structures import CoordinateExtraction
    from extractors.base_extractor import BaseExtractor

logger = logging.getLogger(__name__)


class CoordinateExtractor(BaseExtractor):
    """Extract geographic coordinates from MSP documents"""

    def _compile_patterns(self):
        """Compile coordinate patterns for both languages"""
        # Decimal degrees: 41.0082° N, 28.9784° E
        decimal_pattern = re.compile(
            r'(?P<lat>\d{1,2}[.,]\d+)\s*[°º]?\s*(?P<lat_dir>[NS])\s*[,;]?\s*'
            r'(?P<lon>\d{1,3}[.,]\d+)\s*[°º]?\s*(?P<lon_dir>[EW])',
            re.IGNORECASE | re.UNICODE
        )

        # DMS format: 41°00'30"N, 28°58'42"E
        dms_pattern = re.compile(
            r'(?P<lat_deg>\d{1,2})[°º]\s*(?P<lat_min>\d{1,2})[\''']\s*(?P<lat_sec>\d{1,2}(?:[.,]\d+)?)?[""]?\s*(?P<lat_dir>[NS])\s*[,;]?\s*'
            r'(?P<lon_deg>\d{1,3})[°º]\s*(?P<lon_min>\d{1,2})[\''']\s*(?P<lon_sec>\d{1,2}(?:[.,]\d+)?)?[""]?\s*(?P<lon_dir>[EW])',
            re.IGNORECASE | re.UNICODE
        )

        # Simple decimal: 41.0082, 28.9784
        simple_decimal = re.compile(
            r'(?P<lat>-?\d{1,2}[.,]\d+)\s*[,;]\s*(?P<lon>-?\d{1,3}[.,]\d+)',
            re.UNICODE
        )

        # Both Turkish and English use same coordinate formats
        self.turkish_patterns = [decimal_pattern, dms_pattern, simple_decimal]
        self.english_patterns = [decimal_pattern, dms_pattern, simple_decimal]

    def extract(self, text: str, page_texts: Dict[int, str],
                doc_type: DocumentType) -> List[CoordinateExtraction]:
        """Extract coordinates from text"""
        results: List[CoordinateExtraction] = []
        language = self._get_language(doc_type)

        patterns = self.turkish_patterns if language == "turkish" else self.english_patterns

        # Extract coordinates
        for pattern in patterns:
            for match in pattern.finditer(text):
                result = self._process_match(match, text, text, page_texts, language, doc_type)
                if result:
                    results.append(result)

        return self._deduplicate(results)

    def _process_match(self, match: re.Match, converted_text: str, original_text: str,
                       page_texts: Dict[int, str], language: str,
                       doc_type: DocumentType) -> Optional[CoordinateExtraction]:
        """Process a coordinate match"""
        try:
            groups = match.groupdict()
            sentence, context = self._get_sentence_context(converted_text, match.start(), match.end())

            # False positive check
            is_fp, fp_reason = self._is_false_positive(sentence, match.group(0), language)
            if is_fp:
                return None

            # Check marine relevance
            marine_score = self.fp_filter.get_marine_relevance_score(sentence, language)
            min_marine_score = 0.05

            if marine_score < min_marine_score:
                return None

            # Parse coordinates
            latitude, longitude = self._parse_coordinates(groups)

            # Validate coordinates
            if not self._validate_coordinates(latitude, longitude):
                return None

            # Extract location description
            location_desc = self._extract_location_description(context, language)

            # Determine boundary type
            boundary_type = self._determine_boundary_type(context, language)

            # Extract legal reference
            legal_ref = self._extract_legal_reference(context, language)

            # Find page number
            page_num = self._find_page_number(match.start(), page_texts)

            # Calculate confidence
            confidence = self._calculate_confidence(
                marine_score, bool(location_desc), bool(boundary_type)
            )

            return CoordinateExtraction(
                latitude=latitude,
                longitude=longitude,
                coordinate_system="WGS84",
                location_description=location_desc,
                boundary_type=boundary_type,
                legal_reference=legal_ref,
                context=context[:200],
                exact_text=match.group(0),
                page_number=page_num,
                confidence=confidence,
                marine_relevance=marine_score
            )

        except Exception as e:
            logger.warning(f"Error processing coordinate match: {e}")
            return None

    def _parse_coordinates(self, groups: Dict) -> tuple:
        """Parse latitude and longitude from match groups"""
        # Decimal degrees
        if 'lat' in groups and groups['lat'] and 'lon' in groups and groups['lon']:
            lat = float(groups['lat'].replace(',', '.'))
            lon = float(groups['lon'].replace(',', '.'))

            # Apply direction
            if 'lat_dir' in groups and groups['lat_dir']:
                if groups['lat_dir'].upper() == 'S':
                    lat = -lat
            if 'lon_dir' in groups and groups['lon_dir']:
                if groups['lon_dir'].upper() == 'W':
                    lon = -lon

            return lat, lon

        # DMS format
        if 'lat_deg' in groups and groups['lat_deg']:
            lat_deg = float(groups['lat_deg'])
            lat_min = float(groups.get('lat_min', 0))
            lat_sec = float(groups.get('lat_sec', 0).replace(',', '.')) if groups.get('lat_sec') else 0
            lat = lat_deg + lat_min/60 + lat_sec/3600

            lon_deg = float(groups['lon_deg'])
            lon_min = float(groups.get('lon_min', 0))
            lon_sec = float(groups.get('lon_sec', 0).replace(',', '.')) if groups.get('lon_sec') else 0
            lon = lon_deg + lon_min/60 + lon_sec/3600

            # Apply direction
            if groups.get('lat_dir', '').upper() == 'S':
                lat = -lat
            if groups.get('lon_dir', '').upper() == 'W':
                lon = -lon

            return lat, lon

        return None, None

    def _validate_coordinates(self, lat: Optional[float], lon: Optional[float]) -> bool:
        """Validate coordinate values"""
        if lat is None or lon is None:
            return False

        # Latitude must be between -90 and 90
        if not (-90 <= lat <= 90):
            return False

        # Longitude must be between -180 and 180
        if not (-180 <= lon <= 180):
            return False

        return True

    def _extract_location_description(self, context: str, language: str) -> Optional[str]:
        """Extract location description from context"""
        if language == 'turkish':
            patterns = [
                r'(?:bölge|alan|konum|nokta|s[ıi]n[ıi]r)[\s:]+([^.;]{5,50})',
            ]
        else:
            patterns = [
                r'(?:area|zone|location|point|boundary)[\s:]+([^.;]{5,50})',
            ]

        for pattern in patterns:
            match = re.search(pattern, context, re.IGNORECASE | re.UNICODE)
            if match:
                return match.group(1).strip()

        return None

    def _determine_boundary_type(self, context: str, language: str) -> Optional[str]:
        """Determine boundary type from context"""
        context_lower = context.lower()

        if language == 'turkish':
            if 'köşe' in context_lower or 'nokta' in context_lower:
                return 'point'
            elif 'çizgi' in context_lower or 'hat' in context_lower:
                return 'line'
            elif 'alan' in context_lower or 'bölge' in context_lower or 'poligon' in context_lower:
                return 'polygon'
        else:
            if 'point' in context_lower or 'corner' in context_lower:
                return 'point'
            elif 'line' in context_lower or 'boundary line' in context_lower:
                return 'line'
            elif 'area' in context_lower or 'polygon' in context_lower or 'zone' in context_lower:
                return 'polygon'

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

    def _calculate_confidence(self, marine_score: float, has_location: bool,
                             has_boundary_type: bool) -> float:
        """Calculate confidence score"""
        base_confidence = 0.8  # Higher base for coordinates

        if marine_score > 0.3:
            base_confidence += 0.1
        if has_location:
            base_confidence += 0.05
        if has_boundary_type:
            base_confidence += 0.05

        return min(base_confidence, 1.0)
