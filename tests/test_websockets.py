from unittest.mock import patch, MagicMock
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from src.signconnect import crud, schemas
from src.signconnect.llm.client import GeminiClient
from src.signconnect.dependencies import get_llm_client


# This is a helper function, not a pytest fixture
def setup_websocket_test_environment(
    client: TestClient, db_session: Session
) -> tuple[str, MagicMock]:
    """Helper function to set up the test environment for websockets."""
    mock_gemini_client = MagicMock(spec=GeminiClient)
    mock_gemini_client.get_response_suggestions.return_value = ["A", "B"]

    app = client.app
    app.dependency_overrides[get_llm_client] = lambda: mock_gemini_client

    # This is the mock user that firebase_admin.auth.verify_id_token will return
    FAKE_FIREBASE_USER = {
        "email": "newuser@example.com",
        "name": "New User",
        "uid": "fake-firebase-uid-123",
    }

    # Create the user in the database so the websocket can find them
    crud.create_user(
        db_session,
        schemas.UserCreate(
            email=FAKE_FIREBASE_USER["email"],
            username=FAKE_FIREBASE_USER["name"],
            password="a-password",
            firebase_uid=FAKE_FIREBASE_USER["uid"],
        ),
    )

    # We can just use a simple string as the token now, since verification is mocked
    return "fake-jwt-token", mock_gemini_client, FAKE_FIREBASE_USER


# --- Your Tests ---


# Use patch to mock the firebase admin auth function for the duration of the test
@patch("firebase_admin.auth.verify_id_token")
def test_websocket_connect_and_disconnect(
    mock_verify_token, integration_client: TestClient, integration_db_session: Session
):
    """Tests that a client can successfully connect and disconnect."""
    token, _, fake_user = setup_websocket_test_environment(
        integration_client, integration_db_session
    )
    # Configure the mock to return our fake user when called with our fake token
    mock_verify_token.return_value = fake_user

    with integration_client.websocket_connect(f"/api/ws/{token}") as websocket:
        # If the connection succeeds, this code will run.
        # We can add a simple assertion to be sure.
        assert websocket


@patch("firebase_admin.auth.verify_id_token")
def test_websocket_sends_and_receives_messages(
    mock_verify_token, integration_client: TestClient, integration_db_session: Session
):
    """Tests that the websocket correctly handles and responds to messages."""
    token, mock_llm_client, fake_user = setup_websocket_test_environment(
        integration_client, integration_db_session
    )
    mock_verify_token.return_value = fake_user

    with integration_client.websocket_connect(f"/api/ws/{token}") as websocket:
        # Send a message
        websocket.send_json(
            {"type": "speech_chunk", "payload": "dGhpcyBpcyBhIHRlc3Q="}
        )  # "this is a test" in base64

        # Check for a response from the server (optional, but good to have)
        response = websocket.receive_json()
        assert response["type"] == "suggestions"
