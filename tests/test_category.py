import pytest

from app.models import Category
from tests import utils


class TestCategory:
    TEST_CATEGORY_NAME = "Electronics"

    @pytest.fixture(autouse=True)
    def setup(self, client):
        self.client = client
        with client.application.app_context():
            assert Category.query.count() == 0

    @pytest.fixture
    def create_category(self, create_authenticated_headers):
        def _create(name, headers=None):
            if headers is None:
                headers = create_authenticated_headers()
            return self.client.post(
                "/category/create", json={"name": name}, headers=headers
            )

        return _create

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
        response = create_category(self.TEST_CATEGORY_NAME)

        assert response.status_code == 500
        assert self._count_categories() == 1
        self._verify_category_in_db(self.TEST_CATEGORY_NAME)

    def test_get_category_by_id(self, create_category):
        response = create_category("Books")
        data = response.get_json()
        cat_id = data["id"]
        get_resp = self.client.get(f"/category/{cat_id}")

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
        response = create_category("OldName", headers)
        data = response.get_json()
        cat_id = data["id"]
        update_resp = self.client.put(
            f"/category/{cat_id}/update", json={"name": "NewName"}, headers=headers
        )

        assert update_resp.status_code == 201
        data = update_resp.get_json()
        assert data["name"] == "NewName"
        assert data["id"] == cat_id

        self._verify_category_in_db("NewName")
        self._verify_category_in_db("OldName", should_exist=False)

    def test_delete_category(self, create_authenticated_headers, create_category):
        headers = create_authenticated_headers()
        response = create_category("ToDelete", headers)
        data = response.get_json()
        cat_id = data["id"]
        delete_resp = self.client.delete(f"/category/{cat_id}", headers=headers)

        assert delete_resp.status_code == 200
        get_resp = self.client.get(f"/category/{cat_id}")
        assert get_resp.status_code == 404
        self._verify_category_in_db("ToDelete", should_exist=False)

    def test_create_category_expired_token(self):
        headers = utils.get_expired_token_headers(self.client.application.app_context())
        response = self.client.post(
            "/category/create", json={"name": "TestExpired"}, headers=headers
        )

        utils.verify_token_error_response(response, "token_expired")
        self._verify_category_in_db("TestExpired", should_exist=False)

    def test_create_category_invalid_token(self):
        headers = utils.get_invalid_token_headers()
        response = self.client.post(
            "/category/create", json={"name": "TestInvalid"}, headers=headers
        )

        utils.verify_token_error_response(response, "invalid_token")
        self._verify_category_in_db("TestInvalid", should_exist=False)

    def test_create_category_missing_token(self):
        response = self.client.post("/category/create", json={"name": "TestMissing"})
        utils.verify_token_error_response(response, "authorization_required")
        self._verify_category_in_db("TestMissing", should_exist=False)

    def test_update_category_expired_token(
        self, create_category, create_authenticated_headers
    ):
        headers = create_authenticated_headers()
        response = create_category("UpdateExpired", headers)
        data = response.get_json()
        cat_id = data["id"]

        expired_headers = utils.get_expired_token_headers(
            self.client.application.app_context()
        )
        update_resp = self.client.put(
            f"/category/{cat_id}/update",
            json={"name": "UpdatedName"},
            headers=expired_headers,
        )

        utils.verify_token_error_response(update_resp, "token_expired")
        self._verify_category_in_db("UpdateExpired")
        self._verify_category_in_db("UpdatedName", should_exist=False)

    def test_update_category_invalid_token(
        self, create_category, create_authenticated_headers
    ):
        headers = create_authenticated_headers()
        response = create_category("UpdateInvalid", headers)
        data = response.get_json()
        cat_id = data["id"]

        invalid_headers = utils.get_invalid_token_headers()
        update_resp = self.client.put(
            f"/category/{cat_id}/update",
            json={"name": "UpdatedName"},
            headers=invalid_headers,
        )

        utils.verify_token_error_response(update_resp, "invalid_token")
        self._verify_category_in_db("UpdateInvalid")
        self._verify_category_in_db("UpdatedName", should_exist=False)

    def test_update_category_missing_token(
        self, create_category, create_authenticated_headers
    ):
        headers = create_authenticated_headers()
        response = create_category("UpdateMissing", headers)
        data = response.get_json()
        cat_id = data["id"]

        update_resp = self.client.put(
            f"/category/{cat_id}/update", json={"name": "UpdatedName"}
        )

        utils.verify_token_error_response(update_resp, "authorization_required")
        self._verify_category_in_db("UpdateMissing")
        self._verify_category_in_db("UpdatedName", should_exist=False)

    def test_delete_category_expired_token(
        self, create_category, create_authenticated_headers
    ):
        headers = create_authenticated_headers()
        response = create_category("DeleteExpired", headers)
        data = response.get_json()
        cat_id = data["id"]

        expired_headers = utils.get_expired_token_headers(
            self.client.application.app_context()
        )
        delete_resp = self.client.delete(f"/category/{cat_id}", headers=expired_headers)

        utils.verify_token_error_response(delete_resp, "token_expired")
        self._verify_category_in_db("DeleteExpired")

    def test_delete_category_invalid_token(
        self, create_category, create_authenticated_headers
    ):
        headers = create_authenticated_headers()
        response = create_category("DeleteInvalid", headers)
        data = response.get_json()
        cat_id = data["id"]

        invalid_headers = utils.get_invalid_token_headers()
        delete_resp = self.client.delete(f"/category/{cat_id}", headers=invalid_headers)

        utils.verify_token_error_response(delete_resp, "invalid_token")
        self._verify_category_in_db("DeleteInvalid")

    def test_delete_category_missing_token(
        self, create_category, create_authenticated_headers
    ):
        headers = create_authenticated_headers()
        response = create_category("DeleteMissing", headers)
        data = response.get_json()
        cat_id = data["id"]

        delete_resp = self.client.delete(f"/category/{cat_id}")

        utils.verify_token_error_response(delete_resp, "authorization_required")
        self._verify_category_in_db("DeleteMissing")
