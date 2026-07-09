import streamlit as st
from services.ai_service import generate_analysis
from config.prompts import SPECIALIST_PROMPTS
from utils.pdf_extractor import extract_text_from_pdf
from utils.image_extractor import extract_text_from_image
from utils.validators import validate_uploaded_file, validate_report_content
from config.sample_data import SAMPLE_REPORT
from config.app_config import MAX_UPLOAD_SIZE_MB

def show_analysis_form():
    # Initialize report source in session state for new sessions
    if 'current_session' in st.session_state and 'report_source' not in st.session_state:
        st.session_state.report_source = "Upload PDF"
    
    report_source = st.radio(
        "Choose report source",
        ["Upload PDF", "Use Sample PDF"],
        index=0 if st.session_state.get('report_source') == "Upload PDF" else 1,
        horizontal=True,
        key='report_source'
    )

    pdf_contents = get_report_contents(report_source)
            
    if pdf_contents:  # Only show form if we have report content
        render_patient_form(pdf_contents)

def get_report_contents(report_source):
    if report_source == "Upload PDF":
        uploaded_file = st.file_uploader(
            f"Upload blood report (Max {MAX_UPLOAD_SIZE_MB}MB)", 
            type=['pdf', 'png', 'jpg', 'jpeg'],
            help=f"Maximum file size: {MAX_UPLOAD_SIZE_MB}MB. Supports PDF and Image files (PNG, JPG, JPEG) containing medical reports."
        )
        if uploaded_file:
            # Validate uploaded file format and size
            is_valid, error = validate_uploaded_file(uploaded_file)
            if not is_valid:
                st.error(error)
                return None
                
            # Dispatch to correct text extractor based on file mime type
            if uploaded_file.type == 'application/pdf':
                extracted_text = extract_text_from_pdf(uploaded_file)
            else:
                extracted_text = extract_text_from_image(uploaded_file)
                
            if isinstance(extracted_text, str) and (
                extracted_text.startswith(("File size exceeds", "Invalid file type", "Error validating", "Error extracting")) or
                extracted_text.startswith("The uploaded file") or
                "error" in extracted_text.lower()
            ):
                st.error(extracted_text)
                return None
                
            # Perform report validation on extracted text content
            is_valid_content, content_error = validate_report_content(extracted_text)
            if not is_valid_content:
                st.error(content_error)
                return None
                
            with st.expander("View Extracted Report"):
                st.text(extracted_text)
            return extracted_text
    else:
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
        
        if st.form_submit_button("Analyze Report"):
            handle_form_submission(patient_name, age, gender, pdf_contents)

def handle_form_submission(patient_name, age, gender, pdf_contents):
    if not all([patient_name, age, gender]):
        st.error("Please fill in all fields")
        return

    # Check rate limit first, outside of spinner
    can_analyze, error_msg = generate_analysis(None, None, check_only=True)
    if not can_analyze:
        st.error(error_msg)
        st.stop()
        return

    with st.spinner("Analyzing report..."):
        # Save user message with report details for extraction and display
        report_summary = (
            f"**Patient**: {patient_name} (Age: {age}, Gender: {gender})\n\n"
            f"**Report Content**:\n{pdf_contents}"
        )
        st.session_state.auth_service.save_chat_message(
            st.session_state.current_session['id'],
            report_summary,
            role='user'
        )
        
        # Generate analysis
        result = generate_analysis({
            "patient_name": patient_name,
            "age": age,
            "gender": gender,
            "report": pdf_contents
        }, SPECIALIST_PROMPTS["comprehensive_analyst"])
        
        if result["success"]:
            # Add model used information if available
            content = result["content"]
            if "model_used" in result:
                model_info = f"\n\n*Analysis generated using {result['model_used']}*"
                content += model_info
                
            st.session_state.auth_service.save_chat_message(
                st.session_state.current_session['id'],
                content,
                role='assistant'
            )
            st.rerun()
        else:
            st.error(result["error"])
            st.stop()
