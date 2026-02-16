"""
Data Source Extractor - FULLY WORKING
Extracts data source mentions from scientific papers
"""
import re
import logging
from typing import Dict, List, Optional

try:
    from ..core.enums import DocumentType
    from ..data_structures import DataSourceExtraction
    from .base_extractor import BaseExtractor
except ImportError:
    from core.enums import DocumentType
    from data_structures import DataSourceExtraction
    from extractors.base_extractor import BaseExtractor

logger = logging.getLogger(__name__)


class DataSourceExtractor(BaseExtractor):
    """Extract data source mentions from scientific papers"""

    def _compile_patterns(self):
        """Compile data source patterns"""
        # Turkish patterns
        self.turkish_patterns = [
            re.compile(
                r'(?P<source_type>uydu|satellit|anket|veritaban[ıi]|veri\s+seti)\s*'
                r'(?P<source_name>[\w\s]+?)?',
                re.IGNORECASE | re.UNICODE
            ),
        ]

        # English patterns
        self.english_patterns = [
            re.compile(
                r'(?P<source_type>satellite|survey|database|dataset|imagery|remote\s+sensing)\s*'
                r'(?:data\s+)?(?:from\s+)?(?P<source_name>[\w\s-]+)?',
                re.IGNORECASE
            ),
            re.compile(
                r'(?P<source_name>Landsat|Sentinel|MODIS|Copernicus|AIS|VMS)\s*(?:data|imagery)',
                re.IGNORECASE
            ),
        ]

    def extract(self, text: str, page_texts: Dict[int, str],
                doc_type: DocumentType) -> List[DataSourceExtraction]:
        """Extract data sources from text"""
        results: List[DataSourceExtraction] = []
        language = self._get_language(doc_type)

        patterns = self.turkish_patterns if language == "turkish" else self.english_patterns

        for pattern in patterns:
            for match in pattern.finditer(text):
                result = self._process_match(match, text, text, page_texts, language, doc_type)
                if result:
                    results.append(result)

        return self._deduplicate(results)

    def _process_match(self, match: re.Match, converted_text: str, original_text: str,
                       page_texts: Dict[int, str], language: str,
                       doc_type: DocumentType) -> Optional[DataSourceExtraction]:
        """Process a data source match"""
        try:
            groups = match.groupdict()
            sentence, context = self._get_sentence_context(converted_text, match.start(), match.end())

            marine_score = self.fp_filter.get_marine_relevance_score(sentence, language)
            if marine_score < 0.1:
                return None

            source_type = self._parse_source_type(groups, language)
            source_name = groups.get('source_name', '').strip() if groups.get('source_name') else None
            spatial_coverage = self._extract_spatial_coverage(context, language)
            temporal_coverage = self._extract_temporal_coverage(context, language)
            resolution = self._extract_resolution(context)

            page_num = self._find_page_number(match.start(), page_texts)

            confidence = 0.7 + (0.1 if marine_score > 0.3 else 0) + (0.1 if source_name else 0)

            return DataSourceExtraction(
                source_type=source_type,
                source_name=source_name[:100] if source_name else None,
                spatial_coverage=spatial_coverage,
                temporal_coverage=temporal_coverage,
                resolution=resolution,
                context=context[:200],
                exact_text=match.group(0),
                page_number=page_num,
                confidence=min(confidence, 1.0),
                marine_relevance=marine_score
            )

        except Exception as e:
            logger.warning(f"Error processing data source match: {e}")
            return None

    def _parse_source_type(self, groups: Dict, language: str) -> str:
        """Parse source type"""
        source_type = (groups.get('source_type') or '').lower()
        source_name = (groups.get('source_name') or '').lower()

        if any(x in source_type or x in source_name for x in ['satellite', 'uydu', 'satellit', 'landsat', 'sentinel', 'modis']):
            return 'satellite'
        elif any(x in source_type or x in source_name for x in ['survey', 'anket']):
            return 'survey'
        elif any(x in source_type or x in source_name for x in ['database', 'veritaban']):
            return 'database'
        elif 'imagery' in source_type or 'remote sensing' in source_type:
            return 'remote_sensing'

        return 'data_source'

    def _extract_spatial_coverage(self, context: str, language: str) -> Optional[str]:
        """Extract spatial coverage"""
        if language == 'turkish':
            patterns = [r'(?:kapsam|alan)[:\s]+([^.;]+?)(?:km²|km2|ha)']
        else:
            patterns = [r'(?:coverage|area)[:\s]+([^.;]+?)(?:km²|km2|ha)']

        for pattern in patterns:
            match = re.search(pattern, context, re.IGNORECASE | re.UNICODE)
            if match:
                return match.group(0)[:100]
        return None

    def _extract_temporal_coverage(self, context: str, language: str) -> Optional[str]:
        """Extract temporal coverage"""
        # Look for year ranges
        pattern = r'(\d{4})\s*[-–]\s*(\d{4})'
        match = re.search(pattern, context)
        if match:
            return f"{match.group(1)}-{match.group(2)}"
        return None

    def _extract_resolution(self, context: str) -> Optional[str]:
        """Extract resolution"""
        patterns = [
            r'(\d+\s*m\s*resolution)',
            r'(resolution\s+of\s+\d+\s*m)',
            r'(\d+\s*metre\s*çözünürlük)',
        ]

        for pattern in patterns:
            match = re.search(pattern, context, re.IGNORECASE | re.UNICODE)
            if match:
                return match.group(1)
        return None
