import streamlit as st
from config.prompts import get_specialist_prompt
from utils.pdf_extractor import extract_text_from_pdf
from config.sample_data import SAMPLE_REPORT
from config.app_config import MAX_UPLOAD_SIZE_MB
from utils.validators import detect_report_type


def show_analysis_form():
  
    if (
        "current_session" in st.session_state
        and "report_source" not in st.session_state
    ):
        st.session_state.report_source = "Upload PDF"

    report_source = st.radio(
        "Choose report source",
        ["Upload PDF", "Use Sample PDF"],
        index=0 if st.session_state.get("report_source") == "Upload PDF" else 1,
        horizontal=True,
        key="report_source",
    )

    pdf_contents = get_report_contents(report_source)

    if pdf_contents:
        render_patient_form(pdf_contents)



def get_report_contents(report_source):
    if report_source == "Upload PDF":
        uploaded_file = st.file_uploader(
            f"Upload report PDF (Max {MAX_UPLOAD_SIZE_MB}MB)",
            type=["pdf"],
        )

        if uploaded_file:
            file_size_mb = uploaded_file.size / (1024 * 1024)

            if file_size_mb > MAX_UPLOAD_SIZE_MB:
                st.error(
                    f"File size ({file_size_mb:.1f}MB) exceeds the limit"
                )
                return None

            if uploaded_file.type != "application/pdf":
                st.error("Please upload a valid PDF file.")
                return None

            pdf_contents = extract_text_from_pdf(uploaded_file)

            if not pdf_contents:
                st.error("Failed to extract text from PDF")
                return None

           
            report_type = detect_report_type(pdf_contents)
            st.session_state.report_type = report_type

            st.success(f"Detected Report Type: {report_type.upper()}")

            with st.expander("View Extracted Report"):
                st.text(pdf_contents)

            return pdf_contents

    else:
        st.session_state.report_type = detect_report_type(SAMPLE_REPORT)

        with st.expander("View Sample Report"):
            st.text(SAMPLE_REPORT)

        return SAMPLE_REPORT

    return None



def render_patient_form(pdf_contents):
    with st.form("analysis_form"):
        patient_name = st.text_input("Patient Name")

        col1, col2 = st.columns(2)
        with col1:
            age = st.number_input("Age", min_value=0, max_value=120)
        with col2:
            gender = st.selectbox("Gender", ["Male", "Female", "Other"])

        user_prompt = st.text_area(
            "Custom Instructions (Optional)",
            placeholder="Example: Explain only abnormal values in simple language"
        )

        submitted = st.form_submit_button("Analyze Report")

        if submitted:
            handle_form_submission(
                patient_name,
                age,
                gender,
                pdf_contents,
                user_prompt
            )


def handle_form_submission(patient_name, age, gender, pdf_contents, user_prompt):
    if not all([patient_name, age, gender]):
        st.error("Please fill in all fields")
        return

    from services.ai_service import generate_analysis

   
    with st.spinner("Analyzing report..."):

   
        st.session_state.current_report_text = pdf_contents

        st.session_state.auth_service.save_chat_message(
            st.session_state.current_session["id"],
            f"Analyzing report for patient: {patient_name}",
        )

    
        report_type = st.session_state.get("report_type", "blood")
        final_prompt = get_specialist_prompt(report_type)

    
        if user_prompt:
            final_prompt += f"\n\nUser Instruction:\n{user_prompt}"

        result = generate_analysis(
            {
                "patient_name": patient_name,
                "age": age,
                "gender": gender,
                "report": pdf_contents,
            },
            final_prompt,
        )

        if result["success"]:
            report_metadata = f"__REPORT_TEXT__\n{pdf_contents}\n__END_REPORT_TEXT__"

            st.session_state.auth_service.save_chat_message(
                st.session_state.current_session["id"],
                report_metadata,
                role="system"
            )

            content = result["content"]

            if "model_used" in result:
                content += f"\n\n*Generated using {result['model_used']}*"

            st.session_state.auth_service.save_chat_message(
                st.session_state.current_session["id"],
                content,
                role="assistant"
            )

            st.rerun()

        else:
            st.error(result["error"])
            st.stop()