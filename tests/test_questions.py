# tests/test_questions.py

import uuid
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from signconnect import crud, schemas
from signconnect.db import models

"""
----- Test POST -----
"""
def test_create_question_for_scenario(
        authenticated_client: TestClient,
        db_session: Session
):
    """
    GIVEN an authenticated user with an existing scenario,
    WHEN they make a POST request to add a question to that scenario,
    THEN the question should be created in the database and linked to the scenario.
    """
    # ARRANGE: Create a user and a parent scenario.
    user = crud.create_user(db_session, schemas.UserCreate(
        email="newuser@example.com",
        username="New User",
        password="password",
        firebase_uid="fake-firebase-uid-123"
    ))
    parent_scenario = crud.create_scenario(
        db=db_session,
        scenario=schemas.ScenarioCreate(name="Test Scenario", description="A test"),
        user_id=user.id
    )

    # Define the data for the new question.
    question_data = {
        "question_text": "What is the daily special?",
        "user_answer_text": "The daily special is chicken soup."
    }

    # ACT: Make the POST request to the nested endpoint.
    response = authenticated_client.post(
        f"/api/users/me/scenarios/{parent_scenario.id}/questions/",
        json=question_data
    )

    # ASSERT Part 1: Check the API response.
    assert response.status_code == 200, response.text
    response_data = response.json()
    assert response_data["question_text"] == question_data["question_text"]
    assert "id" in response_data

    # ASSERT Part 2: Verify the question was saved to the database.
    question_id = response_data["id"]
    db_question = db_session.query(models.ScenarioQuestion).filter(
        models.ScenarioQuestion.id == uuid.UUID(question_id)).one_or_none()

    assert db_question is not None
    assert db_question.user_answer_text == "The daily special is chicken soup."

    # ASSERT Part 3: Verify the question is linked to the correct scenario.
    assert db_question.scenario_id == parent_scenario.id


"""
----- Testing the unhappy path -----

"""

def test_cannot_create_question_for_another_users_scenario(
        authenticated_client: TestClient,
        db_session: Session
):
    """
    GIVEN User A is authenticated, and a scenario exists that belongs to User B,
    WHEN User A tries to POST a question to User B's scenario,
    THEN the API should return a 403 Forbidden error.
    """
    # ARRANGE Part 1: Create two separate users.
    # User A is the one making the request (from the authenticated_client fixture).
    user_a = crud.create_user(db_session, schemas.UserCreate(
        email="newuser@example.com",
        username="User A",
        password="password",
        firebase_uid="fake-firebase-uid-123"  # This matches the mock
    ))

    # User B is the owner of the scenario.
    user_b = crud.create_user(db_session, schemas.UserCreate(
        email="userb@example.com",
        username="User B",
        password="password",
        firebase_uid="some-other-uid-456"
    ))

    # ARRANGE Part 2: Create a scenario owned by User B.
    scenario_owned_by_b = crud.create_scenario(
        db=db_session,
        scenario=schemas.ScenarioCreate(name="User B's Private Scenario", description="A test"),
        user_id=user_b.id
    )

    # ARRANGE Part 3: Define the question data User A will try to add.
    question_data = {
        "question_text": "Trying to add this to your scenario!",
        "user_answer_text": "This should not work."
    }

    # ACT: Make the POST request as User A to User B's scenario.
    response = authenticated_client.post(
        f"/api/users/me/scenarios/{scenario_owned_by_b.id}/questions/",
        json=question_data
    )

    # ASSERT: The request should be forbidden.
    # Your endpoint correctly returns 403, which is "Forbidden".
    assert response.status_code == 403
    assert "Not authorized" in response.json()["detail"]


"""
--------------------
"""

def test_update_question(
    authenticated_client: TestClient,
    db_session: Session
):
    """
    GIVEN an authenticated user with an existing question,
    WHEN they make a PUT request to update that question,
    THEN the question's text should be updated in the database.
    """
    # ARRANGE: Create a user, a scenario, and a question to update.
    user = crud.create_user(db_session, schemas.UserCreate(
        email="newuser@example.com",
        username="New User",
        password="password",
        firebase_uid="fake-firebase-uid-123"
    ))
    scenario = crud.create_scenario(
        db=db_session,
        scenario=schemas.ScenarioCreate(name="Test Scenario", description="A test"),
        user_id=user.id
    )
    initial_question = crud.create_scenario_question(
        db=db_session,
        question=schemas.ScenarioQuestionCreate(
            question_text="Old Question",
            user_answer_text="Old Answer"
        ),
        scenario_id=scenario.id
    )

    # Define the update payload.
    update_data = {
        "question_text": "This is the updated question text.",
        "user_answer_text": "This is the updated answer."
    }

    # ACT: Make the PUT request to the question's direct endpoint.
    response = authenticated_client.put(
        f"/api/users/me/questions/{initial_question.id}",
        json=update_data
    )

    # ASSERT Part 1: Check the API response.
    assert response.status_code == 200
    response_data = response.json()
    assert response_data["question_text"] == update_data["question_text"]

    # ASSERT Part 2: Verify the change was saved to the database.
    # We refresh the original object to get its new state from the DB.
    db_session.refresh(initial_question)
    assert initial_question.question_text == "This is the updated question text."
    assert initial_question.user_answer_text == "This is the updated answer."


def test_cannot_update_another_users_question(
    authenticated_client: TestClient,
    db_session: Session
):
    """
    GIVEN User A is authenticated and a question belongs to User B,
    WHEN User A tries to PUT an update to User B's question,
    THEN the API should return a 404 Not Found error.
    """
    # ARRANGE: Create two users and a question owned by User B.
    # User A is from the authenticated_client fixture.
    crud.create_user(db_session, schemas.UserCreate(
        email="newuser@example.com",
        username="User A",
        password="password",
        firebase_uid="fake-firebase-uid-123"
    ))
    user_b = crud.create_user(db_session, schemas.UserCreate(
        email="userb@example.com",
        username="User B",
        password="password",
        firebase_uid="some-other-uid-456"
    ))
    scenario_b = crud.create_scenario(
        db=db_session,
        scenario=schemas.ScenarioCreate(name="User B's Scenario"),
        user_id=user_b.id
    )
    question_b = crud.create_scenario_question(
        db=db_session,
        question=schemas.ScenarioQuestionCreate(
            question_text="User B's Question",
            user_answer_text="An answer"
        ),
        scenario_id=scenario_b.id
    )

    update_data = {"question_text": "Attempted update"}

    # ACT: User A attempts to update User B's question.
    response = authenticated_client.put(
        f"/api/users/me/questions/{question_b.id}",
        json=update_data
    )

    # ASSERT: The API should respond with 404 Not Found.
    # We use 404 here because, from User A's perspective, the resource
    # they are trying to access does not exist. This prevents leaking
    # information about what other users' resources might exist.
    assert response.status_code == 404


"""
-----------------------
"""

def test_delete_question(
    authenticated_client: TestClient,
    db_session: Session
):
    """
    GIVEN an authenticated user with an existing question,
    WHEN they make a DELETE request for that question,
    THEN the question should be removed from the database.
    """
    # ARRANGE: Create a user, scenario, and a question to delete.
    user = crud.create_user(db_session, schemas.UserCreate(
        email="newuser@example.com",
        username="New User",
        password="password",
        firebase_uid="fake-firebase-uid-123"
    ))
    scenario = crud.create_scenario(
        db=db_session,
        scenario=schemas.ScenarioCreate(name="Test Scenario"),
        user_id=user.id
    )
    question_to_delete = crud.create_scenario_question(
        db=db_session,
        question=schemas.ScenarioQuestionCreate(
            question_text="Delete Me",
            user_answer_text="An answer"
        ),
        scenario_id=scenario.id
    )
    question_id = question_to_delete.id

    # Verify it exists in the database before the call.
    assert db_session.query(models.ScenarioQuestion).filter(models.ScenarioQuestion.id == question_id).one_or_none() is not None

    # ACT: Make the DELETE request to the question's endpoint.
    response = authenticated_client.delete(f"/api/users/me/questions/{question_id}")

    # ASSERT Part 1: Check the API response.
    assert response.status_code == 200

    # ASSERT Part 2: Verify the question was truly deleted from the database.
    db_question = db_session.query(models.ScenarioQuestion).filter(models.ScenarioQuestion.id == question_id).one_or_none()
    assert db_question is None


def test_cannot_delete_another_users_question(
    authenticated_client: TestClient,
    db_session: Session
):
    """
    GIVEN User A is authenticated and a question belongs to User B,
    WHEN User A tries to DELETE User B's question,
    THEN the API should return a 404 Not Found error.
    """
    # ARRANGE: Create two users and a question owned by User B.
    crud.create_user(db_session, schemas.UserCreate(
        email="newuser@example.com",
        username="User A",
        password="password",
        firebase_uid="fake-firebase-uid-123"
    ))
    user_b = crud.create_user(db_session, schemas.UserCreate(
        email="userb@example.com",
        username="User B",
        password="password",
        firebase_uid="some-other-uid-456"
    ))
    scenario_b = crud.create_scenario(
        db=db_session,
        scenario=schemas.ScenarioCreate(name="User B's Scenario"),
        user_id=user_b.id
    )
    question_b = crud.create_scenario_question(
        db=db_session,
        question=schemas.ScenarioQuestionCreate(
            question_text="User B's Question",
            user_answer_text="An answer"
        ),
        scenario_id=scenario_b.id
    )

    # ACT: User A attempts to delete User B's question.
    response = authenticated_client.delete(f"/api/users/me/questions/{question_b.id}")

    # ASSERT: The API should respond with 404 Not Found to prevent leaking information.
    assert response.status_code == 404