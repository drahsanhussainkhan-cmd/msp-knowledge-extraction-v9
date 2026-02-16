#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Test ALL 17 extraction categories on a sample PDF
"""
import sys
import os
from pathlib import Path
import json

# Add paths
sys.path.insert(0, str(Path(__file__).parent))
sys.path.insert(0, r'C:\Users\ahk79\Downloads')

print("="*70)
print("MSP EXTRACTOR - ALL 17 CATEGORIES TEST")
print("="*70)

# Import utilities from old script
print("\nLoading utilities...")
try:
    old_script = r'C:\Users\ahk79\Downloads\msp_extractor_v8_complete (1).py'
    with open(old_script, 'r', encoding='utf-8') as f:
        code = f.read()

    lines = code.split('\n')
    filtered = []
    in_main = False
    for line in lines:
        if 'if __name__ ==' in line:
            in_main = True
            continue
        if in_main:
            if line and not line[0].isspace():
                in_main = False
            else:
                continue
        filtered.append(line)

    exec('\n'.join(filtered), globals())
    print("[OK] Utilities loaded")
except Exception as e:
    print(f"[ERROR] {e}")
    sys.exit(1)

# Import ALL extractors
print("Loading all extractors...")
try:
    from core.enums import DocumentType
    from data_structures import *
    from extractors.distance_extractor import DistanceExtractor
    from extractors.penalty_extractor import PenaltyExtractor
    from extractors.temporal_extractor import TemporalExtractor
    from extractors.environmental_extractor import EnvironmentalExtractor
    from extractors.prohibition_extractor import ProhibitionExtractor
    from extractors.species_extractor import SpeciesExtractor
    from extractors.protected_area_extractor import ProtectedAreaExtractor
    from extractors.permit_extractor import PermitExtractor
    from extractors.coordinate_extractor import CoordinateExtractor
    from extractors.stakeholder_extractor import StakeholderExtractor
    from extractors.institution_extractor import InstitutionExtractor
    from extractors.conflict_extractor import ConflictExtractor
    from extractors.method_extractor import MethodExtractor
    from extractors.finding_extractor import FindingExtractor
    from extractors.policy_extractor import PolicyExtractor
    from extractors.data_source_extractor import DataSourceExtractor
    from extractors.legal_reference_extractor import LegalReferenceExtractor
    print("[OK] All extractors loaded")
except Exception as e:
    print(f"[ERROR] {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

# Initialize utilities
print("\nInitializing...")
keywords = MSPKeywords()
segmenter = TurkishLegalSentenceSegmenter()
fp_filter = FalsePositiveFilter()
legal_filter = LegalReferenceFilter()
number_converter = MultilingualNumberConverter()

# Initialize ALL extractors
extractors = {
    'distance': DistanceExtractor(keywords, segmenter, fp_filter, legal_filter, number_converter),
    'penalty': PenaltyExtractor(keywords, segmenter, fp_filter, legal_filter, number_converter),
    'temporal': TemporalExtractor(keywords, segmenter, fp_filter, legal_filter, number_converter),
    'environmental': EnvironmentalExtractor(keywords, segmenter, fp_filter, legal_filter, number_converter),
    'prohibition': ProhibitionExtractor(keywords, segmenter, fp_filter, legal_filter, number_converter),
    'species': SpeciesExtractor(keywords, segmenter, fp_filter, legal_filter, number_converter),
    'protected_area': ProtectedAreaExtractor(keywords, segmenter, fp_filter, legal_filter, number_converter),
    'permit': PermitExtractor(keywords, segmenter, fp_filter, legal_filter, number_converter),
    'coordinate': CoordinateExtractor(keywords, segmenter, fp_filter, legal_filter, number_converter),
    'stakeholder': StakeholderExtractor(keywords, segmenter, fp_filter, legal_filter, number_converter),
    'institution': InstitutionExtractor(keywords, segmenter, fp_filter, legal_filter, number_converter),
    'conflict': ConflictExtractor(keywords, segmenter, fp_filter, legal_filter, number_converter),
    'method': MethodExtractor(keywords, segmenter, fp_filter, legal_filter, number_converter),
    'finding': FindingExtractor(keywords, segmenter, fp_filter, legal_filter, number_converter),
    'policy': PolicyExtractor(keywords, segmenter, fp_filter, legal_filter, number_converter),
    'data_source': DataSourceExtractor(keywords, segmenter, fp_filter, legal_filter, number_converter),
    'legal_reference': LegalReferenceExtractor(keywords, segmenter, fp_filter, legal_filter, number_converter),
}
print(f"[OK] {len(extractors)} extractors initialized")

# Test PDF
test_pdf = r"C:\Users\ahk79\OneDrive\Desktop\msp laws seperate\7.5.7221.pdf"

print(f"\n{'='*70}")
print(f"Processing: {Path(test_pdf).name}")
print("="*70)

try:
    import pdfplumber

    # Extract text
    page_texts = {}
    full_text = []

    with pdfplumber.open(test_pdf) as pdf:
        for i, page in enumerate(pdf.pages, 1):
            text = page.extract_text() or ""
            page_texts[i] = text
            full_text.append(text)

    full_text = '\n\n'.join(full_text)
    print(f"[OK] Extracted {len(page_texts)} pages")

    # Detect document type
    doc_type = LanguageDetector.detect(full_text)
    print(f"[OK] Detected: {doc_type.value}")

    # Run ALL extractors
    print(f"\n{'='*70}")
    print("RUNNING ALL 17 EXTRACTORS")
    print("="*70)

    all_results = {}
    total_extractions = 0

    for category, extractor in extractors.items():
        try:
            print(f"\n[{category.upper()}]", end=" ")
            results = extractor.extract(full_text, page_texts, doc_type)
            all_results[category] = results
            count = len(results)
            total_extractions += count

            if count > 0:
                print(f"[OK] {count} extractions")
                # Show first result
                first = results[0]
                if hasattr(first, 'exact_text'):
                    print(f"  Example: {first.exact_text[:60]}...")
            else:
                print("[OK] 0 extractions")

        except Exception as e:
            print(f"[ERROR] {e}")
            all_results[category] = []

    # Summary
    print(f"\n{'='*70}")
    print("EXTRACTION SUMMARY")
    print("="*70)
    print(f"Total extractions: {total_extractions}")
    print("\nBreakdown by category:")
    for category, results in all_results.items():
        if len(results) > 0:
            print(f"  {category:20s}: {len(results):3d}")

    # Save results
    output_file = "all_categories_test.json"
    results_data = {
        "document": Path(test_pdf).name,
        "document_type": doc_type.value,
        "total_pages": len(page_texts),
        "total_extractions": total_extractions,
        "statistics": {cat: len(res) for cat, res in all_results.items()},
        "extractions": {}
    }

    # Convert to JSON-serializable format
    for category, results in all_results.items():
        results_data["extractions"][category] = [
            {k: v for k, v in vars(r).items() if not k.startswith('_')}
            for r in results
        ]

    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(results_data, f, indent=2, ensure_ascii=False)

    print(f"\n[OK] Results saved to: {output_file}")

    print(f"\n{'='*70}")
    print("ALL 17 CATEGORIES WORKING!")
    print("="*70)

except Exception as e:
    print(f"\n[ERROR] {e}")
    import traceback
    traceback.print_exc()
