import streamlit as st
from auth.session_manager import SessionManager
from components.auth_pages import show_login_page
from components.sidebar import show_sidebar
from components.analysis_form import show_analysis_form
from components.footer import show_footer
from config.app_config import APP_NAME, APP_TAGLINE, APP_DESCRIPTION, APP_ICON
from services.db_service import init_db
from components.admin_page import show_admin_page

# Must be the first Streamlit command
st.set_page_config(
    page_title="HIA - Health Insights Agent",
    page_icon=None,
    layout="wide"
)

# Initialize session state
SessionManager.init_session()

# Inject Custom CSS for Premium UI/UX
st.markdown("""
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');
        
        /* Apply Font */
        html, body, [data-testid="stAppViewContainer"], .stApp {
            font-family: 'Inter', sans-serif !important;
        }
        
        /* Hide form submission helper text */
        div[data-testid="InputInstructions"] > span:nth-child(1) {
            visibility: hidden;
        }
        
        /* Modernized Sidebar */
        section[data-testid="stSidebar"] {
            background-color: #0A0D14 !important;
            border-right: 1px solid rgba(255, 255, 255, 0.05);
        }
        
        /* Clean card borders and backgrounds */
        div[data-testid="stForm"] {
            background-color: #141923 !important;
            border: 1px solid rgba(255, 255, 255, 0.05) !important;
            border-radius: 12px !important;
            box-shadow: 0 4px 20px rgba(0, 0, 0, 0.15) !important;
            padding: 2rem !important;
        }
        
        /* Button Styling */
        .stButton>button {
            border-radius: 8px !important;
            font-weight: 500 !important;
            transition: all 0.2s ease !important;
        }
        
        .stButton>button:hover {
            transform: translateY(-1px);
            box-shadow: 0 4px 12px rgba(78, 140, 255, 0.2);
        }
        
        /* Expander Styling */
        div[data-testid="stExpander"] {
            background-color: #141923 !important;
            border: 1px solid rgba(255, 255, 255, 0.05) !important;
            border-radius: 8px !important;
        }
        
        /* Welcome header gradient */
        .welcome-title {
            background: linear-gradient(90deg, #4E8CFF 0%, #10B981 100%);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            font-weight: 800;
            font-size: 3rem;
            margin-bottom: 0.5rem;
        }
        
        /* Chat Input Area Adjustments */
        div[data-testid="stChatMessage"] {
            background-color: #141923 !important;
            border: 1px solid rgba(255, 255, 255, 0.03) !important;
            border-radius: 10px !important;
            padding: 1rem !important;
            margin-bottom: 0.8rem !important;
        }
        
        /* Info banner styled custom card */
        .custom-banner {
            padding: 1rem;
            border-radius: 10px;
            background: rgba(78, 140, 255, 0.05);
            border-left: 4px solid #4E8CFF;
            margin-bottom: 1rem;
        }
    </style>
""", unsafe_allow_html=True)

def show_welcome_screen():
    st.markdown(
        f"""
        <div style='text-align: center; padding: 50px;'>
            <h1 class='welcome-title'>{APP_ICON} {APP_NAME}</h1>
            <h3>{APP_DESCRIPTION}</h3>
            <p style='font-size: 1.2em; color: #8A99AD;'>{APP_TAGLINE}</p>
            <p style='color: #64748B;'>Start by creating a new analysis session</p>
        </div>
        """,
        unsafe_allow_html=True
    )
    
    col1, col2, col3 = st.columns([2, 3, 2])
    with col2:
        welcome_sess_name = st.text_input("Analysis Session Name", placeholder="e.g. My Blood Report", label_visibility="collapsed", key="welcome_new_sess_title")
        if st.button("Create New Analysis Session", use_container_width=True, type="primary"):
            st.session_state.show_admin = False
            if st.session_state.user and 'id' in st.session_state.user:
                title = welcome_sess_name.strip() if welcome_sess_name.strip() else "New Analysis"
                success, session = st.session_state.auth_service.create_session(
                    st.session_state.user['id'],
                    title=title
                )
                if success:
                    st.session_state.current_session = session
                    st.rerun()
                else:
                    st.error("Failed to create session")
            else:
                st.error("Please log in again")
                SessionManager.logout()
                st.rerun()

def show_chat_history():
    import re
    success, messages = st.session_state.auth_service.get_session_messages(
        st.session_state.current_session['id']
    )
    
    if success:
        # Find the last assistant message index
        last_assistant_idx = -1
        for idx, msg in enumerate(messages):
            if msg['role'] == 'assistant':
                last_assistant_idx = idx
                
        for idx, msg in enumerate(messages):
            role = msg['role']
            avatar = None
            
            if role == 'user' and "**Report Content**:" in msg['content']:
                # Show only patient summary, and put raw report inside an expander
                parts = msg['content'].split("**Report Content**:\n")
                summary = parts[0]
                raw_report = parts[1] if len(parts) > 1 else ""
                
                with st.chat_message(role, avatar=avatar):
                    st.markdown(summary)
                    if raw_report:
                        with st.expander("View Raw Extracted Report"):
                            st.text(raw_report)
            else:
                with st.chat_message(role, avatar=avatar):
                    st.markdown(msg['content'])
                    
                    # If this is the last assistant message (the report), show the download button
                    if idx == last_assistant_idx:
                        patient_name = "Valued Patient"
                        age = "Unknown"
                        gender = "Unknown"
                        
                        # Find patient details from user message
                        for u_msg in messages:
                            if u_msg['role'] == 'user' and "**Patient**:" in u_msg['content']:
                                match = re.search(r"Patient\*\*:\s*(.*?)\s*\(Age:\s*(.*?),\s*Gender:\s*(.*?)\)", u_msg['content'])
                                if match:
                                    patient_name = match.group(1).strip()
                                    age = match.group(2).strip()
                                    gender = match.group(3).strip()
                                    break
                                    
                        try:
                            from utils.pdf_generator import generate_pdf_report
                            pdf_bytes = generate_pdf_report(patient_name, age, gender, msg['content'])
                            st.markdown("<div style='margin-top: 0.8rem;'></div>", unsafe_allow_html=True)
                            st.download_button(
                                label="Export Diagnostic Report as PDF",
                                data=pdf_bytes,
                                file_name=f"HIA_Analysis_{patient_name.replace(' ', '_')}.pdf",
                                mime="application/pdf",
                                key=f"dl_pdf_{idx}"
                            )
                        except Exception as e:
                            st.error(f"Failed to generate PDF download: {str(e)}")

def get_report_content_from_history():
    if not st.session_state.get('current_session'):
        return None
    success, messages = st.session_state.auth_service.get_session_messages(
        st.session_state.current_session['id']
    )
    if success:
        for msg in messages:
            if msg['role'] == 'user' and "**Report Content**:" in msg['content']:
                parts = msg['content'].split("**Report Content**:\n")
                if len(parts) > 1:
                    return parts[1]
    return None

def show_user_greeting():
    pass

def show_demo_mode_banner():
    is_sqlite = True
    if 'auth_service' in st.session_state:
        is_sqlite = (getattr(st.session_state.auth_service, 'db_mode', 'sqlite') == 'sqlite')
        
    from agents.model_manager import get_groq_api_key, get_mistral_api_key
    has_ai_key = (get_groq_api_key() is not None) or (get_mistral_api_key() is not None)
    
    # If fully configured, show nothing
    if not is_sqlite and has_ai_key:
        return
        
    warnings = []
    if is_sqlite:
        warnings.append("Supabase URL not set (running on local SQLite)")
    if not has_ai_key:
        warnings.append("AI API Key not set (using mock simulated responses)")
        
    if warnings:
        st.warning("⚠️ **Configuration Notice**: " + " | ".join(warnings))

def main():
    # Initialize SQLite database schema
    init_db()
    
    SessionManager.init_session()
    
    # Show demo mode banner if applicable
    show_demo_mode_banner()

    # If admin page is requested, show it directly
    if st.session_state.get('show_admin'):
        show_admin_page()
        show_footer()
        return

    if not SessionManager.is_authenticated():
        show_login_page()
        show_footer()
        return

    # Show user greeting at the top
    show_user_greeting()
    
    # Show sidebar
    show_sidebar()

    # Main chat area
    if st.session_state.get('current_session'):
        current_sess = st.session_state.current_session
        
        # Session title editing interface
        if 'editing_sess_id' not in st.session_state:
            st.session_state.editing_sess_id = None
            
        if st.session_state.editing_sess_id == current_sess['id']:
            col_inp, col_btn1, col_btn2 = st.columns([6, 1, 1])
            with col_inp:
                new_title = st.text_input("Rename Analysis Session", value=current_sess['title'], label_visibility="collapsed", key="rename_sess_input")
            with col_btn1:
                if st.button("Save", type="primary", use_container_width=True, key="save_sess_title_btn"):
                    if new_title.strip():
                        success, err = SessionManager.update_session_title(current_sess['id'], new_title.strip())
                        if success:
                            st.session_state.current_session['title'] = new_title.strip()
                            st.session_state.editing_sess_id = None
                            st.rerun()
                        else:
                            st.error(f"Error: {err}")
            with col_btn2:
                if st.button("Cancel", use_container_width=True, key="cancel_sess_title_btn"):
                    st.session_state.editing_sess_id = None
                    st.rerun()
        else:
            col_title, col_edit = st.columns([8, 2])
            with col_title:
                st.title(current_sess['title'])
            with col_edit:
                st.markdown("<div style='margin-top: 1.2rem;'></div>", unsafe_allow_html=True)
                if st.button("Rename Analysis 📝", use_container_width=True, key="rename_sess_trigger_btn"):
                    st.session_state.editing_sess_id = current_sess['id']
                    st.rerun()
        
        # Extract and show biomarker dashboard if report is present in session history
        report_content = get_report_content_from_history()
        if report_content:
            from components.dashboard import show_biomarker_dashboard
            show_biomarker_dashboard(report_content)
            
        show_chat_history()
        show_analysis_form()
    else:
        show_welcome_screen()

if __name__ == "__main__":
    main()