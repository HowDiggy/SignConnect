import json
from unittest.mock import MagicMock

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from src.signconnect.dependencies import get_llm_client
from src.signconnect.llm.client import GeminiClient
from src.signconnect.crud import create_user
from src.signconnect.schemas import UserCreate


def setup_websocket_test_environment(
    client: TestClient,
    db_session: Session
) -> tuple[str, MagicMock]:
    """Helper function to set up the test environment for websockets."""
    # 1. Create a mock GeminiClient
    mock_gemini_client = MagicMock(spec=GeminiClient)
    mock_gemini_client.get_response_suggestions.return_value = ["A", "B"]

    # 2. Override the LLM client dependency for the websocket endpoint
    app = client.app
    app.dependency_overrides[get_llm_client] = lambda: mock_gemini_client

    # 3. Create the user in the database
    user_data = client.user
    create_user(
        db_session,
        UserCreate(
            email=user_data["email"],
            username=user_data["name"],
            password="a-password",
            firebase_uid=user_data["uid"],
        ),
    )
    
    return user_data["uid"], mock_gemini_client


def test_websocket_connect_and_disconnect(
    authenticated_client: TestClient, db_session: Session
):
    """Tests that a client can successfully connect and disconnect."""
    # ARRANGE: Set up mocks and DB state
    token, _ = setup_websocket_test_environment(authenticated_client, db_session)
    
    try:
        # ACT & ASSERT
        with authenticated_client.websocket_connect(f"/api/ws/{token}") as websocket:
            websocket.close()
    finally:
        authenticated_client.app.dependency_overrides.pop(get_llm_client, None)


def test_websocket_sends_and_receives_messages(
    authenticated_client: TestClient, db_session: Session
):
    """Tests that the websocket correctly handles and responds to messages."""
    # ARRANGE: Set up mocks and DB state
    token, mock_llm_client = setup_websocket_test_environment(
        authenticated_client, db_session
    )

    try:
        # ACT
        with authenticated_client.websocket_connect(f"/api/ws/{token}") as websocket:
            websocket.send_text(json.dumps({"transcript": "Hello"}))
            response_data = websocket.receive_json()

        # ASSERT
        mock_llm_client.get_response_suggestions.assert_called_once()
        assert response_data["suggestions"] == ["A", "B"]
    finally:
        authenticated_client.app.dependency_overrides.pop(get_llm_client, None)