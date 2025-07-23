# tests/test_websockets.py

import json
import base64
from unittest.mock import patch, MagicMock, AsyncMock
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from signconnect import schemas, crud
from signconnect.db import models


@patch('src.signconnect.routers.websockets.speech.SpeechAsyncClient')
def test_websocket_connect_and_disconnect(
        mock_speech_client: MagicMock,
        authenticated_client: TestClient,
        db_session: Session
):
    """
    GIVEN an authenticated client,
    WHEN they attempt to connect to the WebSocket endpoint,
    THEN the connection should be accepted and then closed cleanly.
    """
    try:
        with authenticated_client.websocket_connect("/ws") as websocket:
            # The successful connection is the test.
            print("\n--- WebSocket connection successful ---")
    except Exception as e:
        assert False, f"WebSocket connection failed with an exception: {e}"


@patch('src.signconnect.routers.websockets.crud.find_similar_question')
@patch('src.signconnect.routers.websockets.get_response_suggestions')
@patch('src.signconnect.routers.websockets.speech.SpeechAsyncClient')
def test_websocket_sends_and_receives_messages(
        mock_speech_client: MagicMock,
        mock_llm_client: MagicMock,
        mock_find_similar: MagicMock,
        authenticated_client: TestClient,
        db_session: Session
):
    """
    GIVEN an active WebSocket connection,
    WHEN the client sends audio data and requests suggestions,
    THEN the server should send back a final transcript and suggestions.
    """
    # ARRANGE
    mock_llm_client.return_value = "Suggestion 1\nSuggestion 2"
    mock_find_similar.return_value = models.ScenarioQuestion(
        question_text="Fake similar question", user_answer_text="Fake answer"
    )

    mock_speech_instance = MagicMock()
    mock_result = MagicMock()
    mock_result.results = [MagicMock()]
    mock_result.results[0].is_final = True
    final_transcript_text = "This is a final transcript."
    mock_result.results[0].alternatives[0].transcript = final_transcript_text

    async def async_generator():
        yield mock_result

    mock_speech_instance.streaming_recognize = AsyncMock(return_value=async_generator())
    mock_speech_client.return_value = mock_speech_instance

    # THE FIX: Add the required 'username' and 'password' fields.
    crud.create_user(db_session, schemas.UserCreate(
        email="newuser@example.com",
        username="testuser",
        password="password",
        firebase_uid="fake-firebase-uid-123"
    ))

    # ACT & ASSERT
    with authenticated_client.websocket_connect("/ws") as websocket:
        # 1. Send audio
        audio_b64 = base64.b64encode(b'fake-audio-data').decode('utf-8')
        websocket.send_json({"type": "audio", "data": audio_b64})

        # 2. Receive transcript
        final_transcript_data = websocket.receive_text()
        assert final_transcript_data == f"final:{final_transcript_text}"

        # 3. Request suggestions
        websocket.send_json({"type": "get_suggestions", "transcript": final_transcript_text})

        # 4. Receive suggestions
        suggestions_data = websocket.receive_text()
        assert suggestions_data.startswith("suggestions:")
        suggestions_list = json.loads(suggestions_data.split("suggestions:", 1)[1])
        assert suggestions_list == ["Suggestion 1", "Suggestion 2"]