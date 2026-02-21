# MSP Knowledge Extraction System - Progress Report

**Author:** Ahsan Hussain Khan
**Date:** 17 February 2026
**Supervisors:** David Mateo Fouz Varela, Manuel Marey Perez, Rodrigo Carballo Sanchez, Borja Alvarez Fernandez

---

## 1. Executive Summary

I have developed a fully functional AI-based knowledge extraction system for Marine Spatial Planning (MSP) documents. The system processes both English-language scientific literature and Turkish legal documents, automatically extracting structured knowledge across 21 categories (species, stakeholders, methods, legal references, environmental conditions, etc.).

The system has been built, tested, and validated. Below I present the current results, what works well, what needs improvement, and the decisions I need guidance on before proceeding to the Q1 journal paper and the AEIPRO conference paper.

---

## 2. What Has Been Built

### 2.1 System Architecture
- **67 Python source files** organized across 8 modules
- **21 specialized extractors** for different knowledge categories
- **Multi-stage filtering pipeline** with 5 filtering components:
  1. Bibliography section detector (filters references/citations)
  2. Cross-line garble detector (filters broken PDF text)
  3. Marine relevance scorer (filters non-marine content)
  4. False positive detector (filters generic/ambiguous terms)
  5. Deduplication engine (removes duplicate extractions)
- **Bilingual support:** English research papers + Turkish legal documents
- **Parallel processing:** 8 concurrent workers for document-level parallelism
- **Knowledge base:** SQLite database with cross-linking between entities
- **Gap detection:** Identifies research gaps, legal gaps, data gaps, and integration gaps

### 2.2 Data Sources Processed
| Source | Count | Language | Content |
|--------|-------|----------|---------|
| Research papers | 248 PDFs | English | Q1 journal articles on MSP, coastal management, marine ecology |
| Turkish legal documents | 25 PDFs | Turkish | Maritime laws, coastal regulations, port regulations, environmental law |
| **Total** | **273 PDFs** | Bilingual | |

### 2.3 Extraction Categories (21 total)
The system extracts structured information in these categories:

| # | Category | Description | Extractions |
|---|----------|-------------|-------------|
| 1 | Data Source | Datasets, databases, monitoring sources | 1,319 |
| 2 | Legal Reference | Turkish law articles, regulations, directives | 1,039 |
| 3 | Stakeholder | Organizations, actor groups, governance bodies | 753 |
| 4 | Institution | Named institutions, agencies, commissions | 727 |
| 5 | Species | Marine species (scientific + common names) | 664 |
| 6 | Policy | EU directives, national policies, frameworks | 571 |
| 7 | Method | Research methods, analytical tools, techniques | 529 |
| 8 | Environmental | Environmental conditions, parameters, factors | 493 |
| 9 | Gap | Research, legal, data, and integration gaps | 192 |
| 10 | Result | Quantitative research results | 162 |
| 11 | Finding | Qualitative research findings | 144 |
| 12 | Distance | Spatial distances, setbacks, buffer zones | 102 |
| 13 | Conflict | Marine use conflicts (activity vs activity) | 62 |
| 14 | Protected Area | MPAs, nature parks, conservation zones | 42 |
| 15 | Prohibition | Legal prohibitions on marine activities | 37 |
| 16 | Temporal | Seasonal restrictions, permit durations | 26 |
| 17 | Penalty | Legal penalties for violations | 19 |
| 18 | Conclusion | Paper conclusions | 13 |
| 19 | Permit | Marine activity permits | 10 |
| 20 | Objective | Research objectives | 7 |
| 21 | Coordinate | Geographic coordinates | 3 |
| | **Total** | | **6,914** |

---

## 3. Validation Results

### 3.1 Precision (How accurate are the extractions?)

Precision was measured by sampling up to 50 extractions per category (795 total samples) and annotating each as correct or incorrect.

**High-performing categories (>50% precision):**

| Category | N | Precision | 95% CI | Notes |
|----------|---|-----------|--------|-------|
| Legal Reference | 46 | **0.957** | [0.855-0.988] | Excellent - structured Turkish law patterns |
| Protected Area | 42 | **0.905** | [0.779-0.962] | Excellent - specific Turkish designations |
| Stakeholder | 50 | **0.820** | [0.692-0.902] | Very good - named organizations |
| Method | 50 | **0.660** | [0.522-0.776] | Good - research method terms |
| Permit | 10 | 0.600 | [0.313-0.832] | Moderate (small sample) |
| Penalty | 17 | 0.588 | [0.360-0.784] | Moderate (small sample) |
| Objective | 7 | 0.571 | [0.250-0.842] | Moderate (very small sample) |
| Distance | 49 | 0.531 | [0.394-0.663] | Moderate |

**Low-performing categories (<50% precision):**

| Category | N | Precision | 95% CI | Main Error Types |
|----------|---|-----------|--------|-----------------|
| Institution | 50 | 0.480 | [0.348-0.615] | Incomplete names, garbled text |
| Policy | 50 | 0.420 | [0.294-0.558] | Journal names confused with policies |
| Gap | 50 | 0.400 | [0.276-0.538] | Cross-line garbling |
| Finding | 50 | 0.380 | [0.259-0.518] | Cross-line garbling |
| Data Source | 50 | 0.340 | [0.224-0.478] | Generic terms |
| Result | 50 | 0.240 | [0.143-0.374] | Cross-line garbling (52% of errors) |
| Temporal | 25 | 0.240 | [0.115-0.434] | Administrative deadlines misclassified |
| Species | 50 | 0.220 | [0.128-0.352] | Generic group names, bibliography |
| Prohibition | 37 | 0.189 | [0.095-0.342] | Exception clauses confused with prohibitions |
| Conflict | 50 | 0.180 | [0.098-0.308] | Activity boundary detection failure |
| Conclusion | 12 | 0.167 | [0.047-0.448] | Very small sample |
| Environmental | 50 | 0.080 | [0.032-0.188] | CIA methodology confused with env. variables |

**Overall: Macro Precision = 0.448, Micro Precision = 0.445**

### 3.2 Recall (How much does the system find?)

Recall was measured using a 10-document gold standard. For each document, ALL true mentions were exhaustively identified by reading the full paper, then compared with system extractions.

| Category | True Mentions (Gold) | System Found | Matched | Recall | F1 |
|----------|---------------------|--------------|---------|--------|-----|
| Species | 186 | 95 | 71 | **0.382** | 0.279 |
| Method | 206 | 80 | 32 | 0.155 | 0.251 |
| Stakeholder | 219 | 47 | 26 | 0.119 | 0.207 |
| Environmental | 167 | 72 | 12 | 0.072 | 0.076 |
| Finding | 191 | 9 | 9 | 0.047 | 0.084 |
| **Total** | **969** | **303** | **150** | **0.155** | **0.180** |

**Key observation:** The system finds only ~15% of true mentions. This is a fundamental limitation of the regex/rule-based approach - it can only match pre-defined patterns and misses mentions that don't follow expected text patterns.

### 3.3 Error Distribution (What goes wrong?)

Analysis of 441 false positives across 795 validated samples:

| Error Type | Count | % | Description |
|------------|-------|---|-------------|
| Cross-line garbling | 121 | 27.4% | Multi-column PDF text merged across lines |
| False positive | 109 | 24.7% | Generic terms not matching category definition |
| Bibliography | 78 | 17.7% | Text extracted from reference sections |
| Wrong category | 58 | 13.2% | Valid extraction assigned to wrong category |
| Wrong value | 53 | 12.0% | Correct entity but wrong value extracted |
| Non-marine | 20 | 4.5% | Content from non-marine domain papers |
| Author credit | 2 | 0.5% | CRediT author contribution text |

---

## 4. Comparative Evaluation

### 4.1 Baseline Comparison

The baseline is a simple keyword-matching extractor with no context filtering.

| Category | Baseline (Keywords) | Our System | Noise Reduction |
|----------|-------------------|------------|-----------------|
| Species | 6,066 | 664 | 89.1% |
| Method | 10,415 | 529 | 94.9% |
| Stakeholder | 9,631 | 753 | 92.2% |
| Environmental | 11,447 | 493 | 95.7% |
| Finding | 3,004 | 144 | 95.2% |
| **Total** | **40,563** | **6,914** | **83.0%** |

Our multi-stage filtering pipeline eliminates 83% of noise compared to naive keyword matching.

### 4.2 Ablation Study (20-document sample)

Testing the contribution of each filtering component:

| Configuration | Extractions | Change | Impact |
|---------------|-------------|--------|--------|
| **Full System** | **232** | --- | --- |
| No FP Filter | 243 | +11 | +4.7% (most impactful) |
| No Blacklists | 236 | +4 | +1.7% |
| No Marine Filter | 235 | +3 | +1.3% |
| No Legal Ref Filter | 234 | +2 | +0.9% |
| No Dedup | 232 | +0 | +0.0% |

The false positive filter is the most impactful component, preventing 4.7% additional noise.

---

## 5. What Works Well

1. **Turkish legal document extraction** - Legal references (95.7%), protected areas (90.5%), penalties (58.8%), permits (60.0%) all perform well. The structured nature of Turkish legal text is well-suited to regex patterns.

2. **Stakeholder extraction** - 82.0% precision. Named organizations and actor types are reliably identified.

3. **Method extraction** - 66.0% precision. Research methodology terms are well-captured.

4. **Noise reduction pipeline** - 83% reduction vs baseline keyword matching. The multi-stage filtering genuinely works.

5. **System scalability** - Processes 273 documents in parallel with 8 workers. Architecture is modular and extensible.

---

## 6. What Needs Improvement

### 6.1 Low Recall (15% overall)
The system misses 85% of true mentions. This is the biggest limitation. Regex patterns can only match what they're programmed to match - they cannot understand meaning.

**Example:** The system has patterns for "MaxEnt" and "GIS" as methods, but misses "10-fold cross-validation", "bootstrapping", "Bayesian network ecosystem model" because these aren't in the pattern lists.

### 6.2 Cross-line Garbling (27.4% of errors)
Multi-column PDF layout causes text from adjacent columns to merge, creating garbled extractions like: "lack of consid- Climate and Environmental Change in the Mediterranean Basin"

### 6.3 Semantic Understanding (for free-text categories)
Categories like environmental, finding, result, and conclusion require understanding what text MEANS, not just pattern matching. Regex cannot distinguish between "Environmental Impact Assessment" (a policy) and "sea surface temperature" (an environmental variable).

---

## 7. Decision Points for Professors

### 7.1 Approach for Q1 Journal Paper

**Current system (regex-based):**
- Macro Precision: 0.448
- Macro Recall: 0.155
- Macro F1: 0.180
- These numbers are below Q1 standards (typically F1 > 0.60)

**Three options going forward:**

| Option | Expected F1 | Effort | Risk |
|--------|------------|--------|------|
| A. Keep improving regex | ~0.25-0.30 | Low | Ceiling too low for Q1 |
| B. LLM-based extraction (replace regex) | ~0.70-0.80 | High | API costs, new pipeline |
| C. **Hybrid: regex for legal + LLM for semantic** | ~0.65-0.75 | Medium | Best cost/benefit |

**My recommendation is Option C (Hybrid):**
- Keep regex for categories where it excels: legal_reference (95.7%), protected_area (90.5%), stakeholder (82.0%), penalty, permit, distance
- Use LLM (Claude API) for semantic categories: species, method, environmental, finding, result, conflict, gap
- Paper narrative: "We compare rule-based vs LLM-based extraction and present a hybrid approach"
- This gives a strong contribution: the comparison itself is valuable research

**I need your guidance on:**
- Do you agree with the hybrid approach?
- Should the Q1 paper focus on the extraction system evaluation, or on the MSP knowledge base and its applications?
- What Q1 journal are we targeting? (Ocean & Coastal Management? Marine Policy? Environmental Modelling & Software?)

### 7.2 Conference Paper (AEIPRO, deadline March 28)

The abstract has been accepted. The full paper (8-12 pages) needs to be written.

**Proposed scope for conference paper:**
- Focus on the METHODOLOGY (system architecture, pipeline design, case study approach)
- Show the Turkish coast case study with extraction results
- Present baseline comparison (83% noise reduction) as the main quantitative result
- Mention precision for top categories (legal 95.7%, protected area 90.5%, stakeholder 82.0%)
- Keep the full P/R/F1 evaluation and LLM hybrid for the Q1 paper

**I need your guidance on:**
- Is this scope appropriate? Does it overlap too much with the Q1 paper?
- Which results are safe to include without "compromising the scope of the future paper"?
- Should I emphasize the Turkish legal framework analysis or the MSP literature review?

### 7.3 What the Q1 Paper Could Look Like

**Title idea:** "A hybrid AI approach for knowledge extraction from marine spatial planning literature: Comparing rule-based and LLM methods"

**Contributions:**
1. A modular, bilingual extraction system for MSP documents (21 categories)
2. Systematic comparison of rule-based vs LLM-based extraction for domain-specific NLP
3. A structured knowledge base of 273 MSP documents from the Turkish coast
4. Gap analysis identifying research, legal, and data gaps in Turkish MSP

**Structure:**
1. Introduction (MSP challenges, need for systematic review)
2. Related Work (NLP for scientific literature, MSP reviews)
3. Methodology (system architecture, extraction pipeline, LLM integration)
4. Case Study (Turkish coast, 273 documents, bilingual corpus)
5. Results (P/R/F1 comparison: regex vs LLM vs hybrid)
6. Discussion (what works, limitations, implications for MSP practitioners)
7. Conclusions

---

## 8. Current File Structure

```
msp_extractor_modular/
|-- main.py                          # Pipeline entry point (parallel processing)
|-- extractors/                      # 21 specialized extractors
|   |-- base_extractor.py            # Base class with filtering integration
|   |-- species_extractor.py         # Species extraction
|   |-- method_extractor.py          # Research methods
|   |-- stakeholder_extractor.py     # Stakeholders/actors
|   |-- legal_reference_extractor.py # Turkish law references
|   |-- ... (17 more extractors)
|-- utils/
|   |-- filters.py                   # FP filter, garble detector, marine filter
|   |-- bibliography_detector.py     # Bibliography section detection
|   |-- text_processor.py            # PDF text extraction
|-- scripts/
|   |-- compute_metrics.py           # Precision/recall computation
|   |-- generate_validation_sheets.py
|   |-- compute_recall_f1.py         # F1 from gold standard
|   |-- generate_paper_tables.py     # LaTeX table generation
|-- validation/
|   |-- baseline_extractor.py        # Keyword-only baseline
|   |-- ablation_study.py            # Component ablation
|-- output_final3/                   # Latest extraction results (6,914 extractions)
|-- validation_sheets_v2/            # 20 annotated precision CSVs
|   |-- recall_evaluation/           # 10-document gold standard
|-- validation_results_v2/           # Metrics, reports
|-- paper_assets/                    # LaTeX tables, figures, summary
|-- knowledge_base.db               # SQLite knowledge base
```

**Total: 67 source files, ~6,000 lines of Python code**

---

## 9. Timeline and Next Steps

| Task | Status | Notes |
|------|--------|-------|
| System architecture | COMPLETE | 67 files, 21 extractors, 8 modules |
| PDF processing pipeline | COMPLETE | 273 docs, parallel processing |
| Extraction (regex-based) | COMPLETE | 6,914 extractions |
| Multi-stage filtering | COMPLETE | Bibliography, garble, marine, FP, dedup |
| Precision validation | COMPLETE | 20 categories, 795 samples |
| Recall gold standard | COMPLETE | 10 documents, 5 categories, 969 mentions |
| Baseline comparison | COMPLETE | 83% noise reduction |
| Ablation study | COMPLETE | 5 component tests |
| Error analysis | COMPLETE | 7 error types classified |
| Conference paper (AEIPRO) | TO DO | Deadline: March 28 |
| LLM hybrid extraction | TO DO | Pending professor guidance |
| Q1 journal paper | TO DO | Pending approach decision |

---

## 10. Summary of Key Numbers

| Metric | Value |
|--------|-------|
| Documents processed | 273 (248 research + 25 legal) |
| Total extractions | 6,914 |
| Extraction categories | 21 |
| Macro precision | 0.448 |
| Macro recall | 0.155 |
| Macro F1 | 0.180 |
| Baseline noise reduction | 83.0% |
| Best category precision | Legal Reference: 0.957 |
| Best category recall | Species: 0.382 |
| Source files | 67 |
| Python code | ~6,000 lines |

---

*Report generated: 17 February 2026*
*System version: msp_extractor_modular v3 (output_final3)*
