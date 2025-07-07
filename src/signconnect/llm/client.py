import google.generativeai as genai
from ..core.config import get_settings

# configure the client with the API key from our settings
genai.configure(api_key=get_settings().GEMINI_API_KEY)

def get_response_suggestions(transcript: str) -> str:
    """
    Genereates response suggestions gor a given transcript using Gemini API.
    :param transcript:
    :return:
    """

    # For initializing the model, 'gemini-pro' is a good choice for this task
    model = genai.GenerativeModel('gemini-1.5-flash')

    prompt = f"""
    You are an assistant for a deaf or hard-of-hearing person.
    Based on the following transcribed text, provide three concise, natural-sounding responses that the user can say.
    Each response should be on a new line, with no extra formatting.
    
    Transcript: "{transcript}"
    
    Responses:
    """

    try:
        response = model.generate_content(prompt)
        return response.text
    except Exception as e:
        print(f"Error generating context with Gemini: {e}")
        return ""
