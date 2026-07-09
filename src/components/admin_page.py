import streamlit as st
from services.db_service import get_config_db, set_config_db
from datetime import datetime

def show_admin_page():
    st.title("Admin Configuration Panel")
    st.write("Configure settings and manage active users or diagnostic sessions.")

    # Initialize admin session states
    if "admin_authenticated" not in st.session_state:
        st.session_state.admin_authenticated = False

    if not st.session_state.admin_authenticated:
        with st.form("admin_login"):
            admin_pwd = st.text_input("Enter Admin Password", type="password")
            submit = st.form_submit_button("Verify", use_container_width=True, type="primary")
            if submit:
                # Retrieve from environment or secrets, fallback to fry65 if not set
                import os
                secret_password = os.environ.get("ADMIN_PASSWORD") or st.secrets.get("ADMIN_PASSWORD", "fry65")
                if admin_pwd == secret_password:
                    st.session_state.admin_authenticated = True
                    st.success("Authenticated successfully!")
                    st.rerun()
                else:
                    st.error("Invalid Password. Access Denied.")
    else:
        # Create Multi-Tab Admin Suite
        tab_config, tab_users = st.tabs(["System Configuration", "User & Report Management"])

        with tab_config:
            import os
            
            def get_active_config(key_name, placeholder_term):
                val = get_config_db(key_name, "")
                if val and placeholder_term not in val and val.strip() != "":
                    return val.strip()
                val = os.environ.get(key_name)
                if val and placeholder_term not in val and val.strip() != "":
                    return val.strip()
                try:
                    val = st.secrets.get(key_name)
                    if val and placeholder_term not in val and val.strip() != "":
                        return val.strip()
                except Exception:
                    pass
                return ""
                
            current_groq = get_active_config("GROQ_API_KEY", "your-groq")
            current_mistral = get_active_config("MISTRAL_API_KEY", "your-mistral")
            current_supabase_url = get_active_config("SUPABASE_URL", "your-supabase")
            current_supabase_key = get_active_config("SUPABASE_KEY", "your-supabase")

            if current_supabase_url:
                st.success(f"Active Supabase URL: `{current_supabase_url}` (Loaded from secrets or database)")
            else:
                st.warning("No active Supabase URL configured (Running on local SQLite)")
                
            st.info("Pro Tip: Leave Supabase credentials empty to run exclusively on the local SQLite database.")

            with st.form("config_form"):
                groq_key = st.text_input(
                    "Groq API Key", 
                    value=current_groq, 
                    type="password",
                    help="API key from Groq console used for AI analysis cascades."
                )
                mistral_key = st.text_input(
                    "Mistral API Key", 
                    value=current_mistral, 
                    type="password",
                    help="API key from Mistral AI console used for fallback vision OCR and report analysis."
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
                    set_config_db("MISTRAL_API_KEY", mistral_key)
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

        with tab_users:
            auth_service = st.session_state.auth_service
            success, users = auth_service.get_all_users()

            if not success:
                st.error(f"Failed to fetch users: {users}")
            elif not users:
                st.warning("No registered user accounts found.")
            else:
                st.subheader("Registered User Accounts")
                
                # Show all users in a clean dataframe
                user_list = []
                for u in users:
                    # Clean date strings
                    created = u.get("created_at", "N/A")
                    if isinstance(created, str) and "T" in created:
                        created = created.split("T")[0]
                    user_list.append({
                        "Name": u.get("name") or "New User",
                        "Email": u.get("email"),
                        "Registered Date": created,
                        "User ID": u.get("id")
                    })
                st.dataframe(user_list, use_container_width=True)

                st.markdown("---")
                st.subheader("User Session Inspector & Administration")
                
                # Selector for management
                selected_user = st.selectbox(
                    "Select user to manage",
                    users,
                    format_func=lambda u: f"{u.get('name') or 'New User'} ({u.get('email')})"
                )

                if selected_user:
                    user_id = selected_user["id"]
                    
                    col_info, col_actions = st.columns([3, 1])
                    with col_info:
                        st.markdown(f"**Selected ID:** `{user_id}`")
                        st.markdown(f"**Email Address:** `{selected_user.get('email')}`")
                        st.markdown(f"**Name:** {selected_user.get('name') or 'New User'}")
                    
                    with col_actions:
                        # User Account Deletion Trigger
                        if st.button("Delete User Account", type="primary", use_container_width=True, key=f"del_user_{user_id}"):
                            st.session_state.confirm_delete_user = user_id
                            st.rerun()
                    
                    # Confirm user deletion dialog
                    if st.session_state.get("confirm_delete_user") == user_id:
                        st.warning(f"Are you sure you want to completely delete {selected_user.get('email')} and all their data?")
                        left, right = st.columns(2)
                        with left:
                            if st.button("Yes, Delete Completely", type="primary", use_container_width=True, key=f"c_del_user_{user_id}"):
                                del_success, del_err = auth_service.delete_user(user_id)
                                if del_success:
                                    st.session_state.confirm_delete_user = None
                                    st.success("User deleted successfully!")
                                    st.rerun()
                                else:
                                    st.error(f"Failed to delete user: {del_err}")
                        with right:
                            if st.button("Cancel", use_container_width=True, key=f"c_cancel_del_{user_id}"):
                                st.session_state.confirm_delete_user = None
                                st.rerun()

                    st.markdown("#### User Diagnostic Sessions")
                    sess_success, sessions = auth_service.get_user_sessions_by_admin(user_id)

                    if not sess_success:
                        st.error(f"Failed to load sessions: {sessions}")
                    elif not sessions:
                        st.info("No active chat sessions found for this user account.")
                    else:
                        for sess in sessions:
                            sess_id = sess["id"]
                            
                            sess_title_col, sess_del_col = st.columns([5, 1.5])
                            with sess_title_col:
                                st.markdown(f"**Session:** {sess['title']}")
                            with sess_del_col:
                                # Import SessionManager dynamically to prevent circular imports
                                from auth.session_manager import SessionManager
                                if st.button("Delete Session", key=f"adm_del_sess_{sess_id}", use_container_width=True):
                                    del_sess_ok, del_sess_err = SessionManager.delete_session(sess_id)
                                    if del_sess_ok:
                                        st.success("Session deleted!")
                                        st.rerun()
                                    else:
                                        st.error(f"Delete failed: {del_sess_err}")
                            
                            # Expand conversation logs
                            with st.expander("View Conversation Logs"):
                                msg_success, messages = auth_service.get_session_messages(sess_id)
                                if msg_success and messages:
                                    for msg in messages:
                                        role = msg["role"].upper()
                                        st.markdown(f"**{role}:**")
                                        if role == "USER" and "**Report Content**:" in msg["content"]:
                                            # format nicely
                                            parts = msg["content"].split("**Report Content**:\n")
                                            st.markdown(parts[0])
                                            with st.expander("View Extracted Report Contents"):
                                                st.text(parts[1] if len(parts) > 1 else "")
                                        else:
                                            st.markdown(msg["content"])
                                        st.markdown("---")
                                else:
                                    st.text("No messages in this session.")

    # Back button to close admin panel
    if st.button("Back to Main Screen", use_container_width=True):
        st.session_state.show_admin = False
        st.rerun()
