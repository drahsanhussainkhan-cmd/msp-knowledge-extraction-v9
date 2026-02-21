"""
Generate publication-ready tables and figures for the paper.

Reads validation results, ablation results, and extraction statistics
to produce LaTeX tables, markdown tables, and HTML charts.

Usage:
    python scripts/generate_paper_tables.py
    python scripts/generate_paper_tables.py --validation-dir validation_results --output-dir paper_assets
"""

import json
import os
import sys
from collections import Counter, defaultdict
from pathlib import Path
from datetime import datetime

if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

PROJECT_ROOT = Path(__file__).parent.parent


def load_json_safe(path):
    """Load JSON file if exists, return None otherwise."""
    if Path(path).exists():
        with open(path, 'r', encoding='utf-8') as f:
            return json.load(f)
    return None


def load_extraction_stats(results_json_path):
    """Load extraction statistics from raw results."""
    data = load_json_safe(results_json_path)
    if not data:
        return {}

    cat_counts = Counter()
    doc_count = 0
    for doc_name, categories in data.items():
        if isinstance(categories, dict):
            doc_count += 1
            for cat, items in categories.items():
                if isinstance(items, list):
                    cat_counts[cat] += len(items)

    return {
        'total_documents': doc_count,
        'total_extractions': sum(cat_counts.values()),
        'per_category': dict(cat_counts.most_common()),
    }


def generate_table1_extraction_summary(stats, output_path):
    """Table 1: Extraction results summary."""
    lines = []

    # LaTeX
    lines.append("% Table 1: Extraction Results Summary")
    lines.append("\\begin{table*}[htbp]")
    lines.append("\\centering")
    lines.append("\\caption{Extraction results from 273 MSP documents (25 Turkish legal + 248 Q1 research papers)}")
    lines.append("\\label{tab:extraction_results}")
    lines.append("\\begin{tabular}{llrp{5cm}}")
    lines.append("\\hline")
    lines.append("\\textbf{Category} & \\textbf{Source} & \\textbf{Count} & \\textbf{Description} \\\\")
    lines.append("\\hline")

    descriptions = {
        'finding': ('Research', 'Research findings and statistical results'),
        'data_source': ('Research', 'Datasets, monitoring stations, surveys'),
        'institution': ('Both', 'Named institutions and organizations'),
        'legal_reference': ('Legal', 'Law numbers, regulation citations'),
        'stakeholder': ('Research', 'Stakeholder groups and role mentions'),
        'species': ('Both', 'Marine species (145 unique)'),
        'policy': ('Research', 'Policy references and frameworks'),
        'method': ('Research', 'Research methods (13 classified types)'),
        'environmental': ('Both', 'Water quality, pollution, noise parameters'),
        'gap': ('Research', 'Research gaps identified in papers'),
        'result': ('Research', 'Quantitative and qualitative results'),
        'distance': ('Legal', 'Buffer zones and distance restrictions'),
        'conflict': ('Research', 'Use-use and use-environment conflicts'),
        'prohibition': ('Legal', 'Activity bans in protected zones'),
        'protected_area': ('Legal', 'MPA designations, Natura 2000 sites'),
        'objective': ('Research', 'Research aims and study objectives'),
        'temporal': ('Legal', 'Seasonal restrictions, date ranges'),
        'conclusion': ('Research', 'Study conclusions with evidence strength'),
        'penalty': ('Legal', 'Fines and imprisonment terms'),
        'permit': ('Legal', 'License requirements, EIA mandates'),
        'coordinate': ('Legal', 'Geographic boundaries of zones'),
    }

    for cat, count in stats.get('per_category', {}).items():
        source, desc = descriptions.get(cat, ('Both', ''))
        name = cat.replace('_', ' ').title()
        lines.append(f"{name} & {source} & {count:,} & {desc} \\\\")

    lines.append("\\hline")
    lines.append(f"\\textbf{{Total}} & & \\textbf{{{stats.get('total_extractions', 0):,}}} & \\\\")
    lines.append("\\hline")
    lines.append("\\end{tabular}")
    lines.append("\\end{table*}")

    with open(output_path, 'w', encoding='utf-8') as f:
        f.write('\n'.join(lines))
    return lines


def generate_table2_gap_detection(gaps_path, output_path):
    """Table 2: Gap detection results."""
    lines = []
    gaps = load_json_safe(gaps_path)
    if not gaps:
        # Try loading from gap report or CSV
        return ["% No gap data available"]

    lines.append("% Table 2: Gap Detection Results")
    lines.append("\\begin{table}[htbp]")
    lines.append("\\centering")
    lines.append("\\caption{Cross-source gap detection results}")
    lines.append("\\label{tab:gap_detection}")
    lines.append("\\begin{tabular}{llrl}")
    lines.append("\\hline")
    lines.append("\\textbf{Detector} & \\textbf{Gap Type} & \\textbf{Count} & \\textbf{Severity} \\\\")
    lines.append("\\hline")

    if isinstance(gaps, list):
        type_counts = Counter()
        category_counts = Counter()
        severity_counts = Counter()
        for gap in gaps:
            gt = gap.get('gap_type', 'unknown')
            gc = gap.get('gap_category', 'unknown')
            gs = gap.get('severity', 'unknown')
            type_counts[gt] += 1
            category_counts[gc] += 1
            severity_counts[gs] += 1

        for gap_type, count in type_counts.most_common():
            name = gap_type.replace('_', ' ').title()
            lines.append(f"{name} & & {count} & \\\\")

    lines.append("\\hline")
    lines.append("\\end{tabular}")
    lines.append("\\end{table}")

    with open(output_path, 'w', encoding='utf-8') as f:
        f.write('\n'.join(lines))
    return lines


def generate_chart_html(stats, validation_data, output_path):
    """Generate an HTML page with Chart.js publication figures."""
    categories = list(stats.get('per_category', {}).keys())
    counts = list(stats.get('per_category', {}).values())

    # Validation data for precision chart
    val_categories = []
    val_precisions = []
    if validation_data and 'per_category' in validation_data:
        for cat, data in sorted(validation_data['per_category'].items()):
            val_categories.append(cat)
            val_precisions.append(data.get('precision', 0))

    html = f"""<!DOCTYPE html>
<html>
<head>
<meta charset="UTF-8">
<title>MSP System - Publication Figures</title>
<script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
<style>
  body {{ font-family: Arial, sans-serif; max-width: 1000px; margin: 40px auto; }}
  .chart-container {{ margin: 30px 0; padding: 20px; border: 1px solid #ddd; }}
  h2 {{ color: #2c3e50; }}
  .instructions {{ background: #f8f9fa; padding: 15px; border-radius: 5px; margin: 20px 0; }}
</style>
</head>
<body>
<h1>MSP Knowledge Extraction - Publication Figures</h1>
<div class="instructions">
  <strong>How to use:</strong> Open this in Chrome/Edge, right-click each chart,
  select "Save image as..." to get PNG files for your paper. Or use browser print to PDF.
</div>

<div class="chart-container">
  <h2>Figure 1: Extraction Distribution by Category</h2>
  <canvas id="chart1" height="400"></canvas>
</div>

<div class="chart-container">
  <h2>Figure 2: Precision by Category (after validation)</h2>
  <canvas id="chart2" height="400"></canvas>
</div>

<script>
// Figure 1: Extraction counts
new Chart(document.getElementById('chart1'), {{
  type: 'bar',
  data: {{
    labels: {json.dumps([c.replace('_', ' ').title() for c in categories])},
    datasets: [{{
      label: 'Extractions',
      data: {json.dumps(counts)},
      backgroundColor: 'rgba(41, 128, 185, 0.7)',
      borderColor: 'rgba(41, 128, 185, 1)',
      borderWidth: 1
    }}]
  }},
  options: {{
    responsive: true,
    indexAxis: 'y',
    plugins: {{
      title: {{ display: true, text: 'Extraction count by category (N={stats.get("total_extractions", 0):,})', font: {{size: 16}} }},
      legend: {{ display: false }}
    }},
    scales: {{
      x: {{ title: {{ display: true, text: 'Number of extractions' }} }}
    }}
  }}
}});

// Figure 2: Precision
{"" if not val_categories else f'''
new Chart(document.getElementById('chart2'), {{
  type: 'bar',
  data: {{
    labels: {json.dumps([c.replace('_', ' ').title() for c in val_categories])},
    datasets: [{{
      label: 'Precision',
      data: {json.dumps(val_precisions)},
      backgroundColor: val_precisions.map(v => v >= 0.8 ? 'rgba(39, 174, 96, 0.7)' : v >= 0.6 ? 'rgba(243, 156, 18, 0.7)' : 'rgba(231, 76, 60, 0.7)'),
      borderWidth: 1
    }}]
  }},
  options: {{
    responsive: true,
    plugins: {{
      title: {{ display: true, text: 'Precision by extraction category', font: {{size: 16}} }},
      legend: {{ display: false }}
    }},
    scales: {{
      y: {{ min: 0, max: 1, title: {{ display: true, text: 'Precision' }} }},
      x: {{ title: {{ display: true, text: 'Category' }} }}
    }}
  }}
}});
'''}

{"" if val_categories else '''
document.getElementById('chart2').parentElement.innerHTML += '<p style="color: #e74c3c;"><em>Validation data not yet available. Run compute_metrics.py after annotation.</em></p>';
'''}
</script>
</body>
</html>"""

    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(html)


def generate_markdown_summary(stats, validation_data, output_path):
    """Generate a markdown summary of all results."""
    lines = []
    lines.append("# MSP Knowledge Extraction - Results Summary\n")
    lines.append(f"Generated: {datetime.now().strftime('%Y-%m-%d')}\n")

    # Extraction summary
    lines.append("## Extraction Results\n")
    lines.append(f"- **Documents processed:** {stats.get('total_documents', 0)}")
    lines.append(f"- **Total extractions:** {stats.get('total_extractions', 0):,}")
    lines.append(f"- **Categories:** {len(stats.get('per_category', {}))}\n")

    lines.append("| Category | Count |")
    lines.append("|----------|-------|")
    for cat, count in stats.get('per_category', {}).items():
        lines.append(f"| {cat.replace('_', ' ').title()} | {count:,} |")
    lines.append(f"| **Total** | **{stats.get('total_extractions', 0):,}** |")

    # Validation results if available
    if validation_data and 'per_category' in validation_data:
        lines.append("\n## Validation Results (Precision)\n")
        lines.append("| Category | N | TP | FP | Precision | 95% CI |")
        lines.append("|----------|---|----|----|-----------|--------|")
        for cat, data in sorted(validation_data['per_category'].items()):
            lines.append(
                f"| {cat} | {data['total_annotated']} | {data['correct']} | "
                f"{data['incorrect']} | {data['precision']:.3f} | "
                f"[{data.get('precision_ci_low', 0):.3f}-{data.get('precision_ci_high', 0):.3f}] |"
            )

        overall = validation_data.get('overall', {})
        if overall:
            lines.append(f"\n- **Macro Precision:** {overall.get('macro_precision', 0):.3f}")
            lines.append(f"- **Micro Precision:** {overall.get('micro_precision', 0):.3f}")

    with open(output_path, 'w', encoding='utf-8') as f:
        f.write('\n'.join(lines))


def main():
    import argparse
    parser = argparse.ArgumentParser(description='Generate publication tables and figures')
    parser.add_argument('--results-json', default=None,
                        help='Path to raw_results JSON')
    parser.add_argument('--validation-dir', default=str(PROJECT_ROOT / 'validation_results'),
                        help='Directory with validation results')
    parser.add_argument('--output-dir', default=str(PROJECT_ROOT / 'paper_assets'),
                        help='Output directory for paper assets')
    args = parser.parse_args()

    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    # Find results JSON
    if args.results_json:
        results_json = args.results_json
    else:
        candidates = sorted((PROJECT_ROOT / 'output_final2').glob('raw_results_*.json'), reverse=True)
        results_json = str(candidates[0]) if candidates else None

    print("=" * 60)
    print("GENERATING PUBLICATION ASSETS")
    print("=" * 60)

    # Load extraction stats
    stats = {}
    if results_json:
        print(f"\nLoading extraction results: {results_json}")
        stats = load_extraction_stats(results_json)
        print(f"  {stats.get('total_documents', 0)} documents, {stats.get('total_extractions', 0):,} extractions")

    # Load validation results (if available)
    validation_data = load_json_safe(Path(args.validation_dir) / 'validation_detailed.json')
    if validation_data:
        print(f"  Validation data loaded ({len(validation_data.get('per_category', {}))} categories)")
    else:
        print("  No validation data yet (run compute_metrics.py after annotation)")

    # Generate Table 1: Extraction summary
    print("\nGenerating Table 1: Extraction summary...")
    generate_table1_extraction_summary(stats, str(output_dir / 'table1_extractions.tex'))
    print(f"  -> {output_dir / 'table1_extractions.tex'}")

    # Generate charts
    print("Generating figures (HTML with Chart.js)...")
    generate_chart_html(stats, validation_data, str(output_dir / 'figures.html'))
    print(f"  -> {output_dir / 'figures.html'}")

    # Generate markdown summary
    print("Generating markdown summary...")
    generate_markdown_summary(stats, validation_data, str(output_dir / 'results_summary.md'))
    print(f"  -> {output_dir / 'results_summary.md'}")

    print(f"\nAll assets saved to: {output_dir}")
    print("\nTo get images for the paper:")
    print(f"  1. Open {output_dir / 'figures.html'} in Chrome/Edge")
    print(f"  2. Right-click each chart > Save image as PNG")
    print(f"  3. Copy LaTeX tables from .tex files into your paper")


if __name__ == '__main__':
    main()
