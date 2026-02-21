"""
Error Analyzer - Categorize and analyze extraction errors.

After annotation, this analyzes the false positives and false negatives
to understand system limitations and produce error distribution tables
for the paper.

Usage:
    python -m validation.error_analyzer --sheets-dir validation_sheets
"""

import csv
import sys
from collections import Counter, defaultdict
from pathlib import Path
from datetime import datetime

if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")


# Standard error categories for false positives
FP_ERROR_CATEGORIES = {
    'bibliography': 'Match in reference/bibliography section',
    'author_credit': 'CRediT author contributions or author names',
    'table_header': 'Match in table header/caption, not actual content',
    'non_marine': 'Correct extraction type but not marine/MSP related',
    'wrong_category': 'Valid extraction but wrong category assigned',
    'wrong_value': 'Correct entity but wrong value/attribute extracted',
    'cross_line': 'Garbage text from regex spanning multiple lines',
    'partial_match': 'Only part of the entity captured correctly',
    'generic_term': 'Too generic (e.g., "stakeholders" without specifics)',
    'duplicate': 'Same entity already captured with different text',
    'unspecified': 'Error type not specified by annotator',
}


class ErrorAnalyzer:
    """Analyze extraction errors from annotated validation sheets."""

    def analyze_sheets(self, sheets_dir):
        """Analyze all annotated validation sheets."""
        sheets_dir = Path(sheets_dir)
        results = {}

        for csv_file in sorted(sheets_dir.glob("validate_*.csv")):
            category = csv_file.stem.replace('validate_', '')
            analysis = self._analyze_single_sheet(csv_file, category)
            if analysis:
                results[category] = analysis

        return results

    def _analyze_single_sheet(self, csv_path, category):
        """Analyze errors in a single validation sheet."""
        rows = []
        with open(csv_path, 'r', encoding='utf-8-sig') as f:
            reader = csv.DictReader(f)
            for row in reader:
                rows.append(row)

        # Separate correct and incorrect
        correct = []
        incorrect = []
        for row in rows:
            is_correct = str(row.get('is_correct', '')).strip().lower()
            if is_correct in ('y', 'yes', 'true', '1'):
                correct.append(row)
            elif is_correct in ('n', 'no', 'false', '0'):
                incorrect.append(row)

        if not correct and not incorrect:
            return None

        # Analyze error types
        error_types = Counter()
        error_examples = defaultdict(list)

        for row in incorrect:
            error_type = str(row.get('error_type', 'unspecified')).strip().lower()
            if not error_type:
                error_type = 'unspecified'
            error_types[error_type] += 1

            # Store example (first 3 per error type)
            if len(error_examples[error_type]) < 3:
                error_examples[error_type].append({
                    'exact_text': str(row.get('exact_text', ''))[:100],
                    'context': str(row.get('context', ''))[:150],
                    'source_file': row.get('source_file', ''),
                    'notes': row.get('notes', ''),
                })

        # Analyze confidence distribution of errors
        correct_confidences = [float(r.get('confidence', 0)) for r in correct if r.get('confidence')]
        incorrect_confidences = [float(r.get('confidence', 0)) for r in incorrect if r.get('confidence')]

        avg_correct_conf = sum(correct_confidences) / len(correct_confidences) if correct_confidences else 0
        avg_incorrect_conf = sum(incorrect_confidences) / len(incorrect_confidences) if incorrect_confidences else 0

        # Relevance analysis
        relevant_count = sum(1 for r in rows if str(r.get('is_relevant', '')).strip().lower() in ('y', 'yes'))
        irrelevant_count = sum(1 for r in rows if str(r.get('is_relevant', '')).strip().lower() in ('n', 'no'))

        return {
            'total_annotated': len(correct) + len(incorrect),
            'correct': len(correct),
            'incorrect': len(incorrect),
            'precision': len(correct) / (len(correct) + len(incorrect)) if (len(correct) + len(incorrect)) > 0 else 0,
            'error_types': dict(error_types),
            'error_examples': dict(error_examples),
            'avg_confidence_correct': round(avg_correct_conf, 3),
            'avg_confidence_incorrect': round(avg_incorrect_conf, 3),
            'relevant': relevant_count,
            'irrelevant': irrelevant_count,
        }

    def generate_error_report(self, results, output_path=None):
        """Generate a detailed error analysis report."""
        lines = []
        lines.append("=" * 80)
        lines.append("ERROR ANALYSIS REPORT")
        lines.append(f"Generated: {datetime.now().isoformat()}")
        lines.append("=" * 80)

        # Overall error distribution
        all_errors = Counter()
        for cat_data in results.values():
            for error_type, count in cat_data.get('error_types', {}).items():
                all_errors[error_type] += count

        total_errors = sum(all_errors.values())
        total_correct = sum(d['correct'] for d in results.values())
        total_annotated = sum(d['total_annotated'] for d in results.values())

        lines.append(f"\nOVERALL: {total_correct}/{total_annotated} correct "
                      f"({total_correct/total_annotated*100:.1f}% precision)")
        lines.append(f"Total false positives: {total_errors}")

        lines.append("\n\n1. ERROR TYPE DISTRIBUTION (ALL CATEGORIES)")
        lines.append("-" * 60)
        lines.append(f"{'Error Type':<30} {'Count':>6} {'%':>7} Description")
        lines.append("-" * 60)
        for error_type, count in all_errors.most_common():
            pct = count / total_errors * 100 if total_errors > 0 else 0
            desc = FP_ERROR_CATEGORIES.get(error_type, '')
            lines.append(f"{error_type:<30} {count:>6} {pct:>6.1f}% {desc}")

        # Per-category breakdown
        lines.append("\n\n2. PER-CATEGORY ERROR BREAKDOWN")
        lines.append("-" * 60)

        for cat in sorted(results.keys()):
            data = results[cat]
            lines.append(f"\n  {cat.upper()} (precision: {data['precision']:.3f})")
            lines.append(f"  Correct: {data['correct']}, Incorrect: {data['incorrect']}")
            lines.append(f"  Avg confidence (correct): {data['avg_confidence_correct']:.3f}")
            lines.append(f"  Avg confidence (incorrect): {data['avg_confidence_incorrect']:.3f}")

            if data['error_types']:
                lines.append(f"  Error types:")
                for et, count in sorted(data['error_types'].items(), key=lambda x: -x[1]):
                    lines.append(f"    - {et}: {count}")

            # Show examples of errors
            if data['error_examples']:
                lines.append(f"  Error examples:")
                for et, examples in data['error_examples'].items():
                    for ex in examples[:2]:
                        lines.append(f"    [{et}] \"{ex['exact_text']}\"")
                        if ex.get('notes'):
                            lines.append(f"           Notes: {ex['notes']}")

        # Confidence analysis
        lines.append("\n\n3. CONFIDENCE SCORE ANALYSIS")
        lines.append("-" * 60)
        lines.append("Can confidence scores distinguish correct from incorrect extractions?")
        lines.append(f"{'Category':<20} {'Avg Conf (TP)':>15} {'Avg Conf (FP)':>15} {'Delta':>8}")
        lines.append("-" * 60)
        for cat in sorted(results.keys()):
            data = results[cat]
            delta = data['avg_confidence_correct'] - data['avg_confidence_incorrect']
            lines.append(
                f"{cat:<20} {data['avg_confidence_correct']:>15.3f} "
                f"{data['avg_confidence_incorrect']:>15.3f} {delta:>+8.3f}"
            )

        # Recommendations
        lines.append("\n\n4. IMPROVEMENT RECOMMENDATIONS")
        lines.append("-" * 60)

        # Find most common error types
        if all_errors:
            top_error = all_errors.most_common(1)[0]
            lines.append(f"  - Most common error: '{top_error[0]}' ({top_error[1]} occurrences)")
            lines.append(f"    Recommendation: Focus filtering improvements on this error type")

        # Find worst category
        if results:
            worst_cat = min(results.items(), key=lambda x: x[1]['precision'])
            lines.append(f"  - Lowest precision: '{worst_cat[0]}' ({worst_cat[1]['precision']:.3f})")
            lines.append(f"    Recommendation: Review and tighten patterns for this category")

        report = '\n'.join(lines)

        if output_path:
            Path(output_path).parent.mkdir(parents=True, exist_ok=True)
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(report)

        return report


def main():
    import argparse
    parser = argparse.ArgumentParser(description='Analyze extraction errors')
    parser.add_argument('--sheets-dir', default=str(Path(__file__).parent.parent / 'validation_sheets'))
    parser.add_argument('--output', default=str(Path(__file__).parent.parent / 'validation_results' / 'error_analysis.txt'))
    args = parser.parse_args()

    analyzer = ErrorAnalyzer()
    print("Analyzing annotated validation sheets...")
    results = analyzer.analyze_sheets(args.sheets_dir)

    if not results:
        print("No annotated sheets found. Please annotate first.")
        sys.exit(1)

    report = analyzer.generate_error_report(results, args.output)
    print(report)
    print(f"\nSaved to: {args.output}")


if __name__ == '__main__':
    main()
