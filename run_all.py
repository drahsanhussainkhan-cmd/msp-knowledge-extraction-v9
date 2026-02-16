#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Process ALL PDFs with modular MSP extractor
"""
import sys
import os
from pathlib import Path
import json
from datetime import datetime

# Add paths
sys.path.insert(0, str(Path(__file__).parent))
sys.path.insert(0, r'C:\Users\ahk79\Downloads')

print("="*70)
print("MSP EXTRACTOR MODULAR - FULL BATCH PROCESSING")
print("="*70)
print(f"\nStarted: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")

# Import utilities from old script
print("Loading utilities...")
try:
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
    print("[OK] Modular components loaded\n")
except Exception as e:
    print(f"[ERROR] Error loading modular components: {e}")
    sys.exit(1)

# Initialize extractors once
print("Initializing extractors...")
keywords = MSPKeywords()
segmenter = TurkishLegalSentenceSegmenter()
fp_filter = FalsePositiveFilter()
legal_filter = LegalReferenceFilter()
number_converter = MultilingualNumberConverter()

distance_extractor = DistanceExtractor(
    keywords=keywords,
    sentence_segmenter=segmenter,
    fp_filter=fp_filter,
    legal_ref_filter=legal_filter,
    number_converter=number_converter
)
print("[OK] Distance extractor initialized\n")


def process_pdf(pdf_path, output_dir):
    """Process a single PDF"""
    try:
        import pdfplumber

        # Extract text
        page_texts = {}
        full_text = []

        with pdfplumber.open(pdf_path) as pdf:
            for i, page in enumerate(pdf.pages, 1):
                text = page.extract_text() or ""
                page_texts[i] = text
                full_text.append(text)

        full_text = '\n\n'.join(full_text)

        # Detect document type
        doc_type = LanguageDetector.detect(full_text)

        # Extract distances
        distances = distance_extractor.extract(full_text, page_texts, doc_type)

        # Prepare results
        results = {
            "document": Path(pdf_path).name,
            "document_type": doc_type.value,
            "total_pages": len(page_texts),
            "extraction_date": datetime.now().isoformat(),
            "statistics": {
                "total_extractions": len(distances),
                "distance": len(distances)
            },
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
                        "marine_relevance": d.marine_relevance,
                        "exact_text": d.exact_text,
                        "context": d.context[:200] if d.context else None
                    }
                    for d in distances
                ]
            }
        }

        # Save individual result
        output_file = output_dir / f"{Path(pdf_path).stem}_results.json"
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(results, f, indent=2, ensure_ascii=False)

        return results

    except Exception as e:
        print(f"  [ERROR] {Path(pdf_path).name}: {e}")
        return None


def process_folder(folder_path, output_dir, folder_name):
    """Process all PDFs in a folder"""
    print("="*70)
    print(f"PROCESSING: {folder_name}")
    print("="*70)
    print(f"Input:  {folder_path}")
    print(f"Output: {output_dir}\n")

    # Create output directory
    output_dir.mkdir(parents=True, exist_ok=True)

    # Get all PDFs
    pdf_files = list(Path(folder_path).glob("*.pdf"))
    print(f"Found {len(pdf_files)} PDF files\n")

    # Process each PDF
    all_results = []
    success_count = 0
    total_distances = 0

    for i, pdf_path in enumerate(pdf_files, 1):
        try:
            print(f"[{i}/{len(pdf_files)}] Processing: {pdf_path.name[:60]}...")
            result = process_pdf(pdf_path, output_dir)

            if result:
                all_results.append(result)
                success_count += 1
                dist_count = result['statistics']['distance']
                total_distances += dist_count

                if dist_count > 0:
                    print(f"  [OK] {dist_count} distances found")
                else:
                    print(f"  [OK] No distances")

        except KeyboardInterrupt:
            print("\n\n[STOPPED] Processing interrupted by user")
            break
        except Exception as e:
            print(f"  [ERROR] {e}")

    # Create combined results
    print(f"\n{'='*70}")
    print("CREATING COMBINED RESULTS")
    print("="*70)

    combined_file = output_dir / "all_combined.json"
    with open(combined_file, 'w', encoding='utf-8') as f:
        json.dump(all_results, f, indent=2, ensure_ascii=False)
    print(f"[OK] Saved: {combined_file}")

    # Create summary
    summary = {
        "folder": folder_name,
        "processed_date": datetime.now().isoformat(),
        "total_documents": len(pdf_files),
        "successful": success_count,
        "failed": len(pdf_files) - success_count,
        "total_extractions": {
            "distance": total_distances
        },
        "documents": [
            {
                "name": r["document"],
                "type": r["document_type"],
                "pages": r["total_pages"],
                "distances": r["statistics"]["distance"]
            }
            for r in all_results
        ]
    }

    summary_file = output_dir / "summary.json"
    with open(summary_file, 'w', encoding='utf-8') as f:
        json.dump(summary, f, indent=2, ensure_ascii=False)
    print(f"[OK] Saved: {summary_file}")

    # Print summary
    print(f"\n{'='*70}")
    print(f"SUMMARY: {folder_name}")
    print("="*70)
    print(f"Total documents:    {len(pdf_files)}")
    print(f"Successfully processed: {success_count}")
    print(f"Failed:             {len(pdf_files) - success_count}")
    print(f"Total distances:    {total_distances}")
    print(f"Average per doc:    {total_distances/success_count:.1f}" if success_count > 0 else "")
    print("="*70 + "\n")

    return all_results


# MAIN EXECUTION
print("\n" + "="*70)
print("BATCH 1: LEGAL DOCUMENTS")
print("="*70 + "\n")

legal_folder = Path(r"C:\Users\ahk79\OneDrive\Desktop\msp laws seperate")
legal_output = Path(r"C:\Users\ahk79\Downloads\msp_extractor_modular\results_legal")

if legal_folder.exists():
    legal_results = process_folder(legal_folder, legal_output, "Legal Documents")
else:
    print(f"[WARNING] Legal folder not found: {legal_folder}\n")
    legal_results = []


print("\n" + "="*70)
print("BATCH 2: Q1 SCIENTIFIC PAPERS")
print("="*70 + "\n")

q1_folder = Path(r"C:\Users\ahk79\OneDrive\Desktop\Q1 JOURNALS")
q1_output = Path(r"C:\Users\ahk79\Downloads\msp_extractor_modular\results_q1")

if q1_folder.exists():
    q1_results = process_folder(q1_folder, q1_output, "Q1 Journals")
else:
    print(f"[WARNING] Q1 folder not found: {q1_folder}\n")
    q1_results = []


# GRAND SUMMARY
print("\n" + "="*70)
print("FINAL SUMMARY - MODULAR EXTRACTOR")
print("="*70)
print(f"\nLegal Documents:")
print(f"  - Processed: {len(legal_results)}")
print(f"  - Distances: {sum(r['statistics']['distance'] for r in legal_results)}")
print(f"  - Results:   {legal_output}")

print(f"\nQ1 Papers:")
print(f"  - Processed: {len(q1_results)}")
print(f"  - Distances: {sum(r['statistics']['distance'] for r in q1_results)}")
print(f"  - Results:   {q1_output}")

print(f"\nGRAND TOTAL:")
print(f"  - Documents: {len(legal_results) + len(q1_results)}")
print(f"  - Distances: {sum(r['statistics']['distance'] for r in legal_results + q1_results)}")

print("\n" + "="*70)
print(f"COMPLETE! - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
print("="*70)
