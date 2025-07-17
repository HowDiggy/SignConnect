import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from src.signconnect.main import app
from src.signconnect.db import models
from src.signconnect.db.database import get_db, Base
from src.signconnect.db.test_database import engine, TestingSessionLocal

from src.signconnect.dependencies import get_current_user

# --- ARRANGE (Part 1): Mocking the Firebase Dependency ---

# This is our fake user data that the mock will return.
# It simulates a user who is logged into Firebase but doesn't exist in our local DB yet.
FAKE_FIREBASE_USER = {
    "email": "newuser@example.com",
    "name": "New User",
    "uid": "fake-firebase-uid-123",
}


# This function will replace the real `get_current_user` function during our test.
def override_get_current_user():
    return FAKE_FIREBASE_USER


# We apply the mock to our app.
app.dependency_overrides[get_current_user] = override_get_current_user


# --- The Test Function ---

def test_create_user_on_first_preference(authenticated_client: TestClient, db_session: Session):
    """
    GIVEN a user exists in Firebase but not the local database,
    WHEN they make a POST request to create their first preference,
    THEN a new user record should be created in the local database.
    """
    # ARRANGE (Part 2): Define the data for the new preference
    preference_data = {
        "preference_text": "I prefer a friendly and casual tone.",
    }

    # ACT: Make a POST request to the create preference endpoint.
    # The `client` fixture handles the HTTP request, and our mock provides the user.
    response = authenticated_client.post("/users/me/preferences/", json=preference_data)

    # ASSERT (Part 1): Check that the API call was successful.
    assert response.status_code == 200, response.text

    # ASSERT (Part 2): Verify the user was actually created in the database.
    # We query our test database directly to confirm the side-effect.
    user_in_db = db_session.query(models.User).filter(
        models.User.email == FAKE_FIREBASE_USER["email"]
    ).first()

    assert user_in_db is not None
    assert user_in_db.email == FAKE_FIREBASE_USER["email"]