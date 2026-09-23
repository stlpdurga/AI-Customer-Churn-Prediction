import os
import sqlite3


def signup(client, email="jane@example.com", password="strongpass"):
    return client.post("/signup", data={"name": "Jane Doe", "email": email, "password": password, "confirm_password": password})


def test_signup_success_and_hashed_password(client):
    response = signup(client)
    assert response.status_code == 302
    assert response.headers["Location"].endswith("/login")
    conn = sqlite3.connect(os.environ["DATABASE_PATH"])
    password_hash = conn.execute("SELECT password_hash FROM users WHERE email = ?", ("jane@example.com",)).fetchone()[0]
    conn.close()
    assert password_hash != "strongpass"
    assert password_hash.startswith("scrypt:") or password_hash.startswith("pbkdf2:")


def test_duplicate_email(client):
    signup(client)
    response = signup(client)
    assert response.status_code == 400
    assert b"An account with this email already exists." in response.data


def test_signup_validation(client):
    response = client.post("/signup", data={"name": "", "email": "bad", "password": "short", "confirm_password": "different"})
    assert response.status_code == 400
    assert b"Enter a valid email address." in response.data
    assert b"Passwords do not match." in response.data
    assert b"at least 8 characters" in response.data


def test_login_session_and_dashboard(client):
    signup(client)
    response = client.post("/login", data={"email": "jane@example.com", "password": "strongpass"})
    assert response.status_code == 302
    assert response.headers["Location"].endswith("/dashboard")
    with client.session_transaction() as session:
        assert session["user_name"] == "Jane Doe"
    assert b"Welcome, Jane Doe" in client.get("/dashboard").data


def test_invalid_login_is_generic(client):
    response = client.post("/login", data={"email": "missing@example.com", "password": "wrongpass"})
    assert response.status_code == 401
    assert b"Invalid email or password." in response.data


def test_logout_clears_session(client):
    signup(client)
    client.post("/login", data={"email": "jane@example.com", "password": "strongpass"})
    response = client.get("/logout")
    assert response.status_code == 302
    assert response.headers["Location"].endswith("/login")
    with client.session_transaction() as session:
        assert "user_id" not in session
    assert b"You have been logged out successfully." in client.get("/login").data


def test_protected_routes_redirect_or_return_unauthorized(client):
    assert client.get("/").status_code == 302
    assert client.get("/dashboard").headers["Location"].endswith("/login")
    assert client.post("/api/analyze-data").status_code == 401
