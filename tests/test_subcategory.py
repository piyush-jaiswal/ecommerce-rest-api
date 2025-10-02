import sqlite3

import pytest
from sqlalchemy.exc import IntegrityError

from app.models import Subcategory
from tests import utils


class TestSubcategory:
    TEST_SUBCATEGORY_NAME = "Smartphones"

    @pytest.fixture(autouse=True)
    def setup(self, client):
        self.client = client
        with client.application.app_context():
            assert Subcategory.query.count() == 0

    def _count_subcategories(self):
        with self.client.application.app_context():
            return Subcategory.query.count()

    def _verify_subcategory_in_db(self, name, should_exist=True):
        with self.client.application.app_context():
            subcategory = Subcategory.query.filter_by(name=name).first()
            if should_exist:
                assert subcategory is not None
                assert subcategory.name == name
                return subcategory
            else:
                assert subcategory is None

    def test_create_subcategory(self, create_subcategory):
        response = create_subcategory(self.TEST_SUBCATEGORY_NAME)

        assert response.status_code == 201
        data = response.get_json()
        assert data["name"] == self.TEST_SUBCATEGORY_NAME
        assert "id" in data
        self._verify_subcategory_in_db(self.TEST_SUBCATEGORY_NAME)

    def test_create_subcategory_duplicate_name(self, create_subcategory):
        create_subcategory(self.TEST_SUBCATEGORY_NAME)

        with pytest.raises(IntegrityError) as ie:
            create_subcategory(self.TEST_SUBCATEGORY_NAME)

        assert isinstance(ie.value.orig, sqlite3.IntegrityError)
        assert "UNIQUE constraint failed" in str(ie.value.orig)
        assert self._count_subcategories() == 1
        self._verify_subcategory_in_db(self.TEST_SUBCATEGORY_NAME)

    def test_get_subcategory_by_id(self, create_subcategory):
        response = create_subcategory("Laptops")
        data = response.get_json()
        sc_id = data["id"]
        get_resp = self.client.get(f"/subcategories/{sc_id}")

        assert get_resp.status_code == 200
        data = get_resp.get_json()
        assert data["name"] == "Laptops"
        assert data["id"] == sc_id

    def test_get_all_subcategories(self, create_subcategory):
        create_subcategory("A")
        create_subcategory("B")
        resp = self.client.get("/subcategories")

        assert resp.status_code == 200
        data = resp.get_json()
        assert "subcategories" in data
        assert len(data["subcategories"]) == 2
        names = [sc["name"] for sc in data["subcategories"]]
        assert "A" in names
        assert "B" in names

    def test_update_subcategory(self, create_authenticated_headers, create_subcategory):
        headers = create_authenticated_headers()
        response = create_subcategory("OldSubcat", headers=headers)
        data = response.get_json()
        sc_id = data["id"]
        update_resp = self.client.put(
            f"/subcategories/{sc_id}", json={"name": "NewSubcat"}, headers=headers
        )

        assert update_resp.status_code == 200
        data = update_resp.get_json()
        assert data["name"] == "NewSubcat"
        assert data["id"] == sc_id
        self._verify_subcategory_in_db("NewSubcat")
        self._verify_subcategory_in_db("OldSubcat", should_exist=False)

    def test_delete_subcategory(self, create_authenticated_headers, create_subcategory):
        headers = create_authenticated_headers()
        response = create_subcategory("ToDelete", headers=headers)
        data = response.get_json()
        sc_id = data["id"]
        delete_resp = self.client.delete(f"/subcategories/{sc_id}", headers=headers)

        assert delete_resp.status_code == 204
        get_resp = self.client.get(f"/subcategories/{sc_id}")
        assert get_resp.status_code == 404
        self._verify_subcategory_in_db("ToDelete", should_exist=False)

    @pytest.mark.parametrize(
        "get_headers, expected_code",
        [
            (lambda self: utils.get_expired_token_headers(self.client.application.app_context()), "token_expired"),
            (lambda self: utils.get_invalid_token_headers(), "invalid_token"),
            (lambda self: None, "authorization_required")
        ]
    )
    def test_create_subcategory_token_error(self, get_headers, expected_code):
        headers = get_headers(self)
        response = self.client.post(
            "/subcategories", json={"name": "CreateTokenError"}, headers=headers
        )
        utils.verify_token_error_response(response, expected_code)
        self._verify_subcategory_in_db("CreateTokenError", should_exist=False)

    @pytest.mark.parametrize(
        "get_headers, expected_code",
        [
            (lambda self: utils.get_expired_token_headers(self.client.application.app_context()), "token_expired"),
            (lambda self: utils.get_invalid_token_headers(), "invalid_token"),
            (lambda self: None, "authorization_required")
        ]
    )
    def test_update_subcategory_token_error(self, get_headers, create_subcategory, expected_code):
        response = create_subcategory("UpdateTokenError")
        data = response.get_json()
        sc_id = data["id"]

        update_headers = get_headers(self)
        update_resp = self.client.put(
            f"/subcategories/{sc_id}",
            json={"name": "UpdatedName"},
            headers=update_headers,
        )

        utils.verify_token_error_response(update_resp, expected_code)
        self._verify_subcategory_in_db("UpdateTokenError")
        self._verify_subcategory_in_db("UpdatedName", should_exist=False)

    @pytest.mark.parametrize(
        "get_headers, expected_code",
        [
            (lambda self: utils.get_expired_token_headers(self.client.application.app_context()), "token_expired"),
            (lambda self: utils.get_invalid_token_headers(), "invalid_token"),
            (lambda self: None, "authorization_required")
        ]
    )
    def test_delete_subcategory_token_error(self, get_headers, create_subcategory, expected_code):
        response = create_subcategory("DeleteTokenError")
        data = response.get_json()
        sc_id = data["id"]

        delete_headers = get_headers(self)
        delete_resp = self.client.delete(f"/subcategories/{sc_id}", headers=delete_headers)

        utils.verify_token_error_response(delete_resp, expected_code)
        self._verify_subcategory_in_db("DeleteTokenError")
