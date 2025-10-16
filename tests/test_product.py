import sqlite3

import pytest
from sqlalchemy.exc import IntegrityError

from app.models import Product
from tests import utils


class TestProduct:
    TEST_PRODUCT_NAME = "iPhone 13"
    TEST_PRODUCT_DESC = "Latest Apple iPhone"

    @pytest.fixture(autouse=True)
    def setup(self, client):
        self.client = client
        assert Product.query.count() == 0

    def _count_products(self):
        return Product.query.count()

    def _verify_product_in_db(self, name, should_exist=True):
        product = Product.query.filter_by(name=name).first()
        if should_exist:
            assert product is not None
            assert product.name == name
            return product
        else:
            assert product is None

    def test_create_product(self, create_product):
        response = create_product(self.TEST_PRODUCT_NAME, self.TEST_PRODUCT_DESC)

        assert response.status_code == 201
        data = response.get_json()
        assert data["name"] == self.TEST_PRODUCT_NAME
        assert data["description"] == self.TEST_PRODUCT_DESC
        assert "id" in data
        self._verify_product_in_db(self.TEST_PRODUCT_NAME)

    def test_create_product_duplicate_name(self, create_product):
        create_product(self.TEST_PRODUCT_NAME, self.TEST_PRODUCT_DESC)

        with pytest.raises(IntegrityError) as ie:
            create_product(self.TEST_PRODUCT_NAME, self.TEST_PRODUCT_DESC)

        assert isinstance(ie.value.orig, sqlite3.IntegrityError)
        assert "UNIQUE constraint failed" in str(ie.value.orig)
        assert self._count_products() == 1
        self._verify_product_in_db(self.TEST_PRODUCT_NAME)

    def test_get_product_by_id(self, create_product):
        response = create_product("Pixel 6", "Google phone")
        data = response.get_json()
        p_id = data["id"]
        get_resp = self.client.get(f"/products/{p_id}")

        assert get_resp.status_code == 200
        data = get_resp.get_json()
        assert data["name"] == "Pixel 6"
        assert data["id"] == p_id

    def test_get_all_products(self, create_product):
        create_product("A", "descA")
        create_product("B", "descB")
        resp = self.client.get("/products")

        assert resp.status_code == 200
        data = resp.get_json()
        assert "products" in data
        assert len(data["products"]) == 2
        names = [prod["name"] for prod in data["products"]]
        assert "A" in names
        assert "B" in names

    def test_update_product(self, create_authenticated_headers, create_product):
        response = create_product("OldProduct", "OldDesc")
        data = response.get_json()
        p_id = data["id"]

        update_resp = self.client.put(
            f"/products/{p_id}",
            json={"name": "NewProduct", "description": "NewDesc"},
            headers=create_authenticated_headers(),
        )

        assert update_resp.status_code == 200
        data = update_resp.get_json()
        assert data["name"] == "NewProduct"
        assert data["description"] == "NewDesc"
        assert data["id"] == p_id
        self._verify_product_in_db("NewProduct")
        self._verify_product_in_db("OldProduct", should_exist=False)

    def test_update_product_duplicate_name(
        self, create_authenticated_headers, create_product
    ):
        create_product("OldProduct", "OldDesc")
        response = create_product("NewProduct", "NewDesc")
        data = response.get_json()
        cat_id = data["id"]

        with pytest.raises(IntegrityError) as ie:
            self.client.put(
                f"/products/{cat_id}",
                json={"name": "OldProduct"},
                headers=create_authenticated_headers(),
            )

        assert isinstance(ie.value.orig, sqlite3.IntegrityError)
        assert "UNIQUE constraint failed" in str(ie.value.orig)
        self._verify_product_in_db("OldProduct")
        self._verify_product_in_db("NewProduct")

    def test_delete_product(self, create_authenticated_headers, create_product):
        response = create_product("ToDelete", "desc")
        data = response.get_json()
        p_id = data["id"]

        delete_resp = self.client.delete(
            f"/products/{p_id}", headers=create_authenticated_headers()
        )

        assert delete_resp.status_code == 204
        get_resp = self.client.get(f"/products/{p_id}")
        assert get_resp.status_code == 404
        self._verify_product_in_db("ToDelete", should_exist=False)

    @pytest.mark.parametrize(
        "name",
        [
            "Test Product With Spaces And / And @",
            "Café",
            "C++",
            "20% off"
        ]
    )
    def test_get_product_by_name(self, create_product, name):
        response = create_product(name, "desc")
        assert response.status_code == 201
        data = response.get_json()
        p_id = data["id"]

        get_resp = self.client.get("/products", query_string={"name": name})
        assert get_resp.status_code == 200
        prod_data = get_resp.get_json()["products"][0]
        assert prod_data["id"] == p_id
        assert prod_data["name"] == name
        assert prod_data["description"] == "desc"

        not_found_resp = self.client.get("/products", query_string={"name": "Non existent product"})
        assert not_found_resp.get_json()["products"] == []

    @pytest.mark.parametrize(
        "get_headers, expected_code",
        [
            (utils.get_expired_token_headers, "token_expired"),
            (utils.get_invalid_token_headers, "invalid_token"),
            (lambda: None, "authorization_required")
        ]
    )
    def test_create_product_token_error(self, get_headers, expected_code):
        headers = get_headers()
        response = self.client.post(
            "/products", json={"name": "CreateTokenError"}, headers=headers
        )
        utils.verify_token_error_response(response, expected_code)
        self._verify_product_in_db("CreateTokenError", should_exist=False)

    @pytest.mark.parametrize(
        "get_headers, expected_code",
        [
            (utils.get_expired_token_headers, "token_expired"),
            (utils.get_invalid_token_headers, "invalid_token"),
            (lambda: None, "authorization_required")
        ]
    )
    def test_update_product_token_error(self, get_headers, create_product, expected_code):
        response = create_product("UpdateTokenError", "desc")
        data = response.get_json()
        p_id = data["id"]

        update_headers = get_headers()
        update_resp = self.client.put(
            f"/products/{p_id}",
            json={"name": "UpdatedName"},
            headers=update_headers,
        )

        utils.verify_token_error_response(update_resp, expected_code)
        self._verify_product_in_db("UpdateTokenError")
        self._verify_product_in_db("UpdatedName", should_exist=False)

    @pytest.mark.parametrize(
        "get_headers, expected_code",
        [
            (utils.get_expired_token_headers, "token_expired"),
            (utils.get_invalid_token_headers, "invalid_token"),
            (lambda: None, "authorization_required")
        ]
    )
    def test_delete_product_token_error(self, get_headers, create_product, expected_code):
        response = create_product("DeleteTokenError", "desc")
        data = response.get_json()
        p_id = data["id"]

        delete_headers = get_headers()
        delete_resp = self.client.delete(f"/products/{p_id}", headers=delete_headers)

        utils.verify_token_error_response(delete_resp, expected_code)
        self._verify_product_in_db("DeleteTokenError")

    def test_products_pagination(self, create_product):
        for i in range(15):
            create_product(f"Product{i}", f"Description{i}")

        # Page 1 - default
        resp1 = self.client.get("/products")
        assert resp1.status_code == 200
        data1 = resp1.get_json()
        assert "products" in data1
        assert len(data1["products"]) == 10

        # Page 2
        resp2 = self.client.get("/products?page=2")
        assert resp2.status_code == 200
        data2 = resp2.get_json()
        assert "products" in data2
        assert len(data2["products"]) == 5
