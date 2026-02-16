"""
Institution Extractor - FULLY WORKING
Extracts government institutions and authorities
"""
import re
import logging
from typing import Dict, List, Optional

try:
    from ..core.enums import DocumentType
    from ..data_structures import InstitutionExtraction
    from .base_extractor import BaseExtractor
except ImportError:
    from core.enums import DocumentType
    from data_structures import InstitutionExtraction
    from extractors.base_extractor import BaseExtractor

logger = logging.getLogger(__name__)


class InstitutionExtractor(BaseExtractor):
    """Extract institution mentions from MSP documents"""

    def _compile_patterns(self):
        """Compile institution patterns"""
        # Turkish patterns
        self.turkish_patterns = [
            re.compile(
                r'(?P<name>[A-ZÇĞIÖŞÜ][\wçğıöşü\s]+?)\s*'
                r'(?P<type>Bakanlı[ğg][ıi]|Müdürlü[ğg]ü|Başkanlı[ğg][ıi]|Kurumu|Enstitüsü|Komitesi)',
                re.UNICODE
            ),
        ]

        # English patterns
        self.english_patterns = [
            re.compile(
                r'(?P<name>[A-Z][\w\s]+?)\s+'
                r'(?P<type>Ministry|Department|Agency|Authority|Institute|Committee|Commission)',
                re.UNICODE
            ),
        ]

    def extract(self, text: str, page_texts: Dict[int, str],
                doc_type: DocumentType) -> List[InstitutionExtraction]:
        """Extract institutions from text"""
        results: List[InstitutionExtraction] = []
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
                       doc_type: DocumentType) -> Optional[InstitutionExtraction]:
        """Process an institution match"""
        try:
            groups = match.groupdict()
            sentence, context = self._get_sentence_context(converted_text, match.start(), match.end())

            marine_score = self.fp_filter.get_marine_relevance_score(sentence, language)
            if marine_score < 0.05:
                return None

            institution_name = f"{groups['name']} {groups['type']}".strip()
            institution_type = self._parse_institution_type(groups, language)
            role = self._extract_role(context, language)
            jurisdiction = self._extract_jurisdiction(context, language)

            legal_ref = self._extract_legal_reference(context, language)
            page_num = self._find_page_number(match.start(), page_texts)

            confidence = 0.75 + (0.1 if marine_score > 0.3 else 0) + (0.1 if role else 0)

            return InstitutionExtraction(
                institution_name=institution_name[:200],
                institution_type=institution_type,
                role=role,
                jurisdiction=jurisdiction,
                legal_reference=legal_ref,
                context=context[:200],
                exact_text=match.group(0),
                page_number=page_num,
                confidence=min(confidence, 1.0),
                marine_relevance=marine_score
            )

        except Exception as e:
            logger.warning(f"Error processing institution match: {e}")
            return None

    def _parse_institution_type(self, groups: Dict, language: str) -> Optional[str]:
        """Parse institution type"""
        type_text = (groups.get('type') or '').lower()

        if language == 'turkish':
            if 'bakanlı' in type_text:
                return 'ministry'
            elif 'müdürlü' in type_text:
                return 'directorate'
            elif 'başkanlı' in type_text:
                return 'presidency'
            elif 'kurum' in type_text:
                return 'agency'
            elif 'enstitü' in type_text:
                return 'institute'
            elif 'komite' in type_text:
                return 'committee'
        else:
            if 'ministry' in type_text:
                return 'ministry'
            elif 'department' in type_text:
                return 'department'
            elif 'agency' in type_text or 'authority' in type_text:
                return 'agency'
            elif 'institute' in type_text:
                return 'institute'
            elif 'committee' in type_text or 'commission' in type_text:
                return 'committee'

        return None

    def _extract_role(self, context: str, language: str) -> Optional[str]:
        """Extract role"""
        if language == 'turkish':
            patterns = [r'(?:yetkili|sorumlu|görevli)[:\s]+([^.;]+)']
        else:
            patterns = [r'(?:responsible|authorized|in\s+charge)[:\s]+([^.;]+)']

        for pattern in patterns:
            match = re.search(pattern, context, re.IGNORECASE | re.UNICODE)
            if match:
                return match.group(1).strip()[:100]
        return None

    def _extract_jurisdiction(self, context: str, language: str) -> Optional[str]:
        """Extract jurisdiction"""
        if language == 'turkish':
            patterns = [r'(?:bölge|alan|yetkisi)[:\s]+([^.;]+)']
        else:
            patterns = [r'(?:jurisdiction|area\s+of\s+authority)[:\s]+([^.;]+)']

        for pattern in patterns:
            match = re.search(pattern, context, re.IGNORECASE | re.UNICODE)
            if match:
                return match.group(1).strip()[:100]
        return None

    def _extract_legal_reference(self, context: str, language: str) -> Optional[str]:
        """Extract legal reference"""
        if language == 'turkish':
            pattern = r'\d+\s*sayılı\s*(?:kanun|yönetmelik|tüzük)'
        else:
            pattern = r'(?:Act|Law|Regulation)\s+(?:No\.\s*)?\d+'

        match = re.search(pattern, context, re.IGNORECASE | re.UNICODE)
        return match.group(0) if match else None
