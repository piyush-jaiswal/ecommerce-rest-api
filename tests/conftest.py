import os

import pytest

# TODO: Fix hack. Changes the env var before initializing the db for testing
os.environ["SQLALCHEMY_DATABASE_URI"] = "sqlite:///:memory:"
os.environ["JWT_SECRET_KEY"] = os.urandom(24).hex()

from app import app, db
from tests import utils


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


@pytest.fixture
def create_authenticated_headers(register_user, login_user):
    def _get_headers(email="testuser@example.com", password="testpassword"):
        nonlocal headers
        if not headers:
            register_user(email, password)
            resp = login_user(email, password)
            tokens = resp.get_json()
            headers = utils.get_auth_header(tokens["access_token"])

        return headers

    headers = None
    return _get_headers


@pytest.fixture
def create_category(client, create_authenticated_headers):
    def _create(name, subcategories=None, headers=None):
        if headers is None:
            headers = create_authenticated_headers()
        payload = {"name": name}
        if subcategories is not None:
            payload["subcategories"] = subcategories
        return client.post("/categories", json=payload, headers=headers)

    return _create


@pytest.fixture
def create_subcategory(client, create_authenticated_headers):
    def _create(name, categories=None, products=None, headers=None):
        if headers is None:
            headers = create_authenticated_headers()
        payload = {"name": name}
        if categories is not None:
            payload["categories"] = categories
        if products is not None:
            payload["products"] = products
        return client.post("/subcategories", json=payload, headers=headers)

    return _create


@pytest.fixture
def create_product(client, create_authenticated_headers):
    def _create(name, description=None, subcategories=None, headers=None):
        if headers is None:
            headers = create_authenticated_headers()
        payload = {"name": name}
        if description is not None:
            payload["description"] = description
        if subcategories is not None:
            payload["subcategories"] = subcategories
        return client.post("/products", json=payload, headers=headers)

    return _create
