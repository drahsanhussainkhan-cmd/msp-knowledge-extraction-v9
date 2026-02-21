"""
Compute recall and F1 from gold standard recall evaluation batches.
Merges batch files and computes per-category and overall metrics.
"""
import csv
import math
import sys
from pathlib import Path
from collections import defaultdict

if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

PROJECT_ROOT = Path(__file__).parent.parent
RECALL_DIR = PROJECT_ROOT / "validation_sheets_v2" / "recall_evaluation"
PRECISION_FILE = PROJECT_ROOT / "validation_results_v2" / "validation_report.txt"
OUTPUT_DIR = PROJECT_ROOT / "validation_results_v2"

# Precision values from validation (from results_summary.md)
PRECISION = {
    'species': 0.220,
    'method': 0.660,
    'stakeholder': 0.820,
    'environmental': 0.080,
    'finding': 0.380,
}


def wilson_ci(p, n, z=1.96):
    """Wilson score confidence interval."""
    if n == 0:
        return (0.0, 1.0)
    denominator = 1 + z**2 / n
    center = (p + z**2 / (2 * n)) / denominator
    spread = z * math.sqrt((p * (1 - p) + z**2 / (4 * n)) / n) / denominator
    return (max(0.0, center - spread), min(1.0, center + spread))


def main():
    # Merge all batch files
    all_rows = []
    for batch_file in sorted(RECALL_DIR.glob("gold_standard_batch*.csv")):
        with open(batch_file, 'r', encoding='utf-8-sig') as f:
            reader = csv.DictReader(f)
            for row in reader:
                all_rows.append(row)
        print(f"Loaded {batch_file.name}")

    print(f"\nTotal rows: {len(all_rows)} ({len(all_rows)//5} documents x 5 categories)")

    # Write merged file
    merged_path = RECALL_DIR / "gold_standard_merged.csv"
    with open(merged_path, 'w', newline='', encoding='utf-8-sig') as f:
        writer = csv.DictWriter(f, fieldnames=['document', 'category', 'human_count',
                                                'system_count', 'matched_count'])
        writer.writeheader()
        writer.writerows(all_rows)
    print(f"Merged file: {merged_path}")

    # Also write per-category recall files (for compute_metrics.py compatibility)
    by_category = defaultdict(list)
    for row in all_rows:
        by_category[row['category']].append(row)

    for cat, rows in by_category.items():
        cat_path = PROJECT_ROOT / "validation_sheets_v2" / f"recall_{cat}.csv"
        with open(cat_path, 'w', newline='', encoding='utf-8-sig') as f:
            writer = csv.DictWriter(f, fieldnames=['document', 'category', 'human_count',
                                                    'system_count', 'matched_count'])
            writer.writeheader()
            writer.writerows(rows)

    # Compute per-category recall
    print(f"\n{'='*80}")
    print(f"RECALL AND F1 RESULTS (10 documents, 5 categories)")
    print(f"{'='*80}\n")

    print(f"{'Category':<15} {'Human':>7} {'System':>8} {'Matched':>8} {'Recall':>8} {'95% CI':>16} {'Precision':>10} {'F1':>6}")
    print(f"{'-'*15} {'-'*7} {'-'*8} {'-'*8} {'-'*8} {'-'*16} {'-'*10} {'-'*6}")

    results = {}
    total_human = 0
    total_system = 0
    total_matched = 0

    for cat in ['species', 'method', 'stakeholder', 'environmental', 'finding']:
        rows = by_category[cat]
        h = sum(int(r['human_count']) for r in rows)
        s = sum(int(r['system_count']) for r in rows)
        m = sum(int(r['matched_count']) for r in rows)

        recall = m / h if h > 0 else 0.0
        ci = wilson_ci(recall, h)
        precision = PRECISION.get(cat, 0.0)
        f1 = 2 * precision * recall / (precision + recall) if (precision + recall) > 0 else 0.0

        results[cat] = {
            'human': h, 'system': s, 'matched': m,
            'recall': recall, 'ci': ci,
            'precision': precision, 'f1': f1
        }

        total_human += h
        total_system += s
        total_matched += m

        print(f"{cat:<15} {h:>7} {s:>8} {m:>8} {recall:>8.3f} [{ci[0]:.3f}-{ci[1]:.3f}] {precision:>10.3f} {f1:>6.3f}")

    # Macro averages
    macro_recall = sum(r['recall'] for r in results.values()) / len(results)
    macro_precision = sum(r['precision'] for r in results.values()) / len(results)
    macro_f1 = sum(r['f1'] for r in results.values()) / len(results)

    # Micro averages
    micro_recall = total_matched / total_human if total_human > 0 else 0.0
    micro_precision = sum(PRECISION.values()) / len(PRECISION)  # approx

    print(f"\n{'Macro Average':<15} {'':>7} {'':>8} {'':>8} {macro_recall:>8.3f} {'':>16} {macro_precision:>10.3f} {macro_f1:>6.3f}")
    print(f"{'Micro Recall':<15} {total_human:>7} {total_system:>8} {total_matched:>8} {micro_recall:>8.3f}")

    # Per-document breakdown
    print(f"\n\n{'='*80}")
    print(f"PER-DOCUMENT BREAKDOWN")
    print(f"{'='*80}\n")

    docs = defaultdict(lambda: defaultdict(dict))
    for row in all_rows:
        doc = row['document'][:60]
        cat = row['category']
        docs[doc][cat] = {
            'human': int(row['human_count']),
            'system': int(row['system_count']),
            'matched': int(row['matched_count'])
        }

    for doc, cats in docs.items():
        print(f"\n{doc}...")
        for cat in ['species', 'method', 'stakeholder', 'environmental', 'finding']:
            if cat in cats:
                d = cats[cat]
                r = d['matched'] / d['human'] if d['human'] > 0 else 0
                print(f"  {cat:<15}: {d['matched']:>3}/{d['human']:>3} recall={r:.2f}  (system extracted {d['system']})")

    # Write LaTeX table
    latex_path = PROJECT_ROOT / "paper_assets" / "table_recall_f1.tex"
    with open(latex_path, 'w', encoding='utf-8') as f:
        f.write("\\begin{table}[htbp]\n")
        f.write("\\centering\n")
        f.write("\\caption{Precision, recall, and F1 for five key extraction categories (10-document gold standard)}\n")
        f.write("\\label{tab:recall}\n")
        f.write("\\begin{tabular}{lrrrrr}\n")
        f.write("\\hline\n")
        f.write("Category & N (Gold) & Precision & Recall & 95\\% CI & F1 \\\\\n")
        f.write("\\hline\n")

        for cat in ['species', 'method', 'stakeholder', 'environmental', 'finding']:
            r = results[cat]
            f.write(f"{cat.capitalize()} & {r['human']} & {r['precision']:.3f} & {r['recall']:.3f} & "
                   f"[{r['ci'][0]:.3f}-{r['ci'][1]:.3f}] & {r['f1']:.3f} \\\\\n")

        f.write("\\hline\n")
        f.write(f"\\textbf{{Macro Avg}} & \\textbf{{{total_human}}} & "
               f"\\textbf{{{macro_precision:.3f}}} & \\textbf{{{macro_recall:.3f}}} & "
               f"--- & \\textbf{{{macro_f1:.3f}}} \\\\\n")
        f.write("\\hline\n")
        f.write("\\end{tabular}\n")
        f.write("\\end{table}\n")

    print(f"\n\nLaTeX table written to: {latex_path}")

    # Write markdown summary
    md_path = OUTPUT_DIR / "recall_f1_report.md"
    with open(md_path, 'w', encoding='utf-8') as f:
        f.write("# Recall and F1 Evaluation Report\n\n")
        f.write(f"**Gold standard:** 10 marine/MSP documents, 5 categories\n")
        f.write(f"**Total human-identified mentions:** {total_human}\n")
        f.write(f"**Total system extractions:** {total_system}\n")
        f.write(f"**Total true matches:** {total_matched}\n\n")

        f.write("## Per-Category Results\n\n")
        f.write("| Category | N (Gold) | Precision | Recall | 95% CI | F1 |\n")
        f.write("|----------|----------|-----------|--------|--------|----|\n")
        for cat in ['species', 'method', 'stakeholder', 'environmental', 'finding']:
            r = results[cat]
            f.write(f"| {cat.capitalize()} | {r['human']} | {r['precision']:.3f} | {r['recall']:.3f} | "
                   f"[{r['ci'][0]:.3f}-{r['ci'][1]:.3f}] | {r['f1']:.3f} |\n")
        f.write(f"| **Macro Avg** | **{total_human}** | **{macro_precision:.3f}** | "
               f"**{macro_recall:.3f}** | --- | **{macro_f1:.3f}** |\n")

        f.write("\n## Interpretation\n\n")
        f.write("- **Recall** measures what fraction of true mentions the system found\n")
        f.write("- **Precision** measures what fraction of system extractions are correct\n")
        f.write("- **F1** is the harmonic mean of precision and recall\n")

    print(f"Report written to: {md_path}")


if __name__ == '__main__':
    main()
