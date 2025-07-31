import os

import pytest

# TODO: Fix hack. Changes the env var before initializing the db for testing
os.environ["SQLALCHEMY_DATABASE_URI"] = "sqlite:///:memory:"
os.environ["JWT_SECRET_KEY"] = os.urandom(24).hex()

from app import app, db


@pytest.fixture
def client():
    app.config["TESTING"] = True
    with app.test_client() as client:
        with app.app_context():
            db.create_all()
        yield client
        with app.app_context():
            db.drop_all()


@pytest.fixture
def register_user(client):
    def _register(email, password):
        return client.post(
            "/auth/register", json={"email": email, "password": password}
        )

    return _register


@pytest.fixture
def login_user(client):
    def _login(email, password):
        return client.post("/auth/login", json={"email": email, "password": password})

    return _login
