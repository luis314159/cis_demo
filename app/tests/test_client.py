from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_get_clients():
    response = client.get("/clients/")
    assert response.status_code == 200
