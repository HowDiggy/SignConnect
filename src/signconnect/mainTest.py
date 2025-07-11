import asyncio
import json
import uuid
from contextlib import asynccontextmanager
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Depends, HTTPException, Query, Header
from google.cloud import speech
from sqlalchemy.orm import Session

from . import crud, schemas
from .db import database, models
from .db.database import get_db
from .llm.client import get_response_suggestions
from .firebase import verify_firebase_token


@asynccontextmanager
async def lifespan(app: FastAPI):
    print("Application starting: Enabling pgvector extension...")
    database.enable_pgvector_extension()
    print("Creating database tables...")
    models.Base.metadata.create_all(bind=database.engine)
    yield
    print("Application shutdown.")


app = FastAPI(
    lifespan=lifespan,
    title="SignConnect API",
    description="API for the SignConnect assistive communication application.",
    version="0.1.0"
)


async def get_current_user(
        authorization: str | None = Header(None),
        token_from_query: str | None = Query(None, alias="token")
):
    token = None
    if authorization and authorization.startswith("Bearer "):
        token = authorization.split("Bearer ")[1]
    elif token_from_query:
        token = token_from_query

    if not token:
        raise HTTPException(status_code=401, detail="Not authenticated")

    user = verify_firebase_token(token)
    if not user:
        raise HTTPException(status_code=401, detail="Invalid authentication credentials")
    return user


@app.websocket("/ws")
async def websocket_endpoint(
        websocket: WebSocket,
        user: dict = Depends(get_current_user),
        db: Session = Depends(get_db),
):
    await websocket.accept()
    print(f"WebSocket connection established for user: {user.get('email')}")
    audio_queue = asyncio.Queue()
    receiver_task = asyncio.create_task(audio_receiver(websocket, audio_queue))
    processor_task = asyncio.create_task(audio_processor(websocket, audio_queue, user, db))

    done, pending = await asyncio.wait(
        [receiver_task, processor_task],
        return_when=asyncio.FIRST_COMPLETED,
    )
    for task in pending:
        task.cancel()
    print("WebSocket connection closed.")


async def audio_receiver(websocket: WebSocket, queue: asyncio.Queue):
    try:
        while True:
            data = await websocket.receive_bytes()
            await queue.put(data)
    except WebSocketDisconnect:
        print("Client disconnected (audio receiver).")


async def audio_processor(websocket: WebSocket, queue: asyncio.Queue, user: dict, db: Session):
    client = speech.SpeechAsyncClient()
    recognition_config = speech.RecognitionConfig(...)
    streaming_config = speech.StreamingRecognitionConfig(...)

    async def request_generator():
        yield speech.StreamingRecognizeRequest(streaming_config=streaming_config)
        while True:
            chunk = await queue.get()
            if chunk is None:
                break
            yield speech.StreamingRecognizeRequest(audio_content=chunk)

    try:
        async for response in await client.streaming_recognize(requests=request_generator()):
            for result in response.results:
                transcript = result.alternatives[0].transcript
                if result.is_final:
                    print(f"Final transcript: {transcript}")
                    await websocket.send_text(f"final: {transcript}")

                    db_user = crud.get_user_by_email(db, email=user.get("email"))
                    if not db_user:
                        continue

                    similar_question = crud.find_similar_question(db, query_text=transcript, user_id=db_user.id)
                    preferences = crud.get_user_preferences(db, user_id=db_user.id)

                    print("Getting personalized suggestions...")
                    suggestions_text = get_response_suggestions(
                        transcript=transcript,
                        similar_question=similar_question,
                        preferences=preferences
                    )

                    if suggestions_text:
                        suggestions_list = [s.strip() for s in suggestions_text.split('\n') if s.strip()]
                        print(f"Personalized suggestions: {suggestions_list}")
                        await websocket.send_text(f"suggestions:{json.dumps(suggestions_list)}")
                else:
                    print(f"Interim transcript: {transcript}")
                    await websocket.send_text(f"interim: {transcript}")

    except Exception as e:
        print(f"Error during transcription: {e}")
    finally:
        print("Stopped processing audio.")


@app.post("/users/me/scenarios/", response_model=schemas.Scenario)
def create_scenario(
        scenario: schemas.ScenarioCreate,
        db: Session = Depends(get_db),
        current_user: dict = Depends(get_current_user),
):
    firebase_user_email = current_user.get("email")
    db_user = crud.get_user_by_email(db, email=firebase_user_email)

    if db_user is None:
        user_to_create = schemas.UserCreate(
            email=firebase_user_email,
            username=current_user.get("name") or firebase_user_email,
            password="firebase_user_placeholder"
        )
        db_user = crud.create_user(db=db, user=user_to_create)

    existing_scenario = crud.get_scenario_by_name(db, name=scenario.name, user_id=db_user.id)
    if existing_scenario:
        raise HTTPException(status_code=400, detail="A scenario with this name already exists.")
    return crud.create_scenario(db=db, scenario=scenario, user_id=db_user.id)


@app.post("/users/me/scenarios/{scenario_id}/questions/", response_model=schemas.ScenarioQuestion)
def create_scenario_question(
        scenario_id: uuid.UUID,
        question: schemas.ScenarioQuestionCreate,
        db: Session = Depends(get_db),
        current_user: dict = Depends(get_current_user),
):
    db_user = crud.get_user_by_email(db, email=current_user.get("email"))
    db_scenario = crud.get_scenario(db, scenario_id=scenario_id)

    if db_scenario is None:
        raise HTTPException(status_code=404, detail="Scenario not found")

    if db_scenario.user_id != db_user.id:
        raise HTTPException(status_code=403, detail="Not authorized to add questions to this scenario.")

    return crud.create_scenario_question(db=db, question=question, scenario_id=scenario_id)


@app.post("/users/me/preferences/", response_model=schemas.UserPreference)
def create_preference(
        preference: schemas.UserPreferenceCreate,
        db: Session = Depends(get_db),
        current_user: dict = Depends(get_current_user),
):
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
    firebase_user_email = current_user.get("email")
    db_user = crud.get_user_by_email(db, email=firebase_user_email)
    if db_user is None:
        return []

    preferences = crud.get_user_preferences(db, user_id=db_user.id, skip=skip, limit=limit)
    return preferences


@app.get("/users/me/scenarios/", response_model=list[schemas.Scenario])
def read_scenarios_for_user(
        db: Session = Depends(get_db),
        current_user: dict = Depends(get_current_user)
):
    db_user = crud.get_user_by_email(db, email=current_user.get("email"))
    if not db_user:
        return []

    scenarios = crud.get_scenarios_by_user(db, user_id=db_user.id)
    return scenarios