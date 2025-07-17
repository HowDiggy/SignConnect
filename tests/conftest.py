# tests/conftest.py

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import StaticPool

# Import from your application
from src.signconnect.app_factory import create_app
from src.signconnect.db.database import Base, get_db
from src.signconnect.dependencies import get_current_user

# 1. A completely self-contained test database setup inside conftest.py.
# This prevents any potential conflicts with your main database.py or test_database.py.
SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,  # This is crucial for in-memory SQLite with FastAPI.
)

TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


# 2. The database fixture: it creates tables, yields a session, and then drops the tables.
# This ensures every single test runs on a fresh, clean database.
@pytest.fixture(scope="function")
def db_session() -> Session:
    """
    Creates a fresh, isolated database session for each test.
    This fixture has the sole responsibility for the database lifecycle.
    """
    # All your SQLAlchemy models must be imported somewhere for Base.metadata
    # to know about them. We assume they are loaded when create_app() is called.
    Base.metadata.create_all(bind=engine)
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()
        Base.metadata.drop_all(bind=engine)


# 3. The client fixture: it creates the app, overrides the database dependency,
# and then yields the TestClient. This is the heart of the solution.
@pytest.fixture(scope="function")
def client(db_session: Session) -> TestClient:
    """
    Creates a FastAPI TestClient with its database dependency
    overridden to use the isolated test session.
    """
    app = create_app()

    # We override the get_db dependency *before* the TestClient is created.
    # This ensures that all parts of the app, including any startup
    # events, will use the test database session.
    app.dependency_overrides[get_db] = lambda: db_session

    with TestClient(app) as test_client:
        yield test_client

    # Clean up the override after the test to ensure no state leaks.
    app.dependency_overrides.clear()


@pytest.fixture
def authenticated_client(client: TestClient) -> TestClient:
    """
    Provides a client that is pre-authenticated with a mock user.
    """
    FAKE_FIREBASE_USER = {"email": "newuser@example.com", "name": "New User", "uid": "fake-firebase-uid-123"}

    def override_get_current_user():
        return FAKE_FIREBASE_USER

    app = client.app
    app.dependency_overrides[get_current_user] = override_get_current_user
    yield client
    # The get_current_user override is cleared automatically by the client fixture.