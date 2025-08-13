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
