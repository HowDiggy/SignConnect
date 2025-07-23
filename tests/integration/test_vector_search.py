# tests/integration/test_vector_search.py
import json
import base64
from unittest.mock import patch, MagicMock, AsyncMock
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from signconnect import crud, schemas
from signconnect.db import models


# We will mock the external AI and Speech services, but test the real database.
@patch('src.signconnect.routers.websockets.get_response_suggestions')
@patch('src.signconnect.routers.websockets.speech.SpeechAsyncClient')
def test_full_transcription_and_vector_search(
        mock_speech_client,
        mock_llm_client,
        integration_client: TestClient,
        integration_db_session: Session
):
    """
    GIVEN a user with several saved questions in a real PostgreSQL database,
    WHEN they send a new transcript via WebSocket,
    THEN the system should use a real pgvector search to find the most similar question.
    """
    # ARRANGE Part 1: Configure the mocks
    mock_llm_client.return_value = "Mocked suggestion"
    mock_speech_instance = MagicMock()
    mock_result = MagicMock()
    mock_result.results = [MagicMock()]
    mock_result.results[0].is_final = True
    transcript_text = "What's the price for a latte?"
    mock_result.results[0].alternatives[0].transcript = transcript_text

    async def async_generator():
        yield mock_result

    mock_speech_instance.streaming_recognize = AsyncMock(return_value=async_generator())
    mock_speech_client.return_value = mock_speech_instance

    # ARRANGE Part 2: Populate the REAL PostgreSQL database
    db = integration_db_session
    user = crud.create_user(db, schemas.UserCreate(
        email="newuser@example.com",
        username="New User",
        password="password",
        firebase_uid="fake-firebase-uid-123"
    ))
    scenario = crud.create_scenario(
        db=db,
        scenario=schemas.ScenarioCreate(name="Coffee Shop"),
        user_id=user.id
    )
    crud.create_scenario_question(db, schemas.ScenarioQuestionCreate(question_text="Where is the bathroom?",
                                                                     user_answer_text="It's in the back."), scenario.id)
    crud.create_scenario_question(db, schemas.ScenarioQuestionCreate(question_text="How much does a coffee cost?",
                                                                     user_answer_text="It is $3."), scenario.id)
    crud.create_scenario_question(db, schemas.ScenarioQuestionCreate(question_text="Do you have Wi-Fi?",
                                                                     user_answer_text="Yes, the password is 'coffee'."),
                                  scenario.id)

    # ACT
    with integration_client.websocket_connect("/ws") as websocket:
        # 1. Send audio data
        fake_audio_bytes = b'fake-audio-of-a-latte-question'
        fake_audio_base64 = base64.b64encode(fake_audio_bytes).decode('utf-8')
        websocket.send_json({"type": "audio", "data": fake_audio_base64})

        # 2. Receive the final transcript from the server
        final_transcript = websocket.receive_text()
        assert final_transcript == f"final:{transcript_text}"

        # 3. **THE FIX**: Send the request for suggestions, mimicking the frontend
        websocket.send_json({"type": "get_suggestions", "transcript": transcript_text})

        # 4. Now, receive the suggestions from the server
        suggestions = websocket.receive_text()
        assert "suggestions:" in suggestions

    # ASSERT
    mock_llm_client.assert_called_once()
    call_kwargs = mock_llm_client.call_args.kwargs
    found_similar_question = call_kwargs.get("similar_question")

    assert found_similar_question is not None
    assert found_similar_question.question_text == "How much does a coffee cost?"