import asyncio
import logging
import signal
import sys
import time
from threading import Thread
from database import db_manager
from telegram_bot import bot
from platform_connectors import PlatformManager
from message_manager import MessageManager
from config import settings
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from models import Base, MessageTypeStyle, PersonConfiguration, WebSearchConfiguration

# Configure logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)


def create_new_tables():
    """Create new tables for enhanced features"""
    try:
        # Create database engine
        engine = create_engine(settings.DATABASE_URL)
        
        # Create all tables
        Base.metadata.create_all(engine)
        
        logger.info("✅ New tables created successfully!")
        
        # Insert default message type styles
        Session = sessionmaker(bind=engine)
        session = Session()
        
        # Default message type styles
        default_styles = [
            {
                'message_type': 'business',
                'writing_style': 'professional',
                'tone': 'formal',
                'personality_traits': {'professional': True, 'solution-oriented': True},
                'response_rules': ['Be concise and professional', 'Focus on solutions', 'Use formal language'],
                'max_length': 300
            },
            {
                'message_type': 'personal',
                'writing_style': 'conversational',
                'tone': 'friendly',
                'personality_traits': {'friendly': True, 'warm': True},
                'response_rules': ['Be warm and friendly', 'Show personal interest', 'Use casual language'],
                'max_length': 400
            },
            {
                'message_type': 'support',
                'writing_style': 'helpful',
                'tone': 'patient',
                'personality_traits': {'helpful': True, 'patient': True},
                'response_rules': ['Be patient and helpful', 'Provide clear solutions', 'Show empathy'],
                'max_length': 350
            },
            {
                'message_type': 'networking',
                'writing_style': 'professional',
                'tone': 'engaging',
                'personality_traits': {'professional': True, 'engaging': True},
                'response_rules': ['Be professional but engaging', 'Show interest in connection', 'Be concise'],
                'max_length': 250
            },
            {
                'message_type': 'sales',
                'writing_style': 'persuasive',
                'tone': 'enthusiastic',
                'personality_traits': {'enthusiastic': True, 'persuasive': True},
                'response_rules': ['Be enthusiastic about value', 'Focus on benefits', 'Include call to action'],
                'max_length': 300
            }
        ]
        
        # Insert default styles
        for style_data in default_styles:
            existing = session.query(MessageTypeStyle).filter_by(
                message_type=style_data['message_type']
            ).first()
            
            if not existing:
                style = MessageTypeStyle(**style_data)
                session.add(style)
                logger.info(f"✅ Added default style for {style_data['message_type']} messages")
        
        # Create default web search configuration
        existing_web_config = session.query(WebSearchConfiguration).first()
        if not existing_web_config:
            web_config = WebSearchConfiguration()
            session.add(web_config)
            logger.info("✅ Added default web search configuration")
        
        session.commit()
        session.close()
        
        logger.info("✅ Migration completed successfully!")
        
    except Exception as e:
        logger.error(f"❌ Error during migration: {e}")


class AnsweringAgent:
    """Main application class that orchestrates the answering agent"""
    
    def __init__(self):
        self.platform_manager = PlatformManager()
        self.running = False
        self.message_polling_thread = None
        
    def start(self):
        """Start the answering agent"""
        logger.info("Starting Answering Agent...")
        
        try:
            # Run database migration for enhanced features
            logger.info("Running database migration for enhanced features...")
            create_new_tables()
            
            # Connect to all platforms
            logger.info("Connecting to platforms...")
            connection_results = self.platform_manager.connect_all()
            
            for platform, connected in connection_results.items():
                status = "✅ Connected" if connected else "❌ Failed"
                logger.info(f"{platform.title()}: {status}")
            
            # Start message polling in a separate thread
            self.running = True
            self.message_polling_thread = Thread(target=self._poll_messages, daemon=True)
            self.message_polling_thread.start()
            
            logger.info("Answering Agent started successfully!")
            logger.info(f"Mode: {settings.APP_MODE}")
            
            # Start the Telegram bot
            logger.info("Starting Telegram bot...")
            bot.run()
            
        except KeyboardInterrupt:
            logger.info("Received interrupt signal, shutting down...")
            self.stop()
        except Exception as e:
            logger.error(f"Error starting Answering Agent: {e}")
            self.stop()
    
    def stop(self):
        """Stop the answering agent"""
        logger.info("Stopping Answering Agent...")
        self.running = False
        
        if settings.APP_MODE == "local":
            # Clear local storage
            try:
                db = db_manager.get_session()
                message_manager = MessageManager(db)
                message_manager.clear_local_storage()
                db_manager.close_session(db)
                logger.info("Local storage cleared")
            except Exception as e:
                logger.error(f"Error clearing local storage: {e}")
        
        logger.info("Answering Agent stopped")
    
    def _poll_messages(self):
        """Poll for new messages from all platforms"""
        logger.info("Starting message polling...")
        
        while self.running:
            try:
                # Get messages from all platforms
                messages = self.platform_manager.get_all_messages()
                
                if messages:
                    # Process new messages
                    db = db_manager.get_session()
                    message_manager = MessageManager(db)
                    
                    for message_data in messages:
                        try:
                            # Add message to database
                            message = message_manager.add_message(
                                platform=message_data["platform"],
                                sender=message_data["sender"],
                                content=message_data["content"]
                            )
                                    
                            # Notify via Telegram (using a new event loop for the thread)
                            try:
                                loop = asyncio.new_event_loop()
                                asyncio.set_event_loop(loop)
                                loop.run_until_complete(bot.notify_new_message(
                                    platform=message_data["platform"],
                                    sender=message_data["sender"],
                                    content=message_data["content"]
                                ))
                                loop.close()
                            except Exception as e:
                                logger.error(f"Error sending Telegram notification: {e}")
                            
                            logger.info(f"New message from {message_data['platform']}: {message_data['sender']}")
                            
                        except Exception as e:
                            logger.error(f"Error processing message: {e}")
                    
                    db_manager.close_session(db)
                
                # Wait before next poll
                time.sleep(30)  # Poll every 30 seconds
                
            except Exception as e:
                logger.error(f"Error in message polling: {e}")
                time.sleep(60)  # Wait longer on error
    
    def get_status(self) -> dict:
        """Get current status of the agent"""
        return {
            "running": self.running,
            "mode": settings.APP_MODE,
            "platforms": self.platform_manager.get_connection_status(),
            "database": "connected" if db_manager.engine else "disconnected"
        }


def signal_handler(signum, frame):
    """Handle shutdown signals"""
    logger.info(f"Received signal {signum}, shutting down...")
    if hasattr(signal_handler, 'agent'):
        signal_handler.agent.stop()
    sys.exit(0)


def main():
    """Main entry point"""
    print("🤖 Answering Agent - AI-Powered Message Management")
    print("=" * 50)
    
    # Setup signal handlers
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    # Create and start the agent
    agent = AnsweringAgent()
    signal_handler.agent = agent  # Store reference for signal handler
    
    try:
        agent.start()
    except Exception as e:
        logger.error(f"Fatal error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
