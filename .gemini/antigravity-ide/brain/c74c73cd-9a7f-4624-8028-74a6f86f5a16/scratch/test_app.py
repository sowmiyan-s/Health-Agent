import streamlit as st
import sys
import os

# Add workspace root to path
sys.path.append(r"c:\Users\VSB-AIDSPC79\Documents\SOWMIYAN S\Health-Agent")
from src.utils.pdf_generator import generate_pdf_report

st.title("PDF Download Test")

patient_name = "Valued Patient"
age = "Unknown"
gender = "Unknown"
report_text = """# Potential Health Risks:
1. Prediabetes (High Risk)
Evidence: HbA1C = 6.2% (Normal: <5.7%, Prediabetes: 5.7-6.4%), Estimated Average Glucose (eAG) = 131 mg/dL

# Recommendations:
- Consult a physician
- Exercise regularly
"""

pdf_bytes = generate_pdf_report(patient_name, age, gender, report_text)

st.write("PDF size generated:", len(pdf_bytes))

st.download_button(
    label="Download PDF Report",
    data=pdf_bytes,
    file_name="test_download.pdf",
    mime="application/pdf",
    key="test_download_btn"
)
