# tests/integration/test_vector_search.py

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

# Corrected: Import the modules themselves, not specific classes
from src.signconnect import crud, schemas
# Corrected: Import the dependency function to use as a key
from src.signconnect.dependencies import get_current_user

# Mark this test as an integration test
pytestmark = pytest.mark.integration


def test_full_transcription_and_vector_search(
    authenticated_client: TestClient, db_session: Session
):
    """
    An end-to-end test that simulates a user creating scenarios and questions,
    and then uses the vector search to find the most relevant one.

    Args:
        authenticated_client: A TestClient that is pre-authenticated.
        db_session: A database session for setting up test data.
    """
    # ARRANGE
    # 1. Get the mock user's ID from the authenticated client's dependency override
    # Corrected: Use the imported dependency function as the key
    firebase_uid = authenticated_client.user["uid"]

    # 2. FIX: Create the user in the database first to get a real user ID
    user = crud.create_user(db_session, schemas.UserCreate(
        email="testuser@example.com",  # Use a consistent test email
        username="Test User",
        password="password",
        firebase_uid=firebase_uid
    ))

    # 2. Create scenarios and questions in the database
    # Corrected: Use the schemas module to access the Pydantic models
    scenario1 = crud.create_scenario(
        db=db_session,
        user_id=user.id,
        scenario=schemas.ScenarioCreate(name="Coffee Shop Order"),
    )
    crud.create_scenario_question(
        db=db_session,
        scenario_id=scenario1.id,
        question=schemas.ScenarioQuestionCreate(
            question_text="What are your dairy-free milk options?",
            user_answer_text="I'd like to know about your alternative milks.",
            embedding=[0.1, 0.2, 0.3],  # Dummy embedding
        ),
    )

    scenario2 = crud.create_scenario(
        db=db_session,
        user_id=user.id,
        scenario=schemas.ScenarioCreate(name="Doctor's Appointment"),
    )
    crud.create_scenario_question(
        db=db_session,
        scenario_id=scenario2.id,
        question=schemas.ScenarioQuestionCreate(
            question_text="What are the side effects of this medication?",
            user_answer_text="Can you tell me about the side effects?",
            embedding=[0.7, 0.8, 0.9],  # Dummy embedding
        ),
    )
    db_session.commit()

    # 3. Define the new transcript we want to find a match for
    new_transcript = "Tell me about the risks of this treatment."

    # ACT
    # For this integration test, we call the CRUD function directly.
    similar_question = crud.find_similar_question(
        db=db_session, query_text=new_transcript, user_id=user.id
    )

    # ASSERT
    assert similar_question is not None
    assert (
        similar_question.question_text
        == "What are the side effects of this medication?"
    )
    assert similar_question.scenario.name == "Doctor's Appointment"
