# tests/conftest.py

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

# Use the Application Factory
from src.signconnect.app_factory import create_app

# Import DB and dependency components
from src.signconnect.db.database import get_db, Base
from src.signconnect.db.test_database import engine, TestingSessionLocal
from src.signconnect.dependencies import get_current_user


@pytest.fixture(scope="function")
def db_session() -> Session:
    """Creates a clean database session for each test."""
    Base.metadata.create_all(bind=engine)
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()
        Base.metadata.drop_all(bind=engine)


@pytest.fixture(scope="function")
def client(db_session: Session) -> TestClient:
    """
    Creates a fresh app instance and a TestClient for each test function.
    This is the most robust way to ensure test isolation.
    """
    # Create a new app instance for each test
    app = create_app()

    # Override the get_db dependency for THIS app instance
    app.dependency_overrides[get_db] = lambda: db_session

    with TestClient(app) as test_client:
        yield test_client

    # The dependency override is cleared automatically when the app instance is discarded.


@pytest.fixture
def authenticated_client(client: TestClient) -> TestClient:
    """Provides a mocked, authenticated client."""
    FAKE_FIREBASE_USER = {
        "email": "newuser@example.com",
        "name": "New User",
        "uid": "fake-firebase-uid-123",
    }

    def override_get_current_user():
        return FAKE_FIREBASE_USER

    # Apply the override to the app instance within the client
    client.app.dependency_overrides[get_current_user] = override_get_current_user
    yield client