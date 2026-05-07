import re
import streamlit as st
from config.app_config import MAX_UPLOAD_SIZE_MB


def validate_password(password):
    if len(password) < 8:
        return False, "Password must be at least 8 characters long"
    if not any(c.isupper() for c in password):
        return False, "Password must contain at least one uppercase letter"
    if not any(c.islower() for c in password):
        return False, "Password must contain at least one lowercase letter"
    if not any(c.isdigit() for c in password):
        return False, "Password must contain at least one number"
    return True, None


def validate_email(email):
    pattern = r'^[\w\.-]+@[\w\.-]+\.\w+$'
    return bool(re.match(pattern, email))


def validate_signup_fields(name, email, password, confirm_password):
    if not all([name, email, password, confirm_password]):
        return False, "Please fill in all fields"

    if not validate_email(email):
        return False, "Please enter a valid email address"

    if password != confirm_password:
        return False, "Passwords do not match"

    is_valid, error_msg = validate_password(password)
    if not is_valid:
        return False, error_msg

    return True, None



def validate_pdf_file(file):
    if not file:
        return False, "No file uploaded"

    file_size_mb = file.size / (1024 * 1024)
    if file_size_mb > MAX_UPLOAD_SIZE_MB:
        return False, f"File size ({file_size_mb:.1f}MB) exceeds the {MAX_UPLOAD_SIZE_MB}MB limit"

    if file.type != 'application/pdf':
        return False, "Invalid file type. Please upload a PDF file"

    return True, None


def detect_report_type(text):
    """Detect report type using keyword scoring."""
    text = text.lower()

    report_keywords = {
        "blood": [
            "hemoglobin", "wbc", "rbc", "platelet",
            "cholesterol", "hdl", "ldl"
        ],
        "urine": [
            "urine", "ph", "protein", "ketones",
            "pus cells", "specific gravity"
        ],
        "liver": [
            "alt", "ast", "alp", "bilirubin",
            "sgpt", "sgot", "gamma gt"
        ],
        "thyroid": [
            "tsh", "t3", "t4", "ft3", "ft4"
        ],
        "kidney": [
            "creatinine", "urea", "bun", "egfr",
            "uric acid"
        ],
        "radiology": [
            "mri", "ct scan", "x-ray", "ultrasound",
            "impression", "findings", "lesion", "mass"
        ]
    }

    scores = {
        report: sum(keyword in text for keyword in keywords)
        for report, keywords in report_keywords.items()
    }

    detected = max(scores, key=scores.get)

    return detected if scores[detected] > 0 else "unknown"


def validate_pdf_content(text):
    """Validate extracted PDF content (multi-report + OCR friendly)."""


    if not text or not text.strip():
        return False, "No text could be extracted from the PDF."

    text_clean = text.strip()
    text_lower = text_clean.lower()

    
    if len(text_clean) < 20:
        st.warning("⚠️ Extracted text is very short (OCR may be low quality), but continuing...")
        return True, {"report_type": "unknown"}

   
    report_type = detect_report_type(text_lower)

  
    general_terms = [
        "test", "report", "lab", "patient", "diagnostic"
    ]

    general_matches = sum(term in text_lower for term in general_terms)

  
    if report_type == "unknown" and general_matches < 1:
        st.warning("⚠️ Could not strongly detect medical report type (OCR noise possible).")

    if report_type != "unknown":
        st.success(f"✅ Detected report type: {report_type.upper()}")
    else:
        st.info("ℹ️ Report type unclear — proceeding with general analysis.")

    return True, {"report_type": report_type}