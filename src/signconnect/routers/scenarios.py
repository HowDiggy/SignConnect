from starlette import status

print("--- SCENARIOS ROUTER FILE IS BEING IMPORTED ---")

import uuid
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from .. import crud, schemas
from ..db.database import get_db
from ..dependencies import get_current_user

# Create a new router object
router = APIRouter(
    prefix="/users/me/scenarios",
    tags=["scenarios"],
)
# ADD THIS TEST ENDPOINT
@router.get("/test")
def test_router():
    return {"message": "The scenarios router is working!"}

@router.get("/", response_model=list[schemas.Scenario])
def read_scenarios_for_user(
        db: Session = Depends(get_db),
        current_user: dict = Depends(get_current_user)
):
    """
    Retrieve all scenarios for the currently authenticated user.
    """
    print("--- 1. Entered read_scenarios_for_user endpoint ---")
    firebase_user_email = current_user.get("email")
    print(f"--- 2. Got email from Firebase token: {firebase_user_email} ---")

    db_user = crud.get_user_by_email(db, email=firebase_user_email)

    if not db_user:
        print(f"--- 3. User not found in local DB. Returning empty list. ---")
        return []

    print(f"--- 3. Found user in local DB with ID: {db_user.id} ---")

    scenarios = crud.get_scenarios_by_user(db, user_id=db_user.id)
    print(f"--- 4. Found {len(scenarios)} scenarios for this user. ---")

    return scenarios

@router.post("/", response_model=schemas.Scenario)
def create_scenario(
    scenario: schemas.ScenarioCreate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """
    Create a new scenario for the currently authenticated user.
    If the user doesn't exist in the local DB, create them first.
    """
    firebase_user_email = current_user.get("email")
    db_user = crud.get_user_by_email(db, email=firebase_user_email)

    # if user doesn't exist in DB, create them now
    if db_user is None:
        user_to_create = schemas.UserCreate(
            email=firebase_user_email,
            username=current_user.get("name") or firebase_user_email,
            password="firebase_user_placeholder",
            firebase_uid=current_user.get("uid"),
        )
        db_user = crud.create_user(db=db, user=user_to_create)

    # check if a scenario with this name already exists for this user
    existing_scenario = crud.get_scenario_by_name(db, name=scenario.name, user_id=db_user.id)
    if existing_scenario:
        raise HTTPException(status_code=400, detail="A scenario with this name already exists.")

    return crud.create_scenario(db=db, scenario=scenario, user_id=db_user.id)

@router.post("/{scenario_id}/questions/", response_model=schemas.ScenarioQuestion)
def create_scenario_question(
    scenario_id: uuid.UUID,
    question: schemas.ScenarioQuestionCreate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """
    Create a new pre-configured question for one of the user's scenarios, ensuring the user owns the parent scenario.
    """
    db_user = crud.get_user_by_email(db, email=current_user.get("email"))

    # get scenario from DB
    db_scenario = crud.get_scenario(db, scenario_id=scenario_id)

    # security check: ensure the scenario exists and belongs to current user
    if db_scenario is None:
        raise HTTPException(status_code=404, detail="Scenario not found")
    if db_scenario.user_id != db_user.id:
        raise HTTPException(status_code=403, detail="Not authorized to add questions to this scenario.")
    return crud.create_scenario_question(db=db, question=question, scenario_id=scenario_id)

@router.delete(
    "/{scenario_id}",
    response_model=schemas.Scenario,
    status_code=status.HTTP_200_OK,
    summary="Delete a specific scenario for the current user from the database.",
)
def delete_scenario(
        scenario_id: uuid.UUID,
        *,
        db: Session = Depends(get_db),
        current_user: dict = Depends(get_current_user),
):
    """
    Delete a scenario by its ID.
    The scenario must belong to the currently authenticated user.
    """
    # Get the user from the database based on the Firebase token
    db_user = crud.get_user_by_email(db, email=current_user.get("email"))
    if not db_user:
        raise HTTPException(status_code=404, detail="User not found")

    # Call the new CRUD function to delete the scenario
    deleted_scenario = crud.delete_scenario_by_id(db=db, scenario_id=scenario_id, user_id=db_user.id)

    # If the CRUD function returned None, it means the scenario wasn't found
    # or didn't belong to the user.
    if deleted_scenario is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Scenario with ID {scenario_id} not found or you do not have permission to delete it."
        )

    return deleted_scenario

# --- ADD THIS NEW ENDPOINT ---
@router.put(
    "/{scenario_id}",
    response_model=schemas.Scenario,
    summary="Update a specific scenario"
)
def update_scenario_endpoint(
    scenario_id: uuid.UUID,
    scenario_update: schemas.ScenarioUpdate, # Data from the request body
    *,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """
    Update a scenario's name or description.
    """
    db_user = crud.get_user_by_email(db, email=current_user.get("email"))
    if not db_user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    updated_scenario = crud.update_scenario(
        db=db,
        scenario_id=scenario_id,
        user_id=db_user.id,
        scenario_update=scenario_update
    )

    if updated_scenario is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Scenario with ID {scenario_id} not found or you do not have permission to edit it."
        )

    return updated_scenario