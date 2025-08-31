import pytest
import os
import tempfile
from unittest.mock import Mock, patch
from database import DatabaseManager
from message_manager import MessageManager
from ai_agent import AIAgent
from platform_connectors import PlatformManager


class TestDatabaseManager:
    """Test database functionality"""
    
    def setup_method(self):
        """Setup test database"""
        self.temp_db = tempfile.NamedTemporaryFile(delete=False, suffix='.db')
        self.db_url = f"sqlite:///{self.temp_db.name}"
        
        # Mock settings
        with patch('database.settings') as mock_settings:
            mock_settings.DATABASE_URL = self.db_url
            self.db_manager = DatabaseManager()
    
    def teardown_method(self):
        """Cleanup test database"""
        self.temp_db.close()
        os.unlink(self.temp_db.name)
    
    def test_database_creation(self):
        """Test database creation"""
        assert self.db_manager.engine is not None
        assert self.db_manager.SessionLocal is not None
    
    def test_session_management(self):
        """Test session creation and cleanup"""
        session = self.db_manager.get_session()
        assert session is not None
        
        self.db_manager.close_session(session)
        # Session should be closed without error


class TestMessageManager:
    """Test message management functionality"""
    
    def setup_method(self):
        """Setup test message manager"""
        self.temp_db = tempfile.NamedTemporaryFile(delete=False, suffix='.db')
        self.db_url = f"sqlite:///{self.temp_db.name}"
        
        with patch('database.settings') as mock_settings:
            mock_settings.DATABASE_URL = self.db_url
            self.db_manager = DatabaseManager()
        
        self.db_session = self.db_manager.get_session()
        self.message_manager = MessageManager(self.db_session)
    
    def teardown_method(self):
        """Cleanup test database"""
        self.db_session.close()
        self.temp_db.close()
        os.unlink(self.temp_db.name)
    
    def test_add_message(self):
        """Test adding a message"""
        message = self.message_manager.add_message(
            platform="linkedin",
            sender="John Doe",
            content="Hello, how are you?"
        )
        
        assert message.id is not None
        assert message.platform == "linkedin"
        assert message.sender == "John Doe"
        assert message.content == "Hello, how are you?"
        assert message.status == "pending"
    
    def test_get_pending_messages(self):
        """Test getting pending messages"""
        # Add a message
        self.message_manager.add_message("linkedin", "John", "Test message")
        
        # Get pending messages
        pending = self.message_manager.get_pending_messages()
        assert len(pending) == 1
        assert pending[0].sender == "John"
    
    def test_mark_message_ignored(self):
        """Test marking message as ignored"""
        message = self.message_manager.add_message("linkedin", "John", "Test")
        
        success = self.message_manager.mark_message_ignored(message.id)
        assert success is True
        
        # Check message status
        updated_message = self.message_manager.get_message_with_responses(message.id)
        assert updated_message.status == "ignored"
        assert updated_message.is_ignored is True


class TestAIAgent:
    """Test AI agent functionality"""
    
    def setup_method(self):
        """Setup test AI agent"""
        with patch('ai_agent.settings') as mock_settings:
            mock_settings.OPENAI_API_KEY = "test_key"
            mock_settings.OPENAI_MODEL = "gpt-4"
            mock_settings.MAX_RESPONSE_LENGTH = 500
            mock_settings.RESPONSE_STYLE = "professional"
            self.ai_agent = AIAgent()
    
    @patch('openai.ChatCompletion.create')
    def test_generate_response(self, mock_openai):
        """Test response generation"""
        # Mock OpenAI response
        mock_response = Mock()
        mock_response.choices = [Mock()]
        mock_response.choices[0].message.content = "Thank you for your message!"
        mock_openai.return_value = mock_response
        
        response = self.ai_agent.generate_response(
            message_content="Hello",
            platform="linkedin",
            sender="John Doe"
        )
        
        assert response == "Thank you for your message!"
        mock_openai.assert_called_once()
    
    def test_build_system_prompt(self):
        """Test system prompt building"""
        prompt = self.ai_agent._build_system_prompt("linkedin")
        assert "linkedin" in prompt.lower()
        assert "professional" in prompt.lower()


class TestPlatformManager:
    """Test platform management functionality"""
    
    def setup_method(self):
        """Setup test platform manager"""
        self.platform_manager = PlatformManager()
    
    def test_platform_connectors_initialization(self):
        """Test platform connectors are initialized"""
        expected_platforms = ["linkedin", "gmail", "telegram", "facebook", "instagram"]
        
        for platform in expected_platforms:
            assert platform in self.platform_manager.connectors
            assert self.platform_manager.connectors[platform] is not None
    
    def test_connect_all(self):
        """Test connecting to all platforms"""
        results = self.platform_manager.connect_all()
        
        # All platforms should connect successfully in mock mode
        for platform, connected in results.items():
            assert connected is True
        
        # Check connected platforms set
        expected_platforms = {"linkedin", "gmail", "telegram", "facebook", "instagram"}
        assert self.platform_manager.connected_platforms == expected_platforms
    
    def test_get_connection_status(self):
        """Test getting connection status"""
        # Connect first
        self.platform_manager.connect_all()
        
        status = self.platform_manager.get_connection_status()
        
        for platform, connected in status.items():
            assert connected is True
    
    def test_get_all_messages(self):
        """Test getting messages from all platforms"""
        # Connect first
        self.platform_manager.connect_all()
        
        # Get messages (may be empty due to random nature of mock)
        messages = self.platform_manager.get_all_messages()
        
        # Messages should be a list
        assert isinstance(messages, list)
        
        # If messages exist, they should have required fields
        for message in messages:
            assert "platform" in message
            assert "sender" in message
            assert "content" in message
            assert "timestamp" in message


if __name__ == "__main__":
    pytest.main([__file__])
