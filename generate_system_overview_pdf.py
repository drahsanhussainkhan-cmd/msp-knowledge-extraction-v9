"""Generate a professional PDF overview of the MSP Knowledge Extraction System."""

from fpdf import FPDF


class SystemOverviewPDF(FPDF):
    def __init__(self):
        super().__init__()
        self.set_auto_page_break(auto=True, margin=20)
        # Add Unicode font
        self.add_font("Arial", "", "C:/Windows/Fonts/arial.ttf", uni=True)
        self.add_font("Arial", "B", "C:/Windows/Fonts/arialbd.ttf", uni=True)
        self.add_font("Arial", "I", "C:/Windows/Fonts/ariali.ttf", uni=True)
        self.add_font("Arial", "BI", "C:/Windows/Fonts/arialbi.ttf", uni=True)
        self.add_font("Consolas", "", "C:/Windows/Fonts/consola.ttf", uni=True)

    def header(self):
        if self.page_no() > 1:
            self.set_font("Arial", "I", 8)
            self.set_text_color(120, 120, 120)
            self.cell(0, 8, "MSP Knowledge Extraction System - Technical Overview", align="C")
            self.ln(4)
            self.set_draw_color(200, 200, 200)
            self.line(15, self.get_y(), self.w - 15, self.get_y())
            self.ln(6)

    def footer(self):
        self.set_y(-15)
        self.set_font("Arial", "I", 8)
        self.set_text_color(150, 150, 150)
        self.cell(0, 10, f"Page {self.page_no()}/{{nb}}", align="C")

    def title_page(self):
        self.add_page()
        self.ln(50)
        self.set_font("Arial", "B", 28)
        self.set_text_color(20, 60, 100)
        self.cell(0, 15, "MSP Knowledge Extraction System", align="C")
        self.ln(14)
        self.set_font("Arial", "", 16)
        self.set_text_color(80, 80, 80)
        self.cell(0, 10, "Technical Overview", align="C")
        self.ln(30)

        self.set_draw_color(20, 60, 100)
        self.set_line_width(0.5)
        self.line(60, self.get_y(), self.w - 60, self.get_y())
        self.ln(15)

        self.set_font("Arial", "", 11)
        self.set_text_color(60, 60, 60)
        details = [
            "Automated Bilingual Information Extraction",
            "from Marine Spatial Planning Documents",
            "",
            "273 Documents  |  17 Categories  |  3,155 Extractions",
            "Macro Precision: 0.777  |  Micro Precision: 0.809",
            "",
            "",
            "Ahsan Hussain Khan",
            "PhD Candidate",
        ]
        for line in details:
            self.cell(0, 7, line, align="C")
            self.ln(7)

    def section_title(self, number, title):
        self.ln(4)
        self.set_font("Arial", "B", 15)
        self.set_text_color(20, 60, 100)
        self.cell(0, 10, f"{number}. {title}")
        self.ln(10)
        self.set_draw_color(20, 60, 100)
        self.set_line_width(0.3)
        self.line(15, self.get_y(), self.w - 15, self.get_y())
        self.ln(6)

    def subsection_title(self, title):
        self.ln(2)
        self.set_font("Arial", "B", 11)
        self.set_text_color(40, 80, 120)
        self.cell(0, 8, title)
        self.ln(8)

    def body_text(self, text):
        self.set_font("Arial", "", 10)
        self.set_text_color(40, 40, 40)
        self.multi_cell(0, 5.5, text)
        self.ln(2)

    def bullet(self, text, indent=15):
        x = self.get_x()
        self.set_font("Arial", "", 10)
        self.set_text_color(40, 40, 40)
        self.cell(indent, 5.5, "")
        self.set_font("Arial", "B", 10)
        self.cell(4, 5.5, "\u2022")
        self.set_font("Arial", "", 10)
        self.multi_cell(self.w - 2 * self.l_margin - indent - 4, 5.5, f" {text}")
        self.ln(1)

    def numbered_item(self, number, text, bold_prefix=""):
        self.set_font("Arial", "", 10)
        self.set_text_color(40, 40, 40)
        self.cell(15, 5.5, "")
        self.set_font("Arial", "B", 10)
        self.set_text_color(20, 60, 100)
        self.cell(8, 5.5, f"{number}.")
        self.set_text_color(40, 40, 40)
        if bold_prefix:
            self.set_font("Arial", "B", 10)
            w_bold = self.get_string_width(bold_prefix + " ")
            self.cell(w_bold, 5.5, bold_prefix + " ")
            self.set_font("Arial", "", 10)
            self.multi_cell(self.w - 2 * self.l_margin - 23 - w_bold, 5.5, text)
        else:
            self.set_font("Arial", "", 10)
            self.multi_cell(self.w - 2 * self.l_margin - 23, 5.5, text)
        self.ln(1)

    def table(self, headers, rows, col_widths=None):
        if col_widths is None:
            col_widths = [(self.w - 2 * self.l_margin) / len(headers)] * len(headers)

        # Check if table fits on current page
        needed = 8 + len(rows) * 7 + 4
        if self.get_y() + needed > self.h - 25:
            self.add_page()

        # Header
        self.set_font("Arial", "B", 9)
        self.set_fill_color(20, 60, 100)
        self.set_text_color(255, 255, 255)
        for i, h in enumerate(headers):
            self.cell(col_widths[i], 8, f" {h}", border=1, fill=True)
        self.ln()

        # Rows
        self.set_font("Arial", "", 9)
        self.set_text_color(40, 40, 40)
        for row_idx, row in enumerate(rows):
            if row_idx % 2 == 0:
                self.set_fill_color(245, 248, 252)
            else:
                self.set_fill_color(255, 255, 255)
            for i, cell in enumerate(row):
                self.cell(col_widths[i], 7, f" {cell}", border=1, fill=True)
            self.ln()
        self.ln(4)

    def code_block(self, text):
        self.set_font("Consolas", "", 8.5)
        self.set_fill_color(240, 240, 240)
        self.set_text_color(40, 40, 40)
        self.set_draw_color(200, 200, 200)
        x = self.get_x() + 10
        y = self.get_y()
        lines = text.split("\n")
        line_h = 4.5
        block_h = len(lines) * line_h + 6

        if y + block_h > self.h - 25:
            self.add_page()
            y = self.get_y()

        self.rect(x, y, self.w - 2 * self.l_margin - 20, block_h, style="DF")
        self.set_xy(x + 3, y + 3)
        for line in lines:
            self.cell(0, line_h, line)
            self.ln(line_h)
            self.set_x(x + 3)
        self.ln(4)

    def highlight_box(self, text, color=(230, 243, 255)):
        self.set_fill_color(*color)
        self.set_draw_color(20, 60, 100)
        y = self.get_y()
        self.set_font("Arial", "", 10)
        self.set_text_color(30, 30, 30)
        lines = text.split("\n")
        line_h = 5.5
        block_h = len(lines) * line_h + 8

        if y + block_h > self.h - 25:
            self.add_page()
            y = self.get_y()

        self.rect(15, y, self.w - 30, block_h, style="DF")
        self.set_xy(20, y + 4)
        for line in lines:
            self.cell(0, line_h, line)
            self.ln(line_h)
            self.set_x(20)
        self.ln(6)


def build_pdf():
    pdf = SystemOverviewPDF()
    pdf.alias_nb_pages()

    # ── Title Page ──
    pdf.title_page()

    # ── Section 1: Problem Statement ──
    pdf.add_page()
    pdf.section_title("1", "Problem Statement")
    pdf.body_text(
        "Marine Spatial Planning (MSP) requires synthesizing knowledge from hundreds of research papers "
        "and legal documents across multiple languages. For Turkish maritime waters, this includes 248 Q1 "
        "journal articles and 25 Turkish legal documents covering spatial regulations, species protections, "
        "fishing restrictions, and environmental standards."
    )
    pdf.body_text(
        "Manually extracting structured data from 273 PDF documents is impractical. Key information such as "
        "distance regulations, species mentions, prohibited activities, and stakeholder roles is buried in "
        "unstructured text in both English and Turkish. This system automates that extraction process."
    )

    # ── Section 2: System Overview ──
    pdf.section_title("2", "System Overview")
    pdf.body_text(
        "The MSP Knowledge Extraction System is a bilingual (English/Turkish) NLP pipeline that processes "
        "PDF documents and extracts structured data across 17 validated categories. The system uses "
        "regex-based pattern matching combined with an 8-stage false positive filtering pipeline to "
        "achieve 0.777 macro precision and 0.809 micro precision."
    )

    pdf.highlight_box(
        "Key Statistics:\n"
        "  Documents Processed:  273 (248 Q1 research papers + 25 Turkish legal)\n"
        "  Extraction Categories:  17 validated\n"
        "  Total Extractions:  3,155\n"
        "  Macro Precision:  0.777 | Micro Precision: 0.809 [95% CI: 0.776-0.838]\n"
        "  Validation Samples:  618 manually annotated"
    )

    # ── Section 3: Pipeline Architecture ──
    pdf.section_title("3", "Pipeline Architecture")
    pdf.body_text("The system executes in six sequential phases:")
    pdf.ln(2)

    pdf.numbered_item("1", "Reads PDFs using pdfplumber, extracts full text and per-page text, detects language (Turkish vs English), and routes each document to the appropriate processor.", "Document Ingestion:")
    pdf.numbered_item("2", "21 extractors run bilingual regex patterns against document text. Research papers use 13 extractors; legal documents use 10 extractors. Processing is parallelized across 8 threads.", "Pattern Matching:")
    pdf.numbered_item("3", "Every regex match passes through 8 sequential validation stages (bibliography detection, garble filtering, NLP validation, marine relevance scoring, category-specific rules, false positive filtering, deduplication, and confidence scoring).", "Multi-Stage Filtering:")
    pdf.numbered_item("4", "Extractions are stored in a SQLite database with cross-references linking related items across documents (species, methods, protected areas).", "Knowledge Base Construction:")
    pdf.numbered_item("5", "Four specialized detectors identify research gaps, legal gaps, data gaps, and integration gaps across the corpus.", "Gap Detection:")
    pdf.numbered_item("6", "JSON results, SQLite knowledge base, interactive HTML dashboard, text reports, and gap analysis files.", "Output Generation:")

    # ── Section 4: Extraction Categories ──
    pdf.add_page()
    pdf.section_title("4", "Extraction Categories")
    pdf.body_text(
        "The system extracts 17 categories of MSP-relevant information. Each category has dedicated "
        "bilingual regex patterns optimized through 7 versions of iterative refinement."
    )

    pdf.table(
        ["Category", "Count", "Precision", "95% CI", "Source"],
        [
            ["Legal Reference", "1,039", "1.000", "[0.929-1.000]", "Legal"],
            ["Prohibition", "6", "1.000", "[0.610-1.000]", "Legal"],
            ["Environmental", "245", "0.980", "[0.895-0.996]", "Both"],
            ["Stakeholder", "296", "0.939", "[0.835-0.979]", "Research"],
            ["Species", "244", "0.938", "[0.832-0.979]", "Both"],
            ["Gap", "165", "0.880", "[0.762-0.944]", "Research"],
            ["Method", "408", "0.860", "[0.738-0.930]", "Research"],
            ["Conflict", "22", "0.818", "[0.615-0.927]", "Research"],
            ["Protected Area", "37", "0.784", "[0.628-0.886]", "Legal"],
            ["Data Source", "227", "0.760", "[0.626-0.857]", "Research"],
            ["Institution", "153", "0.735", "[0.597-0.838]", "Research"],
            ["Distance", "61", "0.720", "[0.583-0.825]", "Legal"],
            ["Temporal", "22", "0.591", "[0.387-0.767]", "Legal"],
            ["Penalty", "19", "0.579", "[0.363-0.769]", "Legal"],
            ["Objective", "7", "0.571", "[0.250-0.842]", "Research"],
            ["Policy", "185", "0.551", "[0.413-0.681]", "Both"],
            ["Permit", "10", "0.500", "[0.237-0.763]", "Legal"],
        ],
        col_widths=[32, 18, 22, 32, 76],
    )

    pdf.body_text(
        "12 of 17 categories achieve >= 0.70 precision. 5 categories achieve >= 0.90 precision. "
        "Wilson score confidence intervals are used throughout (appropriate for small/medium samples)."
    )

    # ── Section 5: Filtering Pipeline ──
    pdf.add_page()
    pdf.section_title("5", "Multi-Stage Filtering Pipeline")
    pdf.body_text(
        "The filtering pipeline is the core innovation of the system. Rather than attempting exhaustive "
        "recall, the system aggressively filters false positives through 8 sequential stages. This "
        "precision-first approach is deliberate: in decision-support systems, false positives cost "
        "credibility more than missed extractions."
    )

    pdf.table(
        ["Stage", "Filter", "What It Catches"],
        [
            ["1", "Bibliography Detection", "Matches in reference sections (5 methods)"],
            ["2", "Garble Detection", "PDF column-merge artifacts, boilerplate"],
            ["3", "NLP Validation", "NER, POS tagging, coherence scoring"],
            ["4", "Marine Relevance", "Building regulations (Imar) vs marine context"],
            ["5", "Category-Specific Rules", "Per-category constraints (length, format)"],
            ["6", "False Positive Filter", "Non-marine domains (ML, robotics, etc.)"],
            ["7", "Deduplication", "MD5 hash-based duplicate removal"],
            ["8", "Confidence Scoring", "Multi-signal confidence calculation"],
        ],
        col_widths=[14, 42, 124],
    )

    pdf.subsection_title("Bibliography Detection (5 Methods)")
    pdf.body_text(
        "Bibliography sections are the largest single source of false positives. The system uses "
        "five complementary detection methods:"
    )
    pdf.bullet("Section header matching: 'References', 'KAYNAKCA', 'Bibliography'")
    pdf.bullet("CRediT statement detection: author contributions, data availability, funding")
    pdf.bullet("Citation density: 5+ bracketed citations [N] within 2,000 characters")
    pdf.bullet("DOI density: 3+ DOI patterns within 2,000 characters")
    pdf.bullet("Author-year density: 5+ 'Author, A.B., Year' patterns within 3,000 characters")

    pdf.subsection_title("Marine Relevance Scoring")
    pdf.body_text(
        "A critical filter for Turkish legal documents. Turkish building regulations (Imar Yonetmeligi) "
        "contain distance measurements, room dimensions, and setback requirements that regex patterns "
        "match incorrectly. The filter computes a marine/imar keyword ratio per sentence:"
    )
    pdf.code_block(
        "score = marine_keyword_count / (marine_keyword_count + imar_keyword_count)\n"
        "\n"
        "Marine terms:  coast, marine, fishing, port, sea, vessel, ...\n"
        "Imar terms:    floor height, building height, TAKS, KAKS, parcel, ...\n"
        "\n"
        "Thresholds:    Distance >= 0.20 | Finding >= 0.15 | Policy >= 0.05"
    )

    pdf.subsection_title("False Positive Filter (6 Signals)")
    pdf.bullet("Marine vs building keyword density in surrounding sentence")
    pdf.bullet("Building-specific regex patterns (TAKS, KAKS, floor height)")
    pdf.bullet("Law reference proximity detection")
    pdf.bullet("Non-marine domain term detection (neural network, deep learning, robot)")
    pdf.bullet("Weighted composite score across all signals")
    pdf.bullet("Rejection: imar >= 3 with no marine terms, or weighted score > 5")

    # ── Section 6: Bilingual Design ──
    pdf.add_page()
    pdf.section_title("6", "Bilingual Design")
    pdf.body_text(
        "The system handles Turkish and English as first-class languages with separate pattern sets "
        "rather than translations. This is essential because Turkish morphology requires fundamentally "
        "different regex design."
    )

    pdf.subsection_title("Pattern Examples")

    pdf.body_text("Distance extraction (Turkish):")
    pdf.code_block(
        'r"kiyidan 500 metre"  ->  coast + distance + unit\n'
        'r"en az 100 metre"    ->  qualifier(minimum) + value + unit\n'
        'r"50 ila 200 metre"   ->  range(min to max) + unit'
    )

    pdf.body_text("Distance extraction (English):")
    pdf.code_block(
        'r"100 metres from coast"     ->  value + unit + reference\n'
        'r"buffer zone of 500 m"      ->  type + value + unit\n'
        'r"between 50 and 200 km"     ->  range(min to max) + unit'
    )

    pdf.body_text("Prohibition extraction (Turkish):")
    pdf.code_block(
        'r"avcilik yasaktir"                 ->  fishing is prohibited\n'
        'r"koruma alaninda ... yasaktir"      ->  in protected area ... prohibited'
    )

    pdf.subsection_title("Key Linguistic Decisions")
    pdf.bullet("Turkish suffixes (-dan/-den, -inda/-inde, -sina/-sine) handled via alternation groups")
    pdf.bullet("Word boundaries required for short acronyms (AIS, VMS, ICES) to prevent substring matches")
    pdf.bullet("Turkish exception words (disinda, haric, mustesna) identified as scope qualifiers, not prohibitions -- a discovery that eliminated 70%+ false positives in the Prohibition category")
    pdf.bullet("Species use explicit name lists only; generic 'Genus species' pattern rejected (80%+ FP rate)")

    # ── Section 7: Precision Improvement ──
    pdf.section_title("7", "Iterative Precision Improvement")
    pdf.body_text(
        "The system was developed over 7 versions with systematic error analysis and targeted fixes "
        "at each stage. Total improvement: +73% macro precision while reducing extractions by 54%."
    )

    pdf.table(
        ["Version", "Macro P", "Extractions", "Key Changes"],
        [
            ["v3 (Baseline)", "0.448", "6,914", "Initial regex extractors"],
            ["v4", "0.514", "6,380", "Added NLP filters (NER, POS, coherence)"],
            ["v5", "0.567", "4,178", "Bibliography detection (5 methods)"],
            ["v6", "0.711", "3,248", "Targeted regex and threshold fixes"],
            ["v7", "0.777", "3,155", "Context-aware filtering, NLP confidence"],
        ],
        col_widths=[28, 20, 24, 108],
    )

    pdf.subsection_title("Impact of Each Innovation")
    pdf.bullet("Bibliography detection: ~15% precision gain (single most impactful filter)")
    pdf.bullet("Marine relevance thresholding: ~12% precision gain")
    pdf.bullet("Category-specific quantitative requirements: ~8% precision gain")
    pdf.bullet("NLP validation (NER + POS + coherence): ~5% precision gain")

    pdf.subsection_title("Approaches Tried and Removed")
    pdf.bullet("Generic 'Genus species' patterns for species extraction (80% false positive rate)")
    pdf.bullet("Exception-word patterns for prohibitions (70% FP rate -- Turkish qualifiers misidentified)")
    pdf.bullet("Generic stakeholder patterns without NER validation (60% FP rate)")

    # ── Section 8: Validation ──
    pdf.add_page()
    pdf.section_title("8", "Validation Methodology")
    pdf.body_text(
        "Validation follows a rigorous protocol designed for reproducibility and statistical soundness."
    )

    pdf.numbered_item("1", "Run the pipeline to generate raw_results_*.json with all extractions.", "Run Pipeline:")
    pdf.numbered_item("2", "Stratified random sampling (seed=42) selects up to 50 samples per category. Categories with fewer than 5 extractions include all samples.", "Generate Validation Sheets:")
    pdf.numbered_item("3", "Each sample is manually annotated as correct (y) or incorrect (n) with error type classification (wrong_category, false_positive, extraction_error, garbled_text, etc.).", "Manual Annotation:")
    pdf.numbered_item("4", "Wilson score confidence intervals computed per category. Macro average (mean of category precisions) and micro average (total correct / total annotated) reported.", "Compute Metrics:")
    pdf.ln(2)

    pdf.highlight_box(
        "Final Validation Results (v7):\n"
        "  Total Samples:       618 across 17 categories\n"
        "  Correct Extractions: 500\n"
        "  Macro Precision:     0.777\n"
        "  Micro Precision:     0.809 [95% CI: 0.776-0.838]\n"
        "  Categories >= 0.70:  12 of 17\n"
        "  Categories >= 0.90:  5 of 17"
    )

    # ── Section 9: Output ──
    pdf.section_title("9", "System Outputs")
    pdf.body_text("The pipeline generates six types of output:")
    pdf.ln(2)

    pdf.bullet("raw_results_*.json -- Complete structured extractions with confidence scores, page numbers, context, and marine relevance for every match")
    pdf.bullet("knowledge.db -- SQLite database with cross-references linking related extractions across documents (species, methods, protected areas)")
    pdf.bullet("dashboard_*.html -- Interactive HTML dashboard with Chart.js visualizations: extractions by category, precision scatter plots, gap severity distribution")
    pdf.bullet("msp_report_*.txt -- Human-readable summary report with statistics per category and document")
    pdf.bullet("gap_report_*.txt -- Identified research, legal, data, and integration gaps with severity ratings")
    pdf.bullet("validation_sheets/*.csv -- Stratified samples for manual precision validation")

    # ── Section 10: Design Decisions ──
    pdf.add_page()
    pdf.section_title("10", "Key Design Decisions")

    pdf.subsection_title("Precision Over Recall")
    pdf.body_text(
        "The system deliberately prioritizes precision over recall. In a decision-support context for "
        "marine spatial planning, false positives (incorrect extractions presented as facts) are more "
        "costly than false negatives (missed extractions). The 54% reduction in total extractions from "
        "v3 to v7 represents almost entirely false positives being removed."
    )

    pdf.subsection_title("Regex + Classical NLP (No Deep Learning)")
    pdf.body_text(
        "The system uses regex patterns with NLTK-based NLP validation rather than transformer models. "
        "This decision provides three advantages: (1) Full interpretability -- every extraction traces to "
        "a specific pattern and every rejection to a specific filter; (2) No training data requirement -- "
        "the bilingual Turkish/English corpus has no existing annotated dataset; (3) Reproducibility -- "
        "deterministic output for the same input, independent of GPU hardware or model versions."
    )

    pdf.subsection_title("Bilingual From the Ground Up")
    pdf.body_text(
        "Turkish and English patterns are developed independently rather than translated. Turkish "
        "agglutinative morphology (suffixes like -dan, -inda, -sina) requires fundamentally different "
        "regex design. This avoids the quality loss inherent in pattern translation."
    )

    pdf.subsection_title("Multi-Stage Filtering Over Single-Pass Classification")
    pdf.body_text(
        "Rather than a single classifier deciding accept/reject, the 8-stage pipeline allows each filter "
        "to specialize in detecting a specific type of false positive. This modular approach makes the "
        "system debuggable: when a false positive passes through, the failing stage can be identified "
        "and fixed without affecting other stages."
    )

    # ── Section 11: Technical Architecture ──
    pdf.section_title("11", "Technical Architecture")

    pdf.subsection_title("Code Structure")
    pdf.code_block(
        "msp_extractor_modular/\n"
        "  main.py                    # Pipeline entry point\n"
        "  extractors/                # 21 category-specific extractors\n"
        "    base_extractor.py        #   Abstract base class (8-stage filter)\n"
        "    distance_extractor.py    #   Distance regulations\n"
        "    species_extractor.py     #   Species mentions\n"
        "    prohibition_extractor.py #   Prohibited activities\n"
        "    ...                      #   (18 more extractors)\n"
        "  processors/                # Document-type orchestrators\n"
        "    q1_paper_processor.py    #   Research paper processing (13 extractors)\n"
        "    legal_processor.py       #   Legal document processing (10 extractors)\n"
        "  utils/                     # Shared utilities\n"
        "    bibliography_detector.py #   5-method bibliography detection\n"
        "    filters.py               #   FP filter, garble detection, OCR normalization\n"
        "    nlp_filters.py           #   NER, POS, coherence validation\n"
        "  data_structures/           # 21 typed dataclass models\n"
        "  scripts/                   # Validation and metrics tools\n"
        "    generate_validation_sheets.py\n"
        "    compute_metrics.py\n"
        "    generate_paper_tables.py"
    )

    pdf.subsection_title("Dependencies")
    pdf.bullet("pdfplumber -- PDF text extraction with page-level positioning")
    pdf.bullet("NLTK -- Named entity recognition, POS tagging, tokenization")
    pdf.bullet("scikit-learn -- TF-IDF category classification")
    pdf.bullet("Chart.js (embedded) -- Interactive dashboard visualizations")

    pdf.output("system_overview.pdf")
    print("PDF generated: system_overview.pdf")


if __name__ == "__main__":
    build_pdf()
