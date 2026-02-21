"""
Generate beautiful PDF reports for the MSP Knowledge Extraction System.
Produces: (1) Progress Report PDF, (2) Email PDF
"""
import sys
from pathlib import Path

if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

from fpdf import FPDF

PROJECT_ROOT = Path(__file__).parent.parent
OUTPUT_DIR = PROJECT_ROOT / "paper_assets"


class MSPReport(FPDF):
    """Custom PDF with header/footer styling."""

    def __init__(self):
        super().__init__()
        self.set_auto_page_break(auto=True, margin=25)

    def header(self):
        self.set_font("Helvetica", "I", 8)
        self.set_text_color(100, 100, 100)
        self.cell(0, 5, "MSP Knowledge Extraction System - Progress Report", align="R")
        self.ln(3)
        self.set_draw_color(0, 102, 153)
        self.set_line_width(0.5)
        self.line(10, 12, 200, 12)
        self.ln(5)

    def footer(self):
        self.set_y(-20)
        self.set_draw_color(0, 102, 153)
        self.set_line_width(0.3)
        self.line(10, self.get_y(), 200, self.get_y())
        self.ln(3)
        self.set_font("Helvetica", "I", 8)
        self.set_text_color(100, 100, 100)
        self.cell(0, 5, f"Page {self.page_no()}/{{nb}}", align="C")

    def section_title(self, num, title):
        self.set_font("Helvetica", "B", 14)
        self.set_text_color(0, 82, 133)
        self.cell(0, 10, f"{num}. {title}", new_x="LMARGIN", new_y="NEXT")
        self.set_draw_color(0, 102, 153)
        self.set_line_width(0.3)
        self.line(10, self.get_y(), 120, self.get_y())
        self.ln(3)

    def subsection_title(self, title):
        self.set_font("Helvetica", "B", 11)
        self.set_text_color(0, 102, 153)
        self.cell(0, 8, title, new_x="LMARGIN", new_y="NEXT")
        self.ln(1)

    def body_text(self, text):
        self.set_font("Helvetica", "", 10)
        self.set_text_color(40, 40, 40)
        self.multi_cell(0, 5.5, text)
        self.ln(2)

    def bold_text(self, text):
        self.set_font("Helvetica", "B", 10)
        self.set_text_color(40, 40, 40)
        self.multi_cell(0, 5.5, text)
        self.ln(1)

    def bullet(self, text):
        self.set_font("Helvetica", "", 10)
        self.set_text_color(40, 40, 40)
        self.set_x(10)
        self.multi_cell(0, 5.5, "  - " + text)

    def table(self, headers, rows, col_widths=None):
        """Draw a styled table."""
        if col_widths is None:
            available = 190
            col_widths = [available / len(headers)] * len(headers)

        # Header
        self.set_font("Helvetica", "B", 9)
        self.set_fill_color(0, 82, 133)
        self.set_text_color(255, 255, 255)
        for i, h in enumerate(headers):
            self.cell(col_widths[i], 7, h, border=1, fill=True, align="C")
        self.ln()

        # Rows
        self.set_font("Helvetica", "", 9)
        self.set_text_color(40, 40, 40)
        fill = False
        for row in rows:
            if fill:
                self.set_fill_color(235, 243, 248)
            else:
                self.set_fill_color(255, 255, 255)

            max_h = 7
            for i, cell in enumerate(row):
                self.cell(col_widths[i], max_h, str(cell)[:50], border=1, fill=True, align="C")
            self.ln()
            fill = not fill
        self.ln(3)

    def key_metric_box(self, label, value, color=(0, 82, 133)):
        """Draw a highlighted metric box."""
        self.set_fill_color(*color)
        self.set_text_color(255, 255, 255)
        self.set_font("Helvetica", "B", 11)
        self.cell(45, 18, "", border=0, fill=True)
        x = self.get_x() - 45
        y = self.get_y()
        self.set_xy(x, y + 2)
        self.cell(45, 6, value, align="C")
        self.set_xy(x, y + 9)
        self.set_font("Helvetica", "", 7)
        self.cell(45, 6, label, align="C")
        self.set_xy(x + 48, y)


def generate_progress_report():
    pdf = MSPReport()
    pdf.alias_nb_pages()
    pdf.add_page()

    # Title page
    pdf.set_font("Helvetica", "B", 24)
    pdf.set_text_color(0, 82, 133)
    pdf.ln(20)
    pdf.cell(0, 15, "MSP Knowledge Extraction", align="C", new_x="LMARGIN", new_y="NEXT")
    pdf.cell(0, 15, "System", align="C", new_x="LMARGIN", new_y="NEXT")
    pdf.ln(5)
    pdf.set_font("Helvetica", "", 16)
    pdf.set_text_color(80, 80, 80)
    pdf.cell(0, 10, "Progress Report", align="C", new_x="LMARGIN", new_y="NEXT")
    pdf.ln(5)
    pdf.set_draw_color(0, 102, 153)
    pdf.set_line_width(1)
    pdf.line(60, pdf.get_y(), 150, pdf.get_y())
    pdf.ln(10)

    pdf.set_font("Helvetica", "", 11)
    pdf.set_text_color(60, 60, 60)
    pdf.cell(0, 8, "Author: Ahsan Hussain Khan", align="C", new_x="LMARGIN", new_y="NEXT")
    pdf.cell(0, 8, "Date: 17 February 2026", align="C", new_x="LMARGIN", new_y="NEXT")
    pdf.ln(3)
    pdf.set_font("Helvetica", "", 9)
    pdf.cell(0, 6, "Supervisors: Manuel Marey Perez, David Mateo Fouz Varela", align="C", new_x="LMARGIN", new_y="NEXT")

    # Key metrics boxes
    pdf.ln(15)
    pdf.set_x(15)
    pdf.key_metric_box("Documents Processed", "273")
    pdf.key_metric_box("Total Extractions", "6,914")
    pdf.key_metric_box("Categories", "21", (0, 130, 100))
    pdf.key_metric_box("Source Files", "67", (0, 130, 100))
    pdf.ln(25)

    # === Section 1: Executive Summary ===
    pdf.add_page()
    pdf.section_title(1, "Executive Summary")
    pdf.body_text(
        "A fully functional AI-based knowledge extraction system has been developed for Marine Spatial Planning (MSP) "
        "documents. The system processes both English-language scientific literature (248 papers) and Turkish legal "
        "documents (25 laws/regulations), automatically extracting structured knowledge across 21 categories."
    )
    pdf.body_text(
        "The system includes a multi-stage filtering pipeline (bibliography detection, garble detection, "
        "marine relevance scoring, false positive filtering, deduplication) that reduces noise by 83% compared "
        "to baseline keyword matching. Validation shows strong performance for structured categories "
        "(legal references 95.7%, protected areas 90.5%, stakeholders 82.0%) but limitations for "
        "semantic categories that require contextual understanding."
    )

    # === Section 2: System Architecture ===
    pdf.section_title(2, "System Architecture")
    pdf.body_text("The system comprises 67 Python source files organized across 8 modules:")
    pdf.bullet("21 specialized extractors for different knowledge categories")
    pdf.bullet("Multi-stage filtering pipeline with 5 components")
    pdf.bullet("Bilingual support: English research papers + Turkish legal documents")
    pdf.bullet("Thread-parallel processing: 8 concurrent workers")
    pdf.bullet("SQLite knowledge base with cross-linking between entities")
    pdf.bullet("Gap detection: research, legal, data, and integration gap analysis")
    pdf.ln(3)

    pdf.subsection_title("Data Sources")
    pdf.table(
        ["Source", "Count", "Language", "Content"],
        [
            ["Research papers", "248 PDFs", "English", "Q1 journal articles on MSP"],
            ["Turkish legal docs", "25 PDFs", "Turkish", "Maritime laws, regulations"],
            ["Total", "273 PDFs", "Bilingual", ""],
        ],
        [40, 30, 30, 90]
    )

    # === Section 3: Extraction Results ===
    pdf.section_title(3, "Extraction Results")
    pdf.body_text("The system extracted 6,914 structured knowledge items across 21 categories:")

    pdf.table(
        ["Category", "Count", "Category", "Count"],
        [
            ["Data Source", "1,319", "Gap", "192"],
            ["Legal Reference", "1,039", "Result", "162"],
            ["Stakeholder", "753", "Finding", "144"],
            ["Institution", "727", "Distance", "102"],
            ["Species", "664", "Conflict", "62"],
            ["Policy", "571", "Protected Area", "42"],
            ["Method", "529", "Prohibition", "37"],
            ["Environmental", "493", "Other (5 cats)", "78"],
        ],
        [45, 30, 45, 30]
    )

    # === Section 4: Validation ===
    pdf.add_page()
    pdf.section_title(4, "Validation Results")

    pdf.subsection_title("4.1 Precision (795 samples across 20 categories)")
    pdf.body_text("Precision was measured by sampling up to 50 extractions per category and annotating each as correct or incorrect.")

    pdf.bold_text("High-performing categories (>50% precision):")
    pdf.table(
        ["Category", "N", "Precision", "95% CI"],
        [
            ["Legal Reference", "46", "0.957", "[0.855-0.988]"],
            ["Protected Area", "42", "0.905", "[0.779-0.962]"],
            ["Stakeholder", "50", "0.820", "[0.692-0.902]"],
            ["Method", "50", "0.660", "[0.522-0.776]"],
            ["Permit", "10", "0.600", "[0.313-0.832]"],
            ["Penalty", "17", "0.588", "[0.360-0.784]"],
            ["Objective", "7", "0.571", "[0.250-0.842]"],
            ["Distance", "49", "0.531", "[0.394-0.663]"],
        ],
        [45, 20, 30, 50]
    )

    pdf.bold_text("Low-performing categories (<50% precision):")
    pdf.table(
        ["Category", "N", "Precision", "Main Issue"],
        [
            ["Institution", "50", "0.480", "Incomplete names"],
            ["Policy", "50", "0.420", "Journal name confusion"],
            ["Gap", "50", "0.400", "Cross-line garbling"],
            ["Finding", "50", "0.380", "Cross-line garbling"],
            ["Data Source", "50", "0.340", "Generic terms"],
            ["Species", "50", "0.220", "Generic group names"],
            ["Environmental", "50", "0.080", "Semantic confusion"],
        ],
        [40, 20, 30, 60]
    )

    pdf.bold_text("Overall: Macro Precision = 0.448 | Micro Precision = 0.445")

    # Recall
    pdf.subsection_title("4.2 Recall & F1 (10-document gold standard)")
    pdf.body_text(
        "Recall was measured by exhaustively identifying ALL true mentions in 10 marine/MSP documents "
        "(969 total mentions) and comparing with system extractions."
    )

    pdf.table(
        ["Category", "Gold Standard", "Matched", "Recall", "Precision", "F1"],
        [
            ["Species", "186", "71", "0.382", "0.220", "0.279"],
            ["Method", "206", "32", "0.155", "0.660", "0.251"],
            ["Stakeholder", "219", "26", "0.119", "0.820", "0.207"],
            ["Environmental", "167", "12", "0.072", "0.080", "0.076"],
            ["Finding", "191", "9", "0.047", "0.380", "0.084"],
            ["Macro Avg", "969", "150", "0.155", "0.432", "0.180"],
        ],
        [35, 30, 25, 25, 25, 25]
    )

    # Error analysis
    pdf.subsection_title("4.3 Error Distribution (441 false positives)")
    pdf.table(
        ["Error Type", "Count", "%", "Description"],
        [
            ["Cross-line", "121", "27.4%", "PDF multi-column garbling"],
            ["False Positive", "109", "24.7%", "Generic terms"],
            ["Bibliography", "78", "17.7%", "Reference section text"],
            ["Wrong Category", "58", "13.2%", "Misclassified"],
            ["Wrong Value", "53", "12.0%", "Incorrect value"],
            ["Non-marine", "20", "4.5%", "Non-marine content"],
        ],
        [35, 20, 20, 70]
    )

    # === Section 5: Comparative Evaluation ===
    pdf.add_page()
    pdf.section_title(5, "Comparative Evaluation")

    pdf.subsection_title("5.1 Baseline Comparison (keyword matching vs our system)")
    pdf.table(
        ["Category", "Baseline", "Our System", "Reduction"],
        [
            ["Species", "6,066", "664", "89.1%"],
            ["Method", "10,415", "529", "94.9%"],
            ["Stakeholder", "9,631", "753", "92.2%"],
            ["Environmental", "11,447", "493", "95.7%"],
            ["Finding", "3,004", "144", "95.2%"],
            ["Total", "40,563", "6,914", "83.0%"],
        ],
        [45, 40, 40, 40]
    )
    pdf.body_text("Our multi-stage filtering pipeline eliminates 83% of noise compared to naive keyword matching.")

    pdf.subsection_title("5.2 Ablation Study (20-document sample)")
    pdf.table(
        ["Configuration", "Extractions", "Change", "Impact"],
        [
            ["Full System", "232", "---", "---"],
            ["No FP Filter", "243", "+11", "+4.7%"],
            ["No Blacklists", "236", "+4", "+1.7%"],
            ["No Marine Filter", "235", "+3", "+1.3%"],
            ["No Legal Ref Filter", "234", "+2", "+0.9%"],
            ["No Dedup", "232", "+0", "+0.0%"],
        ],
        [50, 35, 30, 30]
    )

    # === Section 6: Assessment ===
    pdf.section_title(6, "Strengths and Limitations")

    pdf.subsection_title("What Works Well")
    pdf.bullet("Turkish legal extraction: Legal references 95.7%, Protected areas 90.5%")
    pdf.bullet("Stakeholder identification: 82.0% precision")
    pdf.bullet("Method extraction: 66.0% precision")
    pdf.bullet("Noise reduction: 83% fewer false positives than keyword baseline")
    pdf.bullet("Scalable architecture: 273 documents processed in parallel")
    pdf.ln(3)

    pdf.subsection_title("What Needs Improvement")
    pdf.bullet("Low recall (15%): System misses 85% of true mentions due to regex limitations")
    pdf.bullet("Cross-line garbling (27.4% of errors): PDF layout parsing issues")
    pdf.bullet("Semantic categories (environmental 8%, finding 38%): Require contextual understanding")
    pdf.bullet("Overall F1 = 0.180: Below Q1 journal standards (typically >0.60)")
    pdf.ln(3)

    # === Section 7: Path Forward ===
    pdf.add_page()
    pdf.section_title(7, "Decision Points - Guidance Needed")

    pdf.subsection_title("7.1 Approach for Q1 Journal")
    pdf.body_text("Three options for improving performance to Q1 standards:")
    pdf.table(
        ["Option", "Expected F1", "Effort", "Risk"],
        [
            ["A. Keep improving regex", "~0.25-0.30", "Low", "Ceiling too low"],
            ["B. Full LLM extraction", "~0.70-0.80", "High", "API costs"],
            ["C. Hybrid (regex+LLM)", "~0.65-0.75", "Medium", "Best tradeoff"],
        ],
        [55, 35, 30, 45]
    )
    pdf.body_text(
        "Recommended: Option C (Hybrid). Keep regex for structured legal text where it excels "
        "(legal references 95.7%, protected areas 90.5%). Use LLM for semantic categories "
        "(species, methods, environmental, findings). The comparison between approaches "
        "becomes a research contribution itself."
    )

    pdf.subsection_title("7.2 Conference Paper (AEIPRO, deadline March 28)")
    pdf.body_text(
        "Proposed scope: Focus on methodology and Turkish coast case study. "
        "Show system architecture, baseline comparison (83% noise reduction), "
        "and top category results. Keep full P/R/F1 evaluation and LLM hybrid for Q1 paper."
    )

    pdf.subsection_title("7.3 Questions for Professors")
    pdf.bullet("Do you agree with the hybrid approach (regex + LLM) for Q1?")
    pdf.bullet("What scope is appropriate for the conference paper without overlapping Q1?")
    pdf.bullet("Which Q1 journal are we targeting? (Ocean & Coastal Management? Marine Policy?)")
    pdf.bullet("Should the Q1 paper emphasize the extraction system or the MSP knowledge base applications?")

    # === Section 8: Timeline ===
    pdf.ln(5)
    pdf.section_title(8, "Status and Timeline")
    pdf.table(
        ["Task", "Status", "Notes"],
        [
            ["System architecture (67 files)", "COMPLETE", "21 extractors, 8 modules"],
            ["PDF processing pipeline", "COMPLETE", "273 docs, parallel"],
            ["Extraction (regex-based)", "COMPLETE", "6,914 extractions"],
            ["Multi-stage filtering", "COMPLETE", "5 filter components"],
            ["Precision validation", "COMPLETE", "20 categories, 795 samples"],
            ["Recall gold standard", "COMPLETE", "10 docs, 969 mentions"],
            ["Baseline comparison", "COMPLETE", "83% noise reduction"],
            ["Ablation study", "COMPLETE", "5 conditions tested"],
            ["Error analysis", "COMPLETE", "7 error types"],
            ["Conference paper", "TO DO", "Deadline: March 28"],
            ["LLM hybrid extraction", "TO DO", "Pending guidance"],
            ["Q1 journal paper", "TO DO", "Pending approach decision"],
        ],
        [60, 35, 60]
    )

    # Save
    output_path = OUTPUT_DIR / "MSP_Progress_Report_2026-02-17.pdf"
    pdf.output(str(output_path))
    print(f"Progress report: {output_path}")
    return output_path


def generate_email_pdf():
    pdf = FPDF()
    pdf.set_auto_page_break(auto=True, margin=20)
    pdf.add_page()

    # Header
    pdf.set_font("Helvetica", "B", 14)
    pdf.set_text_color(0, 82, 133)
    pdf.cell(0, 10, "Email to Professors", align="C", new_x="LMARGIN", new_y="NEXT")
    pdf.set_draw_color(0, 102, 153)
    pdf.set_line_width(0.5)
    pdf.line(10, pdf.get_y(), 200, pdf.get_y())
    pdf.ln(8)

    # Email fields
    pdf.set_font("Helvetica", "B", 10)
    pdf.set_text_color(80, 80, 80)
    pdf.cell(20, 7, "To:")
    pdf.set_font("Helvetica", "", 10)
    pdf.cell(0, 7, "Manuel Marey Perez, David Mateo Fouz Varela", new_x="LMARGIN", new_y="NEXT")

    pdf.set_font("Helvetica", "B", 10)
    pdf.cell(20, 7, "From:")
    pdf.set_font("Helvetica", "", 10)
    pdf.cell(0, 7, "Ahsan Hussain Khan", new_x="LMARGIN", new_y="NEXT")

    pdf.set_font("Helvetica", "B", 10)
    pdf.cell(20, 7, "Subject:")
    pdf.set_font("Helvetica", "", 10)
    pdf.cell(0, 7, "MSP Extraction System - Progress Report & Guidance Needed", new_x="LMARGIN", new_y="NEXT")

    pdf.set_font("Helvetica", "B", 10)
    pdf.cell(20, 7, "Date:")
    pdf.set_font("Helvetica", "", 10)
    pdf.cell(0, 7, "17 February 2026", new_x="LMARGIN", new_y="NEXT")

    pdf.ln(5)
    pdf.set_draw_color(200, 200, 200)
    pdf.line(10, pdf.get_y(), 200, pdf.get_y())
    pdf.ln(8)

    # Body
    W = 190
    pdf.set_font("Helvetica", "", 11)
    pdf.set_text_color(40, 40, 40)

    pdf.set_x(10); pdf.multi_cell(W, 6, "Dear Manuel and Mateo,")
    pdf.ln(3)
    pdf.set_x(10); pdf.multi_cell(W, 6, "I hope you are doing well. Following your feedback on my first report, I have been working intensively on the NLP-based extraction system as you suggested. I am happy to share that significant progress has been made, and I would like to present the current results and get your guidance on the next steps.")
    pdf.ln(2)
    pdf.set_x(10); pdf.multi_cell(W, 6, "Please find attached a detailed progress report. I will also upload the full codebase, extracted datasets, legal documents, and validation results to our OneDrive repository this week so you can review everything directly.")
    pdf.ln(3)

    pdf.set_font("Helvetica", "B", 11)
    pdf.set_x(10); pdf.multi_cell(W, 7, "Summary of work completed since January:")
    pdf.set_font("Helvetica", "", 10)
    pdf.set_x(10); pdf.multi_cell(W, 6, "  - Built a complete NLP extraction system: 67 Python files, 21 specialized extractors, multi-stage filtering pipeline")
    pdf.set_x(10); pdf.multi_cell(W, 6, "  - Processed 273 documents (248 English research papers + 25 Turkish legal texts)")
    pdf.set_x(10); pdf.multi_cell(W, 6, "  - Extracted 6,914 structured knowledge items across 21 categories")
    pdf.set_x(10); pdf.multi_cell(W, 6, "  - Full validation: precision (795 samples), recall (10-doc gold standard), baseline comparison, ablation study, error analysis")
    pdf.ln(3)

    pdf.set_font("Helvetica", "B", 11)
    pdf.set_x(10); pdf.multi_cell(W, 7, "Key results:")
    pdf.set_font("Helvetica", "", 10)
    pdf.set_x(10); pdf.multi_cell(W, 6, "  - Turkish legal extraction: legal references 95.7% precision, protected areas 90.5%")
    pdf.set_x(10); pdf.multi_cell(W, 6, "  - Stakeholder identification: 82.0%, research methods: 66.0%")
    pdf.set_x(10); pdf.multi_cell(W, 6, "  - 83% noise reduction compared to simple keyword matching")
    pdf.set_x(10); pdf.multi_cell(W, 6, "  - Overall F1: 0.180 (low recall is the main limitation of the rule-based approach)")
    pdf.ln(3)

    pdf.set_font("Helvetica", "B", 11)
    pdf.set_x(10); pdf.multi_cell(W, 7, "The main challenge and proposed solution:")
    pdf.set_font("Helvetica", "", 10)
    pdf.set_x(10); pdf.multi_cell(W, 6,
        "The rule-based approach works excellently for structured Turkish legal text but has a performance ceiling "
        "for semantic categories. I believe integrating LLM-based extraction for semantic categories while keeping "
        "the rule-based system for legal text would significantly improve results and provide a strong research "
        "contribution - comparing rule-based vs. LLM extraction for domain-specific knowledge extraction."
    )
    pdf.ln(3)

    pdf.set_font("Helvetica", "B", 11)
    pdf.set_x(10); pdf.multi_cell(W, 7, "I would appreciate your guidance on:")
    pdf.set_font("Helvetica", "", 10)
    pdf.set_x(10); pdf.multi_cell(W, 6, "  1. Do you agree with the hybrid approach (rule-based + LLM) for the Q1 paper?")
    pdf.set_x(10); pdf.multi_cell(W, 6, "  2. For the AEIPRO conference paper (deadline March 28): should I focus on methodology and Turkish case study, keeping the full evaluation for Q1?")
    pdf.set_x(10); pdf.multi_cell(W, 6, "  3. Which Q1 journal should we target? (I have included Renewable and Sustainable Energy Reviews in the corpus as you suggested.)")
    pdf.ln(3)

    pdf.set_x(10); pdf.multi_cell(W, 6,
        "The full report with all numbers, tables, and system details is attached (7 pages). "
        "I am ready to schedule a meeting at your convenience to discuss the path forward."
    )
    pdf.ln(5)
    pdf.set_x(10); pdf.multi_cell(W, 6, "Best regards,")
    pdf.set_x(10); pdf.multi_cell(W, 6, "Ahsan")

    output_path = OUTPUT_DIR / "Email_to_Professors_2026-02-17.pdf"
    pdf.output(str(output_path))
    print(f"Email PDF: {output_path}")
    return output_path


if __name__ == "__main__":
    print("Generating PDFs...\n")
    p1 = generate_progress_report()
    p2 = generate_email_pdf()
    print(f"\nDone! Files saved to {OUTPUT_DIR}")
