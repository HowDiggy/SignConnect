# src/signconnect/routers/websockets.py

import asyncio
import json
from typing import List, Dict

from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends
from sqlalchemy.orm import Session
from google.cloud import speech
from .. import crud
# Import the new dependency and the client class
from ..dependencies import get_current_user_ws, get_db
from ..llm.client import GeminiClient
from ..schemas import User

router = APIRouter(
    prefix="/api",
)


class ConnectionManager:
    def __init__(self):
        self.active_connections: Dict[str, WebSocket] = {}

    async def connect(self, user_id: str, websocket: WebSocket):
        await websocket.accept()
        self.active_connections[user_id] = websocket
        print(f"User {user_id} connected. Total connections: {len(self.active_connections)}")

    def disconnect(self, user_id: str):
        if user_id in self.active_connections:
            del self.active_connections[user_id]
            print(f"User {user_id} disconnected. Total connections: {len(self.active_connections)}")

    async def send_personal_message(self, message: dict, websocket: WebSocket):
        await websocket.send_json(message)


manager = ConnectionManager()


@router.websocket("/ws")
async def websocket_endpoint(
    websocket: WebSocket,
    db: Session = Depends(get_db),
    user: dict = Depends(get_current_user_ws),
):
    """
    Handles the WebSocket connection, including real-time audio transcription.
    """
    await websocket.accept()
    print(f"WebSocket connection accepted for user: {user.get('email')}")

    # Get the LLM client from the application state
    llm_client: GeminiClient = websocket.app.state.llm_client

    # Create a queue to hold audio chunks from the client
    audio_queue = asyncio.Queue()

    # Define the function that will process the audio stream
    async def audio_processor():
        # Configure the Google Cloud Speech-to-Text client
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

        # This generator feeds audio chunks from our queue to the Google API
        async def request_generator():
            yield speech.StreamingRecognizeRequest(streaming_config=streaming_config)
            while True:
                chunk = await audio_queue.get()
                if chunk is None:
                    break
                yield speech.StreamingRecognizeRequest(audio_content=chunk)
                audio_queue.task_done()

        try:
            # Start the streaming recognition
            responses = await client.streaming_recognize(requests=request_generator())
            
            # Process the responses from the API
            async for response in responses:
                if not response.results:
                    continue

                result = response.results[0]
                if not result.alternatives:
                    continue

                transcript = result.alternatives[0].transcript
                
                # Send the transcript back to the frontend
                if result.is_final:
                    print(f"Final transcript: {transcript}")
                    await websocket.send_json({"type": "final_transcript", "data": transcript})
                else:
                    await websocket.send_json({"type": "interim_transcript", "data": transcript})

        except Exception as e:
            print(f"Error during transcription: {e}")
        finally:
            print("Audio processor finished.")

    # Start the audio processing task in the background
    process_task = asyncio.create_task(audio_processor())

    # Main loop to receive audio data from the client
    try:
        while True:
            # The frontend sends audio as bytes, so we use receive_bytes
            audio_chunk = await websocket.receive_bytes()
            await audio_queue.put(audio_chunk)
    except WebSocketDisconnect:
        print("Client disconnected.")
        # Signal the processor to stop by putting None in the queue
        await audio_queue.put(None)
    finally:
        # Wait for the processor to finish cleanly
        if not process_task.done():
            process_task.cancel()
        print("WebSocket connection closed.")