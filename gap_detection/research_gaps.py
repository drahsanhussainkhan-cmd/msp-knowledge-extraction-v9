"""
Research gap detection - identifies gaps within the research literature.

Detects methodological, geographic, temporal, and thematic gaps
by analyzing extraction patterns across the corpus.
"""

from typing import Dict, List
from collections import Counter, defaultdict

import sys
sys.path.insert(0, str(__import__('pathlib').Path(__file__).parent.parent))
from data_structures.integrated import Gap


class ResearchGapDetector:
    """Detect gaps within research literature"""

    def detect_all(self, knowledge_base) -> List[Gap]:
        """Run all research gap detection methods."""
        gaps = []
        gaps.extend(self.detect_method_gaps(knowledge_base))
        gaps.extend(self.detect_geographic_gaps(knowledge_base))
        gaps.extend(self.detect_thematic_gaps(knowledge_base))
        gaps.extend(self.detect_temporal_gaps(knowledge_base))
        return gaps

    def detect_method_gaps(self, kb) -> List[Gap]:
        """Find underutilized research methods."""
        gaps = []
        method_counts = Counter()

        # Count method usage across documents
        extractions = kb.query_extractions(category='method') if hasattr(kb, 'query_extractions') else []
        for ext in extractions:
            method_type = ext.get('method_type', ext.get('metadata', {}).get('method_type', 'unknown'))
            method_counts[method_type] += 1

        if not method_counts:
            return gaps

        avg_usage = sum(method_counts.values()) / len(method_counts) if method_counts else 0

        # Important MSP methods that should be used
        expected_methods = [
            'gis_analysis', 'stakeholder_analysis', 'ecological_modeling',
            'economic_analysis', 'cumulative_impact', 'scenario_planning'
        ]

        for method in expected_methods:
            count = method_counts.get(method, 0)
            if count < avg_usage * 0.3:
                severity = 'critical' if count == 0 else 'important'
                gaps.append(Gap(
                    gap_category='research',
                    gap_type='method_gap',
                    severity=severity,
                    description=f"Method '{method}' is underutilized ({count} uses vs avg {avg_usage:.0f})",
                    impact=f"MSP decisions may lack {method} evidence base",
                    recommendation=f"Encourage use of {method} in future MSP studies",
                    evidence=[f"Used in {count} papers, average method usage: {avg_usage:.0f}"],
                ))

        return gaps

    def detect_geographic_gaps(self, kb) -> List[Gap]:
        """Find geographic areas with low research coverage."""
        gaps = []

        # Analyze protected areas mentioned vs studied
        pa_extractions = kb.query_extractions(category='protected_area') if hasattr(kb, 'query_extractions') else []
        pa_by_doc = defaultdict(set)
        for ext in pa_extractions:
            name = ext.get('name', ext.get('metadata', {}).get('name', ''))
            doc = ext.get('source_file', ext.get('document_id', ''))
            if name:
                pa_by_doc[name].add(str(doc))

        for pa_name, docs in pa_by_doc.items():
            if len(docs) < 2:
                gaps.append(Gap(
                    gap_category='research',
                    gap_type='geographic_gap',
                    severity='important',
                    description=f"Protected area '{pa_name}' mentioned in only {len(docs)} document(s)",
                    impact=f"Insufficient research coverage for management of {pa_name}",
                    recommendation=f"Prioritize research in {pa_name}",
                    evidence=[f"Mentioned in {len(docs)} documents"],
                ))

        return gaps

    def detect_thematic_gaps(self, kb) -> List[Gap]:
        """Find under-researched MSP themes."""
        gaps = []

        # Count topics by finding keyword categories
        category_counts = {}
        if hasattr(kb, 'get_extraction_counts'):
            category_counts = kb.get_extraction_counts()

        # Important categories for MSP
        critical_categories = {
            'conflict': 'Use conflict analysis',
            'stakeholder': 'Stakeholder engagement',
            'species': 'Biodiversity assessment',
            'environmental': 'Environmental impact',
        }

        for cat, label in critical_categories.items():
            count = category_counts.get(cat, 0)
            if count < 5:
                gaps.append(Gap(
                    gap_category='research',
                    gap_type='thematic_gap',
                    severity='important' if count > 0 else 'critical',
                    description=f"Limited research on {label} ({count} extractions found)",
                    impact=f"MSP framework lacks adequate {label.lower()} evidence",
                    recommendation=f"Commission studies focused on {label.lower()}",
                    evidence=[f"{count} extractions in category '{cat}'"],
                ))

        return gaps

    def detect_temporal_gaps(self, kb) -> List[Gap]:
        """Find time periods with insufficient research coverage."""
        gaps = []

        temporal_extractions = kb.query_extractions(category='temporal') if hasattr(kb, 'query_extractions') else []

        if not temporal_extractions:
            gaps.append(Gap(
                gap_category='research',
                gap_type='temporal_gap',
                severity='important',
                description="No temporal restriction data found in research corpus",
                impact="Cannot assess seasonal management effectiveness",
                recommendation="Include temporal analysis in future MSP studies",
            ))

        return gaps
