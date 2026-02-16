"""
Q1 Paper Processor - orchestrates all research-oriented extractors on a scientific paper.

Uses extractors: stakeholder, institution, conflict, method, finding,
policy, data_source, objective, result, conclusion, gap
"""
from typing import Dict, List, Any


class Q1PaperProcessor:
    """Processor for Q1 scientific / research papers."""

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

        # Initialize all research extractors
        self.extractors: Dict[str, Any] = {}

        # --- Extractors that already exist ---
        try:
            from extractors.stakeholder_extractor import StakeholderExtractor
            self.extractors['stakeholder'] = StakeholderExtractor(
                self.keywords, self.segmenter, self.fp_filter,
                self.legal_filter, self.number_converter,
            )
        except ImportError as e:
            print(f"    [WARN] stakeholder extractor not available: {e}")

        try:
            from extractors.institution_extractor import InstitutionExtractor
            self.extractors['institution'] = InstitutionExtractor(
                self.keywords, self.segmenter, self.fp_filter,
                self.legal_filter, self.number_converter,
            )
        except ImportError as e:
            print(f"    [WARN] institution extractor not available: {e}")

        try:
            from extractors.conflict_extractor import ConflictExtractor
            self.extractors['conflict'] = ConflictExtractor(
                self.keywords, self.segmenter, self.fp_filter,
                self.legal_filter, self.number_converter,
            )
        except ImportError as e:
            print(f"    [WARN] conflict extractor not available: {e}")

        try:
            from extractors.method_extractor import MethodExtractor
            self.extractors['method'] = MethodExtractor(
                self.keywords, self.segmenter, self.fp_filter,
                self.legal_filter, self.number_converter,
            )
        except ImportError as e:
            print(f"    [WARN] method extractor not available: {e}")

        try:
            from extractors.finding_extractor import FindingExtractor
            self.extractors['finding'] = FindingExtractor(
                self.keywords, self.segmenter, self.fp_filter,
                self.legal_filter, self.number_converter,
            )
        except ImportError as e:
            print(f"    [WARN] finding extractor not available: {e}")

        try:
            from extractors.policy_extractor import PolicyExtractor
            self.extractors['policy'] = PolicyExtractor(
                self.keywords, self.segmenter, self.fp_filter,
                self.legal_filter, self.number_converter,
            )
        except ImportError as e:
            print(f"    [WARN] policy extractor not available: {e}")

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

        try:
            from extractors.environmental_extractor import EnvironmentalExtractor
            self.extractors['environmental'] = EnvironmentalExtractor(
                self.keywords, self.segmenter, self.fp_filter,
                self.legal_filter, self.number_converter,
            )
        except ImportError as e:
            print(f"    [WARN] environmental extractor not available: {e}")

        # --- Extractors that may not exist yet ---
        try:
            from extractors.objective_extractor import ObjectiveExtractor
            self.extractors['objective'] = ObjectiveExtractor(
                self.keywords, self.segmenter, self.fp_filter,
                self.legal_filter, self.number_converter,
            )
        except ImportError as e:
            print(f"    [WARN] objective extractor not available: {e}")

        try:
            from extractors.result_extractor import ResultExtractor
            self.extractors['result'] = ResultExtractor(
                self.keywords, self.segmenter, self.fp_filter,
                self.legal_filter, self.number_converter,
            )
        except ImportError as e:
            print(f"    [WARN] result extractor not available: {e}")

        try:
            from extractors.conclusion_extractor import ConclusionExtractor
            self.extractors['conclusion'] = ConclusionExtractor(
                self.keywords, self.segmenter, self.fp_filter,
                self.legal_filter, self.number_converter,
            )
        except ImportError as e:
            print(f"    [WARN] conclusion extractor not available: {e}")

        try:
            from extractors.gap_extractor import GapExtractor
            self.extractors['gap'] = GapExtractor(
                self.keywords, self.segmenter, self.fp_filter,
                self.legal_filter, self.number_converter,
            )
        except ImportError as e:
            print(f"    [WARN] gap extractor not available: {e}")

        print(f"  Q1PaperProcessor: {len(self.extractors)} extractors loaded")

    def process(self, text: str, page_texts: Dict[int, str],
                doc_type, source_file: str = "") -> Dict[str, List[Dict]]:
        """
        Run all research extractors on the given text.

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
        """Convert an extraction dataclass instance to a plain dict.

        Handles both new-style dataclasses with a ``to_dict`` helper and
        older dataclasses that rely on ``dataclasses.asdict``.
        """
        if hasattr(extraction, 'to_dict'):
            return extraction.to_dict()
        # Fallback for old-style dataclasses
        from dataclasses import asdict
        return asdict(extraction)
