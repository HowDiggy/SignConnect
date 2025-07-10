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

    # --- dynamically build rich prompt ---

    prompt_parts = [
        "You are an assistant for a deaf or hard-of-hearing person.",
        "Based on the following information, provide three concise, natural-sounding responses that the user can say.",
        "Each response should be on a new line, with no extra formatting.",
        f'\nTranscript of what was just said: "{transcript}"'
    ]


    # add the similar question context if one was found
    if similar_question:
        prompt_parts.append(
            "\nThis is similar to the pre-configured question the user has saved."
        )
        prompt_parts.append(
            f'User\'s pre-configured question: "{similar_question.question_text}"'
        )
        prompt_parts.append(
            f'User\'s pre-configured answer: "{similar_question.user_answer_text}"'
        )
        prompt_parts.append(
            "One of your suggestions should be very similar to the user's pre-configured answer."
        )

    # add the user's general preferences if they exist
    if preferences:
        prompt_parts.append("\nConsider the user's general preferences:")
        for pref in preferences:
            prompt_parts.append(f'- {pref.category}: {pref.preference_text}')

    prompt_parts.append("\nResponses:")

    # join all parts into a single prompt string
    prompt = "\n".join(prompt_parts)
    print(f"--- Generated Prompt for Gemini ---\n{prompt}\n------------------------------")

    try:
        response = model.generate_content(prompt)
        return response.text
    except Exception as e:
        print(f"Error generating context with Gemini: {e}")
        return ""
