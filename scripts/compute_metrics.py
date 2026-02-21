"""
Compute validation metrics from annotated CSV sheets.

After you've annotated the validation_sheets/validate_*.csv files
(filling in is_correct column with 'y' or 'n'), run this script
to compute precision, recall, F1 for each category.

Usage:
    python scripts/compute_metrics.py
    python scripts/compute_metrics.py --sheets-dir validation_sheets
    python scripts/compute_metrics.py --sheets-dir validation_sheets --annotator-2-dir validation_sheets_annotator2
"""

import csv
import json
import math
import os
import sys
from collections import defaultdict, Counter
from pathlib import Path
from datetime import datetime

if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

PROJECT_ROOT = Path(__file__).parent.parent
DEFAULT_SHEETS_DIR = PROJECT_ROOT / "validation_sheets"
DEFAULT_OUTPUT_DIR = PROJECT_ROOT / "validation_results"


def load_annotated_csv(csv_path):
    """Load an annotated validation CSV and return rows."""
    rows = []
    with open(csv_path, 'r', encoding='utf-8-sig') as f:
        reader = csv.DictReader(f)
        for row in reader:
            rows.append(row)
    return rows


def compute_precision_from_sheet(rows):
    """
    Compute precision from a validation sheet.

    Precision = correct extractions / total extractions sampled
    Each row is a system extraction; is_correct tells us if it's a TP or FP.
    """
    total = 0
    correct = 0
    incorrect = 0
    unannotated = 0
    error_types = Counter()

    for row in rows:
        is_correct = str(row.get('is_correct', '')).strip().lower()
        if is_correct in ('y', 'yes', 'true', '1'):
            correct += 1
            total += 1
        elif is_correct in ('n', 'no', 'false', '0'):
            incorrect += 1
            total += 1
            # Track error types
            error_type = str(row.get('error_type', '')).strip()
            if error_type:
                error_types[error_type] += 1
            else:
                error_types['unspecified'] += 1
        else:
            unannotated += 1

    precision = correct / total if total > 0 else 0.0

    return {
        'total_annotated': total,
        'correct': correct,
        'incorrect': incorrect,
        'unannotated': unannotated,
        'precision': precision,
        'error_types': dict(error_types),
    }


def compute_wilson_ci(p, n, z=1.96):
    """
    Wilson score confidence interval for a proportion.
    More accurate than normal approximation for small samples.
    """
    if n == 0:
        return (0.0, 0.0)
    denominator = 1 + z**2 / n
    center = (p + z**2 / (2 * n)) / denominator
    spread = z * math.sqrt((p * (1 - p) + z**2 / (4 * n)) / n) / denominator
    return (max(0.0, center - spread), min(1.0, center + spread))


def compute_recall_from_sheet(csv_path):
    """
    Compute recall from a recall annotation sheet.

    Recall sheets have columns: document, category, human_count, system_count, matched_count
    Recall = sum(matched) / sum(human_count)
    """
    rows = []
    with open(csv_path, 'r', encoding='utf-8-sig') as f:
        reader = csv.DictReader(f)
        for row in reader:
            rows.append(row)

    total_human = 0
    total_matched = 0

    for row in rows:
        human = int(row.get('human_count', 0))
        matched = int(row.get('matched_count', 0))
        total_human += human
        total_matched += matched

    recall = total_matched / total_human if total_human > 0 else 0.0
    return {
        'total_human': total_human,
        'total_matched': total_matched,
        'recall': recall,
        'recall_ci': compute_wilson_ci(recall, total_human),
    }


def compute_f1(precision, recall):
    """Compute F1 score from precision and recall."""
    if precision + recall == 0:
        return 0.0
    return 2 * precision * recall / (precision + recall)


def compute_cohens_kappa(annotations_1, annotations_2):
    """
    Compute Cohen's Kappa inter-annotator agreement.

    Args:
        annotations_1: list of 'y'/'n' from annotator 1
        annotations_2: list of 'y'/'n' from annotator 2

    Returns:
        kappa score (-1 to 1), where >= 0.70 is acceptable
    """
    if len(annotations_1) != len(annotations_2):
        return None

    n = len(annotations_1)
    if n == 0:
        return None

    # Count agreements
    agree = sum(1 for a, b in zip(annotations_1, annotations_2) if a == b)
    po = agree / n  # observed agreement

    # Count marginals
    a1_y = sum(1 for a in annotations_1 if a == 'y')
    a2_y = sum(1 for a in annotations_2 if a == 'y')
    a1_n = n - a1_y
    a2_n = n - a2_y

    # Expected agreement by chance
    pe = (a1_y * a2_y + a1_n * a2_n) / (n * n)

    if pe == 1.0:
        return 1.0  # perfect agreement

    kappa = (po - pe) / (1 - pe)
    return kappa


def process_all_sheets(sheets_dir, annotator2_dir=None):
    """Process all validation sheets and compute metrics."""
    sheets_dir = Path(sheets_dir)
    results = {}

    for csv_file in sorted(sheets_dir.glob("validate_*.csv")):
        category = csv_file.stem.replace('validate_', '')
        rows = load_annotated_csv(csv_file)

        # Check if any annotations exist
        has_annotations = any(
            str(row.get('is_correct', '')).strip().lower() in ('y', 'yes', 'n', 'no', 'true', 'false', '1', '0')
            for row in rows
        )

        if not has_annotations:
            print(f"  {category}: NOT ANNOTATED (skipping)")
            continue

        metrics = compute_precision_from_sheet(rows)

        # Confidence interval
        ci_low, ci_high = compute_wilson_ci(metrics['precision'], metrics['total_annotated'])
        metrics['precision_ci_low'] = ci_low
        metrics['precision_ci_high'] = ci_high

        # Inter-annotator agreement if second annotator provided
        if annotator2_dir:
            a2_path = Path(annotator2_dir) / csv_file.name
            if a2_path.exists():
                rows2 = load_annotated_csv(a2_path)
                ann1 = [str(r.get('is_correct', '')).strip().lower() for r in rows
                        if str(r.get('is_correct', '')).strip().lower() in ('y', 'n')]
                ann2 = [str(r.get('is_correct', '')).strip().lower() for r in rows2
                        if str(r.get('is_correct', '')).strip().lower() in ('y', 'n')]
                # Normalize to same length
                min_len = min(len(ann1), len(ann2))
                if min_len > 0:
                    kappa = compute_cohens_kappa(ann1[:min_len], ann2[:min_len])
                    metrics['inter_annotator_kappa'] = kappa

        # Load recall data if available
        recall_path = sheets_dir / f"recall_{category}.csv"
        if recall_path.exists():
            recall_data = compute_recall_from_sheet(str(recall_path))
            metrics['recall'] = recall_data['recall']
            metrics['recall_ci'] = recall_data['recall_ci']
            metrics['f1'] = compute_f1(metrics['precision'], metrics['recall'])

        results[category] = metrics
        status = f"P={metrics['precision']:.3f} [{ci_low:.3f}-{ci_high:.3f}]"
        status += f" ({metrics['correct']}/{metrics['total_annotated']})"
        if 'recall' in metrics:
            status += f" R={metrics['recall']:.3f} F1={metrics['f1']:.3f}"
        if 'inter_annotator_kappa' in metrics:
            status += f" kappa={metrics['inter_annotator_kappa']:.3f}"
        print(f"  {category}: {status}")

    return results


def compute_overall_metrics(per_category):
    """Compute macro and micro averaged precision."""
    if not per_category:
        return {}

    precisions = [v['precision'] for v in per_category.values()]
    total_correct = sum(v['correct'] for v in per_category.values())
    total_annotated = sum(v['total_annotated'] for v in per_category.values())

    macro_precision = sum(precisions) / len(precisions) if precisions else 0
    micro_precision = total_correct / total_annotated if total_annotated > 0 else 0

    macro_ci = compute_wilson_ci(macro_precision, len(precisions) * 50)
    micro_ci = compute_wilson_ci(micro_precision, total_annotated)

    # Recall/F1 averages (only for categories that have recall data)
    recalls = [v['recall'] for v in per_category.values() if 'recall' in v]
    f1s = [v['f1'] for v in per_category.values() if 'f1' in v]
    macro_recall = sum(recalls) / len(recalls) if recalls else None
    macro_f1 = sum(f1s) / len(f1s) if f1s else None

    result = {
        'macro_precision': macro_precision,
        'macro_precision_ci': macro_ci,
        'micro_precision': micro_precision,
        'micro_precision_ci': micro_ci,
        'total_correct': total_correct,
        'total_annotated': total_annotated,
        'categories_evaluated': len(per_category),
    }

    if macro_recall is not None:
        result['macro_recall'] = macro_recall
        result['macro_f1'] = macro_f1
        result['categories_with_recall'] = len(recalls)

    return result


def generate_report(per_category, overall, output_path=None):
    """Generate a publication-ready validation report."""
    lines = []
    lines.append("=" * 80)
    lines.append("EXTRACTION VALIDATION REPORT")
    lines.append(f"Generated: {datetime.now().isoformat()}")
    lines.append("=" * 80)

    # Per-category table
    lines.append("")
    lines.append(f"{'Category':<20} {'Prec':>7} {'95% CI':>15} {'TP':>5} {'FP':>5} {'N':>5}")
    lines.append("-" * 80)

    for cat in sorted(per_category.keys()):
        m = per_category[cat]
        ci = f"[{m['precision_ci_low']:.3f}-{m['precision_ci_high']:.3f}]"
        lines.append(
            f"{cat:<20} {m['precision']:>7.3f} {ci:>15} "
            f"{m['correct']:>5} {m['incorrect']:>5} {m['total_annotated']:>5}"
        )

    lines.append("-" * 80)
    lines.append(
        f"{'MACRO AVERAGE':<20} {overall['macro_precision']:>7.3f} "
        f"[{overall['macro_precision_ci'][0]:.3f}-{overall['macro_precision_ci'][1]:.3f}]"
    )
    lines.append(
        f"{'MICRO AVERAGE':<20} {overall['micro_precision']:>7.3f} "
        f"[{overall['micro_precision_ci'][0]:.3f}-{overall['micro_precision_ci'][1]:.3f}]"
    )
    lines.append("=" * 80)

    # Error analysis summary
    all_errors = Counter()
    for m in per_category.values():
        for error_type, count in m.get('error_types', {}).items():
            all_errors[error_type] += count

    if all_errors:
        lines.append("\nERROR TYPE DISTRIBUTION")
        lines.append("-" * 40)
        total_errors = sum(all_errors.values())
        for error_type, count in all_errors.most_common():
            pct = count / total_errors * 100
            lines.append(f"  {error_type:<25} {count:>4} ({pct:.1f}%)")

    # Inter-annotator agreement
    kappas = {cat: m['inter_annotator_kappa']
              for cat, m in per_category.items()
              if 'inter_annotator_kappa' in m}
    if kappas:
        lines.append("\nINTER-ANNOTATOR AGREEMENT (Cohen's Kappa)")
        lines.append("-" * 40)
        for cat, kappa in sorted(kappas.items()):
            level = "excellent" if kappa >= 0.80 else "good" if kappa >= 0.60 else "moderate" if kappa >= 0.40 else "poor"
            lines.append(f"  {cat:<20} kappa={kappa:.3f} ({level})")
        avg_kappa = sum(kappas.values()) / len(kappas)
        lines.append(f"  {'AVERAGE':<20} kappa={avg_kappa:.3f}")

    # Determine if any categories have recall data
    has_recall = any('recall' in m for m in per_category.values())

    # LaTeX table
    lines.append("\n\nLATEX TABLE (copy into paper)")
    lines.append("-" * 60)
    lines.append("\\begin{table}[htbp]")
    lines.append("\\centering")
    lines.append("\\caption{Extraction validation results}")
    lines.append("\\label{tab:validation}")
    if has_recall:
        lines.append("\\begin{tabular}{lcccccc}")
        lines.append("\\hline")
        lines.append("Category & N & TP & Precision & 95\\% CI & Recall & F1 \\\\")
    else:
        lines.append("\\begin{tabular}{lcccc}")
        lines.append("\\hline")
        lines.append("Category & N & TP & Precision & 95\\% CI \\\\")
    lines.append("\\hline")
    for cat in sorted(per_category.keys()):
        m = per_category[cat]
        row = (
            f"{cat.replace('_', ' ').title()} & {m['total_annotated']} & {m['correct']} & "
            f"{m['precision']:.3f} & [{m['precision_ci_low']:.3f}--{m['precision_ci_high']:.3f}]"
        )
        if has_recall:
            r = f"{m['recall']:.3f}" if 'recall' in m else '--'
            f1 = f"{m['f1']:.3f}" if 'f1' in m else '--'
            row += f" & {r} & {f1}"
        lines.append(row + " \\\\")
    lines.append("\\hline")
    macro_row = (
        f"Macro Average & {overall['total_annotated']} & {overall['total_correct']} & "
        f"{overall['macro_precision']:.3f} & "
        f"[{overall['macro_precision_ci'][0]:.3f}--{overall['macro_precision_ci'][1]:.3f}]"
    )
    if has_recall and 'macro_recall' in overall:
        macro_row += f" & {overall['macro_recall']:.3f} & {overall['macro_f1']:.3f}"
    elif has_recall:
        macro_row += " & -- & --"
    lines.append(macro_row + " \\\\")
    lines.append("\\hline")
    lines.append("\\end{tabular}")
    lines.append("\\end{table}")

    # Markdown table
    lines.append("\n\nMARKDOWN TABLE")
    lines.append("-" * 60)
    lines.append("| Category | N | TP | FP | Precision | 95% CI |")
    lines.append("|----------|---|----|----|-----------|--------|")
    for cat in sorted(per_category.keys()):
        m = per_category[cat]
        lines.append(
            f"| {cat} | {m['total_annotated']} | {m['correct']} | {m['incorrect']} | "
            f"{m['precision']:.3f} | [{m['precision_ci_low']:.3f}-{m['precision_ci_high']:.3f}] |"
        )
    lines.append(
        f"| **Macro Avg** | {overall['total_annotated']} | {overall['total_correct']} | "
        f"{overall['total_annotated'] - overall['total_correct']} | "
        f"**{overall['macro_precision']:.3f}** | "
        f"[{overall['macro_precision_ci'][0]:.3f}-{overall['macro_precision_ci'][1]:.3f}] |"
    )

    report = '\n'.join(lines)

    if output_path:
        Path(output_path).parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(report)

    return report


def main():
    import argparse
    parser = argparse.ArgumentParser(description='Compute validation metrics from annotated sheets')
    parser.add_argument('--sheets-dir', default=str(DEFAULT_SHEETS_DIR),
                        help='Directory with annotated validate_*.csv files')
    parser.add_argument('--annotator-2-dir', default=None,
                        help='Directory with second annotator sheets (for inter-annotator agreement)')
    parser.add_argument('--output-dir', default=str(DEFAULT_OUTPUT_DIR),
                        help='Output directory for validation results')
    args = parser.parse_args()

    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    print("=" * 60)
    print("VALIDATION METRICS COMPUTATION")
    print("=" * 60)
    print(f"\nLoading annotated sheets from: {args.sheets_dir}")

    # Compute per-category metrics
    per_category = process_all_sheets(args.sheets_dir, args.annotator_2_dir)

    if not per_category:
        print("\nERROR: No annotated sheets found!")
        print("Please annotate the validation_sheets/validate_*.csv files first.")
        print("Fill in the 'is_correct' column with 'y' or 'n' for each row.")
        sys.exit(1)

    # Overall metrics
    overall = compute_overall_metrics(per_category)

    print(f"\nOverall:")
    print(f"  Macro Precision: {overall['macro_precision']:.3f}")
    print(f"  Micro Precision: {overall['micro_precision']:.3f}")
    print(f"  Categories: {overall['categories_evaluated']}")

    # Generate report
    report_path = output_dir / "validation_report.txt"
    report = generate_report(per_category, overall, str(report_path))
    print(f"\nReport saved to: {report_path}")
    print(report)

    # Save detailed JSON
    detailed = {
        'timestamp': datetime.now().isoformat(),
        'per_category': per_category,
        'overall': overall,
    }
    json_path = output_dir / "validation_detailed.json"
    with open(json_path, 'w', encoding='utf-8') as f:
        json.dump(detailed, f, indent=2, ensure_ascii=False)
    print(f"Detailed results: {json_path}")


if __name__ == '__main__':
    main()
