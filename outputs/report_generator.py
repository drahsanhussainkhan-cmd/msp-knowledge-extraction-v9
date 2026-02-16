"""
Report Generator - Produces comprehensive MSP extraction reports.
"""

import json
import os
from datetime import datetime
from collections import defaultdict


class ReportGenerator:
    """Generates detailed text and JSON reports from extraction results."""

    def __init__(self, knowledge_db=None):
        self.knowledge_db = knowledge_db

    def generate_full_report(self, results, output_dir, report_name="msp_extraction_report"):
        """Generate both text and JSON reports."""
        os.makedirs(output_dir, exist_ok=True)

        text_path = os.path.join(output_dir, f"{report_name}.txt")
        json_path = os.path.join(output_dir, f"{report_name}.json")

        text_report = self._build_text_report(results)
        with open(text_path, "w", encoding="utf-8") as f:
            f.write(text_report)

        json_report = self._build_json_report(results)
        with open(json_path, "w", encoding="utf-8") as f:
            json.dump(json_report, f, ensure_ascii=False, indent=2, default=str)

        print(f"Reports saved to {output_dir}")
        return text_path, json_path

    def _build_text_report(self, results):
        """Build a human-readable text report."""
        lines = []
        lines.append("=" * 80)
        lines.append("MSP KNOWLEDGE EXTRACTION REPORT")
        lines.append(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        lines.append("=" * 80)
        lines.append("")

        # Summary statistics
        lines.append("SUMMARY")
        lines.append("-" * 40)
        total_extractions = 0
        category_counts = defaultdict(int)

        if isinstance(results, dict):
            for doc_name, doc_results in results.items():
                if isinstance(doc_results, dict):
                    for category, items in doc_results.items():
                        if isinstance(items, list):
                            count = len(items)
                            category_counts[category] += count
                            total_extractions += count

        lines.append(f"Total documents processed: {len(results) if isinstance(results, dict) else 0}")
        lines.append(f"Total extractions: {total_extractions}")
        lines.append("")

        lines.append("EXTRACTIONS BY CATEGORY")
        lines.append("-" * 40)
        for category, count in sorted(category_counts.items(), key=lambda x: -x[1]):
            lines.append(f"  {category}: {count}")
        lines.append("")

        # Per-document details
        lines.append("DOCUMENT DETAILS")
        lines.append("-" * 40)
        if isinstance(results, dict):
            for doc_name, doc_results in results.items():
                lines.append(f"\n  Document: {doc_name}")
                if isinstance(doc_results, dict):
                    for category, items in doc_results.items():
                        if isinstance(items, list) and items:
                            lines.append(f"    {category} ({len(items)} items):")
                            for item in items[:5]:  # Show first 5
                                text = ""
                                if isinstance(item, dict):
                                    text = item.get("exact_text", item.get("text", str(item)))[:100]
                                else:
                                    text = str(item)[:100]
                                lines.append(f"      - {text}")
                            if len(items) > 5:
                                lines.append(f"      ... and {len(items) - 5} more")

        # Knowledge base stats if available
        if self.knowledge_db:
            lines.append("\n")
            lines.append("KNOWLEDGE BASE STATISTICS")
            lines.append("-" * 40)
            try:
                summary = self.knowledge_db.get_document_summary()
                lines.append(f"  Documents in KB: {summary.get('total_documents', 'N/A')}")
                counts = self.knowledge_db.get_extraction_counts()
                for cat, cnt in sorted(counts.items(), key=lambda x: -x[1]):
                    lines.append(f"    {cat}: {cnt}")
            except Exception as e:
                lines.append(f"  Error reading KB: {e}")

        lines.append("\n" + "=" * 80)
        lines.append("END OF REPORT")
        return "\n".join(lines)

    def _build_json_report(self, results):
        """Build a structured JSON report."""
        category_counts = defaultdict(int)
        total = 0

        if isinstance(results, dict):
            for doc_results in results.values():
                if isinstance(doc_results, dict):
                    for category, items in doc_results.items():
                        if isinstance(items, list):
                            category_counts[category] += len(items)
                            total += len(items)

        report = {
            "metadata": {
                "generated_at": datetime.now().isoformat(),
                "tool": "MSP Knowledge Extraction System",
                "version": "2.0"
            },
            "summary": {
                "total_documents": len(results) if isinstance(results, dict) else 0,
                "total_extractions": total,
                "extractions_by_category": dict(category_counts)
            },
            "results": results
        }

        if self.knowledge_db:
            try:
                report["knowledge_base_summary"] = self.knowledge_db.get_document_summary()
            except Exception:
                pass

        return report

    def generate_gap_report(self, gaps, output_path):
        """Generate a dedicated gap analysis report."""
        lines = []
        lines.append("=" * 80)
        lines.append("MSP GAP ANALYSIS REPORT")
        lines.append(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        lines.append("=" * 80)
        lines.append("")

        if not gaps:
            lines.append("No gaps detected.")
            with open(output_path, "w", encoding="utf-8") as f:
                f.write("\n".join(lines))
            return output_path

        # Group by category
        by_category = defaultdict(list)
        for gap in gaps:
            cat = getattr(gap, "gap_category", "unknown") if hasattr(gap, "gap_category") else gap.get("gap_category", "unknown")
            by_category[cat].append(gap)

        lines.append(f"Total gaps identified: {len(gaps)}")
        lines.append(f"Categories: {', '.join(by_category.keys())}")
        lines.append("")

        for category, cat_gaps in sorted(by_category.items()):
            lines.append(f"\n{'='*60}")
            lines.append(f"CATEGORY: {category.upper()} ({len(cat_gaps)} gaps)")
            lines.append(f"{'='*60}")

            # Sort by severity
            severity_order = {"critical": 0, "important": 1, "minor": 2}
            cat_gaps_sorted = sorted(cat_gaps, key=lambda g: severity_order.get(
                getattr(g, "severity", "minor") if hasattr(g, "severity") else g.get("severity", "minor"), 2
            ))

            for i, gap in enumerate(cat_gaps_sorted, 1):
                if hasattr(gap, "description"):
                    desc = gap.description
                    sev = gap.severity
                    gtype = gap.gap_type
                    rec = gap.recommendation
                elif isinstance(gap, dict):
                    desc = gap.get("description", "N/A")
                    sev = gap.get("severity", "N/A")
                    gtype = gap.get("gap_type", "N/A")
                    rec = gap.get("recommendation", "N/A")
                else:
                    desc = str(gap)
                    sev = gtype = rec = "N/A"

                lines.append(f"\n  Gap #{i}")
                lines.append(f"    Type: {gtype}")
                lines.append(f"    Severity: {sev}")
                lines.append(f"    Description: {desc}")
                lines.append(f"    Recommendation: {rec}")

        with open(output_path, "w", encoding="utf-8") as f:
            f.write("\n".join(lines))
        print(f"Gap report saved to {output_path}")
        return output_path
