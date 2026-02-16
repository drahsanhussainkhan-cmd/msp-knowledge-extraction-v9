#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Test runner for modular MSP Extractor
Temporarily imports utilities from old script, runs distance extractor
"""
import sys
import os
from pathlib import Path
import json

# Add paths
sys.path.insert(0, str(Path(__file__).parent))
sys.path.insert(0, r'C:\Users\ahk79\Downloads')

print("="*70)
print("MSP EXTRACTOR MODULAR - TEST RUN")
print("="*70)
print("\nTesting Distance Extractor on one PDF...")
print()

# Import from old script temporarily
print("Loading utilities from old script...")
try:
    # Read and execute old script to get its classes
    old_script = r'C:\Users\ahk79\Downloads\msp_extractor_v8_complete (1).py'
    with open(old_script, 'r', encoding='utf-8') as f:
        code = f.read()

    # Remove __main__ block
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

    # Execute to get classes
    exec('\n'.join(filtered), globals())
    print("[OK] Utilities loaded")

except Exception as e:
    print(f"[ERROR] Error loading utilities: {e}")
    sys.exit(1)

# Import modular components
print("Loading modular components...")
try:
    from core.enums import DocumentType
    from data_structures import DistanceExtraction
    from extractors.distance_extractor import DistanceExtractor
    print("[OK] Modular components loaded")
except Exception as e:
    print(f"[ERROR] Error loading modular components: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

# Test on one PDF
print("\n" + "-"*70)
print("Processing test PDF...")
print("-"*70)

# Pick a test PDF
test_pdf = r"C:\Users\ahk79\OneDrive\Desktop\msp laws seperate\1.5.1380_Su Ürünleri Kanunu (No. 1380).pdf"

if not os.path.exists(test_pdf):
    print(f"[ERROR] Test PDF not found: {test_pdf}")
    print("\nTrying first available PDF...")
    pdf_dir = Path(r"C:\Users\ahk79\OneDrive\Desktop\msp laws seperate")
    pdfs = list(pdf_dir.glob("*.pdf"))
    if pdfs:
        test_pdf = str(pdfs[0])
    else:
        print("[ERROR] No PDFs found!")
        sys.exit(1)

print(f"\nTest file: {Path(test_pdf).name}")

try:
    # Extract text
    import pdfplumber
    print("Extracting PDF text...")

    page_texts = {}
    full_text = []

    with pdfplumber.open(test_pdf) as pdf:
        for i, page in enumerate(pdf.pages, 1):
            text = page.extract_text() or ""
            page_texts[i] = text
            full_text.append(text)

    full_text = '\n\n'.join(full_text)
    print(f"[OK] Extracted {len(page_texts)} pages, {len(full_text)} characters")

    # Detect document type
    print("\nDetecting document type...")
    doc_type = LanguageDetector.detect(full_text)
    print(f"[OK] Detected: {doc_type.value}")

    # Initialize utilities
    print("\nInitializing extractors...")
    keywords = MSPKeywords()
    segmenter = TurkishLegalSentenceSegmenter()
    fp_filter = FalsePositiveFilter()
    legal_filter = LegalReferenceFilter()
    number_converter = MultilingualNumberConverter()

    # Create distance extractor
    distance_extractor = DistanceExtractor(
        keywords=keywords,
        sentence_segmenter=segmenter,
        fp_filter=fp_filter,
        legal_ref_filter=legal_filter,
        number_converter=number_converter
    )
    print("[OK] Distance extractor initialized")

    # Extract distances
    print("\nExtracting distances...")
    distances = distance_extractor.extract(full_text, page_texts, doc_type)
    print(f"[OK] Found {len(distances)} distance extractions")

    # Display results
    if distances:
        print("\n" + "="*70)
        print("EXTRACTION RESULTS")
        print("="*70)

        for i, dist in enumerate(distances, 1):
            print(f"\n{i}. {'='*66}")
            if dist.is_range:
                print(f"   RANGE: {dist.min_value}-{dist.max_value} {dist.unit}")
            else:
                print(f"   VALUE: {dist.value} {dist.unit}")

            if dist.qualifier:
                print(f"   Qualifier: {dist.qualifier}")

            print(f"   Activity: {dist.activity} (confidence: {dist.activity_confidence:.2f})")

            if dist.reference_point:
                print(f"   Reference: {dist.reference_point} ({dist.reference_point_type})")

            print(f"   Page: {dist.page_number}")
            print(f"   Confidence: {dist.confidence:.2f}")
            print(f"   Marine relevance: {dist.marine_relevance:.2f}")
            try:
                print(f"   Exact text: \"{dist.exact_text}\"")
                print(f"   Context: {dist.context[:150]}...")
            except UnicodeEncodeError:
                print(f"   Exact text: [Turkish text - see JSON file]")
                print(f"   Context: [Turkish text - see JSON file]")

    else:
        print("\n[WARNING]  No distances found in this document")

    # Save results
    output_file = "test_distance_results.json"
    results_data = {
        "document": Path(test_pdf).name,
        "document_type": doc_type.value,
        "total_pages": len(page_texts),
        "extractions": {
            "distance": [
                {
                    "activity": d.activity,
                    "value": d.value,
                    "min_value": d.min_value,
                    "max_value": d.max_value,
                    "unit": d.unit,
                    "qualifier": d.qualifier,
                    "reference_point": d.reference_point,
                    "reference_point_type": d.reference_point_type,
                    "is_range": d.is_range,
                    "page_number": d.page_number,
                    "confidence": d.confidence,
                    "exact_text": d.exact_text,
                    "context": d.context
                }
                for d in distances
            ]
        }
    }

    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(results_data, f, indent=2, ensure_ascii=False)

    print(f"\n[OK] Results saved to: {output_file}")

    print("\n" + "="*70)
    print("TEST COMPLETE - MODULAR DISTANCE EXTRACTOR WORKS!")
    print("="*70)
    print(f"\nSummary:")
    print(f"  - Processed: {Path(test_pdf).name}")
    print(f"  - Type: {doc_type.value}")
    print(f"  - Distances found: {len(distances)}")
    print(f"  - Results saved: {output_file}")

except Exception as e:
    print(f"\n[ERROR] Error during extraction: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
