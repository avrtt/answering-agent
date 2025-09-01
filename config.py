import os
from typing import Optional
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # Telegram Bot Configuration
    TELEGRAM_BOT_TOKEN: Optional[str] = None
    TELEGRAM_CHAT_ID: Optional[str] = None
    
    # OpenAI Configuration
    OPENAI_API_KEY: Optional[str] = None
    OPENAI_MODEL: str = "gpt-4"
    
    # Database Configuration
    DATABASE_URL: str = "sqlite:///./answering_agent.db"
    
    # Redis Configuration (for Celery)
    REDIS_URL: str = "redis://localhost:6379/0"
    
    # Application Mode
    APP_MODE: str = "local"  # "local" or "cloud"
    
    # Social Media API Keys (optional for MVP)
    LINKEDIN_CLIENT_ID: Optional[str] = None
    LINKEDIN_CLIENT_SECRET: Optional[str] = None
    FACEBOOK_ACCESS_TOKEN: Optional[str] = None
    INSTAGRAM_ACCESS_TOKEN: Optional[str] = None
    GMAIL_CREDENTIALS_FILE: Optional[str] = None
    
    # Response Generation Settings
    MAX_RESPONSE_LENGTH: int = 500
    RESPONSE_STYLE: str = "professional"
    
    # Web Search Configuration
    ENABLE_GOOGLE_SEARCH: bool = True
    ENABLE_PERSONAL_INFO_SEARCH: bool = True
    GOOGLE_SEARCH_API_KEY: Optional[str] = None
    GOOGLE_SEARCH_ENGINE_ID: Optional[str] = None
    
    # Personal Information Sources
    PERSONAL_WEBSITE: str = "https://avrtt.github.io/about"
    GITHUB_PROFILE: str = "https://github.com/avrtt"
    LINKEDIN_PROFILE: Optional[str] = None
    TWITTER_PROFILE: Optional[str] = None
    
    # Message Type Detection
    ENABLE_MESSAGE_TYPE_DETECTION: bool = True
    ENABLE_PERSON_SPECIFIC_RESPONSES: bool = True
    
    class Config:
        env_file = ".env"
        case_sensitive = True


# Global settings instance
settings = Settings()
