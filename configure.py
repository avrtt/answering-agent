#!/usr/bin/env python3
"""
Simple configuration script for the answering agent
"""

import sys
import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from config import settings
from models import PersonConfiguration

def setup_person_config():
    """Setup a person configuration"""
    try:
        engine = create_engine(settings.DATABASE_URL)
        Session = sessionmaker(bind=engine)
        session = Session()
        
        print("🤖 Person Configuration Setup")
        print("=" * 30)
        
        # Get input from user
        person_name = input("Enter person name: ").strip()
        platform = input("Enter platform (linkedin/telegram/facebook/instagram/gmail): ").strip().lower()
        
        if platform not in ['linkedin', 'telegram', 'facebook', 'instagram', 'gmail']:
            print("❌ Invalid platform. Please choose from: linkedin, telegram, facebook, instagram, gmail")
            return
        
        print("\nAvailable writing styles:")
        print("1. professional")
        print("2. conversational")
        print("3. formal")
        print("4. casual")
        print("5. friendly")
        
        writing_style = input("Enter writing style (or press Enter for 'professional'): ").strip()
        if not writing_style:
            writing_style = "professional"
        
        print("\nAvailable tones:")
        print("1. formal")
        print("2. friendly")
        print("3. casual")
        print("4. professional")
        print("5. enthusiastic")
        
        tone = input("Enter tone (or press Enter for 'friendly'): ").strip()
        if not tone:
            tone = "friendly"
        
        print("\nAvailable relationship types:")
        print("1. acquaintance")
        print("2. friend")
        print("3. colleague")
        print("4. client")
        print("5. mentor")
        
        relationship_type = input("Enter relationship type (or press Enter for 'acquaintance'): ").strip()
        if not relationship_type:
            relationship_type = "acquaintance"
        
        # Check if configuration already exists
        existing = session.query(PersonConfiguration).filter(
            PersonConfiguration.person_name == person_name,
            PersonConfiguration.platform == platform
        ).first()
        
        if existing:
            print(f"⚠️  Configuration for {person_name} on {platform} already exists")
            update = input("Do you want to update it? (y/n): ").strip().lower()
            if update != 'y':
                return
        
        # Create or update configuration
        if existing:
            existing.writing_style = writing_style
            existing.tone = tone
            existing.relationship_type = relationship_type
            print(f"✅ Updated configuration for {person_name}")
        else:
            config = PersonConfiguration(
                person_name=person_name,
                platform=platform,
                writing_style=writing_style,
                tone=tone,
                relationship_type=relationship_type
            )
            session.add(config)
            print(f"✅ Created configuration for {person_name}")
        
        session.commit()
        session.close()
        
    except Exception as e:
        print(f"❌ Error: {e}")

def list_person_configs():
    """List all person configurations"""
    try:
        engine = create_engine(settings.DATABASE_URL)
        Session = sessionmaker(bind=engine)
        session = Session()
        
        configs = session.query(PersonConfiguration).all()
        
        if not configs:
            print("No person configurations found.")
            return
        
        print("📋 Person Configurations:")
        print("=" * 40)
        
        for config in configs:
            print(f"👤 {config.person_name} ({config.platform})")
            print(f"   Style: {config.writing_style}")
            print(f"   Tone: {config.tone}")
            print(f"   Relationship: {config.relationship_type}")
            print()
        
        session.close()
        
    except Exception as e:
        print(f"❌ Error: {e}")

def show_help():
    """Show help information"""
    print("""
🤖 Answering Agent Configuration

Available commands:
1. add-person     - Add a new person configuration
2. list-persons   - List all person configurations
3. help           - Show this help

Environment Variables to configure:
- GOOGLE_SEARCH_API_KEY: Your Google Search API key
- GOOGLE_SEARCH_ENGINE_ID: Your Google Custom Search Engine ID
- PERSONAL_WEBSITE: Your personal website URL
- GITHUB_PROFILE: Your GitHub profile URL
- LINKEDIN_PROFILE: Your LinkedIn profile URL
- TWITTER_PROFILE: Your Twitter profile URL

Features enabled by default:
- Message type detection
- Person-specific responses
- Personal information search
- Web search integration

To disable features, set in .env:
- ENABLE_MESSAGE_TYPE_DETECTION=false
- ENABLE_PERSON_SPECIFIC_RESPONSES=false
- ENABLE_GOOGLE_SEARCH=false
- ENABLE_PERSONAL_INFO_SEARCH=false
""")

def main():
    """Main configuration function"""
    if len(sys.argv) < 2:
        show_help()
        return
    
    command = sys.argv[1].lower()
    
    if command == "add-person":
        setup_person_config()
    elif command == "list-persons":
        list_person_configs()
    elif command == "help":
        show_help()
    else:
        print(f"❌ Unknown command: {command}")
        show_help()

if __name__ == "__main__":
    main()
