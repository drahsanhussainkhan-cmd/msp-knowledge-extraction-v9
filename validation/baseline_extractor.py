"""
Baseline Extractor - Simple keyword matching for comparison.

This provides a naive baseline to compare against our regex-based system.
Uses flat keyword lists with no context filtering, no marine relevance scoring,
no false positive filtering, and no deduplication.

This is intentionally simple - it demonstrates the value of our system's
sophisticated filtering pipeline.
"""

import re
import sys
from typing import Dict, List, Set
from pathlib import Path

if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")


class BaselineExtractor:
    """Simple keyword-matching baseline for comparison."""

    def __init__(self):
        self._build_keyword_lists()

    def _build_keyword_lists(self):
        """Build flat keyword lists per category."""

        # Species: common marine species names
        self.species_keywords = {
            # Fish
            'tuna', 'salmon', 'cod', 'herring', 'anchovy', 'sardine', 'mackerel',
            'swordfish', 'shark', 'ray', 'skate', 'grouper', 'snapper', 'bass',
            'haddock', 'halibut', 'sole', 'flounder', 'eel', 'sturgeon',
            # Mammals
            'whale', 'dolphin', 'porpoise', 'seal', 'sea lion', 'walrus',
            'manatee', 'dugong', 'otter',
            # Reptiles
            'sea turtle', 'turtle', 'loggerhead', 'leatherback',
            # Invertebrates
            'coral', 'sponge', 'mussel', 'oyster', 'clam', 'shrimp', 'prawn',
            'crab', 'lobster', 'octopus', 'squid', 'jellyfish', 'sea urchin',
            'starfish', 'sea cucumber',
            # Plants/algae
            'seagrass', 'kelp', 'mangrove', 'algae', 'phytoplankton', 'zooplankton',
            # Turkish
            'balina', 'yunus', 'fok', 'deniz kaplumbağası', 'mercan',
            'levrek', 'hamsi', 'palamut', 'orkinos',
        }

        # Methods: research method keywords
        self.method_keywords = {
            'gis', 'marxan', 'zonation', 'maxent', 'invest',
            'remote sensing', 'satellite', 'habitat mapping',
            'survey', 'questionnaire', 'interview',
            'ecosystem-based management', 'ecosystem based management', 'ebm',
            'multi-criteria', 'multi criteria', 'mca', 'delphi',
            'cost-benefit', 'cost benefit', 'cba',
            'stakeholder analysis', 'stakeholder engagement',
            'spatial analysis', 'spatial planning',
            'cumulative impact', 'cumulative effect',
            'environmental impact assessment', 'eia',
            'suitability analysis', 'overlap analysis',
            'scenario analysis', 'scenario planning',
            'statistical analysis', 'regression', 'correlation',
            'participatory mapping', 'participatory planning',
        }

        # Stakeholders: stakeholder type keywords
        self.stakeholder_keywords = {
            'stakeholder', 'stakeholders',
            'local community', 'local communities',
            'fishermen', 'fishers', 'fishing community',
            'coastal community', 'coastal communities',
            'tourism industry', 'tourism sector',
            'shipping industry', 'shipping sector',
            'port authority', 'port authorities',
            'government agency', 'government agencies',
            'ministry', 'department', 'authority',
            'ngo', 'ngos', 'non-governmental',
            'indigenous', 'aboriginal',
            'aquaculture', 'fish farmers',
            'recreational users', 'recreational fishers',
            # Turkish
            'paydaş', 'paydaşlar', 'yerel halk', 'balıkçılar',
            'bakanlık', 'müdürlük',
        }

        # Environmental: environmental condition keywords
        self.environmental_keywords = {
            'water quality', 'air quality',
            'dissolved oxygen', 'salinity', 'temperature', 'ph',
            'turbidity', 'chlorophyll', 'nutrients',
            'pollution', 'contamination', 'eutrophication',
            'ocean acidification', 'acidification',
            'noise pollution', 'underwater noise',
            'oil spill', 'oil pollution',
            'heavy metals', 'microplastics',
            'habitat degradation', 'habitat loss',
            'biodiversity loss',
            'emission', 'discharge',
            # Turkish
            'su kalitesi', 'kirlilik', 'çevre kirliliği',
        }

        # Findings: finding indicator keywords
        self.finding_keywords = {
            'results show', 'results indicate', 'results suggest',
            'we found', 'we observed', 'we identified',
            'analysis revealed', 'analysis showed',
            'significant increase', 'significant decrease',
            'significant difference', 'significant correlation',
            'statistically significant',
            'trend', 'pattern', 'relationship',
            'p < 0.05', 'p < 0.01', 'p < 0.001',
            'confidence interval',
        }

    def extract_all(self, text: str) -> Dict[str, List[str]]:
        """Extract all categories from text using simple keyword matching."""
        results = {}
        results['species'] = self._match_keywords(text, self.species_keywords)
        results['method'] = self._match_keywords(text, self.method_keywords)
        results['stakeholder'] = self._match_keywords(text, self.stakeholder_keywords)
        results['environmental'] = self._match_keywords(text, self.environmental_keywords)
        results['finding'] = self._match_keywords(text, self.finding_keywords)
        return results

    def _match_keywords(self, text: str, keywords: Set[str]) -> List[str]:
        """Find all keyword matches in text (case-insensitive, no dedup)."""
        matches = []
        text_lower = text.lower()
        for keyword in keywords:
            # Find all occurrences
            start = 0
            while True:
                idx = text_lower.find(keyword, start)
                if idx == -1:
                    break
                # Extract the matched text with original case
                matched = text[idx:idx + len(keyword)]
                matches.append(matched)
                start = idx + 1
        return matches

    def extract_from_file(self, pdf_path: str) -> Dict[str, List[str]]:
        """Extract from a PDF file."""
        try:
            sys.path.insert(0, str(Path(__file__).parent.parent))
            from utils.pdf_parser import extract_text_from_pdf
            text, page_texts = extract_text_from_pdf(pdf_path)
            return self.extract_all(text)
        except Exception as e:
            print(f"  Error processing {pdf_path}: {e}")
            return {}


def run_baseline_on_corpus(research_dir: str, legal_dir: str, output_path: str = None):
    """Run baseline extraction on the full corpus and report results."""
    from collections import Counter

    baseline = BaselineExtractor()
    all_results = {}
    category_totals = Counter()

    # Process research papers
    research_path = Path(research_dir)
    if research_path.exists():
        pdfs = sorted(research_path.glob("*.pdf"))
        print(f"Processing {len(pdfs)} research papers...")
        for i, pdf in enumerate(pdfs, 1):
            if i % 50 == 0:
                print(f"  [{i}/{len(pdfs)}]...")
            results = baseline.extract_from_file(str(pdf))
            all_results[pdf.name] = results
            for cat, matches in results.items():
                category_totals[cat] += len(matches)

    # Process legal documents
    legal_path = Path(legal_dir)
    if legal_path.exists():
        pdfs = sorted(legal_path.glob("*.pdf"))
        print(f"Processing {len(pdfs)} legal documents...")
        for pdf in pdfs:
            results = baseline.extract_from_file(str(pdf))
            all_results[pdf.name] = results
            for cat, matches in results.items():
                category_totals[cat] += len(matches)

    print(f"\nBaseline Results:")
    for cat, count in category_totals.most_common():
        print(f"  {cat}: {count}")
    print(f"  TOTAL: {sum(category_totals.values())}")

    if output_path:
        import json
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump({
                'totals': dict(category_totals),
                'per_document': all_results,
            }, f, indent=2, ensure_ascii=False)
        print(f"\nSaved to: {output_path}")

    return all_results, category_totals


if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser(description='Run baseline keyword extraction')
    parser.add_argument('--research-dir', required=True)
    parser.add_argument('--legal-dir', required=True)
    parser.add_argument('--output', default='validation_sheets/baseline_results.json')
    args = parser.parse_args()

    run_baseline_on_corpus(args.research_dir, args.legal_dir, args.output)
