import json
import logging
from pathlib import Path
from typing import Optional

from .database import KnowledgeDatabase

logger = logging.getLogger(__name__)


class KnowledgeBuilder:
    """Ingests JSON result files produced by the extraction pipeline
    into a :class:`KnowledgeDatabase`."""

    # Mapping from directory name hints to doc_type labels
    _DIR_TYPE_MAP = {
        "research": "research",
        "legal": "legal",
        "dataset": "dataset",
        "data": "dataset",
    }

    def __init__(self, db: KnowledgeDatabase):
        self.db = db

    # ------------------------------------------------------------------
    # Public helpers
    # ------------------------------------------------------------------

    def ingest_results_directory(self, results_dir: str,
                                 doc_type_hint: Optional[str] = None) -> int:
        """Load all JSON result files from *results_dir* into the DB.

        Looks for files matching ``*_results.json``.  Returns the number
        of files successfully ingested.
        """
        results_path = Path(results_dir)
        if not results_path.is_dir():
            logger.warning("Results directory does not exist: %s", results_dir)
            return 0

        json_files = sorted(results_path.glob("*_results.json"))
        if not json_files:
            # Also try plain *.json as a fallback
            json_files = sorted(results_path.glob("*.json"))

        ingested = 0
        for jf in json_files:
            try:
                self.ingest_single_result(str(jf), doc_type_hint=doc_type_hint)
                ingested += 1
            except Exception as exc:
                logger.error("Failed to ingest %s: %s", jf.name, exc)
        return ingested

    def ingest_single_result(self, json_path: str,
                             doc_type_hint: Optional[str] = None) -> int:
        """Load a single JSON result file and return the document id."""
        path = Path(json_path)
        with open(path, "r", encoding="utf-8") as fh:
            data = json.load(fh)

        # --- Determine document metadata ---
        filename = data.get("filename", path.stem)
        doc_type = data.get("doc_type") or doc_type_hint or self._guess_doc_type(path)
        language = data.get("language", "unknown")
        pages = data.get("pages", data.get("total_pages", 0))
        source_path = data.get("source_path", str(path))

        doc_id = self.db.insert_document(
            filename=filename,
            doc_type=doc_type,
            language=language,
            pages=pages,
            source_path=source_path,
        )

        # --- Ingest extractions -----------------------------------------
        # The results JSON is expected to have a top-level key "extractions"
        # which is a dict mapping category names to lists of extraction dicts.
        # Example:
        #   { "extractions": { "species": [{...}, ...], "methods": [...] } }
        #
        # We also support a flat list under "extractions" where each item
        # carries its own "category" key, as well as a top-level "results"
        # key used by some pipeline variants.

        extractions = data.get("extractions") or data.get("results") or {}

        if isinstance(extractions, dict):
            for category, items in extractions.items():
                if isinstance(items, list):
                    self.db.insert_batch_extractions(doc_id, category, items)
                elif isinstance(items, dict):
                    # Single extraction dict rather than a list
                    self.db.insert_extraction(doc_id, category, items)
        elif isinstance(extractions, list):
            for item in extractions:
                category = item.get("category", "uncategorised")
                self.db.insert_extraction(doc_id, category, item)

        # Some result files store categories at the top level (e.g.
        # "species", "methods", "distances" keys directly).  We handle
        # those as a fallback when no "extractions"/"results" key exists.
        if not extractions:
            skip_keys = {
                "filename", "doc_type", "language", "pages",
                "total_pages", "source_path", "processing_time",
                "timestamp", "metadata", "summary", "error",
            }
            for key, value in data.items():
                if key in skip_keys:
                    continue
                if isinstance(value, list) and value:
                    # Treat each list as a category of extractions
                    if isinstance(value[0], dict):
                        self.db.insert_batch_extractions(doc_id, key, value)

        logger.info("Ingested %s (doc_id=%d, type=%s)", filename, doc_id, doc_type)
        return doc_id

    def build_knowledge_base(self, research_results_dir: str,
                             legal_results_dir: str,
                             dataset_results_dir: Optional[str] = None) -> dict:
        """Build a complete knowledge base from all result directories.

        Returns a summary dict with counts of ingested files per source.
        """
        summary = {}

        logger.info("Ingesting research results from %s", research_results_dir)
        summary["research"] = self.ingest_results_directory(
            research_results_dir, doc_type_hint="research"
        )

        logger.info("Ingesting legal results from %s", legal_results_dir)
        summary["legal"] = self.ingest_results_directory(
            legal_results_dir, doc_type_hint="legal"
        )

        if dataset_results_dir:
            logger.info("Ingesting dataset results from %s", dataset_results_dir)
            summary["dataset"] = self.ingest_results_directory(
                dataset_results_dir, doc_type_hint="dataset"
            )

        logger.info(
            "Knowledge base built: %s",
            ", ".join(f"{k}={v}" for k, v in summary.items()),
        )
        return summary

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _guess_doc_type(self, path: Path) -> str:
        """Try to infer the doc_type from the file path."""
        parts = [p.lower() for p in path.parts]
        for part in parts:
            for hint, dtype in self._DIR_TYPE_MAP.items():
                if hint in part:
                    return dtype
        return "unknown"
