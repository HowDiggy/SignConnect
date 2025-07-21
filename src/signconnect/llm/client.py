import os
import google.generativeai as genai
from ..core.config import get_settings
from ..db import models
from typing import List, Optional

# configure the client with the API key from our settings
genai.configure(api_key=get_settings().GEMINI_API_KEY)


def get_response_suggestions(
        transcript: str,
        similar_question: Optional[models.ScenarioQuestion],
        preferences: List[models.UserPreference],
) -> str:
    """
    Generates personalized response suggestions using a rich context.
    :param preferences:
    :param similar_question:
    :param transcript:
    :return:
    """

    # For initializing the model, 'gemini-pro' is a good choice for this task
    model = genai.GenerativeModel('gemini-1.5-flash')

    # Add a check for the API key
    if not get_settings().GEMINI_API_KEY:
        print("Warning: GEMINI_API_KEY is not set. Using placeholder suggestions.")
        return "How can I help you?\nWhat is the price?\nThank you."

    # --- Build the Enhanced Prompt ---

    # Start with the basic instruction and structure
    prompt_parts = [
        "You are a helpful assistant providing response suggestions for a user who is deaf or hard-of-hearing.",
        "Based on the following conversation transcript and the user's personal context, provide 2-3 brief and relevant response suggestions, each on a new line.",
        "Do not include any other text, numbering, or explanations.",
        "\n---\n"
    ]

    # Add the conversation transcript
    prompt_parts.append(f"**Conversation Transcript:**\n\"{transcript}\"")


    # Format and add preferences if they exist
    if preferences:
        # Add the user's personal context section
        prompt_parts.append("\n**User's Personal Context:**")

        # This creates a clean, bulleted list of preferences
        formatted_preferences = "\n".join([f"- {p.preference_text}" for p in preferences])
        prompt_parts.append(f"General Preferences:\n{formatted_preferences}")
    else:
        # Handle the case where there are no preferences
        prompt_parts.append("General Preferences: None")

    # Format and add the most similar saved question-answer pair if it exists
    if similar_question:
        prompt_parts.append(
            "\nMost Relevant Saved Scenario:\n"
            f"Question: \"{similar_question.question_text}\"\n"
            f"User's Answer: \"{similar_question.user_answer_text}\""
        )

    prompt_parts.append("\n---\n")
    prompt_parts.append("Provide your suggestions below:")

    # Join all parts into a single prompt string
    prompt = "\n".join(prompt_parts)

    # The print statement that was here has been removed

    try:
        response = model.generate_content(prompt)
        return response.text
    except Exception as e:
        print(f"Error generating context with Gemini: {e}")
        return ""