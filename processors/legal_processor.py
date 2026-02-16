"""
Legal Document Processor - orchestrates all legal / regulatory extractors.

Uses extractors: distance, penalty, temporal, environmental, prohibition,
species, protected_area, permit, coordinate, legal_reference
"""
from typing import Dict, List, Any


class LegalDocumentProcessor:
    """Processor for legal and regulatory documents (laws, by-laws, circulars)."""

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

        # Initialize all legal extractors
        self.extractors: Dict[str, Any] = {}

        try:
            from extractors.distance_extractor import DistanceExtractor
            self.extractors['distance'] = DistanceExtractor(
                self.keywords, self.segmenter, self.fp_filter,
                self.legal_filter, self.number_converter,
            )
        except ImportError as e:
            print(f"    [WARN] distance extractor not available: {e}")

        try:
            from extractors.penalty_extractor import PenaltyExtractor
            self.extractors['penalty'] = PenaltyExtractor(
                self.keywords, self.segmenter, self.fp_filter,
                self.legal_filter, self.number_converter,
            )
        except ImportError as e:
            print(f"    [WARN] penalty extractor not available: {e}")

        try:
            from extractors.temporal_extractor import TemporalExtractor
            self.extractors['temporal'] = TemporalExtractor(
                self.keywords, self.segmenter, self.fp_filter,
                self.legal_filter, self.number_converter,
            )
        except ImportError as e:
            print(f"    [WARN] temporal extractor not available: {e}")

        try:
            from extractors.environmental_extractor import EnvironmentalExtractor
            self.extractors['environmental'] = EnvironmentalExtractor(
                self.keywords, self.segmenter, self.fp_filter,
                self.legal_filter, self.number_converter,
            )
        except ImportError as e:
            print(f"    [WARN] environmental extractor not available: {e}")

        try:
            from extractors.prohibition_extractor import ProhibitionExtractor
            self.extractors['prohibition'] = ProhibitionExtractor(
                self.keywords, self.segmenter, self.fp_filter,
                self.legal_filter, self.number_converter,
            )
        except ImportError as e:
            print(f"    [WARN] prohibition extractor not available: {e}")

        try:
            from extractors.species_extractor import SpeciesExtractor
            self.extractors['species'] = SpeciesExtractor(
                self.keywords, self.segmenter, self.fp_filter,
                self.legal_filter, self.number_converter,
            )
        except ImportError as e:
            print(f"    [WARN] species extractor not available: {e}")

        try:
            from extractors.protected_area_extractor import ProtectedAreaExtractor
            self.extractors['protected_area'] = ProtectedAreaExtractor(
                self.keywords, self.segmenter, self.fp_filter,
                self.legal_filter, self.number_converter,
            )
        except ImportError as e:
            print(f"    [WARN] protected_area extractor not available: {e}")

        try:
            from extractors.permit_extractor import PermitExtractor
            self.extractors['permit'] = PermitExtractor(
                self.keywords, self.segmenter, self.fp_filter,
                self.legal_filter, self.number_converter,
            )
        except ImportError as e:
            print(f"    [WARN] permit extractor not available: {e}")

        try:
            from extractors.coordinate_extractor import CoordinateExtractor
            self.extractors['coordinate'] = CoordinateExtractor(
                self.keywords, self.segmenter, self.fp_filter,
                self.legal_filter, self.number_converter,
            )
        except ImportError as e:
            print(f"    [WARN] coordinate extractor not available: {e}")

        try:
            from extractors.legal_reference_extractor import LegalReferenceExtractor
            self.extractors['legal_reference'] = LegalReferenceExtractor(
                self.keywords, self.segmenter, self.fp_filter,
                self.legal_filter, self.number_converter,
            )
        except ImportError as e:
            print(f"    [WARN] legal_reference extractor not available: {e}")

        print(f"  LegalDocumentProcessor: {len(self.extractors)} extractors loaded")

    def process(self, text: str, page_texts: Dict[int, str],
                doc_type, source_file: str = "") -> Dict[str, List[Dict]]:
        """
        Run all legal extractors on the given text.

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
