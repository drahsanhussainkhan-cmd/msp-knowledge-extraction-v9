Subject: MSP Extraction System - Progress Report & Guidance Needed

Dear Manuel and Mateo,

I hope you are doing well. Following your feedback on my first report, I have been working intensively on the NLP-based extraction system as you suggested. I am happy to share that significant progress has been made, and I would like to present the current results and get your guidance on the next steps.

Please find attached a detailed progress report. I will also upload the full codebase, extracted datasets, legal documents, and validation results to our OneDrive repository this week so you can review everything directly.

**Summary of work completed since January:**
- Built a complete NLP extraction system: 67 Python source files, 21 specialized extractors, multi-stage filtering pipeline
- Processed 273 documents (248 English research papers + 25 Turkish legal texts)
- Extracted 6,914 structured knowledge items across 21 categories (species, stakeholders, methods, legal references, environmental conditions, policies, conflicts, gaps, etc.)
- Conducted full validation: precision evaluation (795 samples, 20 categories), recall evaluation (10-document gold standard, 969 human-identified mentions), baseline comparison, ablation study, and error analysis

**Key results:**
- Turkish legal extraction performs very well: legal references 95.7% precision, protected areas 90.5%
- Stakeholder identification: 82.0% precision, research methods: 66.0%
- The system reduces noise by 83% compared to simple keyword matching
- However, overall F1 is 0.180 due to low recall (15%) - the regex-based approach misses many true mentions because it can only match pre-defined patterns

**The main challenge and proposed solution:**
The current rule-based approach works excellently for structured Turkish legal text but has a performance ceiling for semantic categories (environmental conditions, research findings, species). I believe integrating LLM-based extraction for these semantic categories while keeping the rule-based system for legal text would significantly improve results and provide a strong research contribution - comparing rule-based vs. LLM extraction for domain-specific knowledge extraction.

**I would appreciate your guidance on:**
1. Do you agree with this hybrid approach (rule-based for legal + LLM for semantic) for the Q1 paper?
2. For the AEIPRO conference paper (deadline March 28): David mentioned we should include relevant aspects without compromising the Q1 scope. I propose focusing on the methodology and Turkish coast case study. Is this appropriate?
3. Which Q1 journal should we target? (Ocean & Coastal Management? Marine Policy? I have also included Renewable and Sustainable Energy Reviews in the literature corpus as you suggested.)

The full report with all numbers, tables, system architecture details, and validation results is attached (7 pages). I am ready to schedule a meeting at your convenience to discuss the path forward for both the conference paper and Q1 journal.

Best regards,
Ahsan
