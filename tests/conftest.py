import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

# We explicitly import all models here to ensure they are registered with the Base.
from src.signconnect.db import models
from src.signconnect.app_factory import create_app
from src.signconnect.db.database import Base, get_db
from src.signconnect.db.test_database import engine, TestingSessionLocal
from src.signconnect.dependencies import get_current_user

@pytest.fixture(scope="function", autouse=True)
def set_test_environment(monkeypatch):
    """
    Sets the necessary environment variables before any tests run.
    This fixture ensures tests are independent of any .env file.
    """
    monkeypatch.setenv("DATABASE_URL", "sqlite:///./test_db_from_env.db")
    monkeypatch.setenv("GOOGLE_APPLICATION_CREDENTIALS", "fake-credentials.json")
    monkeypatch.setenv("GEMINI_API_KEY", "fake-api-key")
    # Add any other required environment variables here
    # monkeypatch.setenv("FIREBASE_CLIENT_API_KEY", "fake-api-key")


@pytest.fixture(scope="function")
def db_session() -> Session:
    """Creates a fresh, isolated database session for each test."""
    Base.metadata.create_all(bind=engine)
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()
        Base.metadata.drop_all(bind=engine)


@pytest.fixture(scope="function")
def client(db_session: Session) -> TestClient:
    """Creates a TestClient with dependencies overridden for testing."""
    app = create_app(testing=True)
    app.dependency_overrides[get_db] = lambda: db_session
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


@pytest.fixture
def authenticated_client(client: TestClient) -> TestClient:
    """Provides a client that is pre-authenticated with a mock user."""
    FAKE_FIREBASE_USER = {"email": "newuser@example.com", "name": "New User", "uid": "fake-firebase-uid-123"}
    def override_get_current_user():
        return FAKE_FIREBASE_USER
    app = client.app
    app.dependency_overrides[get_current_user] = override_get_current_user
    yield client