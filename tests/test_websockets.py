# tests/test_websockets.py

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

def test_websocket_connect_and_disconnect(
    authenticated_client: TestClient,
    db_session: Session
):
    """
    GIVEN an authenticated client,
    WHEN they attempt to connect to the WebSocket endpoint,
    THEN the connection should be accepted and then closed cleanly.
    """
    # ARRANGE: No special setup is needed beyond having an authenticated client.

    # ACT & ASSERT: We use a 'with' block to manage the connection.
    # If the block opens and closes without any errors, the test passes.
    try:
        with authenticated_client.websocket_connect("/ws") as websocket:
            # We don't need to send or receive anything for this test.
            # We are just proving that the connection itself works.
            print("\n--- WebSocket connection successful ---")
    except Exception as e:
        # If any exception occurs during connection, fail the test.
        assert False, f"WebSocket connection failed with an exception: {e}"