import uuid
from sqlalchemy.orm import Session
from sentence_transformers import SentenceTransformer
from .db import models
from . import schemas, db

# ---- Model for Sentence Transformers ----
# Load the model once the application starts.
# 'all-MiniLM-L6-v2' is a great, lightweight model for this purpose.
embedding_model = SentenceTransformer('all-MiniLM-L6-v2')


# --- User CRUD ---

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

# --- User Preference CRUD ---

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
        is_active=True
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user

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

# --- Conversation Turn CRUD ---
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
    db_turn = models.ConversationTurn(**turn.model_dump(), user_id=user_id)
    db.add(db_turn)
    db.commit()
    db.refresh(db_turn)
    return db_turn


# --- Scenario and ScenarioQuestion CRUD ---

def create_scenario(db: Session, scenario: schemas.ScenarioCreate, user_id: uuid.UUID) -> models.Scenario:
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
    return db_scenario

def create_scenario_question(db: Session, question: schemas.ScenarioQuestionCreate, scenario_id: uuid.UUID) -> models.ScenarioQuestion:
    """
    Creates a new question within a scenario and generates its vector embedding.

    :param db:
    :param question:
    :param scenario_id:
    :return:
    """

    # Generate the embedding from the question text
    embedding = embedding_model.encode(question.question_text)

    db_question = models.ScenarioQuestion(
        **question.model_dump(),
        scenario_id=scenario_id,
        question_embedding=embedding
    )
    db.add(db_question)
    db.commit()
    db.refresh(db_question)
    return db_question

def find_similar_question(db: Session, query_text: str, user_id: uuid.UUID) -> models.ScenarioQuestion | None:
    """
    Finds the most similar ScenarioQuestion for a given user based on a query text.

    :param db:
    :param query_text:
    :param user_id:
    :return:
    """

    # Generate the embedding for the incoming transcribed text
    query_embedding = embedding_model.encode(query_text)

    # Use the l2_distance function from pgvector to find the most similar question.
    # We join across the tables to ensure we only search questions owned by the current user.
    similar_question = (
        db.query(models.ScenarioQuestion)
        .join(models.Scenario)
        .filter(models.Scenario.user_id == user_id)
        .order_by(models.ScenarioQuestion.question_embedding.l2_distance(query_embedding))
        .first()
    )
    return similar_question

# --- helper functions for security and data integrity of endpoints ---
def get_scenario(db: Session, scenario_id: uuid.UUID) -> models.Scenario | None:
    """
    Retrieves a single scenario by its ID.

    :param db:
    :param scenario_id:
    :return:
    """
    return db.query(models.Scenario).filter(models.Scenario.id == scenario_id).first()

def get_scenario_by_name(db: Session, name: str, user_id: uuid.UUID) -> models.Scenario | None:
    """
    Retrieved a scenario by its name for a specific user.

    :param db:
    :param name:
    :param user_id:
    :return:
    """

    return db.query(models.Scenario).filter(
        models.Scenario.name == name,
        models.Scenario.user_id == user_id
    ).first()

def get_scenarios_by_user(db: Session, user_id: uuid.UUID) -> list[models.Scenario]:
    """
    Retrieves all scenarios owned by a specific user.

    :param db:
    :param user_id:
    :return:
    """

    return db.query(models.Scenario).filter(models.Scenario.user_id == user_id).all()

def delete_scenario_by_id(db: Session, *, scenario_id: uuid.UUID, user_id: uuid.UUID) -> models.Scenario | None:
    """
    Deletes a scenario by its ID, but only if it belongs to the specified user.
    """
    # This logic remains the same
    scenario_to_delete = db.query(models.Scenario).filter(models.Scenario.id == scenario_id).first()

    if not scenario_to_delete or scenario_to_delete.user_id != user_id:
        return None

    db.delete(scenario_to_delete)
    db.commit()

    return scenario_to_delete

def delete_question_by_id(db: Session, *, question_id: uuid.UUID, user_id: uuid.UUID) -> models.ScenarioQuestion | None:
    """
    Deletes a ScenarioQuestion by its ID.

    Ensures that the question belongs to a scenario owned by the specified user
    to prevent unauthorized deletions.
    """
    # Query for the question and join with the scenario to check the owner
    question_to_delete = (
        db.query(models.ScenarioQuestion)
        .join(models.Scenario, models.ScenarioQuestion.scenario_id == models.Scenario.id)
        .filter(
            models.ScenarioQuestion.id == question_id,
            models.Scenario.user_id == user_id
        )
        .first()
    )

    if not question_to_delete:
        # The question does not exist or does not belong to the user
        return None

    db.delete(question_to_delete)
    db.commit()

    return question_to_delete