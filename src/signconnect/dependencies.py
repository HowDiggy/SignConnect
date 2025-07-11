from fastapi import Query, Header, Depends, HTTPException
from .firebase import verify_firebase_token


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