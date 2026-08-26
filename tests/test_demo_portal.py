import pytest

import demo_portal


@pytest.fixture
def client():
    demo_portal.app.config["TESTING"] = True
    with demo_portal.app.test_client() as client:
        yield client


def test_login_get_returns_form(client):
    response = client.get("/login")
    assert response.status_code == 200
    assert b'id="username"' in response.data
    assert b'id="password"' in response.data


def test_login_post_correct_credentials_redirects_to_dashboard(client):
    response = client.post("/login", data={"username": "demo", "password": "demo123"})
    assert response.status_code == 302
    assert response.location == "/dashboard"


def test_login_post_correct_credentials_sets_session(client):
    client.post("/login", data={"username": "demo", "password": "demo123"})
    with client.session_transaction() as session:
        assert session["logged_in"] is True


def test_login_post_wrong_credentials_returns_401(client):
    response = client.post("/login", data={"username": "wrong", "password": "wrong"})
    assert response.status_code == 401


def test_login_post_wrong_credentials_does_not_set_session(client):
    client.post("/login", data={"username": "wrong", "password": "wrong"})
    with client.session_transaction() as session:
        assert "logged_in" not in session


def test_dashboard_without_session_redirects_to_login(client):
    response = client.get("/dashboard")
    assert response.status_code == 302
    assert response.location == "/login"


def test_dashboard_with_session_shows_download_link(client):
    with client.session_transaction() as session:
        session["logged_in"] = True
    response = client.get("/dashboard")
    assert response.status_code == 200
    assert b'href="/download"' in response.data


def test_download_without_session_redirects_to_login(client):
    response = client.get("/download")
    assert response.status_code == 302
    assert response.location == "/login"


def test_download_with_session_returns_file(client):
    with client.session_transaction() as session:
        session["logged_in"] = True
    response = client.get("/download")
    assert response.status_code == 200
    assert b"invoice_id" in response.data
