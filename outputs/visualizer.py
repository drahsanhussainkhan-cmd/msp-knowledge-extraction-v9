"""
Visualizer - Creates matplotlib-based static charts for MSP extraction results.
"""

import os
from collections import defaultdict


class Visualizer:
    """Generates static charts (PNG/SVG) using matplotlib."""

    def __init__(self):
        self._plt = None

    def _get_plt(self):
        """Lazy import matplotlib."""
        if self._plt is None:
            try:
                import matplotlib
                matplotlib.use("Agg")
                import matplotlib.pyplot as plt
                self._plt = plt
            except ImportError:
                raise ImportError(
                    "matplotlib is required for visualization. Install with: pip install matplotlib"
                )
        return self._plt

    def plot_extraction_summary(self, results, output_path):
        """Bar chart of extraction counts by category."""
        plt = self._get_plt()
        category_counts = defaultdict(int)

        if isinstance(results, dict):
            for doc_results in results.values():
                if isinstance(doc_results, dict):
                    for category, items in doc_results.items():
                        if isinstance(items, list):
                            category_counts[category] += len(items)

        if not category_counts:
            print("No data to plot.")
            return None

        categories = sorted(category_counts.keys(), key=lambda c: -category_counts[c])
        counts = [category_counts[c] for c in categories]

        fig, ax = plt.subplots(figsize=(12, 6))
        bars = ax.barh(categories, counts, color="#0077b6")
        ax.set_xlabel("Count")
        ax.set_title("Extractions by Category")
        ax.invert_yaxis()

        for bar, count in zip(bars, counts):
            ax.text(bar.get_width() + 0.3, bar.get_y() + bar.get_height() / 2,
                    str(count), va="center", fontsize=9)

        plt.tight_layout()
        os.makedirs(os.path.dirname(output_path) or ".", exist_ok=True)
        fig.savefig(output_path, dpi=150, bbox_inches="tight")
        plt.close(fig)
        print(f"Chart saved to {output_path}")
        return output_path

    def plot_gap_analysis(self, gaps, output_path):
        """Stacked bar chart of gaps by category and severity."""
        plt = self._get_plt()

        if not gaps:
            print("No gaps to plot.")
            return None

        by_cat_sev = defaultdict(lambda: defaultdict(int))
        for gap in gaps:
            cat = getattr(gap, "gap_category", None) or (gap.get("gap_category") if isinstance(gap, dict) else "unknown")
            sev = getattr(gap, "severity", None) or (gap.get("severity") if isinstance(gap, dict) else "unknown")
            by_cat_sev[cat][sev] += 1

        categories = sorted(by_cat_sev.keys())
        severities = ["critical", "important", "minor"]
        colors = {"critical": "#e74c3c", "important": "#f39c12", "minor": "#3498db"}

        fig, ax = plt.subplots(figsize=(10, 6))
        bottom = [0] * len(categories)

        for sev in severities:
            values = [by_cat_sev[cat].get(sev, 0) for cat in categories]
            ax.bar(categories, values, bottom=bottom, label=sev.capitalize(),
                   color=colors.get(sev, "#95a5a6"))
            bottom = [b + v for b, v in zip(bottom, values)]

        ax.set_ylabel("Number of Gaps")
        ax.set_title("Gap Analysis by Category and Severity")
        ax.legend()
        plt.xticks(rotation=30, ha="right")
        plt.tight_layout()

        os.makedirs(os.path.dirname(output_path) or ".", exist_ok=True)
        fig.savefig(output_path, dpi=150, bbox_inches="tight")
        plt.close(fig)
        print(f"Gap chart saved to {output_path}")
        return output_path

    def plot_confidence_distribution(self, results, output_path):
        """Histogram of confidence scores across all extractions."""
        plt = self._get_plt()

        confidences = []
        if isinstance(results, dict):
            for doc_results in results.values():
                if isinstance(doc_results, dict):
                    for items in doc_results.values():
                        if isinstance(items, list):
                            for item in items:
                                conf = None
                                if isinstance(item, dict):
                                    conf = item.get("confidence")
                                elif hasattr(item, "confidence"):
                                    conf = item.confidence
                                if conf is not None:
                                    try:
                                        confidences.append(float(conf))
                                    except (ValueError, TypeError):
                                        pass

        if not confidences:
            print("No confidence data to plot.")
            return None

        fig, ax = plt.subplots(figsize=(8, 5))
        ax.hist(confidences, bins=20, color="#0077b6", edgecolor="white", alpha=0.8)
        ax.set_xlabel("Confidence Score")
        ax.set_ylabel("Frequency")
        ax.set_title("Distribution of Extraction Confidence Scores")
        ax.axvline(x=0.8, color="#e74c3c", linestyle="--", label="Target threshold (0.8)")
        ax.legend()

        plt.tight_layout()
        os.makedirs(os.path.dirname(output_path) or ".", exist_ok=True)
        fig.savefig(output_path, dpi=150, bbox_inches="tight")
        plt.close(fig)
        print(f"Confidence chart saved to {output_path}")
        return output_path
