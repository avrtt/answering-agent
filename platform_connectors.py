import logging
from typing import List, Dict, Any, Optional
from abc import ABC, abstractmethod
import time
import random
import os
import json
import asyncio
from datetime import datetime, timedelta
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
try:
    import facebook
except ImportError:
    facebook = None

try:
    import linkedin.client
    from linkedin.client import LinkedInClient
except ImportError:
    linkedin = None
    LinkedInClient = None

try:
    import instagram_private_api
except ImportError:
    instagram_private_api = None
import base64

logger = logging.getLogger(__name__)


class PlatformConnector(ABC):
    """Abstract base class for platform connectors"""
    
    def __init__(self):
        self.connected = False
        self.last_error = None
        self.rate_limit_reset = None
        self.request_count = 0
        self.max_requests_per_minute = 60
        
        # Setup retry strategy
        self.session = requests.Session()
        retry_strategy = Retry(
            total=3,
            backoff_factor=1,
            status_forcelist=[429, 500, 502, 503, 504],
        )
        adapter = HTTPAdapter(max_retries=retry_strategy)
        self.session.mount("http://", adapter)
        self.session.mount("https://", adapter)
    
    @abstractmethod
    def connect(self) -> bool:
        """Connect to the platform"""
        pass
    
    @abstractmethod
    def get_messages(self) -> List[Dict[str, Any]]:
        """Get new messages from the platform"""
        pass
    
    @abstractmethod
    def send_message(self, recipient: str, content: str) -> bool:
        """Send a message to a recipient"""
        pass
    
    @abstractmethod
    def is_connected(self) -> bool:
        """Check if connected to the platform"""
        pass
    
    def _check_rate_limit(self) -> bool:
        """Check if we're within rate limits"""
        if self.rate_limit_reset and datetime.now() < self.rate_limit_reset:
            return False
        
        if self.request_count >= self.max_requests_per_minute:
            self.rate_limit_reset = datetime.now() + timedelta(minutes=1)
            self.request_count = 0
            return False
        
        self.request_count += 1
        return True
    
    def _handle_error(self, error: Exception, operation: str):
        """Handle and log errors"""
        self.last_error = str(error)
        logger.error(f"Error in {operation}: {error}")
        return False


class LinkedInConnector(PlatformConnector):
    """Real LinkedIn connector using LinkedIn API"""
    
    def __init__(self):
        super().__init__()
        self.client = None
        self.access_token = os.getenv('LINKEDIN_ACCESS_TOKEN')
        self.client_id = os.getenv('LINKEDIN_CLIENT_ID')
        self.client_secret = os.getenv('LINKEDIN_CLIENT_SECRET')
        self.max_requests_per_minute = 30  # LinkedIn rate limit
    
    def connect(self) -> bool:
        try:
            if not LinkedInClient:
                logger.warning("LinkedIn API module not available")
                return False
                
            if not all([self.access_token, self.client_id, self.client_secret]):
                logger.warning("LinkedIn credentials not configured")
                return False
            
            # Initialize LinkedIn client
            self.client = LinkedInClient(
                client_id=self.client_id,
                client_secret=self.client_secret,
                access_token=self.access_token
            )
            
            # Test connection
            profile = self.client.get_profile()
            if profile:
                self.connected = True
                logger.info("Connected to LinkedIn API")
                return True
            else:
                logger.error("Failed to connect to LinkedIn API")
                return False
                
        except Exception as e:
            return self._handle_error(e, "LinkedIn connection")
    
    def get_messages(self) -> List[Dict[str, Any]]:
        if not self._check_rate_limit():
            logger.warning("LinkedIn rate limit reached")
            return []
        
        try:
            if not self.connected:
                return []
            
            # Get messages from LinkedIn
            messages = self.client.get_messages()
            formatted_messages = []
            
            for msg in messages:
                formatted_messages.append({
                    "sender": msg.get('sender', {}).get('name', 'Unknown'),
                    "content": msg.get('content', ''),
                    "timestamp": msg.get('timestamp', datetime.now().isoformat()),
                    "message_id": msg.get('id')
                })
            
            return formatted_messages
            
        except Exception as e:
            self._handle_error(e, "LinkedIn get_messages")
            return []
    
    def send_message(self, recipient: str, content: str) -> bool:
        if not self._check_rate_limit():
            return False
        
        try:
            if not self.connected:
                return False
            
            # Send message via LinkedIn
            result = self.client.send_message(
                recipient_id=recipient,
                message=content
            )
            
            if result:
                logger.info(f"LinkedIn message sent to {recipient}")
                return True
            else:
                logger.error(f"Failed to send LinkedIn message to {recipient}")
                return False
                
        except Exception as e:
            return self._handle_error(e, "LinkedIn send_message")
    
    def is_connected(self) -> bool:
        return self.connected


class GmailConnector(PlatformConnector):
    """Real Gmail connector using Gmail API"""
    
    def __init__(self):
        super().__init__()
        self.service = None
        self.credentials_file = os.getenv('GMAIL_CREDENTIALS_FILE')
        self.token_file = 'gmail_token.json'
        self.scopes = ['https://www.googleapis.com/auth/gmail.readonly',
                      'https://www.googleapis.com/auth/gmail.send']
        self.max_requests_per_minute = 100  # Gmail rate limit
    
    def _get_credentials(self):
        """Get Gmail API credentials"""
        creds = None
        
        # Load existing token
        if os.path.exists(self.token_file):
            creds = Credentials.from_authorized_user_file(self.token_file, self.scopes)
        
        # If no valid credentials, get new ones
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
            else:
                if not self.credentials_file:
                    logger.error("Gmail credentials file not configured")
                    return None
                
                flow = InstalledAppFlow.from_client_secrets_file(
                    self.credentials_file, self.scopes)
                creds = flow.run_local_server(port=0)
            
            # Save credentials
            with open(self.token_file, 'w') as token:
                token.write(creds.to_json())
        
        return creds
    
    def connect(self) -> bool:
        try:
            creds = self._get_credentials()
            if not creds:
                return False
            
            self.service = build('gmail', 'v1', credentials=creds)
            
            # Test connection
            profile = self.service.users().getProfile(userId='me').execute()
            if profile:
                self.connected = True
                logger.info(f"Connected to Gmail API as {profile.get('emailAddress')}")
                return True
            else:
                logger.error("Failed to connect to Gmail API")
                return False
                
        except Exception as e:
            return self._handle_error(e, "Gmail connection")
    
    def get_messages(self) -> List[Dict[str, Any]]:
        if not self._check_rate_limit():
            return []
        
        try:
            if not self.connected:
                return []
            
            # Get unread messages
            results = self.service.users().messages().list(
                userId='me', labelIds=['UNREAD'], maxResults=10
            ).execute()
            
            messages = results.get('messages', [])
            formatted_messages = []
            
            for msg in messages:
                message = self.service.users().messages().get(
                    userId='me', id=msg['id']
                ).execute()
                
                headers = message['payload']['headers']
                subject = next((h['value'] for h in headers if h['name'] == 'Subject'), 'No Subject')
                sender = next((h['value'] for h in headers if h['name'] == 'From'), 'Unknown')
                
                # Extract message body
                body = self._extract_message_body(message['payload'])
                
                formatted_messages.append({
                    "sender": sender,
                    "content": f"Subject: {subject}\n\n{body}",
                    "timestamp": datetime.fromtimestamp(
                        int(message['internalDate']) / 1000
                    ).isoformat(),
                    "message_id": msg['id']
                })
            
            return formatted_messages
            
        except Exception as e:
            self._handle_error(e, "Gmail get_messages")
            return []
    
    def _extract_message_body(self, payload):
        """Extract message body from Gmail payload"""
        if 'parts' in payload:
            for part in payload['parts']:
                if part['mimeType'] == 'text/plain':
                    return part['body']['data']
        elif 'body' in payload and 'data' in payload['body']:
            return payload['body']['data']
        return "No readable content"
    
    def send_message(self, recipient: str, content: str) -> bool:
        if not self._check_rate_limit():
            return False
        
        try:
            if not self.connected:
                return False
            
            # Create message
            message = MIMEMultipart()
            message['to'] = recipient
            message['subject'] = 'Response from Answering Agent'
            message.attach(MIMEText(content, 'plain'))
            
            # Encode message
            raw_message = base64.urlsafe_b64encode(message.as_bytes()).decode('utf-8')
            
            # Send message
            self.service.users().messages().send(
                userId='me', body={'raw': raw_message}
            ).execute()
            
            logger.info(f"Gmail message sent to {recipient}")
            return True
            
        except Exception as e:
            return self._handle_error(e, "Gmail send_message")
    
    def is_connected(self) -> bool:
        return self.connected


class FacebookConnector(PlatformConnector):
    """Real Facebook connector using Facebook Graph API"""
    
    def __init__(self):
        super().__init__()
        self.graph = None
        self.access_token = os.getenv('FACEBOOK_ACCESS_TOKEN')
        self.page_id = os.getenv('FACEBOOK_PAGE_ID')
        self.max_requests_per_minute = 200  # Facebook rate limit
    
    def connect(self) -> bool:
        try:
            if not facebook:
                logger.warning("Facebook API module not available")
                return False
                
            if not self.access_token:
                logger.warning("Facebook access token not configured")
                return False
            
            self.graph = facebook.GraphAPI(access_token=self.access_token, version="18.0")
            
            # Test connection
            profile = self.graph.get_object('me')
            if profile:
                self.connected = True
                logger.info(f"Connected to Facebook API as {profile.get('name')}")
                return True
            else:
                logger.error("Failed to connect to Facebook API")
                return False
                
        except Exception as e:
            return self._handle_error(e, "Facebook connection")
    
    def get_messages(self) -> List[Dict[str, Any]]:
        if not self._check_rate_limit():
            return []
        
        try:
            if not self.connected:
                return []
            
            # Get page messages
            if self.page_id:
                messages = self.graph.get_object(
                    f"{self.page_id}/conversations",
                    fields="messages{message,from,created_time},participants"
                )
            else:
                # Get user messages
                messages = self.graph.get_object(
                    'me/conversations',
                    fields="messages{message,from,created_time},participants"
                )
            
            formatted_messages = []
            
            for conv in messages.get('data', []):
                for msg in conv.get('messages', {}).get('data', []):
                    formatted_messages.append({
                        "sender": msg.get('from', {}).get('name', 'Unknown'),
                        "content": msg.get('message', ''),
                        "timestamp": msg.get('created_time', datetime.now().isoformat()),
                        "message_id": msg.get('id')
                    })
            
            return formatted_messages
            
        except Exception as e:
            self._handle_error(e, "Facebook get_messages")
            return []
    
    def send_message(self, recipient: str, content: str) -> bool:
        if not self._check_rate_limit():
            return False
        
        try:
            if not self.connected:
                return False
            
            # Send message
            result = self.graph.put_object(
                parent_object=recipient,
                connection_name="messages",
                message=content
            )
            
            if result:
                logger.info(f"Facebook message sent to {recipient}")
                return True
            else:
                logger.error(f"Failed to send Facebook message to {recipient}")
                return False
                
        except Exception as e:
            return self._handle_error(e, "Facebook send_message")
    
    def is_connected(self) -> bool:
        return self.connected


class InstagramConnector(PlatformConnector):
    """Real Instagram connector using Instagram Private API"""
    
    def __init__(self):
        super().__init__()
        self.api = None
        self.username = os.getenv('INSTAGRAM_USERNAME')
        self.password = os.getenv('INSTAGRAM_PASSWORD')
        self.max_requests_per_minute = 50  # Instagram rate limit
    
    def connect(self) -> bool:
        try:
            if not instagram_private_api:
                logger.warning("Instagram API module not available")
                return False
                
            if not all([self.username, self.password]):
                logger.warning("Instagram credentials not configured")
                return False
            
            # Initialize Instagram API
            self.api = instagram_private_api.InstagramAPI(
                username=self.username,
                password=self.password,
                auto_patch=True,
                drop_incompat_keys=False
            )
            
            # Test connection
            if self.api.authenticated_user_id:
                self.connected = True
                logger.info(f"Connected to Instagram API as {self.username}")
                return True
            else:
                logger.error("Failed to connect to Instagram API")
                return False
                
        except Exception as e:
            return self._handle_error(e, "Instagram connection")
    
    def get_messages(self) -> List[Dict[str, Any]]:
        if not self._check_rate_limit():
            return []
        
        try:
            if not self.connected:
                return []
            
            # Get direct messages
            inbox = self.api.direct_pending_inbox()
            formatted_messages = []
            
            for thread in inbox.get('inbox', {}).get('threads', []):
                for item in thread.get('items', []):
                    if item.get('item_type') == 'text':
                        formatted_messages.append({
                            "sender": item.get('user_id', 'Unknown'),
                            "content": item.get('text', ''),
                            "timestamp": datetime.fromtimestamp(
                                item.get('timestamp', 0)
                            ).isoformat(),
                            "message_id": item.get('item_id')
                        })
            
            return formatted_messages
            
        except Exception as e:
            self._handle_error(e, "Instagram get_messages")
            return []
    
    def send_message(self, recipient: str, content: str) -> bool:
        if not self._check_rate_limit():
            return False
        
        try:
            if not self.connected:
                return False
            
            # Send direct message
            result = self.api.direct_message(
                text=content,
                user_ids=[recipient]
            )
            
            if result:
                logger.info(f"Instagram message sent to {recipient}")
                return True
            else:
                logger.error(f"Failed to send Instagram message to {recipient}")
                return False
                
        except Exception as e:
            return self._handle_error(e, "Instagram send_message")
    
    def is_connected(self) -> bool:
        return self.connected


class TelegramConnector(PlatformConnector):
    """Real Telegram connector using Telegram Bot API"""
    
    def __init__(self):
        super().__init__()
        self.bot_token = os.getenv('TELEGRAM_BOT_TOKEN')
        self.chat_id = os.getenv('TELEGRAM_CHAT_ID')
        self.max_requests_per_minute = 30  # Telegram rate limit
    
    def connect(self) -> bool:
        try:
            if not self.bot_token:
                logger.warning("Telegram bot token not configured")
                return False
            
            # Test connection
            url = f"https://api.telegram.org/bot{self.bot_token}/getMe"
            response = self.session.get(url)
            
            if response.status_code == 200:
                bot_info = response.json()
                if bot_info.get('ok'):
                    self.connected = True
                    logger.info(f"Connected to Telegram API as {bot_info['result']['username']}")
                    return True
            
            logger.error("Failed to connect to Telegram API")
            return False
            
        except Exception as e:
            return self._handle_error(e, "Telegram connection")
    
    def get_messages(self) -> List[Dict[str, Any]]:
        if not self._check_rate_limit():
            return []
        
        try:
            if not self.connected:
                return []
            
            # Get updates (messages)
            url = f"https://api.telegram.org/bot{self.bot_token}/getUpdates"
            params = {
                'offset': -1,
                'limit': 10,
                'timeout': 0
            }
            
            response = self.session.get(url, params=params)
            
            if response.status_code == 200:
                data = response.json()
                if data.get('ok'):
                    formatted_messages = []
                    
                    for update in data.get('result', []):
                        if 'message' in update:
                            message = update['message']
                            formatted_messages.append({
                                "sender": message.get('from', {}).get('first_name', 'Unknown'),
                                "content": message.get('text', ''),
                                "timestamp": datetime.fromtimestamp(
                                    message.get('date', 0)
                                ).isoformat(),
                                "message_id": message.get('message_id'),
                                "chat_id": message.get('chat', {}).get('id')
                            })
                    
                    return formatted_messages
            
            return []
            
        except Exception as e:
            self._handle_error(e, "Telegram get_messages")
            return []
    
    def send_message(self, recipient: str, content: str) -> bool:
        if not self._check_rate_limit():
            return False
        
        try:
            if not self.connected:
                return False
            
            # Send message
            url = f"https://api.telegram.org/bot{self.bot_token}/sendMessage"
            data = {
                'chat_id': recipient,
                'text': content,
                'parse_mode': 'HTML'
            }
            
            response = self.session.post(url, json=data)
            
            if response.status_code == 200:
                result = response.json()
                if result.get('ok'):
                    logger.info(f"Telegram message sent to {recipient}")
                    return True
            
            logger.error(f"Failed to send Telegram message to {recipient}")
            return False
            
        except Exception as e:
            return self._handle_error(e, "Telegram send_message")
    
    def is_connected(self) -> bool:
        return self.connected


class PlatformManager:
    """Manages all platform connectors with fallback to mock connectors"""
    
    def __init__(self):
        self.connectors = {}
        self.connected_platforms = set()
        self._initialize_connectors()
    
    def _initialize_connectors(self):
        """Initialize connectors with fallback to mock versions"""
        # Try real connectors first, fallback to mock
        try:
            self.connectors["linkedin"] = LinkedInConnector()
            if not self.connectors["linkedin"].connect():
                logger.warning("LinkedIn real connector failed, using mock")
                self.connectors["linkedin"] = MockLinkedInConnector()
        except Exception as e:
            logger.warning(f"LinkedIn connector error: {e}, using mock")
            self.connectors["linkedin"] = MockLinkedInConnector()
        
        try:
            self.connectors["gmail"] = GmailConnector()
            if not self.connectors["gmail"].connect():
                logger.warning("Gmail real connector failed, using mock")
                self.connectors["gmail"] = MockGmailConnector()
        except Exception as e:
            logger.warning(f"Gmail connector error: {e}, using mock")
            self.connectors["gmail"] = MockGmailConnector()
        
        try:
            self.connectors["facebook"] = FacebookConnector()
            if not self.connectors["facebook"].connect():
                logger.warning("Facebook real connector failed, using mock")
                self.connectors["facebook"] = MockFacebookConnector()
        except Exception as e:
            logger.warning(f"Facebook connector error: {e}, using mock")
            self.connectors["facebook"] = MockFacebookConnector()
        
        try:
            self.connectors["instagram"] = InstagramConnector()
            if not self.connectors["instagram"].connect():
                logger.warning("Instagram real connector failed, using mock")
                self.connectors["instagram"] = MockInstagramConnector()
        except Exception as e:
            logger.warning(f"Instagram connector error: {e}, using mock")
            self.connectors["instagram"] = MockInstagramConnector()
        
        # Telegram is always real since we need it for notifications
        self.connectors["telegram"] = TelegramConnector()
    
    def connect_all(self) -> Dict[str, bool]:
        """Connect to all platforms"""
        results = {}
        for platform, connector in self.connectors.items():
            try:
                success = connector.connect()
                results[platform] = success
                if success:
                    self.connected_platforms.add(platform)
            except Exception as e:
                logger.error(f"Error connecting to {platform}: {e}")
                results[platform] = False
        
        return results
    
    def get_all_messages(self) -> List[Dict[str, Any]]:
        """Get messages from all connected platforms"""
        all_messages = []
        
        for platform, connector in self.connectors.items():
            if platform in self.connected_platforms:
                try:
                    messages = connector.get_messages()
                    for message in messages:
                        message["platform"] = platform
                        all_messages.append(message)
                except Exception as e:
                    logger.error(f"Error getting messages from {platform}: {e}")
        
        return all_messages
    
    def send_message(self, platform: str, recipient: str, content: str) -> bool:
        """Send a message to a specific platform"""
        if platform not in self.connectors:
            logger.error(f"Unknown platform: {platform}")
            return False
        
        connector = self.connectors[platform]
        if not connector.is_connected():
            logger.error(f"Not connected to {platform}")
            return False
        
        try:
            return connector.send_message(recipient, content)
        except Exception as e:
            logger.error(f"Error sending message to {platform}: {e}")
            return False
    
    def get_connection_status(self) -> Dict[str, bool]:
        """Get connection status for all platforms"""
        return {platform: connector.is_connected() for platform, connector in self.connectors.items()}


# Mock connectors for fallback (keeping the original mock implementations)
class MockLinkedInConnector(PlatformConnector):
    """Mock LinkedIn connector for fallback"""
    
    def __init__(self):
        super().__init__()
        self.mock_messages = [
            {
                "sender": "John Doe",
                "content": "Hi! I saw your profile and would love to connect. Are you open to discussing potential collaboration opportunities?",
                "timestamp": "2024-01-15T10:30:00Z"
            },
            {
                "sender": "Jane Smith",
                "content": "Thanks for accepting my connection request! I'm interested in learning more about your work in AI.",
                "timestamp": "2024-01-15T11:15:00Z"
            }
        ]
    
    def connect(self) -> bool:
        logger.info("Connecting to LinkedIn (mock)...")
        time.sleep(1)
        self.connected = True
        logger.info("Connected to LinkedIn (mock)")
        return True
    
    def get_messages(self) -> List[Dict[str, Any]]:
        if not self.connected:
            return []
        
        if random.random() < 0.3:
            return [random.choice(self.mock_messages)]
        return []
    
    def send_message(self, recipient: str, content: str) -> bool:
        if not self.connected:
            return False
        
        logger.info(f"Sending LinkedIn message to {recipient}: {content[:50]}...")
        time.sleep(0.5)
        return True
    
    def is_connected(self) -> bool:
        return self.connected


class MockGmailConnector(PlatformConnector):
    """Mock Gmail connector for fallback"""
    
    def __init__(self):
        super().__init__()
        self.mock_messages = [
            {
                "sender": "client@example.com",
                "content": "Hello, I'm interested in your services. Could you please provide more information about your pricing?",
                "timestamp": "2024-01-15T09:45:00Z"
            },
            {
                "sender": "colleague@company.com",
                "content": "Hi! Can you review the latest project proposal when you have a chance?",
                "timestamp": "2024-01-15T10:20:00Z"
            }
        ]
    
    def connect(self) -> bool:
        logger.info("Connecting to Gmail (mock)...")
        time.sleep(1)
        self.connected = True
        logger.info("Connected to Gmail (mock)")
        return True
    
    def get_messages(self) -> List[Dict[str, Any]]:
        if not self.connected:
            return []
        
        if random.random() < 0.2:
            return [random.choice(self.mock_messages)]
        return []
    
    def send_message(self, recipient: str, content: str) -> bool:
        if not self.connected:
            return False
        
        logger.info(f"Sending Gmail message to {recipient}: {content[:50]}...")
        time.sleep(0.5)
        return True
    
    def is_connected(self) -> bool:
        return self.connected


class MockFacebookConnector(PlatformConnector):
    """Mock Facebook connector for fallback"""
    
    def __init__(self):
        super().__init__()
        self.mock_messages = [
            {
                "sender": "Friend1",
                "content": "Happy birthday! Hope you have a great day!",
                "timestamp": "2024-01-15T08:00:00Z"
            },
            {
                "sender": "Friend2",
                "content": "Are you going to the event this weekend?",
                "timestamp": "2024-01-15T09:15:00Z"
            }
        ]
    
    def connect(self) -> bool:
        logger.info("Connecting to Facebook (mock)...")
        time.sleep(1)
        self.connected = True
        logger.info("Connected to Facebook (mock)")
        return True
    
    def get_messages(self) -> List[Dict[str, Any]]:
        if not self.connected:
            return []
        
        if random.random() < 0.25:
            return [random.choice(self.mock_messages)]
        return []
    
    def send_message(self, recipient: str, content: str) -> bool:
        if not self.connected:
            return False
        
        logger.info(f"Sending Facebook message to {recipient}: {content[:50]}...")
        time.sleep(0.5)
        return True
    
    def is_connected(self) -> bool:
        return self.connected


class MockInstagramConnector(PlatformConnector):
    """Mock Instagram connector for fallback"""
    
    def __init__(self):
        super().__init__()
        self.mock_messages = [
            {
                "sender": "Follower1",
                "content": "Love your latest post! 🔥",
                "timestamp": "2024-01-15T13:00:00Z"
            },
            {
                "sender": "Follower2",
                "content": "Can you share the recipe for that dish?",
                "timestamp": "2024-01-15T13:30:00Z"
            }
        ]
    
    def connect(self) -> bool:
        logger.info("Connecting to Instagram (mock)...")
        time.sleep(1)
        self.connected = True
        logger.info("Connected to Instagram (mock)")
        return True
    
    def get_messages(self) -> List[Dict[str, Any]]:
        if not self.connected:
            return []
        
        if random.random() < 0.35:
            return [random.choice(self.mock_messages)]
        return []
    
    def send_message(self, recipient: str, content: str) -> bool:
        if not self.connected:
            return False
        
        logger.info(f"Sending Instagram message to {recipient}: {content[:50]}...")
        time.sleep(0.5)
        return True
    
    def is_connected(self) -> bool:
        return self.connected
