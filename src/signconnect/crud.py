import uuid

from sqlalchemy.orm import Session
from signconnect.db import models
from signconnect import  schemas
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
    db_turn = models.ConversationTurn(**turn.dict(), owner_id=user_id)
    db.add(db_turn)
    db.commit()
    db.refresh(db_turn)
    return db_turn