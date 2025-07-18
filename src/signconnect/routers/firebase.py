# src/routers/firebase.py

from fastapi import APIRouter
from typing import Dict, Any
from ..core.config import get_settings

router = APIRouter(
    prefix="/api",
    tags=["Firebase"],
)

@router.get("/firebase-config", response_model=Dict[str, Any], summary="Get Firebase client configuration")
def get_firebase_client_config() -> Dict[str, Any]:
    """
    Retrieves the Firebase client-side configuration for frontend applications.

    This endpoint securely provides the necessary Firebase initialization
    parameters (including the client API key) without exposing sensitive
    credentials directly in the frontend's source code.

    Pre-conditions:
    - The FIREBASE_CLIENT_API_KEY must be set in the environment variables
      or .env file accessible by the backend.
    - The backend must be properly configured to load settings via get_settings().

    Post-conditions:
    - Returns a dictionary containing the Firebase configuration parameters.
    - The API key included is specifically restricted for client-side use.
    """
    settings = get_settings()
    firebase_config = {
        "apiKey": settings.FIREBASE_CLIENT_API_KEY,
        "authDomain": "robust-form-464822-c0.firebaseapp.com",
        "projectId": "robust-form-464822-c0",
        "storageBucket": "robust-form-464822-c0.firebasestorage.app",
        "messagingSenderId": "300931117814",
        "appId": "1:300931117814:web:ea51ca90c5bd58a3a1f2d7",
        "measurementId": "G-HZH7QK7NL9"
    }
    return firebase_config