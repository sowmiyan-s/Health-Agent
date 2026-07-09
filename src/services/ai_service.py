from agents.analysis_agent import AnalysisAgent, get_default_user_state
import streamlit as st

# Shared instance of AnalysisAgent
_analysis_agent = AnalysisAgent()

def check_rate_limit(user_state=None):
    """Check if the user has reached their daily analysis limit."""
    if user_state is None:
        user_state = st.session_state.get('user_state') or get_default_user_state()
    return _analysis_agent.check_rate_limit(user_state)

def generate_analysis(data, system_prompt, user_state=None, check_only=False):
    """Generate medical report analysis if within rate limits."""
    if user_state is None:
        user_state = st.session_state.get('user_state') or get_default_user_state()
        
    if check_only:
        return _analysis_agent.check_rate_limit(user_state)
    
    return _analysis_agent.analyze_report(
        data=data,
        system_prompt=system_prompt,
        user_state=user_state,
        check_only=False
    )