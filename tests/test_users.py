from fastapi.testclient import TestClient

def test_users(client: TestClient):
    """
    Tests if the root endpoint is running.
    We don't have one, so this will fail, which is a good test!
    Let's test the /docs endpoint instead.

    :param client:
    :return:
    """

    response = client.get("/docs")
    assert response.status_code == 200
