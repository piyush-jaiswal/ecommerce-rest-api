import pytest

from app.models import User
from tests import utils


class TestAuth:
    TEST_EMAIL = "testuser@example.com"
    TEST_PASSWORD = "testpassword"

    @pytest.fixture(autouse=True)
    def setup(self, client):
        self.client = client
        with client.application.app_context():
            assert User.query.count() == 0

    def _verify_user_in_db(self, email, should_exist=True):
        with self.client.application.app_context():
            user = User.get(email=email)
            if should_exist:
                assert user is not None
                assert user.email == email
                return user
            else:
                assert user is None

    def _count_users(self):
        with self.client.application.app_context():
            return User.query.count()

    def _test_invalid_request_data(self, endpoint, expected_status=400):
        response = self.client.post(endpoint, json={})
        assert response.status_code == expected_status

        response = self.client.post(endpoint, json={"email": self.TEST_EMAIL})
        assert response.status_code == expected_status

        response = self.client.post(endpoint, json={"password": self.TEST_PASSWORD})
        assert response.status_code == expected_status

        response = self.client.post(endpoint, data="not json data")
        assert response.status_code == 415

    def test_register_success(self, register_user):
        response = register_user(self.TEST_EMAIL, self.TEST_PASSWORD)

        assert response.status_code == 201
        assert b"Registered!" in response.data
        assert self._count_users() == 1
        user = self._verify_user_in_db(self.TEST_EMAIL)
        assert user.password_hash != self.TEST_PASSWORD

    def test_register_duplicate_email(self, register_user):
        register_user(self.TEST_EMAIL, self.TEST_PASSWORD)
        response = register_user(self.TEST_EMAIL, self.TEST_PASSWORD)

        assert response.status_code == 409
        assert b"Email already exists" in response.data
        assert self._count_users() == 1
        self._verify_user_in_db(self.TEST_EMAIL)

    def test_register_invalid_email_format(self, register_user):
        invalid_email = "not-an-email"
        response = register_user(invalid_email, self.TEST_PASSWORD)

        assert response.status_code == 400
        data = response.get_json()
        assert data["code"] == "invalid_email_format"
        assert "error" in data
        self._verify_user_in_db(invalid_email, should_exist=False)

    def test_register_invalid_data(self):
        self._test_invalid_request_data("/auth/register")
        assert self._count_users() == 0

    def test_login_success(self, register_user, login_user):
        register_user(self.TEST_EMAIL, self.TEST_PASSWORD)
        response = login_user(self.TEST_EMAIL, self.TEST_PASSWORD)

        assert response.status_code == 200
        data = response.get_json()
        assert "access_token" in data
        assert "refresh_token" in data
        assert len(data["access_token"]) > 0
        assert len(data["refresh_token"]) > 0

    def test_login_invalid_password(self, register_user, login_user):
        register_user(self.TEST_EMAIL, self.TEST_PASSWORD)
        response = login_user(self.TEST_EMAIL, "wrongpassword")

        assert response.status_code == 401
        assert b"Invalid username or password" in response.data

    def test_login_invalid_data(self):
        self._test_invalid_request_data("/auth/login")

    def test_refresh_token(self, register_user, login_user):
        register_user(self.TEST_EMAIL, self.TEST_PASSWORD)
        login_resp = login_user(self.TEST_EMAIL, self.TEST_PASSWORD)
        tokens = login_resp.get_json()
        refresh_token = tokens["refresh_token"]
        original_access_token = tokens["access_token"]

        headers = utils.get_auth_header(refresh_token)
        refresh_resp = self.client.post("/auth/refresh", headers=headers)
        assert refresh_resp.status_code == 200
        data = refresh_resp.get_json()
        assert "access_token" in data
        assert data["access_token"] != original_access_token
        assert "refresh_token" not in data

    def test_refresh_token_invalid(self, register_user, login_user):
        # Access token test
        register_user(self.TEST_EMAIL, self.TEST_PASSWORD)
        login_resp = login_user(self.TEST_EMAIL, self.TEST_PASSWORD)
        tokens = login_resp.get_json()
        access_token = tokens["access_token"]
        headers = utils.get_auth_header(access_token)
        response = self.client.post("/auth/refresh", headers=headers)

        utils.verify_token_error_response(response, "invalid_token")

        # Malformed token test
        malformed_headers = utils.get_invalid_token_headers()
        response = self.client.post("/auth/refresh", headers=malformed_headers)
        utils.verify_token_error_response(response, "invalid_token")

    def test_refresh_token_missing_auth(self):
        response = self.client.post("/auth/refresh")
        utils.verify_token_error_response(response, "authorization_required")

    def test_refresh_token_expired(self):
        expired_headers = utils.get_expired_token_headers(
            self.client.application.app_context()
        )
        response = self.client.post("/auth/refresh", headers=expired_headers)
        utils.verify_token_error_response(response, "token_expired")
