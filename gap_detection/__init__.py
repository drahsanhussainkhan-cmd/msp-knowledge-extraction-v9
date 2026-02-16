"""
Gap detection system for MSP knowledge base.

Detects gaps within and across research, legal, and data sources.
"""

from .research_gaps import ResearchGapDetector
from .legal_gaps import LegalGapDetector
from .data_gaps import DataGapDetector
from .integration_gaps import IntegrationGapDetector
from .gap_prioritizer import GapPrioritizer

__all__ = [
    'ResearchGapDetector',
    'LegalGapDetector',
    'DataGapDetector',
    'IntegrationGapDetector',
    'GapPrioritizer',
]
