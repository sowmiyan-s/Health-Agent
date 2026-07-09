import streamlit as st
import re
import plotly.graph_objects as go

def parse_biomarkers(report_text):
    """
    Extract key biomarkers, their values, and reference ranges from report text.
    Returns a dictionary of biomarkers with their parsed values.
    """
    if not report_text:
        return {}
        
    # Clean commas inside numbers to parse e.g. 7,500 -> 7500
    cleaned_text = re.sub(r'(\d),(\d)', r'\1\2', report_text)
    cleaned_text_lower = cleaned_text.lower()
    
    # Target configurations: Regexes, reference range (low/high), units
    patterns = {
        "Hemoglobin": {
            "patterns": [
                r"\bhemoglobin\b\s*(?:[:\-]?\s*|\s)(\d+\.?\d*)", 
                r"\bhb\b\s*(?:[:\-]?\s*|\s)(\d+\.?\d*)",
                r"\bhgb\b\s*(?:[:\-]?\s*|\s)(\d+\.?\d*)"
            ],
            "low": 12.0, "high": 15.5, "unit": "g/dL"
        },
        "White Blood Cells": {
            "patterns": [
                r"\bwhite blood cells?\b\s*(?:[:\-]?\s*|\s)(\d+\.?\d*)", 
                r"\bwbc\b\s*(?:[:\-]?\s*|\s)(\d+\.?\d*)",
                r"\bleukocytes?\b\s*(?:[:\-]?\s*|\s)(\d+\.?\d*)"
            ],
            "low": 4000.0, "high": 11000.0, "unit": "/µL"
        },
        "Red Blood Cells": {
            "patterns": [
                r"\bred blood cells?\b\s*(?:[:\-]?\s*|\s)(\d+\.?\d*)", 
                r"\brbc\b\s*(?:[:\-]?\s*|\s)(\d+\.?\d*)",
                r"\berythrocytes?\b\s*(?:[:\-]?\s*|\s)(\d+\.?\d*)"
            ],
            "low": 4.0, "high": 5.2, "unit": "M/µL"
        },
        "Platelets": {
            "patterns": [
                r"\bplatelets?\b\s*(?:[:\-]?\s*|\s)(\d+\.?\d*)", 
                r"\bplt\b\s*(?:[:\-]?\s*|\s)(\d+\.?\d*)",
                r"\bthrombocytes?\b\s*(?:[:\-]?\s*|\s)(\d+\.?\d*)"
            ],
            "low": 150000.0, "high": 450000.0, "unit": "/µL"
        },
        "Glucose (Fasting)": {
            "patterns": [
                r"\bglucose\s*(?:\(fasting\))?\b\s*(?:[:\-]?\s*|\s)(\d+\.?\d*)", 
                r"\bfasting glucose\b\s*(?:[:\-]?\s*|\s)(\d+\.?\d*)",
                r"\bfasting blood sugar\b\s*(?:[:\-]?\s*|\s)(\d+\.?\d*)",
                r"\bfbs\b\s*(?:[:\-]?\s*|\s)(\d+\.?\d*)"
            ],
            "low": 70.0, "high": 100.0, "unit": "mg/dL"
        },
        "Creatinine": {
            "patterns": [
                r"\bcreatinine\b\s*(?:[:\-]?\s*|\s)(\d+\.?\d*)",
                r"\bcreat\b\s*(?:[:\-]?\s*|\s)(\d+\.?\d*)"
            ],
            "low": 0.6, "high": 1.2, "unit": "mg/dL"
        },
        "Total Cholesterol": {
            "patterns": [
                r"\btotal cholesterol\b\s*(?:[:\-]?\s*|\s)(\d+\.?\d*)", 
                r"\bcholesterol\b\s*(?:[:\-]?\s*|\s)(\d+\.?\d*)",
                r"\bchol\b\s*(?:[:\-]?\s*|\s)(\d+\.?\d*)"
            ],
            "low": 120.0, "high": 200.0, "unit": "mg/dL"
        },
        "HDL Cholesterol": {
            "patterns": [
                r"\bhdl cholesterol\b\s*(?:[:\-]?\s*|\s)(\d+\.?\d*)", 
                r"\bhdl\b\s*(?:[:\-]?\s*|\s)(\d+\.?\d*)",
                r"\bhdl-c\b\s*(?:[:\-]?\s*|\s)(\d+\.?\d*)"
            ],
            "low": 40.0, "high": 60.0, "unit": "mg/dL"
        },
        "LDL Cholesterol": {
            "patterns": [
                r"\bldl cholesterol\b\s*(?:[:\-]?\s*|\s)(\d+\.?\d*)", 
                r"\bldl\b\s*(?:[:\-]?\s*|\s)(\d+\.?\d*)",
                r"\bldl-c\b\s*(?:[:\-]?\s*|\s)(\d+\.?\d*)"
            ],
            "low": 50.0, "high": 100.0, "unit": "mg/dL"
        },
        "ALT (SGPT)": {
            "patterns": [
                r"\balt\b\s*(?:[:\-]?\s*|\s)(\d+\.?\d*)",
                r"\bsgpt\b\s*(?:[:\-]?\s*|\s)(\d+\.?\d*)",
                r"\balanine aminotransferase\b\s*(?:[:\-]?\s*|\s)(\d+\.?\d*)"
            ],
            "low": 7.0, "high": 56.0, "unit": "U/L"
        },
        "AST (SGOT)": {
            "patterns": [
                r"\bast\b\s*(?:[:\-]?\s*|\s)(\d+\.?\d*)",
                r"\bsgot\b\s*(?:[:\-]?\s*|\s)(\d+\.?\d*)",
                r"\baspartate aminotransferase\b\s*(?:[:\-]?\s*|\s)(\d+\.?\d*)"
            ],
            "low": 10.0, "high": 40.0, "unit": "U/L"
        }
    }
    
    biomarkers = {}
    for name, config in patterns.items():
        val = None
        for pattern in config["patterns"]:
            match = re.search(pattern, cleaned_text_lower)
            if match:
                try:
                    val = float(match.group(1))
                    break
                except ValueError:
                    pass
        if val is not None:
            # Determine status
            status = "Normal"
            if val < config["low"]:
                status = "Low"
            elif val > config["high"]:
                status = "High"
                
            biomarkers[name] = {
                "value": val,
                "low": config["low"],
                "high": config["high"],
                "unit": config["unit"],
                "status": status
            }
            
    return biomarkers

def render_gauge_chart(name, data):
    """Draw an interactive Plotly Gauge Indicator chart."""
    val = data["value"]
    low = data["low"]
    high = data["high"]
    unit = data["unit"]
    
    # Formulate safety boundary ranges for gauge display
    gauge_min = low * 0.6
    gauge_max = high * 1.4
    
    fig = go.Figure(go.Indicator(
        mode = "gauge+number",
        value = val,
        domain = {'x': [0, 1], 'y': [0, 1]},
        title = {'text': f"{name} ({unit})", 'font': {'size': 18, 'color': "#F0F3F8"}},
        number = {'font': {'color': "#F0F3F8", 'size': 32}},
        gauge = {
            'axis': {'range': [gauge_min, gauge_max], 'tickwidth': 1, 'tickcolor': "#8A99AD"},
            'bar': {'color': "#4E8CFF", 'thickness': 0.25},
            'bgcolor': "#1A2332",
            'borderwidth': 1,
            'bordercolor': "rgba(255,255,255,0.05)",
            'steps': [
                {'range': [gauge_min, low], 'color': 'rgba(239, 68, 68, 0.15)'},
                {'range': [low, high], 'color': 'rgba(16, 185, 129, 0.15)'},
                {'range': [high, gauge_max], 'color': 'rgba(239, 68, 68, 0.15)'}
            ],
            'threshold': {
                'line': {'color': "#EF4444", 'width': 3},
                'thickness': 0.75,
                'value': val
            }
        }
    ))
    
    fig.update_layout(
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        font={'color': "#F0F3F8", 'family': "Inter"},
        height=220,
        margin=dict(l=20, r=20, t=50, b=20)
    )
    
    return fig

def show_biomarker_dashboard(report_text):
    """Renders the complete visual biomarkers dashboard."""
    biomarkers = parse_biomarkers(report_text)
    
    if not biomarkers:
        # Fallback if no biomarkers could be parsed
        return
        
    st.markdown("---")
    st.markdown("<h3 style='color: #4E8CFF;'>📊 Biomarker Insights Dashboard</h3>", unsafe_allow_html=True)
    st.markdown("<p style='color: #8A99AD; font-size: 0.9em; margin-bottom: 1.5rem;'>Parsed key parameters detected from the medical report upload.</p>", unsafe_allow_html=True)
    
    # 1. Card grid
    names = list(biomarkers.keys())
    # Display cards in rows of 4
    for i in range(0, len(names), 4):
        chunk = names[i:i+4]
        cols = st.columns(4)
        for idx, name in enumerate(chunk):
            data = biomarkers[name]
            val = data["value"]
            unit = data["unit"]
            status = data["status"]
            low = data["low"]
            high = data["high"]
            
            # Select color based on status
            status_color = "#10B981" if status == "Normal" else "#EF4444"
            bg_opacity = "rgba(16, 185, 129, 0.08)" if status == "Normal" else "rgba(239, 68, 68, 0.08)"
            
            # Formatting numeric values cleanly
            formatted_val = f"{val:,.2f}".rstrip('0').rstrip('.') if '.' in str(val) else f"{int(val):,}"
            
            with cols[idx]:
                st.markdown(f"""
                    <div style='
                        background: #141923;
                        border: 1px solid rgba(255, 255, 255, 0.05);
                        border-radius: 12px;
                        padding: 1.2rem 1rem;
                        text-align: center;
                        box-shadow: 0 4px 12px rgba(0,0,0,0.15);
                        height: 100%;
                    '>
                        <div style='color: #8A99AD; font-size: 0.85em; font-weight: 500; min-height: 2.2em; display: flex; align-items: center; justify-content: center;'>{name}</div>
                        <div style='color: #F0F3F8; font-size: 1.7em; font-weight: 700; margin: 0.3rem 0;'>
                            {formatted_val} <span style='font-size: 0.55em; font-weight: 400; color: #8A99AD;'>{unit}</span>
                        </div>
                        <span style='
                            display: inline-block;
                            padding: 0.2rem 0.6rem;
                            border-radius: 20px;
                            font-size: 0.75em;
                            font-weight: 600;
                            color: {status_color};
                            background: {bg_opacity};
                            border: 1px solid {status_color}22;
                        '>
                            {status}
                        </span>
                        <div style='margin-top: 0.5rem; color: #64748B; font-size: 0.7em;'>
                            Ref: {low} - {high}
                        </div>
                    </div>
                """, unsafe_allow_html=True)
                
    # 2. Interactive selector for Plotly Gauge
    st.markdown("<div style='margin-top: 1.5rem;'></div>", unsafe_allow_html=True)
    col_sel, col_gauge = st.columns([1, 2])
    
    with col_sel:
        st.markdown("<p style='font-weight: 500; color: #F0F3F8; margin-bottom: 0.5rem;'>Select biomarker to visualize range details:</p>", unsafe_allow_html=True)
        selected_biomarker = st.selectbox(
            "Select Biomarker",
            options=names,
            label_visibility="collapsed"
        )
        
        # Display clinical summary
        data = biomarkers[selected_biomarker]
        status_text = f"✅ The patient's {selected_biomarker} is in the normal reference range." if data["status"] == "Normal" else f"⚠️ The patient's {selected_biomarker} is {data['status'].lower()} compared to the reference range."
        
        st.markdown(f"""
            <div style='
                background: #141923;
                border: 1px solid rgba(255, 255, 255, 0.05);
                border-radius: 8px;
                padding: 1rem;
                margin-top: 1rem;
                border-left: 4px solid {"#10B981" if data["status"] == "Normal" else "#EF4444"};
            '>
                <p style='margin: 0; font-size: 0.9em; line-height: 1.5; color: #E2E8F0;'>{status_text}</p>
            </div>
        """, unsafe_allow_html=True)
        
    with col_gauge:
        fig = render_gauge_chart(selected_biomarker, biomarkers[selected_biomarker])
        st.plotly_chart(fig, use_container_width=True)
