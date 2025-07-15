from __future__ import annotations
from pydantic import BaseModel, ConfigDict
import uuid
from datetime import datetime
from typing import List, Optional

# --- ScenarioQuestion Schemas ---
class ScenarioQuestionBase(BaseModel):
    question_text: str
    user_answer_text: str

class ScenarioQuestionCreate(ScenarioQuestionBase):
    pass

class ScenarioQuestion(ScenarioQuestionBase):
    id: uuid.UUID
    scenario_id: uuid.UUID
    model_config = ConfigDict(from_attributes=True)

class ScenarioQuestionUpdate(BaseModel):
    question_text: Optional[str] = None
    user_answer_text: Optional[str] = None


# --- Scenario Schemas ---
class ScenarioBase(BaseModel):
    name: str
    description: Optional[str] = None

class ScenarioCreate(ScenarioBase):
    pass

class Scenario(ScenarioBase):
    id: uuid.UUID
    questions: List[ScenarioQuestion] = []
    model_config = ConfigDict(from_attributes=True)


# --- ConversationTurn Schemas ---
class ConversationTurnBase(BaseModel):
    transcribed_text: str

class ConversationTurnCreate(ConversationTurnBase):
    pass

class ConversationTurn(ConversationTurnBase):
    id: uuid.UUID
    timestamp: datetime
    model_config = ConfigDict(from_attributes=True)


# --- Conversation Schemas ---
class ConversationBase(BaseModel):
    pass

class ConversationCreate(ConversationBase):
    pass

class Conversation(ConversationBase):
    id: uuid.UUID
    start_time: datetime
    turns: List['ConversationTurn'] = []
    model_config = ConfigDict(from_attributes=True)


# --- Preference Schemas ---
class UserPreferenceBase(BaseModel):
    category: str
    preference_text: str

class UserPreferenceCreate(UserPreferenceBase):
    pass

class UserPreference(UserPreferenceBase):
    id: uuid.UUID
    user_id: uuid.UUID
    model_config = ConfigDict(from_attributes=True)


# --- User Schemas ---
class UserBase(BaseModel):
    email: str
    username: str

class UserCreate(UserBase):
    password: str

class User(UserBase):
    id: uuid.UUID
    is_active: bool
    conversations: List['Conversation'] = []
    preferences: List['UserPreference'] = []
    scenarios: List['Scenario'] = []
    model_config = ConfigDict(from_attributes=True)


# Manually trigger the resolution of the forward references
User.model_rebuild()
Conversation.model_rebuild()
UserPreference.model_rebuild()
Scenario.model_rebuild()