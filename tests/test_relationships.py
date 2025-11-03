import sqlite3

import pytest
from sqlalchemy.exc import IntegrityError

from app.models import Category, Product, Subcategory


class TestRelationships:
    @pytest.fixture(autouse=True)
    def setup(self, client):
        self.client = client
        assert Category.query.count() == 0
        assert Subcategory.query.count() == 0
        assert Product.query.count() == 0

    def _category_subcategory_ids(self, category_id):
        category = Category.query.get(category_id)
        assert category is not None
        return sorted([subcategory.id for subcategory in category.subcategories])

    def _subcategory_category_ids(self, subcategory_id):
        subcategory = Subcategory.query.get(subcategory_id)
        assert subcategory is not None
        return sorted([category.id for category in subcategory.categories])

    def _subcategory_product_ids(self, subcategory_id):
        subcategory = Subcategory.query.get(subcategory_id)
        assert subcategory is not None
        return sorted([product.id for product in subcategory.products])

    def _product_subcategory_ids(self, product_id):
        product = Product.query.get(product_id)
        assert product is not None
        return sorted([subcategory.id for subcategory in product.subcategories])

    def _category_product_ids_via_subcategories(self, category_id):
        category = Category.query.get(category_id)
        assert category is not None
        return sorted({product.id for subcategory in category.subcategories for product in subcategory.products.all()})

    def _assert_related_collection(self, resp, key, expected_ids=None, status_code=200):
        assert resp.status_code == status_code
        data = resp.get_json()
        assert key in data
        returned_ids = sorted([item["id"] for item in data[key]])
        expected_ids = expected_ids or []
        assert returned_ids == sorted(expected_ids)

    def test_create_category_with_subcategories(self, create_category, create_subcategory):
        subcategory1 = create_subcategory("SC_A").get_json()
        subcategory2 = create_subcategory("SC_B").get_json()
        response = create_category("Cat_AB", subcategories=[subcategory1["id"], subcategory2["id"]])
        assert response.status_code == 201
        category = response.get_json()

        assert self._category_subcategory_ids(category["id"]) == sorted([subcategory1["id"], subcategory2["id"]])
        assert category["id"] in self._subcategory_category_ids(subcategory1["id"])
        assert category["id"] in self._subcategory_category_ids(subcategory2["id"])

    def test_create_subcategory_with_categories_and_products(self, create_subcategory, create_category, create_product):
        category1 = create_category("C1").get_json()
        category2 = create_category("C2").get_json()
        product1 = create_product("P1", "des").get_json()
        product2 = create_product("P2", "desc").get_json()

        response = create_subcategory("SC_C1C2_P1P2", categories=[category1["id"], category2["id"]], products=[product1["id"], product2["id"]])
        assert response.status_code == 201
        subcategory = response.get_json()

        assert self._subcategory_category_ids(subcategory["id"]) == sorted([category1["id"], category2["id"]])
        assert self._subcategory_product_ids(subcategory["id"]) == sorted([product1["id"], product2["id"]])

    def test_create_product_with_subcategories_links_to_category_products(self, create_category, create_subcategory, create_product):
        category = create_category("C").get_json()
        subcategory = create_subcategory("SC", categories=[category["id"]]).get_json()
        response = create_product("P", "desc", subcategories=[subcategory["id"]])
        assert response.status_code == 201
        product = response.get_json()

        assert subcategory["id"] in self._product_subcategory_ids(product["id"])
        assert product["id"] in self._category_product_ids_via_subcategories(category["id"])
        assert product["id"] in self._subcategory_product_ids(subcategory["id"])

    def test_update_category_adds_subcategories(self, create_authenticated_headers, create_category, create_subcategory):
        subcategory1 = create_subcategory("U_SC1").get_json()
        subcategory2 = create_subcategory("U_SC2").get_json()
        category = create_category("U_Cat", subcategories=[subcategory1["id"]]).get_json()

        headers = create_authenticated_headers()
        update_response = self.client.put(f"/categories/{category['id']}", json={"subcategories": [subcategory2["id"]]}, headers=headers)
        assert update_response.status_code == 200

        assert self._category_subcategory_ids(category["id"]) == sorted([subcategory1["id"], subcategory2["id"]])

    def test_update_category_adds_linked_subcategories(self, create_authenticated_headers, create_category, create_subcategory):
        subcategory = create_subcategory("U_SC1").get_json()
        category = create_category("U_Cat", subcategories=[subcategory["id"]]).get_json()

        headers = create_authenticated_headers()
        with pytest.raises(IntegrityError) as ie:
            self.client.put(f"/categories/{category['id']}", json={"subcategories": [subcategory["id"]]}, headers=headers)

        assert isinstance(ie.value.orig, sqlite3.IntegrityError)
        assert "UNIQUE constraint failed" in str(ie.value.orig)
        assert self._category_subcategory_ids(category["id"]) == [subcategory["id"]]

    def test_update_subcategory_adds_categories_and_products(self, create_authenticated_headers, create_category, create_product, create_subcategory):
        category1 = create_category("UC1").get_json()
        category2 = create_category("UC2").get_json()
        product1 = create_product("UP1").get_json()
        product2 = create_product("UP2").get_json()
        subcategory = create_subcategory("U_SC").get_json()

        headers = create_authenticated_headers()
        update_response = self.client.put(
            f"/subcategories/{subcategory['id']}",
            json={"categories": [category1["id"], category2["id"]], "products": [product1["id"], product2["id"]]},
            headers=headers,
        )
        assert update_response.status_code == 200

        assert self._subcategory_category_ids(subcategory["id"]) == sorted([category1["id"], category2["id"]])
        assert self._subcategory_product_ids(subcategory["id"]) == sorted([product1["id"], product2["id"]])

    def test_update_subcategory_adds_linked_categories_and_products(self, create_authenticated_headers, create_category, create_product, create_subcategory):
        category = create_category("UC1").get_json()
        product = create_product("UP1").get_json()
        subcategory = create_subcategory("U_SC", categories=[category["id"]], products=[product["id"]]).get_json()

        headers = create_authenticated_headers()
        with pytest.raises(IntegrityError) as ie_c:
            self.client.put(
                f"/subcategories/{subcategory['id']}",
                json={"categories": [category["id"]]},
                headers=headers,
            )
        with pytest.raises(IntegrityError) as ie_p:
            self.client.put(
                f"/subcategories/{subcategory['id']}",
                json={"products": [product["id"]]},
                headers=headers,
            )
        with pytest.raises(IntegrityError) as ie_cp:
            self.client.put(
                f"/subcategories/{subcategory['id']}",
                json={"categories": [category["id"]], "products": [product["id"]]},
                headers=headers,
            )

        assert isinstance(ie_c.value.orig, sqlite3.IntegrityError)
        assert isinstance(ie_p.value.orig, sqlite3.IntegrityError)
        assert isinstance(ie_cp.value.orig, sqlite3.IntegrityError)
        assert "UNIQUE constraint failed" in str(ie_c.value.orig)
        assert "UNIQUE constraint failed" in str(ie_p.value.orig)
        assert "UNIQUE constraint failed" in str(ie_cp.value.orig)

        assert self._subcategory_category_ids(subcategory["id"]) == [category["id"]]
        assert self._subcategory_product_ids(subcategory["id"]) == [product["id"]]

    def test_update_product_adds_subcategories(self, create_authenticated_headers, create_product, create_subcategory):
        subcategory1 = create_subcategory("UPS1").get_json()
        subcategory2 = create_subcategory("UPS2").get_json()
        product = create_product("UP", "desc", subcategories=[subcategory1["id"]]).get_json()

        headers = create_authenticated_headers()
        update_response = self.client.put(f"/products/{product['id']}", json={"subcategories": [subcategory2["id"]]}, headers=headers)
        assert update_response.status_code == 200

        assert self._product_subcategory_ids(product["id"]) == sorted([subcategory1["id"], subcategory2["id"]])

    def test_update_product_adds_linked_subcategories(
        self, create_authenticated_headers, create_product, create_subcategory
    ):
        subcategory1 = create_subcategory("UPS1").get_json()
        subcategory2 = create_subcategory("UPS2").get_json()
        product = create_product(
            "UP", "desc", subcategories=[subcategory1["id"], subcategory2["id"]]
        ).get_json()

        with pytest.raises(IntegrityError) as ie:
            self.client.put(
                f"/products/{product['id']}",
                json={"subcategories": [subcategory1["id"]]},
                headers=create_authenticated_headers(),
            )

        assert isinstance(ie.value.orig, sqlite3.IntegrityError)
        assert "UNIQUE constraint failed" in str(ie.value.orig)
        assert self._product_subcategory_ids(product["id"]) == sorted(
            [subcategory1["id"], subcategory2["id"]]
        )

    def test_get_category_subcategories_empty(self, create_category):
        category = create_category("Cat_NoSC").get_json()
        resp = self.client.get(f"/categories/{category['id']}/subcategories")
        self._assert_related_collection(resp, "subcategories")

    def test_get_category_subcategories_populated(self, create_category, create_subcategory):
        subcategory1 = create_subcategory("SC1").get_json()
        subcategory2 = create_subcategory("SC2").get_json()
        category = create_category("Cat_WithSC", subcategories=[subcategory1["id"], subcategory2["id"]]).get_json()

        resp = self.client.get(f"/categories/{category['id']}/subcategories")
        self._assert_related_collection(resp, "subcategories", expected_ids=[subcategory1["id"], subcategory2["id"]])

    def test_get_category_products_empty(self, create_category):
        category = create_category("Cat_NoProd").get_json()
        resp = self.client.get(f"/categories/{category['id']}/products")
        self._assert_related_collection(resp, "products")

    def test_get_category_products_populated_with_pagination(self, create_category, create_subcategory, create_product):
        category = create_category("Cat_Prod").get_json()
        subcategory = create_subcategory("SC_Prod", categories=[category["id"]]).get_json()

        product_ids = set()
        for index in range(12):
            product_resp = create_product(f"P{index}", "desc", subcategories=[subcategory["id"]])
            product_ids.add(product_resp.get_json().get("id"))

        page1 = self.client.get(f"/categories/{category['id']}/products").get_json()
        next_cursor = page1["cursor"]["next"]
        page2 = self.client.get(f"/categories/{category['id']}/products?cursor={next_cursor}").get_json()
        assert len(page1["products"]) == 10
        assert len(page2["products"]) == 2

        returned_product_ids = set(p["id"] for p in page1["products"] + page2["products"])
        assert returned_product_ids == product_ids

    def test_get_subcategory_categories_empty(self, create_subcategory):
        subcategory = create_subcategory("SC_NoCat").get_json()
        resp = self.client.get(f"/subcategories/{subcategory['id']}/categories")
        self._assert_related_collection(resp, "categories")

    def test_get_subcategory_categories_populated(self, create_category, create_subcategory):
        category1 = create_category("C1").get_json()
        category2 = create_category("C2").get_json()
        subcategory = create_subcategory("SC_Cats", categories=[category1["id"], category2["id"]]).get_json()

        resp = self.client.get(f"/subcategories/{subcategory['id']}/categories")
        self._assert_related_collection(resp, "categories", expected_ids=[category1["id"], category2["id"]])

    def test_get_subcategory_products_empty(self, create_subcategory):
        subcategory = create_subcategory("SC_NoProd").get_json()
        resp = self.client.get(f"/subcategories/{subcategory['id']}/products")
        self._assert_related_collection(resp, "products")

    def test_get_subcategory_products_populated_with_pagination(self, create_subcategory, create_product):
        subcategory = create_subcategory("SC_Pag").get_json()

        product_ids = set()
        for index in range(11):
            product_resp = create_product(f"SP{index}", "desc", subcategories=[subcategory["id"]])
            product_ids.add(product_resp.get_json().get("id"))

        page1 = self.client.get(f"/subcategories/{subcategory['id']}/products").get_json()
        next_cursor = page1["cursor"]["next"]
        page2 = self.client.get(f"/subcategories/{subcategory['id']}/products?cursor={next_cursor}").get_json()
        assert len(page1["products"]) == 10
        assert len(page2["products"]) == 1

        returned_product_ids = set(p["id"] for p in page1["products"] + page2["products"])
        assert returned_product_ids == product_ids

    def test_get_product_subcategories_empty(self, create_product):
        product = create_product("Prod_NoSC", "desc").get_json()
        resp = self.client.get(f"/products/{product['id']}/subcategories")
        self._assert_related_collection(resp, "subcategories")

    def test_get_product_subcategories_populated(self, create_product, create_subcategory):
        subcategory1 = create_subcategory("S1").get_json()
        subcategory2 = create_subcategory("S2").get_json()
        product = create_product("Prod_SC", "desc", subcategories=[subcategory1["id"], subcategory2["id"]]).get_json()

        resp = self.client.get(f"/products/{product['id']}/subcategories")
        self._assert_related_collection(resp, "subcategories", expected_ids=[subcategory1["id"], subcategory2["id"]])

    @pytest.mark.parametrize(
        "path",
        [
            "/categories/999999/subcategories",
            "/categories/999999/products",
            "/subcategories/999999/categories",
            "/subcategories/999999/products",
            "/products/999999/subcategories",
        ],
    )
    def test_relationship_getters_404(self, path):
        resp = self.client.get(path)
        assert resp.status_code == 404
