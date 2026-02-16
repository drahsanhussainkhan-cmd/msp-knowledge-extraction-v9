# MSP Knowledge Extraction & Decision Support System

A bilingual (Turkish + English) NLP pipeline for extracting structured knowledge from Marine Spatial Planning documents, detecting cross-source gaps, and providing decision support.

## What It Does

Processes **273 PDF documents** (25 Turkish legal documents + 248 Q1 research papers) and:
1. **Extracts** 8,836 structured data points across 21 categories
2. **Builds** a cross-referenced SQLite knowledge base
3. **Detects** 80 gaps across research, legal, data, and integration dimensions
4. **Generates** reports, dashboards, and decision support outputs

## Architecture

```
msp_extractor_modular/
├── main.py                          # Pipeline orchestrator
├── config.py                        # Configuration & thresholds
├── core/
│   └── enums.py                     # DocumentType, ExtractionCategory enums
├── utils/                           # Shared NLP utilities
│   ├── keywords.py                  # MSP keyword dictionaries (TR+EN)
│   ├── filters.py                   # FalsePositiveFilter, LegalReferenceFilter
│   ├── text_processing.py           # Sentence segmenter, number converter
│   ├── language_detection.py        # Language detector
│   └── pdf_parser.py               # PDF text extraction (pdfplumber)
├── data_structures/
│   ├── extraction_models.py         # 21 extraction dataclasses
│   └── integrated.py               # Cross-reference & Gap dataclasses
├── extractors/                      # 21 regex-based extractors
│   ├── base_extractor.py           # Abstract base class
│   ├── species_extractor.py        # Marine species (724 extractions)
│   ├── method_extractor.py         # Research methods (585, 13 types)
│   ├── stakeholder_extractor.py    # Stakeholders (795 extractions)
│   ├── environmental_extractor.py  # Environmental conditions (529)
│   ├── finding_extractor.py        # Research findings (2,180)
│   ├── institution_extractor.py    # Institutions
│   ├── conflict_extractor.py       # Use conflicts
│   ├── policy_extractor.py         # Policy references
│   ├── data_source_extractor.py    # Data sources
│   ├── distance_extractor.py       # Distance/buffer zones
│   ├── penalty_extractor.py        # Penalties/fines
│   ├── temporal_extractor.py       # Temporal restrictions
│   ├── permit_extractor.py         # Permits/licenses
│   ├── protected_area_extractor.py # Protected areas/MPAs
│   ├── prohibition_extractor.py    # Prohibitions
│   ├── coordinate_extractor.py     # Geographic coordinates
│   ├── legal_reference_extractor.py# Legal references
│   ├── objective_extractor.py      # Research objectives
│   ├── result_extractor.py         # Quantitative results
│   ├── conclusion_extractor.py     # Conclusions
│   └── gap_extractor.py            # Research gaps identified
├── processors/                      # Document-type orchestrators
│   ├── q1_paper_processor.py       # 13 extractors for research papers
│   ├── legal_processor.py          # 10 extractors for legal documents
│   └── dataset_processor.py        # Dataset metadata extraction
├── knowledge_base/                  # SQLite storage & cross-referencing
│   ├── database.py                 # Schema (documents, extractions, cross_refs)
│   ├── knowledge_builder.py        # Ingest JSON results into DB
│   ├── query_engine.py             # Pre-built analytical queries
│   └── cross_linker.py            # Link species/methods/MPAs across sources
├── gap_detection/                   # Novel contribution
│   ├── research_gaps.py            # Methodological, geographic, temporal gaps
│   ├── legal_gaps.py               # Missing regulations, weak enforcement
│   ├── data_gaps.py                # Missing/outdated data types
│   ├── integration_gaps.py         # Cross-source disconnects (key novelty)
│   └── gap_prioritizer.py         # Score gaps by severity/actionability
├── decision_support/                # Actionable recommendations
│   ├── method_recommender.py       # Evidence-based method recommendations
│   ├── evidence_synthesizer.py     # Aggregate findings across papers
│   ├── data_collection_planner.py  # Plan data collection to fill gaps
│   └── legal_compliance_checker.py # Check activity compliance
├── validation/                      # Accuracy measurement
│   ├── metrics_calculator.py       # P/R/F1, confusion matrix, macro/micro avg
│   ├── manual_validator.py         # Generate annotation sheets for review
│   └── accuracy_checker.py         # Full validation workflow
└── outputs/                         # Reporting & visualization
    ├── report_generator.py         # Gap analysis reports (markdown/text)
    ├── dashboard_generator.py      # Interactive HTML dashboard (Chart.js)
    ├── visualizer.py               # Charts & visualizations
    └── export.py                   # CSV/JSON/Excel export
```

## Quick Start

### Requirements
```bash
pip install pdfplumber
```

### Run the full pipeline
```bash
python main.py \
  --research-dir /path/to/q1_papers \
  --legal-dir /path/to/legal_docs \
  --output-dir ./output
```

### Output Files
| File | Description |
|------|-------------|
| `knowledge.db` | SQLite database with all extractions and cross-references |
| `dashboard_*.html` | Interactive HTML dashboard with charts |
| `gap_report_*.txt` | Detailed gap analysis report |
| `extractions_*.csv` | All extractions in tabular format |
| `gaps_*.csv` | All detected gaps with severity ratings |
| `raw_results_*.json` | Complete JSON results |

## Results Summary (273 documents)

### Extraction Categories
| Category | Count | Notes |
|----------|-------|-------|
| Findings | 2,180 | Research findings from Q1 papers |
| Institutions | 1,297 | Named institutions and organizations |
| Stakeholders | 795 | 35 named + 760 role-based mentions |
| Species | 724 | 145 unique marine species |
| Methods | 585 | 13 classified types (EBM, Marxan, GIS, etc.) |
| Environmental | 529 | Water quality, pollution, noise |
| Policy | 471 | Policy references and frameworks |
| Data Sources | 383 | Research datasets and monitoring data |
| Conflicts | 201 | Use-use and use-environment conflicts |
| + 12 more | 1,671 | Legal: distances, penalties, permits, coordinates, etc. |
| **Total** | **8,836** | |

### Gap Detection (80 gaps)
| Category | Count | Severity |
|----------|-------|----------|
| Research gaps | 31 | Methodological, geographic, temporal |
| Integration gaps | 27 | Cross-source disconnects |
| Legal gaps | 14 | Missing regulations, enforcement |
| Data gaps | 8 | Missing essential data types |
| **Critical** | **39** | Require immediate attention |
| **Important** | **40** | Should be addressed |

### Method Type Classification
| Type | Count |
|------|-------|
| Conservation planning tool (Marxan, Zonation) | 247 |
| Ecosystem-based management | 207 |
| Participatory methods | 47 |
| Suitability analysis | 41 |
| Remote sensing / habitat mapping | 15 |
| Multi-criteria analysis | 8 |
| + 7 more types | 20 |

## Novel Contribution

The **Integration Gap Detector** identifies disconnects ACROSS document types:

1. **Unprotected Important Species**: Species mentioned in 3+ research papers but with no legal protection status
2. **Legal-Data Mismatch**: Laws requiring data/analysis that doesn't exist in the corpus
3. **Method-Legal Disconnect**: Research methods widely used but not legally mandated
4. **Unmonitored MPAs**: Marine Protected Areas designated but with no monitoring data
5. **Data Access Barriers**: High proportion of restricted/proprietary data sources
6. **Research-Policy Disconnect**: Many research recommendations but few policy references

## Bilingual Support

All extractors support both Turkish and English with language-specific:
- Regex patterns (Turkish characters: ÇĞIÖŞÜ, suffixes, legal terminology)
- False positive filters
- Marine relevance scoring
- Number conversion ("yuz metre" -> "100 metre")

## Validation (TODO)

The validation framework is built but ground truth annotation is pending:
- `ManualValidator`: Generates stratified annotation sheets
- `MetricsCalculator`: Computes P/R/F1 with exact and fuzzy matching
- `AccuracyChecker`: Full validation pipeline with target F1 >= 0.80

## License

Academic research project - Marine Spatial Planning knowledge extraction.
