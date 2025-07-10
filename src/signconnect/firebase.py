import firebase_admin
from firebase_admin import credentials, auth
from pathlib import Path

# --- Corrected Path Logic ---
# 1. Get the path to the current file (firebase.py)
# 2. Get its parent directory (src/signconnect/)
# 3. Get the parent of that (src/)
# 4. Get the parent of that (the project root)
ROOT_DIR = Path(__file__).parent.parent.parent

# 5. Join the root directory path with your credentials filename
cred_path = ROOT_DIR / "firebase-credentials.json"

# --- Initialization ---
try:
    cred = credentials.Certificate(cred_path)
    firebase_admin.initialize_app(cred)
except Exception as e:
    print(f"Failed to initialize Firebase: {e}")
    print(f"Attempted to load credentials from: {cred_path.resolve()}")


def verify_firebase_token(token: str) -> dict | None:
    """
    Verifies a Firebase ID token and returns the user's decoded claims.
    Returns None if the token is invalid.
    """
    try:
        decoded_token = auth.verify_id_token(token)
        return decoded_token
    except Exception as e:
        print(f"Failed to verify Firebase token: {e}")
        return None