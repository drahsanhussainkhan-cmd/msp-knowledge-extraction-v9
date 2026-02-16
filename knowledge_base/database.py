import sqlite3
import json
import hashlib
from pathlib import Path
from typing import Dict, List, Optional
from datetime import datetime


class KnowledgeDatabase:
    SCHEMA = '''
    CREATE TABLE IF NOT EXISTS documents (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        filename TEXT UNIQUE NOT NULL,
        doc_type TEXT,
        language TEXT,
        pages INTEGER,
        processed_date TEXT,
        source_path TEXT
    );

    CREATE TABLE IF NOT EXISTS extractions (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        document_id INTEGER NOT NULL,
        category TEXT NOT NULL,
        exact_text TEXT,
        context TEXT,
        page_number INTEGER,
        confidence REAL,
        marine_relevance REAL,
        metadata TEXT,  -- JSON blob for category-specific fields
        extraction_hash TEXT,
        FOREIGN KEY (document_id) REFERENCES documents(id)
    );

    CREATE TABLE IF NOT EXISTS cross_references (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        extraction1_id INTEGER NOT NULL,
        extraction2_id INTEGER NOT NULL,
        link_type TEXT NOT NULL,
        confidence REAL DEFAULT 1.0,
        FOREIGN KEY (extraction1_id) REFERENCES extractions(id),
        FOREIGN KEY (extraction2_id) REFERENCES extractions(id)
    );

    CREATE TABLE IF NOT EXISTS integrated_knowledge (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        entity_type TEXT NOT NULL,
        entity_name TEXT NOT NULL,
        legal_mentions INTEGER DEFAULT 0,
        research_mentions INTEGER DEFAULT 0,
        data_sources INTEGER DEFAULT 0,
        metadata TEXT
    );

    CREATE INDEX IF NOT EXISTS idx_ext_category ON extractions(category);
    CREATE INDEX IF NOT EXISTS idx_ext_confidence ON extractions(confidence);
    CREATE INDEX IF NOT EXISTS idx_ext_hash ON extractions(extraction_hash);
    CREATE INDEX IF NOT EXISTS idx_doc_type ON documents(doc_type);
    CREATE INDEX IF NOT EXISTS idx_ik_type ON integrated_knowledge(entity_type);
    '''

    def __init__(self, db_path="msp_knowledge.db"):
        self.db_path = db_path
        self.conn = sqlite3.connect(db_path)
        self.conn.row_factory = sqlite3.Row
        self._create_tables()

    def _create_tables(self):
        self.conn.executescript(self.SCHEMA)
        self.conn.commit()

    def _compute_hash(self, category: str, exact_text: str, context: str) -> str:
        """Compute a hash for deduplication of extractions."""
        raw = f"{category}|{exact_text or ''}|{context or ''}"
        return hashlib.sha256(raw.encode("utf-8")).hexdigest()

    def insert_document(self, filename: str, doc_type: str, language: str,
                        pages: int, source_path: Optional[str] = None) -> int:
        """Insert a document record, returns doc_id.

        If a document with the same filename already exists, returns the
        existing document id without inserting a duplicate.
        """
        try:
            cursor = self.conn.execute(
                """INSERT INTO documents (filename, doc_type, language, pages,
                                         processed_date, source_path)
                   VALUES (?, ?, ?, ?, ?, ?)""",
                (filename, doc_type, language, pages,
                 datetime.now().isoformat(), source_path)
            )
            self.conn.commit()
            return cursor.lastrowid
        except sqlite3.IntegrityError:
            # Document already exists – return existing id
            row = self.conn.execute(
                "SELECT id FROM documents WHERE filename = ?", (filename,)
            ).fetchone()
            return row["id"]

    def insert_extraction(self, document_id: int, category: str,
                          extraction_data: Dict) -> int:
        """Insert a single extraction and return its id.

        ``extraction_data`` is a dict that may contain the keys:
        exact_text, context, page_number, confidence, marine_relevance,
        and any additional category-specific fields stored as JSON metadata.
        """
        exact_text = extraction_data.get("exact_text", "")
        context = extraction_data.get("context", "")
        page_number = extraction_data.get("page_number")
        confidence = extraction_data.get("confidence", 0.0)
        marine_relevance = extraction_data.get("marine_relevance")
        extraction_hash = self._compute_hash(category, exact_text, context)

        # Everything that is not a standard column goes into metadata
        standard_keys = {
            "exact_text", "context", "page_number",
            "confidence", "marine_relevance"
        }
        extra = {k: v for k, v in extraction_data.items()
                 if k not in standard_keys}
        metadata_json = json.dumps(extra, ensure_ascii=False) if extra else None

        # Skip duplicates based on hash
        existing = self.conn.execute(
            "SELECT id FROM extractions WHERE extraction_hash = ? AND document_id = ?",
            (extraction_hash, document_id)
        ).fetchone()
        if existing:
            return existing["id"]

        cursor = self.conn.execute(
            """INSERT INTO extractions
               (document_id, category, exact_text, context, page_number,
                confidence, marine_relevance, metadata, extraction_hash)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (document_id, category, exact_text, context, page_number,
             confidence, marine_relevance, metadata_json, extraction_hash)
        )
        self.conn.commit()
        return cursor.lastrowid

    def insert_batch_extractions(self, document_id: int, category: str,
                                 extractions_list: List[Dict]) -> List[int]:
        """Insert multiple extractions for a category. Returns list of ids."""
        ids = []
        for ext in extractions_list:
            ext_id = self.insert_extraction(document_id, category, ext)
            ids.append(ext_id)
        return ids

    def query_extractions(self, category: Optional[str] = None,
                          min_confidence: float = 0.0,
                          doc_type: Optional[str] = None,
                          limit: int = 100) -> List[Dict]:
        """Query extractions with filters.

        Returns a list of dicts with extraction fields plus the document
        filename and doc_type.
        """
        query = """
            SELECT e.id, e.category, e.exact_text, e.context,
                   e.page_number, e.confidence, e.marine_relevance,
                   e.metadata, d.filename, d.doc_type
            FROM extractions e
            JOIN documents d ON e.document_id = d.id
            WHERE e.confidence >= ?
        """
        params: list = [min_confidence]

        if category is not None:
            query += " AND e.category = ?"
            params.append(category)

        if doc_type is not None:
            query += " AND d.doc_type = ?"
            params.append(doc_type)

        query += " ORDER BY e.confidence DESC LIMIT ?"
        params.append(limit)

        rows = self.conn.execute(query, params).fetchall()
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

    def get_document_summary(self) -> Dict:
        """Get summary statistics across all documents."""
        total_docs = self.conn.execute(
            "SELECT COUNT(*) AS cnt FROM documents"
        ).fetchone()["cnt"]

        by_type = self.conn.execute(
            "SELECT doc_type, COUNT(*) AS cnt FROM documents GROUP BY doc_type"
        ).fetchall()

        by_language = self.conn.execute(
            "SELECT language, COUNT(*) AS cnt FROM documents GROUP BY language"
        ).fetchall()

        total_pages = self.conn.execute(
            "SELECT COALESCE(SUM(pages), 0) AS total FROM documents"
        ).fetchone()["total"]

        return {
            "total_documents": total_docs,
            "total_pages": total_pages,
            "by_type": {row["doc_type"]: row["cnt"] for row in by_type},
            "by_language": {row["language"]: row["cnt"] for row in by_language},
        }

    def get_extraction_counts(self) -> Dict[str, int]:
        """Get extraction counts by category."""
        rows = self.conn.execute(
            "SELECT category, COUNT(*) AS cnt FROM extractions GROUP BY category"
        ).fetchall()
        return {row["category"]: row["cnt"] for row in rows}

    def insert_cross_reference(self, extraction1_id: int, extraction2_id: int,
                               link_type: str, confidence: float = 1.0) -> int:
        """Insert a cross-reference between two extractions."""
        # Avoid duplicate links (order-independent)
        lo, hi = sorted([extraction1_id, extraction2_id])
        existing = self.conn.execute(
            """SELECT id FROM cross_references
               WHERE extraction1_id = ? AND extraction2_id = ?
                     AND link_type = ?""",
            (lo, hi, link_type)
        ).fetchone()
        if existing:
            return existing["id"]

        cursor = self.conn.execute(
            """INSERT INTO cross_references
               (extraction1_id, extraction2_id, link_type, confidence)
               VALUES (?, ?, ?, ?)""",
            (lo, hi, link_type, confidence)
        )
        self.conn.commit()
        return cursor.lastrowid

    def insert_integrated_knowledge(self, entity_type: str, entity_name: str,
                                    legal_mentions: int = 0,
                                    research_mentions: int = 0,
                                    data_sources: int = 0,
                                    metadata: Optional[Dict] = None) -> int:
        """Insert or update an integrated knowledge entry."""
        existing = self.conn.execute(
            """SELECT id FROM integrated_knowledge
               WHERE entity_type = ? AND entity_name = ?""",
            (entity_type, entity_name)
        ).fetchone()

        metadata_json = json.dumps(metadata, ensure_ascii=False) if metadata else None

        if existing:
            self.conn.execute(
                """UPDATE integrated_knowledge
                   SET legal_mentions = ?, research_mentions = ?,
                       data_sources = ?, metadata = ?
                   WHERE id = ?""",
                (legal_mentions, research_mentions, data_sources,
                 metadata_json, existing["id"])
            )
            self.conn.commit()
            return existing["id"]

        cursor = self.conn.execute(
            """INSERT INTO integrated_knowledge
               (entity_type, entity_name, legal_mentions,
                research_mentions, data_sources, metadata)
               VALUES (?, ?, ?, ?, ?, ?)""",
            (entity_type, entity_name, legal_mentions,
             research_mentions, data_sources, metadata_json)
        )
        self.conn.commit()
        return cursor.lastrowid

    def close(self):
        """Close the database connection."""
        if self.conn:
            self.conn.close()
            self.conn = None
