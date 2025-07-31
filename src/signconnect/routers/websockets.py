# src/signconnect/routers/websockets.py

import asyncio
import json
from typing import List, Dict

from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends
from sqlalchemy.orm import Session

from .. import crud
# Import the new dependency and the client class
from ..dependencies import get_current_user_ws, get_db, get_llm_client
from ..llm.client import GeminiClient
from ..schemas import User

router = APIRouter()


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


@router.websocket("/api/ws/{token}")
async def websocket_endpoint(
    websocket: WebSocket,
    token: str,
    db: Session = Depends(get_db),
    llm_client: GeminiClient = Depends(get_llm_client), # Add the new dependency
    user: dict = Depends(get_current_user_ws),
):
    """
    Handles the WebSocket connection for real-time communication.
    Authenticates the user, manages the connection, and provides LLM suggestions.
    """

    user_id = user["uid"]
    await manager.connect(user_id, websocket)

    try:
        while True:
            data = await websocket.receive_text()
            message_data = json.loads(data)
            transcript = message_data.get("transcript", "")
            conversation_history = message_data.get("conversation_history", [])

            if transcript:
                # 1. Get user preferences from the database
                db_user = crud.get_user_by_email(db, email=user["email"])
                if db_user:
                    preferences_db = crud.get_user_preferences(db, user_id=db_user.id)
                    preference_texts = [p.preference_text for p in preferences_db]
                else:
                    preference_texts = []

                # 2. Get suggestions from the LLM via the injected client
                suggestions = llm_client.get_response_suggestions(
                    transcript=transcript,
                    user_preferences=preference_texts,
                    conversation_history=conversation_history,
                )

                # 3. Send the suggestions back to the client
                await manager.send_personal_message(
                    {"type": "suggestions", "suggestions": suggestions},
                    websocket
                )

    except WebSocketDisconnect:
        manager.disconnect(user_id)
    except Exception as e:
        print(f"An error occurred in the WebSocket endpoint: {e}")
        manager.disconnect(user_id)