# tests/conftest.py

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

# Import the app and database components
from src.signconnect.main import app
from src.signconnect.db.database import get_db, Base
from src.signconnect.db.test_database import engine, TestingSessionLocal
from src.signconnect.dependencies import get_current_user

# This is the only place we need to import models now, for the fixture
from src.signconnect.db import models


@pytest.fixture(scope="function")
def db_session() -> Session:
    """Creates a clean database session for each test."""
    # Now that the app (and its models) are loaded cleanly, we can create the tables.
    Base.metadata.create_all(bind=engine)
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()
        Base.metadata.drop_all(bind=engine)


@pytest.fixture(scope="function")
def client(db_session: Session) -> TestClient:
    """Provides a TestClient that uses the clean test database session."""
    def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db
    yield TestClient(app)
    app.dependency_overrides.clear()


@pytest.fixture
def authenticated_client(client: TestClient) -> TestClient:
    """Provides a mocked, authenticated client."""
    FAKE_FIREBASE_USER = { "email": "newuser@example.com", "name": "New User", "uid": "fake-firebase-uid-123" }

    def override_get_current_user():
        return FAKE_FIREBASE_USER

    app.dependency_overrides[get_current_user] = override_get_current_user
    yield client
    app.dependency_overrides.clear()