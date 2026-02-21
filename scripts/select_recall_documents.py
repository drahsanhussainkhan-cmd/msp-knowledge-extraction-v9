"""
Select 10 marine-relevant documents for recall evaluation gold standard.
Picks documents with diverse category coverage that are clearly MSP-related.
"""
import json
import random
import csv
import sys
from pathlib import Path
from collections import defaultdict

if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

PROJECT_ROOT = Path(__file__).parent.parent

# Non-marine keywords to exclude documents
NON_MARINE_KEYWORDS = [
    'autonomous-underwater-vehicle', 'path-planning', 'robot',
    'wave-glider', 'coral-sand', 'coral-clay', 'obstacle-avoidance',
    'CNN', 'neural-network', 'deep-learning', 'USV-trajectory',
    'mechanical-behavior'
]

# Marine/MSP keywords that indicate good recall documents
MARINE_KEYWORDS = [
    'marine-spatial-planning', 'MSP', 'marine-policy', 'coastal',
    'maritime', 'fisheries', 'ocean', 'offshore', 'MPA', 'protected-area',
    'biodiversity', 'conservation', 'stakeholder'
]

TARGET_CATEGORIES = ['species', 'method', 'stakeholder', 'environmental', 'finding']


def main():
    results_path = list(PROJECT_ROOT.glob("output_final3/raw_results_*.json"))[0]
    with open(results_path, 'r', encoding='utf-8') as f:
        data = json.load(f)

    # Score each document
    scored_docs = []
    for doc_name, categories in data.items():
        if not isinstance(categories, dict):
            continue

        # Skip non-marine
        doc_lower = doc_name.lower()
        if any(kw.lower() in doc_lower for kw in NON_MARINE_KEYWORDS):
            continue

        # Count target category extractions
        cat_counts = {}
        total = 0
        for cat in TARGET_CATEGORIES:
            items = categories.get(cat, [])
            if isinstance(items, list):
                cat_counts[cat] = len(items)
                total += len(items)

        # Score: prefer documents with extractions in multiple target categories
        cats_with_data = sum(1 for c in cat_counts.values() if c > 0)

        # Marine relevance bonus
        marine_bonus = sum(2 for kw in MARINE_KEYWORDS if kw.lower() in doc_lower)

        score = cats_with_data * 10 + total + marine_bonus

        if cats_with_data >= 2 and total >= 3:  # At least 2 categories with 3+ extractions
            scored_docs.append((doc_name, score, cat_counts, total))

    # Sort by score descending
    scored_docs.sort(key=lambda x: -x[1])

    print(f"Found {len(scored_docs)} candidate documents\n")
    print("Top 20 candidates:")
    for doc, score, cats, total in scored_docs[:20]:
        cat_str = ", ".join(f"{k}:{v}" for k, v in cats.items() if v > 0)
        print(f"  Score={score:3d} Total={total:2d} | {cat_str} | {doc[:80]}")

    # Select 10 diverse documents
    random.seed(42)
    selected = []

    # Take top 5 by score (highest coverage)
    for doc, score, cats, total in scored_docs[:5]:
        selected.append((doc, cats, total))

    # Take 5 more from rank 5-20 randomly for diversity
    pool = scored_docs[5:20]
    if len(pool) > 5:
        extra = random.sample(pool, 5)
    else:
        extra = pool
    for doc, score, cats, total in extra:
        selected.append((doc, cats, total))

    print(f"\n{'='*60}")
    print(f"SELECTED {len(selected)} DOCUMENTS FOR RECALL EVALUATION")
    print(f"{'='*60}\n")

    # Write recall documents list
    output_dir = PROJECT_ROOT / "validation_sheets_v2" / "recall_evaluation"
    output_dir.mkdir(parents=True, exist_ok=True)

    recall_csv = output_dir / "recall_documents.csv"
    with open(recall_csv, 'w', newline='', encoding='utf-8-sig') as f:
        writer = csv.writer(f)
        writer.writerow(['document', 'total_extractions', 'species', 'method',
                        'stakeholder', 'environmental', 'finding'])
        for doc, cats, total in selected:
            writer.writerow([doc, total, cats.get('species', 0), cats.get('method', 0),
                           cats.get('stakeholder', 0), cats.get('environmental', 0),
                           cats.get('finding', 0)])
            print(f"  {doc[:70]}")
            for cat, count in cats.items():
                if count > 0:
                    print(f"    {cat}: {count}")
            print()

    # Write system extractions per document
    for doc, cats, total in selected:
        doc_results = data.get(doc, {})
        safe_name = doc.replace('.pdf', '')[:80]
        doc_csv = output_dir / f"system_{safe_name}.csv"

        rows = []
        for cat in TARGET_CATEGORIES:
            items = doc_results.get(cat, [])
            if isinstance(items, list):
                for item in items:
                    rows.append({
                        'category': cat,
                        'exact_text': str(item.get('exact_text', ''))[:300],
                        'context': str(item.get('context', ''))[:200],
                        'page_number': item.get('page_number', ''),
                        'confidence': round(item.get('confidence', 0), 3),
                    })

        if rows:
            with open(doc_csv, 'w', newline='', encoding='utf-8-sig') as f:
                writer = csv.DictWriter(f, fieldnames=['category', 'exact_text', 'context',
                                                        'page_number', 'confidence'])
                writer.writeheader()
                writer.writerows(rows)

    print(f"Output: {output_dir}")
    print(f"  recall_documents.csv - master list")
    print(f"  system_*.csv - system extractions per document")


if __name__ == '__main__':
    main()
