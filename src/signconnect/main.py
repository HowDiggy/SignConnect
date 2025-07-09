import asyncio
import json
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from google.cloud import speech
from fastapi import Depends, HTTPException
from sqlalchemy.orm import Session
from signconnect import crud, schemas
from signconnect.db import database, models
from signconnect.db.database import get_db
from contextlib import asynccontextmanager
from signconnect.llm.client import get_response_suggestions


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Handles application startup and shutdown events.
    :param app:
    :return:
    """
    print("Application startup: Creating database tables...")
    # Create database tables
    models.Base.metadata.create_all(bind=database.engine)
    yield
    print("Appliccation shutdown.")


app = FastAPI(
    lifespan=lifespan,
    title="SignConnect API",
    description="API for the SignConnect assistive communication application.",
    version="0.1.0"
)


# --- WebSocket Transcription Logic ---

async def audio_receiver(websocket: WebSocket, queue: asyncio.Queue):
    """Receives audio chunks from the client and puts them into a queue."""
    try:
        while True:
            data = await websocket.receive_bytes()
            # CHECKPOINT 1: Confirm we are receiving audio from the frontend
            print(f"Received {len(data)} bytes from client.")
            await queue.put(data)
    except WebSocketDisconnect:
        print("Client disconnected (audio receiver).")


async def audio_processor(websocket: WebSocket, queue: asyncio.Queue):
    """Processes audio from the queue and sends it to Google Speech-to-Text."""
    client = speech.SpeechAsyncClient()

    recognition_config = speech.RecognitionConfig({
        "encoding": speech.RecognitionConfig.AudioEncoding.WEBM_OPUS,
        "sample_rate_hertz": 48000,
        "language_code": "en-US",
        "enable_automatic_punctuation": True,
    })
    streaming_config = speech.StreamingRecognitionConfig({
        "config": recognition_config,
        "interim_results": True
    })

    async def request_generator():
        """Yields audio chunks from the queue to send to Google."""
        yield speech.StreamingRecognizeRequest(streaming_config=streaming_config)
        while True:
            chunk = await queue.get()
            if chunk is None:
                break
            yield speech.StreamingRecognizeRequest(audio_content=chunk)

    try:
        async for response in await client.streaming_recognize(requests=request_generator()):
            for result in response.results:
                # Get the first alternative from the result
                alternative = result.alternatives[0]
                transcript = alternative.transcript

                if result.is_final:
                    # Send final results with "final:" prefix
                    print(f"Final transcript: {transcript}")
                    await websocket.send_text(f"final: {transcript}")

                    # call the Gemini API
                    print("Getting suggestions from Gemini...")
                    suggestions_text = get_response_suggestions(transcript)

                    if suggestions_text:
                        # process the text into a list
                        suggestions_list = [s.strip() for s in suggestions_text.split('\n') if s.strip()]
                        print(f"Gemini suggestions: {suggestions_list}")

                    # send the list as a JSON string with a prefix
                    await websocket.send_text(f"suggestions:{json.dumps(suggestions_list)}")

                else:
                    # Send interim results with "interim:" prefix
                    print(f"Interim transcript: {transcript}")
                    await websocket.send_text(f"interim: {transcript}")

    except Exception as e:
        print(f"Error during transcription: {e}")
    finally:
        print("Stopped processing audio.")

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """Main WebSocket endpoint to handle the bidirectional audio stream."""
    await websocket.accept()
    audio_queue = asyncio.Queue()

    receiver_task = asyncio.create_task(audio_receiver(websocket, audio_queue))
    processor_task = asyncio.create_task(audio_processor(websocket, audio_queue))

    done, pending = await asyncio.wait(
        [receiver_task, processor_task],
        return_when=asyncio.FIRST_COMPLETED,
    )

    for task in pending:
        task.cancel()
    print("WebSocket connection closed.")

# --- User Endpoints ---

@app.post("/users/", response_model=schemas.User)
def create_user(user: schemas.UserCreate, db: Session = Depends(get_db)):
    """
    Endpoint to create a new user.
    :param user:
    :param db:
    :return:
    """

    db_user = crud.get_user_by_email(db, email=user.email)
    if db_user:
        raise HTTPException(status_code=400, detail="User with this email already exists.")
    return crud.create_user(db=db, user=user)