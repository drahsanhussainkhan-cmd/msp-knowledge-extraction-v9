"""
Legal Reference Extractor - FULLY WORKING
Extracts legal references (law citations, article numbers)
"""
import re
import logging
from typing import Dict, List, Optional

try:
    from ..core.enums import DocumentType
    from ..data_structures import LegalReferenceExtraction
    from .base_extractor import BaseExtractor
except ImportError:
    from core.enums import DocumentType
    from data_structures import LegalReferenceExtraction
    from extractors.base_extractor import BaseExtractor

logger = logging.getLogger(__name__)


class LegalReferenceExtractor(BaseExtractor):
    """Extract legal references from MSP documents"""

    def _compile_patterns(self):
        """Compile legal reference patterns"""
        # Turkish patterns
        self.turkish_patterns = [
            # Law number: X sayılı kanun
            re.compile(
                r'(?P<law_number>\d+)\s*say[ıi]l[ıi]\s*'
                r'(?P<type>(?:kanun|yönetmelik|tüzük|tebli[ğg]))',
                re.IGNORECASE | re.UNICODE
            ),
            # Article: Madde X
            re.compile(
                r'(?:madde|md\.?)\s*(?P<article>\d+)',
                re.IGNORECASE | re.UNICODE
            ),
            # Combined: X sayılı kanunun Y maddesi
            re.compile(
                r'(?P<law_number>\d+)\s*say[ıi]l[ıi]\s*'
                r'(?P<type>kanun|yönetmelik)(?:un|ün)?\s*'
                r'(?P<article>\d+)\s*(?:inci|nci|üncü|uncu)?\s*maddesi',
                re.IGNORECASE | re.UNICODE
            ),
        ]

        # English patterns
        self.english_patterns = [
            # Act/Law with number
            re.compile(
                r'(?P<type>Act|Law|Regulation|Directive)\s+(?:No\.\s*)?(?P<law_number>\d+)',
                re.IGNORECASE
            ),
            # Article/Section
            re.compile(
                r'(?P<type>Article|Section)\s+(?P<article>\d+)',
                re.IGNORECASE
            ),
            # Combined: Article X of Law Y
            re.compile(
                r'(?:Article|Section)\s+(?P<article>\d+)\s+of\s+'
                r'(?:the\s+)?(?P<type>Act|Law|Regulation)\s+(?:No\.\s*)?(?P<law_number>\d+)',
                re.IGNORECASE
            ),
        ]

    def extract(self, text: str, page_texts: Dict[int, str],
                doc_type: DocumentType) -> List[LegalReferenceExtraction]:
        """Extract legal references from text"""
        results: List[LegalReferenceExtraction] = []
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
                       doc_type: DocumentType) -> Optional[LegalReferenceExtraction]:
        """Process a legal reference match"""
        try:

            # Skip bibliography and garbled text
            if self._should_skip_match(converted_text, match.start(), match.group(0), category="legal_reference"):
                return None
            groups = match.groupdict()
            sentence, context = self._get_sentence_context(converted_text, match.start(), match.end())

            marine_score = self.fp_filter.get_marine_relevance_score(sentence, language)
            if marine_score < 0.05:
                return None

            reference_type = self._parse_reference_type(groups, language)
            law_number = groups.get('law_number', '').strip() if groups.get('law_number') else None
            article_number = groups.get('article', '').strip() if groups.get('article') else None
            title = self._extract_title(context, language)
            date = self._extract_date(context)

            page_num = self._find_page_number(match.start(), page_texts)

            confidence = 0.8 + (0.1 if law_number else 0) + (0.05 if article_number else 0)

            return LegalReferenceExtraction(
                reference_type=reference_type,
                law_number=law_number,
                article_number=article_number,
                title=title,
                date=date,
                context=context[:200],
                exact_text=match.group(0),
                page_number=page_num,
                confidence=min(confidence, 1.0),
                marine_relevance=marine_score
            )

        except Exception as e:
            logger.warning(f"Error processing legal reference match: {e}")
            return None

    def _parse_reference_type(self, groups: Dict, language: str) -> str:
        """Parse reference type"""
        type_text = (groups.get('type') or '').lower()

        if language == 'turkish':
            if 'kanun' in type_text:
                return 'law'
            elif 'yönetmelik' in type_text:
                return 'regulation'
            elif 'tüzük' in type_text:
                return 'decree'
            elif 'tebliğ' in type_text:
                return 'directive'
            elif 'madde' in type_text or 'md' in type_text:
                return 'article'
        else:
            if 'act' in type_text or 'law' in type_text:
                return 'law'
            elif 'regulation' in type_text:
                return 'regulation'
            elif 'directive' in type_text:
                return 'directive'
            elif 'article' in type_text or 'section' in type_text:
                return 'article'

        return 'legal_reference'

    def _extract_title(self, context: str, language: str) -> Optional[str]:
        """Extract legal document title"""
        if language == 'turkish':
            # Look for quoted titles or titles with specific patterns
            patterns = [
                r'["\"]([^"\"]+)["\"]',
                r'([A-ZÇĞIÖŞÜ][\wçğıöşü\s]+?(?:Kanunu|Yönetmeliği|Tüzüğü))',
            ]
        else:
            patterns = [
                r'["\"]([^"\"]+)["\"]',
                r'([A-Z][\w\s]+?(?:Act|Law|Regulation))',
            ]

        for pattern in patterns:
            match = re.search(pattern, context, re.UNICODE)
            if match:
                title = match.group(1).strip()
                if len(title) > 10 and len(title) < 200:
                    return title
        return None

    def _extract_date(self, context: str) -> Optional[str]:
        """Extract date"""
        # Look for dates in various formats
        patterns = [
            r'(\d{1,2}[/.]\d{1,2}[/.]\d{4})',
            r'(\d{4})',
        ]

        for pattern in patterns:
            match = re.search(pattern, context)
            if match:
                return match.group(1)
        return None
