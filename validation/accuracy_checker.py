"""
Accuracy checker - orchestrates the full validation workflow.

Coordinates metrics calculation, manual validation,
and generates comprehensive validation reports.
"""

import json
from pathlib import Path
from typing import Dict, List, Optional
from datetime import datetime

from .metrics_calculator import MetricsCalculator, ValidationResult
from .manual_validator import ManualValidator


class AccuracyChecker:
    """Orchestrate the complete validation workflow"""

    def __init__(self):
        self.metrics = MetricsCalculator()
        self.validator = ManualValidator()

    def run_validation(
        self,
        results_dir: str,
        ground_truth_dir: Optional[str] = None,
        output_dir: str = "validation_results"
    ) -> Dict:
        """
        Run the full validation pipeline.

        If ground_truth_dir is provided, calculate metrics against it.
        Otherwise, generate validation sheets for manual review.

        Args:
            results_dir: Directory with extraction JSON results
            ground_truth_dir: Directory with validated ground truth (optional)
            output_dir: Directory for validation outputs

        Returns:
            Dict with validation results
        """
        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)

        # Load all results
        print("Loading extraction results...")
        all_results = self._load_results(results_dir)
        print(f"  Loaded {sum(len(v) for v in all_results.values())} extractions "
              f"across {len(all_results)} categories")

        if ground_truth_dir and Path(ground_truth_dir).exists():
            # Calculate metrics against ground truth
            print("\nLoading ground truth...")
            ground_truth = self._load_ground_truth(ground_truth_dir)
            print(f"  Loaded ground truth for {len(ground_truth)} categories")

            print("\nCalculating metrics...")
            per_category = self.metrics.calculate_per_category(
                all_results, ground_truth
            )
            overall = self.metrics.calculate_overall(per_category)

            # Generate report
            report = self.metrics.generate_report(
                per_category,
                str(output_dir / "validation_report.txt")
            )
            print(report)

            # Save detailed results
            detailed = {
                'timestamp': datetime.now().isoformat(),
                'overall': overall,
                'per_category': {
                    cat: result.to_dict()
                    for cat, result in per_category.items()
                },
            }
            with open(output_dir / "validation_detailed.json", 'w', encoding='utf-8') as f:
                json.dump(detailed, f, indent=2, ensure_ascii=False)

            return detailed

        else:
            # No ground truth - generate validation sheets
            print("\nNo ground truth found. Generating validation sheets...")
            file_paths = self.validator.create_validation_sheets_all(
                all_results,
                str(output_dir / "validation_sheets"),
                sample_size=50
            )

            print(f"\nGenerated {len(file_paths)} validation sheets.")
            print("Please review and fill in 'is_correct' field (y/n) for each sample.")
            print(f"Then re-run with ground_truth_dir='{output_dir / 'validation_sheets'}'")

            return {'status': 'sheets_generated', 'file_paths': file_paths}

    def validate_single_document(
        self,
        result_path: str,
        ground_truth_path: Optional[str] = None
    ) -> Dict:
        """
        Validate extractions from a single document.

        Args:
            result_path: Path to extraction result JSON
            ground_truth_path: Path to ground truth JSON (optional)

        Returns:
            Dict with per-category metrics
        """
        with open(result_path, 'r', encoding='utf-8') as f:
            result_data = json.load(f)

        # Handle different result formats
        if 'extractions' in result_data:
            results = result_data['extractions']
        else:
            results = result_data

        if ground_truth_path:
            with open(ground_truth_path, 'r', encoding='utf-8') as f:
                gt_data = json.load(f)
            if 'extractions' in gt_data:
                ground_truth = gt_data['extractions']
            else:
                ground_truth = gt_data

            per_category = self.metrics.calculate_per_category(results, ground_truth)
            return {cat: r.to_dict() for cat, r in per_category.items()}

        return {'status': 'no_ground_truth', 'extractions': results}

    def check_target_f1(
        self,
        per_category: Dict[str, ValidationResult],
        target: float = 0.80
    ) -> Dict:
        """
        Check if all categories meet the target F1 score.

        Returns:
            Dict with pass/fail status and details
        """
        results = {
            'target_f1': target,
            'all_pass': True,
            'categories': {},
        }

        for cat, result in per_category.items():
            # Skip categories with no ground truth
            cm = result.confusion_matrix
            if cm.true_positives + cm.false_negatives == 0:
                continue

            passes = result.f1_score >= target
            results['categories'][cat] = {
                'f1': round(result.f1_score, 4),
                'passes': passes,
            }
            if not passes:
                results['all_pass'] = False

        return results

    def _load_results(self, results_dir: str) -> Dict[str, List[Dict]]:
        """Load all extraction results and aggregate by category."""
        results_dir = Path(results_dir)
        aggregated = {}

        for json_file in results_dir.glob("*_results.json"):
            try:
                with open(json_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)

                extractions = data.get('extractions', data)
                if isinstance(extractions, dict):
                    for category, items in extractions.items():
                        if isinstance(items, list):
                            if category not in aggregated:
                                aggregated[category] = []
                            for item in items:
                                if isinstance(item, dict):
                                    item['source_file'] = json_file.stem
                                    aggregated[category].append(item)
            except (json.JSONDecodeError, KeyError):
                continue

        # Also check for combined results
        combined_path = results_dir / "all_combined.json"
        if combined_path.exists():
            try:
                with open(combined_path, 'r', encoding='utf-8') as f:
                    combined = json.load(f)
                if isinstance(combined, list):
                    for doc_result in combined:
                        extractions = doc_result.get('extractions', {})
                        for category, items in extractions.items():
                            if isinstance(items, list):
                                if category not in aggregated:
                                    aggregated[category] = []
                                aggregated[category].extend(items)
            except (json.JSONDecodeError, KeyError):
                pass

        return aggregated

    def _load_ground_truth(self, ground_truth_dir: str) -> Dict[str, List[Dict]]:
        """Load ground truth from validated JSON files."""
        gt_dir = Path(ground_truth_dir)
        ground_truth = {}

        for json_file in gt_dir.glob("validate_*.json"):
            try:
                validated = self.validator.load_validated_data(str(json_file))
                correct = self.validator.extract_ground_truth(validated)

                category = json_file.stem.replace('validate_', '')
                ground_truth[category] = correct
            except (json.JSONDecodeError, KeyError):
                continue

        return ground_truth
