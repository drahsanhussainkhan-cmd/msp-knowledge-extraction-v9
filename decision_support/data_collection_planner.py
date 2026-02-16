"""
Data collection planning based on identified gaps.
"""

from typing import Dict, List

import sys
sys.path.insert(0, str(__import__('pathlib').Path(__file__).parent.parent))
from data_structures.integrated import Gap


class DataCollectionPlanner:
    """Plan data collection to fill identified gaps"""

    COST_ESTIMATES = {
        'bathymetry': {'cost': 'high', 'time_months': 6, 'description': 'Multibeam sonar surveys'},
        'biodiversity': {'cost': 'high', 'time_months': 12, 'description': 'Underwater visual census, sampling'},
        'fishing_effort': {'cost': 'medium', 'time_months': 6, 'description': 'VMS data acquisition, logbook analysis'},
        'socioeconomic': {'cost': 'medium', 'time_months': 6, 'description': 'Surveys, interviews, census data'},
        'oceanographic': {'cost': 'high', 'time_months': 12, 'description': 'CTD surveys, current meters'},
        'water_quality': {'cost': 'medium', 'time_months': 3, 'description': 'Water sampling, lab analysis'},
        'satellite': {'cost': 'low', 'time_months': 1, 'description': 'Download from Copernicus/USGS'},
    }

    def plan_collection(self, gaps: List[Gap], budget: str = 'medium') -> List[Dict]:
        """
        Create prioritized data collection plan from gaps.

        Args:
            gaps: List of detected gaps (especially data gaps)
            budget: 'low', 'medium', or 'high'

        Returns:
            List of collection actions sorted by priority
        """
        data_gaps = [g for g in gaps if g.gap_category == 'data' or g.gap_type == 'legal_data_mismatch']

        actions = []
        for gap in data_gaps:
            data_type = self._infer_data_type(gap)
            estimate = self.COST_ESTIMATES.get(data_type, {
                'cost': 'unknown', 'time_months': 6, 'description': 'Custom data collection'
            })

            feasible = self._check_feasibility(estimate['cost'], budget)

            actions.append({
                'gap_description': gap.description,
                'data_type': data_type,
                'collection_method': estimate['description'],
                'estimated_cost': estimate['cost'],
                'estimated_time_months': estimate['time_months'],
                'feasible_within_budget': feasible,
                'priority': gap.priority_score,
                'severity': gap.severity,
            })

        actions.sort(key=lambda x: x['priority'], reverse=True)
        return actions

    def _infer_data_type(self, gap: Gap) -> str:
        """Infer data type from gap description."""
        desc = gap.description.lower()
        for data_type in self.COST_ESTIMATES:
            if data_type.replace('_', ' ') in desc:
                return data_type
        if 'depth' in desc or 'seabed' in desc:
            return 'bathymetry'
        if 'species' in desc or 'habitat' in desc:
            return 'biodiversity'
        if 'fish' in desc or 'catch' in desc:
            return 'fishing_effort'
        if 'economic' in desc or 'social' in desc:
            return 'socioeconomic'
        return 'unknown'

    def _check_feasibility(self, cost: str, budget: str) -> bool:
        """Check if data collection is feasible within budget."""
        cost_levels = {'low': 1, 'medium': 2, 'high': 3, 'unknown': 2}
        budget_levels = {'low': 1, 'medium': 2, 'high': 3}
        return cost_levels.get(cost, 2) <= budget_levels.get(budget, 2)
