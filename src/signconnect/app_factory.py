# src/signconnect/app_factory.py

from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from .llm.client import GeminiClient

from .core.config import Settings
from .db.database import Base
from .dependencies import get_db as get_db_dependency # Import the original dependency
from .routers import firebase, questions, scenarios, users, websockets


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Handles application startup and shutdown events.
    The database tables are created by the app factory.
    """
    # NOTE: You can add logic here that needs to run on startup,
    # for example, enabling database extensions if needed.
    print("Application starting up...")
    yield
    print("Application shutting down.")


def create_app(settings: Settings, testing: bool = False) -> FastAPI:
    """
    Application factory to create and configure the FastAPI app.

    Args:
        settings: The application settings object.
        testing (bool): If True, the app is created for a testing environment.
    """
    print(f"\n--- FACTORY: create_app() called with testing={testing} ---\n")

    lifespan_to_use = None if testing else lifespan
    engine = create_engine(settings.DATABASE_URL.get_secret_value())
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
        
    # Initialize the LLM client with the API key from settings
    llm_client = GeminiClient(api_key=settings.GEMINI_API_KEY.get_secret_value())

    # Store the client on the app state for easy access
    app.state.llm_client = llm_client

    # The factory is now responsible for creating tables.
    Base.metadata.create_all(bind=engine)

    def get_db_override():
        """
        Dependency override for getting a DB session.
        This is specific to this app instance.
        """
        db = SessionLocal()
        try:
            yield db
        finally:
            db.close()

    app = FastAPI(
        lifespan=lifespan_to_use,
        title="SignConnect API",
        version="0.1.0"
    )

    # CRITICAL: Override the dependency imported from dependencies.py
    app.dependency_overrides[get_db_dependency] = get_db_override

    # --- Add CORS Middleware ---
    origins = [
        "http://localhost",
        "http://localhost:55085",
        "http://127.0.0.1:55085",
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:63342",
        "http://127.0.0.1:63342",
        "https://signconnect.paulojauregui.com",
    ]
    app.add_middleware(
        CORSMiddleware,
        allow_origins=origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # --- Include Routers ---
    print("Including routers...")
    app.include_router(scenarios.router)
    app.include_router(users.router)
    app.include_router(questions.router)
    app.include_router(websockets.router)
    app.include_router(firebase.router)

    return app
