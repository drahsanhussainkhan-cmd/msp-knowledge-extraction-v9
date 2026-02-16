"""
Data gap detection - identifies missing, outdated, or insufficient data.
"""

from typing import Dict, List
from collections import Counter

import sys
sys.path.insert(0, str(__import__('pathlib').Path(__file__).parent.parent))
from data_structures.integrated import Gap


class DataGapDetector:
    """Detect gaps in data availability"""

    def detect_all(self, knowledge_base) -> List[Gap]:
        """Run all data gap detection methods."""
        gaps = []
        gaps.extend(self.detect_missing_data_types(knowledge_base))
        gaps.extend(self.detect_coverage_gaps(knowledge_base))
        gaps.extend(self.detect_resolution_gaps(knowledge_base))
        return gaps

    def detect_missing_data_types(self, kb) -> List[Gap]:
        """Find essential data types that are not available."""
        gaps = []

        data_sources = kb.query_extractions(category='data_source') if hasattr(kb, 'query_extractions') else []
        available_types = set()
        for ext in data_sources:
            source_type = ext.get('source_type', ext.get('metadata', {}).get('source_type', ''))
            if source_type:
                available_types.add(source_type.lower())

        essential_types = {
            'bathymetry': 'Bathymetric data for seabed mapping',
            'biodiversity': 'Biodiversity surveys for species distribution',
            'fishing_effort': 'Fishing effort data for resource management',
            'socioeconomic': 'Socioeconomic data for impact assessment',
            'oceanographic': 'Oceanographic data for physical characterization',
            'water_quality': 'Water quality monitoring data',
        }

        for data_type, description in essential_types.items():
            if data_type not in available_types:
                # Check if any similar type exists
                has_similar = any(data_type[:4] in t for t in available_types)
                if not has_similar:
                    gaps.append(Gap(
                        gap_category='data',
                        gap_type='missing_data_type',
                        severity='critical',
                        description=f"No {description.lower()} found in corpus",
                        impact=f"Cannot perform {data_type}-based analysis for MSP",
                        recommendation=f"Acquire or collect {data_type} data",
                        evidence=[f"Data type '{data_type}' not found among {len(available_types)} available types"],
                    ))

        return gaps

    def detect_coverage_gaps(self, kb) -> List[Gap]:
        """Find areas with insufficient spatial or temporal coverage."""
        gaps = []

        data_sources = kb.query_extractions(category='data_source') if hasattr(kb, 'query_extractions') else []

        sources_without_coverage = [
            ext for ext in data_sources
            if not ext.get('spatial_coverage', ext.get('metadata', {}).get('spatial_coverage'))
            and not ext.get('temporal_coverage', ext.get('metadata', {}).get('temporal_coverage'))
        ]

        if sources_without_coverage and len(data_sources) > 0:
            pct = len(sources_without_coverage) / len(data_sources) * 100
            if pct > 30:
                gaps.append(Gap(
                    gap_category='data',
                    gap_type='coverage_gap',
                    severity='important',
                    description=f"{pct:.0f}% of data sources lack coverage information",
                    impact="Cannot assess spatial/temporal completeness of data",
                    recommendation="Document spatial and temporal coverage for all datasets",
                    evidence=[f"{len(sources_without_coverage)}/{len(data_sources)} sources missing coverage info"],
                ))

        return gaps

    def detect_resolution_gaps(self, kb) -> List[Gap]:
        """Find data with insufficient resolution for MSP needs."""
        gaps = []

        data_sources = kb.query_extractions(category='data_source') if hasattr(kb, 'query_extractions') else []

        sources_without_resolution = [
            ext for ext in data_sources
            if not ext.get('resolution', ext.get('metadata', {}).get('resolution'))
        ]

        if sources_without_resolution and len(data_sources) > 0:
            pct = len(sources_without_resolution) / len(data_sources) * 100
            if pct > 50:
                gaps.append(Gap(
                    gap_category='data',
                    gap_type='resolution_gap',
                    severity='minor',
                    description=f"{pct:.0f}% of data sources lack resolution information",
                    impact="Cannot verify if data resolution is adequate for MSP",
                    recommendation="Specify resolution for all spatial datasets",
                    evidence=[f"{len(sources_without_resolution)}/{len(data_sources)} sources missing resolution"],
                ))

        return gaps
