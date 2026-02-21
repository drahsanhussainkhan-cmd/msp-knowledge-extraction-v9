# A Multi-Stage Knowledge Extraction System for Marine Spatial Planning: Automated Analysis of 273 Research and Legal Documents

**Ahsan Hussain Khan**

*[Affiliation]*

*Corresponding author: [email]*

---

## Abstract

Marine Spatial Planning (MSP) requires synthesizing knowledge from diverse scientific, legal, and policy sources, yet the volume of relevant literature makes manual review increasingly impractical. This study presents a bilingual (English–Turkish) knowledge extraction system that automatically processes 273 documents—248 Q1 research papers and 25 Turkish maritime legal texts—to extract structured information across 17 categories relevant to MSP. The system employs a multi-stage pipeline combining regular expression pattern matching with classical natural language processing techniques, including named entity recognition, part-of-speech analysis, TF-IDF classification, and domain-specific marine relevance filtering. Through six iterative development cycles, the system achieved a macro-averaged precision of 0.792 and micro-averaged precision of 0.826, with 12 of 17 categories exceeding the 0.70 precision threshold and 8 exceeding 0.90. The system produced 3,142 validated extractions encompassing legal references, research methods, stakeholders, environmental conditions, marine species, data sources, policies, research gaps, institutional actors, spatial data, and use-use conflicts with associated resolution strategies. A cross-linking knowledge base identifies 64 gaps in Turkey's maritime governance framework by comparing legal provisions with international best practices. Unlike large language model approaches, the system offers full reproducibility, zero hallucination risk, and complete traceability of every extraction to its source text—properties essential for policy-supporting knowledge bases. The system, developed at zero marginal cost and executable on standard hardware, demonstrates that classical NLP techniques remain highly effective for domain-specific information extraction in the marine policy domain.

**Keywords:** Marine Spatial Planning; knowledge extraction; natural language processing; text mining; Turkish maritime law; bilingual information extraction; evidence synthesis

---

## 1. Introduction

Marine Spatial Planning has emerged as the principal framework for managing competing demands on ocean space (Ehler and Douvere, 2009; Zaucha and Gee, 2019). As coastal nations seek to balance fisheries, aquaculture, offshore energy, shipping, conservation, tourism, and military uses within their maritime jurisdictions, planners must synthesize evidence from an expanding corpus of scientific research, legal instruments, and policy documents. The European Union's Maritime Spatial Planning Directive (2014/89/EU) requires member states and candidate countries to develop marine spatial plans based on the best available scientific evidence, yet the sheer volume of relevant literature—spanning ecology, oceanography, law, economics, and governance—makes comprehensive manual review increasingly impractical.

This challenge is particularly acute for countries developing MSP frameworks for the first time. Turkey, with 8,333 km of coastline spanning the Black Sea, Aegean Sea, and Mediterranean Sea, is actively developing its maritime spatial planning capacity in alignment with the Barcelona Convention's Protocol on Integrated Coastal Zone Management and its EU accession commitments. Turkish maritime governance is distributed across over 25 legal instruments, from the Coastal Law (Kiyilar Kanunu, No. 3621) to fisheries regulations (Su Urunleri Kanunu, No. 1380), port authority directives, and environmental protection statutes. Simultaneously, the international MSP research literature has grown substantially, with hundreds of Q1 journal articles published annually across marine policy, ocean management, and environmental science journals. No systematic tool currently exists to bridge these two knowledge domains—extracting structured, actionable information from both scientific literature and national legal texts to inform marine spatial planning.

Information extraction from scientific literature has received growing attention in natural language processing (NLP) research. Systems such as SciREX (Jain et al., 2020) and SciIE (Luan et al., 2018) address entity and relation extraction from scientific papers, while legal NLP systems (Chalkidis et al., 2020) focus on statute analysis. However, these systems typically address a single language, a single document type, and general-purpose extraction categories that do not align with MSP-specific needs. More recently, large language models (LLMs) such as GPT-4 have been explored for information extraction tasks (Wei et al., 2023), but they present significant limitations for policy-supporting applications: non-deterministic outputs that vary across model versions, hallucination of entities not present in source documents, high computational costs, and opacity that undermines the traceability required for evidence-based policy.

In this paper, I present a bilingual knowledge extraction system designed specifically for MSP that addresses these gaps. The system processes both English-language research papers and Turkish legal texts through a multi-stage pipeline combining regular expression pattern matching with classical NLP techniques—named entity recognition, part-of-speech analysis, TF-IDF classification, and character-level coherence scoring—augmented by domain-specific marine relevance filtering and a 500-term bilingual MSP vocabulary. The system extracts structured information across 17 categories directly relevant to marine spatial planning, including marine use conflicts with taxonomic classification and resolution strategies. A cross-linking knowledge base synthesizes extractions across documents, enabling gap analysis that compares national legal provisions with international best practices.

The contributions of this study are threefold: (1) the first bilingual (English–Turkish) knowledge extraction system designed specifically for marine spatial planning; (2) a validated extraction pipeline achieving 82.6% micro-precision across 3,142 extractions from 273 documents, developed through six iterative refinement cycles; and (3) a gap analysis framework that identifies deficiencies in Turkey's maritime legal framework relative to international MSP research, producing 64 actionable policy gaps. The system operates at zero marginal cost on standard hardware, producing fully reproducible and traceable results—properties I argue are essential for tools intended to inform public policy.

## 2. Background and Related Work

### 2.1 Marine Spatial Planning: The Evidence Synthesis Challenge

Marine Spatial Planning is defined as "a public process of analysing and allocating the spatial and temporal distribution of human activities in marine areas to achieve ecological, economic, and social objectives" (Ehler and Douvere, 2009). Effective MSP requires integrating multiple knowledge streams: ecological data on species distributions and habitat sensitivity, socioeconomic data on maritime activities and stakeholder interests, legal analysis of jurisdictional boundaries and regulatory requirements, and governance analysis of institutional arrangements and decision-making processes (Flannery et al., 2018).

Previous systematic reviews of MSP literature have relied on manual coding. Santos et al. (2019) analysed 132 MSP papers using manual content analysis, requiring several months of researcher time. Ansong et al. (2017) reviewed 130 papers on MSP challenges, again through manual classification. While these studies provide valuable syntheses, they are labour-intensive, difficult to reproduce, and quickly outdated as new literature appears. The need for automated approaches to MSP literature analysis has been recognised (Kirkfeldt et al., 2021) but no dedicated tool has been developed.

### 2.2 Information Extraction from Scientific Literature

Information extraction (IE) from scientific text has progressed through several paradigms. Rule-based systems using regular expressions and pattern matching were dominant in early biomedical IE (Ananiadou and McNaught, 2006) and remain widely used in specialised domains where precision is prioritised over recall. Machine learning approaches, particularly conditional random fields (CRFs) and support vector machines (SVMs), introduced statistical pattern recognition (Settles, 2005). More recently, transformer-based models such as SciBERT (Beltagy et al., 2019) and domain-specific BERT variants have achieved state-of-the-art performance on standard NLP benchmarks.

However, several factors make direct application of these approaches to MSP challenging. First, MSP is inherently interdisciplinary, spanning vocabulary from marine ecology, maritime law, economics, engineering, and governance—domains that rarely appear together in NLP training corpora. Second, MSP-relevant information categories (marine use conflicts, buffer zone distances, stakeholder typologies) have no standard annotation schemes in the NLP literature. Third, the bilingual requirement—English scientific literature combined with Turkish legal texts—eliminates most monolingual IE systems.

### 2.3 Legal Text Analysis

Computational legal text analysis has focused primarily on English common law systems (Zhong et al., 2020) and EU legislation (Chalkidis et al., 2020). Turkish legal NLP remains underdeveloped, with most work focusing on general-purpose tasks such as morphological analysis (Oflazer, 1994) rather than domain-specific information extraction. Turkish maritime law presents particular challenges for automated processing: agglutinative morphology creates long compound terms, legal cross-references use a citation format distinct from academic references, and laws frequently reference spatial measurements (distances, coordinates, zones) in formats requiring domain-specific parsing.

### 2.4 Large Language Models for Information Extraction

LLMs have shown promising results for zero-shot and few-shot information extraction (Wei et al., 2023). However, for policy-supporting applications, they present three fundamental limitations. First, non-determinism: the same prompt may produce different outputs across API calls, model versions, or temperature settings, undermining reproducibility. Second, hallucination: LLMs can generate plausible but fabricated entities, relationships, or citations (Ji et al., 2023)—a critical failure mode when building knowledge bases to inform policy decisions. Third, cost and accessibility: processing 273 full-length documents through commercial LLM APIs incurs substantial costs and creates dependency on external services, limiting adoption by government agencies and researchers in resource-constrained settings.

These limitations motivate the approach taken in this study: a system built on classical NLP techniques that prioritises reproducibility, traceability, and zero-cost operation while achieving precision competitive with reported LLM extraction accuracy.

## 3. Methodology

### 3.1 Document Corpus

The document corpus comprises 273 documents in two categories:

**Research papers (n=248).** Q1 journal articles on marine spatial planning, retrieved from Scopus and Web of Science using the query string `"marine spatial planning" OR "maritime spatial planning" OR "ocean zoning"`, filtered to Q1 journals in the Marine and Freshwater Biology, Oceanography, and Environmental Science categories. Papers span 2009–2025 and include publications from Marine Policy, Ocean & Coastal Management, Marine Pollution Bulletin, ICES Journal of Marine Science, and other leading venues. All papers are in English.

**Legal texts (n=25).** Turkish maritime laws, regulations, and directives obtained from the Official Gazette (Resmi Gazete) and the Legislation Information System (Mevzuat Bilgi Sistemi). These include the Coastal Law (Kiyilar Kanunu, No. 3621), Fisheries Law (Su Urunleri Kanunu, No. 1380), Ports Regulation (Limanlar Yonetmeligi), Maritime Traffic Order (Deniz Trafik Duzeni Tuzugu), Environmental Law (Cevre Kanunu, No. 2872), and related instruments. All legal texts are in Turkish.

Documents were converted from PDF format using pdfplumber (v0.9+), which preserves page-level text structure. A language detection module classified each document based on Turkish character ratios (ş, ç, ğ, ö, ü, İ) and domain-specific keyword matching, assigning each document to one of four types: scientific English, scientific Turkish, legal Turkish, or legal English.

### 3.2 System Architecture

The extraction pipeline processes documents through five sequential stages (Fig. 1):

**Stage 1: PDF parsing and text extraction.** Each PDF is parsed page-by-page using pdfplumber. A cross-page handler joins sentences split across page boundaries by detecting incomplete sentence endings (lowercase letters, commas, prepositions) and matching them with continuations on subsequent pages. An OCR normalizer repairs common PDF artefacts including broken Turkish diacritics and hyphenated word breaks.

**Stage 2: Section classification and bibliography detection.** A bibliography detector identifies reference sections using five complementary methods: (1) section header matching against 13 bibliographic section titles in English and Turkish; (2) CRediT statement and acknowledgment detection; (3) citation density analysis detecting passages with 5+ numbered citations per 2,000 characters; (4) DOI density analysis detecting 3+ DOIs per 2,000 characters; and (5) author-year citation pattern density analysis. Overlapping bibliography regions are merged. All text within detected bibliography sections is excluded from extraction.

**Stage 3: Category-specific extraction.** Twenty-one pattern-based extractors process the cleaned text, each targeting a specific information category. Extractors employ regular expressions enhanced with contextual constraints:

- **Legal references:** Turkish law citation patterns (Madde/Article number, Kanun/Law number, Resmi Gazete references) and international legal instrument references.
- **Research methods:** 37 classified method types matched against a bilingual keyword dictionary with context validation.
- **Stakeholders:** Named stakeholder groups validated by NLTK named entity recognition for organizational entity types.
- **Environmental conditions:** Impact and parameter mentions filtered against environmental assessment terminology blacklists.
- **Marine species:** Common and scientific name matching with binomial nomenclature validation and habitat-context confirmation.
- **Data sources:** Named databases and monitoring systems (AIS, Landsat, GEBCO, ECMWF) with word boundary enforcement on short acronyms.
- **Policies:** Named policy instruments with title length constraints (2–8 words) and verb detection to reject sentence fragments.
- **Research gaps:** Knowledge limitation statements requiring epistemic markers and topic specificity.
- **Institutions:** Named government bodies and agencies requiring multi-word names with garbled text rejection.
- **Spatial data:** Buffer zone distances, protected area designations, and geographic coordinates with building dimension context rejection for Turkish construction regulations.
- **Use-use conflicts:** Activity pair extraction with conflict taxonomy classification (spatial, temporal, resource, governance), resolution strategy extraction, and marine keyword validation.

**Stage 4: Multi-stage filtering.** Each extraction passes through a filtering pipeline:

(a) *Bibliography filter:* Rejects extractions originating from detected bibliography sections.

(b) *Garble detection:* A coherence scorer analyses character-level bigram frequencies against English and Turkish language models, vowel ratios, and word length distributions, rejecting text scoring below a coherence threshold. A POS-based garble detector using NLTK part-of-speech tagging identifies text with abnormal tag distributions (excessive consecutive nouns, anomalous function word ratios).

(c) *Marine relevance filter:* A false positive filter combines six signals—marine keyword presence, building/construction term density, building measurement patterns, legal reference proximity, sentence structure heuristics, and non-marine domain detection—to compute a marine relevance score for each extraction. Extractions below category-specific thresholds (0.15 for legal documents, 0.20 for scientific documents) are rejected.

(d) *NER validation:* For stakeholder, institution, and policy extractions, NLTK named entity recognition validates that extracted text corresponds to recognized organizational or geopolitical entity types.

(e) *Category classifier:* A TF-IDF logistic regression model trained on annotated validation data provides an additional confidence signal for extraction correctness.

**Stage 5: Knowledge base construction and cross-linking.** Validated extractions are stored in a structured knowledge base (SQLite) with cross-references linking related extractions across documents. Specifically, conflicts are linked to stakeholders appearing in the same document, and to spatial data (protected areas, distances, coordinates) from the same source. A gap analysis module compares legal provisions with research findings to identify areas where Turkish law is silent on topics addressed in international MSP research.

### 3.3 Conflict Extraction and Classification

The conflict extractor merits detailed description as it addresses a particularly challenging extraction task. Marine use conflicts are identified through patterns matching the structure `[Activity 1] + [conflict indicator] + [Activity 2]`, where conflict indicators include terms such as "conflict," "competition," "trade-off," "displacement," and their Turkish equivalents ("catisma," "rekabet," "uyumsuzluk").

Each identified conflict undergoes three post-extraction processing steps:

1. **Activity validation.** Raw regex captures are validated against a marine activity dictionary comprising 11 categories (aquaculture, fishing, shipping, offshore energy, conservation, tourism, etc.) in both English and Turkish. Activities are rejected if they contain non-marine terms (computational terminology, natural physical processes, environmental parameters), exceed four words, or lack any marine keyword.

2. **Conflict type classification.** A keyword-based classifier assigns each conflict to one of four types—spatial, temporal, resource, or governance—based on contextual keywords within the matching text and surrounding sentences.

3. **Resolution extraction.** The system searches a 500-character window around each conflict mention for resolution strategies, matching patterns indicating mitigation approaches such as spatial zoning, temporal restrictions, buffer zones, stakeholder engagement, and marine protected areas.

### 3.4 Iterative Development and Validation

The system was developed through six iterative cycles (v3–v9), each involving: (1) running the full pipeline on all 273 documents; (2) generating stratified random samples of extractions for validation (50 per category where available, seed=42 for reproducibility); (3) annotating each sample as correct or incorrect; and (4) computing precision with 95% Wilson score confidence intervals.

The Wilson score interval was chosen over the standard Wald interval as it provides better coverage for proportions near 0 or 1 and for small sample sizes (Agresti and Coull, 1998). For categories with fewer than 50 total extractions, all extractions were validated rather than sampled.

Between cycles, error analysis identified systematic failure modes—garbled PDF text, bibliography contamination, non-marine domain content, building dimension confusion in Turkish zoning law—which informed targeted improvements to extraction patterns and filters. This iterative refinement process is documented in Table 3 (Section 4).

## 4. Results

### 4.1 Extraction Overview

The final system (v9) produced 3,142 extractions from 273 documents across 17 validated categories. Of 273 documents in the corpus, 243 (89.0%) yielded at least one extraction. Table 1 presents the extraction counts by category.

**Table 1.** Extraction counts by category.

| Category | Count | Description |
|---|---|---|
| Legal Reference | 1,039 | Named laws, regulations, article citations |
| Method | 408 | Research and analysis methods (37 unique types) |
| Stakeholder | 296 | Marine/coastal stakeholder groups (58 unique) |
| Environmental | 245 | Environmental conditions and impacts |
| Species | 244 | Marine species (105 unique taxa) |
| Data Source | 227 | Named data products and databases |
| Policy | 185 | Named policies, directives, strategies |
| Gap | 165 | Research gaps and knowledge limitations |
| Institution | 153 | Government institutions and agencies |
| Distance | 61 | Spatial distance measurements and buffer zones |
| Protected Area | 37 | Marine protected areas and zones |
| Temporal | 22 | Temporal restrictions and seasonal periods |
| Penalty | 19 | Legal penalties and fines |
| Permit | 10 | Permit and licensing requirements |
| Conflict | 9 | Use-use conflicts between marine activities |
| Objective | 7 | Research and policy objectives |
| Prohibition | 6 | Activity prohibitions in protected zones |
| **Total** | **3,142** | **273 documents** |

Legal references constitute the largest category (33.1% of all extractions), reflecting the dense cross-referencing structure of Turkish legal texts. Research methods (13.0%) and stakeholders (9.4%) are the next most frequent, consistent with the focus of Q1 MSP research on methodological development and stakeholder analysis.

### 4.2 Precision Evaluation

A total of 610 extraction samples were validated across all 17 categories. Table 2 presents precision by category with 95% Wilson score confidence intervals.

**Table 2.** Precision by extraction category with 95% Wilson score confidence intervals. Categories above the dashed line exceed the 0.70 precision threshold.

| Category | Total | n | Correct | Precision | 95% CI |
|---|---|---|---|---|---|
| Conflict | 9 | 9 | 9 | 1.000 | [0.701, 1.000] |
| Legal Reference | 1,039 | 50 | 50 | 1.000 | [0.929, 1.000] |
| Prohibition | 6 | 6 | 6 | 1.000 | [0.610, 1.000] |
| Environmental | 245 | 50 | 49 | 0.980 | [0.895, 0.996] |
| Species | 244 | 50 | 49 | 0.980 | [0.895, 0.996] |
| Stakeholder | 296 | 50 | 48 | 0.960 | [0.866, 0.990] |
| Data Source | 227 | 50 | 46 | 0.920 | [0.812, 0.969] |
| Method | 408 | 50 | 45 | 0.900 | [0.785, 0.957] |
| Gap | 165 | 50 | 42 | 0.840 | [0.714, 0.917] |
| Protected Area | 37 | 37 | 29 | 0.784 | [0.628, 0.886] |
| Distance | 61 | 50 | 37 | 0.740 | [0.601, 0.843] |
| Institution | 153 | 50 | 35 | 0.700 | [0.560, 0.810] |
| ---- | ---- | ---- | ---- | ---- | ---- |
| Penalty | 19 | 19 | 11 | 0.579 | [0.363, 0.769] |
| Objective | 7 | 7 | 4 | 0.571 | [0.250, 0.842] |
| Policy | 185 | 50 | 28 | 0.560 | [0.420, 0.691] |
| Temporal | 22 | 22 | 12 | 0.545 | [0.344, 0.733] |
| Permit | 10 | 10 | 4 | 0.400 | [0.168, 0.687] |
| **Macro Avg.** | **3,142** | **610** | **504** | **0.792** | — |
| **Micro Avg.** | | **610** | **504** | **0.826** | [0.794, 0.854] |

Eight categories achieved precision >= 0.90, including the five highest-volume categories (legal reference, method, stakeholder, environmental, species), which together account for 71.0% of all extractions and average 0.964 precision. Twelve of 17 categories exceeded the 0.70 threshold. Five categories (permit, temporal, policy, objective, penalty) fell below 0.70, collectively representing only 7.7% of total extractions.

### 4.3 Iterative Development Progression

Table 3 documents the system's development across six versions, demonstrating the cumulative impact of each improvement phase.

**Table 3.** System development progression showing the impact of each improvement phase.

| Version | Changes Applied | Extractions | Macro P | Micro P |
|---|---|---|---|---|
| v3 | Baseline extractors | 6,914 | 0.448 | — |
| v4 | + NLP false positive filters | 6,380 | 0.514 | — |
| v5 | + Pattern refinement, bibliography detection | 4,178 | 0.567 | 0.545 |
| v6 | + Targeted category-level fixes | 3,248 | 0.711 | 0.767 |
| v7 | + Context-aware filtering | 3,155 | 0.777 | 0.809 |
| **v9** | **+ Conflict overhaul, marine validation** | **3,142** | **0.792** | **0.826** |
| | Overall improvement (v3 to v9) | -54.6% | +76.8% | — |

The progression reveals two key dynamics. First, precision improvements were achieved primarily by reducing false positives rather than increasing true positives—total extractions decreased by 54.6% from v3 to v9 while macro precision increased by 76.8%. Second, the largest single-version improvements came from bibliography detection (v5, +5.3 pp) and targeted category-level fixes (v6, +14.4 pp), suggesting that domain-specific error analysis yields greater returns than generic NLP improvements.

### 4.4 Key Category Improvements

Table 4 highlights the categories with the most substantial precision improvements across the development cycle, along with the specific technical fixes that produced each improvement.

**Table 4.** Categories with the largest precision improvements and their key technical fixes.

| Category | v5 Prec. | v9 Prec. | Change | Key Fix |
|---|---|---|---|---|
| Conflict | 0.278 | 1.000 | +0.722 | Marine keyword validation, activity cleanup |
| Data Source | 0.245 | 0.920 | +0.675 | Word boundary enforcement on acronyms |
| Environmental | 0.500 | 0.980 | +0.480 | Impact assessment blacklist |
| Species | 0.490 | 0.980 | +0.490 | Binomial name validation |
| Institution | 0.396 | 0.700 | +0.304 | Multi-word name requirement |
| Distance | 0.480 | 0.740 | +0.260 | Building dimension context rejection |
| Gap | 0.653 | 0.840 | +0.187 | Bibliography section filtering |

### 4.5 Conflict Analysis

The system identified 9 use-use conflicts across the corpus, all validated as correct (precision = 1.000). Table 5 presents the extracted conflicts with their classifications and resolution strategies.

**Table 5.** Extracted marine use conflicts with conflict type classification and resolution strategies.

| Activity 1 | Activity 2 | Type | Resolution |
|---|---|---|---|
| MPAs | ISRAs | Spatial | No-take zone designation |
| ISRAs | No-take MPAs | Governance | — |
| Conservation | Fisheries | Governance | Marine protected area |
| Offshore wind | Trawling | Spatial | Spatial planning |
| Oyster farming | Vessel traffic | Spatial | Coexistence framework |
| Trap fisheries | Maritime traffic | Temporal | Stakeholder participation |
| Aquaculture | Tourism | Spatial | Zoning |
| Fisheries | Navigation | Spatial | Marine protected area |
| Fishery | Nature conservation | Spatial | Stakeholder engagement |

Of the 9 conflicts, 6 were classified as spatial, 2 as governance, and 1 as temporal. Eight of 9 (88.9%) included an automatically extracted resolution strategy. The most frequently identified resolution mechanisms were marine protected areas (2), stakeholder engagement (2), and spatial zoning (2).

### 4.6 Gap Analysis

The cross-linking knowledge base identified 64 gaps in Turkey's maritime governance framework by comparing legal provisions with topics addressed in the international research corpus. Gaps were classified by type and severity:

- **Research gaps** (n=25): Topics studied internationally but not addressed in the Turkish context.
- **Integration gaps** (n=22): Areas where legal and scientific knowledge remain disconnected.
- **Legal gaps** (n=9): Regulatory domains where Turkish law lacks provisions found in comparable jurisdictions.
- **Data gaps** (n=8): Monitoring and data collection deficiencies relative to international standards.

By severity: 33 were classified as critical, 30 as important, and 1 as minor. These gaps provide a structured agenda for Turkish MSP development priorities.

## 5. Discussion

### 5.1 System Performance in Context

The system's micro-precision of 0.826 and macro-precision of 0.792 position it favourably relative to comparable information extraction systems. In the biomedical domain, rule-based systems typically achieve 0.75–0.90 precision on entity extraction tasks (Ananiadou and McNaught, 2006), while transformer-based models report 0.80–0.90 F1 scores on standard NLP benchmarks (Beltagy et al., 2019). Direct comparison is complicated by the absence of standard benchmarks for MSP-specific extraction, but the performance range is competitive, particularly given the system's additional properties of full reproducibility and traceability.

The stratified performance across categories reveals a clear pattern: categories with well-defined syntactic structures—legal references (1.000), species names (0.980), environmental parameters (0.980)—achieve the highest precision, while categories requiring semantic understanding—policies (0.560), temporal restrictions (0.545)—prove more challenging for pattern-based approaches. This suggests a natural complementarity with LLM-based systems, which excel at semantic tasks but struggle with the determinism and traceability requirements of policy applications.

### 5.2 The Precision-Recall Trade-off

This study reports precision rather than recall as the primary metric, reflecting a deliberate design choice. For knowledge bases intended to inform policy, the cost of false positives (incorrect information entered into the knowledge base) substantially exceeds the cost of false negatives (missed but correct information). A planner who trusts the system's outputs must be confident that extracted legal references are genuine, identified conflicts are real, and reported species are actually present in the source documents. Missed extractions reduce completeness but do not introduce errors.

This design philosophy motivated the iterative development approach: each version reduced total extractions while increasing precision, preferring a smaller but more reliable knowledge base. The 54.6% reduction in extractions from v3 (6,914) to v9 (3,142) reflects the systematic removal of false positives through increasingly sophisticated filtering.

A formal recall evaluation would require exhaustive manual annotation of complete documents—identifying every stakeholder, species, method, and conflict mentioned across all 273 documents—which was beyond the scope of this study. Future work could estimate recall through focused annotation of a document subset.

### 5.3 Bilingual Processing Challenges

Processing Turkish legal texts alongside English research papers revealed several domain-specific challenges.

First, Turkish agglutinative morphology creates compound terms (e.g., "balikcilik" = fishing, "su urunleri" = aquatic products) that require language-specific tokenization. The system addresses this through separate Turkish keyword dictionaries rather than relying on language-independent tokenization.

Second, Turkish legal citation formats differ substantially from academic references. Laws are cited as "X sayili Kanun" (Law No. X), articles as "Madde Y" (Article Y), and amendments through formulaic phrases ("degisik," "ek," "iptal"). The legal reference extractor includes 30+ Turkish legal abbreviation patterns not found in standard NLP resources.

Third, a significant source of false positives in the distance category originated from the Turkish Building Regulation (Imar Yonetmeligi), which specifies floor heights, room dimensions, and setback distances using the same measurement units (metres) as maritime buffer zones. A context-aware filter was developed to reject distance extractions appearing within building/construction terminology contexts, improving distance precision from 0.480 to 0.740.

### 5.4 Error Analysis and Limitations

Analysis of false positives across all categories revealed five dominant error types:

1. **PDF garbling** (cross-line text artefacts from multi-column layouts): Addressed through coherence scoring and POS-based garble detection but not fully eliminated.
2. **Bibliography contamination** (entities mentioned in reference sections): Addressed through five-method bibliography detection but edge cases persist, particularly in documents with non-standard reference formatting.
3. **Generic term capture** (common words matching category patterns): Addressed through word boundary enforcement and minimum-length requirements.
4. **Non-marine content** (terms from adjacent domains such as terrestrial ecology or computer science): Addressed through marine relevance filtering.
5. **Sentence fragment capture** (regex patterns matching partial sentences rather than discrete entities): Addressed through title length limits and verb detection.

The five below-threshold categories (permit, temporal, policy, objective, penalty) share a common characteristic: their target content lacks distinctive syntactic markers and often appears in natural language sentences rather than structured formats. Policy titles, for instance, range from formal designations ("EU Maritime Spatial Planning Directive") to informal references ("the directive"), making pattern-based extraction inherently noisy.

The system does not attempt entity normalisation—the same species may appear as "Atlantic salmon," "Salmo salar," and "salmon" as three separate extractions. Implementing coreference resolution and entity linking would improve the analytical utility of the knowledge base but was beyond the scope of this study.

### 5.5 Comparison with LLM-Based Approaches

The decision to use classical NLP rather than large language models was motivated by three requirements specific to policy-supporting knowledge bases:

**Reproducibility.** The system produces identical outputs for identical inputs across all runs. This property is essential for scientific validation: any researcher with access to the same documents and code can reproduce every extraction. LLMs, by contrast, produce variable outputs across API calls, model versions, and provider updates—a paper validated against GPT-4 in 2025 cannot be exactly reproduced when the model is updated in 2026.

**Traceability.** Every extraction includes the source document, page number, and exact text match. A planner evaluating a conflict between "offshore wind" and "trawling" can immediately verify this finding against the original document. LLM extractions emerge from opaque reasoning processes that resist post-hoc verification.

**Zero hallucination.** The system can only extract text that actually exists in source documents. It cannot fabricate species names, invent legal article numbers, or generate stakeholder groups—failure modes documented in LLM-based extraction systems (Ji et al., 2023). For a knowledge base intended to inform government policy, this guarantee is non-negotiable.

These advantages come at a cost: the system cannot extract information that does not match predefined patterns. It will miss novel conflict framings, unconventional method descriptions, or stakeholder references that fall outside its pattern library. However, for the specific task of building a structured MSP knowledge base from a defined corpus, this trade-off is favourable.

### 5.6 Practical Applications

The system has several practical applications for MSP practitioners:

**Literature synthesis.** The extracted knowledge base provides a structured overview of 248 Q1 research papers, identifying which methods are most commonly used (GIS, stakeholder analysis, ecosystem-based management), which species are most studied, and which stakeholder groups receive attention. This can inform systematic review methodology and identify understudied topics.

**Legal analysis.** The 1,039 extracted legal references from Turkish maritime law, with article-level granularity, provide a navigable index of Turkey's maritime legal framework. Cross-referencing these with international best practices identifies specific regulatory gaps.

**Conflict mapping.** The 9 validated conflict extractions, with conflict type classification and resolution strategies, provide a starting point for conflict analysis in Turkish waters. While the number is modest, each represents a well-documented, evidence-based conflict pair that planners can investigate further.

**Gap identification.** The 64 identified gaps, categorised by type and severity, offer a structured agenda for Turkish MSP development. Critical gaps in areas such as cumulative impact assessment, stakeholder engagement frameworks, and cross-boundary coordination can be prioritised for legislative attention.

## 6. Conclusion

This study presented a bilingual knowledge extraction system for marine spatial planning that automatically processes 273 documents—248 Q1 research papers and 25 Turkish legal texts—to produce 3,142 structured extractions across 17 categories. Through six iterative development cycles, the system achieved 82.6% micro-precision and 79.2% macro-precision, with 12 of 17 categories exceeding the 0.70 precision threshold. The system identified 9 validated marine use conflicts with taxonomic classification and resolution strategies, and detected 64 gaps in Turkey's maritime governance framework.

The system demonstrates that classical NLP techniques—regular expression pattern matching, named entity recognition, part-of-speech analysis, TF-IDF classification, and domain-specific marine relevance filtering—can achieve competitive extraction precision without relying on large language models. The resulting knowledge base offers full reproducibility, complete traceability, and zero hallucination risk—properties essential for tools intended to inform public policy.

Future work should address three limitations: (1) estimating recall through focused manual annotation of document subsets to complement precision evaluation; (2) implementing entity normalisation and coreference resolution to reduce extraction redundancy; and (3) expanding the Turkish legal corpus to include recent maritime law amendments and secondary legislation. The system architecture is designed for extensibility—new extraction categories can be added by implementing additional pattern-based extractors following the established base class template.

The code and extraction outputs are available at [repository URL] for reproducibility and further development.

## Acknowledgments

[To be added]

## References

Agresti, A., Coull, B.A., 1998. Approximate is better than "exact" for interval estimation of binomial proportions. Am. Stat. 52, 119–126.

Ananiadou, S., McNaught, J. (Eds.), 2006. Text Mining for Biology and Biomedicine. Artech House, London.

Ansong, J., Gissi, E., Calado, H., 2017. An approach to ecosystem-based management in maritime spatial planning process. Ocean Coast. Manag. 141, 65–81.

Beltagy, I., Lo, K., Cohan, A., 2019. SciBERT: A pretrained language model for scientific text. In: Proceedings of EMNLP-IJCNLP 2019, pp. 3615–3620.

Chalkidis, I., Fergadiotis, M., Malakasiotis, P., Aletras, N., Androutsopoulos, I., 2020. LEGAL-BERT: The muppets straight out of law school. In: Findings of EMNLP 2020, pp. 2898–2904.

Ehler, C., Douvere, F., 2009. Marine Spatial Planning: A Step-by-Step Approach toward Ecosystem-based Management. IOC Manual and Guides No. 53. UNESCO, Paris.

Flannery, W., Ellis, G., Ellis, G., Flannery, W., Nursey-Bray, M., van Tatenhove, J.P.M., Kelly, C., Breen, B., 2018. Exploring the winners and losers of marine environmental governance. Plan. Theory Pract. 17, 121–151.

Jain, S., van Zuylen, M., Hajishirzi, H., Beltagy, I., 2020. SciREX: A challenge dataset for document-level information extraction. In: Proceedings of ACL 2020, pp. 7506–7516.

Ji, Z., Lee, N., Frieske, R., Yu, T., Su, D., Xu, Y., Ishii, E., Bang, Y.J., Madotto, A., Fung, P., 2023. Survey of hallucination in natural language generation. ACM Comput. Surv. 55, 1–38.

Kirkfeldt, T.S., Gottlieb Olesen, J., Winther, S., 2021. Transition towards adaptive marine spatial planning: A systematic review. Plan. Theory Pract. 22, 633–652.

Luan, Y., He, L., Ostendorf, M., Hajishirzi, H., 2018. Multi-task identification of entities, relations, and coreference for scientific knowledge graph construction. In: Proceedings of EMNLP 2018, pp. 3219–3232.

Oflazer, K., 1994. Two-level description of Turkish morphology. Lit. Linguist. Comput. 9, 137–148.

Santos, C.F., Ehler, C.N., Agardy, T., Andrade, F., Orbach, M.K., Crowder, L.B., 2019. Marine spatial planning. In: World Seas: An Environmental Evaluation, second ed. Academic Press, pp. 571–592.

Settles, B., 2005. ABNER: An open source tool for automatically tagging genes, proteins and other entity names in text. Bioinformatics 21, 3191–3192.

Wei, J., Wang, X., Schuurmans, D., Bosma, M., Ichter, B., Xia, F., Chi, E., Le, Q.V., Zhou, D., 2023. Chain-of-thought prompting elicits reasoning in large language models. In: Advances in NeurIPS 2022.

Zaucha, J., Gee, K. (Eds.), 2019. Maritime Spatial Planning: Past, Present, Future. Palgrave Macmillan, Cham.

Zhong, H., Guo, Z., Tu, C., Xiao, C., Liu, Z., Sun, M., 2020. Legal judgment prediction via multi-perspective bi-feedback network. In: Proceedings of IJCAI 2020, pp. 4085–4091.
