# src/signconnect/routers/firebase.py
from fastapi import APIRouter, HTTPException
from ..core.config import get_settings
import structlog

logger = structlog.get_logger(__name__)

router = APIRouter(prefix="/api", tags=["Firebase"])


@router.get("/firebase-config")
def get_firebase_config():
    settings = get_settings()

    # UNWRAP the SecretStr -> actual string
    api_key = (
        settings.FIREBASE_CLIENT_API_KEY.get_secret_value()
        if settings.FIREBASE_CLIENT_API_KEY
        else None
    )
    if not api_key:
        # Fail fast so we don't silently send "**********"
        raise HTTPException(
            status_code=500, detail="FIREBASE_CLIENT_API_KEY is not set"
        )

    return {
        "apiKey": api_key,
        "authDomain": "robust-form-464822-c0.firebaseapp.com",
        "projectId": "robust-form-464822-c0",
        "storageBucket": "robust-form-464822-c0.firebasestorage.app",
        "messagingSenderId": "300931117814",
        "appId": "1:300931117814:web:ea51ca90c5bd58a3a1f2d7",
        "measurementId": "G-HZH7QK7NL9",
    }
