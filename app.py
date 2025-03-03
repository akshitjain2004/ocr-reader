import streamlit as st
st.set_page_config(layout="wide")  # Must be the first Streamlit command

import pdfplumber  # For PDF extraction
import os
from dotenv import load_dotenv
from langchain_groq import ChatGroq
from docx import Document  # For Word document extraction
import base64
from datetime import datetime
import re
from fpdf import FPDF
import json

# Azure Computer Vision imports
from azure.cognitiveservices.vision.computervision import ComputerVisionClient
from msrest.authentication import CognitiveServicesCredentials
from io import BytesIO

# Load environment variables
load_dotenv()
API_KEY = os.getenv("GROQ_API_KEY")
llm = ChatGroq(groq_api_key=API_KEY)

# Load Azure credentials from environment variables
AZURE_ENDPOINT = os.getenv("AZURE_ENDPOINT")
AZURE_API_KEY = os.getenv("AZURE_API_KEY")

# Note: Azure OCR supports multiple languages and handwritten text.
st.caption("Note: Our code supports multiple languages and handwritten text.")

# Azure OCR extraction from image bytes
def extract_text_from_image(image_bytes):
    if not AZURE_ENDPOINT or not AZURE_API_KEY:
        return "Error: Azure credentials not set."
    
    client = ComputerVisionClient(AZURE_ENDPOINT, CognitiveServicesCredentials(AZURE_API_KEY))
    try:
        img_stream = BytesIO(image_bytes)
        analysis = client.read_in_stream(img_stream, raw=True)
        operation_location = analysis.headers.get("Operation-Location")
        if not operation_location:
            return "Error: No operation location returned."
        operation_id = operation_location.split("/")[-1]

        # Poll for the result
        while True:
            result = client.get_read_result(operation_id)
            if result.status not in ["notStarted", "running"]:
                break

        # Process the result
        if result.status == "succeeded":
            extracted_text = ""
            for page in result.analyze_result.read_results:
                for line in page.lines:
                    extracted_text += line.text + "\n"
            return extracted_text
        else:
            return "Error: OCR extraction did not succeed."
    except Exception as e:
        return f"Error during OCR extraction: {str(e)}"

# Text extraction from PDF
def extract_text_from_pdf(pdf_file):
    text = ""
    try:
        with pdfplumber.open(pdf_file) as pdf:
            for page in pdf.pages:
                page_text = page.extract_text()
                if page_text:
                    text += page_text
                else:
                    page_image = page.to_image()
                    try:
                        img_bytes = page_image.to_bytes(format="PNG")
                    except Exception as e:
                        return f"Error extracting image bytes from PDF page: {str(e)}"
                    text += extract_text_from_image(img_bytes)
    except Exception as e:
        text = f"Error reading PDF: {str(e)}"
    return text

# Text extraction from Word documents
def extract_text_from_docx(docx_file):
    text = ""
    try:
        doc = Document(docx_file)
        for para in doc.paragraphs:
            text += para.text + "\n"
    except Exception as e:
        text = f"Error reading Word document: {str(e)}"
    return text

# Call to GroqCloud API with refined template
def call_groqcloud_api(text):
    try:
        prompt = f"""
        Extract key patient information from the document.
        Return a JSON with fields:
        - Name
        - Age (convert from Birthdate if available use today's date)
        - Birthdate
        - Address (parse into Street, City, State, Pincode)
        - Contact Information (Phone, Email)
        - Medical History
        - Diagnosis
        - Prescription Details
        - Any other relevant patient-specific information
        - Automatically calculate age from the birthdate if available (use today's date as reference)
        - Parse addresses into structured fields
        - Add custom fields based on content (e.g., emergency contacts, insurance details)
        - Do not write anything else other than json format, no note or explanation needed.
        Document:
        {text}
        """
        response = llm.invoke([prompt])
        return response.content
    except Exception as e:
        return f"Error: {str(e)}"

# Embed PDF in Streamlit UI
def display_pdf(file_path):
    with open(file_path, "rb") as f:
        base64_pdf = base64.b64encode(f.read()).decode("utf-8")
    pdf_display = f'<iframe src="data:application/pdf;base64,{base64_pdf}" width="100%" height="500px" type="application/pdf"></iframe>'
    st.markdown(pdf_display, unsafe_allow_html=True)

# New PDF generation function: table of key-value pairs and diagnosis summary
def generate_pdf_from_json(json_response, file_name="extracted_data.pdf"):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_auto_page_break(auto=True, margin=15)
    
    # Title
    pdf.set_font("Arial", "B", 16)
    pdf.cell(0, 10, "Patient Information Report", ln=True, align='C')
    pdf.ln(10)
    
    # Parse JSON
    try:
        data_dict = json.loads(json_response)
    except Exception as e:
        data_dict = {"Error": "Invalid JSON data"}
    
    # Table Header
    pdf.set_font("Arial", "B", 12)
    pdf.cell(50, 10, "Field", border=1)
    pdf.cell(0, 10, "Value", border=1, ln=True)
    
    # Table Rows: key-value pairs
    pdf.set_font("Arial", "", 12)
    for key, value in data_dict.items():
        pdf.cell(50, 10, str(key), border=1)
        # Ensure value is a string; if too long, let it wrap
        pdf.cell(0, 10, str(value), border=1, ln=True)
    
    pdf.ln(10)
    
    # Diagnosis Summary (derived from the "Diagnosis" field)
    diagnosis_summary = data_dict.get("Diagnosis", "No diagnosis available.")
    pdf.set_font("Arial", "B", 12)
    pdf.cell(0, 10, "Diagnosis Summary:", ln=True)
    pdf.set_font("Arial", "", 12)
    pdf.multi_cell(0, 10, str(diagnosis_summary))
    
    pdf.output(file_name)

# Main app logic
def main():
    st.title("Patient Document Parser & AI Extractor")

    # Document upload
    uploaded_file = st.file_uploader("Upload Document", type=["pdf", "png", "jpg", "jpeg"])

    col1, col2 = st.columns([1, 1])

    extracted_text = ""
    api_response_text = ""

    if uploaded_file:
        file_type = uploaded_file.type
        with col1:
            if "pdf" in file_type:
                st.write("### Uploaded PDF:")
                temp_file_path = f"temp_{uploaded_file.name}"
                with open(temp_file_path, "wb") as f:
                    f.write(uploaded_file.read())
                display_pdf(temp_file_path)
                extracted_text = extract_text_from_pdf(temp_file_path)

            elif "docx" in file_type:
                st.write("### Uploaded Word Document:")
                extracted_text = extract_text_from_docx(uploaded_file)
                st.text_area("Preview", extracted_text, height=300)

            else:
                # For image files, get the bytes directly and display using HTML (avoids PIL)
                image_bytes = uploaded_file.getvalue()
                encoded_image = base64.b64encode(image_bytes).decode('utf-8')
                st.markdown(
                    f'<img src="data:image/png;base64,{encoded_image}" alt="Uploaded Image" style="max-width:100%;">',
                    unsafe_allow_html=True
                )
                extracted_text = extract_text_from_image(image_bytes)

        # Call the GroqCloud API on the extracted text
        api_response_text = call_groqcloud_api(extracted_text)

    with col2:
        st.write("### Extracted AI Response (JSON):")
        st.text_area("", api_response_text, height=400)

        st.write("### Extracted Text:")
        st.text_area("", extracted_text, height=200)

        if api_response_text:
            download_format = st.selectbox("Download Format", ["JSON", "Text", "PDF"], index=0)
            if download_format == "JSON":
                st.download_button("Download JSON", api_response_text, file_name="extracted_data.json", mime="application/json")
            elif download_format == "Text":
                # For plain text, download the extracted text (not the JSON)
                st.download_button("Download Text", extracted_text, file_name="extracted_data.txt", mime="text/plain")
            elif download_format == "PDF":
                pdf_file_name = "extracted_data.pdf"
                # Use the new function to generate a formatted PDF from the JSON response
                generate_pdf_from_json(api_response_text, pdf_file_name)
                with open(pdf_file_name, "rb") as f:
                    st.download_button("Download PDF", f.read(), file_name=pdf_file_name, mime="application/pdf")

if __name__ == "__main__":
    main()
