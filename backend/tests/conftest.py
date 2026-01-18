import pytest
from fastapi.testclient import TestClient
from backend.app.main import app

@pytest.fixture
def client():
    # Use TestClient which handles async endpoints synchronously for tests
    return TestClient(app)
