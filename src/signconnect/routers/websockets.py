# src/signconnect/routers/websockets.py

import asyncio
import json
import base64
from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from google.cloud import speech
from sqlalchemy.orm import Session
from .. import crud
from ..db.database import get_db
from ..llm.client import get_response_suggestions
from ..firebase import verify_firebase_token

router = APIRouter(tags=["websockets"])


class SpeechStreamManager:
    """
    Manages Google Speech API streaming sessions with automatic restart on timeout.
    """

    def __init__(self, websocket: WebSocket, user: dict, db: Session):
        self.websocket = websocket
        self.user = user
        self.db = db
        self.client = speech.SpeechAsyncClient()
        self.audio_queue = asyncio.Queue()
        self.is_running = False

        self.recognition_config = speech.RecognitionConfig(
            encoding=speech.RecognitionConfig.AudioEncoding.WEBM_OPUS,
            sample_rate_hertz=48000,
            language_code="en-US",
            enable_automatic_punctuation=True,
        )
        self.streaming_config = speech.StreamingRecognitionConfig(
            config=self.recognition_config, interim_results=True
        )

    async def start(self):
        """Start the speech recognition loop."""
        self.is_running = True
        while self.is_running:
            try:
                await self._run_speech_session()
            except Exception as e:
                print(f"Speech session error: {e}")
                if self.is_running:
                    print("Restarting speech session in 1 second...")
                    await asyncio.sleep(1)
                else:
                    break

    async def stop(self):
        """Stop the speech recognition loop."""
        self.is_running = False
        await self.audio_queue.put(None)  # Signal to stop

    async def add_audio(self, audio_data: bytes):
        """Add audio data to the processing queue."""
        if self.is_running:
            await self.audio_queue.put(audio_data)

    async def _run_speech_session(self):
        """Run a single speech recognition session."""
        print("Starting new speech recognition session...")

        async def request_generator():
            """Generate requests for the Speech API."""
            yield speech.StreamingRecognizeRequest(
                streaming_config=self.streaming_config
            )
            while self.is_running:
                try:
                    chunk = await asyncio.wait_for(self.audio_queue.get(), timeout=30.0)
                    if chunk is None or not self.is_running:
                        break
                    yield speech.StreamingRecognizeRequest(audio_content=chunk)
                except asyncio.TimeoutError:
                    print("No audio received for 30 seconds, restarting session...")
                    break

        try:
            responses = await self.client.streaming_recognize(
                requests=request_generator()
            )
            async for response in responses:
                if not self.is_running:
                    break

                for result in response.results:
                    transcript = result.alternatives[0].transcript
                    if result.is_final:
                        print(f"Final transcript: {transcript}")
                        await self.websocket.send_text(f"final:{transcript}")

                        # Generate suggestions
                        await self._generate_suggestions(transcript)
                    else:
                        await self.websocket.send_text(f"interim:{transcript}")

        except Exception as e:
            print(f"Speech recognition error: {e}")
            if "timeout" in str(e).lower() or "400" in str(e):
                print("Google Speech API timeout - will restart session")
            else:
                raise e

    async def _generate_suggestions(self, transcript: str):
        """Generate AI suggestions for the transcript."""
        try:
            db_user = crud.get_user_by_email(self.db, email=self.user.get("email"))
            if not db_user:
                return

            similar_question = crud.find_similar_question(
                self.db, query_text=transcript, user_id=db_user.id
            )
            preferences = crud.get_user_preferences(self.db, user_id=db_user.id)

            print("Getting personalized suggestions...")
            suggestions_text = get_response_suggestions(
                transcript=transcript,
                similar_question=similar_question,
                preferences=preferences,
            )

            if suggestions_text:
                suggestions_list = [
                    s.strip() for s in suggestions_text.split("\n") if s.strip()
                ]
                await self.websocket.send_text(
                    f"suggestions:{json.dumps(suggestions_list)}"
                )
        except Exception as e:
            print(f"Error generating suggestions: {e}")


@router.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """
    Secure WebSocket endpoint that handles authentication via post-connection handshake.
    """
    await websocket.accept()
    print("WebSocket connection established, waiting for authentication...")

    user = None
    db = None
    authenticated = False
    speech_manager = None

    try:
        # Wait for authentication message within 10 seconds
        auth_message = await asyncio.wait_for(websocket.receive_json(), timeout=10.0)

        if auth_message.get("type") != "authenticate":
            await websocket.send_text("auth_failed")
            await websocket.close(code=4001, reason="Authentication required")
            return

        token = auth_message.get("token")
        if not token:
            await websocket.send_text("auth_failed")
            await websocket.close(code=4001, reason="Token required")
            return

        # Verify the Firebase token
        user = verify_firebase_token(token)
        if not user:
            await websocket.send_text("auth_failed")
            await websocket.close(code=4001, reason="Invalid token")
            return

        # Get database session
        db_gen = get_db()
        db = next(db_gen)

        authenticated = True
        await websocket.send_text("auth_success")
        print(f"WebSocket authenticated for user: {user.get('email')}")

        # Initialize speech manager
        speech_manager = SpeechStreamManager(websocket, user, db)

    except asyncio.TimeoutError:
        print("WebSocket authentication timeout")
        await websocket.send_text("auth_failed")
        await websocket.close(code=4001, reason="Authentication timeout")
        return
    except Exception as e:
        print(f"WebSocket authentication error: {e}")
        await websocket.send_text("auth_failed")
        await websocket.close(code=4001, reason="Authentication error")
        return

    if not authenticated:
        return

    # Start speech recognition
    speech_task = asyncio.create_task(speech_manager.start())

    try:
        while True:
            message = await websocket.receive_json()
            msg_type = message.get("type")

            if msg_type == "audio":
                audio_data = message.get("data")
                if audio_data:
                    try:
                        decoded_audio = base64.b64decode(audio_data)
                        await speech_manager.add_audio(decoded_audio)
                    except Exception as e:
                        print(f"Error decoding audio: {e}")

            elif msg_type == "get_suggestions":
                transcript = message.get("transcript")
                if transcript and speech_manager:
                    await speech_manager._generate_suggestions(transcript)

    except WebSocketDisconnect:
        print("Client disconnected.")
    except Exception as e:
        print(f"Main processing loop error: {e}")
    finally:
        # Cleanup
        if speech_manager:
            await speech_manager.stop()

        if speech_task and not speech_task.done():
            speech_task.cancel()
            try:
                await speech_task
            except asyncio.CancelledError:
                pass

        # Close database session
        if db:
            try:
                next(db_gen, None)  # Close the generator
            except StopIteration:
                pass

        print("WebSocket connection closed and resources cleaned up.")
