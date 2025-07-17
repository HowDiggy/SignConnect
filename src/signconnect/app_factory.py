# src/signconnect/app_factory.py

from fastapi import FastAPI
from contextlib import asynccontextmanager
from fastapi.middleware.cors import CORSMiddleware

# --- Core application and DB modules ---
from .db.database import Base, engine

def create_app() -> FastAPI:
    """
    Application factory to create and configure the FastAPI app.
    This is the single source of truth for app creation.
    """
    @asynccontextmanager
    async def lifespan(app: FastAPI):
        """Handles application startup and shutdown events."""
        # Import modules needed only for startup right here
        from .db import database, models

        print("Application starting: Enabling pgvector extension...")
        database.enable_pgvector_extension()

        print("Creating database tables...")
        models.Base.metadata.create_all(bind=engine)
        yield
        print("Application shutdown.")

    app = FastAPI(
        lifespan=lifespan,
        title="SignConnect API",
        description="API for the SignConnect assistive communication application.",
        version="0.1.0"
    )

    # --- Import and include all your routers ---
    from .routers import users, scenarios, questions, websockets
    print("Including routers...")
    app.include_router(scenarios.router)
    app.include_router(users.router)
    app.include_router(questions.router)
    app.include_router(websockets.router)

    # --- Add CORS Middleware ---
    origins = [
        "http://localhost",
        "http://localhost:63342",
        "http://127.0.0.1:63342",
    ]
    app.add_middleware(
        CORSMiddleware,
        allow_origins=origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    return app