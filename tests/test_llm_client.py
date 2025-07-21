# tests/test_llm_client.py

from unittest.mock import patch, MagicMock

# Import the function we want to test
from signconnect.llm.client import get_response_suggestions
from signconnect.db import models


# The @patch decorator intercepts the real Gemini API call
@patch('signconnect.llm.client.genai.GenerativeModel')
def test_get_response_suggestions_builds_correct_prompt(mock_generative_model):
    """
    GIVEN a transcript, a similar question, and user preferences,
    WHEN get_response_suggestions is called,
    THEN it should build a rich, correctly formatted prompt for the AI.
    """
    # ARRANGE Part 1: Set up the mock
    # Create a mock object that will be returned by the patched GenerativeModel
    mock_model_instance = MagicMock()
    # Configure what the 'generate_content' method of our mock should return
    mock_model_instance.generate_content.return_value.text = "Mocked AI response"
    # Make the main mock return our configured instance
    mock_generative_model.return_value = mock_model_instance

    # ARRANGE Part 2: Create fake input data for our function
    transcript = "Hello, I have a question about my bill."

    # Create a fake SQLAlchemy ScenarioQuestion object
    similar_question = models.ScenarioQuestion(
        question_text="Is there a problem with my invoice?",
        user_answer_text="My invoice number is 12345."
    )

    # Create a list of fake SQLAlchemy UserPreference objects
    preferences = [
        models.UserPreference(preference_text="I prefer a formal tone."),
        models.UserPreference(preference_text="My account number is XYZ.")
    ]

    # ACT: Call the function we are testing
    get_response_suggestions(transcript, similar_question, preferences)

    # ASSERT: Check that the 'generate_content' method was called exactly once
    mock_model_instance.generate_content.assert_called_once()

    # Get the actual prompt that was passed to the mock
    actual_prompt = mock_model_instance.generate_content.call_args[0][0]

    # Verify that all the key pieces of information are in the prompt
    print(f"\n--- Actual Prompt Sent to Mock AI ---\n{actual_prompt}")
    assert "Conversation Transcript:" in actual_prompt
    assert transcript in actual_prompt
    assert "User's Personal Context:" in actual_prompt
    assert "I prefer a formal tone." in actual_prompt
    assert "My account number is XYZ." in actual_prompt
    assert "Most Relevant Saved Scenario:" in actual_prompt
    assert "Is there a problem with my invoice?" in actual_prompt
    assert "My invoice number is 12345." in actual_prompt


@patch('signconnect.llm.client.genai.GenerativeModel')
def test_get_response_suggestions_with_no_similar_question(mock_generative_model):
    """
    GIVEN a transcript and preferences, but no similar question,
    WHEN get_response_suggestions is called,
    THEN it should build a correct prompt that omits the scenario section.
    """
    # ARRANGE Part 1: Set up the mock
    mock_model_instance = MagicMock()
    mock_model_instance.generate_content.return_value.text = "Mocked response"
    mock_generative_model.return_value = mock_model_instance

    # ARRANGE Part 2: Create input data, this time with similar_question as None
    transcript = "I'd like to book a follow-up appointment."
    similar_question = None  # This is the condition we are testing
    preferences = [
        models.UserPreference(preference_text="My doctor is Dr. Smith."),
    ]

    # ACT: Call the function we are testing
    get_response_suggestions(transcript, similar_question, preferences)

    # ASSERT: Check that the generate_content method was called
    mock_model_instance.generate_content.assert_called_once()

    # Get the actual prompt that was passed to the mock
    actual_prompt = mock_model_instance.generate_content.call_args[0][0]

    # Verify that the correct information is present, and the
    # scenario information is correctly omitted.
    print(f"\n--- Actual Prompt (No Scenario) ---\n{actual_prompt}")
    assert "Conversation Transcript:" in actual_prompt
    assert transcript in actual_prompt
    assert "User's Personal Context:" in actual_prompt
    assert "My doctor is Dr. Smith." in actual_prompt
    assert "Most Relevant Saved Scenario:" not in actual_prompt


@patch('signconnect.llm.client.genai.GenerativeModel')
def test_get_response_suggestions_with_no_preferences(mock_generative_model):
    """
    GIVEN a transcript and a similar question, but no user preferences,
    WHEN get_response_suggestions is called,
    THEN it should build a correct prompt that omits the personal context section.
    """
    # ARRANGE Part 1: Set up the mock
    mock_model_instance = MagicMock()
    mock_model_instance.generate_content.return_value.text = "Mocked response"
    mock_generative_model.return_value = mock_model_instance

    # ARRANGE Part 2: Create input data, this time with an empty preferences list
    transcript = "I need to know your hours."
    similar_question = models.ScenarioQuestion(
        question_text="What time do you close?",
        user_answer_text="We close at 5 PM."
    )
    preferences = []  # This is the condition we are testing

    # ACT: Call the function we are testing
    get_response_suggestions(transcript, similar_question, preferences)

    # ASSERT: Check that the generate_content method was called
    mock_model_instance.generate_content.assert_called_once()

    # Get the actual prompt that was passed to the mock
    actual_prompt = mock_model_instance.generate_content.call_args[0][0]

    # Verify that the correct information is present, and the
    # preferences section is correctly omitted.
    print(f"\n--- Actual Prompt (No Preferences) ---\n{actual_prompt}")
    assert "Conversation Transcript:" in actual_prompt
    assert transcript in actual_prompt
    assert "Most Relevant Saved Scenario:" in actual_prompt
    assert "What time do you close?" in actual_prompt
    assert "User's Personal Context:" not in actual_prompt