# tests/test_websockets.py
from unittest.mock import patch, MagicMock, AsyncMock
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

    # Check if user already exists before creating
    existing_user = crud.get_user_by_email(db_session, FAKE_FIREBASE_USER["email"])
    if not existing_user:
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


@patch("firebase_admin.auth.verify_id_token")
@patch("google.cloud.speech.SpeechAsyncClient")
def test_websocket_connect_and_disconnect(
    mock_speech_client,
    mock_verify_token,
    integration_client: TestClient,
    integration_db_session: Session,
):
    """Tests that a client can successfully connect and disconnect."""
    # Mock the Google Cloud Speech client to prevent authentication issues
    mock_speech_instance = AsyncMock()
    mock_speech_client.return_value = mock_speech_instance

    # Create an async generator for the streaming_recognize method
    async def mock_streaming_responses():
        # Return an empty async generator to simulate no speech results
        return
        yield  # This makes it an async generator

    mock_speech_instance.streaming_recognize.return_value = mock_streaming_responses()

    token, _, fake_user = setup_websocket_test_environment(
        integration_client, integration_db_session
    )
    # Configure the mock to return our fake user when called with our fake token
    mock_verify_token.return_value = fake_user

    # Use the correct WebSocket URL format with query parameter
    with integration_client.websocket_connect(f"/api/ws?token={token}") as websocket:
        # Send a simple message to keep the connection alive briefly
        websocket.send_json({"type": "ping"})

        # Receive the pong response
        response = websocket.receive_json()
        assert response["type"] == "pong"
        assert response["data"] == "Connection alive"


@patch("firebase_admin.auth.verify_id_token")
@patch("google.cloud.speech.SpeechAsyncClient")
def test_websocket_sends_and_receives_messages(
    mock_speech_client,
    mock_verify_token,
    integration_client: TestClient,
    integration_db_session: Session,
):
    """Tests that the websocket correctly handles and responds to messages."""
    # Mock the Google Cloud Speech client to prevent authentication issues
    mock_speech_instance = AsyncMock()
    mock_speech_client.return_value = mock_speech_instance

    # Create an async generator for the streaming_recognize method
    async def mock_streaming_responses():
        # Return an empty async generator to simulate no speech results
        return
        yield  # This makes it an async generator

    mock_speech_instance.streaming_recognize.return_value = mock_streaming_responses()

    token, mock_llm_client, fake_user = setup_websocket_test_environment(
        integration_client, integration_db_session
    )
    mock_verify_token.return_value = fake_user

    # Use the correct WebSocket URL format with query parameter
    with integration_client.websocket_connect(f"/api/ws?token={token}") as websocket:
        # Test 1: Send a ping message
        websocket.send_json({"type": "ping"})
        response = websocket.receive_json()
        assert response["type"] == "pong"

        # Test 2: Send an audio message (the type your WebSocket actually expects)
        websocket.send_json(
            {
                "type": "audio",
                "data": "dGhpcyBpcyBhIHRlc3Q=",
            }  # "this is a test" in base64
        )

        # Test 3: Send a get_suggestions message
        websocket.send_json(
            {"type": "get_suggestions", "transcript": "Hello, how are you?"}
        )

        # Receive the suggestions response
        response = websocket.receive_json()
        assert response["type"] == "suggestions"
        assert "data" in response
        assert isinstance(response["data"], list)
