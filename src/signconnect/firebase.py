# src/signconnect/firebase.py

import firebase_admin
from firebase_admin import auth
import structlog

logger = structlog.get_logger(__name__)

# By not passing any arguments to initialize_app(), the SDK will automatically
# look for the GOOGLE_APPLICATION_CREDENTIALS environment variable, which
# is correctly set in your docker-compose.yml file.
try:
    # Check if the app is already initialized to prevent errors during reloads
    if not firebase_admin._apps:
        firebase_admin.initialize_app()
    logger.info("Firebase Admin SDK initialized successfully.")
except Exception as e:
    logger.error(f"Failed to initialize Firebase: {e}")
    # In a real production scenario, you might want to raise the exception
    # to prevent the app from starting in a misconfigured state.


def verify_firebase_token(token: str) -> dict | None:
    """
    Verifies a Firebase ID token and returns the user's decoded claims.

    Pre-conditions:
    - Firebase Admin SDK must be initialized.
    - The provided token must be a valid Firebase ID token string.

    Post-conditions:
    - Returns a dictionary of decoded claims if the token is valid.
    - Returns None if the token is invalid or verification fails.
    """
    if not token:
        return None
    try:
        decoded_token = auth.verify_id_token(token)
        return decoded_token
    except Exception as e:
        # It's helpful to log the specific error during development
        logger.error(f"Error verifying Firebase token: {e}")
        return None
