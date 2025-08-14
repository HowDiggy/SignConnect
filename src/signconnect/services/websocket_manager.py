# src/signconnect/services/websocket_manager.py
import base64
import json
from typing import List, Any, Dict
from fastapi import WebSocket
from sqlalchemy.orm import Session
import asyncio

# Use absolute imports for our own modules
from signconnect import crud
from signconnect.llm.client import GeminiClient


class ConnectionManager:
    """Manages active WebSocket connections."""

    def __init__(self):
        """
        Initializes the ConnectionManager.

        Post-conditions:
        - self.active_connections is initialized as an empty list.
        """
        self.active_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        """
        Accepts and stores a new WebSocket connection.

        Pre-conditions:
        - `websocket` is a valid WebSocket object.

        Post-conditions:
        - The new WebSocket connection is accepted.
        - The WebSocket is added to the active_connections list.
        """
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        """
        Removes a WebSocket connection from the active list.

        Pre-conditions:
        - `websocket` is a WebSocket object that is in the active_connections list.

        Post-conditions:
        - The WebSocket is removed from the active_connections list.
        """
        self.active_connections.remove(websocket)

    async def send_personal_json(self, data: Any, websocket: WebSocket):
        """
        Sends a private JSON message to a single specific WebSocket connection.

        Pre-conditions:
        - `data` is a JSON-serializable object (like a dict or list).
        - `websocket` is a valid, active WebSocket object.
        """
        await websocket.send_json(data)

    async def broadcast_json(self, data: Any):
        """
        Broadcasts a JSON message to all active WebSocket connections.

        Pre-conditions:
        - `data` is a JSON-serializable object.

        Post-conditions:
        - The message is sent to every connected client.
        """
        # The frontend expects a JSON string, so we dump the data.
        message = json.dumps(data)
        for connection in self.active_connections:
            await connection.send_text(message)


async def handle_message(
    manager: ConnectionManager,
    websocket: WebSocket,
    message: Dict[str, Any],
    db: Session,
    user: Dict[str, Any],
    llm_client: GeminiClient,
    audio_queue: asyncio.Queue,
):
    """
    Processes a single JSON message from a WebSocket client.

    This function acts as a dispatcher, delegating tasks based on message type.
    """
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
                preferences = crud.get_user_preferences(db, user_id=db_user.id)
                preference_texts = [pref.preference_text for pref in preferences]
                conversation_history = []  # Placeholder for future enhancement

                suggestions = llm_client.get_response_suggestions(
                    transcript=transcript,
                    user_preferences=preference_texts,
                    conversation_history=conversation_history,
                )
            else:
                suggestions = ["Yes", "No", "Can you repeat that?"]  # Fallback

            await manager.send_personal_json(
                {"type": "suggestions", "data": suggestions}, websocket
            )

    elif msg_type == "ping":
        await manager.send_personal_json(
            {"type": "pong", "data": "Connection alive"}, websocket
        )

    else:
        print(f"Unknown message type: {msg_type}")
