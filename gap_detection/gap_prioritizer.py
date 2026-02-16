"""
Gap prioritization - ranks detected gaps by severity and actionability.
"""

from typing import Dict, List

import sys
sys.path.insert(0, str(__import__('pathlib').Path(__file__).parent.parent))
from data_structures.integrated import Gap


class GapPrioritizer:
    """Prioritize detected gaps by severity, evidence, and actionability"""

    SEVERITY_SCORES = {
        'critical': 3.0,
        'important': 2.0,
        'minor': 1.0,
    }

    CATEGORY_WEIGHTS = {
        'integration': 1.5,  # Novel contribution - weight higher
        'legal': 1.3,
        'research': 1.0,
        'data': 1.1,
    }

    def prioritize(self, gaps: List[Gap]) -> List[Gap]:
        """
        Score and sort gaps by priority.

        Priority score considers:
        - Severity (critical > important > minor)
        - Gap category weight (integration > legal > data > research)
        - Evidence strength (more evidence = higher priority)

        Args:
            gaps: List of Gap objects

        Returns:
            Same gaps sorted by priority_score (descending)
        """
        for gap in gaps:
            gap.priority_score = self._calculate_priority(gap)

        gaps.sort(key=lambda g: g.priority_score, reverse=True)
        return gaps

    def _calculate_priority(self, gap: Gap) -> float:
        """Calculate priority score for a single gap."""
        severity_score = self.SEVERITY_SCORES.get(gap.severity, 1.0)
        category_weight = self.CATEGORY_WEIGHTS.get(gap.gap_category, 1.0)
        evidence_bonus = min(len(gap.evidence) * 0.1, 0.5)

        # Actionability bonus
        actionability = 0.0
        if gap.recommendation:
            actionability = 0.2
        if gap.impact:
            actionability += 0.1

        return severity_score * category_weight + evidence_bonus + actionability

    def get_top_gaps(self, gaps: List[Gap], n: int = 10) -> List[Gap]:
        """Get top N priority gaps."""
        prioritized = self.prioritize(gaps)
        return prioritized[:n]

    def get_gaps_by_category(self, gaps: List[Gap]) -> Dict[str, List[Gap]]:
        """Group gaps by category."""
        by_category = {}
        for gap in gaps:
            if gap.gap_category not in by_category:
                by_category[gap.gap_category] = []
            by_category[gap.gap_category].append(gap)
        return by_category

    def generate_summary(self, gaps: List[Gap]) -> Dict:
        """Generate a summary of all detected gaps."""
        prioritized = self.prioritize(gaps)

        by_severity = {'critical': 0, 'important': 0, 'minor': 0}
        by_category = {}

        for gap in prioritized:
            by_severity[gap.severity] = by_severity.get(gap.severity, 0) + 1
            by_category[gap.gap_category] = by_category.get(gap.gap_category, 0) + 1

        return {
            'total_gaps': len(prioritized),
            'by_severity': by_severity,
            'by_category': by_category,
            'top_5': [gap.to_dict() for gap in prioritized[:5]],
            'critical_gaps': [gap.to_dict() for gap in prioritized if gap.severity == 'critical'],
        }
