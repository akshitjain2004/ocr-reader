# extractor.py
import pytesseract
from PIL import Image
import pdfplumber
from docx import Document
import os

# Tesseract path (update as per your system)
pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"

def extract_text(file_path: str) -> str:
    """Extract text from image, PDF, or Word documents."""
    text = ""

    # Determine file type
    file_ext = os.path.splitext(file_path)[-1].lower()

    try:
        # Extract text from images
        if file_ext in [".png", ".jpg", ".jpeg"]:
            image = Image.open(file_path)
            text = pytesseract.image_to_string(image)

        # Extract text from PDFs
        elif file_ext == ".pdf":
            with pdfplumber.open(file_path) as pdf:
                for page in pdf.pages:
                    page_text = page.extract_text() or ""
                    text += page_text + "\n"
        
        # Extract text from Word documents
        elif file_ext == ".docx":
            doc = Document(file_path)
            for para in doc.paragraphs:
                text += para.text + "\n"

        else:
            text = "Unsupported file type!"

    except Exception as e:
        text = f"Error extracting text: {str(e)}"
    
    return text
