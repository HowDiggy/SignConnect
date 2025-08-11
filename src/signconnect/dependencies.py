from fastapi import Query, Header, Depends, HTTPException, Request, status
from .firebase import verify_firebase_token
from typing import Generator
from sqlalchemy.orm import Session
from .llm.client import GeminiClient
from firebase_admin import auth


def get_db() -> Generator[Session, None, None]:
    """
    Placeholder dependency for getting a database session.

    This function is intended to be overridden by the application factory
    (create_app) with a real database session provider.
    """
    raise NotImplementedError("get_db dependency was not overridden by the app factory")

def get_llm_client(request: Request) -> GeminiClient:
    """
    Dependency to get the singleton instance of the GeminiClient
    from the application state.
    """
    return request.app.state.llm_client

async def get_current_user(
        authorization: str | None = Header(None),
        token_from_query: str | None = Query(None, alias="token")
):
    """
    Dependency to verify a Firebase token from either the Authorization header
    (for HTTP requests) or a query parameter (for WebSocket connections).
    """
    token = None
    if authorization and authorization.startswith("Bearer "):
        token = authorization.split("Bearer ")[1]
    elif token_from_query:
        token = token_from_query

    if not token:
        raise HTTPException(
            status_code=401,
            detail="Not authenticated",
            headers={"WWW-Authenticate": "Bearer"},
        )

    user = verify_firebase_token(token)
    if not user:
        raise HTTPException(
            status_code=401,
            detail="Invalid authentication credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return user

async def get_current_user_ws(
    token: str | None = Query(None), # Takes the token directly from the path
    db: Session = Depends(get_db)
) -> dict:
    """
    Dependency for authenticating WebSocket connections.
    Verifies the Firebase ID token from the URL path.
    """
    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing authentication token",
        )
    try:
        # This part remains the same, as it's just business logic.
        decoded_token = auth.verify_id_token(token)
        return decoded_token
    except auth.InvalidIdTokenError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication token",
        )
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Could not validate credentials",
        )
