import uuid
from sqlalchemy.orm import Session
from .db import models
from . import  schemas

def get_user(db: Session, user_id: uuid.UUID) -> models.User | None:
    """
    Retrieve a user by ID.
    :param db:
    :param user_id:
    :return:
    """
    return db.query(models.User).filter(models.User.id == user_id).first()

def get_user_by_email(db: Session, email: str) -> models.User | None:
    """
    Retrieve a user by email.
    :param db:
    :param email:
    :return:
    """
    return db.query(models.User).filter(models.User.email == email).first()


def get_user_preferences(db: Session, user_id: uuid.UUID, skip: int = 0, limit: int = 100) -> list[models.UserPreference]:
    """
    Retrieves all preferences for a specific user.

    :param db:
    :param user_id:
    :param skip:
    :param limit:
    :return:
    """
    return db.query(models.UserPreference).filter(models.UserPreference.user_id == user_id).offset(skip).limit(limit).all()

def create_conversation_turn(db: Session, turn: schemas.ConversationTurnCreate, user_id: uuid.UUID) -> models.ConversationTurn:
    """
    Creates a new conversation turn record for a user.
    :param db:
    :param turn:
    :param user_id:
    :return:
    """

    # this function assumes a conversation model exists and you'd link to it.
    # for now, let's simplify and link directly to the user.
    db_turn = models.ConversationTurn(**turn.model_dump(), owner_id=user_id)
    db.add(db_turn)
    db.commit()
    db.refresh(db_turn)
    return db_turn


def create_user_preference(db: Session, preference: schemas.UserPreferenceCreate, user_id: uuid.UUID) -> models.UserPreference:
    """
    Creates a new user preference record for a user.
    :param db:
    :param preference:
    :param user_id:
    :return:
    """
    db_preference = models.UserPreference(**preference.model_dump(), user_id=user_id)
    db.add(db_preference)
    db.commit()
    db.refresh(db_preference)
    return db_preference