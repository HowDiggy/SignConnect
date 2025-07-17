# src/signconnect/app_factory.py

from fastapi import FastAPI
from contextlib import asynccontextmanager

from .db.database import Base, engine


def create_app() -> FastAPI:
    """
    Application factory to create and configure the FastAPI app.
    """

    @asynccontextmanager
    async def lifespan(app: FastAPI):
        """Handles application startup and shutdown events."""
        print("--- Lifespan: Creating database tables... ---")
        Base.metadata.create_all(bind=engine)
        yield
        print("--- Lifespan: Application shutdown. ---")

    app = FastAPI(lifespan=lifespan)

    # --- Import and include routers inside the factory ---
    from .routers import users, scenarios, questions
    app.include_router(users.router)
    app.include_router(scenarios.router)
    app.include_router(questions.router)

    # You can add middleware here if needed
    # from fastapi.middleware.cors import CORSMiddleware
    # app.add_middleware(...)

    return app