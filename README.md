# MSP Knowledge Extraction System

**A modular, bilingual NLP pipeline for automated knowledge extraction from Marine Spatial Planning literature and legislation**

Author: **Ahsan Hussain Khan**
PhD Student, Universidade de Santiago de Compostela
Supervisors: David Mateo Fouz Varela, Manuel Marey Perez, Rodrigo Carballo Sanchez, Borja Alvarez Fernandez

---

## Results at a Glance

| Metric | Value |
|--------|-------|
| Documents processed | **273** (248 Q1 research + 25 Turkish legal) |
| Total extractions | **3,142** across 17 validated categories |
| Macro precision | **0.792** |
| Micro precision | **0.826** (95% CI: 0.794--0.854) |
| Categories >= 0.90 precision | **8 / 17** |
| Categories >= 0.70 precision | **12 / 17** |
| Validation samples annotated | **610** |
| Source files | **87** Python modules |
| Specialized extractors | **22** regex-based |
| Languages supported | **English + Turkish** |
| Processing | **8 parallel workers** |

> **Precision progression across development iterations:**
> v3 (0.448) --> v4 (0.514) --> v5 (0.567) --> v6 (0.711) --> v7 (0.777) --> **v9 (0.792)**

---

## Table of Contents

1. [Project Overview](#project-overview)
2. [Motivation and Scope](#motivation-and-scope)
3. [System Architecture](#system-architecture)
4. [Extraction Categories](#extraction-categories)
5. [Precision Results (v9)](#precision-results-v9)
6. [Error Analysis](#error-analysis)
7. [Pipeline Design](#pipeline-design)
8. [Multi-Stage Filtering](#multi-stage-filtering)
9. [Novel Contributions](#novel-contributions)
10. [Interactive Dashboard](#interactive-dashboard)
11. [Installation](#installation)
12. [Usage](#usage)
13. [Output Files](#output-files)
14. [Validation Methodology](#validation-methodology)
15. [Project Structure](#project-structure)
16. [Technical Notes](#technical-notes)
17. [License](#license)

---

## Project Overview

The MSP Knowledge Extraction System is a rule-based information extraction pipeline designed to systematically process large corpora of Marine Spatial Planning (MSP) documents. It extracts structured knowledge from two distinct document types -- peer-reviewed Q1 research papers and Turkish maritime legal texts -- and organizes the results into a cross-referenced knowledge base.

The system addresses a key challenge in MSP research: the need to synthesize fragmented knowledge scattered across hundreds of scientific publications and legal instruments. Rather than relying on manual literature review, this pipeline automates the extraction of stakeholders, species, methods, legal references, spatial data, conflicts, research gaps, and 15 additional categories with measured precision.

All 273 documents in the corpus are processed through 22 specialized regex-based extractors, each employing multi-stage filtering to suppress false positives from bibliography sections, garbled PDF text, non-marine content, and cross-line artifacts. The result is a structured, queryable knowledge base suitable for gap analysis, evidence synthesis, and decision support.

---

## Motivation and Scope

Marine Spatial Planning requires integrating evidence from diverse sources: oceanographic research, ecological surveys, stakeholder analyses, and legal frameworks. For Turkey's maritime zones specifically, no prior automated system has attempted to bridge the gap between international Q1 research literature and national Turkish legal instruments governing marine activities.

This project contributes:

- **Automated knowledge extraction** from 248 Q1 English-language MSP research papers and 25 Turkish-language legal documents
- **Cross-source gap detection** that identifies disconnects between what research recommends and what law mandates
- **Bilingual processing** with language-specific regex patterns, keyword dictionaries, and false positive filters for both English and Turkish (including full Turkish character support: c, g, i, o, s, u)
- **Reproducible validation** with seed-controlled sampling (seed=42), manual annotation, and Wilson confidence interval computation

---

## System Architecture

```
                          +------------------+
                          |    main.py       |
                          |  (Orchestrator)  |
                          +--------+---------+
                                   |
                    +--------------+--------------+
                    |              |               |
             +------+------+ +----+-----+ +------+------+
             | Q1 Paper    | | Legal    | | Dataset     |
             | Processor   | | Processor| | Processor   |
             | (13 extrs)  | | (10 ext) | | (metadata)  |
             +------+------+ +----+-----+ +------+------+
                    |              |               |
                    +--------------+--------------+
                                   |
                    +-----------------------------+
                    |     22 Extractors           |
                    |  (base_extractor.py parent) |
                    +-----------------------------+
                                   |
                    +-----------------------------+
                    |   Multi-Stage Filtering     |
                    |  Bibliography | Garble |     |
                    |  Marine Rel.  | FP     |     |
                    |  Deduplication              |
                    +-----------------------------+
                                   |
                    +-----------------------------+
                    |   Knowledge Base (SQLite)   |
                    |  + Cross-Linker             |
                    +-----------------------------+
                                   |
              +--------------------+--------------------+
              |                    |                     |
     +--------+-------+  +--------+--------+  +--------+--------+
     | Gap Detection   |  | Decision Support|  | Outputs         |
     | research/legal/ |  | recommender/    |  | dashboard/      |
     | data/integration|  | synthesizer/    |  | reports/        |
     | + prioritizer   |  | planner/checker |  | CSV/JSON/Excel  |
     +-----------------+  +-----------------+  +-----------------+
```

The architecture follows a modular, pipeline-oriented design with clear separation between:

- **Processors** -- route documents to the appropriate set of extractors based on document type
- **Extractors** -- 22 specialized modules, each targeting a single extraction category with domain-specific regex patterns
- **Filters** -- five-component filtering chain applied to all extractions before output
- **Knowledge Base** -- SQLite storage with cross-reference linking across documents and categories
- **Gap Detection** -- four analyzers (research, legal, data, integration) with severity scoring
- **Decision Support** -- evidence synthesis, method recommendation, and compliance checking
- **Outputs** -- interactive HTML dashboards, reports, and multi-format exports

---

## Extraction Categories

The system extracts structured data across 17 validated categories. Extraction counts for the latest run (v9):

| Category | Extractions | Description |
|----------|-------------|-------------|
| legal_reference | 1,039 | Citations to laws, directives, regulations |
| method | 408 | Research methods (13 classified types: EBM, Marxan, GIS, etc.) |
| stakeholder | 296 | Named actors, agencies, user groups |
| environmental | 245 | Environmental conditions, water quality, pollution |
| species | 244 | Marine species (scientific and common names) |
| data_source | 227 | Datasets, monitoring systems, remote sensing |
| policy | 185 | Policy frameworks and instruments |
| gap | 165 | Explicitly stated research gaps |
| institution | 153 | Named organizations and governing bodies |
| distance | 61 | Spatial distances, buffer zones, depth ranges |
| protected_area | 37 | Marine Protected Areas and conservation zones |
| temporal | 22 | Temporal restrictions and seasonal regulations |
| penalty | 19 | Legal penalties, fines, sanctions |
| permit | 10 | Permits, licenses, authorization requirements |
| conflict | 9 | Marine use conflicts (with taxonomy and resolution) |
| objective | 7 | Stated research or policy objectives |
| prohibition | 6 | Explicit activity prohibitions |
| **Total** | **3,142** | |

Additional small categories (coordinate: 3, finding: 2, result: 2, conclusion: 2) are extracted but excluded from the main validation due to insufficient sample size.

---

## Precision Results (v9)

All precision estimates are based on manual annotation of 610 stratified random samples (seed=42) with Wilson score 95% confidence intervals.

| Category | N Validated | Correct | Precision | 95% CI |
|----------|-------------|---------|-----------|--------|
| conflict | 9 | 9 | **1.000** | [0.701--1.000] |
| legal_reference | 50 | 50 | **1.000** | [0.929--1.000] |
| prohibition | 6 | 6 | **1.000** | [0.610--1.000] |
| environmental | 50 | 49 | **0.980** | [0.895--0.996] |
| species | 50 | 49 | **0.980** | [0.895--0.996] |
| stakeholder | 50 | 48 | **0.960** | [0.865--0.989] |
| data_source | 50 | 46 | **0.920** | [0.812--0.968] |
| method | 50 | 45 | **0.900** | [0.786--0.957] |
| gap | 50 | 42 | **0.840** | [0.715--0.917] |
| protected_area | 37 | 29 | **0.784** | [0.628--0.886] |
| distance | 50 | 37 | **0.740** | [0.604--0.841] |
| institution | 50 | 35 | **0.700** | [0.562--0.809] |
| penalty | 19 | 11 | 0.579 | [0.363--0.769] |
| objective | 7 | 4 | 0.571 | [0.250--0.842] |
| policy | 50 | 28 | 0.560 | [0.423--0.688] |
| temporal | 22 | 12 | 0.545 | [0.347--0.731] |
| permit | 10 | 4 | 0.400 | [0.168--0.687] |
| **Macro Average** | **610** | **504** | **0.792** | |
| **Micro Average** | **610** | **504** | **0.826** | [0.794--0.854] |

**Summary:** 12 of 17 categories achieve precision >= 0.70. Eight categories achieve precision >= 0.90. The top-performing categories (conflict, legal_reference, prohibition, environmental, species, stakeholder) all exceed 0.95 precision.

---

## Error Analysis

Of the 106 errors identified across 610 validation samples, the distribution by error type is:

| Error Type | Count | Percentage | Description |
|------------|-------|------------|-------------|
| false_positive | 33 | 31.1% | Extracted text does not represent claimed category |
| extraction_error | 26 | 24.5% | Partial or malformed extraction |
| wrong_category | 25 | 23.6% | Valid extraction assigned to incorrect category |
| reference_only | 6 | 5.7% | Extracted from bibliography rather than body text |
| wrong_value | 4 | 3.8% | Correct category but incorrect value captured |
| garbled_text | 4 | 3.8% | PDF parsing artifact passed through filters |
| generic_term | 3 | 2.8% | Overly generic term lacking specificity |
| non_marine | 2 | 1.9% | Content not related to marine domain |

The three dominant error types (false_positive, extraction_error, wrong_category) account for 79.2% of all errors. Each version iteration has systematically targeted these categories through improved regex patterns, tighter capture group constraints, and enhanced filtering rules.

---

## Pipeline Design

The extraction pipeline operates in five sequential phases:

### Phase 1: Document Discovery
- Scans research and legal directories for PDF files
- Classifies each document by type (Q1 research paper or legal document)
- Detects document language (English or Turkish)

### Phase 2: Extraction (Parallelized)
- Routes each document to the appropriate processor (Q1PaperProcessor or LegalProcessor)
- Q1 papers pass through 13 extractors; legal documents through 10 extractors
- Extraction runs on 8 parallel workers using Python's `concurrent.futures`
- Each extractor applies multi-stage filtering before emitting results

### Phase 3: Knowledge Base Construction
- Ingests all extraction results from JSON into a SQLite database
- Cross-linker identifies relationships between extractions across documents
- Builds cross-reference tables linking species to methods, stakeholders to conflicts, MPAs to legal references

### Phase 4: Gap Detection
- **Research gaps:** Identifies methodological, geographic, and temporal gaps in the literature
- **Legal gaps:** Detects missing regulations, weak enforcement provisions, undefined penalties
- **Data gaps:** Finds missing or outdated data types referenced but not available
- **Integration gaps:** Discovers disconnects between research recommendations and legal mandates
- Gap prioritizer scores each gap by severity and actionability

### Phase 5: Reports and Outputs
- Generates an interactive HTML dashboard with Chart.js visualizations
- Produces text and Markdown reports summarizing findings
- Exports data in CSV, JSON, and Excel formats for further analysis

---

## Multi-Stage Filtering

A key design principle is that raw regex extraction produces unacceptably high false positive rates (83% noise in ablation studies against a keyword-only baseline). The system applies five filtering stages sequentially:

### 1. Bibliography Detector
Identifies and excludes bibliography, references, and acknowledgment sections using five complementary methods:
- **Header detection** -- recognizes "References", "Bibliography", "Kaynakca" section headings
- **CRediT statement detection** -- identifies author contribution statements
- **Citation density scoring** -- flags paragraphs with abnormally high citation rates
- **DOI density scoring** -- detects clusters of DOI strings
- **Author-year density scoring** -- identifies (Author, Year) pattern clusters

### 2. Cross-Line Garble Detector
Rejects matches that span line breaks (`\n` within the captured text), which typically indicate PDF text extraction artifacts where fragments from adjacent columns or pages are concatenated.

### 3. Marine Relevance Scorer
Computes a relevance score for each extraction based on co-occurring marine keywords. Thresholds are calibrated per document type:
- Scientific documents: 0.20 minimum relevance
- Legal documents: 0.15 minimum relevance

This filter prevents extraction of superficially matching content from non-marine sections (e.g., building dimensions from construction law).

### 4. False Positive Filter
Applies category-specific blacklists and structural rules:
- Minimum and maximum word counts for captured text
- Character-class restrictions (e.g., `[^,.;\[\]()\n\r<>]{3,40}` for conflict activities)
- Marine keyword whitelists requiring at least one marine term in context
- Domain-specific exclusion lists (natural processes excluded from activity conflicts)

### 5. Deduplication Engine
Removes duplicate extractions within and across documents using normalized text comparison.

---

## Novel Contributions

### 1. Integration Gap Detector
The primary methodological contribution: a system that identifies disconnects *across* document types rather than within a single document. By comparing what research papers recommend against what legal instruments mandate, the detector surfaces:

- **Unprotected important species** -- species mentioned in 3+ research papers with no legal protection status found
- **Legal-data mismatches** -- laws requiring data or analyses that do not appear in the research corpus
- **Method-legal disconnects** -- research methods widely adopted but not legally mandated or referenced
- **Unmonitored MPAs** -- protected areas designated in law but lacking monitoring data in research
- **Research-policy disconnects** -- research recommendations not reflected in legal instruments

### 2. Conflict Taxonomy
Marine use conflicts are classified into four types with structured extraction:
- **Spatial conflicts** -- overlapping use zones
- **Temporal conflicts** -- competing seasonal demands
- **Resource conflicts** -- shared resource competition
- **Governance conflicts** -- jurisdictional overlaps

Each conflict extraction includes resolution strategies and cross-links to relevant stakeholders and spatial data where available.

### 3. Bilingual Extraction
All 22 extractors support both English and Turkish with language-specific:
- Regex patterns accommodating Turkish morphology and characters (c, g, i, o, s, u)
- Keyword dictionaries covering marine and legal terminology in both languages
- Turkish number conversion (e.g., "yuz metre" to "100 metre")
- Turkish sentence segmentation handling suffixed postpositions

### 4. Multi-Stage Filtering Pipeline
The five-component filtering chain reduces false positive rates by 83% compared to a keyword-only baseline, as measured by ablation study. Each filtering component is independently toggleable for ablation analysis.

---

## Interactive Dashboard

The pipeline generates a fully interactive HTML dashboard (`dashboard.html`) in the project root directory. The dashboard provides:

- **Extraction overview** -- bar charts of extraction counts by category
- **Precision visualization** -- precision scores with confidence interval error bars
- **Document coverage** -- heatmap of which categories appear in which documents
- **Gap analysis summary** -- severity-ranked gap listings with category breakdown
- **Cross-reference explorer** -- linked view of relationships between extractions

Open `dashboard.html` in any modern web browser for the full interactive view. The dashboard is self-contained (uses Chart.js via CDN) and requires no server.

---

## Installation

### Requirements

- Python 3.10 or higher
- Operating system: Windows, Linux, or macOS

### Dependencies

**Required:**
```
pdfplumber>=0.9.0
```

**Optional (for visualization and export):**
```
matplotlib>=3.5.0
openpyxl>=3.0.0
```

### Setup

```bash
# Clone or copy the project directory
cd msp_extractor_modular

# Install dependencies
pip install pdfplumber

# Optional: install visualization and export dependencies
pip install matplotlib openpyxl
```

No additional NLP models, embeddings, or external services are required. The system is entirely self-contained and runs offline.

---

## Usage

### Full Pipeline

```bash
python main.py \
    --research-dir /path/to/q1_papers \
    --legal-dir /path/to/legal_docs \
    --output-dir ./output
```

### Arguments

| Argument | Required | Description |
|----------|----------|-------------|
| `--research-dir` | Yes | Path to directory containing Q1 research paper PDFs |
| `--legal-dir` | Yes | Path to directory containing legal document PDFs |
| `--output-dir` | No | Output directory (default: `./output`) |

### Validation Workflow

After running the pipeline, validation is performed in four steps:

```bash
# 1. Generate stratified validation sheets (seed=42 for reproducibility)
python scripts/generate_validation_sheets.py \
    --input output_final9/raw_results_20260219_152227.json \
    --output-dir validation_sheets_v9/

# 2. Manually annotate is_correct (y/n) for each sample in the CSV files

# 3. Compute precision metrics with Wilson confidence intervals
python scripts/compute_metrics.py \
    --sheets-dir validation_sheets_v9_final/

# 4. (Optional) Generate LaTeX tables for publication
python scripts/generate_paper_tables.py
```

---

## Output Files

| File | Description |
|------|-------------|
| `raw_results_*.json` | Complete extraction results in structured JSON |
| `knowledge.db` | SQLite database with all extractions and cross-references |
| `dashboard_*.html` | Interactive HTML dashboard with Chart.js visualizations |
| `gap_report_*.txt` | Detailed gap analysis report (research, legal, data, integration) |
| `extractions_*.csv` | All extractions in tabular format for analysis |
| `gaps_*.csv` | Detected gaps with severity ratings and category labels |
| `paper_tables.tex` | LaTeX tables formatted for journal submission |
| `publication_results.md` | Summary results formatted for manuscript preparation |

---

## Validation Methodology

Precision is measured through manual annotation of stratified random samples:

1. **Sampling:** For each category with more than 50 extractions, 50 samples are drawn using stratified random sampling (seed=42). Categories with fewer than 50 extractions are validated exhaustively.

2. **Annotation:** Each sample is reviewed and marked as correct (`y`) or incorrect (`n`). Incorrect samples are further categorized by error type (false_positive, extraction_error, wrong_category, reference_only, wrong_value, garbled_text, generic_term, non_marine).

3. **Metrics:** Precision is computed as the proportion of correct extractions. Wilson score confidence intervals are used rather than normal approximation intervals, providing better coverage for small sample sizes and extreme proportions.

4. **Reproducibility:** The fixed random seed (42) ensures identical samples are drawn across runs. When only a subset of extractors are modified between versions, annotations for unchanged categories are carried forward, avoiding redundant re-annotation.

5. **Aggregation:** Macro-averaged precision (unweighted mean across categories) and micro-averaged precision (total correct / total validated, weighted by sample size) are both reported.

---

## Project Structure

```
msp_extractor_modular/
|
|-- main.py                            Pipeline orchestrator (parallel processing)
|-- config.py                          Configuration and thresholds
|-- core/
|   +-- enums.py                       DocumentType, ExtractionCategory enums
|
|-- extractors/                        22 regex-based extractors
|   |-- base_extractor.py             Abstract base (bibliography + garble detection)
|   |-- conflict_extractor.py         Marine use conflicts (taxonomy + resolution)
|   |-- distance_extractor.py         Spatial distances and buffer zones
|   |-- species_extractor.py          Marine species (scientific + common names)
|   |-- method_extractor.py           Research methods (13 classified types)
|   |-- finding_extractor.py          Research findings with quantitative evidence
|   |-- environmental_extractor.py    Environmental conditions and parameters
|   |-- stakeholder_extractor.py      Stakeholders, actors, and user groups
|   |-- policy_extractor.py           Policy frameworks and instruments
|   |-- institution_extractor.py      Organizations and governing bodies
|   |-- data_source_extractor.py      Datasets, monitoring, and remote sensing
|   |-- penalty_extractor.py          Legal penalties and fines
|   |-- temporal_extractor.py         Temporal and seasonal restrictions
|   |-- permit_extractor.py           Permits, licenses, authorizations
|   |-- protected_area_extractor.py   MPAs and conservation zones
|   |-- prohibition_extractor.py      Activity prohibitions
|   |-- coordinate_extractor.py       Geographic coordinates
|   |-- legal_reference_extractor.py  Legal citations and references
|   |-- objective_extractor.py        Research and policy objectives
|   |-- result_extractor.py           Quantitative results
|   |-- conclusion_extractor.py       Research conclusions
|   +-- gap_extractor.py              Explicitly stated research gaps
|
|-- processors/                        Document-type orchestrators
|   |-- q1_paper_processor.py         13 extractors for Q1 research papers
|   |-- legal_processor.py            10 extractors for Turkish legal documents
|   +-- dataset_processor.py          Dataset metadata extraction
|
|-- utils/                             Shared NLP utilities
|   |-- keywords.py                   Marine and legal keyword dictionaries (TR + EN)
|   |-- filters.py                    FalsePositiveFilter, GarbleDetector
|   |-- bibliography_detector.py      5-method bibliography section detection
|   |-- nlp_filters.py               NLP-based filtering rules
|   |-- text_processing.py           Turkish segmenter, number converter
|   |-- language_detection.py         Language detection
|   +-- pdf_parser.py                PDF text extraction (pdfplumber)
|
|-- data_structures/
|   |-- extraction_models.py          21 extraction dataclasses
|   +-- integrated.py                 Cross-reference and Gap models
|
|-- knowledge_base/                    SQLite storage and cross-referencing
|   |-- database.py                   Schema (documents, extractions, cross_refs)
|   |-- knowledge_builder.py          JSON to SQLite ingestion
|   |-- query_engine.py              Analytical query interface
|   +-- cross_linker.py              Link species/methods/MPAs across sources
|
|-- gap_detection/                     Gap analysis (novel contribution)
|   |-- research_gaps.py             Methodological, geographic, temporal gaps
|   |-- legal_gaps.py                Missing regulations, enforcement gaps
|   |-- data_gaps.py                 Missing or outdated data types
|   |-- integration_gaps.py          Cross-source disconnects
|   +-- gap_prioritizer.py           Severity scoring and ranking
|
|-- decision_support/                  Actionable recommendations
|   |-- method_recommender.py        Evidence-based method recommendations
|   |-- evidence_synthesizer.py      Findings aggregation across papers
|   |-- data_collection_planner.py   Gap-filling data collection strategy
|   +-- legal_compliance_checker.py  Regulatory compliance checking
|
|-- validation/                        Accuracy measurement framework
|   |-- accuracy_checker.py          Full validation workflow
|   |-- manual_validator.py          Annotation sheet generation
|   |-- metrics_calculator.py        Precision/Recall/F1 with Wilson CI
|   |-- error_analyzer.py            Error type categorization
|   |-- ablation_study.py            Component ablation analysis
|   +-- baseline_extractor.py        Simple baseline for comparison
|
|-- outputs/                           Reporting and visualization
|   |-- report_generator.py          Text and Markdown reports
|   |-- dashboard_generator.py       Interactive HTML dashboard (Chart.js)
|   |-- visualizer.py                Chart generation
|   +-- export.py                    CSV, JSON, and Excel export
|
|-- scripts/                           Utility scripts
|   |-- generate_validation_sheets.py  Stratified sample generation
|   |-- compute_metrics.py             Wilson CI metrics computation
|   |-- generate_paper_tables.py       LaTeX table generation
|   |-- compute_recall_f1.py           Recall and F1 estimation
|   +-- select_recall_documents.py     Document selection for recall study
|
|-- validation_sheets_v9_final/        610 annotated validation samples (17 CSVs)
+-- output_final9/                     Latest extraction results (v9)
```

---

## Technical Notes

### Key Design Decisions

- **Regex over ML:** The system uses handcrafted regex patterns rather than machine learning models. This provides full transparency, deterministic behavior, zero training data requirements, and the ability to precisely diagnose and fix individual errors. For a domain-specific extraction task on a corpus of this size, regex with robust filtering achieves competitive precision without the overhead of model training and tuning.

- **Word boundary enforcement:** Short acronyms (AIS, VMS, ICES) require strict `\b` word boundaries to prevent substring matches within longer words.

- **Non-greedy capture constraints:** Policy and institution name patterns use minimum 2-word requirements because non-greedy `+?` quantifiers otherwise capture single words.

- **Turkish exception handling:** Words like `disinda`, `haric`, and `mustesna` are scope qualifiers in Turkish legal text, not prohibitions. The system correctly classifies these.

- **PDF text quality:** Cross-line matches (containing `\n` in the captured text), verb-fragment activities, and fragments shorter than 3 characters are rejected as PDF parsing artifacts.

- **Marine relevance thresholds:** Calibrated separately for legal (0.15+) and scientific (0.20+) documents to account for differing keyword densities.

- **Conflict extraction specificity:** Marine keyword whitelists require at least one marine term in context. Natural processes (waves, currents, sediment, erosion) are excluded from human activity extraction.

### Reproducibility

- Random seed 42 is used for all sampling operations
- PDF text extraction is deterministic (pdfplumber)
- All regex patterns are compiled at module load time
- Output JSON includes timestamps and version identifiers

---

## License

Academic research project. Developed as part of a PhD thesis on Marine Spatial Planning knowledge extraction at the Universidade de Santiago de Compostela.

---

## Interactive Dashboard

Explore the full system results, precision metrics, and architecture interactively:

**[Live Dashboard](https://drahsanhussainkhan-cmd.github.io/msp-knowledge-extraction-v9/dashboard.html)**

---

*MSP Knowledge Extraction System v9 -- February 2026*
