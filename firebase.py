import firebase_admin
from firebase_admin import credentials, auth
import os

# get the path to the credentials file from from an environment variable
cred_path = os.getenv('FIREBASE_CREDENTIALS_PATH', "firebase-credentials.json")

cred = credentials.Certificate(cred_path)
firebase_admin.initialize_app(cred)

def verify_firebase_token(token: str) -> dict | None:
    """
    Verifies a Firebase ID token and returns the user's decoded claims.
    Returns None if the token is invalid.
    :param token:
    :return:
    """

    try:
        decoded_token = auth.verify_id_token(token)
        return decoded_token
    except Exception as e:
        print(f"Failed to verify token: {e}")
        return None