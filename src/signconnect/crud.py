# src/signconnect/crud.py

import uuid
import structlog
from sqlalchemy.orm import Session
from sentence_transformers import SentenceTransformer
from .db import models
from . import schemas

# ---- Model for Sentence Transformers ----
# Load the model once the application starts.
# 'all-MiniLM-L6-v2' is a great, lightweight model for this purpose.
embedding_model = SentenceTransformer("all-MiniLM-L6-v2")

logger = structlog.get_logger(__name__)


# --- User CRUD ---


def get_user(db: Session, user_id: uuid.UUID) -> models.User | None:
    """
    Retrieve a user by ID.
    :param db:
    :param user_id:
    :return:
    """
    logger.info("Fetching user by ID.", user_id=user_id)
    user = db.query(models.User).filter(models.User.id == user_id).first()
    if user:
        logger.info("User found.", user_id=user_id)
    else:
        logger.warning("User not found.", user_id=user_id)
    return user


def get_user_by_email(db: Session, email: str) -> models.User | None:
    """
    Retrieve a user by email.
    :param db:
    :param email:
    :return:
    """
    logger.info("Fetching user by email.", email=email)
    user = db.query(models.User).filter(models.User.email == email).first()
    if user:
        logger.info("User found by email.", email=email)
    else:
        logger.warning("User not found by email.", email=email)
    return user


# --- User Preference CRUD ---


def get_user_preferences(
    db: Session, user_id: uuid.UUID, skip: int = 0, limit: int = 100
) -> list[models.UserPreference]:
    """
    Retrieves all preferences for a specific user.

    :param db:
    :param user_id:
    :param skip:
    :param limit:
    :return:
    """
    logger.info("Fetching user preferences.", user_id=user_id, skip=skip, limit=limit)
    preferences = (
        db.query(models.UserPreference)
        .filter(models.UserPreference.user_id == user_id)
        .offset(skip)
        .limit(limit)
        .all()
    )
    logger.info(f"Found {len(preferences)} preferences for user.", user_id=user_id)
    return preferences


def create_user(db: Session, user: schemas.UserCreate) -> models.User:
    """
    Creates a user in our local DB to sync with Firebase.
    Password is a placeholder as Firebase handles real auth.
    """
    # Use a simple placeholder hash. No security functions needed.
    placeholder_hash = "firebase_auth_user"
    db_user = models.User(
        email=user.email,
        username=user.username,
        password_hash=placeholder_hash,
        firebase_uid=user.firebase_uid,
        is_active=True,
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    logger.info("Created new user.", user_id=db_user.id, email=db_user.email)
    return db_user


def create_user_preference(
    db: Session, preference: schemas.UserPreferenceCreate, user_id: uuid.UUID
) -> models.UserPreference:
    """
    Creates a user preference in our local DB.
    :param db:
    :param preference:
    :param user_id:
    :return:
    """
    db_preference = models.UserPreference(**preference.model_dump(), user_id=user_id)
    db.add(db_preference)
    db.commit()
    db.refresh(db_preference)
    logger.info(
        "Created new user preference.", preference_id=db_preference.id, user_id=user_id
    )
    return db_preference


# --- Conversation Turn CRUD ---
def create_conversation_turn(
    db: Session, turn: schemas.ConversationTurnCreate, user_id: uuid.UUID
) -> models.ConversationTurn:
    """
    Creates a new conversation turn record for a user.
    :param db:
    :param turn:
    :param user_id:
    :return:
    """

    # this function assumes a conversation model exists and you'd link to it.
    # for now, let's simplify and link directly to the user.
    db_turn = models.ConversationTurn(**turn.model_dump(), user_id=user_id)
    db.add(db_turn)
    db.commit()
    db.refresh(db_turn)
    logger.info("Created new conversation turn.", turn_id=db_turn.id, user_id=user_id)
    return db_turn


# --- Scenario and ScenarioQuestion CRUD ---


def create_scenario(
    db: Session, scenario: schemas.ScenarioCreate, user_id: uuid.UUID
) -> models.Scenario:
    """
    Creates a new scenario record for a user.
    :param db:
    :param scenario:
    :param user_id:
    :return:
    """

    db_scenario = models.Scenario(**scenario.model_dump(), user_id=user_id)
    db.add(db_scenario)
    db.commit()
    db.refresh(db_scenario)
    logger.info("Created new scenario.", scenario_id=db_scenario.id, user_id=user_id)
    return db_scenario


def create_scenario_question(
    db: Session, question: schemas.ScenarioQuestionCreate, scenario_id: uuid.UUID
) -> models.ScenarioQuestion:
    """
    Creates a new question within a scenario and generates its vector embedding.

    :param db:
    :param question:
    :param scenario_id:
    :return:
    """

    # Generate the embedding from the question text
    logger.info(
        "Generating embedding for new scenario question.",
        question_text=question.question_text,
    )
    embedding = embedding_model.encode(question.question_text)

    db_question = models.ScenarioQuestion(
        **question.model_dump(), scenario_id=scenario_id, question_embedding=embedding
    )
    db.add(db_question)
    db.commit()
    db.refresh(db_question)
    logger.info(
        "Created new scenario question.",
        question_id=db_question.id,
        scenario_id=scenario_id,
    )
    return db_question


def find_similar_question(
    db: Session, query_text: str, user_id: uuid.UUID
) -> models.ScenarioQuestion | None:
    """
    Finds the most similar ScenarioQuestion for a given user based on a query text.

    :param db:
    :param query_text:
    :param user_id:
    :return:
    """

    # Generate the embedding for the incoming transcribed text
    logger.info("Generating embedding for similarity search.", query_text=query_text)
    query_embedding = embedding_model.encode(query_text)

    # Use the l2_distance function from pgvector to find the most similar question.
    # We join across the tables to ensure we only search questions owned by the current user.
    logger.info("Performing similarity search for user.", user_id=user_id)
    similar_question = (
        db.query(models.ScenarioQuestion)
        .join(models.Scenario)
        .filter(models.Scenario.user_id == user_id)
        .order_by(
            models.ScenarioQuestion.question_embedding.l2_distance(query_embedding)
        )
        .first()
    )
    if similar_question:
        logger.info(
            "Found similar question.",
            question_id=similar_question.id,
            question_text=similar_question.question_text,
        )
    else:
        logger.info("No similar question found for user.", user_id=user_id)
    return similar_question
