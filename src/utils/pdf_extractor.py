import io
import pdfplumber
import streamlit as st
import pytesseract
from pdf2image import convert_from_bytes

from config.app_config import MAX_PDF_PAGES
from utils.validators import validate_pdf_file, validate_pdf_content


pytesseract.pytesseract.tesseract_cmd = r"C:\Users\swast\Desktop\medicalreportanalyzer\src\Tesseract-OCR\tesseract.exe"

POPPLER_PATH = r"C:\Users\swast\Desktop\poppler-25.12.0\Library\bin"


def clean_medical_text(text):
    """Remove irrelevant lines like hospital, doctor, etc."""
    
    lines = text.split("\n")
    cleaned_lines = []

    ignore_keywords = [
        "diagnostics", "hospital", "clinic", "road", "address",
        "email", "phone", "dr.", "doctor", "md", "signature",
        "regd", "lab id", "received", "reported"
    ]

    for line in lines:
        line_lower = line.lower()

        if any(keyword in line_lower for keyword in ignore_keywords):
            continue

        if len(line.strip()) < 3:
            continue

        cleaned_lines.append(line.strip())

    return "\n".join(cleaned_lines)



def extract_text_from_pdf(pdf_file):
    """Extract and validate text from PDF (supports scanned PDFs via OCR)."""
    try:
       
        is_valid, error = validate_pdf_file(pdf_file)
        if not is_valid:
            return error

       
        pdf_file.seek(0)
        pdf_bytes = pdf_file.read()

        text = ""

       
        with pdfplumber.open(io.BytesIO(pdf_bytes)) as pdf:
            if len(pdf.pages) > MAX_PDF_PAGES:
                return f"PDF exceeds maximum page limit of {MAX_PDF_PAGES}"

            for page in pdf.pages:
                extracted = page.extract_text()
                if extracted:
                    text += extracted + "\n"

        if not text.strip():
            st.warning("⚠️ Using OCR (scanned PDF detected)...")

            images = convert_from_bytes(
                pdf_bytes,
                poppler_path=POPPLER_PATH
            )

            st.write(f"Images extracted: {len(images)}")

            for img in images:
                ocr_text = pytesseract.image_to_string(
                    img,
                    config="--oem 3 --psm 6" 
                )

                st.write("OCR sample:", ocr_text[:200])  
                text += ocr_text + "\n"

       
        text = clean_medical_text(text)

        is_valid, error = validate_pdf_content(text)
        if not is_valid:
            return error

        return text

    except Exception as e:
        return f"Error extracting text from PDF: {str(e)}"