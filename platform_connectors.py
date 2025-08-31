import logging
from typing import List, Dict, Any, Optional
from abc import ABC, abstractmethod
import time
import random

logger = logging.getLogger(__name__)


class PlatformConnector(ABC):
    """Abstract base class for platform connectors"""
    
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


class MockLinkedInConnector(PlatformConnector):
    """Mock LinkedIn connector for MVP"""
    
    def __init__(self):
        self.connected = False
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
        logger.info("Connecting to LinkedIn...")
        time.sleep(1)  # Simulate connection time
        self.connected = True
        logger.info("Connected to LinkedIn")
        return True
    
    def get_messages(self) -> List[Dict[str, Any]]:
        if not self.connected:
            return []
        
        # Return random messages for demo
        if random.random() < 0.3:  # 30% chance of new message
            return [random.choice(self.mock_messages)]
        return []
    
    def send_message(self, recipient: str, content: str) -> bool:
        if not self.connected:
            return False
        
        logger.info(f"Sending LinkedIn message to {recipient}: {content[:50]}...")
        time.sleep(0.5)  # Simulate sending time
        return True
    
    def is_connected(self) -> bool:
        return self.connected


class MockGmailConnector(PlatformConnector):
    """Mock Gmail connector for MVP"""
    
    def __init__(self):
        self.connected = False
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
        logger.info("Connecting to Gmail...")
        time.sleep(1)
        self.connected = True
        logger.info("Connected to Gmail")
        return True
    
    def get_messages(self) -> List[Dict[str, Any]]:
        if not self.connected:
            return []
        
        if random.random() < 0.2:  # 20% chance of new message
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


class MockTelegramConnector(PlatformConnector):
    """Mock Telegram connector for MVP"""
    
    def __init__(self):
        self.connected = False
        self.mock_messages = [
            {
                "sender": "Alice",
                "content": "Hey! Are you free for a quick call tomorrow?",
                "timestamp": "2024-01-15T12:00:00Z"
            },
            {
                "sender": "Bob",
                "content": "Thanks for the help with the project!",
                "timestamp": "2024-01-15T12:30:00Z"
            }
        ]
    
    def connect(self) -> bool:
        logger.info("Connecting to Telegram...")
        time.sleep(1)
        self.connected = True
        logger.info("Connected to Telegram")
        return True
    
    def get_messages(self) -> List[Dict[str, Any]]:
        if not self.connected:
            return []
        
        if random.random() < 0.4:  # 40% chance of new message
            return [random.choice(self.mock_messages)]
        return []
    
    def send_message(self, recipient: str, content: str) -> bool:
        if not self.connected:
            return False
        
        logger.info(f"Sending Telegram message to {recipient}: {content[:50]}...")
        time.sleep(0.5)
        return True
    
    def is_connected(self) -> bool:
        return self.connected


class MockFacebookConnector(PlatformConnector):
    """Mock Facebook connector for MVP"""
    
    def __init__(self):
        self.connected = False
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
        logger.info("Connecting to Facebook...")
        time.sleep(1)
        self.connected = True
        logger.info("Connected to Facebook")
        return True
    
    def get_messages(self) -> List[Dict[str, Any]]:
        if not self.connected:
            return []
        
        if random.random() < 0.25:  # 25% chance of new message
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
    """Mock Instagram connector for MVP"""
    
    def __init__(self):
        self.connected = False
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
        logger.info("Connecting to Instagram...")
        time.sleep(1)
        self.connected = True
        logger.info("Connected to Instagram")
        return True
    
    def get_messages(self) -> List[Dict[str, Any]]:
        if not self.connected:
            return []
        
        if random.random() < 0.35:  # 35% chance of new message
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


class PlatformManager:
    """Manages all platform connectors"""
    
    def __init__(self):
        self.connectors = {
            "linkedin": MockLinkedInConnector(),
            "gmail": MockGmailConnector(),
            "telegram": MockTelegramConnector(),
            "facebook": MockFacebookConnector(),
            "instagram": MockInstagramConnector()
        }
        self.connected_platforms = set()
    
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
