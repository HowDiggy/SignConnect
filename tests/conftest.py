import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

# We explicitly import all models here to ensure they are registered with the Base.
from src.signconnect.db import models
from src.signconnect.app_factory import create_app
from src.signconnect.db.database import Base, get_db
from src.signconnect.db.test_database import engine, TestingSessionLocal
from src.signconnect.dependencies import get_current_user


@pytest.fixture(scope="function")
def db_session() -> Session:
    """
    Creates a fresh, isolated database session for each test.
    """
    # ------------------- THE CRITICAL DEBUGGING STEP -------------------
    # We will now inspect SQLAlchemy's metadata right before we create the tables.
    # This will tell us if our models (User, Scenario, etc.) have been loaded.
    print(f"\n--- FIXTURE: Inspecting tables before creation: {list(Base.metadata.tables.keys())} ---\n")
    # ---------------------------------------------------------------------

    Base.metadata.create_all(bind=engine)

    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()
        Base.metadata.drop_all(bind=engine)


@pytest.fixture(scope="function")
def client(db_session: Session) -> TestClient:
    app = create_app(testing=True)
    app.dependency_overrides[get_db] = lambda: db_session
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


@pytest.fixture
def authenticated_client(client: TestClient) -> TestClient:
    FAKE_FIREBASE_USER = {"email": "newuser@example.com", "name": "New User", "uid": "fake-firebase-uid-123"}

    def override_get_current_user():
        return FAKE_FIREBASE_USER

    app = client.app
    app.dependency_overrides[get_current_user] = override_get_current_user
    yield client