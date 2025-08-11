# src/signconnect/app_factory.py

from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from .llm.client import GeminiClient

from .core.config import Settings
from .db.models import Base  # Corrected import for Base
from .dependencies import get_db as get_db_dependency
from .routers import firebase, questions, scenarios, users, websockets


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Handles application startup and shutdown events.
    """
    print("Application starting up...")
    yield
    print("Application shutting down.")


def create_app(settings: Settings, testing: bool = False) -> FastAPI:
    """
    Application factory to create and configure the FastAPI app.
    """
    print(f"\n--- FACTORY: create_app() called with testing={testing} ---\n")

    # The factory is now responsible for creating the engine and SessionLocal
    # Using the computed DATABASE_URL from the settings object
    engine = create_engine(str(settings.DATABASE_URL))
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

    # The factory is also responsible for creating all tables
    Base.metadata.create_all(bind=engine)

    # Initialize the LLM client
    llm_client = GeminiClient(api_key=settings.GEMINI_API_KEY.get_secret_value())

    app = FastAPI(
        lifespan=None if testing else lifespan,
        title="SignConnect API",
        version="0.1.0"
    )

    # Store the client on the app state for easy access via dependencies
    app.state.llm_client = llm_client

    def get_db_override():
        """Dependency override for getting a DB session."""
        db = SessionLocal()
        try:
            yield db
        finally:
            db.close()

    # CRITICAL: Override the dependency
    app.dependency_overrides[get_db_dependency] = get_db_override

    # Add CORS Middleware
    origins = [
        "http://localhost", "http://localhost:5173",
        "https://signconnect.paulojauregui.com",
    ]
    app.add_middleware(
        CORSMiddleware,
        allow_origins=origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Include Routers
    app.include_router(scenarios.router)
    app.include_router(users.router)
    app.include_router(questions.router)
    app.include_router(websockets.router)
    app.include_router(firebase.router)

    return app