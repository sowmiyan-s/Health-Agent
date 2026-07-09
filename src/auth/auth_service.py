import streamlit as st
from st_supabase_connection import SupabaseConnection
from datetime import datetime
import time
import re
import uuid
import sqlite3
import os
import logging

logger = logging.getLogger(__name__)

# Import SQLite database operations
from services.db_service import (
    DB_PATH,
    get_config_db,
    create_user,
    authenticate_user,
    get_user_by_id,
    create_chat_session_db,
    get_user_sessions_db,
    save_chat_message_db,
    get_session_messages_db,
    delete_session_db
)

class AuthService:
    def __init__(self):
        # Determine database mode
        self.db_mode = "sqlite"
        
        # Load from config, environment, or Streamlit secrets, ignoring placeholders
        url = get_config_db("SUPABASE_URL")
        key = get_config_db("SUPABASE_KEY")
        
        def clean_val(v):
            if v and isinstance(v, str) and ("your-" in v or v.strip() == ""):
                return None
            return v
            
        url = clean_val(url) or clean_val(os.environ.get("SUPABASE_URL"))
        key = clean_val(key) or clean_val(os.environ.get("SUPABASE_KEY"))
        
        if not url:
            try:
                url = clean_val(st.secrets.get("SUPABASE_URL"))
            except Exception:
                pass
        if not key:
            try:
                key = clean_val(st.secrets.get("SUPABASE_KEY"))
            except Exception:
                pass
                
        if url and key:
            self.db_mode = "supabase"
            
        self.is_mock = (self.db_mode == "sqlite") # Keep compatibility
        
        if self.db_mode == "supabase":
            try:
                self.supabase = st.connection(
                    "supabase",
                    type=SupabaseConnection,
                    ttl=None,
                    url=url,
                    key=key,
                    client_options={
                        "timeout": 30,
                        "retries": 3,
                    }
                )
            except Exception as e:
                st.error(f"Failed to initialize Supabase connection: {str(e)}")
                st.info("Falling back to local SQLite database.")
                self.db_mode = "sqlite"
                self.is_mock = True
                
        # Try to restore session
        self.try_restore_session()
        
        # Validate session on initialization
        if 'auth_token' in st.session_state:
            if not self.validate_session_token():
                self.sign_out()
    
    def try_restore_session(self):
        """Try to restore session from database stored session."""
        if self.db_mode == "sqlite":
            if 'auth_token' in st.session_state and 'user' in st.session_state:
                pass
        else:
            try:
                # Check if Supabase has a stored session
                session = self.supabase.client.auth.get_session()
                if session and session.access_token and 'auth_token' not in st.session_state:
                    # Validate the stored session
                    user = self.supabase.client.auth.get_user()
                    if user and user.user:
                        user_data = self.get_user_data(user.user.id)
                        if user_data:
                            # Restore session state
                            st.session_state.auth_token = session.access_token
                            st.session_state.user = user_data
            except Exception:
                pass

    def validate_email(self, email):
        """Validate email format."""
        pattern = r'^[\w\.-]+@[\w\.-]+\.\w+$'
        return bool(re.match(pattern, email))

    def check_existing_user(self, email):
        """Check if user already exists."""
        if self.db_mode == "sqlite":
            try:
                conn = sqlite3.connect(DB_PATH)
                cursor = conn.cursor()
                cursor.execute("SELECT id FROM users WHERE email = ?", (email,))
                row = cursor.fetchone()
                conn.close()
                return row is not None
            except Exception:
                return False
        else:
            try:
                result = self.supabase.table('users')\
                    .select('id')\
                    .eq('email', email)\
                    .execute()
                return len(result.data) > 0
            except Exception:
                return False

    def sign_up(self, email, password, name):
        if self.db_mode == "sqlite":
            success, user_data = create_user(email, password, name)
            if success:
                st.session_state.auth_token = "sqlite_token_" + user_data['id']
                st.session_state.user = user_data
                try:
                    from auth.session_manager import SessionManager
                    SessionManager._save_to_persistent_storage(user_data, st.session_state.auth_token)
                except Exception:
                    pass
                return True, user_data
            return False, user_data
        else:
            try:
                auth_response = self.supabase.client.auth.sign_up({
                    "email": email,
                    "password": password,
                    "options": {
                        "data": {
                            "name": name
                        }
                    }
                })
                
                if not auth_response.user:
                    return False, "Failed to create user account"
                
                user_data = {
                    'id': auth_response.user.id,
                    'email': email,
                    'name': name,
                    'created_at': datetime.now().isoformat()
                }
                
                # Insert user data into users table (optional fallback, database trigger handles this via SECURITY DEFINER)
                try:
                    self.supabase.table('users').insert(user_data).execute()
                except Exception as insert_err:
                    logger.info(f"Database insert handled by trigger or RLS: {str(insert_err)}")
                
                # Check if session is established automatically (e.g. email confirmation disabled)
                session = getattr(auth_response, 'session', None)
                if session and session.access_token:
                    st.session_state.auth_token = session.access_token
                    st.session_state.user = user_data
                    try:
                        from auth.session_manager import SessionManager
                        SessionManager._save_to_persistent_storage(user_data, session.access_token)
                    except Exception:
                        pass
                    return True, user_data
                
                # If email confirmation is required
                return True, "email_verification_required"
                    
            except Exception as e:
                error_msg = str(e).lower()
                if "duplicate" in error_msg or "already registered" in error_msg:
                    return False, "Email already registered"
                return False, f"Sign up failed: {str(e)}"

    def sign_in(self, email, password):
        try:
            # Clear any existing session data first
            self.sign_out()
            
            if self.db_mode == "sqlite":
                success, response = authenticate_user(email, password)
                if success:
                    st.session_state.auth_token = "sqlite_token_" + response['id']
                    st.session_state.user = response
                    return True, response
                return False, response
            else:
                auth_response = self.supabase.client.auth.sign_in_with_password({
                    "email": email,
                    "password": password
                })
                
                if auth_response and auth_response.user:
                    user_data = self.get_user_data(auth_response.user.id)
                    if not user_data:
                        return False, "User data not found"
                        
                    st.session_state.auth_token = auth_response.session.access_token
                    st.session_state.user = user_data
                    return True, user_data
                    
                return False, "Invalid login response"
        except Exception as e:
            return False, str(e)
    
    def sign_out(self):
        """Sign out and clear all session data."""
        try:
            if self.db_mode == "supabase":
                self.supabase.client.auth.sign_out()
            from auth.session_manager import SessionManager
            SessionManager.clear_session_state()
            return True, None
        except Exception as e:
            return False, str(e)
    
    def get_user(self):
        if self.db_mode == "sqlite":
            if st.session_state.get('user'):
                class UserWrapper:
                    def __init__(self, user):
                        self.user = user
                return UserWrapper(type('User', (), st.session_state.user)())
            return None
        else:
            try:
                return self.supabase.client.auth.get_user()
            except Exception:
                return None

    def create_session(self, user_id, title=None):
        if self.db_mode == "sqlite":
            try:
                current_time = datetime.now()
                default_title = f"{current_time.strftime('%d-%m-%Y')} | {current_time.strftime('%H:%M:%S')}"
                session = create_chat_session_db(user_id, title or default_title)
                return True, session
            except Exception as e:
                return False, str(e)
        else:
            try:
                current_time = datetime.now()
                default_title = f"{current_time.strftime('%d-%m-%Y')} | {current_time.strftime('%H:%M:%S')}"
                
                session_data = {
                    'user_id': user_id,
                    'title': title or default_title,
                    'created_at': current_time.isoformat()
                }
                result = self.supabase.table('chat_sessions').insert(session_data).execute()
                return True, result.data[0] if result.data else None
            except Exception as e:
                return False, str(e)

    def get_user_sessions(self, user_id):
        if self.db_mode == "sqlite":
            try:
                sessions = get_user_sessions_db(user_id)
                return True, sessions
            except Exception as e:
                return False, []
        else:
            try:
                result = self.supabase.table('chat_sessions')\
                    .select('*')\
                    .eq('user_id', user_id)\
                    .order('created_at', desc=True)\
                    .execute()
                return True, result.data
            except Exception as e:
                st.error(f"Error fetching sessions: {str(e)}")
                return False, []

    def save_chat_message(self, session_id, content, role='user'):
        if self.db_mode == "sqlite":
            try:
                msg = save_chat_message_db(session_id, content, role)
                return True, msg
            except Exception as e:
                return False, str(e)
        else:
            try:
                message_data = {
                    'session_id': session_id,
                    'content': content,
                    'role': role,
                    'created_at': datetime.now().isoformat()
                }
                result = self.supabase.table('chat_messages').insert(message_data).execute()
                return True, result.data[0] if result.data else None
            except Exception as e:
                return False, str(e)

    def get_session_messages(self, session_id):
        if self.db_mode == "sqlite":
            try:
                messages = get_session_messages_db(session_id)
                return True, messages
            except Exception as e:
                return False, str(e)
        else:
            try:
                result = self.supabase.table('chat_messages')\
                    .select('*')\
                    .eq('session_id', session_id)\
                    .order('created_at')\
                    .execute()
                return True, result.data
            except Exception as e:
                return False, str(e)

    def delete_session(self, session_id):
        if self.db_mode == "sqlite":
            try:
                delete_session_db(session_id)
                return True, None
            except Exception as e:
                return False, str(e)
        else:
            try:
                self.supabase.table('chat_messages')\
                    .delete()\
                    .eq('session_id', session_id)\
                    .execute()

                self.supabase.table('chat_sessions')\
                    .delete()\
                    .eq('id', session_id)\
                    .execute()

                return True, None
            except Exception as e:
                st.error(f"Failed to delete session: {str(e)}")
                return False, str(e)
    
    def validate_session_token(self):
        """Validate existing session token on startup."""
        if self.db_mode == "sqlite":
            token = st.session_state.get('auth_token')
            if not token or not token.startswith("sqlite_token_"):
                return None
            user_id = token.replace("sqlite_token_", "")
            return self.get_user_data(user_id)
        else:
            try:
                session = self.supabase.client.auth.get_session()
                if not session or not session.access_token:
                    return None
                    
                # Verify token matches stored token
                if session.access_token != st.session_state.get('auth_token'):
                    return None
                    
                user = self.supabase.client.auth.get_user()
                if not user or not user.user:
                    return None
                    
                return self.get_user_data(user.user.id)
            except Exception:
                return None
    
    def get_user_data(self, user_id):
        """Get user data from database."""
        if self.db_mode == "sqlite":
            return get_user_by_id(user_id)
        else:
            try:
                response = self.supabase.table('users')\
                    .select('*')\
                    .eq('id', user_id)\
                    .single()\
                    .execute()
                return response.data if response else None
            except Exception:
                return None
