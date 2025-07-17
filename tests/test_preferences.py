from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from src.signconnect.db import models

# No more global variables, no more manual setup, no more 'app' imports.
# All setup is handled by the fixtures from conftest.py.

def test_create_user_on_first_preference(
    authenticated_client: TestClient, 
    db_session: Session
):
    """
    GIVEN a user is authenticated via Firebase but not in the local DB,
    WHEN they create their first preference,
    THEN a new user record should be created in the database,
    AND the new preference should be returned successfully.
    """
    # ARRANGE Part 1: Verify the user is NOT in the database yet.
    # The `authenticated_client` fixture provides the mocked user info.
    user_in_db = db_session.query(models.User).filter(
        models.User.firebase_uid == "fake-firebase-uid-123"
    ).first()
    assert user_in_db is None, "User should not exist before the API call."

    # ARRANGE Part 2: Define the preference data to be sent.
    preference_data = {
        "preference_text": "Please use a formal and respectful tone in suggestions.",
    }

    # ACT: Make the API call using the pre-authenticated client.
    response = authenticated_client.post(
        "/users/me/preferences/", 
        json=preference_data
    )

    # ASSERT Part 1: Check the API response.
    assert response.status_code == 200, response.text
    response_data = response.json()
    assert response_data["preference_text"] == preference_data["preference_text"]
    assert "id" in response_data, "Response should contain the new preference ID."

    # ASSERT Part 2: Verify the user was created in the database.
    user_in_db = db_session.query(models.User).filter(
        models.User.firebase_uid == "fake-firebase-uid-123"
    ).one_or_none() # .one_or_none() is stricter and good for tests
    assert user_in_db is not None, "User should have been created in the database."
    assert user_in_db.email == "newuser@example.com"
    print(f"\nSUCCESS: User '{user_in_db.email}' was created with ID: {user_in_db.id}")

    # ASSERT Part 3: Verify the preference was linked to the new user.
    assert response_data["user_id"] == str(user_in_db.id)