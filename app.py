# app.py
import streamlit as st
import os
from extractor import extract_text
from jsonfileconverter import extract_info_from_text
import base64

# Ensure the temp_files directory exists
os.makedirs("temp_files", exist_ok=True)

# Streamlit UI Configuration
st.set_page_config(layout="wide")
st.title("AI-Powered Document Extractor")

# File uploader
uploaded_file = st.file_uploader(
    "Upload a Document (PNG, JPG, JPEG, PDF, DOCX)",
    type=["png", "jpg", "jpeg", "pdf", "docx"]
)

if uploaded_file:
    # Save uploaded file to temp_files directory
    file_path = os.path.join("temp_files", uploaded_file.name)
    with open(file_path, "wb") as f:
        f.write(uploaded_file.getbuffer())

    # Extract text
    extracted_text = extract_text(file_path)

    # Convert text to JSON
    structured_json = extract_info_from_text(extracted_text)

    # Layout: Two columns for PDF/JSON and an expander for extracted text
    col1, col2 = st.columns([1, 1])

    with col1:
        st.subheader("📄 PDF Preview")
        if uploaded_file.type == "application/pdf":
            # Display PDF using an iframe
            with open(file_path, "rb") as f:
                base64_pdf = base64.b64encode(f.read()).decode("utf-8")
            pdf_display = f'<iframe src="data:application/pdf;base64,{base64_pdf}" width="100%" height="500px"></iframe>'
            st.markdown(pdf_display, unsafe_allow_html=True)
        else:
            st.error("PDF preview only available for .pdf files")

    with col2:
        st.subheader("🧠 AI-Extracted JSON Output")
        st.text_area("Structured JSON", structured_json, height=500)

        # Download button for JSON
        st.download_button(
            label="📥 Download JSON",
            data=structured_json,
            file_name="output.json",
            mime="application/json",
        )

    # Show raw extracted text in an expander at the bottom
    with st.expander("🔍 View Raw Extracted Text", expanded=True):
        st.text_area("Extracted Text", extracted_text, height=200)

    # Cleanup temporary files
    if os.path.exists(file_path):
        os.remove(file_path)
