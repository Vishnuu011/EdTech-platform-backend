from fastapi.testclient import TestClient

from main import app

def test_liveness():
    client=TestClient(app)
    response=client.get("/health/live")

    assert response.status_code == 200

    assert response.json() == {
        "status": "OK"
    }


def test_correlation_id_is_returned():
    client=TestClient(app)

    response=client.get("/health/live")
    assert response.status_code == 200

    assert "X-Correlation-ID" in response.headers    