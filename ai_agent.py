import openai
from typing import Optional, Dict, Any
from config import settings
import logging
import re
import requests
import json
from bs4 import BeautifulSoup
from datetime import datetime, timedelta
from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)

# Configure OpenAI
openai.api_key = settings.OPENAI_API_KEY


class AIAgent:
    def __init__(self, db_session: Session = None):
        self.model = settings.OPENAI_MODEL
        self.max_length = settings.MAX_RESPONSE_LENGTH
        self.style = settings.RESPONSE_STYLE
        
        # Initialize components
        
        # Web search configuration
        self.google_api_key = settings.GOOGLE_SEARCH_API_KEY
        self.google_engine_id = settings.GOOGLE_SEARCH_ENGINE_ID
        self.personal_website = settings.PERSONAL_WEBSITE
        self.github_profile = settings.GITHUB_PROFILE
        self.linkedin_profile = settings.LINKEDIN_PROFILE
        self.twitter_profile = settings.TWITTER_PROFILE
        
        # Cache for personal information
        self._personal_info_cache = {}
        self._cache_expiry = None
        self._cache_duration = timedelta(hours=24)  # Cache for 24 hours
        
        # Message type patterns
        self.type_patterns = {
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
    
    def generate_response(
        self, 
        message_content: str, 
        platform: str, 
        sender: str,
        user_preferences: Optional[Dict[str, Any]] = None,
        db_session: Session = None
    ) -> str:
        """
        Generate an AI response based on the incoming message and user preferences
        """
        try:
            # Detect message type
            message_type = self._detect_message_type(message_content, sender, platform)
            
            # Get person-specific configuration
            person_preferences = self._get_person_preferences(sender, platform, db_session)
            
            # Get web search context
            web_context = self._get_web_context(message_content)
            
            # Get conversation context
            conversation_context = self._get_conversation_context(sender, platform, db_session)
            
            # Build the system prompt based on all configurations
            system_prompt = self._build_enhanced_system_prompt(
                platform, 
                message_type, 
                user_preferences, 
                person_preferences,
                web_context
            )
            
            # Build the user prompt with all context
            user_prompt = self._build_enhanced_user_prompt(
                message_content, 
                sender, 
                platform, 
                message_type,
                conversation_context,
                web_context
            )
            
            response = openai.ChatCompletion.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                max_tokens=self._get_max_length(person_preferences),
                temperature=0.7
            )
            
            generated_response = response.choices[0].message.content.strip()
            
            # Update conversation history
            self._update_conversation_history(sender, platform, message_content, generated_response, db_session)
            
            return generated_response
            
        except Exception as e:
            logger.error(f"Error generating AI response: {e}")
            return "I apologize, but I'm having trouble generating a response right now. Please try again or respond manually."
    
    def _detect_message_type(self, message_content: str, sender: str, platform: str) -> str:
        """Detect the type of message"""
        if not settings.ENABLE_MESSAGE_TYPE_DETECTION:
            return "general"
        
        try:
            content_lower = message_content.lower()
            sender_lower = sender.lower()
            
            # Calculate scores for each message type
            type_scores = {}
            
            for msg_type, patterns in self.type_patterns.items():
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
    
    def _get_person_preferences(self, sender: str, platform: str, db_session: Session) -> Dict[str, Any]:
        """Get person-specific preferences"""
        if not settings.ENABLE_PERSON_SPECIFIC_RESPONSES or not db_session:
            return {}
        
        try:
            # Try to find person configuration
            from models import PersonConfiguration
            
            config = db_session.query(PersonConfiguration).filter(
                PersonConfiguration.person_name == sender,
                PersonConfiguration.platform == platform
            ).first()
            
            if config:
                preferences = {
                    'writing_style': config.writing_style,
                    'tone': config.tone,
                    'personality_traits': config.personality_traits,
                    'response_rules': config.response_rules,
                    'max_length': config.max_length,
                    'relationship_type': config.relationship_type
                }
                # Remove None values
                return {k: v for k, v in preferences.items() if v is not None}
            
            return {}
            
        except Exception as e:
            logger.error(f"Error getting person preferences: {e}")
            return {}
    
    def _get_web_context(self, message_content: str) -> str:
        """Get web search context for the message"""
        if not settings.ENABLE_GOOGLE_SEARCH and not settings.ENABLE_PERSONAL_INFO_SEARCH:
            return ""
        
        context_parts = []
        
        # Search personal information
        personal_results = self._search_personal_info(message_content)
        if personal_results:
            context_parts.append("Personal Information:")
            for result in personal_results[:3]:  # Top 3 results
                context_parts.append(f"- {result['content']}")
        
        # Search Google if enabled
        if settings.ENABLE_GOOGLE_SEARCH:
            google_results = self._search_google(message_content, num_results=3)
            if google_results:
                context_parts.append("\nRelevant Web Information:")
                for result in google_results:
                    context_parts.append(f"- {result['title']}: {result['snippet']}")
        
        return "\n".join(context_parts) if context_parts else ""
    
    def _search_google(self, query: str, num_results: int = 5) -> list:
        """Search Google for information"""
        if not self.google_api_key or not self.google_engine_id:
            logger.warning("Google Search API not configured")
            return []
        
        try:
            url = "https://www.googleapis.com/customsearch/v1"
            params = {
                'key': self.google_api_key,
                'cx': self.google_engine_id,
                'q': query,
                'num': num_results
            }
            
            response = requests.get(url, params=params)
            response.raise_for_status()
            
            data = response.json()
            results = []
            
            if 'items' in data:
                for item in data['items']:
                    results.append({
                        'title': item.get('title', ''),
                        'snippet': item.get('snippet', ''),
                        'link': item.get('link', '')
                    })
            
            return results
            
        except Exception as e:
            logger.error(f"Error searching Google: {e}")
            return []
    
    def _search_personal_info(self, query: str) -> list:
        """Search personal information sources for specific queries"""
        personal_info = self._get_personal_info()
        results = []
        
        query_lower = query.lower()
        
        # Search in contact info
        if 'contact' in query_lower or 'email' in query_lower or 'phone' in query_lower:
            for key, value in personal_info.get('contact_info', {}).items():
                results.append({
                    'source': 'personal_website',
                    'type': 'contact_info',
                    'content': f"{key}: {value}",
                    'relevance': 'high'
                })
        
        # Search in interests
        if any(word in query_lower for word in ['interest', 'hobby', 'passion', 'like']):
            for interest in personal_info.get('interests', []):
                results.append({
                    'source': 'personal_website',
                    'type': 'interest',
                    'content': interest,
                    'relevance': 'medium'
                })
        
        # Search in projects
        if any(word in query_lower for word in ['project', 'work', 'portfolio', 'github']):
            for project in personal_info.get('projects', []):
                results.append({
                    'source': 'github',
                    'type': 'project',
                    'content': f"{project['name']}: {project['description']}",
                    'relevance': 'high'
                })
        
        # Search in skills
        if any(word in query_lower for word in ['skill', 'technology', 'language', 'tool']):
            for skill in personal_info.get('skills', []):
                results.append({
                    'source': 'personal_website',
                    'type': 'skill',
                    'content': skill,
                    'relevance': 'medium'
                })
        
        return results
    
    def _get_personal_info(self, force_refresh: bool = False) -> Dict[str, Any]:
        """Get personal information from various sources"""
        # Check cache first
        if not force_refresh and self._personal_info_cache and self._cache_expiry and datetime.now() < self._cache_expiry:
            return self._personal_info_cache
        
        personal_info = {
            'contact_info': {},
            'interests': [],
            'projects': [],
            'skills': [],
            'experience': [],
            'education': [],
            'social_links': {}
        }
        
        try:
            # Scrape personal website
            if self.personal_website:
                website_info = self._scrape_personal_website()
                personal_info.update(website_info)
            
            # Scrape GitHub profile
            if self.github_profile:
                github_info = self._scrape_github_profile()
                personal_info.update(github_info)
            
            # Update cache
            self._personal_info_cache = personal_info
            self._cache_expiry = datetime.now() + self._cache_duration
            
            return personal_info
            
        except Exception as e:
            logger.error(f"Error getting personal info: {e}")
            return personal_info
    
    def _scrape_personal_website(self) -> Dict[str, Any]:
        """Scrape personal information from personal website"""
        try:
            response = requests.get(self.personal_website, timeout=10)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            info = {
                'contact_info': {},
                'interests': [],
                'projects': [],
                'skills': [],
                'experience': [],
                'education': []
            }
            
            # Extract contact information
            contact_patterns = [
                r'email[:\s]*([^\s@]+@[^\s@]+\.[^\s@]+)',
                r'phone[:\s]*([+\d\s\-\(\)]+)',
                r'contact[:\s]*([^\n]+)'
            ]
            
            text_content = soup.get_text().lower()
            for pattern in contact_patterns:
                matches = re.findall(pattern, text_content, re.IGNORECASE)
                if matches:
                    info['contact_info']['email'] = matches[0] if 'email' in pattern else matches[0]
            
            # Extract interests and skills
            interest_keywords = ['interests', 'hobbies', 'passions', 'likes']
            skill_keywords = ['skills', 'technologies', 'languages', 'tools']
            
            for keyword in interest_keywords:
                elements = soup.find_all(text=re.compile(keyword, re.IGNORECASE))
                for element in elements:
                    # Extract nearby text as interests
                    parent = element.parent
                    if parent:
                        text = parent.get_text()
                        # Simple extraction - could be improved
                        info['interests'].append(text[:200])
            
            for keyword in skill_keywords:
                elements = soup.find_all(text=re.compile(keyword, re.IGNORECASE))
                for element in elements:
                    parent = element.parent
                    if parent:
                        text = parent.get_text()
                        info['skills'].append(text[:200])
            
            return info
            
        except Exception as e:
            logger.error(f"Error scraping personal website: {e}")
            return {}
    
    def _scrape_github_profile(self) -> Dict[str, Any]:
        """Scrape information from GitHub profile"""
        try:
            # Use GitHub API instead of scraping
            username = self.github_profile.split('/')[-1]
            api_url = f"https://api.github.com/users/{username}"
            
            response = requests.get(api_url, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            
            info = {
                'projects': [],
                'skills': [],
                'social_links': {}
            }
            
            # Get user info
            if data.get('bio'):
                info['interests'] = [data['bio']]
            
            if data.get('blog'):
                info['contact_info']['website'] = data['blog']
            
            # Get repositories
            repos_url = f"https://api.github.com/users/{username}/repos"
            repos_response = requests.get(repos_url, timeout=10)
            if repos_response.status_code == 200:
                repos_data = repos_response.json()
                for repo in repos_data[:10]:  # Top 10 repos
                    if not repo['fork']:  # Only personal projects
                        info['projects'].append({
                            'name': repo['name'],
                            'description': repo.get('description', ''),
                            'language': repo.get('language', ''),
                            'url': repo['html_url']
                        })
            
            info['social_links']['github'] = self.github_profile
            return info
            
        except Exception as e:
            logger.error(f"Error scraping GitHub profile: {e}")
            return {}
    
    def _get_conversation_context(self, sender: str, platform: str, db_session: Session) -> str:
        """Get conversation context for the person"""
        if not settings.ENABLE_PERSON_SPECIFIC_RESPONSES or not db_session:
            return ""
        
        try:
            from models import PersonConfiguration
            
            config = db_session.query(PersonConfiguration).filter(
                PersonConfiguration.person_name == sender,
                PersonConfiguration.platform == platform
            ).first()
            
            if config and config.conversation_history:
                # Get recent messages
                recent_messages = config.conversation_history[-3:]  # Last 3 messages
                
                context_parts = []
                for entry in recent_messages:
                    if entry.get('message'):
                        context_parts.append(f"Previous message: {entry['message']}")
                    if entry.get('response'):
                        context_parts.append(f"Your response: {entry['response']}")
                
                return "\n".join(context_parts)
            
            return ""
            
        except Exception as e:
            logger.error(f"Error getting conversation context: {e}")
            return ""
    
    def _update_conversation_history(self, sender: str, platform: str, message_content: str, response_content: str, db_session: Session):
        """Update conversation history"""
        if not settings.ENABLE_PERSON_SPECIFIC_RESPONSES or not db_session:
            return
        
        try:
            from models import PersonConfiguration
            from datetime import datetime
            
            config = db_session.query(PersonConfiguration).filter(
                PersonConfiguration.person_name == sender,
                PersonConfiguration.platform == platform
            ).first()
            
            if config:
                # Add to conversation history
                history_entry = {
                    'timestamp': datetime.utcnow().isoformat(),
                    'message': message_content,
                    'response': response_content
                }
                
                if not config.conversation_history:
                    config.conversation_history = []
                
                config.conversation_history.append(history_entry)
                
                # Keep only last 10 conversations
                if len(config.conversation_history) > 10:
                    config.conversation_history = config.conversation_history[-10:]
                
                config.updated_at = datetime.utcnow()
                db_session.commit()
            
        except Exception as e:
            logger.error(f"Error updating conversation history: {e}")
            db_session.rollback()
    
    def _get_max_length(self, person_preferences: Dict[str, Any]) -> int:
        """Get max length based on person preferences or default"""
        return person_preferences.get('max_length', self.max_length)
    
    def _build_enhanced_system_prompt(
        self, 
        platform: str, 
        message_type: str, 
        user_preferences: Optional[Dict[str, Any]] = None,
        person_preferences: Dict[str, Any] = None,
        web_context: str = ""
    ) -> str:
        """Build enhanced system prompt with all configurations"""
        base_prompt = f"""You are a helpful AI assistant that generates responses for {platform} messages. 
        
        Message Type: {message_type}
        
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
        
        Message Type Guidelines:
        - Business: Professional, formal, solution-oriented
        - Personal: Warm, friendly, conversational
        - Support: Helpful, patient, solution-focused
        - Networking: Professional, engaging, relationship-building
        - Sales: Informative, persuasive, value-focused
        """
        
        # Add user preferences
        if user_preferences:
            if user_preferences.get("writing_style"):
                base_prompt += f"\nUser Writing Style: {user_preferences['writing_style']}"
            
            if user_preferences.get("personality_traits"):
                traits = ", ".join(user_preferences["personality_traits"])
                base_prompt += f"\nUser Personality Traits: {traits}"
            
            if user_preferences.get("interests"):
                interests = ", ".join(user_preferences["interests"])
                base_prompt += f"\nUser Interests: {interests}"
            
            if user_preferences.get("response_rules"):
                rules = "\n".join([f"- {rule}" for rule in user_preferences["response_rules"]])
                base_prompt += f"\nUser Response Rules:\n{rules}"
        
        # Add person-specific preferences
        if person_preferences:
            if person_preferences.get("writing_style"):
                base_prompt += f"\nPerson-Specific Writing Style: {person_preferences['writing_style']}"
            
            if person_preferences.get("tone"):
                base_prompt += f"\nPerson-Specific Tone: {person_preferences['tone']}"
            
            if person_preferences.get("relationship_type"):
                base_prompt += f"\nRelationship Type: {person_preferences['relationship_type']}"
            
            if person_preferences.get("response_rules"):
                rules = "\n".join([f"- {rule}" for rule in person_preferences["response_rules"]])
                base_prompt += f"\nPerson-Specific Rules:\n{rules}"
        
        # Add web context if available
        if web_context:
            base_prompt += f"\n\nRelevant Context Information:\n{web_context}"
        
        return base_prompt
    
    def _build_enhanced_user_prompt(
        self, 
        message_content: str, 
        sender: str, 
        platform: str, 
        message_type: str,
        conversation_context: str = "",
        web_context: str = ""
    ) -> str:
        """Build enhanced user prompt with all context"""
        prompt_parts = [
            f"Please generate a response to this {platform} message:",
            f"Message Type: {message_type}",
            f"Sender: {sender}",
            f"Message: {message_content}"
        ]
        
        if conversation_context:
            prompt_parts.append(f"\nConversation Context:\n{conversation_context}")
        
        if web_context:
            prompt_parts.append(f"\nRelevant Information:\n{web_context}")
        
        prompt_parts.append("\nGenerate a natural, contextual response that would be appropriate for this conversation.")
        
        return "\n".join(prompt_parts)
    
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
