import logging

import pytest
from flask_migrate import upgrade
from sqlalchemy import create_engine, make_url, text

from app import create_app, db
from config import DevelopmentConfig
from tests import utils


def _get_db_urls():
    dev_url = make_url(DevelopmentConfig.SQLALCHEMY_DATABASE_URI)
    admin_url = dev_url.set(database="postgres")
    test_db_name = "ecommerce_test_db"
    test_url = dev_url.set(database=test_db_name)

    return admin_url, test_url, test_db_name


ADMIN_DB_URL, TEST_DB_URL, TEST_DB_NAME = _get_db_urls()


def _ensure_database():
    admin_engine = create_engine(ADMIN_DB_URL)

    # Postgres requires database creation to happen outside transactions
    with admin_engine.connect().execution_options(isolation_level="AUTOCOMMIT") as conn:
        # Check if the test db exists
        query = text("SELECT 1 FROM pg_database WHERE datname = :db_name").bindparams(
            db_name=TEST_DB_NAME
        )
        database_exists = conn.execute(query).scalar()

        # Create if not
        if not database_exists:
            conn.execute(text(f"CREATE DATABASE {TEST_DB_NAME};"))

    admin_engine.dispose()


@pytest.fixture(scope="session")
def app():
    _ensure_database()
    app = create_app(
        "testing",
        **{
            "SQLALCHEMY_DATABASE_URI": TEST_DB_URL,
        },
    )

    # setup
    app_context = app.app_context()
    app_context.push()
    upgrade()
    app.logger.setLevel(logging.CRITICAL)  # don't need to print logs in tests

    yield app

    # teardown
    db.session.remove()
    db.drop_all()
    with db.engine.connect() as conn:
        conn.execute(text("DROP TABLE IF EXISTS alembic_version"))
        conn.commit()
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
        db.session.remove()


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
