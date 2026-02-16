"""
Integrated knowledge structures for cross-source linking.

These structures combine information from research papers,
legal documents, and datasets into unified knowledge objects.
"""

from dataclasses import dataclass, field
from typing import Optional, Dict, List


@dataclass
class IntegratedSpeciesKnowledge:
    """Integrated knowledge about a species across all sources"""
    species_name: str
    scientific_name: Optional[str] = None
    research_mentions: int = 0
    key_papers: List[str] = field(default_factory=list)
    legal_status: Optional[str] = None  # "protected", "endangered", "not_protected"
    applicable_laws: List[str] = field(default_factory=list)
    available_data: List[str] = field(default_factory=list)
    conservation_status: Optional[str] = None
    gaps: List[Dict] = field(default_factory=list)

    def to_dict(self) -> Dict:
        return {
            'species_name': self.species_name,
            'scientific_name': self.scientific_name,
            'research_mentions': self.research_mentions,
            'key_papers': self.key_papers,
            'legal_status': self.legal_status,
            'applicable_laws': self.applicable_laws,
            'available_data': self.available_data,
            'conservation_status': self.conservation_status,
            'gaps': self.gaps,
        }


@dataclass
class IntegratedMethodKnowledge:
    """Integrated knowledge about a research method across all sources"""
    method_name: str
    method_type: Optional[str] = None
    usage_count: int = 0
    success_rate: Optional[float] = None
    legally_required: bool = False
    relevant_regulations: List[str] = field(default_factory=list)
    data_requirements: List[str] = field(default_factory=list)
    available_data: List[str] = field(default_factory=list)
    data_gaps: List[str] = field(default_factory=list)
    typical_results: List[str] = field(default_factory=list)
    recommendations: List[str] = field(default_factory=list)
    feasibility_score: Optional[float] = None
    example_papers: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict:
        return {
            'method_name': self.method_name,
            'method_type': self.method_type,
            'usage_count': self.usage_count,
            'success_rate': self.success_rate,
            'legally_required': self.legally_required,
            'relevant_regulations': self.relevant_regulations,
            'data_requirements': self.data_requirements,
            'available_data': self.available_data,
            'data_gaps': self.data_gaps,
            'typical_results': self.typical_results,
            'feasibility_score': self.feasibility_score,
            'example_papers': self.example_papers,
        }


@dataclass
class IntegratedMPAKnowledge:
    """Integrated knowledge about a Marine Protected Area across all sources"""
    mpa_name: str
    designation_type: Optional[str] = None  # "MPA", "SPA", "Ramsar", etc.
    size_km2: Optional[float] = None
    management_authority: Optional[str] = None
    research_studies: List[str] = field(default_factory=list)
    legal_designation: Optional[str] = None
    applicable_laws: List[str] = field(default_factory=list)
    monitoring_data: List[str] = field(default_factory=list)
    species_present: List[str] = field(default_factory=list)
    prohibited_activities: List[str] = field(default_factory=list)
    gaps: List[Dict] = field(default_factory=list)

    def to_dict(self) -> Dict:
        return {
            'mpa_name': self.mpa_name,
            'designation_type': self.designation_type,
            'size_km2': self.size_km2,
            'management_authority': self.management_authority,
            'research_studies': self.research_studies,
            'legal_designation': self.legal_designation,
            'applicable_laws': self.applicable_laws,
            'monitoring_data': self.monitoring_data,
            'species_present': self.species_present,
            'prohibited_activities': self.prohibited_activities,
            'gaps': self.gaps,
        }


@dataclass
class Gap:
    """A detected gap across any source type"""
    gap_category: str  # "research", "legal", "data", "integration"
    gap_type: str  # "research_legal_disconnect", "missing_data", etc.
    severity: str = "important"  # "critical", "important", "minor"
    description: str = ""
    impact: str = ""
    recommendation: str = ""
    evidence: List[str] = field(default_factory=list)
    source_documents: List[str] = field(default_factory=list)
    priority_score: float = 0.0

    def to_dict(self) -> Dict:
        return {
            'gap_category': self.gap_category,
            'gap_type': self.gap_type,
            'severity': self.severity,
            'description': self.description,
            'impact': self.impact,
            'recommendation': self.recommendation,
            'evidence': self.evidence,
            'source_documents': self.source_documents,
            'priority_score': self.priority_score,
        }
