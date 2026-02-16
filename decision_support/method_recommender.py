"""
Method recommendation engine for MSP planning.

Recommends research methods based on evidence from the knowledge base,
user context, and data availability.
"""

from typing import Dict, List, Optional


class MethodRecommender:
    """Recommend methods based on evidence from research"""

    def recommend(self, user_context: Dict, knowledge_base) -> List[Dict]:
        """
        Recommend MSP methods based on user's planning context.

        Args:
            user_context: {
                'region': str,
                'objectives': List[str],  # e.g., ['biodiversity', 'fishing']
                'budget': str,  # 'low', 'medium', 'high'
                'timeline': int,  # months
                'available_data': List[str],
            }
            knowledge_base: KnowledgeDatabase instance

        Returns:
            List of recommendation dicts sorted by suitability
        """
        recommendations = []

        # Get all methods from KB
        methods = knowledge_base.query_extractions(category='method') if hasattr(knowledge_base, 'query_extractions') else []

        # Count method usage
        method_info = {}
        for ext in methods:
            metadata = ext.get('metadata', {})
            if isinstance(metadata, str):
                import json
                try:
                    metadata = json.loads(metadata)
                except (json.JSONDecodeError, TypeError):
                    metadata = {}

            method_type = ext.get('method_type', metadata.get('method_type', 'unknown'))
            if method_type not in method_info:
                method_info[method_type] = {
                    'count': 0,
                    'descriptions': [],
                    'tools': [],
                    'papers': [],
                }
            method_info[method_type]['count'] += 1

            desc = ext.get('description', metadata.get('description', ''))
            if desc:
                method_info[method_type]['descriptions'].append(desc[:100])

            tools = ext.get('tools_used', metadata.get('tools_used', []))
            if tools:
                method_info[method_type]['tools'].extend(
                    tools if isinstance(tools, list) else [tools]
                )

            source = ext.get('source_file', ext.get('document_id', ''))
            if source:
                method_info[method_type]['papers'].append(str(source))

        # Score each method
        for method_type, info in method_info.items():
            suitability = self._calculate_suitability(
                method_type, info, user_context
            )

            if suitability > 0.3:
                recommendations.append({
                    'method': method_type,
                    'suitability_score': round(suitability, 3),
                    'research_support': {
                        'usage_count': info['count'],
                        'example_descriptions': list(set(info['descriptions']))[:3],
                        'tools_used': list(set(info['tools']))[:5],
                        'paper_count': len(set(info['papers'])),
                    },
                    'data_requirements': self._infer_data_requirements(method_type),
                    'feasibility': self._assess_feasibility(
                        method_type, user_context
                    ),
                })

        recommendations.sort(key=lambda x: x['suitability_score'], reverse=True)
        return recommendations

    def _calculate_suitability(self, method_type: str, info: Dict,
                               context: Dict) -> float:
        """Calculate suitability score (0-1)."""
        score = 0.0

        # Usage frequency bonus (maturity)
        if info['count'] > 10:
            score += 0.3
        elif info['count'] > 5:
            score += 0.2
        elif info['count'] > 2:
            score += 0.1

        # Objective match
        objectives = context.get('objectives', [])
        method_lower = method_type.lower()
        objective_keywords = {
            'biodiversity': ['ecological', 'species', 'habitat', 'survey', 'sampling'],
            'fishing': ['fishery', 'catch', 'stock', 'survey'],
            'spatial_planning': ['gis', 'spatial', 'mapping', 'marxan', 'zonation'],
            'stakeholder': ['stakeholder', 'participatory', 'interview', 'survey'],
            'impact': ['impact', 'cumulative', 'assessment', 'modeling'],
        }

        for obj in objectives:
            keywords = objective_keywords.get(obj, [obj])
            if any(kw in method_lower for kw in keywords):
                score += 0.3
                break

        # Data availability match
        available = set(context.get('available_data', []))
        requirements = set(self._infer_data_requirements(method_type))
        if requirements:
            match_ratio = len(available & requirements) / len(requirements)
            score += match_ratio * 0.2

        # Tools availability bonus
        if info['tools']:
            score += 0.1

        return min(score, 1.0)

    def _infer_data_requirements(self, method_type: str) -> List[str]:
        """Infer data requirements from method type."""
        requirements = {
            'gis_analysis': ['spatial', 'bathymetry', 'boundaries'],
            'remote_sensing': ['satellite', 'imagery'],
            'ecological_modeling': ['biodiversity', 'environmental', 'bathymetry'],
            'stakeholder_analysis': ['socioeconomic', 'survey'],
            'statistical': ['quantitative', 'survey'],
            'field_sampling': ['survey_equipment', 'vessel'],
            'modeling': ['environmental', 'bathymetry', 'oceanographic'],
        }
        return requirements.get(method_type, [])

    def _assess_feasibility(self, method_type: str, context: Dict) -> str:
        """Assess feasibility based on budget and timeline."""
        budget = context.get('budget', 'medium')
        timeline = context.get('timeline', 12)

        expensive_methods = ['field_sampling', 'ecological_modeling', 'remote_sensing']
        time_intensive = ['field_sampling', 'stakeholder_analysis', 'ecological_modeling']

        if method_type in expensive_methods and budget == 'low':
            return 'low'
        if method_type in time_intensive and timeline < 6:
            return 'low'
        if budget == 'high' and timeline >= 12:
            return 'high'
        return 'medium'
