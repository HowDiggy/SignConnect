# tests/test_llm_client.py

from unittest.mock import MagicMock
import pytest
from src.signconnect.llm.client import GeminiClient

# A fake API key for initialization, not used for real calls.
FAKE_API_KEY = "test-api-key"


@pytest.fixture
def mock_gemini_model(monkeypatch):
    """
    Mocks the genai.GenerativeModel to prevent actual API calls during tests.
    This fixture replaces the real model with a controllable fake.
    """
    # 1. Create a mock for the model instance that the client will use.
    mock_model_instance = MagicMock()

    # 2. Configure the mock response for a successful API call.
    mock_response = MagicMock()
    mock_response.text = "Suggestion 1\nSuggestion 2\nSuggestion 3"
    mock_model_instance.generate_content.return_value = mock_response

    # 3. Use monkeypatch to replace the *class* in the google.generativeai library.
    #    Now, whenever `genai.GenerativeModel()` is called, it will return our mock instance.
    mock_generative_model_class = MagicMock(return_value=mock_model_instance)
    monkeypatch.setattr("google.generativeai.GenerativeModel", mock_generative_model_class)

    # Also, mock the `configure` function so it does nothing.
    monkeypatch.setattr("google.generativeai.configure", lambda api_key: None)

    return mock_model_instance


def test_get_response_suggestions_success(mock_gemini_model):
    """
    Tests that the get_response_suggestions method correctly calls the API
    and processes a successful response.
    """
    # Arrange: Initialize the client. Thanks to our fixture, it will get the mocked model.
    client = GeminiClient(api_key=FAKE_API_KEY)
    test_transcript = "Tell me about your day."
    test_prefs = ["I am a software engineer.", "I like dogs."]
    test_history = ["Hello", "Hi there"]

    # Act: Call the method we want to test.
    suggestions = client.get_response_suggestions(
        transcript=test_transcript,
        user_preferences=test_prefs,
        conversation_history=test_history,
    )

    # Assert: Verify the behavior and the result.
    mock_gemini_model.generate_content.assert_called_once()
    assert suggestions == ["Suggestion 1", "Suggestion 2", "Suggestion 3"]
    assert len(suggestions) == 3


def test_get_response_suggestions_api_error(monkeypatch):
    """
    Tests that the method handles an exception from the API gracefully
    and returns an empty list.
    """
    # Arrange: Mock the model to raise an exception when called.
    mock_model_instance = MagicMock()
    mock_model_instance.generate_content.side_effect = Exception("API call failed")
    mock_generative_model_class = MagicMock(return_value=mock_model_instance)
    monkeypatch.setattr("google.generativeai.GenerativeModel", mock_generative_model_class)
    monkeypatch.setattr("google.generativeai.configure", lambda api_key: None)

    client = GeminiClient(api_key=FAKE_API_KEY)

    # Act: Call the method.
    suggestions = client.get_response_suggestions(
        transcript="Anything", user_preferences=[], conversation_history=[]
    )

    # Assert: Ensure it returns an empty list as designed.
    assert suggestions == []

