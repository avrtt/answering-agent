import openai
from typing import Optional, Dict, Any
from config import settings
import logging

logger = logging.getLogger(__name__)

# Configure OpenAI
openai.api_key = settings.OPENAI_API_KEY


class AIAgent:
    def __init__(self):
        self.model = settings.OPENAI_MODEL
        self.max_length = settings.MAX_RESPONSE_LENGTH
        self.style = settings.RESPONSE_STYLE
    
    def generate_response(
        self, 
        message_content: str, 
        platform: str, 
        sender: str,
        user_preferences: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Generate an AI response based on the incoming message and user preferences
        """
        try:
            # Build the system prompt based on user preferences
            system_prompt = self._build_system_prompt(platform, user_preferences)
            
            # Build the user prompt
            user_prompt = self._build_user_prompt(message_content, sender, platform)
            
            response = openai.ChatCompletion.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                max_tokens=self.max_length,
                temperature=0.7
            )
            
            return response.choices[0].message.content.strip()
            
        except Exception as e:
            logger.error(f"Error generating AI response: {e}")
            return "I apologize, but I'm having trouble generating a response right now. Please try again or respond manually."
    
    def _build_system_prompt(self, platform: str, user_preferences: Optional[Dict[str, Any]] = None) -> str:
        """Build the system prompt based on platform and user preferences"""
        base_prompt = f"""You are a helpful AI assistant that generates responses for {platform} messages. 
        
        Your responses should be:
        - Professional and appropriate for the platform
        - Concise and to the point
        - Friendly but not overly casual
        - Maximum {self.max_length} characters
        
        Platform-specific guidelines:
        - LinkedIn: Professional networking tone
        - Telegram: Conversational and friendly
        - Facebook: Social and engaging
        - Instagram: Visual and trendy
        - Gmail: Professional email tone
        """
        
        if user_preferences:
            if user_preferences.get("writing_style"):
                base_prompt += f"\nWriting style: {user_preferences['writing_style']}"
            
            if user_preferences.get("personality_traits"):
                traits = ", ".join(user_preferences["personality_traits"])
                base_prompt += f"\nPersonality traits: {traits}"
            
            if user_preferences.get("interests"):
                interests = ", ".join(user_preferences["interests"])
                base_prompt += f"\nInterests: {interests}"
            
            if user_preferences.get("response_rules"):
                rules = "\n".join([f"- {rule}" for rule in user_preferences["response_rules"]])
                base_prompt += f"\nResponse rules:\n{rules}"
        
        return base_prompt
    
    def _build_user_prompt(self, message_content: str, sender: str, platform: str) -> str:
        """Build the user prompt with message context"""
        return f"""Please generate a response to this {platform} message:

Sender: {sender}
Message: {message_content}

Generate a natural, contextual response that would be appropriate for this conversation."""
    
    def improve_response(self, original_response: str, feedback: str) -> str:
        """
        Improve an existing response based on user feedback
        """
        try:
            system_prompt = """You are an AI assistant that improves responses based on user feedback. 
            Make the requested changes while maintaining the core message and tone."""
            
            user_prompt = f"""Original response: {original_response}

User feedback: {feedback}

Please provide an improved version of the response based on the feedback."""

            response = openai.ChatCompletion.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                max_tokens=self.max_length,
                temperature=0.7
            )
            
            return response.choices[0].message.content.strip()
            
        except Exception as e:
            logger.error(f"Error improving response: {e}")
            return original_response
