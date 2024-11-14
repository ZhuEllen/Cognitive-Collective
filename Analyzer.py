import os
import json
import fitz  # PyMuPDF for PDF text extraction
import zipfile
import requests
from transformers import pipeline

class ReportAnalyzer:
    def __init__(self, json_file_path):
        # Load JSON configuration
        self.config = self.load_json_config(json_file_path)
        
        # Initialize transformers pipelines
        summarizer_model = self.config["models"]["summarizer"]
        sentiment_model = self.config["models"]["sentiment_analyzer"]
        self.summarizer = pipeline("summarization", model=summarizer_model)
        self.sentiment_analyzer = pipeline("sentiment-analysis", model=sentiment_model)
        
        # Set up Azure OpenAI API parameters from JSON
        self.endpoint = self.config["openai_settings"]["endpoint"]
        self.api_key = self.config["openai_settings"]["api_key"]
        self.deployment_id = self.config["openai_settings"]["deployment_id"]

    def load_json_config(self, json_file_path):
        """Load JSON configuration file."""
        with open(json_file_path, 'r') as file:
            return json.load(file)

    def extract_text_from_pdf(self, filepath):
        """Extract text from a PDF file."""
        text = ""
        with fitz.open(filepath) as pdf:
            for page in pdf:
                text += page.get_text()
        return text

    def process_reports(self):
        """Extract, summarize, and analyze sentiment from PDFs within ZIP files based on JSON config."""
        esg_summaries = {}
        for report in self.config["reports"]:
            zip_file = report["name"]
            report_type = report["type"]
            with zipfile.ZipFile(zip_file, 'r') as archive:
                archive.extractall("extracted_reports")

            for filename in os.listdir("extracted_reports"):
                if filename.endswith(".pdf"):
                    filepath = os.path.join("extracted_reports", filename)
                    text = self.extract_text_from_pdf(filepath)
                    
                    # Summarize the text and analyze sentiment
                    limited_text = text[:2000] if len(text) > 2000 else text
                    summary = self.summarizer(limited_text, max_length=150, min_length=50, do_sample=False)[0]['summary_text']
                    sentiment = self.sentiment_analyzer(summary)[0]
                    
                    # Store results
                    esg_summaries[filename] = {
                        "Summary": summary,
                        "Sentiment": sentiment,
                        "Type": report_type,
                        "Prompt": report["prompt"]
                    }

            # Clean up extracted files
            for file in os.listdir("extracted_reports"):
                os.remove(os.path.join("extracted_reports", file))
            os.rmdir("extracted_reports")
        
        return esg_summaries

    def generate_scenario(self, report_name, report_content, custom_prompt):
        """Generate scenario analysis based on report summary and custom prompt using Azure OpenAI."""
        # Use custom prompt from JSON config
        prompt = (
            f"Analyze the following report summary from {report_name}: '{report_content}'. "
            f"{custom_prompt}"
        )

        # Data payload for the API call
        data = {
            "messages": [
                {"role": "system", "content": "You are a financial analyst creating economic scenarios based on report summaries."},
                {"role": "user", "content": prompt}
            ],
            "max_tokens": 200,
            "temperature": 0.7,
            "n": 1
        }

        # API headers
        headers = {
            "Content-Type": "application/json",
            "api-key": self.api_key,
        }

        # Make the API call to Azure OpenAI
        response = requests.post(
            f"{self.endpoint}openai/deployments/{self.deployment_id}/chat/completions?api-version=2023-03-15-preview",
            headers=headers,
            json=data
        )

        # Check and handle the response
        if response.status_code == 200:
            response_json = response.json()
            try:
                return response_json['choices'][0]['message']['content'].strip()
            except (KeyError, IndexError) as e:
                print(f"Unexpected response format for {report_name}: {response_json}")
                return None
        else:
            print(f"Failed to fetch scenario for {report_name}. Status code: {response.status_code}, Error: {response.text}")
            return None

    def analyze_reports(self):
        """Process ESG reports and generate scenario insights."""
        esg_summaries = self.process_reports()
        scenarios = {}
        for report_name, report_content in esg_summaries.items():
            # Retrieve the custom prompt for each report
            custom_prompt = report_content["Prompt"]
            scenario = self.generate_scenario(report_name, report_content['Summary'], custom_prompt)
            scenarios[report_name] = {
                "Summary": report_content["Summary"],
                "Sentiment": report_content["Sentiment"],
                "Scenario Analysis": scenario,
                "Type": report_content["Type"]
            }
        return scenarios
