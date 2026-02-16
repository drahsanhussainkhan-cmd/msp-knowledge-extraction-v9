import json
from typing import Dict, List, Optional

from .database import KnowledgeDatabase


class QueryEngine:
    """High-level query interface over the knowledge database."""

    def __init__(self, db: KnowledgeDatabase):
        self.db = db

    # ------------------------------------------------------------------
    # Full-text search
    # ------------------------------------------------------------------

    def search_extractions(self, keyword: str,
                           category: Optional[str] = None,
                           limit: int = 100) -> List[Dict]:
        """Full-text search in exact_text and context fields.

        Uses SQLite LIKE for portability.  The *keyword* is matched
        case-insensitively anywhere in the text.
        """
        like_pattern = f"%{keyword}%"
        query = """
            SELECT e.id, e.category, e.exact_text, e.context,
                   e.page_number, e.confidence, e.marine_relevance,
                   e.metadata, d.filename, d.doc_type
            FROM extractions e
            JOIN documents d ON e.document_id = d.id
            WHERE (e.exact_text LIKE ? COLLATE NOCASE
                   OR e.context LIKE ? COLLATE NOCASE)
        """
        params: list = [like_pattern, like_pattern]

        if category is not None:
            query += " AND e.category = ?"
            params.append(category)

        query += " ORDER BY e.confidence DESC LIMIT ?"
        params.append(limit)

        rows = self.db.conn.execute(query, params).fetchall()
        results = []
        for row in rows:
            d = dict(row)
            if d.get("metadata"):
                try:
                    d["metadata"] = json.loads(d["metadata"])
                except (json.JSONDecodeError, TypeError):
                    pass
            results.append(d)
        return results

    # ------------------------------------------------------------------
    # Entity summaries
    # ------------------------------------------------------------------

    def get_species_summary(self) -> List[Dict]:
        """Get all species with mention counts across documents.

        Returns a list of dicts with keys: species_name, mention_count,
        documents, avg_confidence.
        """
        rows = self.db.conn.execute("""
            SELECT e.metadata, e.exact_text, e.confidence, d.filename, d.doc_type
            FROM extractions e
            JOIN documents d ON e.document_id = d.id
            WHERE e.category = 'species'
            ORDER BY e.confidence DESC
        """).fetchall()

        species_map: Dict[str, dict] = {}
        for row in rows:
            # Try to get species_name from metadata, fall back to exact_text
            name = None
            if row["metadata"]:
                try:
                    meta = json.loads(row["metadata"])
                    name = meta.get("species_name") or meta.get("name")
                except (json.JSONDecodeError, TypeError):
                    pass
            if not name:
                name = (row["exact_text"] or "unknown").strip()

            name_lower = name.lower()
            if name_lower not in species_map:
                species_map[name_lower] = {
                    "species_name": name,
                    "mention_count": 0,
                    "documents": set(),
                    "total_confidence": 0.0,
                }
            entry = species_map[name_lower]
            entry["mention_count"] += 1
            entry["documents"].add(row["filename"])
            entry["total_confidence"] += (row["confidence"] or 0.0)

        results = []
        for entry in species_map.values():
            count = entry["mention_count"]
            results.append({
                "species_name": entry["species_name"],
                "mention_count": count,
                "documents": sorted(entry["documents"]),
                "avg_confidence": round(entry["total_confidence"] / count, 3)
                                  if count else 0.0,
            })

        results.sort(key=lambda x: x["mention_count"], reverse=True)
        return results

    def get_methods_summary(self) -> List[Dict]:
        """Get all methods with usage counts across documents.

        Returns a list of dicts with keys: method_name, usage_count,
        documents, avg_confidence.
        """
        rows = self.db.conn.execute("""
            SELECT e.metadata, e.exact_text, e.confidence, d.filename
            FROM extractions e
            JOIN documents d ON e.document_id = d.id
            WHERE e.category = 'methods'
            ORDER BY e.confidence DESC
        """).fetchall()

        methods_map: Dict[str, dict] = {}
        for row in rows:
            name = None
            if row["metadata"]:
                try:
                    meta = json.loads(row["metadata"])
                    name = meta.get("method_name") or meta.get("name")
                except (json.JSONDecodeError, TypeError):
                    pass
            if not name:
                name = (row["exact_text"] or "unknown").strip()

            name_lower = name.lower()
            if name_lower not in methods_map:
                methods_map[name_lower] = {
                    "method_name": name,
                    "usage_count": 0,
                    "documents": set(),
                    "total_confidence": 0.0,
                }
            entry = methods_map[name_lower]
            entry["usage_count"] += 1
            entry["documents"].add(row["filename"])
            entry["total_confidence"] += (row["confidence"] or 0.0)

        results = []
        for entry in methods_map.values():
            count = entry["usage_count"]
            results.append({
                "method_name": entry["method_name"],
                "usage_count": count,
                "documents": sorted(entry["documents"]),
                "avg_confidence": round(entry["total_confidence"] / count, 3)
                                  if count else 0.0,
            })

        results.sort(key=lambda x: x["usage_count"], reverse=True)
        return results

    def get_legal_requirements_for_activity(self, activity: str) -> Dict:
        """Find distance, penalty, prohibition, and permit requirements
        related to a given activity.

        Searches across legal-type documents for extractions whose text
        mentions the activity keyword.
        """
        like_pattern = f"%{activity}%"

        categories = ["distances", "penalties", "prohibitions", "permits",
                       "requirements", "regulations"]
        result: Dict[str, list] = {cat: [] for cat in categories}

        for cat in categories:
            rows = self.db.conn.execute("""
                SELECT e.id, e.exact_text, e.context, e.confidence,
                       e.metadata, d.filename
                FROM extractions e
                JOIN documents d ON e.document_id = d.id
                WHERE e.category = ?
                  AND d.doc_type = 'legal'
                  AND (e.exact_text LIKE ? COLLATE NOCASE
                       OR e.context LIKE ? COLLATE NOCASE)
                ORDER BY e.confidence DESC
            """, (cat, like_pattern, like_pattern)).fetchall()

            for row in rows:
                entry = dict(row)
                if entry.get("metadata"):
                    try:
                        entry["metadata"] = json.loads(entry["metadata"])
                    except (json.JSONDecodeError, TypeError):
                        pass
                result[cat].append(entry)

        # Remove empty categories for cleaner output
        return {k: v for k, v in result.items() if v}

    def get_cross_document_entities(self, entity_name: str) -> List[Dict]:
        """Find all mentions of an entity across documents.

        Searches exact_text, context, and metadata for the entity name
        and returns grouped results.
        """
        like_pattern = f"%{entity_name}%"

        rows = self.db.conn.execute("""
            SELECT e.id, e.category, e.exact_text, e.context,
                   e.page_number, e.confidence, e.metadata,
                   d.filename, d.doc_type
            FROM extractions e
            JOIN documents d ON e.document_id = d.id
            WHERE e.exact_text LIKE ? COLLATE NOCASE
               OR e.context LIKE ? COLLATE NOCASE
               OR e.metadata LIKE ? COLLATE NOCASE
            ORDER BY d.doc_type, e.confidence DESC
        """, (like_pattern, like_pattern, like_pattern)).fetchall()

        results = []
        for row in rows:
            d = dict(row)
            if d.get("metadata"):
                try:
                    d["metadata"] = json.loads(d["metadata"])
                except (json.JSONDecodeError, TypeError):
                    pass
            results.append(d)
        return results

    # ------------------------------------------------------------------
    # Statistics
    # ------------------------------------------------------------------

    def get_statistics(self) -> Dict:
        """Get overall statistics dict covering documents, extractions,
        cross-references, and integrated knowledge entries.
        """
        doc_summary = self.db.get_document_summary()
        ext_counts = self.db.get_extraction_counts()

        total_extractions = sum(ext_counts.values())

        avg_confidence = self.db.conn.execute(
            "SELECT AVG(confidence) AS avg FROM extractions"
        ).fetchone()["avg"] or 0.0

        cross_ref_count = self.db.conn.execute(
            "SELECT COUNT(*) AS cnt FROM cross_references"
        ).fetchone()["cnt"]

        ik_count = self.db.conn.execute(
            "SELECT COUNT(*) AS cnt FROM integrated_knowledge"
        ).fetchone()["cnt"]

        ik_by_type = self.db.conn.execute(
            """SELECT entity_type, COUNT(*) AS cnt
               FROM integrated_knowledge GROUP BY entity_type"""
        ).fetchall()

        return {
            "documents": doc_summary,
            "total_extractions": total_extractions,
            "extractions_by_category": ext_counts,
            "average_confidence": round(avg_confidence, 3),
            "cross_references": cross_ref_count,
            "integrated_knowledge_entries": ik_count,
            "integrated_knowledge_by_type": {
                row["entity_type"]: row["cnt"] for row in ik_by_type
            },
        }
