"""
Enumerations for MSP Extractor
"""
from enum import Enum


class DocumentType(Enum):
    """Document type classification."""
    LEGAL_TURKISH = "legal_turkish"
    LEGAL_ENGLISH = "legal_english"
    SCIENTIFIC_ENGLISH = "scientific_english"
    SCIENTIFIC_TURKISH = "scientific_turkish"
    UNKNOWN = "unknown"


class ExtractionCategory(Enum):
    """Extraction categories - 17 total."""
    DISTANCE = "distance"
    ENVIRONMENTAL = "environmental"
    TEMPORAL = "temporal"
    PENALTY = "penalty"
    PERMIT = "permit"
    PROTECTED_AREA = "protected_area"
    PROHIBITION = "prohibition"
    COORDINATE = "coordinate"
    SPECIES = "species"
    STAKEHOLDER = "stakeholder"
    CONFLICT = "conflict"
    METHOD = "method"
    FINDING = "finding"
    POLICY = "policy"
    DATA_SOURCE = "data_source"
    LEGAL_REFERENCE = "legal_reference"
    INSTITUTION = "institution"


class QualifierType(Enum):
    """Distance/value qualifier types."""
    MINIMUM = "minimum"
    MAXIMUM = "maximum"
    EXACTLY = "exactly"
    APPROXIMATELY = "approximately"
    GREATER_THAN = "greater_than"
    LESS_THAN = "less_than"
    BETWEEN = "between"
