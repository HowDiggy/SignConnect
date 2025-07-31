# tests/test_websockets.py

from unittest.mock import MagicMock

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

# Import the actual dependency we want to override
from src.signconnect.dependencies import get_llm_client


def test_websocket_connect_and_disconnect(
    authenticated_client: TestClient,
):
    """
    Tests that a client can successfully connect and disconnect.
    No mocking is needed as this just tests the connection lifecycle.
    """
    # The 'with' statement handles both connecting and cleanly disconnecting.
    # If this code runs without raising an exception, the test passes.
    with authenticated_client.websocket_connect("/ws/some_user_id") as websocket:
        assert websocket.scope["path"] == "/api/ws/some_user_id"


def test_websocket_sends_and_receives_messages(
    authenticated_client: TestClient,
):
    """
    Tests that the websocket correctly uses the GeminiClient to handle
    and respond to messages.
    """
    # ARRANGE: Create a mock for the GeminiClient.
    mock_gemini_client = MagicMock()
    # Configure our mock to return a specific value when its method is called.
    mock_gemini_client.generate_response.return_value = "This is a mock response."

    # Get the app from the test client and override the dependency.
    # Now, any call to the websocket endpoint will receive our mock client.
    app = authenticated_client.app
    app.dependency_overrides[get_llm_client] = lambda: mock_gemini_client

    try:
        # ACT
        with authenticated_client.websocket_connect("/ws/some_user_id") as websocket:
            # Send a message from the client to the server.
            websocket.send_text("Hello, this is a test.")

            # Wait for the server to send a response back.
            response_text = websocket.receive_text()

        # ASSERT
        # Verify that the correct method on our mock client was called once.
        mock_gemini_client.generate_response.assert_called_once_with(
            "Hello, this is a test."
        )
        # Verify that the websocket sent back the value we told our mock to return.
        assert response_text == "This is a mock response."

    finally:
        # CLEANUP: It's critical to clear the override so it doesn't
        # affect other tests.
        app.dependency_overrides.clear()