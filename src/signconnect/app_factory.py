# src/signconnect/app_factory.py

from fastapi import FastAPI
from contextlib import asynccontextmanager
from fastapi.middleware.cors import CORSMiddleware

# --- Core application and DB modules ---
from .db.database import Base, engine

# This is the production lifespan function.
@asynccontextmanager
async def lifespan(app: FastAPI):
    """Handles application startup and shutdown events."""
    from .db import database, models

    print("Application starting: Enabling pgvector extension...")
    database.enable_pgvector_extension()

    print("Creating database tables...")
    models.Base.metadata.create_all(bind=engine)
    yield
    print("Application shutdown.")


def create_app(testing: bool = False) -> FastAPI:
    """
    Application factory to create and configure the FastAPI app.
    This is the single source of truth for app creation.

    Args:
        testing (bool): If True, the app is created without the production lifespan
                        event handler, making it suitable for testing.
    """

    # ADD THIS PRINT STATEMENT
    print(f"\n--- FACTORY: create_app() called with testing={testing} ---\n")


    # Conditionally set the lifespan based on the 'testing' flag.
    lifespan_to_use = None if testing else lifespan

    app = FastAPI(
        lifespan=lifespan_to_use, # Use the conditional lifespan
        title="SignConnect API",
        description="API for the SignConnect assistive communication application.",
        version="0.1.0"
    )

    # --- Import and include all your routers ---
    from .routers import users, scenarios, questions, websockets, firebase
    print("Including routers...")
    app.include_router(scenarios.router)
    app.include_router(users.router)
    app.include_router(questions.router)
    app.include_router(websockets.router)
    app.include_router(firebase.router)

    # --- Add CORS Middleware ---
    # (Keep your existing CORS middleware setup here)
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

    return app