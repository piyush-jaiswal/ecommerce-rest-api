import sqlite3

import pytest
from sqlalchemy.exc import IntegrityError

from app.models import Category
from tests import utils


class TestCategory:
    TEST_CATEGORY_NAME = "Electronics"

    @pytest.fixture(autouse=True)
    def setup(self, client):
        self.client = client
        with client.application.app_context():
            assert Category.query.count() == 0

    def _count_categories(self):
        with self.client.application.app_context():
            return Category.query.count()

    def _verify_category_in_db(self, name, should_exist=True):
        with self.client.application.app_context():
            category = Category.query.filter_by(name=name).first()
            if should_exist:
                assert category is not None
                assert category.name == name
                return category
            else:
                assert category is None

    def test_create_category(self, create_category):
        response = create_category(self.TEST_CATEGORY_NAME)

        assert response.status_code == 201
        data = response.get_json()
        assert data["name"] == self.TEST_CATEGORY_NAME
        assert "id" in data
        self._verify_category_in_db(self.TEST_CATEGORY_NAME)

    def test_create_category_duplicate_name(self, create_category):
        create_category(self.TEST_CATEGORY_NAME)

        with pytest.raises(IntegrityError) as ie:
            create_category(self.TEST_CATEGORY_NAME)

        assert isinstance(ie.value.orig, sqlite3.IntegrityError)
        assert "UNIQUE constraint failed" in str(ie.value.orig)
        assert self._count_categories() == 1
        self._verify_category_in_db(self.TEST_CATEGORY_NAME)

    def test_get_category_by_id(self, create_category):
        response = create_category("Books")
        data = response.get_json()
        cat_id = data["id"]
        get_resp = self.client.get(f"/categories/{cat_id}")

        assert get_resp.status_code == 200
        data = get_resp.get_json()
        assert data["name"] == "Books"
        assert data["id"] == cat_id

    def test_get_all_categories(self, create_category):
        create_category("A")
        create_category("B")
        resp = self.client.get("/categories")

        assert resp.status_code == 200
        data = resp.get_json()
        assert "categories" in data
        assert len(data["categories"]) == 2
        names = [cat["name"] for cat in data["categories"]]
        assert "A" in names
        assert "B" in names

    def test_update_category(self, create_authenticated_headers, create_category):
        headers = create_authenticated_headers()
        response = create_category("OldName", headers=headers)
        data = response.get_json()
        cat_id = data["id"]
        update_resp = self.client.put(
            f"/categories/{cat_id}", json={"name": "NewName"}, headers=headers
        )

        assert update_resp.status_code == 200
        data = update_resp.get_json()
        assert data["name"] == "NewName"
        assert data["id"] == cat_id

        self._verify_category_in_db("NewName")
        self._verify_category_in_db("OldName", should_exist=False)

    def test_delete_category(self, create_authenticated_headers, create_category):
        headers = create_authenticated_headers()
        response = create_category("ToDelete", headers=headers)
        data = response.get_json()
        cat_id = data["id"]
        delete_resp = self.client.delete(f"/categories/{cat_id}", headers=headers)

        assert delete_resp.status_code == 204
        get_resp = self.client.get(f"/categories/{cat_id}")
        assert get_resp.status_code == 404
        self._verify_category_in_db("ToDelete", should_exist=False)

    @pytest.mark.parametrize(
        "get_headers, expected_code",
        [
            (lambda self: utils.get_expired_token_headers(self.client.application.app_context()), "token_expired"),
            (lambda self: utils.get_invalid_token_headers(), "invalid_token"),
            (lambda self: None, "authorization_required")
        ]
    )
    def test_create_category_token_error(self, get_headers, expected_code):
        headers = get_headers(self)
        response = self.client.post(
            "/categories", json={"name": "CreateTokenError"}, headers=headers
        )
        utils.verify_token_error_response(response, expected_code)
        self._verify_category_in_db("CreateTokenError", should_exist=False)

    @pytest.mark.parametrize(
        "get_headers, expected_code",
        [
            (lambda self: utils.get_expired_token_headers(self.client.application.app_context()), "token_expired"),
            (lambda self: utils.get_invalid_token_headers(), "invalid_token"),
            (lambda self: None, "authorization_required")
        ]
    )
    def test_update_category_token_error(self, get_headers, create_category, expected_code):
        response = create_category("UpdateTokenError")
        data = response.get_json()
        cat_id = data["id"]

        update_headers = get_headers(self)
        update_resp = self.client.put(
            f"/categories/{cat_id}",
            json={"name": "UpdatedName"},
            headers=update_headers,
        )

        utils.verify_token_error_response(update_resp, expected_code)
        self._verify_category_in_db("UpdateTokenError")
        self._verify_category_in_db("UpdatedName", should_exist=False)

    @pytest.mark.parametrize(
        "get_headers, expected_code",
        [
            (lambda self: utils.get_expired_token_headers(self.client.application.app_context()), "token_expired"),
            (lambda self: utils.get_invalid_token_headers(), "invalid_token"),
            (lambda self: None, "authorization_required")
        ]
    )
    def test_delete_category_token_error(self, get_headers, create_category, expected_code):
        response = create_category("DeleteTokenError")
        data = response.get_json()
        cat_id = data["id"]

        delete_headers = get_headers(self)
        delete_resp = self.client.delete(f"/categories/{cat_id}", headers=delete_headers)

        utils.verify_token_error_response(delete_resp, expected_code)
        self._verify_category_in_db("DeleteTokenError")
