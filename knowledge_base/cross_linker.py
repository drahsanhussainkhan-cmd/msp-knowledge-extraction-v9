import json
import logging
from typing import Dict, List, Set, Tuple

from .database import KnowledgeDatabase

logger = logging.getLogger(__name__)


class CrossLinker:
    """Creates cross-references between extractions from different
    documents and builds integrated knowledge entries."""

    def __init__(self, db: KnowledgeDatabase):
        self.db = db

    # ------------------------------------------------------------------
    # Public entry point
    # ------------------------------------------------------------------

    def link_all(self):
        """Run all cross-linking operations."""
        logger.info("Starting cross-linking process...")
        self._link_species_across_sources()
        self._link_methods_to_data()
        self._link_legal_to_research()
        self._link_conflicts_to_stakeholders()
        self._link_conflicts_to_spatial()
        self._build_integrated_knowledge()
        logger.info("Cross-linking complete.")

    # ------------------------------------------------------------------
    # Species linking
    # ------------------------------------------------------------------

    def _link_species_across_sources(self):
        """Find same species mentioned in legal docs and research papers,
        then create cross_references entries between them."""
        logger.info("Linking species across sources...")

        rows = self.db.conn.execute("""
            SELECT e.id, e.exact_text, e.metadata, d.doc_type
            FROM extractions e
            JOIN documents d ON e.document_id = d.id
            WHERE e.category = 'species'
        """).fetchall()

        # Group extraction ids by normalised species name
        species_groups: Dict[str, Dict[str, List[int]]] = {}
        for row in rows:
            name = self._extract_entity_name(row, field="species_name")
            if not name:
                continue
            key = name.lower().strip()
            doc_type = row["doc_type"] or "unknown"
            species_groups.setdefault(key, {}).setdefault(doc_type, []).append(row["id"])

        links_created = 0
        for species, type_map in species_groups.items():
            doc_types = list(type_map.keys())
            # Only create links when the species appears in more than one doc_type
            if len(doc_types) < 2:
                continue
            # Create pairwise links between different doc_types
            for i in range(len(doc_types)):
                for j in range(i + 1, len(doc_types)):
                    for eid1 in type_map[doc_types[i]]:
                        for eid2 in type_map[doc_types[j]]:
                            self.db.insert_cross_reference(
                                eid1, eid2,
                                link_type="species_cross_source",
                                confidence=1.0,
                            )
                            links_created += 1

        logger.info("Species cross-linking created %d links.", links_created)

    # ------------------------------------------------------------------
    # Methods <-> Data linking
    # ------------------------------------------------------------------

    def _link_methods_to_data(self):
        """Link research methods to data sources.

        If a method extraction and a dataset extraction share the same
        document, or if they mention the same keywords, create a link.
        """
        logger.info("Linking methods to data sources...")

        methods = self.db.conn.execute("""
            SELECT e.id, e.document_id, e.exact_text, e.metadata
            FROM extractions e
            WHERE e.category = 'methods'
        """).fetchall()

        datasets = self.db.conn.execute("""
            SELECT e.id, e.document_id, e.exact_text, e.metadata, d.doc_type
            FROM extractions e
            JOIN documents d ON e.document_id = d.id
            WHERE e.category IN ('datasets', 'data_sources', 'data')
               OR d.doc_type = 'dataset'
        """).fetchall()

        # Index datasets by document_id for co-occurrence linking
        ds_by_doc: Dict[int, List[int]] = {}
        for ds in datasets:
            ds_by_doc.setdefault(ds["document_id"], []).append(ds["id"])

        # Also build a keyword index for textual matching
        ds_keywords: Dict[int, Set[str]] = {}
        for ds in datasets:
            text = (ds["exact_text"] or "").lower()
            ds_keywords[ds["id"]] = set(text.split())

        links_created = 0

        for method in methods:
            # Same-document links
            for ds_id in ds_by_doc.get(method["document_id"], []):
                self.db.insert_cross_reference(
                    method["id"], ds_id,
                    link_type="method_uses_data",
                    confidence=0.9,
                )
                links_created += 1

            # Keyword overlap links (lightweight heuristic)
            method_words = set((method["exact_text"] or "").lower().split())
            if len(method_words) < 2:
                continue
            for ds in datasets:
                if ds["document_id"] == method["document_id"]:
                    continue  # already linked above
                overlap = method_words & ds_keywords.get(ds["id"], set())
                # Require meaningful overlap (ignore very short common words)
                meaningful = {w for w in overlap if len(w) > 4}
                if len(meaningful) >= 2:
                    confidence = min(1.0, 0.5 + 0.1 * len(meaningful))
                    self.db.insert_cross_reference(
                        method["id"], ds["id"],
                        link_type="method_uses_data",
                        confidence=round(confidence, 2),
                    )
                    links_created += 1

        logger.info("Method-data linking created %d links.", links_created)

    # ------------------------------------------------------------------
    # Legal <-> Research linking
    # ------------------------------------------------------------------

    def _link_legal_to_research(self):
        """Link legal requirements to supporting research.

        When a legal extraction and a research extraction share
        significant keyword overlap, create a supporting-evidence link.
        """
        logger.info("Linking legal requirements to research...")

        legal_rows = self.db.conn.execute("""
            SELECT e.id, e.exact_text, e.context, e.category
            FROM extractions e
            JOIN documents d ON e.document_id = d.id
            WHERE d.doc_type = 'legal'
        """).fetchall()

        research_rows = self.db.conn.execute("""
            SELECT e.id, e.exact_text, e.context, e.category
            FROM extractions e
            JOIN documents d ON e.document_id = d.id
            WHERE d.doc_type = 'research'
        """).fetchall()

        if not legal_rows or not research_rows:
            logger.info("No legal or research rows to link.")
            return

        # Build keyword sets
        def _keywords(row) -> Set[str]:
            text = f"{row['exact_text'] or ''} {row['context'] or ''}".lower()
            return {w for w in text.split() if len(w) > 4}

        research_kw: List[Tuple[int, Set[str]]] = [
            (r["id"], _keywords(r)) for r in research_rows
        ]

        links_created = 0
        for legal in legal_rows:
            lkw = _keywords(legal)
            if len(lkw) < 2:
                continue
            for rid, rkw in research_kw:
                overlap = lkw & rkw
                meaningful = {w for w in overlap if len(w) > 5}
                if len(meaningful) >= 3:
                    confidence = min(1.0, 0.4 + 0.1 * len(meaningful))
                    self.db.insert_cross_reference(
                        legal["id"], rid,
                        link_type="legal_research_support",
                        confidence=round(confidence, 2),
                    )
                    links_created += 1

        logger.info("Legal-research linking created %d links.", links_created)

    # ------------------------------------------------------------------
    # Conflict <-> Stakeholder linking
    # ------------------------------------------------------------------

    def _link_conflicts_to_stakeholders(self):
        """Link conflict extractions to stakeholders in the same document.

        Uses same-document co-occurrence with keyword overlap boost.
        """
        logger.info("Linking conflicts to stakeholders...")

        conflicts = self.db.conn.execute("""
            SELECT e.id, e.document_id, e.exact_text, e.metadata
            FROM extractions e
            WHERE e.category = 'conflict'
        """).fetchall()

        stakeholders = self.db.conn.execute("""
            SELECT e.id, e.document_id, e.exact_text, e.metadata
            FROM extractions e
            WHERE e.category = 'stakeholder'
        """).fetchall()

        if not conflicts or not stakeholders:
            logger.info("No conflicts or stakeholders to link.")
            return

        # Index stakeholders by document_id
        sh_by_doc: Dict[int, List] = {}
        for sh in stakeholders:
            sh_by_doc.setdefault(sh["document_id"], []).append(sh)

        links_created = 0
        for conflict in conflicts:
            conflict_text = (conflict["exact_text"] or "").lower()
            conflict_kw = {w for w in conflict_text.split() if len(w) > 3}

            for sh in sh_by_doc.get(conflict["document_id"], []):
                sh_name = self._extract_entity_name(sh, field="stakeholder_name").lower()
                sh_words = {w for w in sh_name.split() if len(w) > 3}

                # Keyword overlap between conflict text and stakeholder name
                overlap = conflict_kw & sh_words
                confidence = 0.8 if overlap else 0.6  # same-doc baseline

                self.db.insert_cross_reference(
                    conflict["id"], sh["id"],
                    link_type="conflict_involves_stakeholder",
                    confidence=round(confidence, 2),
                )
                links_created += 1

        logger.info("Conflict-stakeholder linking created %d links.", links_created)

    # ------------------------------------------------------------------
    # Conflict <-> Spatial linking
    # ------------------------------------------------------------------

    def _link_conflicts_to_spatial(self):
        """Link conflict extractions to spatial data (protected areas,
        distances, coordinates) in the same document."""
        logger.info("Linking conflicts to spatial data...")

        conflicts = self.db.conn.execute("""
            SELECT e.id, e.document_id
            FROM extractions e
            WHERE e.category = 'conflict'
        """).fetchall()

        spatial = self.db.conn.execute("""
            SELECT e.id, e.document_id, e.category
            FROM extractions e
            WHERE e.category IN ('protected_area', 'distance', 'coordinate')
        """).fetchall()

        if not conflicts or not spatial:
            logger.info("No conflicts or spatial data to link.")
            return

        # Index spatial extractions by document_id
        spatial_by_doc: Dict[int, List] = {}
        for sp in spatial:
            spatial_by_doc.setdefault(sp["document_id"], []).append(sp)

        links_created = 0
        for conflict in conflicts:
            for sp in spatial_by_doc.get(conflict["document_id"], []):
                link_type = f"conflict_in_{sp['category']}"
                self.db.insert_cross_reference(
                    conflict["id"], sp["id"],
                    link_type=link_type,
                    confidence=0.7,
                )
                links_created += 1

        logger.info("Conflict-spatial linking created %d links.", links_created)

    # ------------------------------------------------------------------
    # Integrated knowledge
    # ------------------------------------------------------------------

    def _build_integrated_knowledge(self):
        """Build the integrated_knowledge table from extraction data.

        For each entity type (species, methods, mpas) counts how many
        times it appears in legal documents, research documents, and
        data sources.
        """
        logger.info("Building integrated knowledge entries...")

        entity_configs = [
            ("species", "species", "species_name"),
            ("methods", "methods", "method_name"),
            ("mpas", "mpas", "mpa_name"),
        ]

        total_entries = 0

        for entity_type, category, name_field in entity_configs:
            rows = self.db.conn.execute("""
                SELECT e.exact_text, e.metadata, d.doc_type
                FROM extractions e
                JOIN documents d ON e.document_id = d.id
                WHERE e.category = ?
            """, (category,)).fetchall()

            # Group by entity name
            entity_stats: Dict[str, Dict[str, int]] = {}
            for row in rows:
                name = self._extract_entity_name(row, field=name_field)
                if not name:
                    continue
                key = name.lower().strip()
                stats = entity_stats.setdefault(key, {
                    "display_name": name,
                    "legal": 0,
                    "research": 0,
                    "dataset": 0,
                })
                doc_type = (row["doc_type"] or "unknown").lower()
                if doc_type == "legal":
                    stats["legal"] += 1
                elif doc_type == "research":
                    stats["research"] += 1
                elif doc_type in ("dataset", "data"):
                    stats["dataset"] += 1

            for key, stats in entity_stats.items():
                self.db.insert_integrated_knowledge(
                    entity_type=entity_type,
                    entity_name=stats["display_name"],
                    legal_mentions=stats["legal"],
                    research_mentions=stats["research"],
                    data_sources=stats["dataset"],
                    metadata={"normalised_key": key},
                )
                total_entries += 1

        logger.info("Built %d integrated knowledge entries.", total_entries)

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _extract_entity_name(row, field: str = "name") -> str:
        """Extract an entity name from either metadata JSON or exact_text."""
        if row["metadata"]:
            try:
                meta = json.loads(row["metadata"]) if isinstance(row["metadata"], str) else row["metadata"]
                name = meta.get(field) or meta.get("name")
                if name:
                    return str(name).strip()
            except (json.JSONDecodeError, TypeError, AttributeError):
                pass
        return (row["exact_text"] or "").strip()
