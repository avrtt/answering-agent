from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
from models import Message, Response, UserPreferences
from ai_agent import AIAgent
import logging
import re
from datetime import datetime

logger = logging.getLogger(__name__)


class MessageManager:
    def __init__(self, db_session: Session):
        self.db = db_session
        self.ai_agent = AIAgent(db_session)
    
    def add_message(self, platform: str, sender: str, content: str) -> Message:
        """Add a new message to the queue"""
        try:
            # Detect message type
            message_type = self._detect_message_type(content, sender, platform)
            
            message = Message(
                platform=platform,
                sender=sender,
                content=content,
                status="pending",
                message_type=message_type
            )
            self.db.add(message)
            self.db.commit()
            self.db.refresh(message)
            logger.info(f"Added new message from {sender} on {platform} (type: {message_type})")
            return message
        except Exception as e:
            self.db.rollback()
            logger.error(f"Error adding message: {e}")
            raise
    
    def _detect_message_type(self, message_content: str, sender: str, platform: str) -> str:
        """Detect the type of message based on content and context"""
        try:
            content_lower = message_content.lower()
            sender_lower = sender.lower()
            
            # Message type patterns
            type_patterns = {
                'business': {
                    'keywords': [
                        'meeting', 'call', 'schedule', 'appointment', 'proposal', 'contract',
                        'partnership', 'collaboration', 'business', 'work', 'project',
                        'client', 'customer', 'service', 'consultation', 'opportunity'
                    ],
                    'patterns': [
                        r'\b(meeting|call|schedule)\b',
                        r'\b(proposal|contract|agreement)\b',
                        r'\b(business|work|project)\b',
                        r'\b(client|customer|service)\b'
                    ]
                },
                'personal': {
                    'keywords': [
                        'friend', 'family', 'personal', 'life', 'hobby', 'interest',
                        'weekend', 'vacation', 'birthday', 'celebration', 'party',
                        'catch up', 'coffee', 'lunch', 'dinner', 'social'
                    ],
                    'patterns': [
                        r'\b(friend|family|personal)\b',
                        r'\b(hobby|interest|weekend)\b',
                        r'\b(birthday|celebration|party)\b',
                        r'\b(catch up|coffee|lunch)\b'
                    ]
                },
                'support': {
                    'keywords': [
                        'help', 'support', 'issue', 'problem', 'error', 'bug',
                        'question', 'inquiry', 'assistance', 'troubleshoot',
                        'fix', 'resolve', 'urgent', 'emergency'
                    ],
                    'patterns': [
                        r'\b(help|support|assistance)\b',
                        r'\b(issue|problem|error|bug)\b',
                        r'\b(question|inquiry)\b',
                        r'\b(urgent|emergency)\b'
                    ]
                },
                'networking': {
                    'keywords': [
                        'connect', 'network', 'introduction', 'referral', 'recommendation',
                        'professional', 'career', 'industry', 'conference', 'event',
                        'speaking', 'presentation', 'workshop', 'mentor', 'mentorship'
                    ],
                    'patterns': [
                        r'\b(connect|network|introduction)\b',
                        r'\b(referral|recommendation)\b',
                        r'\b(professional|career|industry)\b',
                        r'\b(conference|event|speaking)\b'
                    ]
                },
                'sales': {
                    'keywords': [
                        'purchase', 'buy', 'order', 'product', 'service', 'price',
                        'quote', 'discount', 'offer', 'deal', 'promotion',
                        'sales', 'marketing', 'advertisement', 'promote'
                    ],
                    'patterns': [
                        r'\b(purchase|buy|order)\b',
                        r'\b(product|service|price)\b',
                        r'\b(quote|discount|offer)\b',
                        r'\b(sales|marketing|promote)\b'
                    ]
                }
            }
            
            # Calculate scores for each message type
            type_scores = {}
            
            for msg_type, patterns in type_patterns.items():
                score = 0
                
                # Check keywords
                for keyword in patterns['keywords']:
                    if keyword in content_lower:
                        score += 2
                
                # Check patterns
                for pattern in patterns['patterns']:
                    matches = re.findall(pattern, content_lower)
                    score += len(matches) * 3
                
                # Platform-specific adjustments
                score = self._adjust_score_for_platform(score, msg_type, platform)
                
                # Sender-specific adjustments
                score = self._adjust_score_for_sender(score, msg_type, sender_lower)
                
                type_scores[msg_type] = score
            
            # Find the type with highest score
            if type_scores:
                best_type = max(type_scores, key=type_scores.get)
                if type_scores[best_type] > 0:
                    return best_type
            
            # Default to general if no clear type detected
            return 'general'
            
        except Exception as e:
            logger.error(f"Error detecting message type: {e}")
            return 'general'
    
    def _adjust_score_for_platform(self, score: int, msg_type: str, platform: str) -> int:
        """Adjust score based on platform context"""
        platform_adjustments = {
            'linkedin': {
                'business': 3,
                'networking': 3,
                'personal': -1,
                'sales': 1
            },
            'telegram': {
                'personal': 2,
                'business': 1,
                'support': 1
            },
            'facebook': {
                'personal': 2,
                'social': 2,
                'business': 0
            },
            'instagram': {
                'personal': 2,
                'social': 2,
                'business': 0
            },
            'gmail': {
                'business': 2,
                'support': 2,
                'personal': 1
            }
        }
        
        adjustments = platform_adjustments.get(platform, {})
        return score + adjustments.get(msg_type, 0)
    
    def _adjust_score_for_sender(self, score: int, msg_type: str, sender: str) -> int:
        """Adjust score based on sender context"""
        # Common business-related sender patterns
        business_senders = [
            'hr', 'human resources', 'recruiter', 'hiring', 'manager',
            'director', 'ceo', 'cto', 'founder', 'co-founder',
            'sales', 'marketing', 'support', 'customer service'
        ]
        
        # Common personal sender patterns
        personal_senders = [
            'friend', 'family', 'mom', 'dad', 'brother', 'sister',
            'cousin', 'uncle', 'aunt', 'colleague', 'classmate'
        ]
        
        sender_lower = sender.lower()
        
        if any(business in sender_lower for business in business_senders):
            if msg_type == 'business':
                score += 2
            elif msg_type == 'personal':
                score -= 1
        
        if any(personal in sender_lower for personal in personal_senders):
            if msg_type == 'personal':
                score += 2
            elif msg_type == 'business':
                score -= 1
        
        return score
    
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
                preferences,
                self.db
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
