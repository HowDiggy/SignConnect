from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from src.signconnect.db import models
from signconnect import crud, schemas
# No more global variables, no more manual setup, no more 'app' imports.
# All setup is handled by the fixtures from conftest.py.
"""
------ Tests CREATE Case -----
"""

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

"""
------ Tests the READ (GET) Case -----
"""

# In tests/test_preferences.py, after the existing test...

def test_read_preferences_for_user_with_no_preferences(
    authenticated_client: TestClient,
    db_session: Session
):
    """
    GIVEN an authenticated user with no preferences,
    WHEN they make a GET request to the preferences endpoint,
    THEN the response should be a 200 OK with an empty list.
    """
    # ARRANGE: Trigger user creation by making an initial API call.
    # The read_user_preferences endpoint is designed to create a user if one doesn't exist.
    authenticated_client.get("/users/me/preferences/")

    # ACT: Make the GET request again to test the read functionality.
    response = authenticated_client.get("/users/me/preferences/")

    # ASSERT
    assert response.status_code == 200
    assert response.json() == []


def test_read_preferences_for_user_with_preferences(
    authenticated_client: TestClient,
    db_session: Session
):
    """
    GIVEN an authenticated user with existing preferences,
    WHEN they make a GET request to the preferences endpoint,
    THEN the response should be a 200 OK with a list of their preferences.
    """
    # ARRANGE: Create a user and some preferences for them directly.
    user = crud.create_user(db_session, schemas.UserCreate(
        email="newuser@example.com",
        username="New User",
        password="password",
        firebase_uid="fake-firebase-uid-123"
    ))
    crud.create_user_preference(
        db=db_session,
        preference=schemas.UserPreferenceCreate(preference_text="Use a friendly tone."),
        user_id=user.id
    )

    # ACT: Make the GET request.
    response = authenticated_client.get("/users/me/preferences/")

    # ASSERT
    assert response.status_code == 200
    response_data = response.json()
    assert len(response_data) == 1
    assert response_data[0]["preference_text"] == "Use a friendly tone."

"""
------ Tests the Update (PUT) Case -----
"""

def test_update_preference(
    authenticated_client: TestClient,
    db_session: Session
):
    """
    GIVEN an authenticated user with an existing preference,
    WHEN they make a PUT request to update that preference,
    THEN the preference should be updated in the database,
    AND the updated preference data should be returned.
    """
    # ARRANGE: Create a user and an initial preference.
    user = crud.create_user(db_session, schemas.UserCreate(
        email="newuser@example.com",
        username="New User",
        password="password",
        firebase_uid="fake-firebase-uid-123"
    ))
    initial_preference = crud.create_user_preference(
        db=db_session,
        preference=schemas.UserPreferenceCreate(preference_text="Old preference text."),
        user_id=user.id
    )

    # Define the update payload
    update_data = {
        "preference_text": "This is the new, updated preference."
    }

    # ACT: Make the PUT request to the specific preference's endpoint.
    response = authenticated_client.put(
        f"/users/me/preferences/{initial_preference.id}",
        json=update_data
    )

    # ASSERT Part 1: Check the API response.
    assert response.status_code == 200
    response_data = response.json()
    assert response_data["preference_text"] == update_data["preference_text"]
    assert response_data["id"] == str(initial_preference.id)

    # ASSERT Part 2: Verify the change was persisted in the database.
    db_session.refresh(initial_preference)
    assert initial_preference.preference_text == "This is the new, updated preference."


"""
------ Tests the DELETE (DEL) Case -----
"""

def test_delete_preference(
    authenticated_client: TestClient,
    db_session: Session
):
    """
    GIVEN an authenticated user with an existing preference,
    WHEN they make a DELETE request for that preference,
    THEN the preference should be removed from the database,
    AND the deleted preference data should be returned.
    """
    # ARRANGE: Create a user and a preference to be deleted.
    user = crud.create_user(db_session, schemas.UserCreate(
        email="newuser@example.com",
        username="New User",
        password="password",
        firebase_uid="fake-firebase-uid-123"
    ))
    preference_to_delete = crud.create_user_preference(
        db=db_session,
        preference=schemas.UserPreferenceCreate(preference_text="Delete this preference."),
        user_id=user.id
    )
    preference_id = preference_to_delete.id

    # Verify the preference exists before we try to delete it.
    assert db_session.query(models.UserPreference).filter(models.UserPreference.id == preference_id).one_or_none() is not None

    # ACT: Make the DELETE request.
    response = authenticated_client.delete(f"/users/me/preferences/{preference_id}")

    # ASSERT Part 1: Check the API response.
    assert response.status_code == 200
    response_data = response.json()
    assert response_data["preference_text"] == "Delete this preference."
    assert response_data["id"] == str(preference_id)

    # ASSERT Part 2: Verify the preference was actually deleted from the database.
    db_preference = db_session.query(models.UserPreference).filter(models.UserPreference.id == preference_id).one_or_none()
    assert db_preference is None