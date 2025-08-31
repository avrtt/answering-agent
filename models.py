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
