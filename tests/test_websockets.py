# tests/test_websockets.py

import json
from unittest.mock import MagicMock, ANY

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

# Import the actual dependency we want to override
from src.signconnect.dependencies import get_llm_client, get_current_user
from src.signconnect.llm.client import GeminiClient
from src.signconnect.crud import create_user
from src.signconnect.schemas import UserCreate


def test_websocket_connect_and_disconnect(
    authenticated_client: TestClient,
):
    """
    Tests that a client can successfully connect and disconnect.
    """
    # The user is mocked by the authenticated_client fixture
    FAKE_USER = authenticated_client.app.dependency_overrides[get_current_user]()
    token = FAKE_USER["uid"]

    with authenticated_client.websocket_connect(f"/ws/{token}") as websocket:
        # If the connection is accepted and no exception is raised, this part passes.
        websocket.close()


def test_websocket_sends_and_receives_messages(
    authenticated_client: TestClient, db_session: Session
):
    """
    Tests that the websocket correctly uses the GeminiClient to handle
    and respond to messages after user authentication.
    """
    # ARRANGE Part 1: Ensure the mock user from the fixture exists in the DB
    # so that their preferences can be looked up.
    FAKE_USER = authenticated_client.app.dependency_overrides[get_current_user]()
    create_user(
        db_session,
        UserCreate(
            email=FAKE_USER["email"],
            username=FAKE_USER["name"],
            password="password",  # Placeholder
            firebase_uid=FAKE_USER["uid"],
        ),
    )

    # ARRANGE Part 2: Create a mock for the GeminiClient.
    mock_gemini_client = MagicMock(spec=GeminiClient)
    mock_gemini_client.get_response_suggestions.return_value = [
        "Suggestion 1",
        "Suggestion 2",
    ]

    # ARRANGE Part 3: Override the dependency with the correct signature.
    # The dependency expects a function that takes a `request` argument.
    app = authenticated_client.app
    app.dependency_overrides[get_llm_client] = lambda request: mock_gemini_client

    try:
        # ACT
        token = FAKE_USER["uid"]
        with authenticated_client.websocket_connect(f"/ws/{token}") as websocket:
            # Send a valid JSON payload that the router expects.
            websocket.send_text(
                json.dumps({
                    "transcript": "Hello, this is a test.",
                    "conversation_history": ["Hi there."],
                })
            )

            # Wait for the server to send a response back.
            response_data = websocket.receive_json()

        # ASSERT
        # Verify that the correct method on our mock client was called.
        mock_gemini_client.get_response_suggestions.assert_called_once_with(
            transcript="Hello, this is a test.",
            user_preferences=[],  # We haven't added any for this test user.
            conversation_history=["Hi there."],
        )
        # Verify the data sent back to the client.
        assert response_data == {
            "type": "suggestions",
            "suggestions": ["Suggestion 1", "Suggestion 2"],
        }

    finally:
        # CLEANUP: Critical to prevent test leakage.
        app.dependency_overrides.clear()