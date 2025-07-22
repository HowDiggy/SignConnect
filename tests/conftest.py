import pytest
from pathlib import Path
from pytest_docker import docker_ip, docker_services
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, text
from sqlalchemy.orm import Session, sessionmaker

# We explicitly import all models here to ensure they are registered with the Base.
from src.signconnect.db import models
from src.signconnect.app_factory import create_app
from src.signconnect.db.database import Base, get_db
from src.signconnect.db.test_database import engine, TestingSessionLocal
from src.signconnect.dependencies import get_current_user


# --- This fixture correctly points to your docker-compose.yml ---
@pytest.fixture(scope="session")
def docker_compose_file(pytestconfig):
    """Override the default docker-compose.yml file path."""
    # Point to our new test-specific file
    return Path(pytestconfig.rootdir) / "docker-compose.test.yml"


# --- This is the corrected version of the postgres_service fixture ---
@pytest.fixture(scope="session")
def postgres_service(docker_ip, docker_services):
    """Ensure that the postgres service is running and responsive."""
    port = docker_services.port_for("db", 5432)
    host = docker_ip
    docker_services.wait_until_responsive(
        timeout=30.0, pause=0.5, check=lambda: is_postgres_responsive(host, port)
    )
    # THE FIX: Use the correct credentials
    return f"postgresql://myuser:mypassword@{host}:{port}/signconnect_db"


def is_postgres_responsive(host, port):
    """Helper function to check if the PostgreSQL server is ready."""
    try:
        # THE FIX: Use the correct credentials
        engine = create_engine(f"postgresql://myuser:mypassword@{host}:{port}/signconnect_db")
        with engine.connect() as connection:
            connection.execute(text("SELECT 1"))
            return True
    except Exception:
        return False


# --- This fixture remains the same but will now work correctly ---
@pytest.fixture(scope="session")
def integration_db_session(postgres_service):
    """
    Provides a clean, session-scoped database session for integration tests.
    """
    engine = create_engine(postgres_service)
    with engine.connect() as connection:
        connection.execute(text("CREATE EXTENSION IF NOT EXISTS vector;"))
        connection.commit()

    Base.metadata.create_all(bind=engine)
    Session = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    session = Session()

    yield session

    session.close()
    Base.metadata.drop_all(bind=engine)

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


@pytest.fixture(scope="function")
def integration_client(
        integration_db_session: Session,
        monkeypatch  # We still need monkeypatch for the settings
) -> TestClient:
    """
    Provides a TestClient that is fully configured for integration tests:
    - Uses the real PostgreSQL database session.
    - Has a mocked, authenticated user.
    """
    app = create_app(testing=True)

    # Override the DB dependency to use the PostgreSQL session
    app.dependency_overrides[get_db] = lambda: integration_db_session

    # Mock the user authentication
    FAKE_FIREBASE_USER = {"email": "newuser@example.com", "name": "New User", "uid": "fake-firebase-uid-123"}

    def override_get_current_user():
        return FAKE_FIREBASE_USER

    app.dependency_overrides[get_current_user] = override_get_current_user

    with TestClient(app) as test_client:
        yield test_client

    app.dependency_overrides.clear()