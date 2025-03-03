import streamlit as st
import pdfplumber  # For PDF extraction
import pytesseract
from PIL import Image
import os
from dotenv import load_dotenv
from langchain_groq import ChatGroq
from docx import Document  # For Word document extraction
import base64
from datetime import datetime
import re
from fpdf import FPDF

# Tesseract OCR path
pytesseract.pytesseract.tesseract_cmd = r"tess/tesseract.exe"

# Load environment variables
load_dotenv()
API_KEY = os.getenv("GROQ_API_KEY")
llm = ChatGroq(groq_api_key=API_KEY)

# Enhanced OCR for multi-language and handwritten text
def extract_text_from_image(image, languages="eng"):
    custom_config = r'--oem 1 --psm 6'
    return pytesseract.image_to_string(image, lang=languages, config=custom_config)

# Text extraction from PDF
def extract_text_from_pdf(pdf_file, languages="eng"):
    text = ""
    try:
        with pdfplumber.open(pdf_file) as pdf:
            for page in pdf.pages:
                if page.extract_text():
                    text += page.extract_text()
                else:
                    image = page.to_image().original
                    text += extract_text_from_image(image, languages)
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

# Generate PDF file with readable template for doctors
def generate_pdf(data, file_name="extracted_data.pdf"):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.set_font("Arial", size=14)
    pdf.set_text_color(50, 50, 50)

    # Add a title
    pdf.set_font("Arial", style='B', size=16)
    pdf.cell(200, 10, txt="Patient Information Report", ln=True, align='C')
    pdf.ln(10)

    # Add content in a formatted way
    pdf.set_font("Arial", size=12)
    for line in data.split('\n'):
        try:
            pdf.multi_cell(0, 10, line.encode('latin-1', 'replace').decode('latin-1'))
        except UnicodeEncodeError:
            pdf.multi_cell(0, 10, line.encode('latin-1', 'ignore').decode('latin-1'))
        pdf.ln(2)

    pdf.output(file_name)

# Main app logic
def main():
    st.set_page_config(layout="wide")
    st.title("Patient Document Parser & AI Extractor")

    # Document upload and language selection at the top
    uploaded_file = st.file_uploader("Upload Document", type=["pdf", "png", "jpg", "jpeg", "docx"])
    languages = st.multiselect(
        "Select OCR Languages",
        options=["eng", "deu", "fra", "jpn", "spa", "hin"],
        default=["eng"]
    )
    selected_languages = "+".join(languages)

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
                extracted_text = extract_text_from_pdf(temp_file_path, selected_languages)

            elif "docx" in file_type:
                st.write("### Uploaded Word Document:")
                extracted_text = extract_text_from_docx(uploaded_file)
                st.text_area("Preview", extracted_text, height=300)

            else:
                image = Image.open(uploaded_file)
                st.image(image, caption="Uploaded Image", use_column_width=True)
                extracted_text = extract_text_from_image(image, selected_languages)

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
                st.download_button("Download Text", api_response_text, file_name="extracted_data.txt", mime="text/plain")
            elif download_format == "PDF":
                pdf_file_name = "extracted_data.pdf"
                generate_pdf(extracted_text, pdf_file_name)
                with open(pdf_file_name, "rb") as f:
                    st.download_button("Download PDF", f, file_name=pdf_file_name, mime="application/pdf")

if __name__ == "__main__":
    main()
