from datetime import datetime, timedelta
from agents.model_manager import ModelManager

def get_default_user_state():
    """Returns a fresh state dictionary for tracking user analysis limits and history."""
    return {
        "analysis_count": 0,
        "last_analysis": datetime.now(),
        "analysis_limit": 15,
        "models_used": {},
        "knowledge_base": {}
    }

class AnalysisAgent:
    """
    Agent responsible for managing report analysis, rate limiting,
    and implementing in-context learning from previous analyses.
    Stateless with respect to Streamlit session state, allowing multi-user backend execution.
    """
    
    def __init__(self):
        self.model_manager = ModelManager()
            
    def check_rate_limit(self, user_state):
        """Check if user has reached their analysis limit based on their state."""
        last_analysis = user_state.get('last_analysis')
        if not last_analysis:
            last_analysis = datetime.now()
            user_state['last_analysis'] = last_analysis
            
        time_until_reset = timedelta(days=1) - (datetime.now() - last_analysis)
        hours, remainder = divmod(time_until_reset.seconds, 3600)
        minutes, _ = divmod(remainder, 60)
        
        # Reset counter after 24 hours
        if time_until_reset.days < 0:
            user_state['analysis_count'] = 0
            user_state['last_analysis'] = datetime.now()
            return True, None
        
        # Check if limit reached
        limit = user_state.get('analysis_limit', 15)
        count = user_state.get('analysis_count', 0)
        if count >= limit:
            error_msg = f"Daily limit reached. Reset in {hours}h {minutes}m"
            return False, error_msg
        return True, None

    def analyze_report(self, data, system_prompt, user_state, check_only=False, chat_history=None):
        """
        Analyze report data using in-context learning from previous analyses.
        
        Args:
            data: Report data to analyze
            system_prompt: Base system prompt
            user_state: State dictionary for the current user
            check_only: If True, only check rate limit without generating analysis
            chat_history: Previous messages in the current session (optional)
        """
        can_analyze, error_msg = self.check_rate_limit(user_state)
        if not can_analyze:
            return {"success": False, "error": error_msg}
        
        if check_only:
            return can_analyze, error_msg
        
        # Process data before sending to model
        processed_data = self._preprocess_data(data)
        
        # Enhance prompt with in-context learning
        enhanced_prompt = self._build_enhanced_prompt(system_prompt, processed_data, user_state, chat_history) if chat_history else system_prompt
        
        # Generate analysis using model manager
        result = self.model_manager.generate_analysis(processed_data, enhanced_prompt)
        
        if result["success"]:
            # Update analytics and learning systems
            self._update_analytics(result, user_state)
            self._update_knowledge_base(processed_data, result["content"], user_state)
        
        return result
    
    def _update_analytics(self, result, user_state):
        """Update analytics in user_state after successful analysis."""
        user_state['analysis_count'] = user_state.get('analysis_count', 0) + 1
        user_state['last_analysis'] = datetime.now()
        
        # Track which models are being used
        model_used = result.get("model_used", "unknown")
        models_used = user_state.setdefault('models_used', {})
        models_used[model_used] = models_used.get(model_used, 0) + 1
    
    def _update_knowledge_base(self, data, analysis, user_state):
        """
        Update knowledge base in user_state with new analysis results for in-context learning.
        Maps key health indicators to analysis patterns.
        """
        if not isinstance(data, dict) or 'report' not in data:
            return
            
        # Extract key health indicators and map them to analysis outcomes
        report_text = data['report'].lower()
        patient_profile = f"{data.get('age', 'unknown')}-{data.get('gender', 'unknown')}"
        
        # Look for key health indicators in the report
        key_indicators = [
            "hemoglobin", "glucose", "cholesterol", "triglycerides", 
            "hdl", "ldl", "wbc", "rbc", "platelet", "creatinine"
        ]
        
        knowledge_base = user_state.setdefault('knowledge_base', {})
        
        # Store snippets of analysis associated with key health indicators
        for indicator in key_indicators:
            if indicator in report_text:
                # Find any mentions of this indicator in the analysis
                if indicator in analysis.lower():
                    # Store this learning in knowledge base
                    profiles = knowledge_base.setdefault(indicator, {})
                    insights = profiles.setdefault(patient_profile, [])
                    
                    # Extract the relevant section from analysis (simple approach)
                    lines = analysis.split('\n')
                    relevant_lines = [l for l in lines if indicator in l.lower()]
                    if relevant_lines:
                        # Limit knowledge base size to prevent overflow
                        if len(insights) >= 3:
                            insights.pop(0)
                        insights.append(relevant_lines[0])
    
    def _build_enhanced_prompt(self, system_prompt, data, user_state, chat_history):
        """
        Build an enhanced prompt using in-context learning from:
        1. Knowledge base of previous analyses
        2. Current session chat history
        """
        enhanced_prompt = system_prompt
        
        # Add in-context learning from knowledge base
        if isinstance(data, dict) and 'report' in data:
            kb_context = self._get_knowledge_base_context(data, user_state)
            if kb_context:
                enhanced_prompt += "\n\n## Relevant Learning From Previous Analyses\n" + kb_context
        
        # Add session context from chat history
        if chat_history:
            session_context = self._get_session_context(chat_history)
            if session_context:
                enhanced_prompt += "\n\n## Current Session History\n" + session_context
        
        return enhanced_prompt
    
    def _get_knowledge_base_context(self, data, user_state):
        """Extract relevant context from knowledge base in user_state."""
        knowledge_base = user_state.get('knowledge_base', {})
        if not knowledge_base:
            return ""
            
        report_text = data.get('report', '').lower()
        patient_profile = f"{data.get('age', 'unknown')}-{data.get('gender', 'unknown')}"
        
        context_items = []
        
        # Find relevant knowledge from previous analyses
        for indicator, profiles in knowledge_base.items():
            if indicator in report_text:
                # Get insights from similar patient profiles first
                if patient_profile in profiles:
                    for insight in profiles[patient_profile]:
                        context_items.append(f"- {indicator} (similar patient profile): {insight}")
                
                # Then get general insights
                for profile, insights in profiles.items():
                    if profile != patient_profile:
                        for insight in insights:
                            context_items.append(f"- {indicator} (other patient profile): {insight}")
        
        # Limit context size
        if len(context_items) > 5:
            context_items = context_items[:5]
            
        return "\n".join(context_items) if context_items else ""
    
    def _get_session_context(self, chat_history):
        """Extract relevant context from current session."""
        if not chat_history or len(chat_history) < 2:
            return ""
            
        # Get the last few message pairs (up to 2)
        context_items = []
        for i in range(len(chat_history) - 1, 0, -2):
            if i >= 1 and chat_history[i-1]['role'] == 'user' and chat_history[i]['role'] == 'assistant':
                user_msg = chat_history[i-1]['content']
                ai_msg = chat_history[i]['content']
                
                # Keep only the first 200 chars of each message to avoid token explosion
                if len(user_msg) > 200:
                    user_msg = user_msg[:197] + "..."
                if len(ai_msg) > 200:
                    ai_msg = ai_msg[:197] + "..."
                    
                context_items.append(f"User: {user_msg}\nAssistant: {ai_msg}")
                
                # Limit to last 2 exchanges
                if len(context_items) >= 2:
                    break
                    
        return "\n\n".join(reversed(context_items)) if context_items else ""
    
    def _preprocess_data(self, data):
        """Pre-process data before sending to model."""
        if isinstance(data, dict):
            # Extract only necessary information to reduce token usage
            processed = {
                "patient_name": data.get("patient_name", ""),
                "age": data.get("age", ""),
                "gender": data.get("gender", ""),
                "report": data.get("report", "")
            }
            return processed
        return data
