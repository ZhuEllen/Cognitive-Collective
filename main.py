from Analyzer import ReportAnalyzer
import streamlit as st
from change_to_pdf import PDFReport
# Initialize the ESGReportAnalyzer with JSON config path
analyzer = ReportAnalyzer(json_file_path="reports_config.json")

# Process the ESG reports and generate scenario analyses
results = analyzer.analyze_reports()

st.title("Analysis")

# Display each report's analysis
for report_name, content in results.items():
    st.header(f"{report_name}")
    st.subheader("Summary")
    st.write(content["Summary"])
    
    st.subheader("Sentiment")
    st.write(f"Sentiment: {content['Sentiment']['label']} (Score: {content['Sentiment']['score']:.2f})")
    
    st.subheader("Scenario Analysis")
    st.write(content["Scenario Analysis"])
    
    st.divider()

# Generate the report
pdf = PDFReport()
pdf.add_page()

for report_name, content in results.items():
    pdf.add_report_section(report_name, content["Summary"], content["Sentiment"], content["Scenario Analysis"])

# Save the PDF
pdf.output("Portfolio_Analysis_Report.pdf") 