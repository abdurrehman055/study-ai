from tests.conftest import register_user, get_auth_headers


class TestRegister:
    def test_register_success(self, client):
        res = register_user(client)
        assert res.status_code == 201
        body = res.json()
        assert "access_token" in body
        assert body["token_type"] == "bearer"
        assert body["user"]["email"] == "test@example.com"
        assert body["user"]["name"] == "Test User"
        assert "password" not in body["user"]

    def test_register_duplicate_email(self, client):
        register_user(client)
        res = register_user(client)
        assert res.status_code == 409
        assert "already exists" in res.json()["detail"].lower()

    def test_register_invalid_email(self, client):
        res = client.post("/auth/register", json={
            "name": "Test",
            "email": "not-an-email",
            "password": "password123",
        })
        assert res.status_code == 422

    def test_register_password_too_short(self, client):
        res = client.post("/auth/register", json={
            "name": "Test",
            "email": "test@example.com",
            "password": "short",
        })
        assert res.status_code == 422

    def test_register_returns_preferred_study_time(self, client):
        res = client.post("/auth/register", json={
            "name": "Night Owl",
            "email": "night@example.com",
            "password": "password123",
            "preferred_study_time": "Night",
        })
        assert res.status_code == 201
        assert res.json()["user"]["preferred_study_time"] == "Night"


class TestLogin:
    def test_login_success(self, client):
        register_user(client)
        res = client.post("/auth/login", json={
            "email": "test@example.com",
            "password": "password123",
        })
        assert res.status_code == 200
        assert "access_token" in res.json()

    def test_login_wrong_password(self, client):
        register_user(client)
        res = client.post("/auth/login", json={
            "email": "test@example.com",
            "password": "wrongpassword",
        })
        assert res.status_code == 401

    def test_login_unknown_email(self, client):
        res = client.post("/auth/login", json={
            "email": "nobody@example.com",
            "password": "password123",
        })
        assert res.status_code == 401

    def test_protected_endpoint_without_token(self, client):
        res = client.get("/plans/")
        assert res.status_code == 401

    def test_protected_endpoint_with_invalid_token(self, client):
        res = client.get("/plans/", headers={"Authorization": "Bearer fake.token.here"})
        assert res.status_code == 401
