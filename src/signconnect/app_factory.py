# src/signconnect/app_factory.py

from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import structlog
import sentry_sdk

from .core.config import Settings

# Import the new logging configuration function
from .core.logging import configure_logging
from .dependencies import get_db as get_db_dependency
from .routers import firebase, questions, scenarios, users, websockets
from .llm.client import GeminiClient


# Configure logging right at the start
configure_logging()

# --- Sentry Initialization ---
# Get settings to access the DSN
# Note: This is a simple way to get settings here.
# In very complex apps, you might pass settings around more explicitly.
temp_settings = Settings()
if temp_settings.SENTRY_DSN:
    sentry_sdk.init(
        dsn=temp_settings.SENTRY_DSN.get_secret_value(),
        # Set traces_sample_rate to 1.0 to capture 100%
        # of transactions for performance monitoring.
        # Adjust in production.
        traces_sample_rate=1.0,
        # Set profiles_sample_rate to 1.0 to profile 100%
        # of sampled transactions.
        # Adjust in production.
        profiles_sample_rate=1.0,
        # Set the environment
        environment=temp_settings.SENTRY_ENVIRONMENT,
        shutdown_timeout=2,
        debug=False,
    )
# Get a structlog logger instead of a standard one
logger = structlog.get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Handles application startup and shutdown events.
    """
    logger.info("Application starting up...")
    yield
    logger.info("Application shutting down.")


def create_app(settings: Settings, testing: bool = False) -> FastAPI:
    """
    Application factory to create and configure the FastAPI app.
    """
    # Example of adding context to a log message
    logger.info("--- FACTORY: create_app() called ---", testing=testing)

    # The factory is now responsible for creating the engine and SessionLocal
    # Using the computed DATABASE_URL from the settings object
    engine = create_engine(str(settings.DATABASE_URL))
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

    # The factory is also responsible for creating all tables
    # Base.metadata.create_all(bind=engine) MOVING TO ALEMCIB

    # Initialize the LLM client
    llm_client = GeminiClient(api_key=settings.GEMINI_API_KEY.get_secret_value())

    app = FastAPI(
        lifespan=None if testing else lifespan, title="SignConnect API", version="0.1.0"
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
        "http://localhost",
        "http://localhost:5173",
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
