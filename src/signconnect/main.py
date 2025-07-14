print("--- LOADING LATEST VERSION OF main.py ---")

import asyncio
import json
import uuid

from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Depends, HTTPException, Query, Header
from google.cloud import speech
from sqlalchemy.orm import Session
from fastapi.middleware.cors import CORSMiddleware

from . import crud, schemas
from .db import database, models
from .db.database import get_db
from contextlib import asynccontextmanager
from .llm.client import get_response_suggestions
from .firebase import verify_firebase_token

from .routers import users, scenarios, questions
from .dependencies import get_current_user


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Handles application startup and shutdown events.
    :param app:
    :return:
    """
    print("Application starting: Enabling pgvector extenstion...")
    # enable the pgvector extension first
    database.enable_pgvector_extension()

    print("Creating database tables...")
    # Create database tables
    models.Base.metadata.create_all(bind=database.engine)

    # Tell the main app to use the new router
    print("Including scenarios router...")
    app.include_router(scenarios.router)
    # tell the main app to use the users router
    print("Including users router...")
    app.include_router(users.router)
    # tell the main app to use the questions router
    print("Including questions router...")
    app.include_router(questions.router)

    # --- NEW DEBUGGING STEP ---
    print("\n--- Registered Routes ---")
    for route in app.routes:
        if hasattr(route, "path"):
            print(f"Path: {route.path}, Name: {route.name}")
    print("-----------------------\n")

    yield
    print("Appliccation shutdown.")

app = FastAPI(
    lifespan=lifespan,
    title="SignConnect API",
    description="API for the SignConnect assistive communication application.",
    version="0.1.0"
)

# --- ADD THIS CORS MIDDLEWARE CONFIGURATION ---
# This allows your frontend (running on port 63342) to communicate with your backend.
origins = [
    "http://localhost",
    "http://localhost:63342", # The origin for your IDE's dev server
    "http://127.0.0.1:63342",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"], # Allows all methods (GET, POST, etc.)
    allow_headers=["*"], # Allows all headers
)
# ---------------------------------------------

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


async def audio_processor(websocket: WebSocket, queue: asyncio.Queue, user: dict, db: Session):
    """
    Processes audio, finds similar questions, and gets personalized suggestions.
    """
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
                # alternative = result.alternatives[0]
                # transcript = alternative.transcript
                transcript = result.alternatives[0].transcript

                if result.is_final:

                    # Send final results with "final:" prefix
                    print(f"Final transcript: {transcript}")
                    await websocket.send_text(f"final: {transcript}")

                    # --- ENHANCED PERSONALIZATION LOGIC ---

                    # 1. Get the user's ID from our database
                    db_user = crud.get_user_by_email(db, email=user.get("email"))
                    if not db_user:
                        continue # skip if user not found in db

                    # 2. Find the most similar question the user has pre-configured
                    similar_question = crud.find_similar_question(db, query_text=transcript, user_id=db_user.id)

                    # 3. Get the user's general preferences
                    preferences = crud.get_user_preferences(db, user_id=db_user.id)

                    # 4. Construct a rich prompt for the LLM
                    print("Getting personalized suggestions...")
                    suggestions_text = get_response_suggestions(
                        transcript=transcript,
                        similar_question=similar_question,
                        preferences=preferences,
                    )

                    if suggestions_text:
                        # process the text into a list
                        suggestions_list = [s.strip() for s in suggestions_text.split('\n') if s.strip()]
                        print(f"Personalized suggestions: {suggestions_list}")

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
async def websocket_endpoint(
        websocket: WebSocket,
        user: dict = Depends(get_current_user),
        db: Session = Depends(get_db),
):

    """Main WebSocket endpoint to handle the bidirectional audio stream."""
    await websocket.accept()
    print(f"WebSocket connection established for user: {user.get('email')}")
    audio_queue = asyncio.Queue()

    receiver_task = asyncio.create_task(audio_receiver(websocket, audio_queue))

    # pass the user and b session to the processor task
    processor_task = asyncio.create_task(audio_processor(websocket, audio_queue, user, db))

    done, pending = await asyncio.wait(
        [receiver_task, processor_task],
        return_when=asyncio.FIRST_COMPLETED,
    )

    for task in pending:
        task.cancel()
    print("WebSocket connection closed.")


