"""
Generate validation annotation sheets from extraction results.

Creates CSV files with random samples for human review.
Each row has the extraction data + blank columns for annotation.

Usage:
    python scripts/generate_validation_sheets.py
    python scripts/generate_validation_sheets.py --results-json path/to/raw_results.json
    python scripts/generate_validation_sheets.py --sample-size 100
"""

import csv
import json
import os
import random
import sys
from collections import defaultdict
from pathlib import Path

# Fix Windows encoding
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

# Project root
PROJECT_ROOT = Path(__file__).parent.parent
DEFAULT_RESULTS = PROJECT_ROOT / "output_final3"
DEFAULT_OUTPUT = PROJECT_ROOT / "validation_sheets"

# Key fields to show per category (the most informative field for each)
CATEGORY_KEY_FIELDS = {
    'species': ['species_name', 'scientific_name', 'common_name', 'protection_status'],
    'method': ['method_type', 'description', 'tools_used'],
    'stakeholder': ['stakeholder_name', 'stakeholder_type', 'role'],
    'environmental': ['condition_type', 'description', 'value', 'unit'],
    'finding': ['finding_type', 'description', 'quantitative_result'],
    'institution': ['institution_name', 'institution_type', 'role', 'jurisdiction'],
    'conflict': ['conflict_type', 'activity_1', 'activity_2', 'severity'],
    'policy': ['policy_type', 'title', 'scope'],
    'data_source': ['source_type', 'source_name', 'spatial_coverage', 'temporal_coverage'],
    'distance': ['activity', 'value', 'unit', 'reference_point'],
    'penalty': ['penalty_type', 'amount', 'currency', 'violation'],
    'temporal': ['restriction_type', 'start_date', 'end_date', 'activity'],
    'prohibition': ['prohibition_type', 'activity', 'scope'],
    'permit': ['permit_type', 'issuing_authority', 'activity'],
    'protected_area': ['area_type', 'name', 'designation'],
    'legal_reference': ['reference_type', 'law_number', 'article_number', 'title'],
    'coordinate': ['latitude', 'longitude', 'location_description'],
    'objective': ['objective_type', 'objective_text'],
    'result': ['result_type', 'result_text', 'quantitative_value'],
    'conclusion': ['conclusion_type', 'conclusion_text', 'evidence_strength'],
    'gap': ['gap_type', 'gap_description', 'severity'],
}

# Minimum extractions to create a validation sheet
MIN_EXTRACTIONS = 5


def find_results_json(results_dir):
    """Find the raw_results JSON file."""
    results_dir = Path(results_dir)
    for f in sorted(results_dir.glob("raw_results_*.json"), reverse=True):
        return f
    for f in sorted(results_dir.glob("*.json"), reverse=True):
        return f
    return None


def load_results(json_path):
    """Load raw results and aggregate by category."""
    with open(json_path, 'r', encoding='utf-8') as f:
        data = json.load(f)

    # Format: {doc_name: {category: [extractions]}}
    by_category = defaultdict(list)

    for doc_name, categories in data.items():
        if not isinstance(categories, dict):
            continue
        for category, items in categories.items():
            if not isinstance(items, list):
                continue
            for item in items:
                if isinstance(item, dict):
                    item['_source_file'] = doc_name
                    by_category[category].append(item)

    return dict(by_category)


def create_validation_csv(extractions, category, output_path, sample_size=50, seed=42):
    """Create a validation CSV for one category."""
    random.seed(seed)

    if len(extractions) <= sample_size:
        sample = extractions[:]
    else:
        sample = random.sample(extractions, sample_size)

    # Determine columns
    key_fields = CATEGORY_KEY_FIELDS.get(category, [])
    common_fields = ['exact_text', 'context', 'page_number', 'confidence', 'marine_relevance']
    annotation_fields = ['is_correct', 'is_relevant', 'error_type', 'notes']

    # Build header
    header = ['id', 'source_file'] + key_fields + common_fields + annotation_fields

    rows = []
    for i, ext in enumerate(sample, 1):
        row = {'id': i, 'source_file': ext.get('_source_file', '')}

        for field in key_fields:
            val = ext.get(field, '')
            if isinstance(val, list):
                val = '; '.join(str(v) for v in val)
            row[field] = str(val)[:200] if val else ''

        row['exact_text'] = str(ext.get('exact_text', ''))[:300]
        row['context'] = str(ext.get('context', ''))[:200]
        row['page_number'] = ext.get('page_number', '')
        row['confidence'] = round(ext.get('confidence', 0), 3)
        row['marine_relevance'] = round(ext.get('marine_relevance', 0), 3)

        # Blank annotation fields
        row['is_correct'] = ''
        row['is_relevant'] = ''
        row['error_type'] = ''
        row['notes'] = ''

        rows.append(row)

    # Write CSV
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    with open(output_path, 'w', newline='', encoding='utf-8-sig') as f:
        writer = csv.DictWriter(f, fieldnames=header)
        writer.writeheader()
        writer.writerows(rows)

    return len(rows)


def create_recall_sample_list(all_results, output_dir, num_docs=10, seed=42):
    """
    Create a list of documents for recall evaluation.

    For recall, the annotator reads the FULL document and marks ALL
    relevant extractions, then we compare with what the system found.
    """
    random.seed(seed)
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    # Get documents that have extractions across multiple categories
    doc_richness = {}
    for doc_name, categories in all_results.items():
        if isinstance(categories, dict):
            total = sum(len(items) for items in categories.values() if isinstance(items, list))
            doc_richness[doc_name] = total

    # Select documents with moderate extraction counts (not too few, not too many)
    sorted_docs = sorted(doc_richness.items(), key=lambda x: x[1])
    # Pick from the middle range (25th to 75th percentile)
    n = len(sorted_docs)
    mid_range = sorted_docs[n // 4: 3 * n // 4]
    if len(mid_range) > num_docs:
        selected = random.sample(mid_range, num_docs)
    else:
        selected = mid_range

    # Write recall document list
    recall_path = output_dir / "recall_documents.csv"
    with open(recall_path, 'w', newline='', encoding='utf-8-sig') as f:
        writer = csv.writer(f)
        writer.writerow(['document', 'system_extraction_count', 'instructions'])
        for doc_name, count in selected:
            writer.writerow([
                doc_name, count,
                'Read this PDF fully. For each category (species, method, stakeholder, environmental, finding), '
                'list ALL mentions you find. Compare with system extractions.'
            ])

    # Also write what the system found for these documents
    for doc_name, count in selected:
        doc_results = all_results.get(doc_name, {})
        doc_path = output_dir / f"recall_system_{doc_name.replace('.pdf', '')}.csv"

        rows = []
        for cat, items in doc_results.items():
            if isinstance(items, list):
                for item in items:
                    rows.append({
                        'category': cat,
                        'exact_text': str(item.get('exact_text', ''))[:200],
                        'page_number': item.get('page_number', ''),
                        'confidence': round(item.get('confidence', 0), 3),
                        'system_found': 'yes',
                        'annotator_agrees': '',  # blank for annotator
                    })

        if rows:
            with open(doc_path, 'w', newline='', encoding='utf-8-sig') as f:
                writer = csv.DictWriter(f, fieldnames=['category', 'exact_text', 'page_number',
                                                        'confidence', 'system_found', 'annotator_agrees'])
                writer.writeheader()
                writer.writerows(rows)

    return len(selected)


def main():
    import argparse
    parser = argparse.ArgumentParser(description='Generate validation annotation sheets')
    parser.add_argument('--results-dir', default=str(DEFAULT_RESULTS),
                        help='Directory with raw_results JSON')
    parser.add_argument('--results-json', default=None,
                        help='Direct path to raw_results JSON')
    parser.add_argument('--output-dir', default=str(DEFAULT_OUTPUT),
                        help='Output directory for validation sheets')
    parser.add_argument('--sample-size', type=int, default=50,
                        help='Number of samples per category')
    parser.add_argument('--seed', type=int, default=42,
                        help='Random seed for reproducibility')
    args = parser.parse_args()

    # Find results
    if args.results_json:
        json_path = Path(args.results_json)
    else:
        json_path = find_results_json(args.results_dir)

    if not json_path or not json_path.exists():
        print(f"ERROR: No results JSON found in {args.results_dir}")
        sys.exit(1)

    print(f"Loading results from: {json_path}")

    # Load raw results (doc -> categories format)
    with open(json_path, 'r', encoding='utf-8') as f:
        raw_data = json.load(f)

    # Aggregate by category for validation sheets
    by_category = load_results(json_path)

    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    print(f"\nGenerating validation sheets (sample_size={args.sample_size}, seed={args.seed})")
    print(f"Output: {output_dir}\n")

    total_sheets = 0
    total_samples = 0

    # Sort by count descending
    for category, extractions in sorted(by_category.items(), key=lambda x: -len(x[1])):
        if len(extractions) < MIN_EXTRACTIONS:
            print(f"  {category}: SKIPPED ({len(extractions)} < {MIN_EXTRACTIONS} minimum)")
            continue

        csv_path = output_dir / f"validate_{category}.csv"
        n_samples = create_validation_csv(
            extractions, category, csv_path,
            sample_size=args.sample_size, seed=args.seed
        )
        total_sheets += 1
        total_samples += n_samples
        print(f"  {category}: {n_samples} samples from {len(extractions)} total -> {csv_path.name}")

    # Generate recall sample list
    print(f"\nGenerating recall evaluation documents...")
    recall_dir = output_dir / "recall_evaluation"
    n_recall_docs = create_recall_sample_list(raw_data, recall_dir, num_docs=10, seed=args.seed)
    print(f"  Selected {n_recall_docs} documents for recall evaluation")

    # Summary
    print(f"\n{'='*60}")
    print(f"VALIDATION SHEETS GENERATED")
    print(f"  Categories: {total_sheets}")
    print(f"  Total samples: {total_samples}")
    print(f"  Output directory: {output_dir}")
    print(f"  Recall documents: {recall_dir}")
    print(f"{'='*60}")

    print(f"\nNEXT STEPS:")
    print(f"  1. Open each validate_*.csv in Excel")
    print(f"  2. For each row, fill in:")
    print(f"     - is_correct: 'y' if extraction is correct, 'n' if wrong")
    print(f"     - is_relevant: 'y' if relevant to MSP, 'n' if not")
    print(f"     - error_type: if wrong, one of: false_positive, wrong_category,")
    print(f"       wrong_value, bibliography, author_credit, non_marine")
    print(f"     - notes: optional free text")
    print(f"  3. Save the CSVs")
    print(f"  4. Run: python scripts/compute_metrics.py")


if __name__ == '__main__':
    main()
