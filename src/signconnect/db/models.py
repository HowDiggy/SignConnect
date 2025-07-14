# src/signconnect/db/models.py
# SQLAlchemy database models

import uuid
import datetime
from sqlalchemy import Column, String, DateTime, ForeignKey, Boolean
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from datetime import timezone
from pgvector.sqlalchemy import Vector

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
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=lambda: datetime.datetime.now(timezone.utc)) # lambda function ensures time
    # is calculated every time a new row is created, rather than just once when the applications starts

    conversations = relationship("Conversation", back_populates="user")
    preferences = relationship("UserPreference", back_populates="owner")
    scenarios = relationship("Scenario", back_populates="owner")
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

class UserPreference(Base):
    """
    Model for storing user-specific preferences.
    """
    __tablename__ = "user_preferences"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    category = Column(String, index=True, nullable=False)
    preference_text = Column(String, nullable=False)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)

    owner = relationship("User", back_populates="preferences")

class Scenario(Base):
    """
    Model for a communication scenario, like "Restaurant" or "Doctor's Office".
    """
    __tablename__ = "scenarios"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String, nullable=False)
    description = Column(String)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)

    owner = relationship("User", back_populates="scenarios")
    questions = relationship(
        "ScenarioQuestion",
        back_populates="scenario",
        cascade="all, delete-orphan",
    )


class ScenarioQuestion(Base):
    """
    Model for a specific question within a scenario.
    """
    __tablename__ = "scenario_questions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    question_text = Column(String, nullable=False)
    user_answer_text = Column(String, nullable=False)
    # The vector embedding for the question text. The number (384) is the
    # dimension of the embeddings produced by our chosen model.
    question_embedding = Column(Vector(384))
    scenario_id = Column(UUID(as_uuid=True), ForeignKey("scenarios.id"), nullable=False)

    scenario = relationship("Scenario", back_populates="questions")
