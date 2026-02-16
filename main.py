"""
MSP Knowledge Extraction & Decision Support System - Main Pipeline Orchestrator
================================================================================
Processes Q1 research papers, legal documents, and dataset metadata to build
an integrated marine spatial planning knowledge base with gap detection and
decision support capabilities.

Usage:
    python main.py --research-dir ./data/research --legal-dir ./data/legal
    python main.py --research-dir ./data/research --legal-dir ./data/legal --dataset-dir ./data/datasets
    python main.py --help
"""

import argparse
import json
import os
import sys
import time
from datetime import datetime
from collections import defaultdict

# Fix Windows console encoding for Turkish characters
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from config import Config
from core.enums import DocumentType
from utils import (
    MSPKeywords, LanguageDetector, extract_text_from_pdf, get_pdf_metadata
)
from processors import Q1PaperProcessor, LegalDocumentProcessor, DatasetProcessor
from knowledge_base import KnowledgeDatabase, KnowledgeBuilder, QueryEngine, CrossLinker
from gap_detection import (
    ResearchGapDetector, LegalGapDetector, DataGapDetector,
    IntegrationGapDetector, GapPrioritizer
)
from decision_support import (
    MethodRecommender, EvidenceSynthesizer,
    DataCollectionPlanner, LegalComplianceChecker
)
from outputs import ReportGenerator, DashboardGenerator, Visualizer
from outputs.export import export_to_csv, export_to_json, export_gaps_to_csv


def parse_args():
    parser = argparse.ArgumentParser(
        description="MSP Knowledge Extraction & Decision Support System"
    )
    parser.add_argument("--research-dir", type=str, default=None,
                        help="Directory containing Q1 research paper PDFs")
    parser.add_argument("--legal-dir", type=str, default=None,
                        help="Directory containing legal document PDFs")
    parser.add_argument("--dataset-dir", type=str, default=None,
                        help="Directory containing dataset metadata files (JSON/PDF)")
    parser.add_argument("--output-dir", type=str, default="./output",
                        help="Output directory for reports and exports (default: ./output)")
    parser.add_argument("--db-path", type=str, default=None,
                        help="Path for SQLite knowledge base (default: <output-dir>/knowledge.db)")
    parser.add_argument("--skip-gaps", action="store_true",
                        help="Skip gap detection phase")
    parser.add_argument("--skip-dashboard", action="store_true",
                        help="Skip dashboard generation")
    parser.add_argument("--export-csv", action="store_true",
                        help="Export results to CSV")
    parser.add_argument("--export-excel", action="store_true",
                        help="Export results to Excel (requires openpyxl)")
    parser.add_argument("--validate", action="store_true",
                        help="Run validation after extraction")
    return parser.parse_args()


def discover_pdfs(directory):
    """Find all PDF files in a directory."""
    if not directory or not os.path.isdir(directory):
        return []
    pdfs = []
    for fname in sorted(os.listdir(directory)):
        if fname.lower().endswith(".pdf"):
            pdfs.append(os.path.join(directory, fname))
    return pdfs


def process_documents(pdf_paths, processor, label):
    """Process a list of PDFs with a given processor."""
    all_results = {}
    for i, pdf_path in enumerate(pdf_paths, 1):
        fname = os.path.basename(pdf_path)
        print(f"  [{i}/{len(pdf_paths)}] Processing {fname}...")

        try:
            full_text, page_texts = extract_text_from_pdf(pdf_path)
            if not full_text or len(full_text.strip()) < 50:
                print(f"    WARNING: Insufficient text extracted from {fname}, skipping.")
                continue

            doc_type = LanguageDetector.detect(full_text)
            results = processor.process(full_text, page_texts, doc_type, source_file=fname)
            all_results[fname] = results

            total = sum(len(v) for v in results.values() if isinstance(v, list))
            print(f"    Extracted {total} items across {len(results)} categories")

        except Exception as e:
            print(f"    ERROR processing {fname}: {e}")
            all_results[fname] = {"error": str(e)}

    return all_results


def run_pipeline(args):
    """Execute the full extraction pipeline."""
    start_time = time.time()
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    # Setup output directory
    output_dir = args.output_dir
    os.makedirs(output_dir, exist_ok=True)

    db_path = args.db_path or os.path.join(output_dir, "knowledge.db")

    print("=" * 70)
    print("MSP KNOWLEDGE EXTRACTION & DECISION SUPPORT SYSTEM")
    print(f"Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 70)

    # ── Phase 1: Document Discovery ──
    print("\n[Phase 1] Discovering documents...")
    research_pdfs = discover_pdfs(args.research_dir)
    legal_pdfs = discover_pdfs(args.legal_dir)
    dataset_pdfs = discover_pdfs(args.dataset_dir)

    print(f"  Research papers: {len(research_pdfs)}")
    print(f"  Legal documents: {len(legal_pdfs)}")
    print(f"  Dataset files:   {len(dataset_pdfs)}")

    if not research_pdfs and not legal_pdfs and not dataset_pdfs:
        print("\nERROR: No documents found. Please provide at least one document directory.")
        print("  --research-dir <path>  for Q1 research papers")
        print("  --legal-dir <path>     for legal documents")
        return

    # ── Phase 2: Extraction ──
    print("\n[Phase 2] Running extractors...")
    all_results = {}

    if research_pdfs:
        print(f"\n  Processing {len(research_pdfs)} research papers...")
        research_processor = Q1PaperProcessor()
        research_results = process_documents(research_pdfs, research_processor, "research")
        all_results.update(research_results)

    if legal_pdfs:
        print(f"\n  Processing {len(legal_pdfs)} legal documents...")
        legal_processor = LegalDocumentProcessor()
        legal_results = process_documents(legal_pdfs, legal_processor, "legal")
        all_results.update(legal_results)

    if dataset_pdfs:
        print(f"\n  Processing {len(dataset_pdfs)} dataset files...")
        dataset_processor = DatasetProcessor()
        dataset_results = process_documents(dataset_pdfs, dataset_processor, "dataset")
        all_results.update(dataset_results)

    # Save raw results
    raw_path = os.path.join(output_dir, f"raw_results_{timestamp}.json")
    export_to_json(all_results, raw_path)

    total_extractions = sum(
        len(items)
        for doc in all_results.values() if isinstance(doc, dict)
        for items in doc.values() if isinstance(items, list)
    )
    print(f"\n  Total extractions: {total_extractions}")

    # ── Phase 3: Knowledge Base ──
    print("\n[Phase 3] Building knowledge base...")
    kb = KnowledgeDatabase(db_path)

    builder = KnowledgeBuilder(kb)
    # Ingest from result directories if they exist, otherwise from raw results
    if args.research_dir:
        builder.ingest_results_directory(args.research_dir, "SCIENTIFIC_ENGLISH")
    if args.legal_dir:
        builder.ingest_results_directory(args.legal_dir, "LEGAL_TURKISH")

    # Also ingest the current run's results directly
    research_files = {os.path.basename(p) for p in research_pdfs}
    legal_files = {os.path.basename(p) for p in legal_pdfs}
    for doc_name, doc_results in all_results.items():
        if isinstance(doc_results, dict) and "error" not in doc_results:
            if doc_name in legal_files:
                d_type, d_lang = "LEGAL_TURKISH", "turkish"
            else:
                d_type, d_lang = "SCIENTIFIC_ENGLISH", "english"
            doc_id = kb.insert_document(doc_name, doc_type=d_type, language=d_lang,
                                        pages=0, source_path=doc_name)
            for category, items in doc_results.items():
                if isinstance(items, list):
                    kb.insert_batch_extractions(doc_id, category, items)

    # Cross-link
    print("  Cross-linking knowledge...")
    linker = CrossLinker(kb)
    linker.link_all()

    summary = kb.get_document_summary()
    print(f"  KB: {summary.get('total_documents', 0)} documents, "
          f"{sum(kb.get_extraction_counts().values())} extractions")

    # ── Phase 4: Gap Detection ──
    gaps = []
    if not args.skip_gaps:
        print("\n[Phase 4] Detecting gaps...")
        query = QueryEngine(kb)

        research_detector = ResearchGapDetector()
        legal_detector = LegalGapDetector()
        data_detector = DataGapDetector()
        integration_detector = IntegrationGapDetector()

        # Gap detectors use detect_all(knowledge_base) where kb has query_extractions()
        for detector, name in [
            (research_detector, "Research"),
            (legal_detector, "Legal"),
            (data_detector, "Data"),
            (integration_detector, "Integration"),
        ]:
            try:
                found = detector.detect_all(kb)
                gaps.extend(found)
                print(f"  {name}: {len(found)} gaps")
            except Exception as e:
                print(f"  Warning: {name} gap detection error: {e}")

        # Prioritize
        prioritizer = GapPrioritizer()
        gaps = prioritizer.prioritize(gaps)

        print(f"  Total gaps identified: {len(gaps)}")
        severity_counts = defaultdict(int)
        for g in gaps:
            sev = getattr(g, "severity", None) or (g.get("severity") if isinstance(g, dict) else "unknown")
            severity_counts[sev] += 1
        for sev, count in sorted(severity_counts.items()):
            print(f"    {sev}: {count}")

    # ── Phase 5: Reports & Outputs ──
    print("\n[Phase 5] Generating outputs...")

    # Text + JSON report
    reporter = ReportGenerator(knowledge_db=kb)
    reporter.generate_full_report(all_results, output_dir, f"msp_report_{timestamp}")

    # Gap report
    if gaps:
        gap_report_path = os.path.join(output_dir, f"gap_report_{timestamp}.txt")
        reporter.generate_gap_report(gaps, gap_report_path)
        export_gaps_to_csv(gaps, os.path.join(output_dir, f"gaps_{timestamp}.csv"))

    # Dashboard
    if not args.skip_dashboard:
        dashboard_path = os.path.join(output_dir, f"dashboard_{timestamp}.html")
        dashboard = DashboardGenerator(knowledge_db=kb)
        dashboard.generate(all_results, gaps, dashboard_path)

    # CSV export
    if args.export_csv:
        export_to_csv(all_results, os.path.join(output_dir, f"extractions_{timestamp}.csv"))

    # Excel export
    if args.export_excel:
        from outputs.export import export_to_excel
        export_to_excel(all_results, os.path.join(output_dir, f"extractions_{timestamp}.xlsx"))

    # Static charts (optional, only if matplotlib available)
    try:
        viz = Visualizer()
        viz.plot_extraction_summary(all_results, os.path.join(output_dir, f"chart_categories_{timestamp}.png"))
        if gaps:
            viz.plot_gap_analysis(gaps, os.path.join(output_dir, f"chart_gaps_{timestamp}.png"))
        viz.plot_confidence_distribution(all_results, os.path.join(output_dir, f"chart_confidence_{timestamp}.png"))
    except ImportError:
        print("  (matplotlib not available, skipping static charts)")

    # ── Phase 6: Validation ──
    if args.validate:
        print("\n[Phase 6] Running validation...")
        try:
            from validation.accuracy_checker import AccuracyChecker
            checker = AccuracyChecker()
            meets_target = checker.check_target_f1(all_results, target=0.80)
            if meets_target:
                print("  Target F1 >= 0.80 MET")
            else:
                print("  Target F1 >= 0.80 NOT MET (see validation report for details)")
        except Exception as e:
            print(f"  Validation error: {e}")

    # ── Summary ──
    elapsed = time.time() - start_time
    print("\n" + "=" * 70)
    print("PIPELINE COMPLETE")
    print(f"  Time elapsed: {elapsed:.1f}s")
    print(f"  Documents processed: {len(all_results)}")
    print(f"  Total extractions: {total_extractions}")
    print(f"  Gaps identified: {len(gaps)}")
    print(f"  Output directory: {os.path.abspath(output_dir)}")
    print("=" * 70)

    kb.close()


if __name__ == "__main__":
    args = parse_args()
    run_pipeline(args)
