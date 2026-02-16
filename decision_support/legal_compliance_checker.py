"""
Legal compliance checker for MSP activities.

Checks if a proposed activity complies with legal requirements
extracted from the knowledge base.
"""

from typing import Dict, List, Optional


class LegalComplianceChecker:
    """Check activity compliance against legal requirements"""

    def check_compliance(self, activity: str, location: str,
                         knowledge_base) -> Dict:
        """
        Check all legal requirements for a proposed activity.

        Args:
            activity: Activity type (e.g., 'aquaculture', 'fishing')
            location: Location description
            knowledge_base: KnowledgeDatabase instance

        Returns:
            ComplianceReport dict with requirements checklist
        """
        report = {
            'activity': activity,
            'location': location,
            'status': 'unknown',
            'requirements': [],
            'warnings': [],
            'applicable_laws': [],
        }

        activity_lower = activity.lower()

        # Check distance requirements
        distances = knowledge_base.query_extractions(category='distance') if hasattr(knowledge_base, 'query_extractions') else []
        for ext in distances:
            ext_activity = ext.get('activity', ext.get('metadata', {}).get('activity', '') if isinstance(ext.get('metadata'), dict) else '')
            if ext_activity and activity_lower in ext_activity.lower():
                report['requirements'].append({
                    'type': 'distance',
                    'description': ext.get('exact_text', '')[:200],
                    'value': ext.get('value', ext.get('metadata', {}).get('value') if isinstance(ext.get('metadata'), dict) else None),
                    'unit': ext.get('unit', ext.get('metadata', {}).get('unit', 'metre') if isinstance(ext.get('metadata'), dict) else 'metre'),
                    'confidence': ext.get('confidence', 0),
                })

        # Check prohibitions
        prohibitions = knowledge_base.query_extractions(category='prohibition') if hasattr(knowledge_base, 'query_extractions') else []
        for ext in prohibitions:
            ext_activity = ext.get('activity', ext.get('metadata', {}).get('activity', '') if isinstance(ext.get('metadata'), dict) else '')
            if ext_activity and activity_lower in ext_activity.lower():
                report['warnings'].append({
                    'type': 'prohibition',
                    'description': ext.get('exact_text', '')[:200],
                    'scope': ext.get('scope', ext.get('metadata', {}).get('scope') if isinstance(ext.get('metadata'), dict) else None),
                })

        # Check permit requirements
        permits = knowledge_base.query_extractions(category='permit') if hasattr(knowledge_base, 'query_extractions') else []
        for ext in permits:
            ext_activity = ext.get('activity', ext.get('metadata', {}).get('activity', '') if isinstance(ext.get('metadata'), dict) else '')
            if ext_activity and activity_lower in ext_activity.lower():
                report['requirements'].append({
                    'type': 'permit',
                    'permit_type': ext.get('permit_type', ext.get('metadata', {}).get('permit_type') if isinstance(ext.get('metadata'), dict) else ''),
                    'description': ext.get('exact_text', '')[:200],
                    'authority': ext.get('issuing_authority', ext.get('metadata', {}).get('issuing_authority') if isinstance(ext.get('metadata'), dict) else None),
                })

        # Check environmental requirements
        env_reqs = knowledge_base.query_extractions(category='environmental') if hasattr(knowledge_base, 'query_extractions') else []
        for ext in env_reqs:
            context = ext.get('context', ext.get('metadata', {}).get('context', '') if isinstance(ext.get('metadata'), dict) else '')
            if context and activity_lower in context.lower():
                report['requirements'].append({
                    'type': 'environmental',
                    'description': ext.get('exact_text', '')[:200],
                    'threshold': ext.get('value', ext.get('metadata', {}).get('value') if isinstance(ext.get('metadata'), dict) else None),
                })

        # Get applicable laws
        legal_refs = knowledge_base.query_extractions(category='legal_reference') if hasattr(knowledge_base, 'query_extractions') else []
        for ext in legal_refs:
            context = ext.get('context', ext.get('metadata', {}).get('context', '') if isinstance(ext.get('metadata'), dict) else '')
            if context and activity_lower in context.lower():
                report['applicable_laws'].append({
                    'law': ext.get('title', ext.get('metadata', {}).get('title') if isinstance(ext.get('metadata'), dict) else ''),
                    'number': ext.get('law_number', ext.get('metadata', {}).get('law_number') if isinstance(ext.get('metadata'), dict) else ''),
                })

        # Determine overall status
        if report['warnings']:
            report['status'] = 'potential_violation'
        elif report['requirements']:
            report['status'] = 'requirements_identified'
        else:
            report['status'] = 'no_specific_requirements_found'

        return report
