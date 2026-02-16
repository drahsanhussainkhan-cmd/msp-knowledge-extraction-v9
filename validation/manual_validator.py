"""
Manual validation interface for extraction results.

Generates validation spreadsheets for human review and
loads completed validation data back for metrics calculation.
"""

import json
import random
from pathlib import Path
from typing import Dict, List, Optional
from datetime import datetime


class ManualValidator:
    """Generate validation spreadsheets and manage ground truth data"""

    def create_validation_sheet(
        self,
        extractions: List[Dict],
        category: str,
        sample_size: int = 50,
        output_path: Optional[str] = None,
        seed: int = 42
    ) -> List[Dict]:
        """
        Create a validation sample for human review.

        Args:
            extractions: List of extraction dicts
            category: Extraction category name
            sample_size: Number of samples to validate
            output_path: Path to save CSV/JSON (optional)
            seed: Random seed for reproducibility

        Returns:
            List of validation sample dicts
        """
        random.seed(seed)

        if len(extractions) <= sample_size:
            sample = extractions[:]
        else:
            sample = random.sample(extractions, sample_size)

        validation_rows = []
        for i, ext in enumerate(sample, 1):
            row = {
                'id': i,
                'category': category,
                'exact_text': ext.get('exact_text', ''),
                'context': (ext.get('context', '') or '')[:300],
                'page_number': ext.get('page_number'),
                'confidence': ext.get('confidence', 0),
                'source_file': ext.get('source_file', ext.get('document', '')),
                # Fields to fill during validation
                'is_correct': '',  # 'y' or 'n'
                'is_relevant': '',  # 'y' or 'n'
                'notes': '',
            }
            # Add category-specific key fields
            for key in ['species_name', 'method_type', 'finding_type',
                        'penalty_type', 'reference_type', 'stakeholder_name',
                        'objective_type', 'result_type', 'conclusion_type',
                        'gap_type', 'dataset_name']:
                if key in ext:
                    row[key] = ext[key]

            validation_rows.append(row)

        if output_path:
            self._save_validation_sheet(validation_rows, output_path)

        return validation_rows

    def create_validation_sheets_all(
        self,
        results: Dict[str, List[Dict]],
        output_dir: str,
        sample_size: int = 50
    ) -> Dict[str, str]:
        """
        Create validation sheets for all categories.

        Args:
            results: Dict of category -> list of extraction dicts
            output_dir: Directory to save validation files
            sample_size: Samples per category

        Returns:
            Dict of category -> output file path
        """
        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)
        file_paths = {}

        for category, extractions in results.items():
            if not extractions:
                continue
            output_path = str(output_dir / f"validate_{category}.json")
            self.create_validation_sheet(
                extractions, category, sample_size, output_path
            )
            file_paths[category] = output_path
            print(f"  {category}: {min(len(extractions), sample_size)} samples -> {output_path}")

        return file_paths

    def load_validated_data(self, validation_path: str) -> List[Dict]:
        """
        Load completed validation data (after human review).

        Args:
            validation_path: Path to validated JSON file

        Returns:
            List of validated extraction dicts
        """
        with open(validation_path, 'r', encoding='utf-8') as f:
            data = json.load(f)

        if isinstance(data, dict) and 'validations' in data:
            return data['validations']
        return data

    def extract_ground_truth(self, validated_data: List[Dict]) -> List[Dict]:
        """
        Extract ground truth (correct extractions) from validated data.

        Args:
            validated_data: List of validated dicts with 'is_correct' field

        Returns:
            List of extractions marked as correct
        """
        ground_truth = []
        for item in validated_data:
            is_correct = str(item.get('is_correct', '')).lower().strip()
            if is_correct in ('y', 'yes', 'true', '1'):
                ground_truth.append(item)
        return ground_truth

    def interactive_validate(
        self,
        extractions: List[Dict],
        category: str,
        sample_size: int = 50,
        output_path: Optional[str] = None
    ) -> List[Dict]:
        """
        Interactive CLI validation of extractions.

        Presents each extraction and asks for yes/no validation.

        Args:
            extractions: Extractions to validate
            category: Category name
            sample_size: Number to validate
            output_path: Path to save results

        Returns:
            List of validated dicts
        """
        sample = self.create_validation_sheet(
            extractions, category, sample_size
        )

        print(f"\n{'='*60}")
        print(f"MANUAL VALIDATION: {category}")
        print(f"{'='*60}")
        print(f"Validating {len(sample)} samples. Enter y/n for each.\n")

        validated = []
        correct_count = 0

        for item in sample:
            print(f"\n--- Sample {item['id']}/{len(sample)} ---")
            print(f"Text: {item['exact_text'][:100]}")
            print(f"Context: {item['context'][:150]}")
            if item.get('page_number'):
                print(f"Page: {item['page_number']}")

            while True:
                answer = input("Correct? (y/n/q=quit): ").strip().lower()
                if answer in ('y', 'n', 'q'):
                    break
                print("Please enter y, n, or q")

            if answer == 'q':
                print("Validation stopped early.")
                break

            item['is_correct'] = answer
            if answer == 'y':
                correct_count += 1
            validated.append(item)

        total = len(validated)
        if total > 0:
            print(f"\nResults: {correct_count}/{total} correct ({100*correct_count/total:.1f}%)")

        if output_path:
            self._save_validation_sheet(validated, output_path)
            print(f"Saved to: {output_path}")

        return validated

    def _save_validation_sheet(self, rows: List[Dict], output_path: str):
        """Save validation data to JSON file."""
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        data = {
            'metadata': {
                'created': datetime.now().isoformat(),
                'total_samples': len(rows),
                'category': rows[0].get('category', '') if rows else '',
            },
            'validations': rows,
        }

        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

        # Also try CSV if pandas available
        try:
            import pandas as pd
            csv_path = str(output_path).replace('.json', '.csv')
            df = pd.DataFrame(rows)
            df.to_csv(csv_path, index=False, encoding='utf-8')
        except ImportError:
            pass
