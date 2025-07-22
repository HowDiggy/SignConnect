# tests/integration/test_vector_search.py

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
        integration_db_session: Session  # <-- Using our new PostgreSQL fixture
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
    # This is the new transcript from the "user"
    mock_result.results[0].alternatives[0].transcript = "What's the price for a latte?"

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
    # Add several questions. The vector search should find the one about "cost".
    crud.create_scenario_question(db, schemas.ScenarioQuestionCreate(question_text="Where is the bathroom?",
                                                                     user_answer_text="It's in the back."), scenario.id)
    crud.create_scenario_question(db, schemas.ScenarioQuestionCreate(question_text="How much does a coffee cost?",
                                                                     user_answer_text="It is $3."), scenario.id)
    crud.create_scenario_question(db, schemas.ScenarioQuestionCreate(question_text="Do you have Wi-Fi?",
                                                                     user_answer_text="Yes, the password is 'coffee'."),
                                  scenario.id)

    # ACT & ASSERT
    with integration_client.websocket_connect("/ws") as websocket:
        websocket.send_bytes(b'fake-audio-of-a-latte-question')
        websocket.close()

        # We don't need to check the websocket messages here.
        # We just need to let the server process the request.

    # ASSERT: The most important check!
    # We verify that our LLM mock was called with the correct "similar question"
    # that was found by the REAL vector search.

    # Give the server a moment to process the background tasks
    import time
    time.sleep(1)

    mock_llm_client.assert_called_once()

    # THE DEBUGGING STEP: Print the entire call_args object
    print(f"\n--- DEBUG: Inspecting mock_llm_client.call_args ---\n{mock_llm_client.call_args}\n")

    # Access the arguments by name from the kwargs dictionary
    call_kwargs = mock_llm_client.call_args.kwargs

    assert "similar_question" in call_kwargs
    found_similar_question = call_kwargs["similar_question"]

    assert found_similar_question is not None
    assert found_similar_question.question_text == "How much does a coffee cost?"