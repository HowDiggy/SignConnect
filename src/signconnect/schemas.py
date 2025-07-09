from pydantic import BaseModel, ConfigDict
import uuid
from datetime import datetime
from typing import List

# ------- Conversation Schemas ----------
class ConversationTurnBase(BaseModel):
    transcribed_text: str


class ConversationTurnCreate(ConversationTurnBase):
    pass


class ConversationTurn(ConversationTurnBase):
    id: uuid.UUID
    timestamp: datetime

    model_config = ConfigDict(from_attributes=True)


class ConversationBase(BaseModel):
    pass


class ConversationCreate(ConversationBase):
    pass


class Conversation(ConversationBase):
    id: uuid.UUID
    start_time: datetime
    turns: List[ConversationTurn] = []

    model_config = ConfigDict(from_attributes=True)


# ----------- User Schemas ---------

class UserBase(BaseModel):
    email: str
    username: str

class User(UserBase):
    id: uuid.UUID
    is_active: bool
    conversations: List[Conversation] = []

    model_config = ConfigDict(from_attributes=True)