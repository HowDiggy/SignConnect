# tests/test_websockets.py
import json
from unittest.mock import patch, MagicMock, AsyncMock
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from signconnect import schemas, crud
from signconnect.db import models


def test_websocket_connect_and_disconnect(
    authenticated_client: TestClient,
    db_session: Session
):
    """
    GIVEN an authenticated client,
    WHEN they attempt to connect to the WebSocket endpoint,
    THEN the connection should be accepted and then closed cleanly.
    """
    # ARRANGE: No special setup is needed beyond having an authenticated client.

    # ACT & ASSERT: We use a 'with' block to manage the connection.
    # If the block opens and closes without any errors, the test passes.
    try:
        with authenticated_client.websocket_connect("/ws") as websocket:
            # We don't need to send or receive anything for this test.
            # We are just proving that the connection itself works.
            print("\n--- WebSocket connection successful ---")
    except Exception as e:
        # If any exception occurs during connection, fail the test.
        assert False, f"WebSocket connection failed with an exception: {e}"


# We now add a third patch to mock the vector search function
@patch('src.signconnect.routers.websockets.crud.find_similar_question')
@patch('src.signconnect.routers.websockets.get_response_suggestions')
@patch('src.signconnect.routers.websockets.speech.SpeechAsyncClient')
def test_websocket_sends_and_receives_messages(
        mock_speech_client,
        mock_llm_client,
        mock_find_similar,  # Add the new mock to the function signature
        authenticated_client: TestClient,
        db_session: Session
):
    """
    GIVEN an active WebSocket connection,
    WHEN the client sends audio data and closes the connection,
    THEN the server should send back a final transcript and suggestions.
    """
    # ARRANGE Part 1: Configure the mocks
    mock_llm_client.return_value = "Suggestion 1\nSuggestion 2"

    # THE FIX: Mock the find_similar_question function to return a fake question
    mock_find_similar.return_value = models.ScenarioQuestion(
        question_text="Fake similar question",
        user_answer_text="Fake answer"
    )

    mock_speech_instance = MagicMock()
    mock_result = MagicMock()
    mock_result.results = [MagicMock()]
    mock_result.results[0].is_final = True
    mock_result.results[0].alternatives[0].transcript = "This is a final transcript."

    async def async_generator():
        yield mock_result

    mock_speech_instance.streaming_recognize = AsyncMock(return_value=async_generator())
    mock_speech_client.return_value = mock_speech_instance

    # ARRANGE Part 2: Create a user
    crud.create_user(db_session, schemas.UserCreate(
        email="newuser@example.com",
        username="New User",
        password="password",
        firebase_uid="fake-firebase-uid-123"
    ))

    # ACT & ASSERT
    with authenticated_client.websocket_connect("/ws") as websocket:
        websocket.send_bytes(b'fake-audio-data')
        websocket.close()  # Signal the end of the stream

        final_transcript_data = websocket.receive_text()
        assert final_transcript_data == "final: This is a final transcript."

        suggestions_data = websocket.receive_text()
        assert suggestions_data.startswith("suggestions:")
        suggestions_list = json.loads(suggestions_data.split("suggestions:", 1)[1])
        assert suggestions_list == ["Suggestion 1", "Suggestion 2"]