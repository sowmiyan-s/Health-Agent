import streamlit as st
from services.db_service import get_config_db, set_config_db

def show_admin_page():
    st.title("⚙️ Admin Configuration Panel")
    st.write("Configure API keys and connections for the Health Insights Agent.")

    # Initialize admin session states
    if "admin_authenticated" not in st.session_state:
        st.session_state.admin_authenticated = False

    if not st.session_state.admin_authenticated:
        with st.form("admin_login"):
            admin_pwd = st.text_input("Enter Admin Password", type="password")
            submit = st.form_submit_button("Verify", use_container_width=True, type="primary")
            if submit:
                if admin_pwd == "fry65":
                    st.session_state.admin_authenticated = True
                    st.success("Authenticated successfully!")
                    st.rerun()
                else:
                    st.error("Invalid Password. Access Denied.")
    else:
        # Show configuration form
        current_groq = get_config_db("GROQ_API_KEY", "")
        current_supabase_url = get_config_db("SUPABASE_URL", "")
        current_supabase_key = get_config_db("SUPABASE_KEY", "")

        st.info("💡 Pro Tip: Leave Supabase credentials empty to run exclusively on the local SQLite database.")

        with st.form("config_form"):
            groq_key = st.text_input(
                "Groq API Key", 
                value=current_groq, 
                type="password",
                help="API key from Groq console used for AI analysis cascades."
            )
            supabase_url = st.text_input(
                "Supabase URL (Optional)", 
                value=current_supabase_url,
                help="URL of your Supabase project."
            )
            supabase_key = st.text_input(
                "Supabase Anon Key (Optional)", 
                value=current_supabase_key, 
                type="password",
                help="Anon/public key for your Supabase project."
            )

            col1, col2 = st.columns(2)
            with col1:
                save_btn = st.form_submit_button("Save Settings", use_container_width=True, type="primary")
            with col2:
                logout_admin = st.form_submit_button("Logout Admin Panel", use_container_width=True)

            if save_btn:
                set_config_db("GROQ_API_KEY", groq_key)
                set_config_db("SUPABASE_URL", supabase_url)
                set_config_db("SUPABASE_KEY", supabase_key)
                
                # Re-initialize AuthService & ModelManager in session state
                if 'auth_service' in st.session_state:
                    del st.session_state.auth_service
                if 'analysis_agent' in st.session_state:
                    del st.session_state.analysis_agent
                
                st.success("Configuration saved! Real-time settings updated.")
                st.rerun()

            if logout_admin:
                st.session_state.admin_authenticated = False
                st.rerun()

    # Back button to close admin panel
    if st.button("⬅️ Back to Main Screen", use_container_width=True):
        st.session_state.show_admin = False
        st.rerun()
