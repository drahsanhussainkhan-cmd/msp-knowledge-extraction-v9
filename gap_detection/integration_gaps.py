"""
Integration gap detection - THE NOVEL CONTRIBUTION.

Detects gaps ACROSS research, legal, and data sources by identifying
disconnects between what research says, what laws require,
and what data is available.
"""

from typing import Dict, List
from collections import defaultdict

import sys
sys.path.insert(0, str(__import__('pathlib').Path(__file__).parent.parent))
from data_structures.integrated import Gap


class IntegrationGapDetector:
    """Detect gaps ACROSS research, legal, and data sources"""

    def detect_all(self, knowledge_base) -> List[Gap]:
        """Run all integration gap detection methods."""
        gaps = []
        gaps.extend(self.detect_unprotected_important_species(knowledge_base))
        gaps.extend(self.detect_legal_data_mismatch(knowledge_base))
        gaps.extend(self.detect_method_legal_disconnect(knowledge_base))
        gaps.extend(self.detect_unmonitored_mpas(knowledge_base))
        gaps.extend(self.detect_data_access_barriers(knowledge_base))
        gaps.extend(self.detect_research_policy_disconnect(knowledge_base))
        return gaps

    def detect_unprotected_important_species(self, kb) -> List[Gap]:
        """
        GAP TYPE 1: Research says species is important, but no legal protection.

        Find species that are:
        - Frequently mentioned in research (>= 3 papers)
        - BUT have no legal protection status
        """
        gaps = []

        # Get species from research papers (scientific documents)
        species_extractions = kb.query_extractions(category='species') if hasattr(kb, 'query_extractions') else []

        species_by_doc = defaultdict(set)
        species_protection = {}

        for ext in species_extractions:
            metadata = ext.get('metadata', {})
            if isinstance(metadata, str):
                import json
                try:
                    metadata = json.loads(metadata)
                except (json.JSONDecodeError, TypeError):
                    metadata = {}

            name = ext.get('species_name', metadata.get('species_name', ''))
            doc_id = ext.get('document_id', ext.get('source_file', ''))
            protection = ext.get('protection_status', metadata.get('protection_status'))

            if name:
                name_lower = name.lower().strip()
                species_by_doc[name_lower].add(str(doc_id))
                if protection:
                    species_protection[name_lower] = protection

        # Find frequently mentioned but unprotected species
        for species_name, docs in species_by_doc.items():
            if len(docs) >= 3 and species_name not in species_protection:
                gaps.append(Gap(
                    gap_category='integration',
                    gap_type='unprotected_important_species',
                    severity='critical',
                    description=(
                        f"Species '{species_name}' mentioned in {len(docs)} documents "
                        f"but no legal protection status found"
                    ),
                    impact=f"'{species_name}' may be at risk despite research interest",
                    recommendation=f"Assess conservation status of '{species_name}' and consider legal protection",
                    evidence=[
                        f"Mentioned in {len(docs)} documents",
                        "No protection status extracted from legal documents",
                    ],
                    source_documents=list(docs)[:10],
                ))

        return gaps

    def detect_legal_data_mismatch(self, kb) -> List[Gap]:
        """
        GAP TYPE 2: Laws require certain data/analysis that doesn't exist.

        Example: EIA law requires socioeconomic assessment, but no socioeconomic data available.
        """
        gaps = []

        # Get legal requirements (permits, environmental thresholds)
        permits = kb.query_extractions(category='permit') if hasattr(kb, 'query_extractions') else []
        env_reqs = kb.query_extractions(category='environmental') if hasattr(kb, 'query_extractions') else []

        # Get available data types
        data_sources = kb.query_extractions(category='data_source') if hasattr(kb, 'query_extractions') else []
        available_data = set()
        for ext in data_sources:
            metadata = ext.get('metadata', {})
            if isinstance(metadata, str):
                import json
                try:
                    metadata = json.loads(metadata)
                except (json.JSONDecodeError, TypeError):
                    metadata = {}
            source_type = ext.get('source_type', metadata.get('source_type', ''))
            if source_type:
                available_data.add(source_type.lower())

        # Check if permits require data we don't have
        data_requiring_terms = {
            'EIA': ['environmental', 'ecological', 'biodiversity'],
            'socioeconomic': ['socioeconomic', 'economic', 'social'],
            'bathymetric': ['bathymetry', 'depth', 'seabed'],
            'hydrographic': ['hydrographic', 'current', 'tide'],
        }

        for req_type, keywords in data_requiring_terms.items():
            # Check if any permit mentions this requirement
            requires_it = False
            for ext in permits:
                context = ext.get('context', ext.get('metadata', {}).get('context', '') if isinstance(ext.get('metadata'), dict) else '')
                if context and any(kw in context.lower() for kw in keywords):
                    requires_it = True
                    break

            if requires_it:
                has_data = any(kw in t for kw in keywords for t in available_data)
                if not has_data:
                    gaps.append(Gap(
                        gap_category='integration',
                        gap_type='legal_data_mismatch',
                        severity='critical',
                        description=f"Legal requirements reference {req_type} data, but no matching data source found",
                        impact=f"Cannot fulfill {req_type} requirements without the required data",
                        recommendation=f"Acquire {req_type} data to meet legal compliance",
                        evidence=[
                            f"Legal permits reference {req_type}",
                            f"No matching data source found in corpus",
                        ],
                    ))

        return gaps

    def detect_method_legal_disconnect(self, kb) -> List[Gap]:
        """
        GAP TYPE 3: Research recommends methods not legally mandated.

        Find methods frequently used in research that are not
        required or referenced in legal documents.
        """
        gaps = []

        methods = kb.query_extractions(category='method') if hasattr(kb, 'query_extractions') else []
        legal_refs = kb.query_extractions(category='legal_reference') if hasattr(kb, 'query_extractions') else []

        # Count method types used in research
        method_counts = defaultdict(int)
        for ext in methods:
            metadata = ext.get('metadata', {})
            if isinstance(metadata, str):
                import json
                try:
                    metadata = json.loads(metadata)
                except (json.JSONDecodeError, TypeError):
                    metadata = {}
            method_type = ext.get('method_type', metadata.get('method_type', 'unknown'))
            method_counts[method_type] += 1

        # Check which methods are mentioned in legal context
        legal_contexts = ' '.join(
            ext.get('context', ext.get('metadata', {}).get('context', '') if isinstance(ext.get('metadata'), dict) else '')
            for ext in legal_refs
        ).lower()

        for method_type, count in method_counts.items():
            if count >= 5 and method_type not in legal_contexts:
                gaps.append(Gap(
                    gap_category='integration',
                    gap_type='method_legal_disconnect',
                    severity='important',
                    description=f"Method '{method_type}' used in {count} research papers but not referenced in legal framework",
                    impact=f"Research best practice ({method_type}) not codified in regulations",
                    recommendation=f"Consider incorporating {method_type} requirements into MSP regulations",
                    evidence=[f"Used in {count} research papers", "Not found in legal documents"],
                ))

        return gaps

    def detect_unmonitored_mpas(self, kb) -> List[Gap]:
        """
        GAP TYPE 4: MPAs designated but no monitoring data available.
        """
        gaps = []

        mpas = kb.query_extractions(category='protected_area') if hasattr(kb, 'query_extractions') else []
        data_sources = kb.query_extractions(category='data_source') if hasattr(kb, 'query_extractions') else []

        mpa_names = set()
        for ext in mpas:
            metadata = ext.get('metadata', {})
            if isinstance(metadata, str):
                import json
                try:
                    metadata = json.loads(metadata)
                except (json.JSONDecodeError, TypeError):
                    metadata = {}
            name = ext.get('name', metadata.get('name', ''))
            if name:
                mpa_names.add(name.lower().strip())

        # Check if any data source references these MPAs
        data_contexts = ' '.join(
            ext.get('context', ext.get('metadata', {}).get('context', '') if isinstance(ext.get('metadata'), dict) else '')
            for ext in data_sources
        ).lower()

        for mpa_name in mpa_names:
            if mpa_name not in data_contexts:
                gaps.append(Gap(
                    gap_category='integration',
                    gap_type='unmonitored_mpa',
                    severity='critical',
                    description=f"MPA '{mpa_name}' designated but no monitoring data found",
                    impact=f"Cannot assess effectiveness of protection for '{mpa_name}'",
                    recommendation=f"Establish monitoring program for '{mpa_name}'",
                    evidence=[
                        f"MPA '{mpa_name}' found in legal documents",
                        "No monitoring data source references this MPA",
                    ],
                ))

        return gaps

    def detect_data_access_barriers(self, kb) -> List[Gap]:
        """
        GAP TYPE 5: Research uses data that's not publicly available.
        """
        gaps = []

        data_sources = kb.query_extractions(category='data_source') if hasattr(kb, 'query_extractions') else []

        restricted_count = 0
        total_count = len(data_sources)

        for ext in data_sources:
            metadata = ext.get('metadata', {})
            if isinstance(metadata, str):
                import json
                try:
                    metadata = json.loads(metadata)
                except (json.JSONDecodeError, TypeError):
                    metadata = {}
            access = ext.get('access_type', metadata.get('access_type', 'unknown'))
            if access in ('restricted', 'proprietary'):
                restricted_count += 1

        if restricted_count > 0 and total_count > 0:
            pct = restricted_count / total_count * 100
            if pct > 20:
                gaps.append(Gap(
                    gap_category='integration',
                    gap_type='data_access_barrier',
                    severity='important',
                    description=f"{pct:.0f}% of data sources ({restricted_count}/{total_count}) are restricted or proprietary",
                    impact="Limited data access hinders reproducibility and MSP implementation",
                    recommendation="Advocate for open data policies for MSP-relevant datasets",
                    evidence=[f"{restricted_count} restricted sources out of {total_count} total"],
                ))

        return gaps

    def detect_research_policy_disconnect(self, kb) -> List[Gap]:
        """
        GAP TYPE 6: Research conclusions/recommendations not reflected in policy.
        """
        gaps = []

        # Get research conclusions with policy implications
        findings = kb.query_extractions(category='finding') if hasattr(kb, 'query_extractions') else []
        policies = kb.query_extractions(category='policy') if hasattr(kb, 'query_extractions') else []

        recommendation_count = 0
        for ext in findings:
            metadata = ext.get('metadata', {})
            if isinstance(metadata, str):
                import json
                try:
                    metadata = json.loads(metadata)
                except (json.JSONDecodeError, TypeError):
                    metadata = {}
            finding_type = ext.get('finding_type', metadata.get('finding_type', ''))
            if finding_type == 'recommendation':
                recommendation_count += 1

        if recommendation_count > 10 and len(policies) < 5:
            gaps.append(Gap(
                gap_category='integration',
                gap_type='research_policy_disconnect',
                severity='critical',
                description=(
                    f"{recommendation_count} research recommendations found but only "
                    f"{len(policies)} policy references detected"
                ),
                impact="Research evidence not translated into policy action",
                recommendation="Review research recommendations and develop evidence-based policies",
                evidence=[
                    f"{recommendation_count} research recommendations",
                    f"Only {len(policies)} policy references found",
                ],
            ))

        return gaps
