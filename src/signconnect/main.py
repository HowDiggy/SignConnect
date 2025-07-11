import asyncio
import json
import uuid

from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Depends, HTTPException, Query, Header
from google.cloud import speech
from sqlalchemy.orm import Session

from . import crud, schemas
from .db import database, models
from .db.database import get_db
from contextlib import asynccontextmanager
from .llm.client import get_response_suggestions
from .firebase import verify_firebase_token


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


async def get_current_user(
        authorization: str | None = Header(None),
        token_from_query: str | None = Query(None, alias="token")
):
    """
    Dependency to verify a Firebase token from either the Authorization header
    (for HTTP requests) or a query parameter (for WebSocket connections).
    """
    token = None
    if authorization and authorization.startswith("Bearer "):
        # Extract token from "Bearer <token>" header
        token = authorization.split("Bearer ")[1]
    elif token_from_query:
        # Use token from query parameter
        token = token_from_query

    if not token:
        raise HTTPException(
            status_code=401,
            detail="Not authenticated",
            headers={"WWW-Authenticate": "Bearer"},
        )

    user = verify_firebase_token(token)
    if not user:
        raise HTTPException(
            status_code=401,
            detail="Invalid authentication credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return user


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

# --- User Endpoints ---


# --- Preference Endpoints ---
@app.post("/users/me/preferences/", response_model=schemas.UserPreference)
def create_preference(
        preference: schemas.UserPreferenceCreate,
        db: Session = Depends(get_db),
        current_user: dict = Depends(get_current_user),
):
    """
    Create a new preference for the currently authenticated user.
    If the user doesn't exist in the local DB, create them first.

    :param preference:
    :param db:
    :param current_user:
    :return:
    """

    firebase_user_email = current_user.get("email")
    db_user = crud.get_user_by_email(db, email=firebase_user_email)

    if db_user is None:
        user_to_create = schemas.UserCreate(
            email=firebase_user_email,
            username=current_user.get("name") or firebase_user_email,
            password="firebase_user_placeholder"
        )
        db_user = crud.create_user(db=db, user=user_to_create)

    return crud.create_user_preference(db=db, preference=preference, user_id=db_user.id)

@app.get("/users/me/preferences/", response_model=list[schemas.UserPreference])
def read_user_preferences(
        skip: int = 0,
        limit: int = 100,
        db: Session = Depends(get_db),
        current_user: dict = Depends(get_current_user),
):
    """
    Retrieve all preferences for currently authenticated user.
    
    :param skip: 
    :param limit: 
    :param db: 
    :param current_user: 
    :return: 
    """
    firebase_user_email = current_user.get("email")
    db_user = crud.get_user_by_email(db, email=firebase_user_email)
    if db_user is None:
        raise HTTPException(status_code=404, detail="User not found")

    preferences = crud.get_user_preferences(db, user_id=db_user.id, skip=skip, limit=limit)
    return preferences

# --- Scenario and Question Endpoints ---
@app.post("/scenarios/", response_model=schemas.Scenario)
def create_scenario(
        scenario: schemas.ScenarioCreate,
        db: Session = Depends(get_db),
        current_user: dict = Depends(get_current_user),
):
    """
    Create a new scenario for the currently authenticated user.
    If the user doesn't exist in the local DB, create them first.

    :param scenario:
    :param db:
    :param current_user:
    :return:
    """
    firebase_user_email = current_user.get("email")
    db_user = crud.get_user_by_email(db, email=firebase_user_email)

    # if user doesn't exist in our DB, create them now
    if db_user is None:
        user_to_create = schemas.UserCreate(
            email=firebase_user_email,
            username=current_user.get("username") or firebase_user_email,
            password= "firebase_user_password",
        )
        db_user = crud.create_user(db=db, user=user_to_create)


    # Check if a scenario with this name already exists for this user
    existing_scenario = crud.get_scenario_by_name(db, name=scenario.name, user_id=db_user.id)
    if existing_scenario:
        raise HTTPException(
            status_code=400,
            detail="A scenario with that name already exists."
        )

    return crud.create_scenario(db=db, scenario=scenario, user_id=db_user.id)

@app.post("/scenarios/{scenario_id}/questions/", response_model=schemas.ScenarioQuestion)
def create_scenario_question(
        scenario_id: uuid.UUID,
        question: schemas.ScenarioQuestionCreate,
        db: Session = Depends(get_db),
        current_user: dict = Depends(get_current_user),
):
    """
    Create a new pre-configured question for one of the user's scenarios, ensuring the user owns the parent scenario.

    :param scenario_id:
    :param question:
    :param db:
    :param current_user:
    :return:
    """
    db_user = crud.get_user_by_email(db, email=current_user.get("email"))

    # get the scenario from the database
    db_scenario = crud.get_scenario(db, scenario_id=scenario_id)

    # security check: ensure the scenario exists and belongs to the current user
    if db_scenario is None:
        raise HTTPException(status_code=404, detail="Scenario not found")

    if db_scenario.user_id != db_user.id:
        raise HTTPException(status_code=403, detail="Not authorized to add questions to this scenario.")

    return crud.create_scenario_question(db=db, question=question, scenario_id=scenario_id)