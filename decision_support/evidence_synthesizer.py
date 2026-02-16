"""
Evidence synthesis engine for MSP decision support.

Aggregates findings from multiple papers to answer questions like:
- "Does stakeholder engagement improve MSP implementation?"
- "What is the typical MPA size that shows biodiversity benefits?"
- "How effective is Marxan in practice?"
"""

from typing import Dict, List
from collections import defaultdict


class EvidenceSynthesizer:
    """Synthesize evidence from multiple research papers"""

    def synthesize_for_topic(self, topic: str, knowledge_base) -> Dict:
        """
        Aggregate findings on a specific topic.

        Args:
            topic: Topic keyword to search for
            knowledge_base: KnowledgeDatabase instance

        Returns:
            Dict with synthesized evidence
        """
        findings = knowledge_base.query_extractions(category='finding') if hasattr(knowledge_base, 'query_extractions') else []
        methods = knowledge_base.query_extractions(category='method') if hasattr(knowledge_base, 'query_extractions') else []

        topic_lower = topic.lower()

        # Find relevant findings
        relevant_findings = []
        for ext in findings:
            text = ext.get('exact_text', '') or ''
            context = ext.get('context', '') or ''
            if topic_lower in text.lower() or topic_lower in context.lower():
                relevant_findings.append(ext)

        # Find relevant methods
        relevant_methods = []
        for ext in methods:
            text = ext.get('exact_text', '') or ''
            context = ext.get('context', '') or ''
            if topic_lower in text.lower() or topic_lower in context.lower():
                relevant_methods.append(ext)

        return {
            'topic': topic,
            'total_findings': len(relevant_findings),
            'total_methods': len(relevant_methods),
            'findings_summary': [
                {
                    'text': f.get('exact_text', '')[:200],
                    'confidence': f.get('confidence', 0),
                    'source': f.get('source_file', ''),
                }
                for f in relevant_findings[:20]
            ],
            'methods_used': list(set(
                m.get('method_type', m.get('metadata', {}).get('method_type', ''))
                for m in relevant_methods
                if m.get('method_type') or (isinstance(m.get('metadata'), dict) and m['metadata'].get('method_type'))
            )),
            'evidence_strength': self._assess_evidence_strength(relevant_findings),
        }

    def synthesize_all_topics(self, knowledge_base) -> Dict:
        """
        Auto-discover and synthesize evidence for key MSP topics.

        Returns:
            Dict of topic -> synthesis
        """
        topics = [
            'marine protected area', 'biodiversity', 'fishing',
            'aquaculture', 'stakeholder', 'climate change',
            'habitat', 'pollution', 'conservation', 'spatial planning',
        ]

        syntheses = {}
        for topic in topics:
            result = self.synthesize_for_topic(topic, knowledge_base)
            if result['total_findings'] > 0:
                syntheses[topic] = result

        return syntheses

    def compare_methods(self, knowledge_base) -> Dict:
        """
        Compare effectiveness of different research methods.

        Returns:
            Dict of method_type -> effectiveness info
        """
        methods = knowledge_base.query_extractions(category='method') if hasattr(knowledge_base, 'query_extractions') else []
        findings = knowledge_base.query_extractions(category='finding') if hasattr(knowledge_base, 'query_extractions') else []

        method_docs = defaultdict(set)
        for ext in methods:
            metadata = ext.get('metadata', {})
            if isinstance(metadata, str):
                import json
                try:
                    metadata = json.loads(metadata)
                except (json.JSONDecodeError, TypeError):
                    metadata = {}
            method_type = ext.get('method_type', metadata.get('method_type', 'unknown'))
            doc = ext.get('source_file', ext.get('document_id', ''))
            method_docs[method_type].add(str(doc))

        comparison = {}
        for method_type, docs in sorted(method_docs.items(), key=lambda x: -len(x[1])):
            comparison[method_type] = {
                'usage_count': len(docs),
                'paper_count': len(docs),
            }

        return comparison

    def _assess_evidence_strength(self, findings: List[Dict]) -> str:
        """Assess overall evidence strength from findings."""
        if len(findings) >= 10:
            return 'strong'
        elif len(findings) >= 5:
            return 'moderate'
        elif len(findings) >= 2:
            return 'weak'
        elif len(findings) >= 1:
            return 'limited'
        return 'none'
