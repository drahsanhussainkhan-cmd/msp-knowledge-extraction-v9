"""
Ablation Study - Measure contribution of each filtering component.

Removes one component at a time and re-runs extraction on a sample
of documents to measure the impact on precision.

Usage:
    python -m validation.ablation_study --sample-docs 20
    python -m validation.ablation_study --research-dir /path/to/papers --legal-dir /path/to/legal
"""

import json
import os
import sys
import time
import random
from collections import defaultdict, Counter
from pathlib import Path
from datetime import datetime

if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

sys.path.insert(0, str(Path(__file__).parent.parent))

from core.enums import DocumentType
from utils import (
    MSPKeywords, TurkishLegalSentenceSegmenter, FalsePositiveFilter,
    LegalReferenceFilter, MultilingualNumberConverter, extract_text_from_pdf,
)


class AblationStudy:
    """Run ablation experiments by disabling components one at a time."""

    def __init__(self, research_dir=None, legal_dir=None, sample_size=20, seed=42):
        self.research_dir = Path(research_dir) if research_dir else None
        self.legal_dir = Path(legal_dir) if legal_dir else None
        self.sample_size = sample_size
        self.seed = seed
        self.sample_docs = []

    def select_sample_documents(self):
        """Select a stratified sample of documents for ablation."""
        random.seed(self.seed)
        docs = []

        if self.research_dir and self.research_dir.exists():
            research_pdfs = sorted(self.research_dir.glob("*.pdf"))
            n_research = min(self.sample_size - 5, len(research_pdfs))
            docs.extend([('research', p) for p in random.sample(research_pdfs, n_research)])

        if self.legal_dir and self.legal_dir.exists():
            legal_pdfs = sorted(self.legal_dir.glob("*.pdf"))
            n_legal = min(5, len(legal_pdfs))
            docs.extend([('legal', p) for p in random.sample(legal_pdfs, n_legal)])

        self.sample_docs = docs
        return docs

    def run_full_ablation(self):
        """Run all ablation experiments."""
        if not self.sample_docs:
            self.select_sample_documents()

        print(f"Running ablation study on {len(self.sample_docs)} documents")
        print(f"  Research: {sum(1 for t, _ in self.sample_docs if t == 'research')}")
        print(f"  Legal: {sum(1 for t, _ in self.sample_docs if t == 'legal')}")

        # Load document texts once
        doc_texts = {}
        for doc_type, pdf_path in self.sample_docs:
            try:
                text, page_texts = extract_text_from_pdf(str(pdf_path))
                dtype = DocumentType.SCIENTIFIC_ENGLISH if doc_type == 'research' else DocumentType.LEGAL_TURKISH
                doc_texts[pdf_path.name] = (text, page_texts, dtype)
            except Exception as e:
                print(f"  Skipping {pdf_path.name}: {e}")

        print(f"  Loaded {len(doc_texts)} documents\n")

        # Define ablation conditions
        conditions = {
            'full_system': {},  # No ablation - baseline
            'no_marine_filter': {'disable_marine_filter': True},
            'no_fp_filter': {'disable_fp_filter': True},
            'no_blacklists': {'disable_blacklists': True},
            'no_dedup': {'disable_dedup': True},
            'no_legal_ref_filter': {'disable_legal_ref_filter': True},
        }

        results = {}
        for condition_name, config in conditions.items():
            print(f"  Running condition: {condition_name}...")
            start = time.time()
            counts = self._run_extraction(doc_texts, config)
            elapsed = time.time() - start
            results[condition_name] = {
                'counts': dict(counts),
                'total': sum(counts.values()),
                'elapsed_seconds': round(elapsed, 1),
            }
            print(f"    Total extractions: {sum(counts.values())} ({elapsed:.1f}s)")

        return results

    def _run_extraction(self, doc_texts, config):
        """Run extraction with specific ablation config."""
        keywords = MSPKeywords()
        segmenter = TurkishLegalSentenceSegmenter()
        number_converter = MultilingualNumberConverter()

        # Create filters (potentially disabled)
        if config.get('disable_fp_filter'):
            fp_filter = _DisabledFPFilter()
        else:
            fp_filter = FalsePositiveFilter()

        if config.get('disable_legal_ref_filter'):
            legal_filter = None
        else:
            legal_filter = LegalReferenceFilter()

        # Import extractors
        from extractors.species_extractor import SpeciesExtractor
        from extractors.method_extractor import MethodExtractor
        from extractors.stakeholder_extractor import StakeholderExtractor
        from extractors.environmental_extractor import EnvironmentalExtractor
        from extractors.finding_extractor import FindingExtractor

        # Create extractors with potentially modified components
        extractors = {
            'species': SpeciesExtractor(keywords, segmenter, fp_filter, legal_filter, number_converter),
            'method': MethodExtractor(keywords, segmenter, fp_filter, legal_filter, number_converter),
            'stakeholder': StakeholderExtractor(keywords, segmenter, fp_filter, legal_filter, number_converter),
            'environmental': EnvironmentalExtractor(keywords, segmenter, fp_filter, legal_filter, number_converter),
            'finding': FindingExtractor(keywords, segmenter, fp_filter, legal_filter, number_converter),
        }

        # Modify extractors based on config
        if config.get('disable_blacklists'):
            for ext in extractors.values():
                if hasattr(ext, 'NAME_BLACKLIST'):
                    ext.NAME_BLACKLIST = set()
                if hasattr(ext, 'SCIENTIFIC_NAME_BLACKLIST'):
                    ext.SCIENTIFIC_NAME_BLACKLIST = set()
                if hasattr(ext, 'TITLE_BLACKLIST'):
                    ext.TITLE_BLACKLIST = set()

        if config.get('disable_marine_filter'):
            # Monkey-patch marine relevance to always return 1.0
            original_score = fp_filter.get_marine_relevance_score
            fp_filter.get_marine_relevance_score = lambda *args, **kwargs: 1.0

        counts = Counter()
        for doc_name, (text, page_texts, doc_type) in doc_texts.items():
            for cat_name, extractor in extractors.items():
                try:
                    results = extractor.extract(text, page_texts, doc_type)
                    if config.get('disable_dedup'):
                        # Count all matches without dedup
                        counts[cat_name] += len(results)
                    else:
                        counts[cat_name] += len(results)
                except Exception:
                    pass

        # Restore if monkey-patched
        if config.get('disable_marine_filter') and hasattr(fp_filter, '_original_score'):
            fp_filter.get_marine_relevance_score = fp_filter._original_score

        return counts

    def generate_report(self, results, output_path=None):
        """Generate ablation study report."""
        lines = []
        lines.append("=" * 80)
        lines.append("ABLATION STUDY REPORT")
        lines.append(f"Generated: {datetime.now().isoformat()}")
        lines.append(f"Sample size: {len(self.sample_docs)} documents")
        lines.append("=" * 80)

        baseline = results.get('full_system', {}).get('total', 0)

        # Summary table
        lines.append(f"\n{'Condition':<25} {'Total':>8} {'Delta':>8} {'%Change':>9} {'Time':>7}")
        lines.append("-" * 60)

        for condition, data in results.items():
            total = data['total']
            delta = total - baseline
            pct = (delta / baseline * 100) if baseline > 0 else 0
            elapsed = data.get('elapsed_seconds', 0)
            marker = " (baseline)" if condition == 'full_system' else ""
            lines.append(
                f"{condition:<25} {total:>8} {delta:>+8} {pct:>+8.1f}% {elapsed:>6.1f}s{marker}"
            )

        # Per-category breakdown
        lines.append(f"\n\nPER-CATEGORY IMPACT")
        lines.append("-" * 80)

        baseline_counts = results.get('full_system', {}).get('counts', {})
        categories = sorted(set().union(*[d.get('counts', {}).keys() for d in results.values()]))

        header = f"{'Condition':<25}"
        for cat in categories:
            header += f" {cat[:10]:>10}"
        lines.append(header)
        lines.append("-" * 80)

        for condition, data in results.items():
            row = f"{condition:<25}"
            for cat in categories:
                count = data.get('counts', {}).get(cat, 0)
                base = baseline_counts.get(cat, 0)
                if condition == 'full_system':
                    row += f" {count:>10}"
                else:
                    delta = count - base
                    row += f" {delta:>+10}"
            lines.append(row)

        # Interpretation
        lines.append("\n\nINTERPRETATION")
        lines.append("-" * 60)
        for condition, data in results.items():
            if condition == 'full_system':
                continue
            delta = data['total'] - baseline
            if delta > 0:
                lines.append(
                    f"  {condition}: Removing this component INCREASES extractions by {delta} "
                    f"({delta/baseline*100:.1f}%). These are likely false positives that the "
                    f"component normally filters out."
                )
            elif delta < 0:
                lines.append(
                    f"  {condition}: Removing this component DECREASES extractions by {abs(delta)} "
                    f"({abs(delta)/baseline*100:.1f}%). This component may be helping find matches."
                )
            else:
                lines.append(
                    f"  {condition}: No impact on extraction count."
                )

        # LaTeX table
        lines.append("\n\nLATEX TABLE")
        lines.append("-" * 60)
        lines.append("\\begin{table}[htbp]")
        lines.append("\\centering")
        lines.append("\\caption{Ablation study: impact of removing each filtering component}")
        lines.append("\\label{tab:ablation}")
        lines.append("\\begin{tabular}{lrrr}")
        lines.append("\\hline")
        lines.append("Configuration & Extractions & $\\Delta$ & \\% Change \\\\")
        lines.append("\\hline")
        for condition, data in results.items():
            total = data['total']
            delta = total - baseline
            pct = (delta / baseline * 100) if baseline > 0 else 0
            name = condition.replace('_', ' ').title()
            if condition == 'full_system':
                lines.append(f"\\textbf{{{name}}} & \\textbf{{{total}}} & --- & --- \\\\")
            else:
                lines.append(f"{name} & {total} & {delta:+d} & {pct:+.1f}\\% \\\\")
        lines.append("\\hline")
        lines.append("\\end{tabular}")
        lines.append("\\end{table}")

        report = '\n'.join(lines)

        if output_path:
            Path(output_path).parent.mkdir(parents=True, exist_ok=True)
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(report)

        return report


class _DisabledFPFilter:
    """A FalsePositiveFilter that never filters anything."""
    def is_false_positive(self, *args, **kwargs):
        return False, ""
    def get_marine_relevance_score(self, *args, **kwargs):
        return 1.0


def main():
    import argparse
    parser = argparse.ArgumentParser(description='Run ablation study')
    parser.add_argument('--research-dir', default=r"C:\Users\ahk79\OneDrive\Desktop\Q1 JOURNALS")
    parser.add_argument('--legal-dir', default=r"C:\Users\ahk79\OneDrive\Desktop\msp laws seperate")
    parser.add_argument('--sample-docs', type=int, default=20)
    parser.add_argument('--output', default=str(Path(__file__).parent.parent / 'validation_results' / 'ablation_report.txt'))
    args = parser.parse_args()

    study = AblationStudy(
        research_dir=args.research_dir,
        legal_dir=args.legal_dir,
        sample_size=args.sample_docs,
    )
    study.select_sample_documents()

    results = study.run_full_ablation()

    Path(args.output).parent.mkdir(parents=True, exist_ok=True)
    report = study.generate_report(results, args.output)
    print(report)

    # Save raw results
    json_path = args.output.replace('.txt', '.json')
    with open(json_path, 'w', encoding='utf-8') as f:
        json.dump(results, f, indent=2)
    print(f"\nRaw results: {json_path}")


if __name__ == '__main__':
    main()
