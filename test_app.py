from app import app


def test_homepage():
    client = app.test_client()
    response = client.get("/")
    assert response.status_code == 200


def test_register_page():
    client = app.test_client()
    response = client.get("/register")
    assert response.status_code == 200


def test_login_page():
    client = app.test_client()
    response = client.get("/login")
    assert response.status_code == 200