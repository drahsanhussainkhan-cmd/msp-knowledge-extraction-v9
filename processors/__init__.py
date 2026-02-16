"""
Processors module - orchestrate extractors for different document types.

Each processor initializes shared utilities once and runs the appropriate
set of extractors for its document category.
"""

from .q1_paper_processor import Q1PaperProcessor
from .legal_processor import LegalDocumentProcessor
from .dataset_processor import DatasetProcessor

__all__ = [
    'Q1PaperProcessor',
    'LegalDocumentProcessor',
    'DatasetProcessor',
]
