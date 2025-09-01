from sqlalchemy import Column, Integer, String, Text, DateTime, Boolean, ForeignKey, JSON
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from datetime import datetime
import uuid

Base = declarative_base()


class Message(Base):
    __tablename__ = "messages"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    platform = Column(String, nullable=False)  # "linkedin", "telegram", "facebook", "instagram", "gmail"
    sender = Column(String, nullable=False)
    content = Column(Text, nullable=False)
    timestamp = Column(DateTime, default=datetime.utcnow)
    is_answered = Column(Boolean, default=False)
    is_ignored = Column(Boolean, default=False)
    status = Column(String, default="pending")  # "pending", "processing", "answered", "ignored"
    message_type = Column(String, default="general")  # "general", "business", "personal", "support", "networking", "sales"
    
    # Relationships
    responses = relationship("Response", back_populates="message")


class Response(Base):
    __tablename__ = "responses"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    message_id = Column(String, ForeignKey("messages.id"))
    content = Column(Text, nullable=False)
    generated_at = Column(DateTime, default=datetime.utcnow)
    is_sent = Column(Boolean, default=False)
    sent_at = Column(DateTime, nullable=True)
    response_type = Column(String, default="ai")  # "ai", "manual"
    
    # Relationships
    message = relationship("Message", back_populates="responses")


class UserPreferences(Base):
    __tablename__ = "user_preferences"
    
    id = Column(Integer, primary_key=True)
    writing_style = Column(Text, default="professional")
    personality_traits = Column(JSON, default=dict)
    interests = Column(JSON, default=list)
    response_rules = Column(JSON, default=list)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class PlatformCredentials(Base):
    __tablename__ = "platform_credentials"
    
    id = Column(Integer, primary_key=True)
    platform = Column(String, nullable=False)
    credentials = Column(JSON, nullable=False)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class MessageTypeStyle(Base):
    __tablename__ = "message_type_styles"
    
    id = Column(Integer, primary_key=True)
    message_type = Column(String, nullable=False, unique=True)  # "business", "personal", "support", "networking", "sales"
    writing_style = Column(Text, nullable=False)
    tone = Column(String, nullable=False)  # "formal", "casual", "friendly", "professional", "enthusiastic"
    personality_traits = Column(JSON, default=dict)
    response_rules = Column(JSON, default=list)
    max_length = Column(Integer, default=500)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class PersonConfiguration(Base):
    __tablename__ = "person_configurations"
    
    id = Column(Integer, primary_key=True)
    person_name = Column(String, nullable=False)
    person_email = Column(String, nullable=True)
    person_platform_id = Column(String, nullable=True)  # Platform-specific ID
    platform = Column(String, nullable=False)  # "linkedin", "telegram", "facebook", "instagram", "gmail"
    
    # Response customization for this person
    writing_style = Column(Text, nullable=True)
    tone = Column(String, nullable=True)
    personality_traits = Column(JSON, default=dict)
    response_rules = Column(JSON, default=list)
    max_length = Column(Integer, nullable=True)
    
    # Relationship context
    relationship_type = Column(String, default="acquaintance")  # "friend", "colleague", "client", "mentor", "acquaintance"
    conversation_history = Column(JSON, default=list)  # Store recent conversation context
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class WebSearchConfiguration(Base):
    __tablename__ = "web_search_configuration"
    
    id = Column(Integer, primary_key=True)
    
    # Personal information sources
    personal_website = Column(String, default="https://avrtt.github.io/about")
    github_profile = Column(String, default="https://github.com/avrtt")
    linkedin_profile = Column(String, nullable=True)
    twitter_profile = Column(String, nullable=True)
    other_profiles = Column(JSON, default=list)
    
    # Search settings
    enable_google_search = Column(Boolean, default=True)
    enable_personal_info_search = Column(Boolean, default=True)
    search_depth = Column(String, default="moderate")  # "light", "moderate", "deep"
    
    # Personal information cache
    cached_personal_info = Column(JSON, default=dict)
    last_cache_update = Column(DateTime, nullable=True)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
