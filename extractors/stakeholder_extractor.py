"""
Stakeholder Extractor - FULLY WORKING
Extracts stakeholder mentions (institutions, communities, organizations)
"""
import re
import logging
from typing import Dict, List, Optional

try:
    from ..core.enums import DocumentType
    from ..data_structures import StakeholderExtraction
    from .base_extractor import BaseExtractor
except ImportError:
    from core.enums import DocumentType
    from data_structures import StakeholderExtraction
    from extractors.base_extractor import BaseExtractor

logger = logging.getLogger(__name__)


class StakeholderExtractor(BaseExtractor):
    """Extract stakeholder mentions from MSP documents"""

    # Filter out non-stakeholder matches
    NAME_BLACKLIST = {
        'the', 'this', 'that', 'these', 'those', 'which', 'where',
        'marine', 'ocean', 'coastal', 'spatial', 'planning',
        'figure', 'table', 'section', 'chapter', 'results',
        'contents', 'available', 'journal', 'elsevier', 'springer',
        'copyright', 'published', 'abstract', 'introduction',
        'however', 'although', 'furthermore', 'moreover',
        'twin delayed', 'deep deterministic', 'reinforcement',
        'neural', 'path', 'reward', 'actor', 'learning',
        # Common false-positive words before org type keywords
        'federal', 'biodiversity', 'transition', 'agriculture',
        'aquaculture', 'energy', 'cahiers', 'options',
        'established', 'establishing', 'promote', 'sector',
    }

    def _compile_patterns(self):
        """Compile stakeholder patterns for both languages"""
        # Turkish patterns
        self.turkish_patterns = [
            # Organizations
            re.compile(
                r'(?P<name>[A-ZÇĞIÖŞÜ][\wçğıöşü\s]+?)\s*'
                r'(?P<type>Bakanlı[ğg][ıi]|Müdürlü[ğg]ü|Başkanlı[ğg][ıi]|Kurumu|Vakf[ıi]|Derne[ğg]i|Birli[ğg]i)',
                re.UNICODE
            ),
            # Communities
            re.compile(
                r'(?P<name>[\w\s]+?)\s*'
                r'(?P<type>toplulu[ğg]u|yerel\s+halk|bal[ıi]kç[ıi]lar|yerel\s+topluluk)',
                re.IGNORECASE | re.UNICODE
            ),
            # Stakeholder roles
            re.compile(
                r'(?P<role>paydaş|paydaşlar|ilgili\s+taraflar|yerel\s+topluluk)',
                re.IGNORECASE | re.UNICODE
            ),
        ]

        # English patterns - strict to avoid garbage captures
        self.english_patterns = [
            # Organizations - ALL words must start with capital letter (proper noun phrase)
            re.compile(
                r'(?P<name>[A-Z][A-Za-z]+(?:\s+(?:of|and|for|the)\s+)?'
                r'(?:[A-Z][A-Za-z]+)(?:\s+(?:of|and|for|the)\s+[A-Z]?[A-Za-z]+){0,3})\s+'
                r'(?P<type>Ministry|Department|Agency|Authority|Institute|Foundation|Association|Organization)',
                re.UNICODE
            ),
            # Specific stakeholder group patterns
            re.compile(
                r'(?P<role>local\s+(?:community|communities|fishers?|fishermen)|'
                r'fishing\s+(?:community|communities|industry)|'
                r'coastal\s+(?:community|communities)|'
                r'indigenous\s+(?:community|communities|peoples?)|'
                r'tourism\s+(?:industry|sector|operators?)|'
                r'shipping\s+(?:industry|sector|companies)|'
                r'oil\s+and\s+gas\s+(?:industry|sector|companies)|'
                r'offshore\s+(?:wind|energy)\s+(?:industry|sector|developers?)|'
                r'environmental\s+(?:NGOs?|organizations?)|'
                r'conservation\s+(?:NGOs?|organizations?)|'
                r'government\s+(?:agencies|authorities|bodies)|'
                r'port\s+authorities|'
                r'maritime\s+(?:industry|sector|authorities)|'
                r'aquaculture\s+(?:industry|sector|farmers?)|'
                r'recreational\s+(?:users?|fishers?|boaters?))',
                re.IGNORECASE
            ),
            # REMOVED: Generic "stakeholders" pattern - too many false positives
            # Only capture specific stakeholder groups, not the generic word
        ]

    def extract(self, text: str, page_texts: Dict[int, str],
                doc_type: DocumentType) -> List[StakeholderExtraction]:
        """Extract stakeholders from text"""
        results: List[StakeholderExtraction] = []
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
                       doc_type: DocumentType) -> Optional[StakeholderExtraction]:
        """Process a stakeholder match"""
        try:

            # Skip bibliography and garbled text
            if self._should_skip_match(converted_text, match.start(), match.group(0), category="stakeholder"):
                return None
            groups = match.groupdict()
            sentence, context = self._get_sentence_context(converted_text, match.start(), match.end())

            is_fp, fp_reason = self._is_false_positive(sentence, match.group(0), language)
            if is_fp:
                return None

            marine_score = self.fp_filter.get_marine_relevance_score(sentence, language)
            if marine_score < 0.05:
                return None

            stakeholder_name = (groups.get('name') or '').strip() if groups.get('name') else (groups.get('role') or '').strip()

            # Reject names containing newlines (cross-line captures)
            if '\n' in stakeholder_name or '\r' in stakeholder_name:
                return None

            # Filter out too-short, too-long, or blacklisted names
            if stakeholder_name:
                name_lower = stakeholder_name.lower().strip()
                if len(stakeholder_name) < 3 or len(stakeholder_name) > 150:
                    return None
                if any(bl in name_lower for bl in self.NAME_BLACKLIST):
                    return None
                # Filter out names that are just numbers or have more than 50% digits
                digit_count = sum(c.isdigit() for c in stakeholder_name)
                if digit_count > len(stakeholder_name) * 0.3:
                    return None

            stakeholder_type = self._parse_stakeholder_type(groups, language)
            role = self._extract_role(context, language)
            responsibilities = self._extract_responsibilities(context, language)

            legal_ref = self._extract_legal_reference(context, language)
            page_num = self._find_page_number(match.start(), page_texts)

            confidence = 0.7 + (0.1 if marine_score > 0.3 else 0) + (0.1 if role else 0)

            return StakeholderExtraction(
                stakeholder_name=stakeholder_name[:200],
                stakeholder_type=stakeholder_type,
                role=role,
                responsibilities=responsibilities,
                legal_reference=legal_ref,
                context=context[:200],
                exact_text=match.group(0),
                page_number=page_num,
                confidence=min(confidence, 1.0),
                marine_relevance=marine_score
            )

        except Exception as e:
            logger.warning(f"Error processing stakeholder match: {e}")
            return None

    def _parse_stakeholder_type(self, groups: Dict, language: str) -> Optional[str]:
        """Parse stakeholder type"""
        type_text = (groups.get('type') or '').lower()

        if language == 'turkish':
            if 'bakanlı' in type_text:
                return 'government'
            elif any(x in type_text for x in ['vakıf', 'dernek']):
                return 'ngo'
            elif 'balıkçı' in type_text or 'topluluk' in type_text:
                return 'community'
        else:
            if any(x in type_text for x in ['ministry', 'department', 'agency']):
                return 'government'
            elif any(x in type_text for x in ['foundation', 'association', 'organization']):
                return 'ngo'
            elif 'community' in type_text or 'fisher' in type_text:
                return 'community'

        return 'stakeholder'

    def _extract_role(self, context: str, language: str) -> Optional[str]:
        """Extract role from context"""
        if language == 'turkish':
            patterns = [r'(?:rolü|görev)[:\s]+([^.;]+)', r'sorumlu\s+([^.;]+)']
        else:
            patterns = [r'(?:role|responsibility)[:\s]+([^.;]+)', r'responsible\s+for\s+([^.;]+)']

        for pattern in patterns:
            match = re.search(pattern, context, re.IGNORECASE | re.UNICODE)
            if match:
                return match.group(1).strip()[:100]
        return None

    def _extract_responsibilities(self, context: str, language: str) -> List[str]:
        """Extract responsibilities"""
        responsibilities = []
        if language == 'turkish':
            patterns = [r'sorumluluk[:\s]+([^.;]+)', r'yükümlülük[:\s]+([^.;]+)']
        else:
            patterns = [r'responsibilit(?:y|ies)[:\s]+([^.;]+)', r'duties[:\s]+([^.;]+)']

        for pattern in patterns:
            matches = re.finditer(pattern, context, re.IGNORECASE | re.UNICODE)
            for match in matches:
                resp = match.group(1).strip()
                if resp and len(resp) < 100:
                    responsibilities.append(resp)
        return responsibilities[:3]

    def _extract_legal_reference(self, context: str, language: str) -> Optional[str]:
        """Extract legal reference"""
        if language == 'turkish':
            pattern = r'\d+\s*sayılı\s*(?:kanun|yönetmelik|tüzük)'
        else:
            pattern = r'(?:Act|Law|Regulation)\s+(?:No\.\s*)?\d+'

        match = re.search(pattern, context, re.IGNORECASE | re.UNICODE)
        return match.group(0) if match else None
