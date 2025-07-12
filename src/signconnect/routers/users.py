from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from .. import crud, schemas
from ..db.database import get_db
from ..dependencies import get_current_user

# Add the prefix and tags for better organization
router = APIRouter(
    prefix="/users/me",
    tags=["users"],
)

# The path is now "/preferences/" which is relative to the "/users/me" prefix
@router.post("/preferences/", response_model=schemas.UserPreference)
def create_preference(
    preference: schemas.UserPreferenceCreate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """
    Create a new preference for the currently authenticated user.
    """
    firebase_user_email = current_user.get("email")
    db_user = crud.get_user_by_email(db, email=firebase_user_email)

    if db_user is None:
        user_to_create = schemas.UserCreate(
            email=firebase_user_email,
            username=current_user.get("name") or firebase_user_email,
            password="firebase_user_placeholder"
        )
        db_user = crud.create_user(db=db, user=user_to_create)

    return crud.create_user_preference(db=db, preference=preference, user_id=db_user.id)


# This path is also relative to the prefix
@router.get("/preferences/", response_model=list[schemas.UserPreference])
def read_user_preferences(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """
    Retrieve all preferences for currently authenticated user.
    """
    firebase_user_email = current_user.get("email")
    db_user = crud.get_user_by_email(db, email=firebase_user_email)
    if db_user is None:
        raise HTTPException(status_code=404, detail="User not found")

    preferences = crud.get_user_preferences(db, user_id=db_user.id, skip=skip, limit=limit)
    return preferences