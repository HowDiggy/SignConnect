# src/signconnect/db/models.py
# SQLAlchemy database models

import uuid
import datetime
from sqlalchemy import Column, String, DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from datetime import timezone

from signconnect.db.database import Base

class User(Base):
    """
    User model representing the users table.
    """

    __tablename__ = "users"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    username = Column(String, unique=True, index=True, nullable=False)
    email = Column(String, unique=True, index=True, nullable=False)
    password_hash = Column(String, nullable=False)
    created_at = Column(DateTime, default=lambda: datetime.datetime.now(timezone.utc)) # lambda function ensures time
    # is calculated every time a new row is created, rather than just once when the applications starts

    conversations = relationship("Conversation", back_populates="user")

class Conversation(Base):
    """
    Conversation model representing a single communication session.
    """

    __tablename__ = "conversations"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    start_time = Column(DateTime, default=lambda: datetime.datetime.now(timezone.utc))

    user = relationship("User", back_populates="conversations")
    turns = relationship("ConversationTurn", back_populates="conversation")

class ConversationTurn(Base):
    """
    ConversationTurn model representing a single turn in a conversation.
    """

    __tablename__ = "conversation_turns"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    conversation_id = Column(UUID(as_uuid=True), ForeignKey("conversations.id"), nullable=False)
    transcribed_text = Column(String, nullable=False)
    timestamp = Column(DateTime, default=lambda: datetime.datetime.now(timezone.utc))

    conversation = relationship("Conversation", back_populates="turns")