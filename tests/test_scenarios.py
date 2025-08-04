# tests/test_scenarios.py
import uuid

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from signconnect import crud, schemas
from signconnect.db import models

"""
--------- Test the READ (GET) Case --------
"""


# Test Case 1: A user with no scenarios
def test_read_scenarios_for_user_with_no_scenarios(
    authenticated_client: TestClient, db_session: Session
):
    """
    GIVEN an authenticated user who has no scenarios in the database,
    WHEN they make a GET request to the scenarios endpoint,
    THEN the response should be a 200 OK with an empty list.
    """
    # ARRANGE
    # The `authenticated_client` fixture already provides a new, clean user for us.
    # We just need to make the API call.

    # ACT
    response = authenticated_client.get("/api/users/me/scenarios/")

    # ASSERT
    assert response.status_code == 200
    assert response.json() == []


# Test Case 2: A user with existing scenarios
def test_read_scenarios_for_user_with_scenarios(
    authenticated_client: TestClient, db_session: Session
):
    """
    GIVEN an authenticated user who has scenarios in the database,
    WHEN they make a GET request to the scenarios endpoint,
    THEN the response should be a 200 OK with a list of their scenarios.
    """
    # ARRANGE: Create the user and their scenarios directly in the database.
    user_to_create = schemas.UserCreate(
        email="newuser@example.com",
        username="New User",
        password="password",
        firebase_uid="fake-firebase-uid-123",  # Matches the authenticated_client mock
    )
    user = crud.create_user(db=db_session, user=user_to_create)

    # Create two scenarios directly in the database for this user.
    crud.create_scenario(
        db=db_session,
        scenario=schemas.ScenarioCreate(name="Work Meetings", description="For my job"),
        user_id=user.id,
    )
    crud.create_scenario(
        db=db_session,
        scenario=schemas.ScenarioCreate(
            name="Doctor's Office", description="For appointments"
        ),
        user_id=user.id,
    )

    # ACT
    response = authenticated_client.get("/api/users/me/scenarios/")

    # ASSERT
    assert response.status_code == 200
    response_data = response.json()
    assert len(response_data) == 2
    assert response_data[0]["name"] == "Work Meetings"
    assert response_data[1]["name"] == "Doctor's Office"
    assert response_data[0]["user_id"] == str(user.id)


"""
--------- Test the CREATE (POST) Case ---------
"""


def test_create_scenario_for_user(
    authenticated_client: TestClient, db_session: Session
):
    """
    GIVEN an authenticated user,
    WHEN they make a POST request to create a new scenario,
    THEN the response should be a 200 OK with the new scenario's data,
    AND the scenario should be saved in the database.
    """
    # ARRANGE: Define the data for the new scenario.
    scenario_data = {
        "name": "Coffee Shop Order",
        "description": "For ordering my daily coffee",
    }

    # ACT: Make the POST request to the create scenario endpoint.
    response = authenticated_client.post("/api/users/me/scenarios/", json=scenario_data)

    # ASSERT Part 1: Check the API response.
    assert response.status_code == 200
    response_data = response.json()
    assert response_data["name"] == scenario_data["name"]
    assert response_data["description"] == scenario_data["description"]
    assert "id" in response_data

    # ASSERT Part 2: Verify the scenario was actually saved to the database.
    scenario_id_from_response = uuid.UUID(response_data["id"])
    db_scenario = (
        db_session.query(models.Scenario)
        .filter(models.Scenario.id == scenario_id_from_response)
        .one_or_none()
    )

    assert db_scenario is not None
    assert db_scenario.name == "Coffee Shop Order"

    # ASSERT Part 3: Verify the scenario is linked to the correct user.
    user = crud.get_user_by_email(db_session, "newuser@example.com")
    assert user is not None
    assert db_scenario.user_id == user.id


"""
--------- Test the UPDATE (PUT) Case ---------
"""


def test_update_scenario(authenticated_client: TestClient, db_session: Session):
    """
    GIVEN an authenticated user with an existing scenario,
    WHEN they make a PUT request to update that scenario,
    THEN the scenario should be updated in the database,
    AND the updated scenario data should be returned.
    """
    # ARRANGE: Create a user and an initial scenario to be updated.
    user = crud.create_user(
        db_session,
        schemas.UserCreate(
            email="newuser@example.com",
            username="New User",
            password="password",
            firebase_uid="fake-firebase-uid-123",
        ),
    )
    initial_scenario = crud.create_scenario(
        db=db_session,
        scenario=schemas.ScenarioCreate(name="Old Name", description="Old description"),
        user_id=user.id,
    )

    # Define the update payload
    update_data = {
        "name": "Updated Scenario Name",
        "description": "This is the new, updated description.",
    }

    # ACT: Make the PUT request to the specific scenario's endpoint.
    response = authenticated_client.put(
        f"/api/users/me/scenarios/{initial_scenario.id}", json=update_data
    )

    # ASSERT Part 1: Check the API response.
    assert response.status_code == 200
    response_data = response.json()
    assert response_data["name"] == update_data["name"]
    assert response_data["description"] == update_data["description"]
    assert response_data["id"] == str(initial_scenario.id)

    # ASSERT Part 2: Verify the change was persisted in the database.
    db_session.refresh(initial_scenario)  # Refresh the object to get the latest data
    assert initial_scenario.name == "Updated Scenario Name"
    assert initial_scenario.description == "This is the new, updated description."


"""
--------- Test the DELETE (DEL) Case ---------
"""


# In tests/test_scenarios.py


def test_delete_scenario(authenticated_client: TestClient, db_session: Session):
    """
    GIVEN an authenticated user with an existing scenario,
    WHEN they make a DELETE request for that scenario,
    THEN the scenario should be removed from the database,
    AND the deleted scenario data should be returned.
    """
    # ARRANGE: Create a user and a scenario to be deleted.
    user = crud.create_user(
        db_session,
        schemas.UserCreate(
            email="newuser@example.com",
            username="New User",
            password="password",
            firebase_uid="fake-firebase-uid-123",
        ),
    )
    scenario_to_delete = crud.create_scenario(
        db=db_session,
        scenario=schemas.ScenarioCreate(name="To Be Deleted", description="Delete me"),
        user_id=user.id,
    )

    # Get the ID *before* the object is deleted.
    scenario_id = scenario_to_delete.id

    # Verify the scenario exists in the DB before we delete it.
    assert (
        db_session.query(models.Scenario)
        .filter(models.Scenario.id == scenario_id)
        .one_or_none()
        is not None
    )

    # ACT: Make the DELETE request.
    response = authenticated_client.delete(f"/api/users/me/scenarios/{scenario_id}")

    # ASSERT Part 1: Check the API response.
    assert response.status_code == 200
    response_data = response.json()
    assert response_data["name"] == "To Be Deleted"
    assert response_data["id"] == str(scenario_id)

    # ASSERT Part 2: Verify the scenario was actually deleted from the database.
    db_scenario = (
        db_session.query(models.Scenario)
        .filter(models.Scenario.id == scenario_id)
        .one_or_none()
    )
    assert db_scenario is None
