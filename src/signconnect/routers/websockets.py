import asyncio
import base64
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends
from google.cloud import speech
from sqlalchemy.orm import Session

from .. import crud
from ..dependencies import get_current_user_ws, get_db
from ..llm.client import GeminiClient

router = APIRouter(prefix="/api", tags=["websockets"])


@router.websocket("/ws")
async def websocket_endpoint(
    websocket: WebSocket,
    db: Session = Depends(get_db),
    user: dict = Depends(get_current_user_ws),
):
    """
    Handles the WebSocket connection for real-time transcription and suggestions.

    - Receives: JSON messages of type 'audio', 'get_suggestions', or 'ping'.
    - Sends: JSON messages of type 'final_transcript', 'interim_transcript', or 'suggestions'.
    """
    await websocket.accept()
    print(f"WebSocket connection accepted for user: {user.get('email')}")

    # The llm_client is correctly retrieved from the application state
    llm_client: GeminiClient = websocket.app.state.llm_client
    audio_queue = asyncio.Queue()

    async def audio_processor():
        """Processes audio from the queue and sends transcripts to the client."""
        client = speech.SpeechAsyncClient()
        config = speech.RecognitionConfig(
            encoding=speech.RecognitionConfig.AudioEncoding.WEBM_OPUS,
            sample_rate_hertz=48000,
            language_code="en-US",
            enable_automatic_punctuation=True,
            model="latest_long",
        )
        streaming_config = speech.StreamingRecognitionConfig(
            config=config, interim_results=True
        )

        async def request_generator():
            yield speech.StreamingRecognizeRequest(streaming_config=streaming_config)
            while True:
                chunk = await audio_queue.get()
                if chunk is None:
                    break
                yield speech.StreamingRecognizeRequest(audio_content=chunk)
                audio_queue.task_done()

        try:
            responses = await client.streaming_recognize(requests=request_generator())
            async for response in responses:
                if not response.results or not response.results[0].alternatives:
                    continue

                transcript = response.results[0].alternatives[0].transcript

                # Send structured JSON messages, which is the core of the refactor
                if response.results[0].is_final:
                    print(f"Final transcript: {transcript}")
                    await websocket.send_json(
                        {"type": "final_transcript", "data": transcript}
                    )
                else:
                    await websocket.send_json(
                        {"type": "interim_transcript", "data": transcript}
                    )
        except Exception as e:
            print(f"Error during transcription: {e}")
        finally:
            print("Audio processor finished.")

    process_task = asyncio.create_task(audio_processor())

    try:
        while True:
            # Always expect JSON from the frontend
            message = await websocket.receive_json()
            msg_type = message.get("type")

            if msg_type == "audio":
                # Handle incoming audio chunks
                audio_chunk = base64.b64decode(message["data"])
                await audio_queue.put(audio_chunk)

            elif msg_type == "get_suggestions":
                # Use the LLM client to generate suggestions
                transcript = message.get("transcript", "")
                if transcript:
                    print(f"Received request for suggestions for: {transcript}")

                    # Get user data for personalized suggestions
                    db_user = crud.get_user_by_email(db, email=user.get("email"))
                    if db_user:
                        # Get user preferences
                        preferences = crud.get_user_preferences(db, user_id=db_user.id)
                        preference_texts = [
                            pref.preference_text for pref in preferences
                        ]

                        # For now, use empty conversation history - you could enhance this
                        conversation_history = []

                        # Generate suggestions using the LLM client
                        suggestions = llm_client.get_response_suggestions(
                            transcript=transcript,
                            user_preferences=preference_texts,
                            conversation_history=conversation_history,
                        )
                    else:
                        # Fallback if user not found
                        suggestions = ["Yes", "No", "Can you repeat that?"]

                    await websocket.send_json(
                        {"type": "suggestions", "data": suggestions}
                    )

            elif msg_type == "ping":
                # Handle ping messages for testing
                await websocket.send_json({"type": "pong", "data": "Connection alive"})

            else:
                # Unknown message type
                print(f"Unknown message type: {msg_type}")

    except WebSocketDisconnect:
        print("Client disconnected.")
    except Exception as e:
        print(f"WebSocket error: {e}")
    finally:
        # Gracefully shut down the background task
        await audio_queue.put(None)
        if not process_task.done():
            process_task.cancel()
        try:
            await process_task
        except asyncio.CancelledError:
            pass
        print("WebSocket connection closed and resources cleaned up.")
