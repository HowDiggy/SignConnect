from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from src.signconnect.db import models

# Note: We no longer need to import `app` or `get_current_user` here,
# and we've removed the global mock setup.

def test_create_user_on_first_preference(
    authenticated_client: TestClient, db_session: Session
):
    """
    GIVEN a user exists in Firebase but not the local database,
    WHEN they make a POST request to create their first preference,
    THEN a new user record should be created in the local database.
    """
    # ARRANGE: Define the data for the new preference
    preference_data = {
        "preference_text": "I prefer a friendly and casual tone.",
    }

    # ACT: Make a POST request using the authenticated client
    response = authenticated_client.post("/users/me/preferences/", json=preference_data)

    # ASSERT (Part 1): Check that the API call was successful
    assert response.status_code == 200, response.text

    # ASSERT (Part 2): Verify the user was actually created in the database
    user_in_db = db_session.query(models.User).filter(
        models.User.email == "newuser@example.com"
    ).first()

    assert user_in_db is not None
    assert user_in_db.email == "newuser@example.com"