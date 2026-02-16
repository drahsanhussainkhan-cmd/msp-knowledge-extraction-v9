"""
Metrics calculation for extraction validation.

Provides precision, recall, F1 score calculation with
support for exact match and fuzzy matching modes.
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple
import json
from pathlib import Path


@dataclass
class ConfusionMatrix:
    """Confusion matrix for binary classification"""
    true_positives: int = 0
    false_positives: int = 0
    false_negatives: int = 0

    @property
    def precision(self) -> float:
        denom = self.true_positives + self.false_positives
        if denom == 0:
            return 0.0
        return self.true_positives / denom

    @property
    def recall(self) -> float:
        denom = self.true_positives + self.false_negatives
        if denom == 0:
            return 0.0
        return self.true_positives / denom

    @property
    def f1_score(self) -> float:
        p, r = self.precision, self.recall
        if p + r == 0:
            return 0.0
        return 2 * (p * r) / (p + r)

    def to_dict(self) -> Dict:
        return {
            'true_positives': self.true_positives,
            'false_positives': self.false_positives,
            'false_negatives': self.false_negatives,
            'precision': round(self.precision, 4),
            'recall': round(self.recall, 4),
            'f1_score': round(self.f1_score, 4),
        }


@dataclass
class ValidationResult:
    """Result of validating a single category"""
    category: str
    precision: float
    recall: float
    f1_score: float
    confusion_matrix: ConfusionMatrix
    total_extractions: int = 0
    total_ground_truth: int = 0
    sample_size: int = 0

    def to_dict(self) -> Dict:
        return {
            'category': self.category,
            'precision': round(self.precision, 4),
            'recall': round(self.recall, 4),
            'f1_score': round(self.f1_score, 4),
            'total_extractions': self.total_extractions,
            'total_ground_truth': self.total_ground_truth,
            'sample_size': self.sample_size,
            'confusion_matrix': self.confusion_matrix.to_dict(),
        }


class MetricsCalculator:
    """Calculate precision, recall, F1 for extraction validation"""

    def calculate_exact_match(
        self,
        extractions: List[Dict],
        ground_truth: List[Dict],
        key_field: str = 'exact_text'
    ) -> ValidationResult:
        """
        Compare extractions to ground truth using exact text match.

        Args:
            extractions: List of extraction dicts from extractors
            ground_truth: List of manually verified correct extractions
            key_field: Field to match on (default: 'exact_text')

        Returns:
            ValidationResult with precision, recall, F1
        """
        cm = ConfusionMatrix()

        extraction_keys = set()
        for e in extractions:
            val = e.get(key_field, '')
            if val:
                extraction_keys.add(val.lower().strip())

        truth_keys = set()
        for g in ground_truth:
            val = g.get(key_field, '')
            if val:
                truth_keys.add(val.lower().strip())

        cm.true_positives = len(extraction_keys & truth_keys)
        cm.false_positives = len(extraction_keys - truth_keys)
        cm.false_negatives = len(truth_keys - extraction_keys)

        return ValidationResult(
            category='',
            precision=cm.precision,
            recall=cm.recall,
            f1_score=cm.f1_score,
            confusion_matrix=cm,
            total_extractions=len(extractions),
            total_ground_truth=len(ground_truth),
            sample_size=len(truth_keys),
        )

    def calculate_fuzzy_match(
        self,
        extractions: List[Dict],
        ground_truth: List[Dict],
        key_field: str = 'exact_text',
        threshold: float = 0.8
    ) -> ValidationResult:
        """
        Compare extractions to ground truth using fuzzy matching.

        Uses substring overlap ratio for matching.

        Args:
            extractions: Extraction dicts
            ground_truth: Ground truth dicts
            key_field: Field to match on
            threshold: Minimum similarity for a match (0-1)

        Returns:
            ValidationResult
        """
        cm = ConfusionMatrix()

        ext_texts = [e.get(key_field, '').lower().strip() for e in extractions if e.get(key_field)]
        truth_texts = [g.get(key_field, '').lower().strip() for g in ground_truth if g.get(key_field)]

        matched_truth = set()
        matched_ext = set()

        for i, ext in enumerate(ext_texts):
            for j, truth in enumerate(truth_texts):
                if j in matched_truth:
                    continue
                sim = self._similarity(ext, truth)
                if sim >= threshold:
                    matched_ext.add(i)
                    matched_truth.add(j)
                    break

        cm.true_positives = len(matched_ext)
        cm.false_positives = len(ext_texts) - len(matched_ext)
        cm.false_negatives = len(truth_texts) - len(matched_truth)

        return ValidationResult(
            category='',
            precision=cm.precision,
            recall=cm.recall,
            f1_score=cm.f1_score,
            confusion_matrix=cm,
            total_extractions=len(extractions),
            total_ground_truth=len(ground_truth),
            sample_size=len(truth_texts),
        )

    def calculate_per_category(
        self,
        results: Dict[str, List[Dict]],
        ground_truth: Dict[str, List[Dict]],
        key_field: str = 'exact_text'
    ) -> Dict[str, ValidationResult]:
        """
        Calculate metrics for each extraction category.

        Args:
            results: Dict of category -> list of extraction dicts
            ground_truth: Dict of category -> list of ground truth dicts

        Returns:
            Dict of category -> ValidationResult
        """
        metrics = {}
        all_categories = set(list(results.keys()) + list(ground_truth.keys()))

        for category in sorted(all_categories):
            ext = results.get(category, [])
            gt = ground_truth.get(category, [])
            result = self.calculate_exact_match(ext, gt, key_field)
            result.category = category
            metrics[category] = result

        return metrics

    def calculate_overall(
        self,
        per_category: Dict[str, ValidationResult]
    ) -> Dict[str, float]:
        """
        Calculate macro and micro averaged metrics.

        Returns:
            Dict with macro_precision, macro_recall, macro_f1,
            micro_precision, micro_recall, micro_f1
        """
        if not per_category:
            return {
                'macro_precision': 0.0, 'macro_recall': 0.0, 'macro_f1': 0.0,
                'micro_precision': 0.0, 'micro_recall': 0.0, 'micro_f1': 0.0,
            }

        # Macro average
        precisions = [v.precision for v in per_category.values()]
        recalls = [v.recall for v in per_category.values()]
        f1s = [v.f1_score for v in per_category.values()]

        macro_p = sum(precisions) / len(precisions)
        macro_r = sum(recalls) / len(recalls)
        macro_f1 = sum(f1s) / len(f1s)

        # Micro average
        total_tp = sum(v.confusion_matrix.true_positives for v in per_category.values())
        total_fp = sum(v.confusion_matrix.false_positives for v in per_category.values())
        total_fn = sum(v.confusion_matrix.false_negatives for v in per_category.values())

        micro_p = total_tp / (total_tp + total_fp) if (total_tp + total_fp) > 0 else 0.0
        micro_r = total_tp / (total_tp + total_fn) if (total_tp + total_fn) > 0 else 0.0
        micro_f1 = 2 * micro_p * micro_r / (micro_p + micro_r) if (micro_p + micro_r) > 0 else 0.0

        return {
            'macro_precision': round(macro_p, 4),
            'macro_recall': round(macro_r, 4),
            'macro_f1': round(macro_f1, 4),
            'micro_precision': round(micro_p, 4),
            'micro_recall': round(micro_r, 4),
            'micro_f1': round(micro_f1, 4),
        }

    def generate_report(
        self,
        per_category: Dict[str, ValidationResult],
        output_path: Optional[str] = None
    ) -> str:
        """
        Generate a text validation report.

        Returns:
            Report text (also saved to file if output_path given)
        """
        overall = self.calculate_overall(per_category)

        lines = []
        lines.append("=" * 70)
        lines.append("EXTRACTION VALIDATION REPORT")
        lines.append("=" * 70)
        lines.append("")
        lines.append(f"{'Category':<25} {'P':>8} {'R':>8} {'F1':>8} {'TP':>6} {'FP':>6} {'FN':>6}")
        lines.append("-" * 70)

        for cat, result in sorted(per_category.items()):
            cm = result.confusion_matrix
            lines.append(
                f"{cat:<25} {result.precision:>8.3f} {result.recall:>8.3f} "
                f"{result.f1_score:>8.3f} {cm.true_positives:>6} "
                f"{cm.false_positives:>6} {cm.false_negatives:>6}"
            )

        lines.append("-" * 70)
        lines.append(
            f"{'MACRO AVERAGE':<25} {overall['macro_precision']:>8.3f} "
            f"{overall['macro_recall']:>8.3f} {overall['macro_f1']:>8.3f}"
        )
        lines.append(
            f"{'MICRO AVERAGE':<25} {overall['micro_precision']:>8.3f} "
            f"{overall['micro_recall']:>8.3f} {overall['micro_f1']:>8.3f}"
        )
        lines.append("=" * 70)

        # F1 target check
        below_target = [
            cat for cat, r in per_category.items()
            if r.f1_score < 0.80 and r.confusion_matrix.true_positives + r.confusion_matrix.false_negatives > 0
        ]
        if below_target:
            lines.append(f"\nCategories below F1=0.80 target: {', '.join(below_target)}")
        else:
            lines.append("\nAll categories meet F1 >= 0.80 target!")

        report = '\n'.join(lines)

        if output_path:
            Path(output_path).parent.mkdir(parents=True, exist_ok=True)
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(report)

        return report

    @staticmethod
    def _similarity(a: str, b: str) -> float:
        """Calculate word overlap similarity between two strings."""
        if not a or not b:
            return 0.0
        words_a = set(a.split())
        words_b = set(b.split())
        if not words_a or not words_b:
            return 0.0
        intersection = words_a & words_b
        union = words_a | words_b
        return len(intersection) / len(union)
