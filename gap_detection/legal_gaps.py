"""
Legal gap detection - identifies gaps in legal/regulatory frameworks.

Detects missing regulations, conflicting requirements, weak enforcement,
and areas where legal frameworks are incomplete.
"""

from typing import Dict, List
from collections import Counter, defaultdict

import sys
sys.path.insert(0, str(__import__('pathlib').Path(__file__).parent.parent))
from data_structures.integrated import Gap


class LegalGapDetector:
    """Detect gaps in legal/regulatory coverage"""

    def detect_all(self, knowledge_base) -> List[Gap]:
        """Run all legal gap detection methods."""
        gaps = []
        gaps.extend(self.detect_unregulated_activities(knowledge_base))
        gaps.extend(self.detect_missing_penalties(knowledge_base))
        gaps.extend(self.detect_vague_requirements(knowledge_base))
        gaps.extend(self.detect_enforcement_gaps(knowledge_base))
        return gaps

    def detect_unregulated_activities(self, kb) -> List[Gap]:
        """Find MSP activities without corresponding regulations."""
        gaps = []

        # Get all activities mentioned in research
        research_activities = set()
        for cat in ['method', 'finding', 'conflict', 'stakeholder']:
            extractions = kb.query_extractions(category=cat) if hasattr(kb, 'query_extractions') else []
            for ext in extractions:
                context = ext.get('context', ext.get('metadata', {}).get('context', ''))
                if context:
                    context_lower = context.lower()
                    for activity in ['aquaculture', 'fishing', 'shipping', 'tourism',
                                     'offshore_energy', 'dredging', 'mining',
                                     'conservation', 'military']:
                        if activity.replace('_', ' ') in context_lower:
                            research_activities.add(activity)

        # Get activities that have legal requirements
        regulated_activities = set()
        for cat in ['prohibition', 'permit', 'distance', 'penalty']:
            extractions = kb.query_extractions(category=cat) if hasattr(kb, 'query_extractions') else []
            for ext in extractions:
                activity = ext.get('activity', ext.get('metadata', {}).get('activity', ''))
                if activity:
                    regulated_activities.add(activity.lower())

        # Find gaps
        for activity in research_activities:
            if activity not in regulated_activities:
                gaps.append(Gap(
                    gap_category='legal',
                    gap_type='unregulated_activity',
                    severity='critical',
                    description=f"Activity '{activity}' discussed in research but no regulations found",
                    impact=f"No legal framework for managing {activity}",
                    recommendation=f"Develop regulations for {activity} activities",
                    evidence=[
                        f"Activity found in research papers",
                        f"No matching prohibition, permit, or distance requirement found"
                    ],
                ))

        return gaps

    def detect_missing_penalties(self, kb) -> List[Gap]:
        """Find prohibitions without associated penalties."""
        gaps = []

        prohibitions = kb.query_extractions(category='prohibition') if hasattr(kb, 'query_extractions') else []
        penalties = kb.query_extractions(category='penalty') if hasattr(kb, 'query_extractions') else []

        prohibited_activities = set()
        for ext in prohibitions:
            activity = ext.get('activity', ext.get('metadata', {}).get('activity', ''))
            if activity:
                prohibited_activities.add(activity.lower())

        penalized_activities = set()
        for ext in penalties:
            violation = ext.get('violation', ext.get('metadata', {}).get('violation', ''))
            if violation:
                penalized_activities.add(violation.lower())

        for activity in prohibited_activities:
            has_penalty = any(
                activity in p or p in activity
                for p in penalized_activities
            )
            if not has_penalty:
                gaps.append(Gap(
                    gap_category='legal',
                    gap_type='missing_penalty',
                    severity='important',
                    description=f"Prohibition on '{activity}' has no associated penalty",
                    impact=f"Weak enforcement for {activity} violations",
                    recommendation=f"Define specific penalties for {activity} violations",
                    evidence=[f"Prohibition found but no matching penalty extracted"],
                ))

        return gaps

    def detect_vague_requirements(self, kb) -> List[Gap]:
        """Find legal requirements that lack specific numeric values."""
        gaps = []

        distance_extractions = kb.query_extractions(category='distance') if hasattr(kb, 'query_extractions') else []

        low_confidence = [
            ext for ext in distance_extractions
            if ext.get('confidence', 1.0) < 0.5
        ]

        if low_confidence:
            gaps.append(Gap(
                gap_category='legal',
                gap_type='vague_requirement',
                severity='important',
                description=f"{len(low_confidence)} distance requirements have low extraction confidence",
                impact="Vague distance requirements may lead to inconsistent enforcement",
                recommendation="Review and clarify ambiguous distance specifications in legal texts",
                evidence=[f"{len(low_confidence)} extractions below 0.5 confidence"],
            ))

        return gaps

    def detect_enforcement_gaps(self, kb) -> List[Gap]:
        """Detect potential enforcement gaps."""
        gaps = []

        permits = kb.query_extractions(category='permit') if hasattr(kb, 'query_extractions') else []

        permits_without_authority = [
            ext for ext in permits
            if not ext.get('issuing_authority', ext.get('metadata', {}).get('issuing_authority'))
        ]

        if permits_without_authority:
            gaps.append(Gap(
                gap_category='legal',
                gap_type='enforcement_gap',
                severity='important',
                description=f"{len(permits_without_authority)} permit requirements lack specified issuing authority",
                impact="Unclear who is responsible for permit issuance and enforcement",
                recommendation="Specify responsible authority for each permit type",
                evidence=[f"{len(permits_without_authority)} permits without authority"],
            ))

        return gaps
