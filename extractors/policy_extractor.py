"""
Policy Extractor - FULLY WORKING
Extracts policy and regulation mentions
"""
import re
import logging
from typing import Dict, List, Optional

try:
    from ..core.enums import DocumentType
    from ..data_structures import PolicyExtraction
    from .base_extractor import BaseExtractor
except ImportError:
    from core.enums import DocumentType
    from data_structures import PolicyExtraction
    from extractors.base_extractor import BaseExtractor

logger = logging.getLogger(__name__)


class PolicyExtractor(BaseExtractor):
    """Extract policy mentions from MSP documents"""

    # Journal names, publisher boilerplate, and non-policy matches to filter out
    TITLE_BLACKLIST = {
        'marine', 'ocean', 'contents lists available at sciencedirect',
        'contents lists', 'journal', 'elsevier', 'springer', 'wiley',
        'sciencedirect', 'copyright', 'published by', 'all rights reserved',
        'twin delayed deep deterministic', 'deep deterministic',
        'reinforcement learning', 'neural network', 'path planning',
        'deep q', 'reward', 'actor critic', 'available at',
    }

    def _compile_patterns(self):
        """Compile policy patterns"""
        # Turkish patterns
        self.turkish_patterns = [
            re.compile(
                r'(?P<title>[A-ZÇĞIÖŞÜ][\wçğıöşü\s]+?)\s*'
                r'(?P<type>Politikas[ıi]|Yönetmeli[ğg]i|Direktifi|Strateji(?:si)?|Çerçeve(?:si)?)',
                re.UNICODE
            ),
        ]

        # English patterns
        self.english_patterns = [
            re.compile(
                r'(?P<title>[A-Z][\w\s]+?)\s+'
                r'(?P<type>Policy|Directive|Regulation|Strategy|Framework|Guideline)',
                re.UNICODE
            ),
        ]

    def extract(self, text: str, page_texts: Dict[int, str],
                doc_type: DocumentType) -> List[PolicyExtraction]:
        """Extract policies from text"""
        results: List[PolicyExtraction] = []
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
                       doc_type: DocumentType) -> Optional[PolicyExtraction]:
        """Process a policy match"""
        try:
            groups = match.groupdict()
            sentence, context = self._get_sentence_context(converted_text, match.start(), match.end())

            marine_score = self.fp_filter.get_marine_relevance_score(sentence, language)
            if marine_score < 0.05:
                return None

            policy_type = self._parse_policy_type(groups, language)
            title = (groups.get('title') or '').strip()

            # Filter out journal names, publisher boilerplate, and non-policy matches
            title_lower = title.lower().strip()
            if any(bl in title_lower for bl in self.TITLE_BLACKLIST):
                return None
            if len(title) < 3 or len(title) > 150:
                return None

            scope = self._extract_scope(context, language)
            objectives = self._extract_objectives(context, language)

            legal_ref = self._extract_legal_reference(context, language)
            page_num = self._find_page_number(match.start(), page_texts)

            confidence = 0.7 + (0.1 if marine_score > 0.3 else 0) + (0.1 if objectives else 0)

            return PolicyExtraction(
                policy_type=policy_type,
                title=title[:200] if title else None,
                scope=scope,
                objectives=objectives,
                legal_reference=legal_ref,
                context=context[:200],
                exact_text=match.group(0),
                page_number=page_num,
                confidence=min(confidence, 1.0),
                marine_relevance=marine_score
            )

        except Exception as e:
            logger.warning(f"Error processing policy match: {e}")
            return None

    def _parse_policy_type(self, groups: Dict, language: str) -> str:
        """Parse policy type"""
        type_text = (groups.get('type') or '').lower()

        if 'directive' in type_text or 'direktif' in type_text:
            return 'directive'
        elif 'regulation' in type_text or 'yönetmelik' in type_text:
            return 'regulation'
        elif 'strategy' in type_text or 'strateji' in type_text:
            return 'strategy'
        elif 'framework' in type_text or 'çerçeve' in type_text:
            return 'framework'
        elif 'guideline' in type_text:
            return 'guideline'
        elif 'policy' in type_text or 'politika' in type_text:
            return 'policy'

        return 'policy'

    def _extract_scope(self, context: str, language: str) -> Optional[str]:
        """Extract policy scope"""
        if language == 'turkish':
            patterns = [r'(?:kapsam|alan)[:\s]+([^.;]+)']
        else:
            patterns = [r'(?:scope|coverage)[:\s]+([^.;]+)']

        for pattern in patterns:
            match = re.search(pattern, context, re.IGNORECASE | re.UNICODE)
            if match:
                return match.group(1).strip()[:100]
        return None

    def _extract_objectives(self, context: str, language: str) -> List[str]:
        """Extract policy objectives"""
        objectives = []

        if language == 'turkish':
            patterns = [r'(?:amaç|hedef)[:\s]+([^.;]+)', r'(?:sağlamak|korumak|geliştirmek)']
        else:
            patterns = [r'(?:objective|goal|aim)[:\s]+([^.;]+)', r'(?:to\s+ensure|to\s+protect|to\s+promote)']

        for pattern in patterns:
            matches = re.finditer(pattern, context, re.IGNORECASE | re.UNICODE)
            for match in matches:
                obj = match.group(1).strip() if match.lastindex else match.group(0)
                if obj and len(obj) < 100:
                    objectives.append(obj)

        return objectives[:3]

    def _extract_legal_reference(self, context: str, language: str) -> Optional[str]:
        """Extract legal reference"""
        if language == 'turkish':
            pattern = r'\d+\s*sayılı\s*(?:kanun|yönetmelik|tüzük)'
        else:
            pattern = r'(?:Act|Law|Regulation)\s+(?:No\.\s*)?\d+'

        match = re.search(pattern, context, re.IGNORECASE | re.UNICODE)
        return match.group(0) if match else None
