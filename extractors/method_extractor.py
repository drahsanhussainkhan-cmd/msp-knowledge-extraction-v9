"""
Method Extractor - FULLY WORKING
Extracts research methods from scientific papers
"""
import re
import logging
from typing import Dict, List, Optional

try:
    from ..core.enums import DocumentType
    from ..data_structures import MethodExtraction
    from .base_extractor import BaseExtractor
except ImportError:
    from core.enums import DocumentType
    from data_structures import MethodExtraction
    from extractors.base_extractor import BaseExtractor

logger = logging.getLogger(__name__)


class MethodExtractor(BaseExtractor):
    """Extract research methods from scientific papers"""

    def _compile_patterns(self):
        """Compile method patterns"""
        # Turkish patterns - require word boundaries
        self.turkish_patterns = [
            re.compile(
                r'\b(?P<method>anket\s+çalışması|röportaj|mülakat|modelleme\s+(?:yöntemi|çalışması)|'
                r'CBS\s*analiz[i]?|GIS\s*analiz[i]?|'
                r'saha\s+çal[ıi][şs]mas[ıi]|arazi\s+çal[ıi][şs]mas[ıi]|'
                r'paydaş\s+(?:toplantısı|görüşmesi|katılımı))\b',
                re.IGNORECASE | re.UNICODE
            ),
        ]

        # English patterns - require word boundaries and more specific context
        self.english_patterns = [
            # Methods only when preceded by methodological context words
            re.compile(
                r'(?:(?:using|through|via|conducted|performed|employed|applied|based\s+on|'
                r'carried\s+out|method(?:ology)?|approach|technique|framework)\s+(?:a\s+)?)'
                r'(?P<method>survey|interviews?|questionnaires?|'
                r'(?:spatial|GIS|statistical|numerical|ecosystem)\s+(?:analysis|modeling|modelling)|'
                r'field\s+(?:study|survey|work)|case\s+study|stakeholder\s+(?:consultation|engagement|workshop)|'
                r'remote\s+sensing|habitat\s+mapping|cost[\s-]benefit\s+analysis|'
                r'multi[\s-]criteria\s+(?:analysis|decision)|Delphi\s+(?:method|survey|process)|'
                r'scenario\s+(?:analysis|planning|building)|cumulative\s+(?:impact|effect)\s+assessment)',
                re.IGNORECASE
            ),
            # Specific named methodologies (don't need context)
            re.compile(
                r'\b(?P<method>Marxan|MaxEnt|InVEST|Zonation|MIMES|'
                r'SeaSketch|EBSA\s+assessment|EBM|ecosystem[\s-]based\s+management|'
                r'marine\s+cadastre|suitability\s+analysis|overlap\s+analysis|'
                r'participatory\s+(?:mapping|GIS|approach))\b',
                re.IGNORECASE
            ),
        ]

    def extract(self, text: str, page_texts: Dict[int, str],
                doc_type: DocumentType) -> List[MethodExtraction]:
        """Extract methods from text"""
        results: List[MethodExtraction] = []
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
                       doc_type: DocumentType) -> Optional[MethodExtraction]:
        """Process a method match"""
        try:

            # Skip bibliography and garbled text
            if self._should_skip_match(converted_text, match.start(), match.group(0), category="method"):
                return None
            groups = match.groupdict()
            sentence, context = self._get_sentence_context(converted_text, match.start(), match.end())

            marine_score = self.fp_filter.get_marine_relevance_score(sentence, language)
            if marine_score < 0.1:
                return None

            method_type = self._parse_method_type(groups, language)
            description = sentence[:200]
            tools_used = self._extract_tools(context, language)
            sample_size = self._extract_sample_size(context)

            page_num = self._find_page_number(match.start(), page_texts)

            confidence = 0.7 + (0.1 if marine_score > 0.3 else 0) + (0.1 if tools_used else 0)

            return MethodExtraction(
                method_type=method_type,
                description=description,
                tools_used=tools_used,
                sample_size=sample_size,
                context=context[:200],
                exact_text=match.group(0),
                page_number=page_num,
                confidence=min(confidence, 1.0),
                marine_relevance=marine_score
            )

        except Exception as e:
            logger.warning(f"Error processing method match: {e}")
            return None

    def _parse_method_type(self, groups: Dict, language: str) -> str:
        """Parse method type"""
        method = (groups.get('method') or '').lower()

        if any(x in method for x in ['survey', 'anket', 'questionnaire']):
            return 'survey'
        elif any(x in method for x in ['interview', 'mülakat', 'röportaj']):
            return 'stakeholder_interview'
        elif any(x in method for x in ['model', 'modelleme']):
            return 'modeling'
        elif any(x in method for x in ['gis', 'cbs', 'spatial analysis']):
            return 'gis_analysis'
        elif any(x in method for x in ['field', 'saha', 'arazi']):
            return 'field_study'
        elif any(x in method for x in ['marxan', 'zonation', 'maxent', 'invest',
                                        'seasketch', 'mimes']):
            return 'conservation_planning_tool'
        elif any(x in method for x in ['ecosystem-based', 'ecosystem based', 'ebm']):
            return 'ecosystem_based_management'
        elif any(x in method for x in ['participatory', 'stakeholder consultation',
                                        'stakeholder engagement', 'stakeholder workshop',
                                        'paydaş']):
            return 'participatory_method'
        elif any(x in method for x in ['remote sensing', 'habitat mapping']):
            return 'remote_sensing'
        elif any(x in method for x in ['cost-benefit', 'cost benefit']):
            return 'cost_benefit_analysis'
        elif any(x in method for x in ['multi-criteria', 'multi criteria', 'delphi']):
            return 'multi_criteria_analysis'
        elif any(x in method for x in ['scenario', 'cumulative impact', 'cumulative effect']):
            return 'scenario_analysis'
        elif any(x in method for x in ['suitability', 'overlap']):
            return 'suitability_analysis'
        elif any(x in method for x in ['statistical', 'numerical']):
            return 'statistical_analysis'
        elif 'ebsa' in method:
            return 'ebsa_assessment'
        elif 'marine cadastre' in method:
            return 'marine_cadastre'

        return 'research_method'

    def _extract_tools(self, context: str, language: str) -> List[str]:
        """Extract tools used"""
        tools = []
        # Common GIS/analysis software
        tool_names = ['ArcGIS', 'QGIS', 'MATLAB', 'R', 'Python', 'SPSS', 'MarxanMarxan', 'Zonation']

        for tool in tool_names:
            if tool.lower() in context.lower():
                tools.append(tool)

        return tools[:5]

    def _extract_sample_size(self, context: str) -> Optional[int]:
        """Extract sample size"""
        patterns = [
            r'(?:n\s*=\s*|sample\s+size\s*=\s*|örneklem\s*=\s*)(\d+)',
            r'(\d+)\s+(?:participants|respondents|katılımcı)',
        ]

        for pattern in patterns:
            match = re.search(pattern, context, re.IGNORECASE | re.UNICODE)
            if match:
                try:
                    return int(match.group(1))
                except ValueError:
                    pass
        return None
