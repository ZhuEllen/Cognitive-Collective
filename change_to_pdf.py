from fpdf import FPDF

class PDFReport(FPDF):
    def header(self):
        self.set_font("Arial", "B", 12)
        self.cell(0, 10, "Portfolio Analysis Report", 0, 1, "C")

    def add_report_section(self, report_name, summary, sentiment, scenario):
        self.set_font("Arial", "B", 10)
        self.cell(0, 10, report_name, 0, 1)

        self.set_font("Arial", "", 9)
        self.cell(0, 10, "Summary:", 0, 1)
        self.multi_cell(0, 10, summary)

        self.cell(0, 10, f"Sentiment: {sentiment['label']} (Score: {sentiment['score']:.2f})", 0, 1)

        self.cell(0, 10, "Scenario Analysis:", 0, 1)
        self.multi_cell(0, 10, scenario)
        self.ln(10)

