import pytest

from app.models import Subcategory
from tests import utils


class TestSubcategory:
    TEST_SUBCATEGORY_NAME = "Smartphones"

    @pytest.fixture(autouse=True)
    def setup(self, client):
        self.client = client
        with client.application.app_context():
            assert Subcategory.query.count() == 0

    @pytest.fixture
    def create_subcategory(self, create_authenticated_headers):
        def _create(name, categories=None, products=None, headers=None):
            if headers is None:
                headers = create_authenticated_headers()
            payload = {"name": name}
            if categories is not None:
                payload["categories"] = categories
            if products is not None:
                payload["products"] = products
            return self.client.post(
                "/subcategory/create", json=payload, headers=headers
            )
        return _create

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
        response = create_subcategory(self.TEST_SUBCATEGORY_NAME)

        assert response.status_code == 500
        assert self._count_subcategories() == 1
        self._verify_subcategory_in_db(self.TEST_SUBCATEGORY_NAME)

    # TODO: Add tests for creation with categories and products when those fixtures/utilities are available

    def test_get_subcategory_by_id(self, create_subcategory):
        response = create_subcategory("Laptops")
        data = response.get_json()
        sc_id = data["id"]
        get_resp = self.client.get(f"/subcategory/{sc_id}")

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
            f"/subcategory/{sc_id}/update", json={"name": "NewSubcat"}, headers=headers
        )

        assert update_resp.status_code == 201
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
        delete_resp = self.client.delete(f"/subcategory/{sc_id}", headers=headers)

        assert delete_resp.status_code == 200
        get_resp = self.client.get(f"/subcategory/{sc_id}")
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
            "/subcategory/create", json={"name": "CreateTokenError"}, headers=headers
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
    def test_update_subcategory_token_error(self, get_headers, create_subcategory, create_authenticated_headers, expected_code):
        headers = create_authenticated_headers()
        response = create_subcategory("UpdateTokenError", headers=headers)
        data = response.get_json()
        sc_id = data["id"]

        update_headers = get_headers(self)
        update_resp = self.client.put(
            f"/subcategory/{sc_id}/update",
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
    def test_delete_subcategory_token_error(self, get_headers, create_subcategory, create_authenticated_headers, expected_code):
        headers = create_authenticated_headers()
        response = create_subcategory("DeleteTokenError", headers=headers)
        data = response.get_json()
        sc_id = data["id"]

        delete_headers = get_headers(self)
        delete_resp = self.client.delete(f"/subcategory/{sc_id}", headers=delete_headers)

        utils.verify_token_error_response(delete_resp, expected_code)
        self._verify_subcategory_in_db("DeleteTokenError")

    def test_get_subcategory_categories_empty(self, create_subcategory):
        response = create_subcategory("NoCatRel")
        data = response.get_json()
        sc_id = data["id"]

        resp = self.client.get(f"/subcategory/{sc_id}/categories")

        assert resp.status_code == 200
        data = resp.get_json()
        assert "categories" in data
        assert data["categories"] == []

    def test_get_subcategory_products_empty(self, create_subcategory):
        response = create_subcategory("NoProdRel")
        data = response.get_json()
        sc_id = data["id"]

        resp = self.client.get(f"/subcategory/{sc_id}/products")

        assert resp.status_code == 200
        data = resp.get_json()
        assert "products" in data
        assert data["products"] == []
