"""
Dataclass models for all MSP extraction categories.

Original 17 categories + 5 new categories for the full knowledge system:
- ResearchObjectiveExtraction
- ResultExtraction
- ConclusionExtraction
- GapIdentifiedExtraction
- DatasetMetadata
"""
from dataclasses import dataclass, field
from typing import Optional, Dict, List
import hashlib


@dataclass
class DistanceExtraction:
    """Distance/buffer zone extraction - WORKING"""
    activity: str
    value: Optional[float] = None
    min_value: Optional[float] = None
    max_value: Optional[float] = None
    unit: str = 'metre'
    qualifier: Optional[str] = None
    reference_point: Optional[str] = None
    reference_point_type: Optional[str] = None
    legal_reference: Optional[str] = None
    authority: Optional[str] = None
    context: Optional[str] = None
    exact_text: Optional[str] = None
    page_number: Optional[int] = None
    confidence: float = 1.0
    confidence_breakdown: Dict[str, float] = field(default_factory=dict)
    activity_confidence: float = 0.5
    marine_relevance: float = 0.5
    is_range: bool = False
    filter_status: str = "passed"
    document_type: Optional[str] = None
    language: Optional[str] = None

    @property
    def extraction_hash(self) -> str:
        key = f"{self.value}_{self.unit}_{self.activity}_{self.exact_text[:50] if self.exact_text else ''}"
        return hashlib.md5(key.encode()).hexdigest()[:16]


@dataclass
class EnvironmentalExtraction:
    """Environmental condition/requirement extraction"""
    # NOTE: NO 'authority' field - causes error
    condition_type: str  # e.g., "water_quality", "noise_limit", "pollution"
    description: str
    value: Optional[float] = None
    unit: Optional[str] = None
    threshold_type: Optional[str] = None  # "maximum", "minimum", "range"
    legal_reference: Optional[str] = None
    context: Optional[str] = None
    exact_text: Optional[str] = None
    page_number: Optional[int] = None
    confidence: float = 1.0
    marine_relevance: float = 0.5

    @property
    def extraction_hash(self) -> str:
        key = f"{self.condition_type}_{self.description[:30]}_{self.value}"
        return hashlib.md5(key.encode()).hexdigest()[:16]


@dataclass
class TemporalExtraction:
    """Temporal restrictions/periods extraction"""
    # NOTE: NO 'language' field - causes error
    restriction_type: str  # "seasonal", "time_of_day", "duration"
    start_date: Optional[str] = None
    end_date: Optional[str] = None
    duration: Optional[str] = None
    activity: Optional[str] = None
    legal_reference: Optional[str] = None
    context: Optional[str] = None
    exact_text: Optional[str] = None
    page_number: Optional[int] = None
    confidence: float = 1.0
    marine_relevance: float = 0.5

    @property
    def extraction_hash(self) -> str:
        key = f"{self.restriction_type}_{self.start_date}_{self.end_date}_{self.activity}"
        return hashlib.md5(key.encode()).hexdigest()[:16]


@dataclass
class PenaltyExtraction:
    """Penalty/fine extraction"""
    # NOTE: NO 'document_type' field - causes error
    penalty_type: str  # "fine", "imprisonment", "license_revocation"
    amount: Optional[float] = None
    currency: Optional[str] = None
    duration: Optional[str] = None  # for imprisonment
    violation: Optional[str] = None
    legal_reference: Optional[str] = None
    context: Optional[str] = None
    exact_text: Optional[str] = None
    page_number: Optional[int] = None
    confidence: float = 1.0
    marine_relevance: float = 0.5

    @property
    def extraction_hash(self) -> str:
        key = f"{self.penalty_type}_{self.amount}_{self.violation[:30] if self.violation else ''}"
        return hashlib.md5(key.encode()).hexdigest()[:16]


@dataclass
class PermitExtraction:
    """Permit/license requirement extraction"""
    permit_type: str  # "fishing_license", "construction_permit", "environmental_approval"
    issuing_authority: Optional[str] = None
    requirements: Optional[List[str]] = field(default_factory=list)
    validity_period: Optional[str] = None
    activity: Optional[str] = None
    legal_reference: Optional[str] = None
    context: Optional[str] = None
    exact_text: Optional[str] = None
    page_number: Optional[int] = None
    confidence: float = 1.0
    marine_relevance: float = 0.5

    @property
    def extraction_hash(self) -> str:
        key = f"{self.permit_type}_{self.issuing_authority}_{self.activity}"
        return hashlib.md5(key.encode()).hexdigest()[:16]


@dataclass
class ProtectedAreaExtraction:
    """Protected area extraction"""
    # NOTE: Use 'area_type' NOT 'area_name' - causes error
    area_type: str  # "marine_protected_area", "national_park", "conservation_zone"
    name: Optional[str] = None
    designation: Optional[str] = None
    restrictions: Optional[List[str]] = field(default_factory=list)
    legal_reference: Optional[str] = None
    context: Optional[str] = None
    exact_text: Optional[str] = None
    page_number: Optional[int] = None
    confidence: float = 1.0
    marine_relevance: float = 0.5

    @property
    def extraction_hash(self) -> str:
        key = f"{self.area_type}_{self.name}_{self.designation}"
        return hashlib.md5(key.encode()).hexdigest()[:16]


@dataclass
class ProhibitionExtraction:
    """Prohibition/restriction extraction"""
    # NOTE: NO 'language' field - causes error
    prohibition_type: str  # "activity_banned", "area_restricted", "method_prohibited"
    activity: Optional[str] = None
    scope: Optional[str] = None
    exceptions: Optional[List[str]] = field(default_factory=list)
    legal_reference: Optional[str] = None
    context: Optional[str] = None
    exact_text: Optional[str] = None
    page_number: Optional[int] = None
    confidence: float = 1.0
    marine_relevance: float = 0.5

    @property
    def extraction_hash(self) -> str:
        key = f"{self.prohibition_type}_{self.activity}_{self.scope}"
        return hashlib.md5(key.encode()).hexdigest()[:16]


@dataclass
class CoordinateExtraction:
    """Geographic coordinate extraction"""
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    coordinate_system: str = "WGS84"
    location_description: Optional[str] = None
    boundary_type: Optional[str] = None  # "point", "polygon", "line"
    legal_reference: Optional[str] = None
    context: Optional[str] = None
    exact_text: Optional[str] = None
    page_number: Optional[int] = None
    confidence: float = 1.0
    marine_relevance: float = 0.5

    @property
    def extraction_hash(self) -> str:
        key = f"{self.latitude}_{self.longitude}_{self.location_description}"
        return hashlib.md5(key.encode()).hexdigest()[:16]


@dataclass
class SpeciesExtraction:
    """Species mention extraction"""
    # NOTE: NO 'language' field - causes error
    species_name: str
    scientific_name: Optional[str] = None
    common_name: Optional[str] = None
    protection_status: Optional[str] = None
    activity_context: Optional[str] = None  # what activity involves this species
    legal_reference: Optional[str] = None
    context: Optional[str] = None
    exact_text: Optional[str] = None
    page_number: Optional[int] = None
    confidence: float = 1.0
    marine_relevance: float = 0.5

    @property
    def extraction_hash(self) -> str:
        key = f"{self.species_name}_{self.scientific_name}_{self.protection_status}"
        return hashlib.md5(key.encode()).hexdigest()[:16]


@dataclass
class StakeholderExtraction:
    """Stakeholder/institution mention extraction"""
    # NOTE: NO 'language' field - causes error
    stakeholder_name: str
    stakeholder_type: Optional[str] = None  # "government", "ngo", "industry", "community"
    role: Optional[str] = None
    responsibilities: Optional[List[str]] = field(default_factory=list)
    legal_reference: Optional[str] = None
    context: Optional[str] = None
    exact_text: Optional[str] = None
    page_number: Optional[int] = None
    confidence: float = 1.0
    marine_relevance: float = 0.5

    @property
    def extraction_hash(self) -> str:
        key = f"{self.stakeholder_name}_{self.stakeholder_type}_{self.role}"
        return hashlib.md5(key.encode()).hexdigest()[:16]


@dataclass
class ConflictExtraction:
    """Use conflict/compatibility extraction (for scientific papers)"""
    conflict_type: str  # "spatial", "temporal", "resource", "governance"
    activity_1: Optional[str] = None
    activity_2: Optional[str] = None
    severity: Optional[str] = None  # "high", "medium", "low"
    resolution: Optional[str] = None
    context: Optional[str] = None
    exact_text: Optional[str] = None
    page_number: Optional[int] = None
    confidence: float = 1.0
    marine_relevance: float = 0.5
    related_stakeholders: List[str] = field(default_factory=list)
    related_areas: List[str] = field(default_factory=list)

    @property
    def extraction_hash(self) -> str:
        key = f"{self.conflict_type}_{self.activity_1}_{self.activity_2}"
        return hashlib.md5(key.encode()).hexdigest()[:16]


@dataclass
class MethodExtraction:
    """Research method extraction (for scientific papers)"""
    method_type: str  # "survey", "modeling", "gis_analysis", "stakeholder_interview"
    description: Optional[str] = None
    tools_used: Optional[List[str]] = field(default_factory=list)
    sample_size: Optional[int] = None
    context: Optional[str] = None
    exact_text: Optional[str] = None
    page_number: Optional[int] = None
    confidence: float = 1.0
    marine_relevance: float = 0.5

    @property
    def extraction_hash(self) -> str:
        key = f"{self.method_type}_{self.description[:30] if self.description else ''}_{self.sample_size}"
        return hashlib.md5(key.encode()).hexdigest()[:16]


@dataclass
class FindingExtraction:
    """Research finding extraction (for scientific papers)"""
    finding_type: str  # "spatial_pattern", "trend", "correlation", "recommendation"
    description: str
    quantitative_result: Optional[str] = None
    significance: Optional[str] = None
    context: Optional[str] = None
    exact_text: Optional[str] = None
    page_number: Optional[int] = None
    confidence: float = 1.0
    marine_relevance: float = 0.5

    @property
    def extraction_hash(self) -> str:
        key = f"{self.finding_type}_{self.description[:30]}_{self.quantitative_result}"
        return hashlib.md5(key.encode()).hexdigest()[:16]


@dataclass
class PolicyExtraction:
    """Policy/regulation extraction"""
    policy_type: str  # "directive", "regulation", "guideline", "framework"
    title: Optional[str] = None
    scope: Optional[str] = None
    objectives: Optional[List[str]] = field(default_factory=list)
    legal_reference: Optional[str] = None
    context: Optional[str] = None
    exact_text: Optional[str] = None
    page_number: Optional[int] = None
    confidence: float = 1.0
    marine_relevance: float = 0.5

    @property
    def extraction_hash(self) -> str:
        key = f"{self.policy_type}_{self.title}_{self.scope}"
        return hashlib.md5(key.encode()).hexdigest()[:16]


@dataclass
class DataSourceExtraction:
    """Data source extraction (for scientific papers)"""
    source_type: str  # "satellite", "survey", "database", "literature"
    source_name: Optional[str] = None
    spatial_coverage: Optional[str] = None
    temporal_coverage: Optional[str] = None
    resolution: Optional[str] = None
    context: Optional[str] = None
    exact_text: Optional[str] = None
    page_number: Optional[int] = None
    confidence: float = 1.0
    marine_relevance: float = 0.5

    @property
    def extraction_hash(self) -> str:
        key = f"{self.source_type}_{self.source_name}_{self.spatial_coverage}"
        return hashlib.md5(key.encode()).hexdigest()[:16]


@dataclass
class LegalReferenceExtraction:
    """Legal reference/citation extraction"""
    reference_type: str  # "law", "regulation", "decree", "directive"
    law_number: Optional[str] = None
    article_number: Optional[str] = None
    title: Optional[str] = None
    date: Optional[str] = None
    context: Optional[str] = None
    exact_text: Optional[str] = None
    page_number: Optional[int] = None
    confidence: float = 1.0
    marine_relevance: float = 0.5

    @property
    def extraction_hash(self) -> str:
        key = f"{self.reference_type}_{self.law_number}_{self.article_number}"
        return hashlib.md5(key.encode()).hexdigest()[:16]


@dataclass
class InstitutionExtraction:
    """Institution/authority extraction"""
    institution_name: str
    institution_type: Optional[str] = None  # "ministry", "agency", "committee", "university"
    role: Optional[str] = None
    jurisdiction: Optional[str] = None
    legal_reference: Optional[str] = None
    context: Optional[str] = None
    exact_text: Optional[str] = None
    page_number: Optional[int] = None
    confidence: float = 1.0
    marine_relevance: float = 0.5

    @property
    def extraction_hash(self) -> str:
        key = f"{self.institution_name}_{self.institution_type}_{self.role}"
        return hashlib.md5(key.encode()).hexdigest()[:16]


# =============================================================================
# NEW EXTRACTION CATEGORIES (for full knowledge system)
# =============================================================================

@dataclass
class ResearchObjectiveExtraction:
    """Research objective/aim extraction from scientific papers"""
    objective_type: str  # "research_question", "objective", "problem_statement", "hypothesis"
    objective_text: str
    study_area: Optional[str] = None
    context: Optional[str] = None
    exact_text: Optional[str] = None
    page_number: Optional[int] = None
    confidence: float = 1.0
    marine_relevance: float = 0.5
    source_file: Optional[str] = None

    @property
    def extraction_hash(self) -> str:
        key = f"{self.objective_type}_{self.objective_text[:50]}"
        return hashlib.md5(key.encode()).hexdigest()[:16]

    def to_dict(self) -> Dict:
        return {
            'objective_type': self.objective_type,
            'objective_text': self.objective_text,
            'study_area': self.study_area,
            'context': self.context[:200] if self.context else None,
            'exact_text': self.exact_text,
            'page_number': self.page_number,
            'confidence': self.confidence,
            'source_file': self.source_file,
        }


@dataclass
class ResultExtraction:
    """Research result/outcome extraction from scientific papers"""
    result_type: str  # "quantitative", "qualitative", "spatial", "statistical"
    result_text: str
    quantitative_value: Optional[str] = None  # e.g., "30% increase"
    statistical_significance: Optional[str] = None  # e.g., "p<0.05"
    related_method: Optional[str] = None
    context: Optional[str] = None
    exact_text: Optional[str] = None
    page_number: Optional[int] = None
    confidence: float = 1.0
    marine_relevance: float = 0.5
    source_file: Optional[str] = None

    @property
    def extraction_hash(self) -> str:
        key = f"{self.result_type}_{self.result_text[:50]}"
        return hashlib.md5(key.encode()).hexdigest()[:16]

    def to_dict(self) -> Dict:
        return {
            'result_type': self.result_type,
            'result_text': self.result_text,
            'quantitative_value': self.quantitative_value,
            'statistical_significance': self.statistical_significance,
            'related_method': self.related_method,
            'context': self.context[:200] if self.context else None,
            'exact_text': self.exact_text,
            'page_number': self.page_number,
            'confidence': self.confidence,
            'source_file': self.source_file,
        }


@dataclass
class ConclusionExtraction:
    """Research conclusion/implication extraction from scientific papers"""
    conclusion_type: str  # "main_conclusion", "policy_implication", "management_recommendation"
    conclusion_text: str
    evidence_strength: str = "moderate"  # "strong", "moderate", "weak", "speculative"
    target_audience: Optional[str] = None  # "policymakers", "managers", "researchers"
    context: Optional[str] = None
    exact_text: Optional[str] = None
    page_number: Optional[int] = None
    confidence: float = 1.0
    marine_relevance: float = 0.5
    source_file: Optional[str] = None

    @property
    def extraction_hash(self) -> str:
        key = f"{self.conclusion_type}_{self.conclusion_text[:50]}"
        return hashlib.md5(key.encode()).hexdigest()[:16]

    def to_dict(self) -> Dict:
        return {
            'conclusion_type': self.conclusion_type,
            'conclusion_text': self.conclusion_text,
            'evidence_strength': self.evidence_strength,
            'target_audience': self.target_audience,
            'context': self.context[:200] if self.context else None,
            'exact_text': self.exact_text,
            'page_number': self.page_number,
            'confidence': self.confidence,
            'source_file': self.source_file,
        }


@dataclass
class GapIdentifiedExtraction:
    """Research gap identified in scientific papers"""
    gap_type: str  # "data_gap", "knowledge_gap", "methodological_gap", "research_need"
    gap_description: str
    severity: str = "important"  # "critical", "important", "minor"
    proposed_solution: Optional[str] = None
    domain: Optional[str] = None  # "marine_ecology", "spatial_planning", etc.
    context: Optional[str] = None
    exact_text: Optional[str] = None
    page_number: Optional[int] = None
    confidence: float = 1.0
    marine_relevance: float = 0.5
    source_file: Optional[str] = None

    @property
    def extraction_hash(self) -> str:
        key = f"{self.gap_type}_{self.gap_description[:50]}"
        return hashlib.md5(key.encode()).hexdigest()[:16]

    def to_dict(self) -> Dict:
        return {
            'gap_type': self.gap_type,
            'gap_description': self.gap_description,
            'severity': self.severity,
            'proposed_solution': self.proposed_solution,
            'domain': self.domain,
            'context': self.context[:200] if self.context else None,
            'exact_text': self.exact_text,
            'page_number': self.page_number,
            'confidence': self.confidence,
            'source_file': self.source_file,
        }


@dataclass
class DatasetMetadata:
    """Dataset metadata extraction"""
    dataset_name: str
    data_type: str  # "bathymetry", "biodiversity", "fishing_effort", "oceanographic", "socioeconomic"
    provider: Optional[str] = None
    temporal_coverage: Optional[str] = None
    spatial_coverage: Optional[str] = None
    resolution: Optional[str] = None
    access_type: str = "unknown"  # "open", "restricted", "proprietary", "unknown"
    context: Optional[str] = None
    exact_text: Optional[str] = None
    page_number: Optional[int] = None
    confidence: float = 1.0
    marine_relevance: float = 0.5
    source_file: Optional[str] = None

    @property
    def extraction_hash(self) -> str:
        key = f"{self.dataset_name}_{self.data_type}_{self.provider}"
        return hashlib.md5(key.encode()).hexdigest()[:16]

    def to_dict(self) -> Dict:
        return {
            'dataset_name': self.dataset_name,
            'data_type': self.data_type,
            'provider': self.provider,
            'temporal_coverage': self.temporal_coverage,
            'spatial_coverage': self.spatial_coverage,
            'resolution': self.resolution,
            'access_type': self.access_type,
            'context': self.context[:200] if self.context else None,
            'exact_text': self.exact_text,
            'page_number': self.page_number,
            'confidence': self.confidence,
            'source_file': self.source_file,
        }
