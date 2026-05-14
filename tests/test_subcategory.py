import time

import pytest

from app.models import Subcategory
from tests import utils


class TestSubcategory:
    TEST_SUBCATEGORY_NAME = "Smartphones"

    @pytest.fixture(autouse=True)
    def setup(self, client):
        self.client = client
        assert Subcategory.query.count() == 0

    def _count_subcategories(self):
        return Subcategory.query.count()

    def _verify_subcategory_in_db(self, name, should_exist=True):
        subcategory = Subcategory.query.filter_by(name=name).first()
        if should_exist:
            assert subcategory is not None
            assert subcategory.name == name
            return subcategory
        else:
            assert subcategory is None

    def test_create_subcategory(self, create_subcategory):
        response = create_subcategory(self.TEST_SUBCATEGORY_NAME)
        data = response.get_json()

        assert response.status_code == 201
        assert data["name"] == self.TEST_SUBCATEGORY_NAME
        assert "id" in data
        assert "created_at" in data
        assert "updated_at" in data

        created_at = utils.parse_api_datetime(data["created_at"])
        updated_at = utils.parse_api_datetime(data["updated_at"])
        assert created_at.tzinfo is not None
        assert updated_at.tzinfo is not None

        self._verify_subcategory_in_db(self.TEST_SUBCATEGORY_NAME)

    def test_create_subcategory_duplicate_name_case_insensitive(
        self, create_subcategory
    ):
        create_subcategory("Smartphones")
        response = create_subcategory("smartphones")

        assert response.status_code == 409
        data = response.get_json()
        assert "Subcategory with this name already exists" in data["message"]
        assert self._count_subcategories() == 1

    def test_create_subcategory_duplicate_name(self, create_subcategory):
        create_subcategory(self.TEST_SUBCATEGORY_NAME)

        response = create_subcategory(self.TEST_SUBCATEGORY_NAME)

        assert response.status_code == 409
        data = response.get_json()
        assert "Subcategory with this name already exists" in data["message"]
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
        response = create_subcategory("OldSubcat")
        data = response.get_json()
        sc_id = data["id"]
        created0 = utils.parse_api_datetime(data["created_at"])
        updated0 = utils.parse_api_datetime(data["updated_at"])

        time.sleep(0.02)
        update_resp = self.client.put(
            f"/subcategories/{sc_id}",
            json={"name": "NewSubcat"},
            headers=create_authenticated_headers(),
        )
        data = update_resp.get_json()

        assert update_resp.status_code == 200
        assert data["name"] == "NewSubcat"
        assert data["id"] == sc_id
        assert utils.parse_api_datetime(data["created_at"]) == created0
        assert utils.parse_api_datetime(data["updated_at"]) > updated0

        self._verify_subcategory_in_db("NewSubcat")
        self._verify_subcategory_in_db("OldSubcat", should_exist=False)

    def test_update_subcategory_duplicate_name(
        self, create_authenticated_headers, create_subcategory
    ):
        create_subcategory("OldSubcat")
        response = create_subcategory("NewSubcat")
        data = response.get_json()
        sc_id = data["id"]

        update_resp = self.client.put(
            f"/subcategories/{sc_id}",
            json={"name": "OldSubcat"},
            headers=create_authenticated_headers(),
        )

        assert update_resp.status_code == 409
        data = update_resp.get_json()
        assert "Subcategory with this name already exists" in data["message"]
        self._verify_subcategory_in_db("OldSubcat")
        self._verify_subcategory_in_db("NewSubcat")

    def test_delete_subcategory(self, create_authenticated_headers, create_subcategory):
        response = create_subcategory("ToDelete")
        data = response.get_json()
        sc_id = data["id"]

        delete_resp = self.client.delete(
            f"/subcategories/{sc_id}", headers=create_authenticated_headers()
        )

        assert delete_resp.status_code == 204
        get_resp = self.client.get(f"/subcategories/{sc_id}")
        assert get_resp.status_code == 404
        self._verify_subcategory_in_db("ToDelete", should_exist=False)

    @pytest.mark.parametrize(
        "get_headers, expected_code",
        [
            (utils.get_expired_token_headers, "token_expired"),
            (utils.get_invalid_token_headers, "invalid_token"),
            (lambda: None, "authorization_required"),
        ],
    )
    def test_create_subcategory_token_error(self, get_headers, expected_code):
        headers = get_headers()
        response = self.client.post(
            "/subcategories", json={"name": "CreateTokenError"}, headers=headers
        )
        utils.verify_token_error_response(response, expected_code)
        self._verify_subcategory_in_db("CreateTokenError", should_exist=False)

    @pytest.mark.parametrize(
        "get_headers, expected_code",
        [
            (utils.get_expired_token_headers, "token_expired"),
            (utils.get_invalid_token_headers, "invalid_token"),
            (lambda: None, "authorization_required"),
        ],
    )
    def test_update_subcategory_token_error(
        self, get_headers, create_subcategory, expected_code
    ):
        response = create_subcategory("UpdateTokenError")
        data = response.get_json()
        sc_id = data["id"]

        update_headers = get_headers()
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
            (utils.get_expired_token_headers, "token_expired"),
            (utils.get_invalid_token_headers, "invalid_token"),
            (lambda: None, "authorization_required"),
        ],
    )
    def test_delete_subcategory_token_error(
        self, get_headers, create_subcategory, expected_code
    ):
        response = create_subcategory("DeleteTokenError")
        data = response.get_json()
        sc_id = data["id"]

        delete_headers = get_headers()
        delete_resp = self.client.delete(
            f"/subcategories/{sc_id}", headers=delete_headers
        )

        utils.verify_token_error_response(delete_resp, expected_code)
        self._verify_subcategory_in_db("DeleteTokenError")
