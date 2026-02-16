"""
Dataset Processor - minimal processor for dataset documents.

Currently uses only data_source and species extractors.
Additional dataset-specific extractors can be added later.
"""
from typing import Dict, List, Any


class DatasetProcessor:
    """Processor for dataset / data-catalogue documents."""

    def __init__(self):
        # Initialize shared utilities
        from utils import (
            MSPKeywords,
            TurkishLegalSentenceSegmenter,
            FalsePositiveFilter,
            LegalReferenceFilter,
            MultilingualNumberConverter,
        )

        self.keywords = MSPKeywords()
        self.segmenter = TurkishLegalSentenceSegmenter()
        self.fp_filter = FalsePositiveFilter()
        self.legal_filter = LegalReferenceFilter()
        self.number_converter = MultilingualNumberConverter()

        # Initialize dataset extractors
        self.extractors: Dict[str, Any] = {}

        try:
            from extractors.data_source_extractor import DataSourceExtractor
            self.extractors['data_source'] = DataSourceExtractor(
                self.keywords, self.segmenter, self.fp_filter,
                self.legal_filter, self.number_converter,
            )
        except ImportError as e:
            print(f"    [WARN] data_source extractor not available: {e}")

        try:
            from extractors.species_extractor import SpeciesExtractor
            self.extractors['species'] = SpeciesExtractor(
                self.keywords, self.segmenter, self.fp_filter,
                self.legal_filter, self.number_converter,
            )
        except ImportError as e:
            print(f"    [WARN] species extractor not available: {e}")

        print(f"  DatasetProcessor: {len(self.extractors)} extractors loaded")

    def process(self, text: str, page_texts: Dict[int, str],
                doc_type, source_file: str = "") -> Dict[str, List[Dict]]:
        """
        Run dataset extractors on the given text.

        Args:
            text: Full document text.
            page_texts: Dict mapping page number -> page text.
            doc_type: DocumentType enum value.
            source_file: Optional source filename for logging.

        Returns:
            Dict of category name -> list of extraction dicts.
        """
        results: Dict[str, List[Dict]] = {}

        for name, extractor in self.extractors.items():
            try:
                extractions = extractor.extract(text, page_texts, doc_type)
                results[name] = [self._to_dict(e) for e in extractions]
                print(f"    {name}: {len(extractions)} found")
            except Exception as e:
                print(f"    {name}: ERROR - {e}")
                results[name] = []

        return results

    @staticmethod
    def _to_dict(extraction) -> Dict:
        """Convert an extraction dataclass instance to a plain dict."""
        if hasattr(extraction, 'to_dict'):
            return extraction.to_dict()
        from dataclasses import asdict
        return asdict(extraction)
