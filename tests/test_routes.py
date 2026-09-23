def test_health(client):
    response = client.get("/api/health")
    assert response.status_code == 200
    assert response.json["status"] == "ok"


def test_upload_error(client):
    client.post("/signup", data={"name": "Jane Doe", "email": "jane@example.com", "password": "strongpass", "confirm_password": "strongpass"})
    client.post("/login", data={"email": "jane@example.com", "password": "strongpass"})
    response = client.post("/api/analyze-data")
    assert response.status_code == 400
    assert response.json["error"]["code"] == "FILE_INVALID"
