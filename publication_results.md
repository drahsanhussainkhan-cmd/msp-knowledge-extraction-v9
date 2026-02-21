# MSP Knowledge Extraction System - Publication Results (v9)

## System Overview
- **Documents processed:** 273 (248 Q1 research papers + 25 Turkish legal documents)
- **Total extractions:** 3,142
- **Extraction categories:** 17 validated (+ 4 with <5 samples)
- **Validation samples:** 610 manually annotated extractions
- **Source files:** 87 Python files, 22 specialized extractors

## Pipeline Version Progression

| Version | Description | Total Extractions | Macro Precision | Micro Precision |
|---------|------------|-------------------|-----------------|-----------------|
| v3 | Baseline (initial extractors) | 6,914 | 0.448 | --- |
| v4 | + NLP filters | 6,380 | 0.514 | --- |
| v5 | + Regex fixes + Bibliography detection | 4,178 | 0.567 | 0.545 |
| v6 | + Targeted category-level fixes | 3,248 | 0.711 | 0.767 |
| v7 | + Context-aware filtering | 3,155 | 0.777 | 0.809 |
| **v9** | **+ Conflict overhaul, species/data refinement** | **3,142** | **0.792** | **0.826** |

**Overall improvement:** Macro precision +76.8%, extractions reduced by 54.6% (removing false positives).

## Extraction Counts by Category (v9)

| Category | Count | Description |
|----------|-------|-------------|
| Legal Reference | 1,039 | Named laws, regulations, articles, directives |
| Method | 408 | Research and analysis methods (13 types) |
| Stakeholder | 296 | Marine/coastal stakeholder groups |
| Environmental | 245 | Environmental conditions and impacts |
| Species | 244 | Marine species (scientific + common names) |
| Data Source | 227 | Named data products (AIS, Landsat, GEBCO, etc.) |
| Policy | 185 | Named policies, directives, strategies |
| Gap | 165 | Research gaps and knowledge limitations |
| Institution | 153 | Government institutions and agencies |
| Distance | 61 | Spatial distance measurements |
| Protected Area | 37 | Marine protected areas and zones |
| Temporal | 22 | Temporal restrictions and periods |
| Penalty | 19 | Legal penalties and fines |
| Permit | 10 | Permit requirements |
| Conflict | 9 | Use conflicts between marine activities |
| Objective | 7 | Research/policy objectives |
| Prohibition | 6 | Activity prohibitions |
| **Total** | **3,142** | |

## Precision by Category (v9, Sorted by Precision)

| Category | Total | Validated | Correct | Precision | 95% CI |
|----------|-------|-----------|---------|-----------|--------|
| Conflict | 9 | 9 | 9 | **1.000** | [0.701, 1.000] |
| Legal Reference | 1,039 | 50 | 50 | **1.000** | [0.929, 1.000] |
| Prohibition | 6 | 6 | 6 | **1.000** | [0.610, 1.000] |
| Environmental | 245 | 50 | 49 | **0.980** | [0.895, 0.996] |
| Species | 244 | 50 | 49 | **0.980** | [0.895, 0.996] |
| Stakeholder | 296 | 50 | 48 | **0.960** | [0.865, 0.989] |
| Data Source | 227 | 50 | 46 | **0.920** | [0.812, 0.968] |
| Method | 408 | 50 | 45 | **0.900** | [0.786, 0.957] |
| Gap | 165 | 50 | 42 | **0.840** | [0.715, 0.917] |
| Protected Area | 37 | 37 | 29 | **0.784** | [0.628, 0.886] |
| Distance | 61 | 50 | 37 | **0.740** | [0.604, 0.841] |
| Institution | 153 | 50 | 35 | **0.700** | [0.562, 0.809] |
| Penalty | 19 | 19 | 11 | 0.579 | [0.363, 0.769] |
| Objective | 7 | 7 | 4 | 0.571 | [0.250, 0.842] |
| Policy | 185 | 50 | 28 | 0.560 | [0.423, 0.688] |
| Temporal | 22 | 22 | 12 | 0.545 | [0.347, 0.731] |
| Permit | 10 | 10 | 4 | 0.400 | [0.168, 0.687] |
| **Macro Avg.** | **3,142** | **610** | **504** | **0.792** | --- |
| **Micro Avg.** | | **610** | **504** | **0.826** | [0.794, 0.854] |

## Key Results Summary

- **12 out of 17 categories** achieve precision >= 0.70
- **8 categories** achieve precision >= 0.90 (conflict, legal_reference, prohibition, environmental, species, stakeholder, data_source, method)
- **Micro precision of 0.826** with 95% CI [0.794, 0.854]
- **Top-5 categories by volume** (legal_reference, method, stakeholder, environmental, species) average 0.964 precision
- **Macro precision of 0.792** across all 17 categories

## Improvements Applied (v3 -> v9)

### Phase 1: NLP Filters (v3 -> v4)
- Added false positive detection for garbled PDF text
- Marine relevance scoring to reject non-marine content
- Bibliography section detection (header-based)

### Phase 2: Regex Pattern Fixes (v4 -> v5)
- Tightened data_source to require named sources (Landsat, AIS, GEBCO, etc.)
- Required quantitative evidence for result/finding extractions
- Added method blacklists for environmental/cumulative impact assessment terms
- Removed generic stakeholder patterns
- Added activity boundary limits for conflict extraction
- Extended policy title blacklist for ML/path-planning terms

### Phase 3: Targeted Fixes (v5 -> v6)
- **Bibliography detection:** 5 methods (headers, CRediT, citation density, DOI density, author-year density)
- **Data source:** Word boundaries on short acronyms (AIS, VMS, ICES) to prevent substring matching
- **Conflict:** Garbled activity rejection (verb fragments, short fragments, non-marine terms)
- **Finding:** Required quantitative evidence (numbers/percentages in description)
- **Temporal:** Non-marine legal context blacklist (zoning, heritage, construction laws)
- **Policy:** Multi-word title requirement, article/preposition filtering
- **Institution:** Two-word name requirement, garbled text rejection

### Phase 4: Context-Aware Filtering (v6 -> v7)
- **Distance:** Building/construction context rejection (Turkish zoning law measurements)
- **Policy:** Title length limit (max 8 words), verb detection to reject sentence fragments
- **Finding:** Non-MSP topic blacklist (algorithms, AUV/USV), stronger quantitative evidence gate
- **Conclusion:** Cross-column garble detection, bibliography offset fix

### Phase 5: Domain-Specific Overhauls (v7 -> v9)
- **Conflict:** Complete overhaul with marine keyword whitelist, conflict taxonomy (spatial/temporal/resource/governance), activity normalization, cross-linking to stakeholders
- **Species:** Enhanced common name validation, stricter bibliography filtering
- **Data Source:** Improved named source recognition, reduced generic matches
- **Stakeholder:** Tighter pattern matching, improved organization name detection

## Biggest Category Improvements (v5 -> v9)

| Category | v5 Precision | v9 Precision | Improvement |
|----------|-------------|-------------|-------------|
| Conflict | 0.278 | 1.000 | +0.722 |
| Data Source | 0.245 | 0.920 | +0.675 |
| Species | 0.490 | 0.980 | +0.490 |
| Environmental | 0.500 | 0.980 | +0.480 |
| Institution | 0.396 | 0.700 | +0.304 |
| Distance | 0.480 | 0.740 | +0.260 |
| Gap | 0.653 | 0.840 | +0.187 |
| Temporal | 0.385 | 0.545 | +0.160 |

## Error Type Distribution (v9)

| Error Type | Count | Percentage |
|------------|-------|------------|
| False positive | 33 | 31.1% |
| Extraction error | 26 | 24.5% |
| Wrong category | 25 | 23.6% |
| Reference only | 6 | 5.7% |
| Wrong value | 4 | 3.8% |
| Garbled text | 4 | 3.8% |
| Generic term | 3 | 2.8% |
| Non-marine | 2 | 1.9% |

## Noise Reduction vs Baseline

| Configuration | Extractions | Noise Reduction |
|---------------|-------------|-----------------|
| Keyword baseline (no filtering) | 40,563 | --- |
| Full system (v9) | 3,142 | 92.3% |

## Validation Methodology
- **Sampling:** Stratified random sampling (seed=42), up to 50 per category
- **Annotation:** Manual binary annotation (correct/incorrect) by domain expert
- **Confidence intervals:** Wilson score intervals (more accurate for small samples)
- **Total samples:** 610 annotations across 17 categories
