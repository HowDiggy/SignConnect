from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from src.signconnect.db import models
from src.signconnect import crud, schemas

def test_create_user_on_first_preference(
    authenticated_client: TestClient, 
    db_session: Session
):
    """
    GIVEN a user is authenticated via Firebase but not in the local DB,
    WHEN they create their first preference,
    THEN a new user record should be created in the database.
    """
    user_in_db = db_session.query(models.User).filter(
        models.User.firebase_uid == authenticated_client.user["uid"]
    ).first()
    assert user_in_db is None, "User should not exist before the API call."

    preference_data = {"preference_text": "Please use a formal tone."}

    # FIX: Add the /api prefix to the URL.
    response = authenticated_client.post(
        "/api/users/me/preferences/", 
        json=preference_data
    )

    assert response.status_code == 200, response.text
    user_in_db = db_session.query(models.User).filter(
        models.User.firebase_uid == authenticated_client.user["uid"]
    ).one_or_none()
    assert user_in_db is not None, "User should have been created."


def test_read_preferences_for_user_with_no_preferences(
    authenticated_client: TestClient,
    db_session: Session
):
    """
    GIVEN an authenticated user exists in the DB but has no preferences,
    WHEN they make a GET request to the preferences endpoint,
    THEN the response should be a 200 OK with an empty list.
    """
    crud.create_user(db_session, schemas.UserCreate(
        email=authenticated_client.user["email"],
        username=authenticated_client.user["name"],
        password="password",
        firebase_uid=authenticated_client.user["uid"]
    ))

    # FIX: Add the /api prefix to the URL.
    response = authenticated_client.get("/api/users/me/preferences/")

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
    user_data = authenticated_client.user
    user = crud.create_user(db_session, schemas.UserCreate(
        email=user_data["email"],
        username=user_data["name"],
        password="password",
        firebase_uid=user_data["uid"]
    ))
    crud.create_user_preference(
        db=db_session,
        preference=schemas.UserPreferenceCreate(preference_text="Use a friendly tone."),
        user_id=user.id
    )

    # FIX: Add the /api prefix to the URL.
    response = authenticated_client.get("/api/users/me/preferences/")

    assert response.status_code == 200
    response_data = response.json()
    assert len(response_data) == 1
    assert response_data[0]["preference_text"] == "Use a friendly tone."


def test_update_preference(
    authenticated_client: TestClient,
    db_session: Session
):
    """
    GIVEN an authenticated user with an existing preference,
    WHEN they make a PUT request to update that preference,
    THEN the preference should be updated in the database.
    """
    user_data = authenticated_client.user
    user = crud.create_user(db_session, schemas.UserCreate(
        email=user_data["email"],
        username=user_data["name"],
        password="password",
        firebase_uid=user_data["uid"]
    ))
    initial_preference = crud.create_user_preference(
        db=db_session,
        preference=schemas.UserPreferenceCreate(preference_text="Old preference text."),
        user_id=user.id
    )

    update_data = {"preference_text": "This is the new, updated preference."}

    # FIX: Add the /api prefix to the URL.
    response = authenticated_client.put(
        f"/api/users/me/preferences/{initial_preference.id}",
        json=update_data
    )

    assert response.status_code == 200
    db_session.refresh(initial_preference)
    assert initial_preference.preference_text == "This is the new, updated preference."


def test_delete_preference(
    authenticated_client: TestClient,
    db_session: Session
):
    """
    GIVEN an authenticated user with an existing preference,
    WHEN they make a DELETE request for that preference,
    THEN the preference should be removed from the database.
    """
    user_data = authenticated_client.user
    user = crud.create_user(db_session, schemas.UserCreate(
        email=user_data["email"],
        username=user_data["name"],
        password="password",
        firebase_uid=user_data["uid"]
    ))
    preference_to_delete = crud.create_user_preference(
        db=db_session,
        preference=schemas.UserPreferenceCreate(preference_text="Delete this preference."),
        user_id=user.id
    )
    preference_id = preference_to_delete.id

    # FIX: Add the /api prefix to the URL.
    response = authenticated_client.delete(f"/api/users/me/preferences/{preference_id}")

    assert response.status_code == 200
    db_preference = db_session.query(models.UserPreference).filter(models.UserPreference.id == preference_id).one_or_none()
    assert db_preference is None