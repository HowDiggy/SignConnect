# src/signconnect/llm/client.py

import google.generativeai as genai
from typing import List

class GeminiClient:
    """
    A client for interacting with the Google Gemini API.

    This class encapsulates the configuration and model interaction,
    making it easy to manage and inject as a dependency.
    """
    def __init__(self, api_key: str):
        """
        Initializes the Gemini client and configures the API key.

        Args:
            api_key: The Google Gemini API key.
        """
        genai.configure(api_key=api_key)
        self.model = genai.GenerativeModel('gemini-pro')
        print("GeminiClient initialized successfully.")

    def get_response_suggestions(
        self,
        transcript: str,
        user_preferences: List[str],
        conversation_history: List[str]
    ) -> List[str]:
        """
        Generates conversational response suggestions based on the transcript
        and user context.

        Args:
            transcript: The latest transcript of the conversation.
            user_preferences: A list of user-specific details or preferences.
            conversation_history: A list of previous messages in the conversation.

        Returns:
            A list of three suggested responses, or an empty list if an error occurs.
        """
        try:
            # Constructing the prompt with clear context for the model
            prompt = (
                "You are an AI assistant for a deaf or hard-of-hearing person. "
                "Your goal is to provide three concise, natural-sounding, and relevant "
                "response suggestions to the ongoing conversation. The user will provide "
                "the latest transcript, their personal context, and the conversation history.\n\n"
                "**User's Personal Context:**\n"
                f"- {', '.join(user_preferences)}\n\n"
                "**Conversation History:**\n"
                f"{' '.join(conversation_history)}\n\n"
                "**Latest Transcript (what the other person just said):**\n"
                f'"{transcript}"\n\n'
                "Based on all this information, provide exactly three brief and "
                "relevant response suggestions, each on a new line, without any "
                "numbering or bullet points."
            )

            response = self.model.generate_content(prompt)

            # Clean up the response and split into a list
            suggestions = [
                line.strip() for line in response.text.split('\n') if line.strip()
            ]
            return suggestions[:3]  # Ensure we only return up to 3 suggestions

        except Exception as e:
            print(f"Error generating suggestions from Gemini: {e}")
            return []

