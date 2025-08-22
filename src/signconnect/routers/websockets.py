# src/signconnect/routers/websockets.py

import asyncio
from fastapi import (
    APIRouter,
    WebSocket,
    WebSocketDisconnect,
    Depends,
    WebSocketException,
    status,
)
from sqlalchemy.orm import Session
from google.cloud import speech
import structlog

from signconnect.services import websocket_manager as manager_service
from signconnect.dependencies import get_db
from signconnect.firebase import verify_firebase_token

logger = structlog.get_logger(__name__)

router = APIRouter(prefix="/api", tags=["websockets"])
manager = manager_service.ConnectionManager()


async def audio_processor(websocket: WebSocket, audio_queue: asyncio.Queue):
    """
    Processes audio from a queue and sends transcripts back to the client.
    This function runs as a background task for each connection.
    """
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
            msg_type = (
                "final_transcript"
                if response.results[0].is_final
                else "interim_transcript"
            )
            await manager.send_personal_json(
                {"type": msg_type, "data": transcript}, websocket
            )
    except Exception as e:
        logger.exception(f"Error during transcription: {e}")
    finally:
        logger.info("Audio processor finished.")


async def authenticated_websocket_handler(websocket: WebSocket, db: Session) -> dict:
    """
    Handles the initial authentication phase of the WebSocket connection.
    """
    await websocket.accept()
    try:
        token = await websocket.receive_text()
        user = verify_firebase_token(token)
        if not user:
            raise WebSocketException(
                code=status.WS_1008_POLICY_VIOLATION,
                reason="Invalid authentication token",
            )
        return user
    except WebSocketException as e:
        await websocket.close(code=e.code, reason=e.reason)
        raise
    except Exception as e:
        await websocket.close(
            code=status.WS_1011_INTERNAL_ERROR,
            reason=f"An unexpected error occurred: {e}",
        )
        raise


@router.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket, db: Session = Depends(get_db)):
    """
    Acts as a coordinator for the WebSocket connection.
    - Manages connection lifecycle.
    - Starts the audio processing task.
    - Listens for incoming messages and delegates them to the message handler.
    """
    user = None
    try:
        user = await authenticated_websocket_handler(websocket, db)
        await manager.connect(websocket)
        logger.info(f"WebSocket connection accepted for user: {user.get('email')}")

        llm_client = websocket.app.state.llm_client
        audio_queue = asyncio.Queue()
        process_task = asyncio.create_task(audio_processor(websocket, audio_queue))

        while True:
            message = await websocket.receive_json()
            await manager_service.handle_message(
                manager=manager,
                websocket=websocket,
                message=message,
                db=db,
                user=user,
                llm_client=llm_client,
                audio_queue=audio_queue,
            )

    except WebSocketDisconnect:
        logger.info(
            f"Client disconnected: {user.get('email') if user else 'unauthenticated'}"
        )
    except Exception as e:
        logger.exception(
            f"WebSocket error for user {user.get('email') if user else 'unauthenticated'}: {e}"
        )
    finally:
        if user:
            manager.disconnect(websocket)
            # 1. Gracefully tell the audio processor to exit its loop
            await audio_queue.put(None)
            # 2. Cancel the background task if it's still running
            if not process_task.done():
                process_task.cancel()
            try:
                # 3. Wait for the task to acknowledge the cancellation
                await process_task
            except asyncio.CancelledError:
                pass  # This is expected on cancellation
            logger.info(
                f"Connection closed and resources cleaned up for {user.get('email')}."
            )
