from unittest.mock import AsyncMock, MagicMock

import pytest

from src.signconnect.services.websocket_manager import handle_message

# Mark all tests in this file as asynchronous
pytestmark = pytest.mark.asyncio


async def test_handle_message_unknown_type():
    """
    Test that handle_message does nothing when receiving a message of an
    unknown type.

    **Pre-conditions:**
    - A dictionary representing a JSON message with an unsupported 'type' key.
    - Mocked dependencies for the handler function.

    **Post-conditions:**
    - The handler function completes without error.
    - No methods are called on the mocked dependencies, confirming the function
      correctly ignored the message.
    """
    # Arrange: Create mock objects for all dependencies
    mock_manager = MagicMock()
    mock_websocket = MagicMock()
    # Use AsyncMock for coroutine functions
    mock_websocket.send_json = AsyncMock()
    mock_db = AsyncMock()
    mock_llm_client = MagicMock()
    mock_audio_queue = MagicMock()
    mock_user = MagicMock()

    # The message we are testing with
    test_message = {"type": "unknown_type", "data": "some data"}

    # Act: Call the function with our test data and mocks
    await handle_message(
        message=test_message,
        websocket=mock_websocket,
        manager=mock_manager,
        db=mock_db,
        llm_client=mock_llm_client,
        audio_queue=mock_audio_queue,
        user=mock_user,
    )

    # Assert: Verify that no significant methods were called on our mocks
    mock_llm_client.get_response_suggestions.assert_not_called()
    mock_manager.send_personal_json.assert_not_called()
    mock_audio_queue.put.assert_not_called()


async def test_handle_message_get_suggestions():
    """
    Test that handle_message correctly processes the 'get_suggestions'
    message type when a user is found in the database.

    **Pre-conditions:**
    - A message with type 'get_suggestions'.
    - Mocked dependencies, with the db mock configured to return a user.

    **Post-conditions:**
    - The llm_client's get_response_suggestions method is called once.
    - The connection manager's send_personal_json method is called once.
    """
    # Arrange: Create mocks
    mock_manager = MagicMock()
    mock_manager.send_personal_json = AsyncMock()  # This method IS awaited
    mock_websocket = MagicMock()
    mock_db = MagicMock()  # Use a standard MagicMock for the session
    mock_llm_client = MagicMock()  # This method is NOT awaited
    mock_audio_queue = MagicMock()
    mock_user = MagicMock()
    mock_firebase_user = {"email": "test@example.com"}  # Mock the user from auth

    # Configure the mock DB to simulate finding a user.
    # This mocks the chain of calls: db.query(...).filter(...).first()
    mock_db.query.return_value.filter.return_value.first.return_value = mock_user

    # Configure the mock LLM to return a specific value when called
    expected_suggestions = ["Suggestion 1", "Suggestion 2"]
    mock_llm_client.get_response_suggestions.return_value = expected_suggestions

    test_message = {"type": "get_suggestions", "transcript": "a test transcript"}

    # Act: Call the function
    await handle_message(
        manager=mock_manager,
        websocket=mock_websocket,
        message=test_message,
        db=mock_db,
        user=mock_firebase_user,  # Pass the firebase user dict here
        llm_client=mock_llm_client,
        audio_queue=mock_audio_queue,
    )

    # Assert: Verify the correct methods were called
    # Use 'assert_called_once' for the synchronous llm_client call
    mock_llm_client.get_response_suggestions.assert_called_once()

    expected_response = {
        "type": "suggestions",
        "data": expected_suggestions,
    }
    # Use 'assert_awaited_once_with' for the asynchronous manager call
    mock_manager.send_personal_json.assert_awaited_once_with(
        expected_response, mock_websocket
    )
    mock_audio_queue.put.assert_not_called()
