#!/usr/bin/env python3
"""
Demo script for the Answering Agent
"""

import os
import sys
import tempfile
from unittest.mock import patch, MagicMock

# Add current directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from database import DatabaseManager
from message_manager import MessageManager
from platform_connectors import PlatformManager


def demo():
    """Run the demo"""
    print("🤖 Answering Agent Demo")
    print("=" * 50)
    
    # Create temporary database
    temp_db = tempfile.NamedTemporaryFile(delete=False, suffix='.db')
    db_url = f"sqlite:///{temp_db.name}"
    
    try:
        # Mock settings
        mock_settings = MagicMock()
        mock_settings.DATABASE_URL = db_url
        mock_settings.OPENAI_API_KEY = "demo_key"
        mock_settings.OPENAI_MODEL = "gpt-4"
        mock_settings.MAX_RESPONSE_LENGTH = 500
        mock_settings.RESPONSE_STYLE = "professional"
        
        # Initialize components
        with patch('database.settings', mock_settings):
            db_manager = DatabaseManager()
        
        db_session = db_manager.get_session()
        message_manager = MessageManager(db_session)
        platform_manager = PlatformManager()
        
        print("✅ Components initialized")
        
        # Connect to platforms
        print("\n🔌 Connecting to platforms...")
        results = platform_manager.connect_all()
        for platform, connected in results.items():
            print(f"   {platform.title()}: {'✅' if connected else '❌'}")
        
        # Add test messages
        print("\n📨 Adding test messages...")
        test_messages = [
            ("linkedin", "John Doe", "Hi! I'd love to connect."),
            ("gmail", "client@example.com", "Interested in your services."),
            ("telegram", "Alice", "Free for a call tomorrow?")
        ]
        
        for platform, sender, content in test_messages:
            message = message_manager.add_message(platform, sender, content)
            print(f"   📬 {platform.title()}: {sender}")
        
        # Show queue
        print("\n📋 Message queue:")
        pending = message_manager.get_pending_messages()
        for i, msg in enumerate(pending, 1):
            print(f"   {i}. {msg.platform.title()} - {msg.sender}")
        
        print("\n✅ Demo completed!")
        print("\nTo run the full bot:")
        print("1. Copy env.example to .env")
        print("2. Configure API keys")
        print("3. Run: python main.py")
        
    except Exception as e:
        print(f"❌ Demo failed: {e}")
    
    finally:
        # Cleanup
        try:
            db_session.close()
            temp_db.close()
            os.unlink(temp_db.name)
        except:
            pass


if __name__ == "__main__":
    demo()
