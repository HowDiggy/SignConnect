# signconnect/routers/questions.py

import uuid
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from starlette import status

from .. import crud, schemas
from ..dependencies import get_db
from ..dependencies import get_current_user

router = APIRouter(
    prefix="/api/users/me/questions",
    tags=["questions"],
)

@router.delete(
    "/{question_id}",
    response_model=schemas.ScenarioQuestion,
    summary="Delete a specific question"
)
def delete_question(
    question_id: uuid.UUID,
    *,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """
    Delete a specific question by its ID.
    The user must own the scenario to which the question belongs.
    """
    db_user = crud.get_user_by_email(db, email=current_user.get("email"))
    if not db_user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    deleted_question = crud.delete_question_by_id(db=db, question_id=question_id, user_id=db_user.id)

    if deleted_question is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Question with ID {question_id} not found or you do not have permission to delete it."
        )

    return deleted_question

@router.put(
    "/{question_id}",
    response_model=schemas.ScenarioQuestion,
    summary="Update a specific question"
)
def update_question_endpoint(
    question_id: uuid.UUID,
    question_update: schemas.ScenarioQuestionUpdate, # The update data from the request body
    *,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """
    Update a specific question by its ID.
    """
    db_user = crud.get_user_by_email(db, email=current_user.get("email"))
    if not db_user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    updated_question = crud.update_question(
        db=db,
        question_id=question_id,
        user_id=db_user.id,
        question_update=question_update
    )

    if updated_question is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Question with ID {question_id} not found or you do not have permission to edit it."
        )

    return updated_question