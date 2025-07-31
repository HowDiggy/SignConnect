# tests/conftest.py

import pytest
from pathlib import Path
from typing import Generator
from unittest.mock import MagicMock

from fastapi.testclient import TestClient
from pytest_docker import docker_ip, docker_services
from sqlalchemy import create_engine, text
from sqlalchemy.orm import Session, sessionmaker

# --- Import from our app ---
from src.signconnect.app_factory import create_app
from src.signconnect.core.config import Settings
from src.signconnect.db.database import Base
from src.signconnect.dependencies import get_db, get_current_user, get_current_user_ws
from src.signconnect.llm.client import GeminiClient

# Define the path to the root of the project.
PROJECT_ROOT = Path(__file__).parent.parent


@pytest.fixture(scope="session")
def docker_compose_file(pytestconfig) -> Path:
    """
    Returns the path to the docker-compose file used for testing.
    This now points to our isolated test environment definition.
    """
    return PROJECT_ROOT / "docker-compose.test.yml"


def _is_db_responsive(engine) -> bool:
    """
    Checks if the database is responsive by trying to establish a connection
    and execute a simple query.
    """
    try:
        with engine.connect() as connection:
            connection.execute(text("SELECT 1"))
        return True
    except Exception:
        return False


@pytest.fixture(scope="function")
def test_settings(monkeypatch, docker_ip, docker_services) -> Settings:
    """
    Creates a Settings object for the test environment by setting
    environment variables and explicitly disabling .env file loading.
    """
    port = docker_services.port_for("test-db", 5432)

    monkeypatch.setenv("POSTGRES_USER", "myuser")
    monkeypatch.setenv("POSTGRES_PASSWORD", "mypassword")
    monkeypatch.setenv("POSTGRES_DB", "test_db")
    monkeypatch.setenv("POSTGRES_SERVER", docker_ip)
    monkeypatch.setenv("POSTGRES_PORT", str(port))
    monkeypatch.setenv("CLIENT_ORIGIN_URL", "http://test-client.com")
    monkeypatch.setenv("FIREBASE_CLIENT_API_KEY", "fake-key")
    monkeypatch.setenv("FIREBASE_CLIENT_AUTH_DOMAIN", "fake.firebaseapp.com")
    monkeypatch.setenv("FIREBASE_CLIENT_PROJECT_ID", "fake-project")
    monkeypatch.setenv("FIREBASE_CLIENT_STORAGE_BUCKET", "fake.appspot.com")
    monkeypatch.setenv("FIREBASE_CLIENT_MESSAGING_SENDER_ID", "fake-sender-id")
    monkeypatch.setenv("FIREBASE_CLIENT_APP_ID", "fake-app-id")
    monkeypatch.setenv("FIREBASE_CLIENT_MEASUREMENT_ID", "fake-measurement-id")
    monkeypatch.setenv("GEMINI_API_KEY", "fake-gemini-api-key")
    
    from src.signconnect.core.config import get_settings
    get_settings.cache_clear()
    
    # Explicitly disable .env file loading to guarantee test isolation
    return Settings(_env_file=None)


@pytest.fixture(scope="function")
def test_engine(test_settings: Settings, docker_ip: str, docker_services):
    """
    Handles the entire lifecycle of the test database for a single test function.
    This fixture ensures all connections are closed before dropping the database.
    """
    # --- 1. Define connection URLs ---
    port = docker_services.port_for("test-db", 5432)
    default_db_url = (
        f"postgresql://{test_settings.POSTGRES_USER}:"
        f"{test_settings.POSTGRES_PASSWORD.get_secret_value()}@"
        f"{docker_ip}:{port}/postgres"
    )
    test_db_url = (
        f"postgresql://{test_settings.POSTGRES_USER}:"
        f"{test_settings.POSTGRES_PASSWORD.get_secret_value()}@"
        f"{docker_ip}:{port}/{test_settings.POSTGRES_DB}"
    )

    # --- 2. Wait for the PostgreSQL service to be responsive ---
    default_engine = create_engine(default_db_url)
    try:
        docker_services.wait_until_responsive(
            timeout=30.0, pause=0.5, check=lambda: _is_db_responsive(default_engine)
        )
    finally:
        default_engine.dispose()

    # --- 3. Create the test database ---
    with create_engine(default_db_url, isolation_level="AUTOCOMMIT").connect() as conn:
        conn.execute(text(f'DROP DATABASE IF EXISTS "{test_settings.POSTGRES_DB}"'))
        conn.execute(text(f'CREATE DATABASE "{test_settings.POSTGRES_DB}"'))

    # --- 4. Connect to the new DB to enable the vector extension ---
    test_engine = create_engine(test_db_url)
    with test_engine.connect() as conn:
        conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector"))
        conn.commit()

    # --- 5. Create tables and yield the engine to the tests ---
    try:
        Base.metadata.create_all(bind=test_engine)
        yield test_engine
    finally:
        # --- TEARDOWN ---
        
        # Step 1: Explicitly dispose of the test engine's connection pool.
        # This is crucial to close connections held by the test session.
        print("--- FIXTURE TEARDOWN: Disposing test engine connection pool... ---")
        test_engine.dispose()

        # Step 2: Connect to the default DB with a new engine to drop the test DB.
        with create_engine(default_db_url, isolation_level="AUTOCOMMIT").connect() as conn:
            # Step 3 (Safety): Forcibly terminate any other lingering connections.
            print("--- FIXTURE TEARDOWN: Terminating any stray connections... ---")
            conn.execute(text(f"""
                SELECT pg_terminate_backend(pg_stat_activity.pid)
                FROM pg_stat_activity
                WHERE pg_stat_activity.datname = '{test_settings.POSTGRES_DB}'
                  AND pid <> pg_backend_pid();
            """))
            
            # Step 4: Drop the database. This should now succeed.
            print(f"--- FIXTURE TEARDOWN: Dropping database {test_settings.POSTGRES_DB} ---")
            conn.execute(text(f'DROP DATABASE "{test_settings.POSTGRES_DB}"'))



@pytest.fixture(scope="function")
def db_session_factory(test_engine):
    """
    Provides a sessionmaker for the test function.
    """
    return sessionmaker(autocommit=False, autoflush=False, bind=test_engine)


@pytest.fixture(scope="function")
def db_session(db_session_factory) -> Generator[Session, None, None]:
    """
    Provides a clean, transaction-isolated database session for each test function.
    """
    session = db_session_factory()
    yield session
    session.close()


@pytest.fixture(scope="function")
def client(
    db_session: Session, test_settings: Settings, monkeypatch
) -> Generator[TestClient, None, None]:
    """
    Creates a TestClient and overrides dependencies for DB and LLM services.
    """
    mock_llm_client = MagicMock(spec=GeminiClient)
    monkeypatch.setattr("src.signconnect.app_factory.GeminiClient", lambda api_key: mock_llm_client)

    def override_get_db() -> Generator[Session, None, None]:
        yield db_session

    app = create_app(settings=test_settings, testing=True)
    app.dependency_overrides[get_db] = override_get_db

    with TestClient(app) as test_client:
        yield test_client
    
    app.dependency_overrides.clear()


@pytest.fixture(scope="function")
def authenticated_client(client: TestClient) -> Generator[TestClient, None, None]:
    """
    Provides a TestClient with mocked `get_current_user` and `get_current_user_ws`
    dependencies, ensuring both REST and WebSocket endpoints are authenticated.
    """
    FAKE_FIREBASE_USER = {
        "email": "newuser@example.com",
        "name": "Test User",
        "uid": "fake-firebase-uid-123",
    }

    async def override_get_current_user():
        return FAKE_FIREBASE_USER

    client.user = FAKE_FIREBASE_USER
    app = client.app

    # Store original overrides to restore them cleanly
    original_http_auth = app.dependency_overrides.get(get_current_user)
    original_ws_auth = app.dependency_overrides.get(get_current_user_ws)

    # FIX: Override BOTH authentication dependencies
    app.dependency_overrides[get_current_user] = override_get_current_user
    app.dependency_overrides[get_current_user_ws] = override_get_current_user

    yield client

    # CLEANUP: Restore both overrides to their original state
    if original_http_auth:
        app.dependency_overrides[get_current_user] = original_http_auth
    else:
        app.dependency_overrides.pop(get_current_user, None)
    
    if original_ws_auth:
        app.dependency_overrides[get_current_user_ws] = original_ws_auth
    else:
        app.dependency_overrides.pop(get_current_user_ws, None)