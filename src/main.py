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
    page_icon="🩺",
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
        if st.button("➕ Create New Analysis Session", use_container_width=True, type="primary"):
            success, session = SessionManager.create_chat_session()
            if success:
                st.session_state.current_session = session
                st.rerun()
            else:
                st.error("Failed to create session")

def show_chat_history():
    success, messages = st.session_state.auth_service.get_session_messages(
        st.session_state.current_session['id']
    )
    
    if success:
        for msg in messages:
            role = msg['role']
            avatar = "👤" if role == 'user' else "🩺"
            
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
    if st.session_state.user:
        # Get name from user data, fallback to email if name is empty
        display_name = st.session_state.user.get('name') or st.session_state.user.get('email', '')
        st.markdown(f"""
            <div style='text-align: right; padding: 1rem; color: #64B5F6; font-size: 1.1em;'>
                👋 Hi, {display_name}
            </div>
        """, unsafe_allow_html=True)

def show_demo_mode_banner():
    is_sqlite = False
    if 'auth_service' in st.session_state:
        is_sqlite = (getattr(st.session_state.auth_service, 'db_mode', 'sqlite') == 'sqlite')
        
    from agents.model_manager import get_groq_api_key
    has_groq = get_groq_api_key() is not None
    
    if is_sqlite and not has_groq:
        st.warning("⚠️ **Running in Local Demo Mode**: Using local SQLite database (no Supabase) and local mock AI responses (no Groq key). Click **⚙️ Admin Panel** in the sidebar to configure settings.")
    elif is_sqlite and has_groq:
        st.info("ℹ️ **Running in Local SQL Database Mode**: Using local SQLite database for accounts/chats and real Groq AI for report analysis.")
    elif not is_sqlite and not has_groq:
        st.warning("⚠️ **Running in Cloud Demo Mode**: Connected to Supabase cloud, but using local mock AI responses (no Groq key). Configure Groq key in secrets.toml or Admin Panel.")

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
        st.title(f"📊 {st.session_state.current_session['title']}")
        
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