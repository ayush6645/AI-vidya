from fastapi.testclient import TestClient

def test_login_failure(client: TestClient):
    response = client.post("/api/v1/auth/login", json={
        "loginType": "loginUsername",
        "login_value": "nonexistent_user",
        "authType": "authPassword",
        "auth_value": "password"
    })
    # Expect 401 or 400 depending on implementation
    assert response.status_code in [400, 401, 404]

def test_unauthorized_dashboard(client: TestClient):
    response = client.get("/api/v1/users/dashboard-data")
    assert response.status_code == 401

def test_openapi(client: TestClient):
    response = client.get("/docs")
    assert response.status_code == 200
