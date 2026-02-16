"""
Permit Extractor - FULLY WORKING
Extracts permit and license requirements from legal texts
"""
import re
import logging
from typing import Dict, List, Optional

try:
    from ..core.enums import DocumentType
    from ..data_structures import PermitExtraction
    from .base_extractor import BaseExtractor
except ImportError:
    from core.enums import DocumentType
    from data_structures import PermitExtraction
    from extractors.base_extractor import BaseExtractor

logger = logging.getLogger(__name__)


class PermitExtractor(BaseExtractor):
    """Extract permit and license requirements from MSP documents"""

    def _compile_patterns(self):
        """Compile permit patterns for both languages"""
        # Turkish patterns
        self.turkish_patterns = [
            # License/permit required
            re.compile(
                r'(?P<permit_type>avc[ıi]l[ıi]k|bal[ıi]kç[ıi]l[ıi]k|inşaat|yapı|çevresel|'
                r'imar|tahsis|kullanım)\s*'
                r'(?P<permit>ruhsat[ıi]?|lisans[ıi]?|izin|belge)(?:si)?\s*'
                r'(?P<requirement>(?:al[ıi]nmal[ıi]|gerekir|zorunlu|şart))',
                re.IGNORECASE | re.UNICODE
            ),
            # Permit from authority
            re.compile(
                r'(?P<authority>[\w\s]+?(?:Bakanlı[ğg][ıi]|Müdürlü[ğg]ü|Başkanlı[ğg][ıi]))\s*'
                r'(?:ndan|nden|dan|den)?\s*'
                r'(?P<permit>ruhsat|lisans|izin|belge)\s+'
                r'(?:al[ıi]n(?:mal[ıi]|acak)|veril(?:ecek|meli))',
                re.IGNORECASE | re.UNICODE
            ),
            # Permission verb forms
            re.compile(
                r'(?P<requirement>izin\s+(?:verilir|al[ıi]n[ıi]r|gerekir))\s*'
                r'(?:olan\s+)?(?P<permit_type>faaliyetler|işlemler|çal[ıi][şs]malar)?',
                re.IGNORECASE | re.UNICODE
            ),
            # Validity period
            re.compile(
                r'(?P<permit>ruhsat|lisans|izin)\s*'
                r'(?:süresi|geçerlilik\s+süresi)\s*'
                r'(?P<validity>\d+\s+(?:y[ıi]l|ay|gün))',
                re.IGNORECASE | re.UNICODE
            ),
        ]

        # English patterns
        self.english_patterns = [
            # License/permit required
            re.compile(
                r'(?P<permit_type>fishing|hunting|construction|environmental|'
                r'development|aquaculture|marine)\s*'
                r'(?P<permit>license|permit|authorization|approval)\s*'
                r'(?:is\s+)?(?P<requirement>required|necessary|mandatory|shall\s+be\s+obtained)',
                re.IGNORECASE
            ),
            # Permit from authority
            re.compile(
                r'(?P<permit>permit|license|authorization)\s+from\s+'
                r'(?:the\s+)?(?P<authority>[\w\s]+?(?:Department|Agency|Ministry|Authority))',
                re.IGNORECASE
            ),
            # Must obtain permit
            re.compile(
                r'(?:must|shall|should)\s+(?:obtain|acquire|secure)\s+'
                r'(?:a\s+)?(?P<permit>permit|license|authorization)',
                re.IGNORECASE
            ),
            # Validity period
            re.compile(
                r'(?P<permit>permit|license)\s+(?:valid|validity)\s+(?:for|period)\s+'
                r'(?P<validity>\d+\s+(?:years?|months?|days?))',
                re.IGNORECASE
            ),
            # Requirements for permit
            re.compile(
                r'requirements?\s+for\s+(?:a\s+)?(?P<permit_type>[\w\s]+?)\s+'
                r'(?P<permit>permit|license)',
                re.IGNORECASE
            ),
        ]

    def extract(self, text: str, page_texts: Dict[int, str],
                doc_type: DocumentType) -> List[PermitExtraction]:
        """Extract permits from text"""
        results: List[PermitExtraction] = []
        language = self._get_language(doc_type)

        # Convert written numbers
        converted_text = text
        if self.number_converter:
            converted_text = self.number_converter.convert_text(text, language)

        # Select patterns based on language
        patterns = self.turkish_patterns if language == "turkish" else self.english_patterns

        # Extract permits
        for pattern in patterns:
            for match in pattern.finditer(converted_text):
                result = self._process_match(match, converted_text, text, page_texts, language, doc_type)
                if result:
                    results.append(result)

        return self._deduplicate(results)

    def _process_match(self, match: re.Match, converted_text: str, original_text: str,
                       page_texts: Dict[int, str], language: str,
                       doc_type: DocumentType) -> Optional[PermitExtraction]:
        """Process a permit match"""
        try:
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
            min_marine_score = 0.05 if doc_type in [DocumentType.LEGAL_TURKISH, DocumentType.LEGAL_ENGLISH] else 0.15

            if marine_score < min_marine_score:
                return None

            # Parse permit details
            permit_type = self._parse_permit_type(groups, context, language)
            issuing_authority = groups.get('authority', '').strip() if groups.get('authority') else None
            validity_period = groups.get('validity', '').strip() if groups.get('validity') else None

            # Extract requirements
            requirements = self._extract_requirements(context, language)

            # Identify activity
            activity, _ = self._identify_activity(context, language)

            # Extract legal reference
            legal_ref = self._extract_legal_reference(context, language)

            # Find page number
            page_num = self._find_page_number(match.start(), page_texts)

            # Calculate confidence
            confidence = self._calculate_confidence(
                marine_score, bool(permit_type), bool(issuing_authority)
            )

            return PermitExtraction(
                permit_type=permit_type,
                issuing_authority=issuing_authority,
                requirements=requirements,
                validity_period=validity_period,
                activity=activity,
                legal_reference=legal_ref,
                context=context[:200],
                exact_text=match.group(0),
                page_number=page_num,
                confidence=confidence,
                marine_relevance=marine_score
            )

        except Exception as e:
            logger.warning(f"Error processing permit match: {e}")
            return None

    def _parse_permit_type(self, groups: Dict, context: str, language: str) -> str:
        """Parse permit type from match groups"""
        permit_type = (groups.get('permit_type') or '').strip()
        permit = (groups.get('permit') or '').strip()

        if permit_type:
            return f"{permit_type}_{permit}" if permit else permit_type

        # Try to infer from context
        if language == 'turkish':
            if any(x in context.lower() for x in ['balık', 'avcı']):
                return 'fishing_license'
            elif any(x in context.lower() for x in ['inşaat', 'yapı']):
                return 'construction_permit'
            elif 'çevre' in context.lower():
                return 'environmental_approval'
        else:
            if 'fishing' in context.lower():
                return 'fishing_license'
            elif 'construction' in context.lower() or 'development' in context.lower():
                return 'construction_permit'
            elif 'environmental' in context.lower():
                return 'environmental_approval'

        return 'permit'

    def _extract_requirements(self, context: str, language: str) -> List[str]:
        """Extract permit requirements from context"""
        requirements = []

        if language == 'turkish':
            patterns = [
                r'(?:gerekli|şart|zorunlu)\s+olan\s+([^.;]+)',
                r'([^.;]+?)\s+(?:sunulmal[ıi]|ibraz\s+edilmeli)',
            ]
        else:
            patterns = [
                r'(?:required|necessary|must\s+provide)\s+([^.;]+)',
                r'(?:shall|must)\s+(?:submit|present|provide)\s+([^.;]+)',
            ]

        for pattern in patterns:
            matches = re.finditer(pattern, context, re.IGNORECASE | re.UNICODE)
            for match in matches:
                requirement = match.group(1).strip()
                if requirement and len(requirement) < 100:
                    requirements.append(requirement)

        return requirements[:5]  # Limit to 5 requirements

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

    def _calculate_confidence(self, marine_score: float, has_permit_type: bool,
                             has_authority: bool) -> float:
        """Calculate confidence score"""
        base_confidence = 0.7

        if marine_score > 0.3:
            base_confidence += 0.1
        if has_permit_type:
            base_confidence += 0.1
        if has_authority:
            base_confidence += 0.05

        return min(base_confidence, 1.0)
