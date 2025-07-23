# src/signconnect/routers/websockets.py

import asyncio
import json
import base64
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends
from google.cloud import speech
from sqlalchemy.orm import Session
from .. import crud
from ..dependencies import get_current_user
from ..db.database import get_db
from ..llm.client import get_response_suggestions

router = APIRouter(tags=["websockets"])


@router.websocket("/ws")
async def websocket_endpoint(
        websocket: WebSocket,
        user: dict = Depends(get_current_user),
        db: Session = Depends(get_db),
):
    await websocket.accept()
    print(f"WebSocket connection established for user: {user.get('email')}")

    client = speech.SpeechAsyncClient()
    recognition_config = speech.RecognitionConfig(
        encoding=speech.RecognitionConfig.AudioEncoding.WEBM_OPUS,
        sample_rate_hertz=48000,
        language_code="en-US",
        enable_automatic_punctuation=True,
    )
    streaming_config = speech.StreamingRecognitionConfig(
        config=recognition_config, interim_results=True
    )

    audio_queue = asyncio.Queue()

    async def request_generator():
        """Yields audio chunks from the queue to send to Google."""
        yield speech.StreamingRecognizeRequest(streaming_config=streaming_config)
        while True:
            chunk = await audio_queue.get()
            if chunk is None:
                break
            yield speech.StreamingRecognizeRequest(audio_content=chunk)

    async def response_handler():
        """Listens for transcription results from Google and sends them to the client."""
        try:
            responses = await client.streaming_recognize(requests=request_generator())
            async for response in responses:
                for result in response.results:
                    transcript = result.alternatives[0].transcript
                    if result.is_final:
                        print(f"Final transcript: {transcript}")
                        await websocket.send_text(f"final:{transcript}")
                    else:
                        await websocket.send_text(f"interim:{transcript}")
        except asyncio.CancelledError:
            print("Transcription listener cancelled.")
        except Exception as e:
            print(f"Error in transcription listener: {e}")

    transcription_task = asyncio.create_task(response_handler())

    try:
        while True:
            message = await websocket.receive_json()
            msg_type = message.get("type")

            if msg_type == "audio":
                await audio_queue.put(base64.b64decode(message.get("data")))
            elif msg_type == "get_suggestions":
                transcript = message.get("transcript")
                if not transcript:
                    continue

                db_user = crud.get_user_by_email(db, email=user.get("email"))
                if not db_user:
                    continue

                similar_question = crud.find_similar_question(db, query_text=transcript, user_id=db_user.id)
                preferences = crud.get_user_preferences(db, user_id=db_user.id)

                print("Getting personalized suggestions...")
                suggestions_text = get_response_suggestions(
                    transcript=transcript,
                    similar_question=similar_question,
                    preferences=preferences,
                )
                if suggestions_text:
                    suggestions_list = [s.strip() for s in suggestions_text.split('\n') if s.strip()]
                    await websocket.send_text(f"suggestions:{json.dumps(suggestions_list)}")

    except WebSocketDisconnect:
        print("Client disconnected.")
    except Exception as e:
        print(f"Main processing loop error: {e}")
    finally:
        await audio_queue.put(None)
        if not transcription_task.done():
            transcription_task.cancel()
        await transcription_task
        print("WebSocket connection closed and resources cleaned up.")