import pytest
from testcontainers.postgres import PostgresContainer

from app import create_app, db
from tests import utils


@pytest.fixture(scope="session")
def pg_container():
    with PostgresContainer("postgres:16") as pg:
        yield pg


@pytest.fixture(scope="session")
def app(pg_container):
    app = create_app(
        "testing",
        **{
            "SQLALCHEMY_DATABASE_URI": pg_container.get_connection_url(),
        },
    )

    # setup
    app_context = app.app_context()
    app_context.push()
    db.create_all()

    yield app

    # teardown
    db.session.remove()
    db.drop_all()
    db.engine.dispose()
    app_context.pop()


# Automatically clean database between tests. Required since app fixture uses session scope
@pytest.fixture(autouse=True)
def clean_db(app):
    yield

    # Clean all tables after each test
    with app.app_context():
        for table in reversed(db.metadata.sorted_tables):
            db.session.execute(table.delete())
        db.session.commit()
        db.session.close()


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
