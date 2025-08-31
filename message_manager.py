from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
from models import Message, Response, UserPreferences
from ai_agent import AIAgent
import logging
from datetime import datetime

logger = logging.getLogger(__name__)


class MessageManager:
    def __init__(self, db_session: Session):
        self.db = db_session
        self.ai_agent = AIAgent()
    
    def add_message(self, platform: str, sender: str, content: str) -> Message:
        """Add a new message to the queue"""
        try:
            message = Message(
                platform=platform,
                sender=sender,
                content=content,
                status="pending"
            )
            self.db.add(message)
            self.db.commit()
            self.db.refresh(message)
            logger.info(f"Added new message from {sender} on {platform}")
            return message
        except Exception as e:
            self.db.rollback()
            logger.error(f"Error adding message: {e}")
            raise
    
    def get_pending_messages(self) -> List[Message]:
        """Get all pending messages"""
        return self.db.query(Message).filter(
            Message.status == "pending"
        ).order_by(Message.timestamp.asc()).all()
    
    def get_next_message(self) -> Optional[Message]:
        """Get the next pending message"""
        return self.db.query(Message).filter(
            Message.status == "pending"
        ).order_by(Message.timestamp.asc()).first()
    
    def mark_message_processing(self, message_id: str) -> bool:
        """Mark a message as being processed"""
        try:
            message = self.db.query(Message).filter(Message.id == message_id).first()
            if message:
                message.status = "processing"
                self.db.commit()
                return True
            return False
        except Exception as e:
            self.db.rollback()
            logger.error(f"Error marking message as processing: {e}")
            return False
    
    def mark_message_answered(self, message_id: str) -> bool:
        """Mark a message as answered"""
        try:
            message = self.db.query(Message).filter(Message.id == message_id).first()
            if message:
                message.status = "answered"
                message.is_answered = True
                self.db.commit()
                return True
            return False
        except Exception as e:
            self.db.rollback()
            logger.error(f"Error marking message as answered: {e}")
            return False
    
    def mark_message_ignored(self, message_id: str) -> bool:
        """Mark a message as ignored"""
        try:
            message = self.db.query(Message).filter(Message.id == message_id).first()
            if message:
                message.status = "ignored"
                message.is_ignored = True
                self.db.commit()
                return True
            return False
        except Exception as e:
            self.db.rollback()
            logger.error(f"Error marking message as ignored: {e}")
            return False
    
    def generate_ai_response(self, message_id: str) -> Optional[Response]:
        """Generate an AI response for a message"""
        try:
            message = self.db.query(Message).filter(Message.id == message_id).first()
            if not message:
                return None
            
            # Get user preferences
            user_prefs = self.db.query(UserPreferences).first()
            preferences = None
            if user_prefs:
                preferences = {
                    "writing_style": user_prefs.writing_style,
                    "personality_traits": user_prefs.personality_traits,
                    "interests": user_prefs.interests,
                    "response_rules": user_prefs.response_rules
                }
            
            # Generate AI response
            ai_response = self.ai_agent.generate_response(
                message.content,
                message.platform,
                message.sender,
                preferences
            )
            
            # Save response
            response = Response(
                message_id=message_id,
                content=ai_response,
                response_type="ai"
            )
            self.db.add(response)
            self.db.commit()
            self.db.refresh(response)
            
            return response
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"Error generating AI response: {e}")
            return None
    
    def save_manual_response(self, message_id: str, content: str) -> Optional[Response]:
        """Save a manual response"""
        try:
            response = Response(
                message_id=message_id,
                content=content,
                response_type="manual"
            )
            self.db.add(response)
            self.db.commit()
            self.db.refresh(response)
            return response
        except Exception as e:
            self.db.rollback()
            logger.error(f"Error saving manual response: {e}")
            return None
    
    def improve_response(self, response_id: str, feedback: str) -> Optional[Response]:
        """Improve an existing response based on feedback"""
        try:
            response = self.db.query(Response).filter(Response.id == response_id).first()
            if not response:
                return None
            
            # Generate improved response
            improved_content = self.ai_agent.improve_response(response.content, feedback)
            
            # Update response
            response.content = improved_content
            self.db.commit()
            self.db.refresh(response)
            
            return response
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"Error improving response: {e}")
            return None
    
    def mark_response_sent(self, response_id: str) -> bool:
        """Mark a response as sent"""
        try:
            response = self.db.query(Response).filter(Response.id == response_id).first()
            if response:
                response.is_sent = True
                response.sent_at = datetime.utcnow()
                self.db.commit()
                return True
            return False
        except Exception as e:
            self.db.rollback()
            logger.error(f"Error marking response as sent: {e}")
            return False
    
    def get_message_with_responses(self, message_id: str) -> Optional[Message]:
        """Get a message with all its responses"""
        return self.db.query(Message).filter(Message.id == message_id).first()
    
    def clear_local_storage(self):
        """Clear all data (for local mode)"""
        try:
            self.db.query(Response).delete()
            self.db.query(Message).delete()
            self.db.commit()
            logger.info("Local storage cleared")
        except Exception as e:
            self.db.rollback()
            logger.error(f"Error clearing local storage: {e}")
            raise
