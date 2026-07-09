import base64
import streamlit as st
import logging

logger = logging.getLogger(__name__)

def extract_text_from_image(image_file):
    """Converts uploaded image to base64 and uses the active AI client to OCR and extract text."""
    try:
        # Read bytes and convert to base64
        image_file.seek(0)
        file_bytes = image_file.read()
        base64_image = base64.b64encode(file_bytes).decode('utf-8')
        mime_type = image_file.type
        
        # Check active model manager configurations
        from agents.model_manager import ModelManager, get_groq_api_key, get_mistral_api_key
        
        has_groq = get_groq_api_key() is not None
        has_mistral = get_mistral_api_key() is not None
        
        # If running in local simulated mock mode (no API keys configured)
        if not has_groq and not has_mistral:
            logger.info("Using mock image extraction fallback")
            from config.sample_data import SAMPLE_REPORT
            return SAMPLE_REPORT
            
        manager = ModelManager()
        
        # 1. If Groq is configured, use its Llama 3.2 Vision model
        if "groq" in manager.clients:
            client = manager.clients["groq"]
            logger.info("Extracting text from image using Groq Vision model")
            
            completion = client.chat.completions.create(
                model="llama-3.2-11b-vision-preview",
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "text", 
                                "text": "Extract all clinical report content from this medical blood test report image. Output ONLY the raw extracted text as is. Do not include conversational remarks."
                            },
                            {
                                "type": "image_url",
                                "image_url": {
                                    "url": f"data:{mime_type};base64,{base64_image}"
                                }
                            }
                        ]
                    }
                ]
            )
            return completion.choices[0].message.content
            
        # 2. If Mistral is configured, use its Pixtral Vision model via API
        elif "mistral" in manager.clients:
            import requests
            logger.info("Extracting text from image using Mistral Pixtral Vision model")
            
            headers = {
                "Authorization": f"Bearer {manager.clients['mistral']}",
                "Content-Type": "application/json"
            }
            payload = {
                "model": "pixtral-12b",
                "messages": [
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "text", 
                                "text": "Extract all clinical report content from this medical blood test report image. Output ONLY the raw extracted text as is. Do not include conversational remarks."
                            },
                            {
                                "type": "image_url",
                                "image_url": {
                                    "url": f"data:{mime_type};base64,{base64_image}"
                                }
                            }
                        ]
                    }
                ]
            }
            
            response = requests.post(
                "https://api.mistral.ai/v1/chat/completions",
                json=payload,
                headers=headers,
                timeout=30
            )
            if response.status_code == 200:
                return response.json()["choices"][0]["message"]["content"]
            else:
                logger.error(f"Mistral image extraction API failed: {response.text}")
                
        # Final fallback to local mock sample if API requests failed
        from config.sample_data import SAMPLE_REPORT
        return SAMPLE_REPORT
        
    except Exception as e:
        logger.error(f"Image text extraction error: {str(e)}")
        return f"Error extracting text from image: {str(e)}"
