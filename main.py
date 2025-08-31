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

# Configure logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)


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
                                    
                            # Notify via Telegram
                            asyncio.run(bot.notify_new_message(
                                platform=message_data["platform"],
                                sender=message_data["sender"],
                                content=message_data["content"]
                            ))
                            
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
