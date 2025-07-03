from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from sqlalchemy.orm import Session
from signconnect.db import models, database, crud
from signconnect.core.config import get_settings

# This command tell SQLAlchemy to create all the tables defined in our models.py file in the database.
models.Base.metadata.create_all(bind=database.engine)

app = FastAPI(
    title="SignConnect API",
    description="API for the SignConnect assistive communication application",
    version="0.1.0"
)

# A simple endpoint to check if the API is running
@app.get("/")
async def root():
    """
    A simple root endpoint to confirm the API is running.
    :return:
    """
    return {"message": f"Welcome to SignConnect API v{app.version}"}


@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """
    The main WebSocket endpoint for real-time communication.
    It accepts a connection and currently just echoes back any message it received.
    :param websocket:
    :return:
    """
    await websocket.accept()
    try:
        while True:
            # For now, we'll just receive text and echo it back.
            # Later, this will handle receiving audio data.
            data = await websocket.receive_text()
            await websocket.send_text(f"Message received: {data}")
    except WebSocketDisconnect:
        print("Client disconnected")
