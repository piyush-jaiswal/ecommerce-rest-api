import pytest

from app import create_app, db
from config import TestingConfig
from tests import utils


@pytest.fixture
def app():
    app = create_app(TestingConfig)

    # setup
    app_context = app.app_context()
    app_context.push()
    db.create_all()

    yield app

    # teardown
    db.session.remove()
    db.drop_all()
    app_context.pop()


@pytest.fixture
def client(app):
    return app.test_client()


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
